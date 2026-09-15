import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).parents[1]))

from code_review import MAX_TEXT, CodeReviewError, CodeReviewTextTooLong, extract_review, render_review_comment, validate_review, validate_review_repair
from factory_charter import FactoryCharter
from orchestrator import Factory
from project_contract import ProjectContract


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=True,
    ).stdout.strip()


class CodeReviewTests(unittest.TestCase):
    def test_live_smoke_review_fixture_requests_one_changed_path_rework(self):
        with tempfile.TemporaryDirectory() as directory:
            prompt = Path(directory) / "review.md"
            prompt.write_text(
                "## Ticket\nfactory-release-smoke:review-rework\n\n"
                "## Changed paths\n\n- `demo-app/app.py`\n- `demo-app/tests/test_ticket_9.py`\n\n"
                "## Recorded gates\n\n- tests: PASS\n"
            )
            script = Path(__file__).parents[1] / "mock_review_agent.py"
            first = subprocess.run(
                [sys.executable, str(script), "9", str(prompt), "--attempt", "1"],
                text=True, capture_output=True, check=True,
            )
            second = subprocess.run(
                [sys.executable, str(script), "9", str(prompt), "--attempt", "2"],
                text=True, capture_output=True, check=True,
            )

            requested = json.loads(first.stdout)
            approved = json.loads(second.stdout)
            self.assertEqual(requested["decision"], "REQUEST_CHANGES")
            self.assertEqual(requested["findings"][0]["path"], "demo-app/app.py")
            self.assertEqual(approved["decision"], "APPROVE")

    def test_extracts_and_validates_last_json_result(self):
        raw = extract_review('progress\n{"ignored":true}\n{"schema_version":2,"decision":"APPROVE","summary":"Ready.","findings":[]}')
        review = validate_review(raw, {"demo-app/app.py"})
        self.assertEqual(review["decision"], "APPROVE")

    def test_block_requires_blocking_finding_on_changed_path(self):
        payload = {
            "schema_version": 2,
            "decision": "REQUEST_CHANGES",
            "summary": "A regression remains.",
            "findings": [{
                "severity": "blocking",
                "path": "demo-app/app.py",
                "line": 12,
                "message": "The error branch returns a successful status.",
            }],
        }
        review = validate_review(
            extract_review("adapter output\n" + json.dumps(payload)), {"demo-app/app.py"},
        )
        self.assertEqual(review["findings"][0]["line"], 12)

    def test_rejects_unchanged_or_traversing_path(self):
        for path in ("README.md", "../demo-app/app.py"):
            with self.subTest(path=path), self.assertRaises(CodeReviewError):
                validate_review({
                    "schema_version": 2,
                    "decision": "REQUEST_CHANGES",
                    "summary": "Unsafe finding.",
                    "findings": [{
                        "severity": "blocking", "path": path, "line": None, "message": "Problem.",
                    }],
                }, {"demo-app/app.py"})

    def test_approve_rejects_any_comment(self):
        with self.assertRaisesRegex(CodeReviewError, "APPROVE"):
            validate_review({
                "schema_version": 2,
                "decision": "APPROVE",
                "summary": "Contradictory.",
                "findings": [{
                    "severity": "blocking", "path": "app.py", "line": 1, "message": "Problem.",
                }],
            }, {"app.py"})

    def test_renders_supervisor_merge_boundary(self):
        comment = render_review_comment({
            "decision": "APPROVE", "summary": "Ready for @team.", "findings": [],
        }, 7, 2)
        self.assertIn("Factory Code Review · APPROVE", comment)
        self.assertIn("Supervisor may recommend only this approved revision", comment)
        self.assertIn("human exact-revision merge", comment)
        self.assertNotIn("@team", comment)

    def test_orchestrator_records_blocking_review_without_mutating_candidate(self):
        self.check_orchestrator_review()

    def test_overlong_review_is_automatically_repaired_on_same_candidate(self):
        self.check_orchestrator_review(overlong=True)

    def test_overlong_approval_is_repaired_without_changing_verdict(self):
        self.check_orchestrator_review(overlong=True, approve=True)

    def test_failed_text_repair_is_bounded_and_keeps_original(self):
        self.check_orchestrator_review(overlong=True, repair_fails=True)

    def test_charter_can_disable_text_repair(self):
        self.check_orchestrator_review(overlong=True, retries=0)

    def test_candidate_mutation_before_or_during_repair_fails_closed(self):
        for call in (1, 2):
            with self.subTest(call=call):
                self.check_orchestrator_review(overlong=True, mutate_on_call=call)

    def test_repair_cannot_drop_findings_change_verdict_or_retarget(self):
        original = {"schema_version": 2, "decision": "REQUEST_CHANGES", "summary": "Short summary.",
                    "findings": [{"severity": "blocking", "path": "app.py", "line": 1,
                                  "message": "Long. " * (MAX_TEXT // len("Long. ") + 1)}]}
        good = json.loads(json.dumps(original))
        good["findings"][0]["message"] = "Fix the regression."
        self.assertEqual(validate_review_repair(original, good, {"app.py", "other.py"}), good)
        for change in ("drop", "approve", "path", "line", "severity", "summary"):
            value = json.loads(json.dumps(good))
            if change in {"drop", "approve"}:
                value["findings"] = []
                if change == "approve":
                    value["decision"] = "APPROVE"
            elif change == "summary":
                value["summary"] = "Changed the conclusion."
            else:
                value["findings"][0][change] = {"path": "other.py", "line": 2, "severity": "note"}[change]
            with self.subTest(change=change), self.assertRaises(CodeReviewError):
                validate_review_repair(original, value, {"app.py", "other.py"})

    def test_text_limit_does_not_hide_other_invalid_fields(self):
        value = {"schema_version": 2, "decision": "REQUEST_CHANGES", "summary": "x" * (MAX_TEXT + 1),
                 "findings": [{"severity": "blocking", "path": "../unsafe", "line": 1, "message": "Problem"}]}
        with self.assertRaises(CodeReviewError) as raised:
            validate_review(value, {"app.py"})
        self.assertNotIsInstance(raised.exception, CodeReviewTextTooLong)
        value.update(decision="APPROVE", findings=[], summary="x" * MAX_TEXT)
        self.assertEqual(validate_review(value, set())["summary"], "x" * MAX_TEXT)
        value["summary"] += "x"
        with self.assertRaises(CodeReviewTextTooLong):
            validate_review(value, set())

    def check_orchestrator_review(self, overlong=False, approve=False, repair_fails=False,
                                  retries=2, mutate_on_call=0):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            source = Path(__file__).parents[1]
            (repo / "factory").mkdir()
            for name in ("roles.json", "policy.json"):
                shutil.copy2(source / name, repo / "factory" / name)
            (repo / ".gitignore").write_text(".factory/\n")
            git(repo, "init", "-q", "-b", "main")
            git(repo, "config", "user.name", "Factory Test")
            git(repo, "config", "user.email", "factory@example.test")
            (repo / "app.py").write_text("value = 1\n")
            project = ProjectContract.detect(repo)
            project.write()
            charter = FactoryCharter.draft(repo, project)
            charter.write()
            charter.approve()
            git(repo, "add", ".")
            git(repo, "commit", "-qm", "base")
            base = git(repo, "rev-parse", "HEAD")
            (repo / "app.py").write_text("value = 2\n")
            git(repo, "add", "app.py")
            git(repo, "commit", "-qm", "candidate")

            factory = Factory.__new__(Factory)
            factory.repo = repo
            factory.review_agent = "reviewer"
            factory.args = SimpleNamespace(scenario="tv", mock=False)
            factory.record_receipt = mock.Mock()
            factory.charter = replace(charter, max_retries=retries)
            factory.verify_qa_tests_unchanged = mock.Mock(return_value="")
            response = json.dumps({
                "schema_version": 2,
                "decision": "REQUEST_CHANGES",
                "summary": "The candidate changes the public value unexpectedly.",
                "findings": [{
                    "severity": "blocking",
                    "path": "app.py",
                    "line": 1,
                    "message": "Preserve the documented value contract.",
                }],
            })
            if approve:
                value = json.loads(response)
                value.update(decision="APPROVE", findings=[])
                response = json.dumps(value)
            original = json.loads(response)
            def past_limit(sentence: str) -> str:
                return sentence * (MAX_TEXT // len(sentence) + 1)
            original["summary"] = past_limit("Detailed review. ")
            if original["findings"]:
                original["findings"][0]["message"] = past_limit("Preserve the documented value contract. ")
            responses = iter([(0, json.dumps(original)), (0, json.dumps(original) if repair_fails else response)] if overlong else [(0, response)])
            def invoke(*args):
                if factory.run_adapter.call_count == mutate_on_call:
                    (repo / "app.py").write_text("unauthorized = True\n")
                return next(responses)
            factory.run_adapter = mock.Mock(side_effect=invoke)
            ticket = {
                "number": 4, "title": "Preserve value", "body": "## Spec\nKeep the value stable.",
                "attempt": 1, "gate_results": [], "qa_tests": {}, "current_log": "",
            }

            failure = factory.run_code_review(ticket, repo, base, "https://example.test/pull/4")

            invalid = repair_fails or retries == 0 or mutate_on_call
            if invalid:
                self.assertTrue(failure)
                self.assertIsNone(ticket["code_review"]["result"])
                self.assertEqual(ticket["code_review"]["status"], "invalid")
                if mutate_on_call:
                    self.assertIn("modified the worktree", failure)
            elif approve:
                self.assertEqual(failure, "")
                self.assertEqual(ticket["code_review"]["result"]["decision"], "APPROVE")
            else:
                self.assertIn("Code Review requested changes", failure)
                self.assertEqual(ticket["code_review"]["result"]["decision"], "REQUEST_CHANGES")
            self.assertTrue((repo / ticket["code_review"]["artifact"]).is_file())
            factory.record_receipt.assert_called_once()
            if not mutate_on_call:
                self.assertEqual(git(repo, "status", "--porcelain"), "")
            if overlong:
                self.assertEqual(factory.run_adapter.call_count, 1 if retries == 0 or mutate_on_call == 1 else 2)
                self.assertEqual(ticket["attempt"], 1)
                recovery = ticket["code_review"]["recovery"]
                if mutate_on_call == 1:
                    self.assertEqual(recovery, {})
                    return
                self.assertEqual(recovery["status"], "failed" if invalid else "repaired")
                saved = json.loads((repo / recovery["original_response"]).read_text())
                self.assertEqual(saved, original)
                if retries == 0:
                    self.assertEqual(recovery["attempts"], 0)
                    return
                repair_call = factory.run_adapter.call_args_list[1].args
                self.assertEqual(repair_call[2], repo)
                self.assertIn(str(MAX_TEXT), repair_call[3].read_text())
                self.assertIn(ticket["code_review"]["head"], repair_call[3].read_text())


if __name__ == "__main__":
    unittest.main()
