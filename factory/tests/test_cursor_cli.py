import contextlib
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]))

from cursor_cli import (
    CursorCLIError,
    cursor_command,
    cursor_result,
    invoke_cursor,
    probe_cursor_cli,
    resolve_cursor_cli,
    run_prompt,
)


class CursorCLITests(unittest.TestCase):
    def test_write_command_is_headless_forced_and_sandboxed(self):
        command = cursor_command(
            "/bin/agent",
            read_only=False,
            environment={"FACTORY_CURSOR_MODEL": "test-model"},
        )

        self.assertEqual(command[0], "/bin/agent")
        self.assertIn("--print", command)
        self.assertIn("--force", command)
        self.assertEqual(command[command.index("--sandbox") + 1], "enabled")
        self.assertEqual(command[command.index("--output-format") + 1], "json")
        self.assertEqual(command[command.index("--model") + 1], "test-model")
        self.assertNotIn("--mode", command)

    def test_read_only_command_uses_ask_mode(self):
        command = cursor_command("agent", read_only=True, environment={})

        self.assertEqual(command[command.index("--mode") + 1], "ask")

    def test_result_envelope_is_normalized_to_final_text(self):
        output = json.dumps({
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": '{"decision":"APPROVE"}',
        })

        self.assertEqual(cursor_result(output), '{"decision":"APPROVE"}')

    def test_invalid_result_envelope_is_rejected(self):
        with self.assertRaisesRegex(CursorCLIError, "successful result envelope"):
            cursor_result(json.dumps({"type": "result", "subtype": "error"}))

    def test_invoke_does_not_forward_unrelated_credentials(self):
        response = subprocess.CompletedProcess(
            ["agent"], 0,
            json.dumps({
                "type": "result",
                "subtype": "success",
                "is_error": False,
                "result": "done",
            }),
            "",
        )
        with (
            patch.dict(os.environ, {
                "PATH": "/usr/bin",
                "HOME": "/tmp/home",
                "CURSOR_API_KEY": "cursor-secret",
                "OPENAI_API_KEY": "must-not-leak",
            }, clear=True),
            patch("cursor_cli.subprocess.run", return_value=response) as invoked,
        ):
            result = invoke_cursor("agent", Path("/tmp"), "prompt", read_only=True)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "done")
        environment = invoked.call_args.kwargs["env"]
        self.assertEqual(environment["CURSOR_API_KEY"], "cursor-secret")
        self.assertNotIn("OPENAI_API_KEY", environment)
        self.assertEqual(invoked.call_args.kwargs["input"], "prompt")

    def test_probe_checks_required_flags_and_authentication(self):
        responses = [
            subprocess.CompletedProcess(
                ["agent", "--help"], 0,
                "--print --output-format --force --mode --sandbox", "",
            ),
            subprocess.CompletedProcess(["agent", "status"], 0, "Logged in", ""),
        ]
        with patch("cursor_cli.subprocess.run", side_effect=responses):
            ready, detail = probe_cursor_cli("agent", Path("/tmp"))

        self.assertTrue(ready)
        self.assertEqual(detail, "agent")

    def test_resolver_explains_how_to_install_when_no_binary_exists(self):
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("cursor_cli.shutil.which", return_value=None),
        ):
            with self.assertRaisesRegex(CursorCLIError, "Cursor CLI not found"):
                resolve_cursor_cli(Path("/tmp"))

    def test_adapter_entry_point_runs_a_fake_current_cursor_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / "agent"
            record = root / "invocation.json"
            binary.write_text(
                "#!/usr/bin/env python3\n"
                "import json, pathlib, sys\n"
                "if '--help' in sys.argv:\n"
                "    print('--print --output-format --force --mode --sandbox')\n"
                "elif 'status' in sys.argv:\n"
                "    print('Logged in')\n"
                "else:\n"
                f"    pathlib.Path({str(record)!r}).write_text(json.dumps({{'arguments':sys.argv[1:],'prompt':sys.stdin.read()}}))\n"
                "    print(json.dumps({'type':'system','subtype':'init','model':'test-model'}))\n"
                "    print(json.dumps({'type':'tool_call','subtype':'started','tool_call':{'readToolCall':{}}}))\n"
                "    print(json.dumps({'type':'result','subtype':'success','is_error':False,'result':'FACTORY_ROLE_VERDICT: PASS'}))\n"
            )
            binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
            prompt = root / "prompt.md"
            prompt.write_text("Review the candidate")

            with patch.dict(os.environ, {"FACTORY_CURSOR_BIN": str(binary), "HOME": directory}, clear=True):
                previous = Path.cwd()
                try:
                    os.chdir(root)
                    output = io.StringIO()
                    with contextlib.redirect_stdout(output):
                        code = run_prompt(prompt, read_only=True)
                finally:
                    os.chdir(previous)

            self.assertEqual(code, 0)
            invocation = json.loads(record.read_text())
            arguments = invocation["arguments"]
            self.assertIn("--print", arguments)
            self.assertIn("--force", arguments)
            self.assertEqual(arguments[arguments.index("--mode") + 1], "ask")
            self.assertNotIn("Review the candidate", arguments)
            self.assertEqual(invocation["prompt"], "Review the candidate")
            self.assertIn("Cursor session initialized with test-model", output.getvalue())
            self.assertIn("Cursor is using read", output.getvalue())
            self.assertIn("FACTORY_ROLE_VERDICT: PASS", output.getvalue())

            with patch.dict(os.environ, {"FACTORY_CURSOR_BIN": str(binary), "HOME": directory}, clear=True):
                previous = Path.cwd()
                try:
                    os.chdir(root)
                    with contextlib.redirect_stdout(io.StringIO()):
                        write_code = run_prompt(prompt, read_only=False)
                finally:
                    os.chdir(previous)

            self.assertEqual(write_code, 0)
            write_arguments = json.loads(record.read_text())["arguments"]
            self.assertIn("--force", write_arguments)
            self.assertNotIn("--mode", write_arguments)


if __name__ == "__main__":
    unittest.main()
