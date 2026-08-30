import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from orchestrator import parser


class InterfaceCliTests(unittest.TestCase):
    def test_parser_exposes_governed_intake_and_compounding(self):
        intake = parser().parse_args([
            "intake", "evaluate", "feedback.json", "--repo", "/tmp/app", "--json",
        ])
        self.assertEqual(intake.command, "intake")
        self.assertEqual(intake.intake_action, "evaluate")
        self.assertTrue(intake.as_json)
        approval = parser().parse_args([
            "approve-intake", "12", "--case", "case-12",
            "--reason", "Reviewed the reproduction evidence", "--yes",
        ])
        self.assertEqual(approval.issue, 12)
        self.assertTrue(approval.yes)

        improve = parser().parse_args([
            "improve", "report", "--repo", "/tmp/app", "--json",
        ])
        self.assertEqual(improve.improve_action, "report")

    def test_parser_exposes_steward_trigger_and_workspace_contract(self):
        steward = parser().parse_args(["steward", "12", "--json"])
        self.assertEqual(steward.issue, 12)
        trigger = parser().parse_args([
            "trigger", "webhook", "delivery-1", "payload.json", "--authenticated", "--json",
        ])
        self.assertEqual(trigger.source, "webhook")
        self.assertTrue(trigger.authenticated)
        workspace = parser().parse_args(["workspace-check", "--json"])
        self.assertEqual(workspace.command, "workspace-check")


if __name__ == "__main__":
    unittest.main()
