import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parents[1]))
from orchestrator import Factory
from qa_approval import pending_approval, queue_approval


class QaApprovalTests(unittest.TestCase):
    def ticket(self):
        return {"number": 2, "status": "QA Review", "qa_commit": "reviewed",
                "qa_tests": {"tests/test_app.py": "hash"}, "qa_evidence": {"red": "proof"},
                "body": "Original criteria", "spec_sha256": "spec"}

    def test_approval_is_durable_idempotent_and_bound_to_reviewed_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            ticket = self.ticket()
            for _ in range(2):
                queue_approval(repo, ticket)
                self.assertTrue(pending_approval(repo, ticket))
            self.assertFalse((repo / ".factory/state.json").exists())
            self.assertEqual(len(list((repo / ".factory/qa-approvals").iterdir())), 1)
            for field in ("qa_commit", "qa_tests", "qa_evidence", "body", "spec_sha256", "status"):
                changed = copy.deepcopy(ticket)
                changed[field] = "changed"
                with self.subTest(field=field):
                    self.assertIsNone(pending_approval(repo, changed))

    def test_only_runner_consumes_matching_approval_at_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            for stale in (False, True):
                with self.subTest(stale=stale):
                    ticket = self.ticket()
                    queue_approval(repo, ticket)
                    factory = Factory.__new__(Factory)
                    factory.repo, factory.tickets = repo, {2: ticket}
                    factory.verify_qa_tests_unchanged = mock.Mock(return_value="")
                    factory.transition = mock.Mock()
                    factory._sync_store = mock.Mock()
                    if stale:
                        ticket["qa_commit"] = "replacement"
                    factory.apply_qa_approvals()
                    if stale:
                        factory.transition.assert_not_called()
                        self.assertFalse(ticket.get("qa_approved"))
                        self.assertIn("approve again", ticket["failure"])
                    else:
                        factory.transition.assert_called_once_with(ticket, "Ready", "Human approved independent Acceptance Tests")
                        self.assertTrue(ticket["qa_approved"])
                    self.assertFalse((repo / ".factory/qa-approvals/2").exists())

    def test_unversioned_or_partial_markers_are_not_approvals(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            marker = repo / ".factory/qa-approvals/2"
            marker.parent.mkdir(parents=True)
            for content in ("old timestamp\n", "{", "null", json.dumps({"schema_version": 1})):
                marker.write_text(content)
                self.assertIsNone(pending_approval(repo, self.ticket()))
