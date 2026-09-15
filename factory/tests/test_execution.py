import contextlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).parents[1]))
from execution import execution_lock
from orchestrator import FactoryCLI


class ExecutionTests(unittest.TestCase):
    def test_approval_submission_does_not_wait_for_busy_executor(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            cli = FactoryCLI(SimpleNamespace(command="approve-tests", issue=1, yes=True), repo, {})
            with mock.patch("orchestrator.execution_lock", side_effect=ValueError("Executor busy")), \
                    mock.patch.object(cli, "_planning_commands") as approve:
                cli.run()
                approve.assert_called_once()

    def test_companion_waits_for_wave_and_lock_releases_after_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            script = (
                "import sys; from pathlib import Path; "
                f"sys.path.insert(0, {str(Path(__file__).parents[1])!r}); "
                "from execution import execution_lock\n"
                "with execution_lock(Path(sys.argv[1])): print('acquired', flush=True)\n"
            )
            with self.assertRaisesRegex(RuntimeError, "worker failed"):
                with execution_lock(repo):
                    child = subprocess.Popen(
                        [sys.executable, "-c", script, str(repo)],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                    )
                    self.assertIn("No changes have been applied", child.stdout.readline())
                    self.assertIsNone(child.poll())
                    raise RuntimeError("worker failed")
            try:
                output, error = child.communicate(timeout=10)
                self.assertEqual(child.returncode, 0, error)
                self.assertEqual(output.strip(), "acquired")
            finally:
                if child.poll() is None:
                    child.kill()
                    child.communicate()

    def test_second_runner_and_reset_are_rejected_but_status_stays_readable(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            with execution_lock(repo, runner=True), execution_lock(repo):
                with self.assertRaisesRegex(ValueError, "already owns"):
                    with execution_lock(repo, runner=True):
                        self.fail("A second runner acquired ownership")
                cli = FactoryCLI(SimpleNamespace(command="reset"), repo, {})
                with mock.patch.object(cli, "_ticket_commands") as reset:
                    with self.assertRaisesRegex(ValueError, "already owns"):
                        cli.run()
                    reset.assert_not_called()
                for command in ("status", "monitor"):
                    cli = FactoryCLI(SimpleNamespace(command=command), repo, {})
                    with mock.patch.object(cli, "_evidence_commands") as inspect:
                        cli.run()
                        inspect.assert_called_once()

    def test_stale_ticket_action_is_not_applied_after_waiting(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            state = repo / ".factory/state.json"
            state.parent.mkdir()
            state.write_text(json.dumps({"tickets": [{"number": 1, "qa_commit": "old"}]}))

            @contextlib.contextmanager
            def next_checkpoint(*args, **kwargs):
                state.write_text(json.dumps({"tickets": [{"number": 1, "qa_commit": "new"}]}))
                yield

            cli = FactoryCLI(SimpleNamespace(command="request-test-changes", issue=1), repo, {})
            with mock.patch("orchestrator.execution_lock", next_checkpoint), \
                    mock.patch.object(cli, "_planning_commands") as approve:
                with self.assertRaisesRegex(ValueError, "revision changed"):
                    cli.run()
                approve.assert_not_called()


if __name__ == "__main__":
    unittest.main()
