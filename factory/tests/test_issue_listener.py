import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from issue_listener import (
    INTAKE_MARKER,
    RepositoryIssueListener,
    factory_issue_kind,
    render_intake_body,
)


class RepositoryIssueListenerTests(unittest.TestCase):
    def test_first_start_baselines_existing_issues_and_resume_admits_only_new_ones(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            existing = [{"number": 1}, {"number": 4}]
            listener = RepositoryIssueListener(repo, "attendee/product")

            self.assertTrue(listener.begin(existing))
            self.assertEqual(listener.candidates([*existing, {"number": 5}]), [{"number": 5}])
            listener.acknowledge(
                5,
                outcome="admitted",
                detail="Admitted for implementation.",
            )

            resumed = RepositoryIssueListener(repo, "attendee/product")
            self.assertFalse(resumed.begin([*existing, {"number": 5}]))
            self.assertEqual(
                resumed.candidates([*existing, {"number": 5}, {"number": 8}]),
                [{"number": 8}],
            )
            snapshot = resumed.snapshot()
            self.assertEqual(snapshot["baseline_count"], 2)
            self.assertEqual(snapshot["seen_count"], 3)
            self.assertEqual(snapshot["admitted_count"], 1)
            self.assertEqual(snapshot["ignored_count"], 0)
            self.assertNotIn("seen", snapshot)

    def test_listener_state_is_scoped_to_the_connected_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            first = RepositoryIssueListener(repo, "attendee/one")
            first.begin([{"number": 9}])

            second = RepositoryIssueListener(repo, "attendee/two")

            self.assertTrue(second.begin([{"number": 2}]))
            saved = json.loads((repo / ".factory/issue-listener.json").read_text())
            self.assertEqual(saved["repository"], "attendee/two")
            self.assertEqual(saved["seen"], [2])

    def test_factory_markers_exclude_managed_issues(self):
        self.assertEqual(factory_issue_kind("<!-- factory-plan:abc:T1 -->"), "plan")
        self.assertEqual(factory_issue_kind("<!-- factory-monitor:v1 -->"), "monitor")
        self.assertEqual(factory_issue_kind(INTAKE_MARKER), "intake")
        self.assertEqual(
            factory_issue_kind(
                "<!-- factory-governance:v1;profile=standard;"
                f"charter={'a' * 64};merge=human -->"
            ),
            "governance",
        )
        self.assertEqual(factory_issue_kind("Please fix the search result."), "")

    def test_intake_rendering_preserves_user_text_and_is_idempotent(self):
        governance = (
            "<!-- factory-governance:v1;profile=standard;"
            f"charter={'a' * 64};merge=human -->"
        )

        first = render_intake_body("Keep this request exactly.", governance)
        second = render_intake_body(first, governance)

        self.assertTrue(first.startswith("Keep this request exactly."))
        self.assertEqual(first, second)
        self.assertEqual(first.count(INTAKE_MARKER), 1)
        self.assertEqual(first.count(governance), 1)


if __name__ == "__main__":
    unittest.main()
