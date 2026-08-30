import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from bedrock_adapter import BedrockAdapter, BedrockAdapterError, WorkspaceTools
from doctor import DiagnosticSuite


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def converse(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


def response(*content, usage=None):
    return {
        "output": {"message": {"role": "assistant", "content": list(content)}},
        "usage": usage or {"inputTokens": 2, "outputTokens": 3},
    }


class BedrockAdapterTests(unittest.TestCase):
    def test_doctor_probe_requires_region_model_and_sdk(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(DiagnosticSuite._probe_bedrock()[0], False)
        with (
            patch.dict("os.environ", {
                "AWS_REGION": "eu-west-2", "FACTORY_BEDROCK_MODEL_ID": "model",
            }, clear=True),
            patch("doctor.importlib.util.find_spec", return_value=object()),
        ):
            available, detail = DiagnosticSuite._probe_bedrock()
        self.assertTrue(available)
        self.assertIn("model in eu-west-2", detail)

    def test_structured_planning_uses_schema_constrained_tool(self):
        artifact = {"summary": "Build it"}
        client = FakeClient([response({"toolUse": {
            "toolUseId": "one", "name": "submit_artifact", "input": artifact,
        }})])
        adapter = BedrockAdapter(client, "model")

        self.assertEqual(adapter.structured_plan("prd", {"type": "object"}), artifact)
        choice = client.calls[0]["toolConfig"]["toolChoice"]
        self.assertEqual(choice, {"tool": {"name": "submit_artifact"}})

    def test_run_can_edit_then_return_final_response(self):
        client = FakeClient([
            response({"toolUse": {
                "toolUseId": "write-1", "name": "write_file",
                "input": {"path": "src/app.txt", "content": "hello\n"},
            }}),
            response({"text": "Implemented the requested change."}),
        ])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = BedrockAdapter(client, "model").run("change app", root)
            self.assertEqual((root / "src/app.txt").read_text(), "hello\n")
            self.assertIn("Implemented", result)
            tool_result = client.calls[1]["messages"][-1]["content"][0]["toolResult"]
            self.assertEqual(tool_result["status"], "success")

    def test_read_only_assignment_does_not_offer_write_tools(self):
        client = FakeClient([response({"text": "Reviewed."})])
        with tempfile.TemporaryDirectory() as directory:
            BedrockAdapter(client, "model").run("review", Path(directory), read_only=True)
        names = [item["toolSpec"]["name"] for item in client.calls[0]["toolConfig"]["tools"]]
        self.assertNotIn("write_file", names)
        self.assertNotIn("delete_file", names)

    def test_workspace_rejects_traversal_and_read_only_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            tools = WorkspaceTools(Path(directory), read_only=True)
            with self.assertRaisesRegex(BedrockAdapterError, "escapes"):
                tools.read_file("../outside")
            with self.assertRaisesRegex(BedrockAdapterError, "read-only"):
                tools.write_file("file.txt", "content")


if __name__ == "__main__":
    unittest.main()
