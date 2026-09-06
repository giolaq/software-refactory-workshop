import sys
import subprocess
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from acceptance_evidence import classify_focused_result, focused_test_command


class AcceptanceEvidenceTests(unittest.TestCase):
    def test_runner_failure_summary_is_not_assertion_evidence(self):
        for output in (
            "FAILED test_brand - FileNotFoundError: table-story.css\n1 failed",
            "not ok 1 - brand\nerror: ENOENT: no such file",
            "FAILED test_brand - RuntimeError: server unavailable",
            "E       assert False\nFAILED test_one - AssertionError\n"
            "FAILED test_two - FileNotFoundError: missing file",
        ):
            with self.subTest(output=output):
                self.assertEqual(classify_focused_result(1, output), "unrelated_failure")

    def test_builds_a_bounded_command_for_the_exact_python_test_files(self):
        command = focused_test_command(
            ["tests/test_ticket_7_search.py", "tests/test_ticket_7_errors.py"],
            "/tmp/factory python",
        )

        self.assertEqual(
            command,
            "'/tmp/factory python' -m pytest -q "
            "tests/test_ticket_7_errors.py tests/test_ticket_7_search.py",
        )

    def test_rejects_an_unsupported_focused_test_set(self):
        with self.assertRaisesRegex(ValueError, "supported focused test runner"):
            focused_test_command(["tests/Ticket7SearchTest.java"], sys.executable)

    def test_mixed_runners_execute_both_and_never_hide_a_runner_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            python_test = root / "test_ticket_7.py"
            node_test = root / "ticket-7.test.cjs"
            python_test.write_text("def test_behavior():\n    assert False, 'missing recipe'\n")
            node_test.write_text("const test = require('node:test'); test('node behavior', () => {});\n")
            command = focused_test_command([str(node_test), str(python_test)], sys.executable)
            def execute():
                result = subprocess.run(command, shell=True, cwd=root, text=True, capture_output=True)
                return result, classify_focused_result(result.returncode, result.stdout + result.stderr)
            result, classification = execute()
            self.assertEqual(classification, "behavior_assertion", result.stdout + result.stderr)
            self.assertIn("node behavior", result.stdout)
            # An assertion in Python must not hide a separate non-assertion failure.
            node_test.write_text("process.exit(1);\n")
            result, classification = execute()
            self.assertNotEqual(classification, "behavior_assertion", result.stdout + result.stderr)
            self.assertNotEqual(classification, "pass")
            python_test.write_text("def test_behavior():\n    assert True\n")
            node_test.write_text("const test = require('node:test'); test('node behavior', () => {});\n")
            result, classification = execute()
            self.assertEqual(classification, "pass", result.stdout + result.stderr)

    def test_classifies_only_behavior_assertions_as_valid_red_evidence(self):
        self.assertEqual(
            classify_focused_result(1, "FAILED test_search - AssertionError: expected recipe"),
            "behavior_assertion",
        )
        self.assertEqual(
            classify_focused_result(1, "not ok 1 - search\ncode: ERR_ASSERTION"),
            "behavior_assertion",
        )
        self.assertEqual(
            classify_focused_result(2, "ERROR collecting test_search.py\nModuleNotFoundError: flask"),
            "collection_error",
        )
        self.assertEqual(classify_focused_result(124, "timed out"), "timeout")
        self.assertEqual(classify_focused_result(127, "pytest: command not found"), "command_error")
        self.assertEqual(classify_focused_result(1, "process exited unexpectedly"), "unrelated_failure")

    def test_rejects_skipped_or_already_passing_tests_as_red_evidence(self):
        self.assertEqual(classify_focused_result(0, "1 passed"), "pass")
        self.assertEqual(classify_focused_result(0, "1 skipped"), "skipped")
        self.assertEqual(classify_focused_result(0, "# tests 1\n# skipped 1"), "skipped")
        self.assertEqual(classify_focused_result(0, "ℹ tests 1\nℹ skipped 1"), "skipped")
        self.assertEqual(
            classify_focused_result(
                0,
                "Passed: 8\nSkipped: 0\n# pass 1\n# skipped 0\n",
            ),
            "pass",
        )


if __name__ == "__main__":
    unittest.main()
