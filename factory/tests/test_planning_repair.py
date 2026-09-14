"""Regression cases reconstructed from the failures reported in PR #63.

Adapters below deliberately bypass constrained decoding to exercise the local
validator and recovery path, including providers that only receive schema text.
"""
import contextlib
import copy
import io
import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]))
from factory_charter import FactoryCharter
from project_contract import ProjectContract
from planning_pipeline import (
    PlanningArtifactError, _run_stage_agent, approve_product, continue_plan,
    load_manifest, plan_prd, planning_output_schema, render_program,
    require_references, validate_lean_vertical_slices,
)
from planning_presentation import planning_presentation

FAILURES = Path(__file__).with_name("fixtures") / "planning-reference-failures.json"
SUCCESS = subprocess.CompletedProcess(["claude"], 0, "", "")


class PlanningRepairTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        charter = FactoryCharter.draft(self.repo, ProjectContract.detect(self.repo))
        charter.write()
        charter.approve()
        self.prd = self.repo / "PRD.md"
        self.prd.write_text("# TableStory\nConvert the movie app into the complete recipe product.\n")
        self.output = io.StringIO()
        self.redirect = contextlib.redirect_stdout(self.output)
        self.redirect.__enter__()
        self.addCleanup(self.redirect.__exit__, None, None, None)
        self.run = plan_prd(self.repo, self.prd, None, "codex", 3, 12, "mock", "mock", mock=True)
        approve_product(self.repo, self.run.name, assume_yes=True)
        continue_plan(self.repo, self.run.name, "mock", mock=True)
        self.manifest = load_manifest(self.run)
        self.program = json.loads((self.run / "03-program-design.json").read_text())

    def invoke(self, provider="claude"):
        return _run_stage_agent(self.repo, self.run, "program_design", self.manifest, provider, provider, False)

    def test_reported_reference_failures_repair_without_a_manual_retry(self):
        for case in json.loads(FAILURES.read_text()):
            with self.subTest(case=case["name"]):
                broken = copy.deepcopy(self.program)
                broken[case["collection"]][0][case["field"]] = case["values"]
                upstream = (self.run / "02-system-architecture.json").read_bytes()
                approvals = copy.deepcopy(self.manifest["approvals"])
                observations = []
                def answer(*args):
                    observations.append(json.loads((self.repo / ".factory/planning-state.json").read_text()))
                    return SUCCESS, broken if len(observations) == 1 else self.program
                with patch("planning_pipeline._run_claude_agent", side_effect=answer) as adapter:
                    self.invoke()
                self.assertEqual(adapter.call_count, 2)
                record = self.manifest["stages"]["program_design"]
                self.assertEqual(record["status"], "complete")
                self.assertEqual(record["automatic_repairs"], 1)
                rejected = self.repo / record["repair_history"][-1]["rejected_artifact"]
                self.assertEqual(json.loads(rejected.read_text()), broken)
                prompt = adapter.call_args.args[2]
                self.assertIn(case["expected_field"], prompt)
                self.assertIn("Do not invent references, drop requirements", prompt)
                command = adapter.call_args.args[0]
                schema = json.loads(command[command.index("--json-schema") + 1])
                self.assertIn("enum", schema["properties"]["functions"]["items"]["properties"]["requirements"]["items"])
                current = next(s for s in observations[1]["stages"] if s["id"] == "program_design")
                self.assertEqual(current["status"], "running")
                self.assertIn("repair 1 of 2", current["activity"])
                self.assertFalse(current["error"])
                self.assertEqual((self.run / "02-system-architecture.json").read_bytes(), upstream)
                self.assertEqual(self.manifest["approvals"], approvals)

    def test_repairs_are_bounded_and_every_rejected_output_is_retained(self):
        broken = copy.deepcopy(self.program)
        broken["functions"][0]["requirements"] = ["DEC_CSS_ONLY_ART"]
        before = (self.run / "03-program-design.json").read_bytes()
        with patch("planning_pipeline._run_claude_agent", return_value=(SUCCESS, broken)) as adapter:
            with self.assertRaises(PlanningArtifactError): self.invoke()
        self.assertEqual(adapter.call_count, 3)
        record = load_manifest(self.run)["stages"]["program_design"]
        self.assertEqual(record["status"], "blocked")
        self.assertEqual(record["automatic_repairs"], 2)
        paths = [item["rejected_artifact"] for item in record["repair_history"]]
        self.assertEqual(len(set(paths)), 3)
        self.assertTrue(all((self.repo / path).is_file() for path in paths))
        self.assertEqual((self.run / "03-program-design.json").read_bytes(), before)
        self.assertTrue(record["receipt"])

    def test_charter_can_disable_automatic_repairs(self):
        charter = replace(FactoryCharter.load(self.repo, require_approved=True), max_retries=0)
        broken = copy.deepcopy(self.program)
        broken["modules"][0]["components"] = ["WRONG"]
        with patch("planning_pipeline.FactoryCharter.load", return_value=charter), patch(
            "planning_pipeline._run_claude_agent", return_value=(SUCCESS, broken)
        ) as adapter:
            with self.assertRaises(PlanningArtifactError): self.invoke()
        self.assertEqual(adapter.call_count, 1)

    def test_provider_errors_are_not_retried(self):
        for error in ("authentication login required", "rate limit exceeded"):
            with self.subTest(error=error), patch("planning_pipeline._run_claude_agent", return_value=(
                subprocess.CompletedProcess(["claude"], 1, "", error), None,
            )) as adapter:
                with self.assertRaises(RuntimeError): self.invoke()
                self.assertEqual(adapter.call_count, 1)

    def test_context_overflow_restarts_expert_with_smaller_file_backed_prompt(self):
        prompts = []

        def answer(command, repo, prompt, log, stage):
            prompts.append(prompt)
            if len(prompts) == 1:
                return subprocess.CompletedProcess(command, 1, "", "Context too big"), None
            self.assertLess(len(prompt), len(prompts[0]))
            self.assertIn("Read", prompt)
            return SUCCESS, self.program

        with patch("planning_pipeline._run_claude_agent", side_effect=answer):
            self.invoke()
        self.assertEqual(len(prompts), 2)
        self.assertEqual(self.manifest["stages"]["program_design"]["status"], "complete")

    def test_claude_planning_excludes_personal_mcp_servers(self):
        with patch("planning_pipeline._run_claude_agent", return_value=(SUCCESS, self.program)) as adapter:
            self.invoke()
        command = adapter.call_args.args[0]
        self.assertIn("--strict-mcp-config", command)
        self.assertEqual(json.loads(command[command.index("--mcp-config") + 1]), {"mcpServers": {}})

    def test_context_recovery_stops_after_one_restart_without_touching_approvals(self):
        approvals = copy.deepcopy(self.manifest["approvals"])
        with patch("planning_pipeline._run_claude_agent", return_value=(
            subprocess.CompletedProcess(["claude"], 1, "", "Context too big"), None,
        )) as adapter:
            with self.assertRaisesRegex(RuntimeError, "still cannot fit"):
                self.invoke()
        self.assertEqual(adapter.call_count, 2)
        self.assertEqual(self.manifest["approvals"], approvals)
        stage = self.manifest["stages"]["program_design"]
        self.assertEqual(stage["failure_kind"], "context_limit")
        self.assertEqual(len(stage["context_history"]), 2)

    def test_codex_and_cursor_context_recovery_keep_the_same_validation(self):
        for provider in ("codex", "cursor"):
            with self.subTest(provider=provider):
                calls = []

                def codex(command, repo, prompt, log, stage, **kwargs):
                    calls.append(prompt)
                    if len(calls) == 1:
                        return subprocess.CompletedProcess(command, 1, "", "context_length_exceeded")
                    Path(command[command.index("-o") + 1]).write_text(json.dumps(self.program))
                    return SUCCESS

                def cursor(binary, repo, prompt, **kwargs):
                    calls.append(prompt)
                    if len(calls) == 1:
                        return subprocess.CompletedProcess([binary], 1, "", "prompt is too long")
                    return subprocess.CompletedProcess([binary], 0, json.dumps(self.program), "")

                with patch("planning_pipeline._run_codex_agent", side_effect=codex), patch(
                    "planning_pipeline.invoke_cursor", side_effect=cursor,
                ):
                    self.invoke(provider)
                self.assertEqual(len(calls), 2)
                self.assertIn("file-backed", calls[1])
                self.assertEqual(self.manifest["stages"]["program_design"]["status"], "complete")

    def test_human_questions_are_not_answered_by_the_repair_loop(self):
        value = copy.deepcopy(self.program)
        value["blocking_questions"] = ["Should recipes support offline storage?"]
        with patch("planning_pipeline._run_claude_agent", return_value=(SUCCESS, value)) as adapter:
            self.invoke()
        self.assertEqual(adapter.call_count, 1)
        self.assertEqual(self.manifest["stages"]["program_design"]["status"], "blocked")
        self.assertNotIn("failure_kind", self.manifest["stages"]["program_design"])

    def test_malformed_cursor_json_is_preserved_and_repaired(self):
        malformed = "```json\n{broken"
        with patch("planning_pipeline.invoke_cursor", side_effect=[
            subprocess.CompletedProcess(["cursor"], 0, malformed, ""),
            subprocess.CompletedProcess(["cursor"], 0, json.dumps(self.program), ""),
        ]) as adapter:
            self.invoke("cursor")
        self.assertEqual(adapter.call_count, 2)
        record = self.manifest["stages"]["program_design"]
        self.assertEqual((self.repo / record["repair_history"][0]["rejected_artifact"]).read_text(), malformed)
        self.assertIn("enum", adapter.call_args.args[2])

    def test_codex_gets_the_bound_schema_and_can_repair_missing_output(self):
        calls = []
        (self.run / ".program_design-raw.json").write_text(json.dumps(self.program))
        def answer(command, repo, prompt, log, stage, **kwargs):
            schema = json.loads(Path(command[command.index("--output-schema") + 1]).read_text())
            calls.append(schema)
            if len(calls) == 2:
                Path(command[command.index("-o") + 1]).write_text(json.dumps(self.program))
            return SUCCESS
        with patch("planning_pipeline._run_codex_agent", side_effect=answer): self.invoke("codex")
        self.assertEqual(len(calls), 2)
        self.assertNotIn("DEC_CSS_ONLY_ART", calls[0]["properties"]["types"]["items"]["properties"]["requirements"]["items"]["enum"])

    def test_schema_binds_upstream_ids_and_leaves_local_ids_for_validation(self):
        inputs = {stage: json.loads((self.run / filename).read_text()) for stage, filename in (
            ("product_review", "01-product-review.json"), ("system_architecture", "02-system-architecture.json"),
            ("program_design", "03-program-design.json"),
        )}
        expected = sorted(r["id"] for r in inputs["product_review"]["requirements"])
        for stage in ("system_architecture", "program_design", "vertical_slices"):
            path = planning_output_schema(self.repo, self.run, stage, inputs, self.manifest)
            self.assertTrue(path.is_relative_to(self.run))
            schema = json.loads(path.read_text())
            collection, field = {"system_architecture": ("components", "requirements"), "program_design": ("types", "requirements"), "vertical_slices": ("tickets", "requirement_ids")}[stage]
            self.assertEqual(schema["properties"][collection]["items"]["properties"][field]["items"]["enum"], expected)
        program = json.loads((self.run / "schemas/program_design.json").read_text())
        self.assertNotIn("enum", program["properties"]["functions"]["items"]["properties"]["calls"]["items"])
        self.manifest["profile"] = "lean"
        lean = json.loads(planning_output_schema(self.repo, self.run, "vertical_slices", inputs, self.manifest).read_text())
        self.assertEqual(lean["properties"]["tickets"]["items"]["properties"]["contract_ids"]["maxItems"], 0)
        self.assertNotIn('"enum": []', json.dumps(lean))

    def test_module_type_and_function_notes_are_visible(self):
        for collection in ("modules", "types", "functions"):
            self.program[collection][0]["notes"] = f"Preserve {collection} invariant."
        rendered = render_program(self.program, self.run.name)
        for collection in ("modules", "types", "functions"):
            self.assertIn(f"Preserve {collection} invariant.", rendered)

    def test_missing_render_field_is_repaired_before_replacing_accepted_artifact(self):
        broken = copy.deepcopy(self.program)
        del broken["modules"][0]["responsibility"]
        accepted = (self.run / "03-program-design.json").read_bytes()
        calls = []

        def answer(*args):
            self.assertEqual((self.run / "03-program-design.json").read_bytes(), accepted)
            calls.append(args)
            return SUCCESS, broken if len(calls) == 1 else self.program

        with patch("planning_pipeline._run_claude_agent", side_effect=answer):
            self.invoke()
        self.assertEqual(len(calls), 2)
        self.assertIn("responsibility", calls[1][2])

    def test_lean_rejects_undefined_design_references_instead_of_discarding_them(self):
        product = json.loads((self.run / "01-product-review.json").read_text())
        slices = json.loads((self.run / "04-vertical-slices.json").read_text())
        for ticket in slices["tickets"]:
            ticket["contract_ids"] = []
            ticket["program_element_ids"] = []
        slices["tickets"][0]["contract_ids"] = ["UNDEFINED_CONTRACT"]
        with self.assertRaisesRegex(ValueError, "must be empty in Lean"):
            validate_lean_vertical_slices(slices, product)
        self.assertEqual(slices["tickets"][0]["contract_ids"], ["UNDEFINED_CONTRACT"])

    def test_long_prose_cannot_hide_the_repair_guidance(self):
        with self.assertRaises(ValueError) as error:
            require_references(["A long explanation " * 200], {"REQ_ONE"}, "FN_ONE", "functions[].requirements")
        self.assertIn("functions[].requirements", str(error.exception)[:2000])
        self.assertIn("REQ_ONE", str(error.exception)[:2000])

    def test_repair_status_is_not_a_human_decision(self):
        planning = {"status": "planning_program_design", "approvals": {"product": {}}, "stages": [{
            "id": "program_design", "title": "Program Design", "status": "running",
            "activity": "Correcting invalid planning output (repair 1 of 2). No action needed.",
        }]}
        view = planning_presentation(planning)
        self.assertEqual(view["state"], "expert_running")
        self.assertIsNone(view["decision"])
        self.assertFalse(view["can_continue"])
        self.assertEqual(view["selected_stage"], "program_design")
        self.assertIn("repair 1 of 2", view["journey"]["detail"])


if __name__ == "__main__": unittest.main()
