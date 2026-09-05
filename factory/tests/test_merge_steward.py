import sys
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from merge_steward import MergeSteward
from orchestrator import steward_synchronize_ticket, worktree_path


class MergeStewardTests(unittest.TestCase):
    def setUp(self):
        self.steward = MergeSteward()
        self.ready = {
            "candidate_head": "a" * 40,
            "reviewed_head": "a" * 40,
            "candidate_base": "b" * 40,
            "default_branch_head": "b" * 40,
            "required_gates": [{"name": "tests", "status": "passed", "revision": "a" * 40}],
            "review_decision": "approved",
            "unresolved_comments": [],
            "protected_paths_changed": False,
            "acceptance_evidence_sha256": "c" * 64,
            "reviewed_acceptance_evidence_sha256": "c" * 64,
            "branch_protection": "passed",
        }

    def test_ready_candidate_is_presented_for_human_merge_and_never_merged(self):
        result = self.steward.assess(self.ready)
        self.assertEqual(result["state"], "ready-for-human-merge")
        self.assertEqual(result["merge_authority"], "human")
        self.assertNotIn("merge", result["allowed_actions"])

    def test_base_change_requests_sync_and_revokes_revision_bound_approval(self):
        result = self.steward.assess({
            **self.ready, "default_branch_head": "d" * 40,
        })
        self.assertEqual(result["state"], "steward-updating")
        self.assertEqual(result["allowed_actions"], ["synchronize-base"])
        self.assertTrue(result["authorization_revoked"])
        self.assertEqual(result["required_after_change"], ["required-gates", "code-review"])

    def test_unreviewed_head_comments_and_evidence_changes_require_human_decision(self):
        cases = [
            {"candidate_head": "d" * 40},
            {"unresolved_comments": ["Please simplify this branch"]},
            {"protected_paths_changed": True},
            {"acceptance_evidence_sha256": "e" * 64},
            {"branch_protection": "failed"},
        ]
        for changed in cases:
            with self.subTest(changed=changed):
                result = self.steward.assess({**self.ready, **changed})
                self.assertEqual(result["state"], "human-decision-required")
                self.assertFalse(result["may_merge"])

    def test_sync_changes_the_candidate_then_revokes_review_for_direct_reverification(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            remote = root / "remote.git"
            repo = root / "app"
            subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
            repo.mkdir()
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "factory@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Factory Test"], cwd=repo, check=True)
            (repo / "base.txt").write_text("base\n")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
            subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=repo, check=True)
            subprocess.run(["git", "push", "-qu", "origin", "main"], cwd=repo, check=True)
            candidate = worktree_path(repo, 7)
            subprocess.run(["git", "worktree", "add", "-qb", "factory/7-feature", str(candidate), "main"], cwd=repo, check=True)
            (candidate / "feature.txt").write_text("feature\n")
            subprocess.run(["git", "add", "."], cwd=candidate, check=True)
            subprocess.run(["git", "commit", "-qm", "feature"], cwd=candidate, check=True)
            old_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=candidate, text=True).strip()
            subprocess.run(["git", "push", "-qu", "origin", "factory/7-feature"], cwd=candidate, check=True)
            (repo / "upstream.txt").write_text("upstream\n")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "upstream"], cwd=repo, check=True)
            subprocess.run(["git", "push", "-q", "origin", "main"], cwd=repo, check=True)
            state = repo / ".factory/state.json"
            state.parent.mkdir(parents=True)
            state.write_text(json.dumps({"tickets": [{
                "number": 7, "title": "Feature", "status": "In Review",
                "branch": "factory/7-feature", "base_sha": old_head,
                "qa_commit": old_head, "qa_tests": {"tests/t.py": "hash"},
                "qa_approved": True, "approved_head": old_head,
                "merge_authority": "human", "code_review": {"head": old_head},
                "history": [],
            }]}))

            result = steward_synchronize_ticket(repo, 7, assume_yes=True)
            saved = json.loads(state.read_text())["tickets"][0]

            self.assertEqual(result["state"], "steward-updating")
            self.assertNotEqual(result["candidate_head"], old_head)
            self.assertEqual(saved["status"], "Blocked")
            self.assertEqual(saved["reverify_candidate"], result["candidate_head"])
            self.assertEqual(saved["approved_head"], "")
            self.assertTrue((candidate / "feature.txt").is_file())
            self.assertTrue((candidate / "upstream.txt").is_file())

            # A local Rehearsal has no origin, and a human edit invalidates an
            # approval even when the candidate already contains the base.
            subprocess.run(["git", "remote", "remove", "origin"], cwd=repo, check=True)
            saved.update(status="In Review", approved_head=result["candidate_head"])
            state.write_text(json.dumps({"mode": "mock", "tickets": [saved]}))
            (candidate / "feature.txt").write_text("reviewed correction\n")
            subprocess.run(["git", "add", "feature.txt"], cwd=candidate, check=True)
            subprocess.run(["git", "commit", "-qm", "human correction"], cwd=candidate, check=True)
            local = steward_synchronize_ticket(repo, 7, assume_yes=True)
            self.assertEqual(local["state"], "steward-updating")
            self.assertEqual(json.loads(state.read_text())["tickets"][0]["approved_head"], "")


if __name__ == "__main__":
    unittest.main()
