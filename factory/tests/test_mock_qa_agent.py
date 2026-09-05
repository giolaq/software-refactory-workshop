import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class MockQaRevisionTests(unittest.TestCase):
    def generate(self, repo, feedback="", ticket="2"):
        return subprocess.run(
            [sys.executable, str(Path(__file__).parents[1] / "mock_qa_agent.py"),
             ticket, "--scenario", "recipe-rebrand"], cwd=repo,
            input=("## Human review feedback\n```\n" + feedback + "\n```\n") if feedback else "",
            text=True, capture_output=True, timeout=10,
        )

    def test_known_rehearsal_revision_changes_the_test_and_names_its_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "demo-app/tests/test_ticket_2_acceptance.py"
            initial = self.generate(directory)
            self.assertEqual(initial.returncode, 0, initial.stderr)
            original = path.read_text()
            revised = self.generate(directory, "Reject FileNotFoundError; verify served stylesheet behavior.")
            self.assertEqual(revised.returncode, 0, revised.stderr)
            self.assertNotEqual(path.read_text(), original)
            self.assertIn("Browser layout and keyboard focus still require human inspection", revised.stdout)

    def test_unsupported_feedback_stops_instead_of_claiming_a_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.generate(directory, "Test a new payment flow")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not supported", result.stdout)
            self.assertFalse((Path(directory) / "demo-app/tests/test_ticket_2_acceptance.py").exists())

    def test_brand_test_proves_a_public_response_not_a_missing_local_file(self):
        with tempfile.TemporaryDirectory() as directory:
            self.generate(directory)
            source = (Path(directory) / "demo-app/tests/test_ticket_2_acceptance.py").read_text()
            self.assertIn('client.get("/static/table-story.css")', source)
            self.assertIn("response.status_code == 200", source)
            self.assertNotIn("read_text()", source)

    def test_missing_required_documentation_is_an_assertion_not_a_crash(self):
        with tempfile.TemporaryDirectory() as directory:
            self.generate(directory, ticket="5")
            path = Path(directory) / "demo-app/tests/test_ticket_5_acceptance.py"
            namespace = {"__file__": str(path)}
            exec(compile(path.read_text(), str(path), "exec"), namespace)
            with self.assertRaisesRegex(AssertionError, "TableStory run and verification guide"):
                namespace["test_ticket_5_documentation_acceptance"]()


if __name__ == "__main__":
    unittest.main()
