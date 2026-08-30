import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from intake_evidence import IntakeEvaluator, IntakeError


class IntakeEvaluatorTests(unittest.TestCase):
    def test_feature_feedback_proposes_planning_and_never_dispatches(self):
        with tempfile.TemporaryDirectory() as directory:
            evaluator = IntakeEvaluator(Path(directory))
            proposal = evaluator.evaluate({
                "source_ref": "github://org/repo/issues/12",
                "kind": "feature",
                "title": "Let cooks save recipes",
                "description": "Signed-in cooks need a saved recipes collection.",
                "acceptance_criteria": ["A cook can save and remove a recipe."],
            })

            self.assertEqual(proposal["classification"], "READY_TO_PLAN")
            self.assertFalse(proposal["may_dispatch"])
            self.assertEqual(proposal["decision_authority"], "human")
            self.assertTrue(proposal["case_id"])

    def test_bug_requires_latest_revision_environment_and_causal_reproduction(self):
        with tempfile.TemporaryDirectory() as directory:
            evaluator = IntakeEvaluator(Path(directory))
            missing = evaluator.evaluate({
                "kind": "bug", "title": "Search crashes", "description": "Crash",
            })
            self.assertEqual(missing["classification"], "NEEDS_INFORMATION")
            self.assertIn("affected_revision", missing["missing"])

            ready = evaluator.evaluate({
                "kind": "bug",
                "title": "Search crashes",
                "description": "Submitting an empty ingredient crashes search.",
                "affected_revision": "a" * 40,
                "latest_revision": "b" * 40,
                "environment": "python 3.12, macOS",
                "reproduction": {
                    "command": "python -m pytest tests/test_search.py -q",
                    "exit_code": 1,
                    "failure_kind": "product_failure",
                    "bounded_output": "AssertionError: expected validation message",
                    "reviewed": True,
                },
                "acceptance_criteria": ["Empty input shows a validation message."],
                "file_ownership": ["src/search.py", "tests/test_search.py"],
                "duplicate_candidates": [{"ref": "#4", "confidence": 0.42}],
            })
            self.assertEqual(ready["classification"], "READY_TO_IMPLEMENT")
            self.assertFalse(ready["may_dispatch"])
            self.assertTrue(ready["human_review_required"])

    def test_collection_and_environment_failures_are_not_reproductions(self):
        with tempfile.TemporaryDirectory() as directory:
            evaluator = IntakeEvaluator(Path(directory))
            for failure_kind in ("collection_error", "environment_failure", "unrelated_failure"):
                request = {
                    "kind": "bug", "title": "Failure", "description": "Observed",
                    "affected_revision": "a", "latest_revision": "b",
                    "environment": "test",
                    "reproduction": {
                        "command": "pytest", "exit_code": 1,
                        "failure_kind": failure_kind, "bounded_output": "failed",
                        "reviewed": True,
                    },
                }
                proposal = evaluator.evaluate(request)
                self.assertNotEqual(proposal["classification"], "READY_TO_IMPLEMENT")

    def test_human_correction_preserves_original_classification(self):
        with tempfile.TemporaryDirectory() as directory:
            evaluator = IntakeEvaluator(Path(directory))
            proposal = evaluator.evaluate({
                "kind": "feature", "title": "Export", "description": "Export recipes",
            })
            correction = evaluator.correct(
                proposal["case_id"], "WAIT", "Legal review is required.",
            )

            self.assertEqual(correction["original_classification"], "READY_TO_PLAN")
            self.assertEqual(correction["classification"], "WAIT")
            cases = [json.loads(line) for line in evaluator.case_path.read_text().splitlines()]
            self.assertEqual(len(cases), 2)

    def test_rejects_untrusted_reproduction_execution_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            evaluator = IntakeEvaluator(Path(directory))
            with self.assertRaisesRegex(IntakeError, "reviewed"):
                evaluator.evaluate({
                    "kind": "bug", "title": "Attached script", "description": "Run it",
                    "affected_revision": "a", "latest_revision": "b", "environment": "x",
                    "reproduction": {
                        "command": "./attached.sh", "exit_code": 1,
                        "failure_kind": "product_failure", "reviewed": False,
                    },
                })


if __name__ == "__main__":
    unittest.main()
