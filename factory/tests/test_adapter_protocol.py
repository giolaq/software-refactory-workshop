import json
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parents[1]))

from adapter_protocol import (
    AdapterEventJournal,
    AdapterProtocolError,
    build_assignment,
    conformance_report,
    validate_result,
)
from adapter_capabilities import load_capabilities
from orchestrator import Factory


class AdapterProtocolTests(unittest.TestCase):
    def test_assignment_records_factory_invariants_without_embedding_prompt_text(self):
        assignment = build_assignment(
            run_id="run-1",
            role="implementation",
            ticket=7,
            attempt=2,
            repository="/workspace/product",
            working_root="/workspace/product/.factory/worktrees/ticket-7",
            prompt_ref=".factory/prompts/7-attempt2.md",
            profile="standard",
            charter_sha256="a" * 64,
            policy_hashes={"workflow": "b" * 64},
            requested_capabilities=["workspace-write", "progress-events"],
        )

        self.assertEqual(assignment["schema_version"], 1)
        self.assertEqual(assignment["ticket"], 7)
        self.assertEqual(assignment["prompt_ref"], ".factory/prompts/7-attempt2.md")
        self.assertNotIn("prompt", assignment)

    def test_event_journal_synthesizes_legacy_lifecycle_and_accepts_prefixed_events(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            journal = AdapterEventJournal(path, run_id="run-1", role="qa", ticket=4)

            journal.started(adapter="legacy")
            self.assertIsNone(journal.observe("ordinary legacy output\n"))
            accepted = journal.observe(
                'FACTORY_EVENT {"schema_version":1,"type":"tool_activity",'
                '"message":"Running focused tests","tool":"pytest"}\n'
            )
            journal.finished(exit_code=0, artifacts=["tests/test_ticket_4.py"])

            events = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual([event["type"] for event in events], [
                "started", "tool_activity", "completed",
            ])
            self.assertEqual(accepted["tool"], "pytest")
            self.assertEqual(events[-1]["artifacts"], ["tests/test_ticket_4.py"])

    def test_event_journal_rejects_unbounded_or_unknown_protocol_events(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = AdapterEventJournal(
                Path(directory) / "events.jsonl",
                run_id="run-1",
                role="implementation",
                ticket=1,
            )
            journal.started(adapter="protocol")
            with self.assertRaisesRegex(AdapterProtocolError, "event type"):
                journal.observe(
                    'FACTORY_EVENT {"schema_version":1,"type":"thought",'
                    '"message":"not an exposed event"}'
                )

    def test_event_journal_rejects_events_after_a_terminal_transition(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = AdapterEventJournal(
                Path(directory) / "events.jsonl",
                run_id="run-1", role="implementation", ticket=1,
            )
            journal.started(adapter="protocol")
            journal.observe(
                'FACTORY_EVENT {"schema_version":1,"type":"completed"}'
            )
            with self.assertRaisesRegex(AdapterProtocolError, "terminal"):
                journal.observe(
                    'FACTORY_EVENT {"schema_version":1,"type":"status","message":"late"}'
                )

    def test_adapter_terminal_event_must_match_the_process_outcome(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = AdapterEventJournal(
                Path(directory) / "events.jsonl",
                run_id="run-1", role="implementation", ticket=1,
            )
            journal.started(adapter="protocol")
            journal.observe(
                'FACTORY_EVENT {"schema_version":1,"type":"completed"}'
            )
            with self.assertRaisesRegex(AdapterProtocolError, "process outcome"):
                journal.finished(exit_code=1)

    def test_final_result_is_strict_bounded_and_revision_aware(self):
        result = validate_result({
            "schema_version": 1,
            "outcome": "success",
            "output_revisions": {"candidate": "a" * 40},
            "artifacts": ["src/search.py"],
            "verification_claims": ["Focused tests passed"],
            "unresolved_risks": [],
            "usage": {"input_tokens": 12, "output_tokens": 4},
        })
        self.assertEqual(result["outcome"], "success")
        with self.assertRaisesRegex(AdapterProtocolError, "unsupported fields"):
            validate_result({
                "schema_version": 1, "outcome": "success", "reasoning": "private",
                "output_revisions": {}, "artifacts": [],
                "verification_claims": [], "unresolved_risks": [],
            })

        with self.assertRaisesRegex(AdapterProtocolError, "bounded"):
            validate_result({
                "schema_version": 1, "outcome": "success",
                "output_revisions": {}, "artifacts": ["x" * 1001],
                "verification_claims": [], "unresolved_risks": [],
            })

        with self.assertRaisesRegex(AdapterProtocolError, "finite"):
            validate_result({
                "schema_version": 1, "outcome": "success",
                "output_revisions": {}, "artifacts": [],
                "verification_claims": [], "unresolved_risks": [],
                "usage": {"cost": float("inf")},
            })

    def test_event_journal_rejects_unbounded_event_message(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = AdapterEventJournal(
                Path(directory) / "events.jsonl",
                run_id="run-1", role="implementation", ticket=1,
            )
            journal.started(adapter="protocol")
            with self.assertRaisesRegex(AdapterProtocolError, "bounded"):
                journal.observe(
                    "FACTORY_EVENT " + json.dumps({
                        "schema_version": 1,
                        "type": "status",
                        "message": "x" * 1001,
                    })
                )

    def test_conformance_report_preserves_legacy_commands_and_checks_protocol_features(self):
        legacy = conformance_report(
            "legacy",
            "legacy-agent --prompt {prompt}",
            {"protocol_version": 1, "features": []},
        )
        protocol = conformance_report(
            "structured",
            "structured-agent --assignment {assignment} --prompt {prompt}",
            {
                "protocol_version": 1,
                "features": ["progress-events", "usage-telemetry"],
            },
        )

        self.assertTrue(legacy["compatible"])
        self.assertEqual(legacy["mode"], "legacy-command")
        self.assertTrue(protocol["compatible"])
        self.assertEqual(protocol["mode"], "protocol-v1")
        self.assertIn("progress-events", protocol["features"])

        invalid = conformance_report(
            "broken",
            "broken-agent --prompt {prompt}",
            {"protocol_version": 1, "features": ["progress-events"]},
        )
        self.assertFalse(invalid["compatible"])
        self.assertIn("{assignment}", invalid["errors"][0])

    def test_factory_run_adapter_publishes_assignment_and_normalized_events(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            script = repo / "adapter.sh"
            script.write_text(
                "#!/bin/sh\n"
                "printf '%s\\n' 'working'\n"
                "printf '%s\\n' 'FACTORY_EVENT {\"schema_version\":1,\"type\":\"status\",\"message\":\"Patch prepared\"}'\n"
            )
            script.chmod(0o755)
            prompt = repo / ".factory/prompts/7.md"
            prompt.parent.mkdir(parents=True)
            prompt.write_text("Implement ticket 7.\n")
            factory = Factory.__new__(Factory)
            factory.repo = repo
            factory.run_id = "run-1"
            factory.profile_name = "standard"
            factory.governance = {"charter_sha256": "a" * 64}
            factory.store = SimpleNamespace(data={
                "policy": {"hashes": {"workflow": "b" * 64}},
            })
            factory.capabilities = load_capabilities({}, {"worker": f"{script} {{prompt}}"})
            factory.cfg = {
                "agents": {"worker": f"{script} {{prompt}}"},
                "factory": {"agent_timeout": 5},
            }
            factory.args = SimpleNamespace(scenario="test", mock=True)
            factory.python = sys.executable
            factory.codex_bin = None
            factory._sync_store = lambda *args, **kwargs: None
            ticket = {"number": 7, "attempt": 1}

            code, output = factory.run_adapter(
                "worker", ticket, repo, prompt, "7.log", "implementation",
            )

            self.assertEqual(code, 0, output)
            assignment = json.loads((repo / ticket["current_assignment"]).read_text())
            events = [
                json.loads(line)
                for line in (repo / ticket["current_events"]).read_text().splitlines()
            ]
            self.assertEqual(assignment["role"], "implementation")
            self.assertEqual(
                [event["type"] for event in events],
                ["started", "status", "completed"],
            )

            # Retain a bounded tail without dropping a multi-line final decision;
            # the complete ordinary stdout still belongs in the on-disk log.
            payload = ("x" * 8192 + "\n") * 160 + "{\n" + '\n'.join('"key%d": %d,' % (i, i) for i in range(200)) + '\n"decision": "APPROVE"\n}\n'
            (repo / "output.txt").write_text(payload)
            script.write_text('#!/bin/sh\ncat "' + str(repo / "output.txt") + '"\n')
            code, output = factory.run_adapter("worker", ticket, repo, prompt, "long.log", "implementation")
            self.assertEqual(code, 0)
            self.assertEqual(output, payload[-1024 * 1024:])
            self.assertEqual((repo / ".factory/logs/long.log").read_text(), payload)

    def test_protocol_adapter_must_emit_one_valid_final_result(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            script = repo / "adapter.sh"
            script.write_text(
                "#!/bin/sh\n"
                "printf '%s\\n' 'FACTORY_EVENT {\"schema_version\":1,\"type\":\"status\",\"message\":\"Working\"}'\n"
                "printf '%s\\n' 'FACTORY_RESULT {\"schema_version\":1,\"outcome\":\"success\",\"output_revisions\":{},\"artifacts\":[],\"verification_claims\":[\"work complete\"],\"unresolved_risks\":[]}'\n"
            )
            script.chmod(0o755)
            prompt = repo / ".factory/prompts/8.md"
            prompt.parent.mkdir(parents=True)
            prompt.write_text("Implement ticket 8.\n")
            factory = Factory.__new__(Factory)
            factory.repo = repo
            factory.run_id = "run-1"
            factory.profile_name = "standard"
            factory.governance = {"charter_sha256": "a" * 64}
            factory.store = SimpleNamespace(data={"policy": {"hashes": {"workflow": "b" * 64}}})
            template = f"{script} --assignment {{assignment}} --prompt {{prompt}}"
            factory.capabilities = load_capabilities({
                "worker": {"protocol_version": 1, "features": ["progress-events"]},
            }, {"worker": template})
            factory.cfg = {
                "agents": {"worker": template},
                "factory": {"agent_timeout": 5},
            }
            factory.args = SimpleNamespace(scenario="test", mock=True)
            factory.python = sys.executable
            factory.codex_bin = None
            factory._sync_store = lambda *args, **kwargs: None
            ticket = {"number": 8, "attempt": 1}

            code, output = factory.run_adapter(
                "worker", ticket, repo, prompt, "8.log", "implementation",
            )

            self.assertEqual(code, 0, output)
            self.assertEqual(ticket["adapter_result"]["outcome"], "success")
            self.assertTrue((repo / ticket["current_result"]).is_file())

            script.write_text("#!/bin/sh\nprintf '%s\\n' 'no final result'\n")
            code, output = factory.run_adapter(
                "worker", {"number": 9, "attempt": 1}, repo, prompt, "9.log", "implementation",
            )
            self.assertEqual(code, 2)
            self.assertIn("exactly one FACTORY_RESULT", output)

    def test_adapter_check_command_exposes_capabilities_without_running_the_adapter(self):
        repo = Path(__file__).parents[2]
        result = subprocess.run(
            [str(repo / "factory/factory"), "adapter-check", "codex", "--json"],
            cwd=repo,
            text=True,
            capture_output=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["adapter"], "codex")
        self.assertTrue(report["compatible"])
        self.assertIn("supports_read_only", report["capability"])

    def test_documented_custom_protocol_adapter_passes_conformance_and_framing(self):
        factory_root = Path(__file__).parents[1]
        example = tomllib.loads(
            (factory_root / "examples/custom-adapter.toml").read_text()
        )
        report = conformance_report(
            "example-protocol",
            example["agents"]["example-protocol"],
            example["agent_capabilities"]["example-protocol"],
        )
        self.assertTrue(report["compatible"], report["errors"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assignment = root / "assignment.json"
            assignment.write_text(json.dumps(build_assignment(
                run_id="example-run", role="implementation", ticket=1,
                attempt=1, repository=str(root), working_root=str(root),
                prompt_ref="prompt.md", profile="standard",
                charter_sha256="a" * 64,
                policy_hashes={"workflow": "b" * 64},
                requested_capabilities=["workspace-write", "progress-events"],
            )))
            prompt = root / "prompt.md"
            prompt.write_text("Validate protocol framing.\n")
            result = subprocess.run([
                sys.executable,
                str(factory_root / "examples/custom_protocol_adapter.py"),
                "--assignment", str(assignment), "--prompt", str(prompt),
            ], text=True, capture_output=True)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('FACTORY_EVENT {"schema_version":1,"type":"status"', result.stdout)
            result_line = next(
                line.removeprefix("FACTORY_RESULT ")
                for line in result.stdout.splitlines()
                if line.startswith("FACTORY_RESULT ")
            )
            self.assertEqual(validate_result(json.loads(result_line))["outcome"], "success")


if __name__ == "__main__":
    unittest.main()
