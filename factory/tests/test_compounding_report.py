import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from compounding_report import CompoundingEngine


class CompoundingEngineTests(unittest.TestCase):
    def test_only_repeated_or_high_severity_signals_become_suggestions(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = CompoundingEngine(Path(directory))
            engine.record("review", "missing-empty-state", "medium", "run/a#1", "Empty state absent")
            self.assertEqual(engine.build_report()["suggestions"], [])
            engine.record("review", "missing-empty-state", "medium", "run/b#2", "Same finding")
            engine.record("qa", "false-green", "high", "run/c#3", "Focused test was already green")

            report = engine.build_report()
            self.assertEqual(len(report["suggestions"]), 2)
            self.assertFalse(report["authority"]["may_edit_charter"])
            for suggestion in report["suggestions"]:
                self.assertGreaterEqual(len(suggestion["evidence"]), 1)
                self.assertTrue(suggestion["expected_effect"])
                self.assertTrue(suggestion["possible_regression"])
                self.assertTrue(suggestion["verification_plan"])

    def test_usage_is_unavailable_when_adapter_does_not_report_it(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = CompoundingEngine(Path(directory))
            engine.record_usage("codex", {})
            engine.record_usage("claude", {
                "model": "claude-example", "input_tokens": 10,
                "output_tokens": 20, "duration_seconds": 1.2, "cost": 0.01,
                "trustworthy": True,
            })
            report = engine.build_report()
            self.assertEqual(report["usage"]["codex"]["input_tokens"], "unavailable")
            self.assertEqual(report["usage"]["claude"]["input_tokens"], 10)

    def test_human_rejection_does_not_edit_delivery_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            charter = repo / "factory.charter.toml"
            charter.write_text("merge_authority = 'human'\n")
            engine = CompoundingEngine(repo)
            engine.record("monitor", "flaky-gate", "high", "monitor/1", "Gate flakes")
            suggestion = engine.build_report()["suggestions"][0]
            decision = engine.decide(suggestion["id"], "rejected", "Not representative")

            self.assertEqual(decision["decision"], "rejected")
            self.assertEqual(charter.read_text(), "merge_authority = 'human'\n")

    def test_report_collects_existing_run_and_monitor_evidence_idempotently(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            runtime = repo / ".factory"
            runtime.mkdir()
            (runtime / "state.json").write_text(json.dumps({
                "run_id": "run-7",
                "tickets": [
                    {
                        "number": 1,
                        "failure": "Acceptance test already passes before implementation",
                        "metrics": {"retry_count": 1},
                    },
                    {
                        "number": 2,
                        "failure": "Acceptance test was already green",
                        "metrics": {"retry_count": 2},
                    },
                ],
            }))
            monitor = runtime / "monitor"
            monitor.mkdir()
            (monitor / "report.json").write_text(json.dumps({
                "findings": [{
                    "kind": "stale-review",
                    "severity": "warning",
                    "message": "Review queue is stale",
                    "path": "factory/state",
                }],
            }))
            engine = CompoundingEngine(repo)

            first = engine.build_report()
            second = engine.build_report()

            self.assertEqual(first["observation_count"], second["observation_count"])
            signals = {item["signal"] for item in second["suggestions"]}
            self.assertIn("acceptance-test-already-green", signals)
            self.assertIn("ticket-retry", signals)


if __name__ == "__main__":
    unittest.main()
