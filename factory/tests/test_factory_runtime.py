import contextlib
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).parents[1]))

from doctor import Check, baseline_check, run_doctor, version_tuple
from codex_cli import (
    codex_auth_ready,
    codex_region_environment,
    codex_uses_managed_bedrock,
)
from orchestrator import (
    Factory,
    approve_qa_tests,
    create_recovery_checkpoint,
    human_merge_ticket,
    implementation_attempt_failure,
    implementation_no_change_failure,
    latest_recovery_checkpoint,
    publish_evidence_run_summaries,
    publish_repository_setup,
    recovery_checkpoints,
    recover_latest_state,
    recover_remote_ticket_state,
    release_ticket_claim,
    request_qa_test_changes,
    restore_recovery_checkpoint,
    resolve_codex_cli,
    retry_ticket,
    ticket_diff_budget,
    ticket_recovery,
    ticket_spec_fingerprint,
    worktree_path,
)
from factory_charter import FactoryCharter
from planner import governance_marker
from project_contract import ProjectContract


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, text=True, capture_output=True, check=True,
    ).stdout.strip()


def install_approved_charter(repo: Path, merge_authority: str = "human") -> None:
    project = ProjectContract.load(repo) if (repo / "factory.project.toml").is_file() else ProjectContract.detect(repo)
    charter = FactoryCharter.draft(repo, project)
    charter.write()
    if merge_authority != "human":
        path = repo / "factory.charter.toml"
        path.write_text(path.read_text().replace(
            'merge_authority = "human"', f'merge_authority = "{merge_authority}"',
        ))
    FactoryCharter.load(repo).approve()


class RuntimeTests(unittest.TestCase):
    def test_release_claim_reconciles_an_already_absent_remote_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            state = repo / ".factory/state.json"
            state.parent.mkdir(parents=True)
            state.write_text(json.dumps({
                "run_id": "new-run",
                "tickets": [{
                    "number": 4,
                    "status": "Blocked",
                    "phase": "claim",
                    "failure": (
                        "Remote Ticket claim belongs to Factory run old-run."
                    ),
                    "remote_claim": {
                        "ticket": 4,
                        "run_id": "old-run",
                        "released": True,
                    },
                    "pr_url": "https://github.test/pull/10",
                    "branch_generation": 0,
                    "recovery": {"kind": "remote_claim"},
                    "next_human_action": "release_or_resume_claim",
                    "history": [],
                }],
            }))
            remote_ticket = {"number": 4, "labels": ["state:blocked"]}
            backend = mock.Mock()
            backend.project_number = 15
            backend.read_claim.return_value = None
            backend.load.return_value = [remote_ticket]

            with mock.patch(
                "orchestrator.GitHubBackend",
                return_value=backend,
            ):
                result = release_ticket_claim(
                    repo,
                    4,
                    owner_run_id="old-run",
                    reason="Operator confirmed the old runner stopped",
                    assume_yes=True,
                )

            ticket = json.loads(state.read_text())["tickets"][0]
            self.assertFalse(result["released"])
            self.assertTrue(result["reconciled"])
            self.assertEqual(ticket["status"], "Backlog")
            self.assertEqual(ticket["phase"], "backlog")
            self.assertEqual(ticket["remote_claim"], {})
            self.assertEqual(ticket["failure"], "")
            self.assertEqual(ticket["recovery"], {})
            self.assertEqual(ticket["branch_generation"], 1)
            self.assertEqual(ticket["pr_url"], "")
            self.assertEqual(
                ticket["last_released_claim"]["run_id"],
                "old-run",
            )
            self.assertIn(
                "already absent",
                ticket["history"][-1]["note"],
            )
            backend.release_claim.assert_not_called()
            backend.set_status.assert_called_once_with(
                remote_ticket,
                "Backlog",
                "Operator released an abandoned Factory claim",
            )

    def test_checkpoint_restores_exact_runtime_state_and_creates_undo(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            git(repo, "init", "-q", "-b", "main")
            git(repo, "config", "user.name", "Factory Test")
            git(repo, "config", "user.email", "factory@example.invalid")
            (repo / "README.md").write_text("tracked source\n")
            git(repo, "add", "README.md")
            git(repo, "commit", "-qm", "baseline")
            runtime = repo / ".factory"
            plan = runtime / "plans/plan-1"
            plan.mkdir(parents=True)
            original_state = {
                "mode": "github",
                "run_id": "latest-run",
                "tickets": [{"number": 5, "status": "In Review"}],
            }
            (runtime / "state.json").write_text(json.dumps(original_state))
            (runtime / "planning-state.json").write_text(json.dumps({
                "plan_id": "plan-1",
                "status": "published",
            }))
            (plan / "artifact.json").write_text('{"approved": true}\n')

            checkpoint = create_recovery_checkpoint(
                repo,
                reason="Before test reset",
            )
            (runtime / "state.json").write_text('{"tickets": []}\n')
            shutil.rmtree(runtime / "plans")

            restored = restore_recovery_checkpoint(
                repo,
                checkpoint,
                assume_yes=True,
            )

            self.assertEqual(
                json.loads((runtime / "state.json").read_text()),
                original_state,
            )
            self.assertEqual(
                (runtime / "plans/plan-1/artifact.json").read_text(),
                '{"approved": true}\n',
            )
            self.assertEqual(
                latest_recovery_checkpoint(repo)["checkpoint_id"],
                checkpoint["checkpoint_id"],
            )
            undo = [
                item for item in recovery_checkpoints(repo, include_undo=True)
                if item.get("kind") == "undo"
            ]
            self.assertEqual(len(undo), 1)
            self.assertEqual(
                restored["undo_checkpoint_id"],
                undo[0]["checkpoint_id"],
            )
            self.assertEqual((repo / "README.md").read_text(), "tracked source\n")

    def test_checkpoint_rejects_symbolic_links(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            runtime = repo / ".factory"
            runtime.mkdir(parents=True)
            (runtime / "state.json").write_text(json.dumps({
                "tickets": [{"number": 1}],
            }))
            outside = repo / "outside"
            outside.mkdir()
            (runtime / "plans").symlink_to(outside, target_is_directory=True)

            with self.assertRaisesRegex(ValueError, "symbolic links"):
                create_recovery_checkpoint(repo, reason="Unsafe checkpoint")

    def test_recover_latest_prefers_newer_state_preserved_by_undo_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            runtime = repo / ".factory"
            runtime.mkdir(parents=True)
            older = {
                "updated_at": "2026-08-26T10:40:39+00:00",
                "tickets": [{"number": 4, "status": "Ready"}],
            }
            newer = {
                "updated_at": "2026-08-26T11:11:56+00:00",
                "tickets": [{"number": 4, "status": "Backlog"}],
            }
            (runtime / "state.json").write_text(json.dumps(older))
            reset = create_recovery_checkpoint(
                repo,
                reason="Before ticket execution reset",
            )
            (runtime / "state.json").write_text(json.dumps(newer))
            undo = create_recovery_checkpoint(
                repo,
                reason=f"Before restoring checkpoint {reset['checkpoint_id']}",
                kind="undo",
            )
            (runtime / "state.json").write_text(json.dumps(older))

            selected = latest_recovery_checkpoint(repo)
            result = recover_latest_state(
                repo,
                project_number=None,
                assume_yes=True,
            )

            self.assertEqual(selected["checkpoint_id"], undo["checkpoint_id"])
            self.assertEqual(result["checkpoint_id"], undo["checkpoint_id"])
            self.assertEqual(
                json.loads((runtime / "state.json").read_text()),
                newer,
            )

    def test_recover_reconstructs_latest_live_plan_without_remote_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            source = Path(__file__).parents[2]
            shutil.copytree(source / "factory", repo / "factory")
            install_approved_charter(repo)
            charter = FactoryCharter.load(repo, require_approved=True)
            governance = charter.governance("standard")
            governance_comment = governance_marker(governance)
            summary = {
                "schema_version": 1,
                "run_id": "live-run-1",
                "ticket": 11,
                "status": "Backlog",
                "plan_id": "live-plan-1",
                "profile": "standard",
                "governance": {
                    "charter_sha256": governance["charter_sha256"],
                    "merge_authority": "human",
                },
                "revisions": {},
                "verdicts": {},
                "human_decisions": {},
                "metrics": {},
            }
            ticket = {
                "number": 11,
                "title": "Recovered vertical slice",
                "body": (
                    "## Spec\nRecover this behavior.\n\n"
                    "## Acceptance criteria\n- [ ] State is visible.\n\n"
                    "## Agent\nagent: codex\n\n"
                    "<!-- factory-plan:live-plan-1:TICKET_ONE -->\n"
                    f"{governance_comment}"
                ),
                "labels": ["agent-ready"],
                "status": "Backlog",
                "url": "https://github.test/issues/11",
                "updatedAt": "2026-08-26T09:00:00Z",
                "pr_url": "",
                "pull_request": {},
                "remote_run_summary": summary,
                "remote_claim": {
                    "ticket": 11,
                    "run_id": "live-run-1",
                    "owner_run_id": "live-run-1",
                    "claimed_at": "2026-08-26T08:00:00Z",
                },
            }
            backend = SimpleNamespace(
                project_number=15,
                owner="attendee",
                name="workshop",
                load_recovery_state=mock.Mock(return_value=[ticket]),
            )

            with mock.patch(
                "orchestrator.GitHubBackend",
                return_value=backend,
            ):
                result = recover_latest_state(
                    repo,
                    project_number=15,
                    assume_yes=True,
                )

            state = json.loads((repo / ".factory/state.json").read_text())
            planning = json.loads(
                (repo / ".factory/planning-state.json").read_text()
            )
            self.assertEqual(result["source"], "github")
            self.assertEqual(state["run_id"], "live-run-1")
            self.assertEqual(state["tickets"][0]["number"], 11)
            self.assertEqual(state["recovery"]["plan_id"], "live-plan-1")
            self.assertFalse(state["recovery"]["receipts_restored"])
            self.assertEqual(planning["status"], "published")
            self.assertEqual(
                planning["publication"]["issues"],
                {"TICKET_ONE": 11},
            )
            self.assertTrue(
                all(
                    stage["status"] in {"unavailable", "skipped"}
                    for stage in planning["stages"]
                )
            )
            backend.load_recovery_state.assert_called_once_with()

    def test_factory_run_is_complete_only_when_every_ticket_is_done(self):
        factory = Factory.__new__(Factory)
        factory.tickets = {
            1: {"status": "Done"},
            2: {"status": "In Review"},
        }

        self.assertFalse(factory.delivery_complete())
        factory.tickets[2]["status"] = "Done"
        self.assertTrue(factory.delivery_complete())

    def test_running_factory_reconciles_a_companion_human_merge_event(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            event_dir = repo / ".factory/merge-events"
            event_dir.mkdir(parents=True)
            approved_head = "a" * 40
            merged_head = "b" * 40
            receipt = ".factory/receipts/human-review.json"
            (event_dir / "3.json").write_text(json.dumps({
                "schema_version": 1,
                "ticket": 3,
                "approved_head": approved_head,
                "merged_head": merged_head,
                "merged_at": "2026-08-24T21:30:00+00:00",
                "receipt": receipt,
            }))
            ticket = {
                "number": 3,
                "status": "In Review",
                "phase": "in-review",
                "approved_head": approved_head,
                "receipts": [],
                "history": [],
                "failure": "",
            }
            factory = Factory.__new__(Factory)
            factory.repo = repo
            factory.tickets = {3: ticket}
            factory._sync_store = mock.Mock()

            factory.apply_human_merge_events()

            self.assertEqual(ticket["status"], "Done")
            self.assertEqual(ticket["merge_executed_by"], "human")
            self.assertEqual(ticket["receipts"], [receipt])
            self.assertFalse((event_dir / "3.json").exists())
            factory._sync_store.assert_called_once_with()

    def test_retry_preserves_a_verification_candidate_and_qa_tests(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            state = repo / ".factory/state.json"
            state.parent.mkdir(parents=True)
            install_approved_charter(repo)
            worktree = worktree_path(repo, 1)
            qa_test = worktree / "tests/test_ticket_1_contract.py"
            qa_test.parent.mkdir(parents=True)
            qa_test.write_text("def test_contract():\n    assert True\n")
            state.write_text(json.dumps({
                "tickets": [{
                    "number": 1,
                    "status": "Blocked",
                    "phase": "verifying",
                    "failure": "legacy test still expects removed behavior",
                    "attempt": 3,
                    "branch": "factory/1-contract",
                    "base_sha": "base-sha",
                    "qa_attempt": 1,
                    "qa_commit": "qa-sha",
                    "qa_tests": {
                        "tests/test_ticket_1_contract.py": "test-blob",
                    },
                    "qa_approved": False,
                    "history": [],
                }],
            }))

            retry_ticket(repo, 1, mock=True)

            ticket = json.loads(state.read_text())["tickets"][0]
            self.assertEqual(ticket["status"], "Ready")
            self.assertEqual(ticket["attempt"], 0)
            self.assertTrue(ticket["qa_approved"])
            self.assertEqual(ticket["qa_commit"], "qa-sha")
            self.assertEqual(ticket["base_sha"], "base-sha")
            self.assertIn("legacy test", ticket["retry_context"])
            self.assertIn("existing candidate", ticket["history"][-1]["note"])

    def test_diff_budget_excludes_protected_qa_and_retry_records_bounded_exception(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            repo.mkdir()
            git(repo, "init", "-q", "-b", "main")
            git(repo, "config", "user.name", "Factory Test")
            git(repo, "config", "user.email", "factory@example.test")
            project = ProjectContract.detect(repo)
            project.write()
            charter_path = FactoryCharter.draft(repo, project).write()
            charter_path.write_text(
                charter_path.read_text().replace(
                    "max_diff_lines = 1200", "max_diff_lines = 3",
                )
            )
            FactoryCharter.load(repo).approve()
            (repo / "README.md").write_text("# Test\n")
            git(repo, "add", "-A")
            git(repo, "commit", "-qm", "base")
            base = git(repo, "rev-parse", "HEAD")

            worktree = worktree_path(repo, 4)
            git(repo, "worktree", "add", "-qb", "factory/4-test", str(worktree))
            qa_path = worktree / "tests/ticket-4.test.js"
            qa_path.parent.mkdir(parents=True)
            qa_path.write_text("one\ntwo\nthree\nfour\n")
            git(worktree, "add", "-A")
            git(worktree, "commit", "-qm", "qa")
            qa_commit = git(worktree, "rev-parse", "HEAD")
            app_path = worktree / "public/app.js"
            app_path.parent.mkdir()
            app_path.write_text("1\n2\n3\n4\n5\n6\n")
            git(worktree, "add", "-A")
            git(worktree, "commit", "-qm", "implementation")

            ticket = {
                "number": 4,
                "status": "Blocked",
                "phase": "code-review",
                "failure": "candidate is too large",
                "attempt": 3,
                "branch": "factory/4-test",
                "base_sha": base,
                "qa_attempt": 1,
                "qa_commit": qa_commit,
                "qa_tests": {"tests/ticket-4.test.js": "test-blob"},
                "qa_approved": False,
                "history": [],
            }
            state = repo / ".factory/state.json"
            state.parent.mkdir(exist_ok=True)
            state.write_text(json.dumps({"tickets": [ticket]}))

            budget = ticket_diff_budget(
                repo, ticket, FactoryCharter.load(repo, require_approved=True),
            )
            self.assertEqual(budget["total_lines"], 10)
            self.assertEqual(budget["protected_qa_lines"], 4)
            self.assertEqual(budget["implementation_lines"], 6)
            self.assertEqual(budget["status"], "exceeded")

            with self.assertRaisesRegex(SystemExit, "cannot be retried"):
                retry_ticket(repo, 4, mock=True)

            retry_ticket(
                repo, 4, mock=True, budget_lines=10,
                reason="Greenfield browser workflow remains one approved outcome",
                assume_yes=True,
            )

            saved = json.loads(state.read_text())["tickets"][0]
            self.assertEqual(saved["status"], "Ready")
            self.assertEqual(saved["budget_override"]["lines"], 10)
            self.assertEqual(saved["budget_override"]["charter_limit"], 3)
            self.assertTrue(saved["qa_approved"])
            event = json.loads((repo / ".factory/retry-events/4.json").read_text())
            self.assertEqual(event["budget_override"]["reason"], saved["budget_override"]["reason"])

    def test_running_factory_consumes_retry_event(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            event_dir = repo / ".factory/retry-events"
            event_dir.mkdir(parents=True)
            event = {
                "schema_version": 1,
                "event_id": "retry-event-7",
                "ticket": 7,
                "created_at": "2026-08-25T12:00:00+00:00",
                "failure": "required gate failed",
                "budget_override": None,
            }
            marker = event_dir / "7.json"
            marker.write_text(json.dumps(event))
            ticket = {
                "number": 7,
                "status": "Blocked",
                "phase": "build",
                "failure": "required gate failed",
                "attempt": 3,
                "history": [],
            }
            factory = Factory.__new__(Factory)
            factory.repo = repo
            factory.tickets = {7: ticket}
            factory.backend = None
            factory._sync_store = mock.Mock()

            factory.apply_retry_events()

            self.assertEqual(ticket["status"], "Ready")
            self.assertEqual(ticket["last_retry_event"], "retry-event-7")
            self.assertFalse(marker.exists())
            factory._sync_store.assert_called_once_with()

    def test_live_retry_refreshes_an_edited_github_ticket_and_clears_stale_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            repo.mkdir()
            install_approved_charter(repo)
            original = {
                "number": 7,
                "title": "Incomplete slice",
                "body": "Add the workflow.",
                "labels": ["agent-ready", "state:blocked"],
                "dependencies": [],
                "agent": "codex",
                "default_agent": "codex",
                "status": "Blocked",
                "phase": "triage",
                "failure": "Add a Spec and at least one observable Acceptance criterion.",
                "triage": {"result": "NEEDS_INFORMATION"},
                "attempt": 2,
                "branch": "factory/7-incomplete-slice",
                "base_sha": "a" * 40,
                "qa_commit": "b" * 40,
                "qa_tests": {"tests/test_ticket_7.py": "blob"},
                "qa_evidence": {"red": {"result": "RED PROVED"}},
                "gate_results": [{"name": "tests", "classification": "FAIL"}],
                "changed_files": ["src/old.py"],
                "current_prompt": ".factory/prompts/7-attempt2.md",
                "current_log": ".factory/logs/7-attempt2.log",
                "code_review": {"result": {"decision": "REQUEST_CHANGES"}},
                "approved_head": "c" * 40,
                "pr_url": "https://github.test/pull/7",
                "receipts": [".factory/receipts/old-spec.json"],
                "budget_override": {
                    "lines": 1400,
                    "charter_limit": 1200,
                    "reason": "The original ticket required one larger workflow",
                },
                "history": [],
            }
            original["spec_sha256"] = ticket_spec_fingerprint(original)
            state = repo / ".factory/state.json"
            state.parent.mkdir()
            state.write_text(json.dumps({"tickets": [original]}))
            corrected_body = (
                "## Spec\nAdd the workflow.\n\n"
                "## Acceptance criteria\n- The saved workflow is visible.\n"
            )
            backend = mock.Mock()
            backend.load.return_value = [{
                "number": 7,
                "title": "Complete slice",
                "body": corrected_body,
                "labels": ["agent-ready", "state:blocked"],
                "url": "https://github.test/issues/7",
            }]

            with mock.patch("orchestrator.GitHubBackend", return_value=backend):
                retry_ticket(repo, 7, mock=False, project_number=3)

            saved = json.loads(state.read_text())["tickets"][0]
            self.assertEqual(saved["status"], "Ready")
            self.assertEqual(saved["title"], "Complete slice")
            self.assertEqual(saved["body"], corrected_body)
            self.assertEqual(saved["attempt"], 0)
            self.assertEqual(saved["qa_tests"], {})
            self.assertEqual(saved["qa_evidence"], {})
            self.assertEqual(saved["base_sha"], "")
            self.assertEqual(saved["branch"], "")
            self.assertEqual(saved["gate_results"], [])
            self.assertEqual(saved["changed_files"], [])
            self.assertEqual(saved["current_prompt"], "")
            self.assertEqual(saved["current_log"], "")
            self.assertIsNone(saved["code_review"])
            self.assertEqual(saved["approved_head"], "")
            self.assertEqual(saved["pr_url"], "")
            self.assertEqual(saved["receipts"], [])
            self.assertIsNone(saved["budget_override"])
            event = json.loads((repo / ".factory/retry-events/7.json").read_text())
            self.assertTrue(event["spec_changed"])
            self.assertEqual(event["ticket_refresh"]["body"], corrected_body)
            backend.set_status.assert_called_once()

    def test_restart_detects_an_edited_live_ticket_and_discards_old_spec_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            source = Path(__file__).parents[2]
            shutil.copytree(source / "factory", repo / "factory")
            install_approved_charter(repo)
            args = self.factory_args(repo)
            args.mock = False
            args.no_qa = False
            args.profile = "standard"
            args.agent = args.qa_agent = "claude"
            bootstrap = Factory(args)
            plan_id = "live-plan"
            marker = (
                f"<!-- factory-plan:{plan_id}:T7 -->\n"
                f"{governance_marker(bootstrap.governance)}"
            )
            old_body = (
                "## Spec\nCreate the first workflow.\n\n"
                "## Acceptance criteria\n- The first workflow is visible.\n\n"
                "agent: claude\n\n"
                f"{marker}"
            )
            old = {
                "number": 7,
                "title": "First workflow",
                "body": old_body,
                "labels": ["agent-ready"],
                "dependencies": [],
                "agent": "claude",
                "default_agent": "claude",
                "status": "Blocked",
                "phase": "code-review",
                "plan_id": plan_id,
                "planned": True,
                "governance": bootstrap.governance,
                "failure": "Code Review requested changes",
                "attempt": 3,
                "branch": "factory/7-first-workflow",
                "base_sha": "a" * 40,
                "qa_attempt": 1,
                "qa_commit": "b" * 40,
                "qa_tests": {"tests/test_ticket_7.py": "blob"},
                "qa_evidence": {
                    "focused_test_command": "python -m pytest -q tests/test_ticket_7.py",
                    "red": {"result": "RED PROVED"},
                },
                "existing_tests": {"tests/test_existing.py": "blob"},
                "existing_test_changes": ["tests/test_existing.py"],
                "gate_results": [{"name": "tests", "classification": "PASS"}],
                "changed_files": ["src/old.py"],
                "current_prompt": ".factory/prompts/7-attempt3.md",
                "current_log": ".factory/logs/7-attempt3.log",
                "code_review": {"result": {"decision": "REQUEST_CHANGES"}},
                "approved_head": "c" * 40,
                "pr_url": "https://github.test/pull/7",
                "receipts": [".factory/receipts/old-spec.json"],
                "budget_override": {
                    "lines": 1400,
                    "charter_limit": 1200,
                    "reason": "The original ticket required one larger workflow",
                },
                "history": [],
            }
            old["spec_sha256"] = ticket_spec_fingerprint(old)
            state = repo / ".factory/state.json"
            state.parent.mkdir(parents=True, exist_ok=True)
            state.write_text(json.dumps({
                "schema_version": 2,
                "mode": "github",
                "run_id": "live-restart",
                "profile": "standard",
                "governance": bootstrap.governance,
                "tickets": [old],
            }))
            corrected_body = (
                "## Spec\nCreate the corrected workflow.\n\n"
                "## Acceptance criteria\n- The corrected workflow is saved and visible.\n\n"
                "agent: claude\n\n"
                f"{marker}"
            )
            backend = SimpleNamespace(
                project_number=3,
                load=mock.Mock(return_value=[{
                    "number": 7,
                    "title": "Corrected workflow",
                    "body": corrected_body,
                    "labels": ["agent-ready", "state:blocked"],
                    "status": "Blocked",
                    "url": "https://github.test/issues/7",
                    "pr_url": "https://github.test/pull/7",
                }]),
                read_claim=mock.Mock(return_value=None),
                set_status=mock.Mock(),
            )
            restarted = Factory(args)
            restarted.backend = backend

            restarted.load_tickets()

            ticket = restarted.tickets[7]
            self.assertEqual(ticket["status"], "Backlog")
            self.assertEqual(ticket["title"], "Corrected workflow")
            self.assertEqual(ticket["body"], corrected_body)
            self.assertEqual(ticket["branch_generation"], 1)
            for key in (
                "branch", "base_sha", "qa_commit", "approved_head", "pr_url",
                "current_prompt", "current_log",
            ):
                self.assertEqual(ticket[key], "")
            for key in (
                "qa_tests", "qa_evidence", "existing_tests", "gate_results",
                "changed_files", "receipts",
            ):
                self.assertEqual(ticket[key], {} if key in {
                    "qa_tests", "qa_evidence", "existing_tests",
                } else [])
            self.assertIsNone(ticket["code_review"])
            self.assertIsNone(ticket["budget_override"])
            self.assertIn("specification changed", ticket["history"][-1]["note"])
            saved = json.loads(state.read_text())["tickets"][0]
            self.assertEqual(saved["status"], "Backlog")
            self.assertEqual(saved["spec_sha256"], ticket_spec_fingerprint(ticket))
            backend.set_status.assert_called_once()

    def test_configuration_blocker_requires_a_real_contract_change_then_reloads_it(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            repo.mkdir()
            ProjectContract.detect(repo).write()
            install_approved_charter(repo)
            contract = repo / "factory.project.toml"
            blocked_sha = hashlib.sha256(contract.read_bytes()).hexdigest()
            ticket = {
                "number": 5,
                "title": "Nested acceptance test",
                "body": "## Spec\nTest it.\n\n## Acceptance criteria\n- It passes.\n",
                "labels": ["agent-ready"],
                "dependencies": [],
                "agent": "mock",
                "default_agent": "mock",
                "status": "Blocked",
                "phase": "qa",
                "failure": (
                    "QA changed demo-app/tests/test_ticket_5_acceptance.py, "
                    "which is outside the configured test roots"
                ),
                "blocked_project_contract_sha256": blocked_sha,
                "history": [],
            }
            ticket["spec_sha256"] = ticket_spec_fingerprint(ticket)
            running_ticket = json.loads(json.dumps(ticket))
            state = repo / ".factory/state.json"
            state.parent.mkdir()
            state.write_text(json.dumps({"tickets": [ticket]}))

            with self.assertRaisesRegex(SystemExit, "cannot be retried unchanged"):
                retry_ticket(repo, 5, mock=True)

            contract.write_text(contract.read_text().replace(
                'test_roots = ["tests"]',
                'test_roots = ["tests", "demo-app/tests"]',
            ))
            retry_ticket(repo, 5, mock=True)

            event = json.loads((repo / ".factory/retry-events/5.json").read_text())
            self.assertTrue(event["reload_project_configuration"])
            running = Factory.__new__(Factory)
            running.repo = repo
            running.tickets = {5: running_ticket}
            running._sync_store = mock.Mock()
            running.apply_retry_events()
            self.assertIn("demo-app/tests", running.cfg["qa"]["test_roots"])
            self.assertFalse((repo / ".factory/retry-events/5.json").exists())

    def test_recovery_classifier_never_offers_retry_for_claim_or_dependency_blockers(self):
        claim = ticket_recovery({
            "failure": "Remote Ticket claim belongs to another run",
            "remote_claim": {"owner_run_id": "run-123"},
        })
        dependency = ticket_recovery({
            "failure": "Dependency cycle: #1 -> #2 -> #1",
        })
        closed_pr = ticket_recovery({
            "failure": "The remote pull request was closed without merging",
            "next_human_action": "inspect_closed_pull_request",
        })
        stale_merge = ticket_recovery({
            "failure": "Merged pull request head does not match approved revision",
            "next_human_action": "inspect_stale_merge",
        })

        self.assertEqual(claim["action"], "release_or_resume_claim")
        self.assertFalse(claim["retry_allowed"])
        self.assertEqual(dependency["action"], "replan_dependencies")
        self.assertFalse(dependency["retry_allowed"])
        self.assertEqual(closed_pr["kind"], "revision_rebuild")
        self.assertTrue(closed_pr["retry_allowed"])
        self.assertEqual(stale_merge["action"], "create_replacement_ticket")
        self.assertFalse(stale_merge["retry_allowed"])

    def test_scope_conflict_log_requires_ticket_edit_instead_of_blind_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            log = repo / ".factory/logs/5-attempt1.log"
            log.parent.mkdir(parents=True)
            log.write_text(
                "**Handoff Receipt**\n\n"
                "Blocked by scope inconsistency. public/styles.css does not exist and "
                "nothing loads it.\n"
                "Changed paths/commit: none.\n"
                "Resolution requires permission to update public/index.html.\n"
            )
            ticket = {
                "number": 5,
                "failure": "Agent produced no changes or commits.",
                "current_log": ".factory/logs/5-attempt1.log",
                "triage": {"declared_paths": ["public/styles.css"]},
            }

            recovery = ticket_recovery(ticket, repo)

            self.assertEqual(recovery["kind"], "ticket_specification")
            self.assertEqual(recovery["action"], "edit_ticket_and_retry")
            self.assertEqual(recovery["title"], "Expand the Ticket file ownership")
            self.assertTrue(recovery["scope_conflict"])
            self.assertEqual(recovery["required_paths"], ["public/index.html"])
            self.assertIn("Add public/index.html", recovery["summary"])

            ticket.update(
                failure=(
                    "Supervisor blocked dispatch: Three implementation attempts "
                    "produced no acceptable committed output, exceeding the retry limit."
                ),
                current_log="",
            )
            supervisor_recovery = ticket_recovery(ticket, repo)
            self.assertEqual(
                supervisor_recovery["title"],
                "Expand the Ticket file ownership",
            )

    def test_scope_conflict_stops_without_consuming_identical_retries(self):
        factory = Factory.__new__(Factory)
        factory.cfg = {"factory": {"max_retries": 2}}
        factory.transition = mock.Mock()
        ticket = {"attempt": 1, "metrics": {}}

        retried = factory.block_or_retry(
            ticket,
            "TICKET_SCOPE_CONFLICT: public/index.html must be added to File ownership.",
        )

        self.assertFalse(retried)
        factory.transition.assert_called_once_with(
            ticket,
            "Blocked",
            "Ticket scope cannot produce a functional change; edit its file ownership",
        )
        self.assertNotIn("retry_count", ticket["metrics"])

    def test_qa_harness_defect_is_recovered_from_the_latest_implementation_log(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            log = repo / ".factory/logs/6-attempt3.log"
            log.parent.mkdir(parents=True)
            handoff = (
                "**Handoff Receipt**\n\n"
                "Blocked by immutable QA harness defects in the protected test.\n"
                "The verification regex always captures an empty string and nested "
                "node --test is suppressed. The QA harness must be corrected.\n"
                "No new commit was made because implementation cannot make the "
                "protected acceptance test pass.\n"
            )
            log.write_text(handoff)
            ticket = {
                "number": 6,
                "phase": "verifying",
                "failure": (
                    "Supervisor blocked dispatch: Verification failed twice for "
                    "implementation commit abc123."
                ),
                "current_log": "",
            }

            classified = implementation_no_change_failure(handoff)
            recovery = ticket_recovery(ticket, repo)

            self.assertTrue(classified.startswith("QA_EVIDENCE_DEFECT:"))
            self.assertEqual(recovery["kind"], "qa_evidence")
            self.assertEqual(recovery["action"], "regenerate_qa_tests")
            self.assertFalse(recovery["retry_allowed"])
            self.assertTrue(recovery["qa_reset_allowed"])

    def test_unchanged_successful_attempt_surfaces_the_qa_harness_defect(self):
        handoff = (
            "**Handoff Receipt**\n"
            "Blocked by immutable QA harness defects in the protected test. "
            "The QA harness must be corrected. No new commit was made because "
            "implementation cannot make the protected test pass."
        )

        failure = implementation_attempt_failure(
            handoff,
            code=0,
            commits=1,
            attempt_start_head="a" * 40,
            candidate_head="a" * 40,
        )

        self.assertTrue(failure.startswith("QA_EVIDENCE_DEFECT:"))

    def test_qa_harness_defect_stops_without_consuming_identical_retries(self):
        factory = Factory.__new__(Factory)
        factory.cfg = {"factory": {"max_retries": 2}}
        factory.transition = mock.Mock()
        ticket = {"attempt": 2, "metrics": {}}

        retried = factory.block_or_retry(
            ticket,
            "QA_EVIDENCE_DEFECT: protected test harness must be corrected.",
        )

        self.assertFalse(retried)
        factory.transition.assert_called_once_with(
            ticket,
            "Blocked",
            "Protected QA is defective; regenerate its tests before retrying",
        )
        self.assertNotIn("retry_count", ticket["metrics"])

    def test_reset_qa_retry_discards_defective_evidence_and_preserves_qa_context(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            state = repo / ".factory/state.json"
            state.parent.mkdir(parents=True)
            install_approved_charter(repo)
            log = repo / ".factory/logs/6-attempt3.log"
            log.parent.mkdir(parents=True)
            log.write_text(
                "**Handoff Receipt**\n\n"
                "Blocked by immutable QA harness defects in the protected test. "
                "The QA harness must be corrected. No new commit was made because "
                "implementation cannot make the protected acceptance test pass.\n"
            )
            state.write_text(json.dumps({"tickets": [{
                "number": 6,
                "status": "Blocked",
                "phase": "verifying",
                "failure": (
                    "Supervisor blocked dispatch: Verification failed twice for "
                    "implementation commit abc123."
                ),
                "attempt": 3,
                "branch": "factory/6-document-verification",
                "branch_generation": 0,
                "base_sha": "a" * 40,
                "qa_attempt": 1,
                "qa_commit": "b" * 40,
                "qa_tests": {"tests/ticket-6.test.js": "blob"},
                "qa_evidence": {"red": {"result": "RED PROVED"}},
                "qa_approved": True,
                "gate_results": [{"name": "tests", "classification": "FAIL"}],
                "changed_files": [{"status": "M", "path": "README.md"}],
                "code_review": {"result": {"decision": "REQUEST_CHANGES"}},
                "approved_head": "c" * 40,
                "pr_url": "https://github.test/pull/6",
                "receipts": [".factory/receipts/old-qa.json"],
                "history": [],
            }]}))

            with self.assertRaisesRegex(
                SystemExit, "cannot be retried unchanged",
            ):
                retry_ticket(repo, 6, mock=True)

            retry_ticket(repo, 6, mock=True, reset_qa=True, assume_yes=True)

            saved = json.loads(state.read_text())["tickets"][0]
            self.assertEqual(saved["status"], "Ready")
            self.assertEqual(saved["branch"], "")
            self.assertEqual(saved["qa_commit"], "")
            self.assertEqual(saved["qa_tests"], {})
            self.assertEqual(saved["qa_evidence"], {})
            self.assertFalse(saved["qa_approved"])
            self.assertEqual(saved["receipts"], [])
            self.assertIn("QA_EVIDENCE_DEFECT:", saved["qa_retry_context"])
            event = json.loads(
                (repo / ".factory/retry-events/6.json").read_text()
            )
            self.assertTrue(event["reset_qa"])
            self.assertTrue(event["force_repository_base"])
            self.assertIn(
                "protected QA tests", event["qa_retry_context"],
            )

            saved.update(
                status="In Progress",
                phase="qa",
                branch="factory/6-document-verification-r1",
                qa_retry_context="",
            )
            state.write_text(json.dumps({"tickets": [saved]}))
            (repo / ".factory/retry-events/6.json").unlink()

            retry_ticket(repo, 6, mock=True, reset_qa=True, assume_yes=True)

            interrupted = json.loads(state.read_text())["tickets"][0]
            self.assertEqual(interrupted["status"], "Ready")
            self.assertIn("QA_EVIDENCE_DEFECT:", interrupted["qa_retry_context"])
            self.assertIn(
                "interrupted QA regeneration",
                interrupted["history"][-2]["note"],
            )

    def test_ticket_reload_preserves_qa_recovery_context_after_interruption(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            repo.mkdir()
            install_approved_charter(repo)
            args = self.factory_args(repo)
            bootstrap = Factory(args)
            state = repo / ".factory/state.json"
            state.parent.mkdir(exist_ok=True)
            state.write_text(json.dumps({
                "mode": "mock",
                "run_id": "qa-recovery-run",
                "profile": "lean",
                "governance": bootstrap.governance,
                "tickets": [{
                    "number": 6,
                    "title": "Document verification",
                    "body": (
                        "## Spec\nDocument it.\n\n"
                        "## Acceptance criteria\n- Verification is reproducible.\n"
                    ),
                    "labels": ["agent-ready"],
                    "status": "In Progress",
                    "phase": "qa",
                    "agent": "mock",
                    "default_agent": "mock",
                    "dependencies": [],
                    "branch": "factory/6-document-verification-r1",
                    "branch_generation": 1,
                    "qa_retry_context": (
                        "QA_EVIDENCE_DEFECT: nested node --test is suppressed"
                    ),
                    "history": [],
                }],
            }))

            restarted = Factory(args)
            restarted.load_tickets(source=[{
                "number": 6,
                "title": "Document verification",
                "body": (
                    "## Spec\nDocument it.\n\n"
                    "## Acceptance criteria\n- Verification is reproducible.\n"
                ),
                "labels": ["agent-ready"],
                "status": "In Progress",
            }])

            ticket = restarted.tickets[6]
            self.assertEqual(ticket["status"], "Backlog")
            self.assertEqual(
                ticket["qa_retry_context"],
                "QA_EVIDENCE_DEFECT: nested node --test is suppressed",
            )

    def test_existing_run_cannot_switch_between_rehearsal_and_live(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            source = Path(__file__).parents[2]
            shutil.copytree(source / "factory", repo / "factory")
            install_approved_charter(repo)
            args = self.factory_args(repo)
            factory = Factory(args)
            factory.load_tickets()
            args.mock = False

            with self.assertRaisesRegex(ValueError, "Live and Rehearsal runs cannot share"):
                Factory(args)

    def test_live_human_merge_rejects_rehearsal_evidence_before_the_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            state_path = repo / ".factory/state.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(json.dumps({
                "mode": "mock",
                "tickets": [{
                    "number": 5,
                    "status": "In Review",
                    "review_ref": "rehearsal://ticket/5/attempt/1",
                    "pr_url": "",
                }],
            }))

            with self.assertRaisesRegex(
                ValueError,
                "contains Rehearsal evidence and cannot be merged as Live",
            ):
                human_merge_ticket(
                    repo, 5, mock=False, project_number=15, assume_yes=True,
                )

    def test_live_evidence_export_republishes_actual_packet_record(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            state_path = repo / ".factory/state.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(json.dumps({
                "mode": "github",
                "run_id": "run-evidence",
                "profile": "standard",
                "governance": {},
                "tickets": [{
                    "number": 7,
                    "plan_id": "plan-evidence",
                    "status": "Done",
                    "evidence_packet": {
                        "status": "available",
                        "path": ".factory/evidence/plan-evidence/evidence-packet.md",
                        "manifest": ".factory/evidence/plan-evidence/manifest.json",
                        "sha256": "e" * 64,
                    },
                }],
            }))
            backend = mock.Mock()
            backend.publish_run_summary.return_value = {
                "published": True,
                "mode": "issue-comment",
            }

            with mock.patch("orchestrator.GitHubBackend", return_value=backend):
                count = publish_evidence_run_summaries(
                    repo,
                    {
                        "github_repository": "https://github.com/example/repo",
                        "project_number": 3,
                    },
                    "plan-evidence",
                    [7],
                )

            self.assertEqual(count, 1)
            backend.preflight.assert_called_once_with()
            published = backend.publish_run_summary.call_args.args[2]
            self.assertIn('"status": "available"', published)
            self.assertIn('"sha256": "' + "e" * 64 + '"', published)
            updated = json.loads(state_path.read_text())
            self.assertTrue(updated["tickets"][0]["remote_run_summary"]["published"])

    def test_live_human_merge_preflights_its_fresh_github_backend(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            factory = repo / "factory"
            factory.mkdir(parents=True)
            source = Path(__file__).parents[1]
            shutil.copy2(source / "roles.json", factory / "roles.json")
            shutil.copy2(source / "policy.json", factory / "policy.json")
            install_approved_charter(repo)
            charter = FactoryCharter.load(repo, require_approved=True)
            approved_head = "a" * 40
            merged_head = "b" * 40
            state_path = repo / ".factory/state.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(json.dumps({
                "governance": {
                    "charter_sha256": charter.policy_sha256(),
                    "merge_authority": "human",
                },
                "tickets": [{
                    "number": 7,
                    "title": "Deliver one approved slice",
                    "status": "In Review",
                    "phase": "in-review",
                    "attempt": 1,
                    "approved_head": approved_head,
                    "gate_results": [{"name": "tests", "required": True, "exit_code": 0}],
                    "code_review": {
                        "head": approved_head,
                        "result": {"decision": "APPROVE"},
                        "artifact": ".factory/reviews/ticket-7.json",
                    },
                    "branch": "factory/7-approved-slice",
                    "pr_url": "https://github.test/example/pull/7",
                    "plan_id": "live-merge",
                    "receipts": [],
                    "history": [],
                }],
            }))
            backend = mock.Mock(unsafe=True)
            backend.default_branch = "main"
            backend.merged_pr.return_value = {
                "headRefOid": approved_head,
                "mergeCommit": {"oid": merged_head},
            }

            def fake_run(command, *_args, **_kwargs):
                stdout = approved_head if command[:2] == ["git", "rev-parse"] else ""
                return subprocess.CompletedProcess(command, 0, stdout, "")

            with mock.patch("orchestrator.GitHubBackend", return_value=backend), mock.patch(
                "orchestrator.run", side_effect=fake_run,
            ):
                human_merge_ticket(
                    repo, 7, mock=False, project_number=8, assume_yes=True,
                )

            backend.preflight.assert_called_once_with()
            backend.close_issue.assert_called_once()

    def test_path_specific_human_gate_can_merge_under_autonomous_demo_governance(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            factory = repo / "factory"
            factory.mkdir(parents=True)
            source = Path(__file__).parents[1]
            shutil.copy2(source / "roles.json", factory / "roles.json")
            shutil.copy2(source / "policy.json", factory / "policy.json")
            install_approved_charter(repo, merge_authority="supervisor")
            charter = FactoryCharter.load(repo, require_approved=True)
            approved_head = "a" * 40
            merged_head = "b" * 40
            state_path = repo / ".factory/state.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(json.dumps({
                "governance": {
                    "charter_sha256": charter.policy_sha256(),
                    "merge_authority": "supervisor",
                },
                "tickets": [{
                    "number": 8,
                    "title": "Change a path that requires human approval",
                    "status": "In Review",
                    "phase": "in-review",
                    "attempt": 1,
                    "approved_head": approved_head,
                    "triage": {"controls": {"requires_human_approval": True}},
                    "gate_results": [{"name": "tests", "required": True, "exit_code": 0}],
                    "code_review": {
                        "head": approved_head,
                        "result": {"decision": "APPROVE"},
                        "artifact": ".factory/reviews/ticket-8.json",
                    },
                    "branch": "factory/8-human-owned-path",
                    "pr_url": "https://github.test/example/pull/8",
                    "plan_id": "autonomous-path-gate",
                    "receipts": [],
                    "history": [],
                }],
            }))
            backend = mock.Mock(unsafe=True)
            backend.default_branch = "main"
            backend.merged_pr.return_value = {
                "headRefOid": approved_head,
                "mergeCommit": {"oid": merged_head},
            }

            def fake_run(command, *_args, **_kwargs):
                stdout = approved_head if command[:2] == ["git", "rev-parse"] else ""
                return subprocess.CompletedProcess(command, 0, stdout, "")

            with mock.patch("orchestrator.GitHubBackend", return_value=backend), mock.patch(
                "orchestrator.run", side_effect=fake_run,
            ):
                human_merge_ticket(
                    repo, 8, mock=False, project_number=8, assume_yes=True,
                )

            backend.preflight.assert_called_once_with()
            backend.close_issue.assert_called_once()

    def test_publish_repository_setup_commits_and_pushes_only_approved_governance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            remote = root / "remote.git"
            repo.mkdir()
            git(repo, "init", "-q", "-b", "main")
            git(repo, "config", "user.name", "Factory Test")
            git(repo, "config", "user.email", "factory@example.test")
            git(root, "init", "-q", "--bare", str(remote))
            git(repo, "remote", "add", "origin", str(remote))
            project = ProjectContract.detect(repo)
            project.write()
            charter = FactoryCharter.draft(repo, project)
            charter.write()
            charter.approve()
            (repo / ".gitignore").write_text(".factory/\n")

            commit = publish_repository_setup(repo, assume_yes=True)

            self.assertEqual(commit, git(repo, "rev-parse", "HEAD"))
            self.assertEqual(commit, git(root, "--git-dir", str(remote), "rev-parse", "refs/heads/main"))
            self.assertEqual(
                set(git(repo, "show", "--pretty=", "--name-only", "HEAD").splitlines()),
                {".gitignore", "factory.charter.toml", "factory.project.toml"},
            )

    def test_worktree_paths_are_scoped_to_the_repository(self):
        root = Path("/tmp/workshops")
        first = worktree_path(root / "attendee-one", 4)
        second = worktree_path(root / "attendee-two", 4)

        self.assertEqual(first, root / "attendee-one-wt-4")
        self.assertEqual(second, root / "attendee-two-wt-4")
        self.assertNotEqual(first, second)

    def test_dispatch_pauses_when_human_review_capacity_is_full(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            source = Path(__file__).parents[2]
            shutil.copytree(source / "factory", repo / "factory")
            install_approved_charter(repo)
            factory = Factory(self.factory_args(repo))
            ready = {"number": 9, "status": "Ready", "history": []}
            factory.tickets = {
                1: {"number": 1, "status": "In Review", "history": []},
                2: {"number": 2, "status": "QA Review", "history": []},
                3: {"number": 3, "status": "In Review", "history": []},
                9: ready,
            }

            self.assertEqual(factory.coordinate_ready([ready]), [])
            attention = factory.store.data["human_attention"]
            self.assertTrue(attention["dispatch_paused"])
            self.assertEqual(attention["awaiting_review"], 3)
            self.assertEqual(attention["review_limit"], 3)
            self.assertIn("queue 3 / limit 3", attention["reason"])
            factory.tickets[1]["status"] = "Done"
            resumed = factory.coordinate_ready([ready])
            self.assertEqual(resumed, [ready])
            self.assertFalse(factory.store.data["human_attention"]["dispatch_paused"])

    def test_losing_remote_claim_never_creates_a_worktree_or_starts_an_agent(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            source = Path(__file__).parents[2]
            shutil.copytree(source / "factory", repo / "factory")
            install_approved_charter(repo)
            factory = Factory(self.factory_args(repo))
            factory.backend = mock.Mock()
            factory.backend.claim_ticket.return_value = {
                "owned": False,
                "owner_run_id": "other-run",
                "ref": "refs/heads/factory-claims/ticket-9",
            }
            ticket = {
                "number": 9, "title": "Claimed work", "status": "Ready",
                "history": [], "failure": "", "branch": "", "qa_commit": "",
                "qa_approved": False,
            }
            factory.tickets = {9: ticket}

            with mock.patch.object(
                factory, "git", return_value=SimpleNamespace(stdout="a" * 40 + "\n")
            ), mock.patch.object(factory, "create_worktree") as create:
                factory.process(ticket)

            create.assert_not_called()
            self.assertEqual(ticket["status"], "Blocked")
            self.assertIn("other-run", ticket["failure"])

    def factory_args(self, repo: Path):
        return SimpleNamespace(
            repo=str(repo), qa_agent=None, no_qa=True, mock=True, project_number=None,
            review_qa_tests=False, scenario="tv", agent="mock", dry_run=False,
            max_parallel=1, once=True, profile="lean",
        )

    def test_default_branch_sync_fast_forwards_before_new_work(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, remote, checkout = root / "source", root / "remote.git", root / "checkout"
            source.mkdir()
            git(source, "init", "-q", "-b", "main")
            git(source, "config", "user.name", "Factory Test")
            git(source, "config", "user.email", "factory@example.test")
            (source / ".gitignore").write_text(".factory/\n")
            (source / "value.txt").write_text("one\n")
            install_approved_charter(source)
            git(source, "add", ".")
            git(source, "commit", "-qm", "one")
            git(root, "clone", "-q", "--bare", str(source), str(remote))
            git(root, "clone", "-q", str(remote), str(checkout))
            git(source, "remote", "add", "origin", str(remote))
            (source / "value.txt").write_text("two\n")
            git(source, "add", "value.txt")
            git(source, "commit", "-qm", "two")
            git(source, "push", "-q", "origin", "main")

            factory = Factory(self.factory_args(checkout))
            factory.backend = SimpleNamespace(default_branch="main")
            synced = factory.sync_default_branch()
            self.assertEqual((checkout / "value.txt").read_text(), "two\n")
            self.assertEqual(synced, git(source, "rev-parse", "HEAD"))

    def test_blocked_state_retains_the_phase_where_failure_occurred(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            repo.mkdir()
            install_approved_charter(repo)
            factory = Factory(self.factory_args(repo))
            ticket = {
                "number": 7,
                "status": "Verifying",
                "phase": "verifying",
                "history": [],
            }
            factory.tickets = {7: ticket}

            factory.transition(ticket, "Blocked", "Required gate failed")

            self.assertEqual(ticket["status"], "Blocked")
            self.assertEqual(ticket["phase"], "verifying")

    def test_fresh_checkout_recovers_exact_pr_review_and_next_human_action(self):
        approved = "d" * 40
        summary = {
            "schema_version": 1,
            "run_id": "remote-run",
            "ticket": 7,
            "status": "In Review",
            "plan_id": "plan12345",
            "revisions": {"base": "a" * 40, "qa": "b" * 40, "approved_head": approved},
            "verdicts": {"red": "RED PROVED", "green": "GREEN PROVED", "code_review": "APPROVE"},
            "gates": [{"name": "tests", "required": True, "classification": "PASS", "exit_code": 0}],
            "human_decisions": {
                "qa_approved": True,
                "merge_executed_by": "",
                "diff_budget_override": {
                    "lines": 1200,
                    "charter_limit": 800,
                    "reason": "The approved UI workflow remains one outcome",
                    "approved_at": "2026-08-25T21:00:00+00:00",
                    "approved_by": "human",
                },
            },
            "metrics": {
                "attempts": 2,
                "qa_attempts": 1,
                "retry_count": 1,
                "implementation_lines": 990,
                "protected_qa_lines": 799,
                "effective_diff_limit": 1200,
            },
        }
        raw = {
            "status": "In Review",
            "pr_url": "https://github.test/pull/9",
            "pull_request": {
                "state": "OPEN", "mergedAt": None, "headRefName": "factory/7-slice",
                "headRefOid": approved, "mergeCommit": None,
            },
        }

        recovered = recover_remote_ticket_state(raw, summary)

        self.assertEqual(recovered["status"], "In Review")
        self.assertEqual(recovered["approved_head"], approved)
        self.assertEqual(recovered["branch"], "factory/7-slice")
        self.assertEqual(recovered["code_review"]["result"]["decision"], "APPROVE")
        self.assertTrue(recovered["qa_approved"])
        self.assertEqual(recovered["budget_override"]["lines"], 1200)
        self.assertEqual(recovered["diff_budget"]["implementation_lines"], 990)
        self.assertEqual(recovered["next_human_action"], "merge_exact_revision")

    def test_fresh_checkout_preserves_path_required_human_merge(self):
        approved = "d" * 40
        summary = {
            "schema_version": 1,
            "run_id": "remote-run",
            "ticket": 7,
            "status": "In Review",
            "governance": {"merge_authority": "supervisor"},
            "revisions": {"approved_head": approved},
            "verdicts": {"code_review": "APPROVE"},
            "human_decisions": {
                "policy_required_human_merge": True,
                "effective_merge_authority": "human",
            },
        }
        raw = {
            "status": "In Review",
            "pull_request": {
                "state": "OPEN", "headRefOid": approved,
            },
        }

        recovered = recover_remote_ticket_state(raw, summary)

        self.assertEqual(recovered["merge_authority"], "human")
        self.assertTrue(recovered["policy_required_human_merge"])

    def test_fresh_checkout_blocks_when_pr_head_no_longer_matches_remote_approval(self):
        summary = {
            "schema_version": 1, "run_id": "remote-run", "ticket": 7,
            "revisions": {"approved_head": "a" * 40},
            "verdicts": {"code_review": "APPROVE"},
        }
        raw = {
            "status": "In Review",
            "pull_request": {"state": "OPEN", "headRefOid": "b" * 40},
        }

        recovered = recover_remote_ticket_state(raw, summary)

        self.assertEqual(recovered["status"], "Blocked")
        self.assertIn("changed after the remote approval", recovered["failure"])
        self.assertEqual(recovered["next_human_action"], "rerun_code_review")

    def test_fresh_checkout_does_not_trust_a_stale_merged_pr_head(self):
        summary = {
            "schema_version": 1,
            "run_id": "remote-run",
            "ticket": 7,
            "revisions": {"approved_head": "a" * 40},
            "verdicts": {"code_review": "APPROVE"},
        }
        raw = {
            "status": "Done",
            "pull_request": {
                "state": "MERGED",
                "mergedAt": "2026-08-24T10:00:00Z",
                "headRefOid": "b" * 40,
                "mergeCommit": {"oid": "c" * 40},
            },
        }

        recovered = recover_remote_ticket_state(raw, summary)

        self.assertEqual(recovered["status"], "Blocked")
        self.assertIn("does not match", recovered["failure"])
        self.assertEqual(recovered["next_human_action"], "inspect_stale_merge")

    def test_load_tickets_reconstructs_remote_pr_and_claim_without_local_state(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            source = Path(__file__).parents[2]
            shutil.copytree(source / "factory", repo / "factory")
            install_approved_charter(repo)
            args = self.factory_args(repo)
            args.mock = False
            args.no_qa = False
            args.profile = "standard"
            args.agent = args.qa_agent = "claude"
            args.supervisor_agent = args.review_agent = "claude"
            factory = Factory(args)
            approved = "d" * 40
            remote_summary = {
                "schema_version": 1, "run_id": "remote-run", "ticket": 7,
                "status": "In Review", "plan_id": "",
                "revisions": {"base": "a" * 40, "qa": "b" * 40, "approved_head": approved},
                "verdicts": {"red": "RED PROVED", "green": "GREEN PROVED", "code_review": "APPROVE"},
                "human_decisions": {"qa_approved": True},
            }
            backend = SimpleNamespace(
                project_number=3,
                load=mock.Mock(return_value=[{
                    "number": 7, "title": "Recovered slice", "body": "", "labels": [],
                    "status": "In Review", "url": "https://github.test/issues/7",
                    "pr_url": "https://github.test/pull/9",
                    "pull_request": {
                        "url": "https://github.test/pull/9", "state": "OPEN",
                        "headRefName": "factory/7-recovered-slice", "headRefOid": approved,
                        "mergedAt": None, "mergeCommit": None,
                    },
                    "remote_run_summary": remote_summary,
                }]),
                read_claim=mock.Mock(return_value={
                    "ticket": 7, "run_id": "remote-run", "owner_run_id": "remote-run",
                    "base_revision": "a" * 40, "claim_sha": "c" * 40,
                }),
                set_status=mock.Mock(),
            )
            factory.backend = backend

            factory.load_tickets()

            ticket = factory.tickets[7]
            self.assertEqual(ticket["status"], "In Review")
            self.assertEqual(ticket["approved_head"], approved)
            self.assertEqual(ticket["remote_claim"]["run_id"], "remote-run")
            self.assertEqual(ticket["next_human_action"], "merge_exact_revision")
            backend.set_status.assert_not_called()

    def test_required_skipped_gate_is_misconfigured_not_green(self):
        factory = Factory.__new__(Factory)
        factory.cfg = {
            "factory": {"gate_timeout": 10},
            "gate": [{
                "name": "tests", "cmd": "printf '1 skipped\\n'",
                "required": True, "level": "full",
            }],
        }
        factory.project = SimpleNamespace(render_command=lambda command, python: command)
        factory.charter = SimpleNamespace(gate_level="full")
        factory.python = sys.executable
        factory._sync_store = mock.Mock()
        ticket = {"triage": {"controls": {"gate_level": "full"}}}

        failure = factory.verify(ticket, Path.cwd())

        self.assertIn("[tests] exit 0", failure)
        self.assertEqual(ticket["gate_results"][0]["classification"], "MISCONFIGURED")

    def test_missing_tool_and_nonzero_skip_are_misconfigured_not_generic_failures(self):
        commands = (
            "factory-command-that-does-not-exist",
            "sh -c \"printf 'required tool unavailable\\n'; exit 2\"",
        )
        for command in commands:
            with self.subTest(command=command):
                factory = Factory.__new__(Factory)
                factory.cfg = {
                    "factory": {"gate_timeout": 10},
                    "gate": [{
                        "name": "tests", "cmd": command,
                        "required": True, "level": "full",
                    }],
                }
                factory.project = SimpleNamespace(render_command=lambda value, python: value)
                factory.charter = SimpleNamespace(gate_level="full")
                factory.python = sys.executable
                factory._sync_store = mock.Mock()
                ticket = {"triage": {"controls": {"gate_level": "full"}}}

                failure = factory.verify(ticket, Path.cwd())

                self.assertIn("MISCONFIGURED", failure)
                self.assertEqual(
                    ticket["gate_results"][0]["classification"], "MISCONFIGURED",
                )

    def test_external_merge_reconciliation_rejects_a_stale_pr_head(self):
        factory = Factory.__new__(Factory)
        ticket = {
            "number": 4,
            "status": "In Review",
            "approved_head": "a" * 40,
            "pr_url": "https://github.test/example/pull/4",
        }
        factory.tickets = {4: ticket}
        factory.backend = mock.Mock()
        factory.backend.default_branch = "main"
        factory.backend.merged_pr.return_value = {
            "headRefOid": "b" * 40,
            "mergeCommit": {"oid": "c" * 40},
        }
        factory.sync_default_branch = mock.Mock(return_value="c" * 40)
        factory.transition = mock.Mock()
        factory.record_receipt = mock.Mock()
        factory.publish_remote_summary = mock.Mock()
        factory.repo = Path("/unused")
        factory.git = mock.Mock(return_value=subprocess.CompletedProcess([], 0, "", ""))

        factory.sync_merged()

        self.assertIn("does not match", ticket["failure"])
        factory.transition.assert_called_once_with(
            ticket, "Blocked", "Merged pull request head does not match the approved revision",
        )
        factory.backend.close_issue.assert_not_called()
        factory.record_receipt.assert_not_called()

    def test_valid_external_merge_closes_issue_only_after_exact_head_validation(self):
        factory = Factory.__new__(Factory)
        approved_head = "a" * 40
        ticket = {
            "number": 5,
            "status": "In Review",
            "approved_head": approved_head,
            "pr_url": "https://github.test/example/pull/5",
            "attempt": 1,
            "receipts": [],
        }
        factory.tickets = {5: ticket}
        factory.backend = mock.Mock()
        factory.backend.default_branch = "main"
        factory.backend.merged_pr.return_value = {
            "headRefOid": approved_head,
            "mergeCommit": {"oid": "c" * 40},
        }
        factory.sync_default_branch = mock.Mock(return_value="c" * 40)
        factory.transition = mock.Mock()
        factory.record_receipt = mock.Mock()
        factory.publish_remote_summary = mock.Mock()
        factory.repo = Path("/unused")
        factory.git = mock.Mock(return_value=subprocess.CompletedProcess([], 0, "", ""))

        factory.sync_merged()

        factory.transition.assert_called_once_with(ticket, "Done", "PR merged and synchronized")
        factory.backend.close_issue.assert_called_once_with(ticket)
        factory.record_receipt.assert_called_once()

    def test_planning_approval_counts_toward_human_attention_capacity(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            source = Path(__file__).parents[2]
            shutil.copytree(source / "factory", repo / "factory")
            install_approved_charter(repo)
            factory = Factory(self.factory_args(repo))
            factory.tickets = {
                1: {"number": 1, "status": "In Review", "history": []},
                2: {"number": 2, "status": "QA Review", "history": []},
            }
            planning_state = repo / ".factory/planning-state.json"
            planning_state.parent.mkdir(parents=True, exist_ok=True)
            planning_state.write_text(json.dumps({
                "plan_id": "plan-needs-product-review",
                "status": "awaiting_product_approval",
                "updated_at": "2026-08-24T09:00:00+00:00",
            }))

            attention = factory.human_attention_snapshot()

            self.assertEqual(attention["awaiting_review"], 2)
            self.assertEqual(attention["planning_approvals"], 1)
            self.assertEqual(attention["awaiting_human"], 3)
            self.assertTrue(attention["dispatch_paused"])
            self.assertEqual(attention["oldest"]["plan_id"], "plan-needs-product-review")

    def test_planning_question_counts_toward_blocked_human_capacity(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            source = Path(__file__).parents[2]
            shutil.copytree(source / "factory", repo / "factory")
            install_approved_charter(repo)
            factory = Factory(self.factory_args(repo))
            factory.tickets = {
                1: {
                    "number": 1,
                    "status": "Blocked",
                    "failure": "Human clarification is required.",
                    "history": [],
                },
            }
            planning_state = repo / ".factory/planning-state.json"
            planning_state.parent.mkdir(parents=True, exist_ok=True)
            planning_state.write_text(json.dumps({
                "plan_id": "plan-needs-an-answer",
                "status": "blocked",
                "updated_at": "2026-08-24T09:00:00+00:00",
                "stages": [{
                    "id": "system_architecture",
                    "title": "System Architecture",
                    "status": "blocked",
                    "questions": ["Which trust boundary owns this data?"],
                }],
            }))

            attention = factory.human_attention_snapshot()

            self.assertEqual(attention["planning_questions"], 1)
            self.assertEqual(attention["blocked_for_human"], 2)
            self.assertTrue(attention["dispatch_paused"])
            self.assertIn("human-blocked queue 2 / limit 2", attention["reason"])

    def test_live_agents_have_no_presentation_timeout(self):
        factory = Factory.__new__(Factory)
        factory.cfg = {"factory": {"agent_timeout": 900}}
        factory.capabilities = {}
        factory.args = SimpleNamespace(mock=False)
        self.assertIsNone(factory.adapter_timeout())

        factory.args.mock = True
        self.assertEqual(factory.adapter_timeout(), 900)

    def test_read_only_role_mutation_is_discarded_and_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            repo.mkdir()
            git(repo, "init", "-q", "-b", "main")
            git(repo, "config", "user.name", "Factory Test")
            git(repo, "config", "user.email", "factory@example.test")
            (repo / "source.txt").write_text("before\n")
            git(repo, "add", ".")
            git(repo, "commit", "-qm", "base")
            before = git(repo, "rev-parse", "HEAD")
            prompt = Path(directory) / "prompt.md"; prompt.write_text("review\n")
            factory = Factory.__new__(Factory)
            factory.repo = repo
            factory.git = lambda *args, cwd=None, **kwargs: subprocess.run(
                ["git", *args], cwd=cwd or repo, text=True, capture_output=True,
                check=kwargs.get("check", True),
            )
            factory.make_role_prompt = mock.Mock(return_value=prompt)
            def mutate(*_args, **_kwargs):
                (repo / "source.txt").write_text("changed\n")
                (repo / "untracked.txt").write_text("leak\n")
                git(repo, "add", "source.txt")
                git(repo, "commit", "-qm", "forbidden review edit")
                return 0, "APPROVE"
            factory.run_adapter = mutate
            factory.verify_qa_tests_unchanged = mock.Mock(return_value="")
            factory.record_receipt = mock.Mock()
            ticket = {"number": 4, "agent": "codex", "attempt": 1}

            failure = factory.run_profile_role(
                ticket, repo, "critic", before, read_only=True,
            )

            self.assertIn("modified the worktree", failure)
            self.assertEqual(git(repo, "rev-parse", "HEAD"), before)
            self.assertEqual((repo / "source.txt").read_text(), "before\n")
            self.assertFalse((repo / "untracked.txt").exists())

    def test_rehearsal_loads_materialized_approved_slices_before_static_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            source = Path(__file__).parents[2]
            shutil.copytree(source / "factory", repo / "factory")
            install_approved_charter(repo)
            plan_id = "approved-plan"
            governance = FactoryCharter.load(repo, require_approved=True).governance("lean")
            tickets_path = repo / ".factory/rehearsal" / plan_id / "tickets.json"
            tickets_path.parent.mkdir(parents=True)
            tickets_path.write_text(json.dumps([{
                "number": 1,
                "title": "Approved PRD-derived slice",
                "body": (
                    f"## Spec\nReviewed behavior\n\nagent: mock\n\n"
                    f"<!-- factory-plan:{plan_id}:T1 -->\n{governance_marker(governance)}"
                ),
                "labels": ["agent-ready"],
                "mock_action": "recipe-api",
            }]))
            latest = repo / ".factory/plans/latest.json"
            latest.parent.mkdir(parents=True, exist_ok=True)
            latest.write_text(json.dumps({"plan_id": plan_id}))

            factory = Factory(self.factory_args(repo))
            factory.load_tickets()

            self.assertEqual(factory.tickets[1]["title"], "Approved PRD-derived slice")
            self.assertEqual(factory.tickets[1]["plan_id"], plan_id)

    def test_execution_rejects_a_ticket_planned_under_different_governance(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            source = Path(__file__).parents[2]
            shutil.copytree(source / "factory", repo / "factory")
            install_approved_charter(repo)
            charter = FactoryCharter.load(repo, require_approved=True)
            drifted = charter.governance("standard")
            plan_id = "drifted-plan"
            tickets_path = repo / ".factory/rehearsal" / plan_id / "tickets.json"
            tickets_path.parent.mkdir(parents=True)
            tickets_path.write_text(json.dumps([{
                "number": 1,
                "title": "Slice planned with another profile",
                "body": (
                    f"## Spec\nReviewed behavior\n\nagent: mock\n\n"
                    f"<!-- factory-plan:{plan_id}:T1 -->\n{governance_marker(drifted)}"
                ),
                "labels": ["agent-ready"],
                "mock_action": "recipe-api",
            }]))
            latest = repo / ".factory/plans/latest.json"
            latest.parent.mkdir(parents=True, exist_ok=True)
            latest.write_text(json.dumps({"plan_id": plan_id}))

            factory = Factory(self.factory_args(repo))
            with self.assertRaisesRegex(ValueError, "governance does not match"):
                factory.load_tickets()

    def test_legacy_approved_tickets_fail_with_a_governance_migration_instruction(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            source = Path(__file__).parents[2]
            shutil.copytree(source / "factory", repo / "factory")
            install_approved_charter(repo)
            plan_id = "legacy-plan"
            tickets_path = repo / ".factory/rehearsal" / plan_id / "tickets.json"
            tickets_path.parent.mkdir(parents=True)
            tickets_path.write_text(json.dumps([{
                "number": 1,
                "title": "Legacy approved slice",
                "body": (
                    f"## Spec\nReviewed behavior\n\nagent: mock\n\n"
                    f"<!-- factory-plan:{plan_id}:T1 -->"
                ),
                "labels": ["agent-ready"],
                "mock_action": "recipe-api",
            }]))
            latest = repo / ".factory/plans/latest.json"
            latest.parent.mkdir(parents=True, exist_ok=True)
            latest.write_text(json.dumps({"plan_id": plan_id}))

            factory = Factory(self.factory_args(repo))
            with self.assertRaisesRegex(ValueError, "predates governed Tickets.*republish"):
                factory.load_tickets()

    def test_existing_run_cannot_silently_switch_to_a_new_charter_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            source = Path(__file__).parents[2]
            shutil.copytree(source / "factory", repo / "factory")
            install_approved_charter(repo)
            args = self.factory_args(repo)
            Factory(args).load_tickets()

            charter_path = repo / "factory.charter.toml"
            charter_path.write_text(
                charter_path.read_text().replace(
                    "max_diff_lines = 1200", "max_diff_lines = 1201",
                )
            )
            FactoryCharter.load(repo).approve()

            with self.assertRaisesRegex(ValueError, "Factory Run governance changed.*reset"):
                Factory(args)

    def test_existing_standard_qa_run_requires_causal_evidence_migration(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            source = Path(__file__).parents[2]
            shutil.copytree(source / "factory", repo / "factory")
            install_approved_charter(repo)
            args = self.factory_args(repo)
            args.profile = "standard"
            args.no_qa = False
            governance = Factory(args).governance
            state_path = repo / ".factory/state.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(json.dumps({
                "profile": "standard",
                "governance": governance,
                "tickets": [{"number": 12, "qa_commit": "abc123", "qa_tests": {"tests/test_x.py": "blob"}}],
            }))

            with self.assertRaisesRegex(ValueError, "predates causal Acceptance Test evidence"):
                Factory(args)

    def test_recovered_exact_merged_completion_does_not_block_new_tickets(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            source = Path(__file__).parents[2]
            shutil.copytree(source / "factory", repo / "factory")
            install_approved_charter(repo)
            args = self.factory_args(repo)
            args.profile = "standard"
            args.no_qa = False
            governance = Factory(args).governance
            state_path = repo / ".factory/state.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(json.dumps({
                "profile": "standard",
                "governance": governance,
                "tickets": [{
                    "number": 1,
                    "status": "Done",
                    "qa_commit": "qa123",
                    "qa_evidence": {
                        "red": {
                            "result": "RED PROVED",
                            "recovered": True,
                        },
                        "green": {
                            "result": "GREEN PROVED",
                            "recovered": True,
                        },
                    },
                    "pr_url": "https://github.test/pull/1",
                    "pr_state": "MERGED",
                    "pr_merged_at": "2026-08-25T17:34:27Z",
                    "pr_head": "candidate123",
                    "approved_head": "candidate123",
                    "remote_run_summary": {
                        "recovered": True,
                        "run_id": "recovered-run",
                    },
                }],
            }))

            restarted = Factory(args)

            self.assertEqual(restarted.store.data["tickets"][0]["status"], "Done")

    def test_current_failed_red_evidence_remains_a_recoverable_ticket_blocker(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            source = Path(__file__).parents[2]
            shutil.copytree(source / "factory", repo / "factory")
            install_approved_charter(repo)
            args = self.factory_args(repo)
            args.profile = "standard"
            args.no_qa = False
            governance = Factory(args).governance
            state_path = repo / ".factory/state.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(json.dumps({
                "mode": "mock",
                "profile": "standard",
                "governance": governance,
                "tickets": [{
                    "number": 12,
                    "status": "Blocked",
                    "qa_commit": "abc123",
                    "qa_tests": {"tests/test_x.py": "blob"},
                    "qa_evidence": {
                        "focused_test_command": "python -m pytest -q tests/test_x.py",
                        "red": {
                            "result": "RED NOT PROVED",
                            "classification": "unrelated_failure",
                        },
                    },
                }],
            }))

            restarted = Factory(args)

            self.assertEqual(
                restarted.store.data["tickets"][0]["status"], "Blocked",
            )

    def test_qa_approval_writes_resume_marker_after_hash_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            worktree = Path(directory) / "repo-wt-12"
            repo.mkdir(); worktree.mkdir()
            git(worktree, "init", "-q", "-b", "main")
            git(worktree, "config", "user.name", "Factory Test")
            git(worktree, "config", "user.email", "factory@example.test")
            test = worktree / "demo-app/tests/test_ticket_12_search.py"
            test.parent.mkdir(parents=True)
            test.write_text("def test_search():\n    assert True\n")
            git(worktree, "add", ".")
            git(worktree, "commit", "-qm", "qa tests")
            commit = git(worktree, "rev-parse", "HEAD")
            blob = git(worktree, "hash-object", "demo-app/tests/test_ticket_12_search.py")
            state = {
                "tickets": [{
                    "number": 12, "title": "Search", "status": "QA Review",
                    "qa_commit": commit,
                    "qa_tests": {"demo-app/tests/test_ticket_12_search.py": blob},
                }],
            }
            state_path = repo / ".factory/state.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(json.dumps(state))
            with self.assertRaisesRegex(ValueError, "RED PROVED"):
                approve_qa_tests(repo, 12, assume_yes=True)
            state["tickets"][0]["qa_evidence"] = {
                "focused_test_command": "python -m pytest -q demo-app/tests/test_ticket_12_search.py",
                "focused_test_command_sha256": Factory._command_sha256(
                    "python -m pytest -q demo-app/tests/test_ticket_12_search.py"
                ),
                "test_revision": commit,
                "red": {
                    "result": "RED PROVED",
                    "classification": "behavior_assertion",
                    "revision": commit,
                    "output": "assertion failed because search is not implemented",
                },
            }
            state_path.write_text(json.dumps(state))
            approve_qa_tests(repo, 12, assume_yes=True)
            self.assertTrue((repo / ".factory/qa-approvals/12").is_file())

    def test_human_can_request_an_exact_qa_revision_with_feedback(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            worktree = Path(directory) / "repo-wt-12"
            repo.mkdir(); worktree.mkdir()
            git(worktree, "init", "-q", "-b", "factory/12-search")
            git(worktree, "config", "user.name", "Factory Test")
            git(worktree, "config", "user.email", "factory@example.test")
            test = worktree / "tests/test_ticket_12_search.py"
            test.parent.mkdir(parents=True)
            test.write_text("def test_search():\n    assert False\n")
            git(worktree, "add", ".")
            git(worktree, "commit", "-qm", "qa tests")
            commit = git(worktree, "rev-parse", "HEAD")
            blob = git(worktree, "hash-object", "tests/test_ticket_12_search.py")
            ticket = {
                "number": 12,
                "title": "Search",
                "status": "QA Review",
                "phase": "qa-review",
                "branch": "factory/12-search",
                "branch_generation": 0,
                "qa_revision": 1,
                "qa_commit": commit,
                "qa_tests": {"tests/test_ticket_12_search.py": blob},
                "qa_evidence": {
                    "red": {
                        "result": "RED PROVED",
                        "classification": "behavior_assertion",
                        "revision": commit,
                    },
                },
                "qa_approved": False,
                "history": [],
            }
            state_path = repo / ".factory/state.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(json.dumps({"tickets": [ticket]}))
            approval = repo / ".factory/qa-approvals/12"
            approval.parent.mkdir(parents=True)
            approval.write_text("pending\n")

            request_qa_test_changes(
                repo,
                12,
                "Use public search behavior and cover the empty-query boundary.",
                assume_yes=True,
            )

            event_path = repo / ".factory/qa-revision-events/12.json"
            event = json.loads(event_path.read_text())
            self.assertEqual(event["qa_commit"], commit)
            self.assertIn("empty-query boundary", event["feedback"])

            factory = Factory.__new__(Factory)
            factory.repo = repo
            factory.tickets = {12: ticket}
            factory.backend = None
            factory._sync_store = mock.Mock()

            def transition(item, status, note):
                item["status"] = status
                item["phase"] = status.lower().replace(" ", "-")
                item.setdefault("history", []).append({
                    "at": "now",
                    "status": status,
                    "note": note,
                })

            factory.transition = transition
            factory.apply_qa_revision_events()

            self.assertEqual(ticket["status"], "Ready")
            self.assertEqual(ticket["qa_revision"], 2)
            self.assertEqual(
                ticket["qa_revision_feedback"],
                "Use public search behavior and cover the empty-query boundary.",
            )
            self.assertEqual(ticket["qa_commit"], "")
            self.assertEqual(ticket["qa_tests"], {})
            self.assertEqual(ticket["qa_evidence"], {})
            self.assertEqual(ticket["branch_generation"], 1)
            self.assertEqual(ticket["qa_revision_history"][0]["qa_commit"], commit)
            self.assertFalse(event_path.exists())
            self.assertFalse(approval.exists())

    def test_qa_revision_request_rejects_a_manually_edited_test(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            worktree = Path(directory) / "repo-wt-3"
            repo.mkdir(); worktree.mkdir()
            git(worktree, "init", "-q", "-b", "factory/3-input")
            test = worktree / "tests/test_ticket_3_input.py"
            test.parent.mkdir(parents=True)
            test.write_text("def test_input():\n    assert False\n")
            expected = git(worktree, "hash-object", "tests/test_ticket_3_input.py")
            state = {
                "tickets": [{
                    "number": 3,
                    "status": "QA Review",
                    "qa_commit": "a" * 40,
                    "qa_tests": {"tests/test_ticket_3_input.py": expected},
                }],
            }
            state_path = repo / ".factory/state.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(json.dumps(state))
            test.write_text("def test_input():\n    assert True\n")

            with self.assertRaisesRegex(
                ValueError, "changed after QA committed it",
            ):
                request_qa_test_changes(
                    repo,
                    3,
                    "Cover repeated remote events.",
                    assume_yes=True,
                )

    def test_version_parser_handles_cli_prefixes(self):
        self.assertEqual(version_tuple("v22.4.1"), (22, 4, 1))
        self.assertEqual(version_tuple("3.11.9"), (3, 11, 9))

    def test_codex_auth_accepts_saved_login_and_managed_credentials_only(self):
        self.assertTrue(codex_auth_ready(0, "Logged in using ChatGPT"))
        self.assertTrue(codex_auth_ready(
            1,
            "Login is not required. OpenAI Codex uses Bedrock via managed credentials.",
        ))
        self.assertFalse(codex_auth_ready(1, "Not logged in"))
        self.assertTrue(codex_uses_managed_bedrock(
            "Login is not required. OpenAI Codex uses Bedrock via managed credentials.",
        ))

    def test_codex_region_uses_environment_then_shared_aws_config(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            config = home / ".aws/config"
            config.parent.mkdir()
            config.write_text("[default]\nregion = us-east-1\n")

            self.assertEqual(
                codex_region_environment({"HOME": str(home)}),
                {"AWS_REGION": "us-east-1", "AWS_DEFAULT_REGION": "us-east-1"},
            )
            self.assertEqual(
                codex_region_environment({
                    "HOME": str(home),
                    "AWS_DEFAULT_REGION": "eu-west-1",
                }),
                {"AWS_REGION": "eu-west-1", "AWS_DEFAULT_REGION": "eu-west-1"},
            )

    def test_codex_resolution_accepts_managed_credentials_wrapper(self):
        candidate = "/managed/bin/codex"
        results = [
            subprocess.CompletedProcess(
                [candidate, "exec", "--help"], 0, "Run Codex non-interactively\nUsage: codex exec", "",
            ),
            subprocess.CompletedProcess(
                [candidate, "login", "status"],
                1,
                "",
                "Login is not required. OpenAI Codex uses Bedrock via managed credentials.",
            ),
        ]
        with (
            mock.patch.dict(
                "os.environ",
                {"FACTORY_CODEX_BIN": candidate, "AWS_REGION": "us-east-1"},
                clear=True,
            ),
            mock.patch("orchestrator.shutil.which", return_value=candidate),
            mock.patch("orchestrator.subprocess.run", side_effect=results),
        ):
            self.assertEqual(resolve_codex_cli(), candidate)

    def test_codex_resolution_rejects_managed_bedrock_without_a_region(self):
        candidate = "/managed/bin/codex"
        results = [
            subprocess.CompletedProcess(
                [candidate, "exec", "--help"], 0, "Run Codex non-interactively\nUsage: codex exec", "",
            ),
            subprocess.CompletedProcess(
                [candidate, "login", "status"],
                1,
                "",
                "Login is not required. OpenAI Codex uses Bedrock via managed credentials.",
            ),
        ]
        with tempfile.TemporaryDirectory() as directory:
            with (
                mock.patch.dict(
                    "os.environ",
                    {"FACTORY_CODEX_BIN": candidate, "HOME": directory},
                    clear=True,
                ),
                mock.patch("orchestrator.subprocess.run", side_effect=results),
            ):
                with self.assertRaisesRegex(RuntimeError, "no AWS region is configured"):
                    resolve_codex_cli()

    def test_full_doctor_reports_missing_region_for_managed_bedrock(self):
        candidate = "/managed/bin/codex"
        config = {
            "agents": {"codex": "codex {prompt}"},
            "agent_capabilities": {
                "codex": SimpleNamespace(
                    execution_environment="local",
                    filesystem_mode="workspace-write",
                    allowed_working_roots=("worktree",),
                    network_expectation="provider-only",
                    supports_read_only=True,
                ),
            },
            "qa": {
                "agent": "codex",
                "max_retries": 1,
                "test_roots": ["tests"],
                "test_file_patterns": ["test_ticket_{ticket}.py"],
            },
            "gate": [{"name": "tests", "cmd": "true"}],
        }

        def command(args, _repo, **_kwargs):
            if args == [candidate, "login", "status"]:
                return subprocess.CompletedProcess(
                    args,
                    1,
                    "",
                    "Login is not required. OpenAI Codex uses Bedrock via managed credentials.",
                )
            if args == [candidate, "exec", "--help"]:
                return subprocess.CompletedProcess(args, 0, "Usage: codex exec", "")
            return subprocess.CompletedProcess(args, 1, "", "unavailable")

        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            ProjectContract.detect(repo).write()
            install_approved_charter(repo)
            output = io.StringIO()
            with (
                mock.patch.dict("os.environ", {"HOME": directory}, clear=True),
                mock.patch("doctor.command", side_effect=command),
                mock.patch("doctor.codex_candidates", return_value=[candidate]),
                mock.patch("doctor.shutil.which", return_value=None),
                mock.patch(
                    "doctor.port_check",
                    return_value=Check("PASS", "port", "available"),
                ),
                contextlib.redirect_stdout(output),
            ):
                run_doctor(repo, config, full=True)

        self.assertRegex(
            output.getvalue(),
            r"\[FAIL\]\s+codex adapter\s+managed Bedrock credentials require an AWS region",
        )

    def test_basic_doctor_does_not_call_agent_authentication(self):
        config = {
            "agents": {},
            "qa": {"agent": "mock-qa", "max_retries": 1, "test_roots": ["tests"]},
            "gate": [{"name": "tests", "cmd": "true"}],
        }
        with tempfile.TemporaryDirectory() as directory:
            with (
                mock.patch("doctor.shutil.which", return_value=None) as which,
                mock.patch("doctor.codex_candidates", side_effect=AssertionError("agent auth called")),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                run_doctor(Path(directory), config, full=False)

        which.assert_not_called()

    def test_doctor_fails_closed_for_missing_unapproved_or_incompatible_charter(self):
        config = {
            "agents": {},
            "qa": {"agent": "mock-qa", "max_retries": 1, "test_roots": ["tests"]},
            "gate": [{"name": "tests", "cmd": "true"}],
        }
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            ProjectContract.detect(repo).write()

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = run_doctor(repo, config, full=False)
            self.assertEqual(result, 1)
            self.assertRegex(output.getvalue(), r"\[FAIL\].*Factory Charter.*not found")

            FactoryCharter.draft(repo, ProjectContract.load(repo)).write()
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = run_doctor(repo, config, full=False)
            self.assertEqual(result, 1)
            self.assertRegex(output.getvalue(), r"\[FAIL\].*Factory Charter.*not approved")

            FactoryCharter.load(repo).approve()
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = run_doctor(
                    repo, config, full=False, profile_name="autonomous-demo",
                )
            self.assertEqual(result, 1)
            self.assertRegex(
                output.getvalue(),
                r"\[FAIL\].*Factory Charter.*requires supervisor merge authority",
            )

    def baseline_repo(self, root: Path) -> Path:
        """Build a repo whose history holds a mobile baseline and a later rehearsal."""
        repo = root / "repo"
        repo.mkdir()
        git(repo, "init", "-q", "-b", "main")
        git(repo, "config", "user.name", "Factory Test")
        git(repo, "config", "user.email", "factory@example.test")
        (repo / "demo-app").mkdir()
        (repo / "demo-app/tests").mkdir()
        (repo / "demo-app/tests/test_app.py").write_text("def test_app():\n    assert True\n")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "chore: establish factory workshop baseline")
        for name in ("test_device_mode.py", "test_rails.py", "test_tv_detail.py"):
            (repo / "demo-app/tests" / name).write_text("def test_tv():\n    assert True\n")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "feat: finish the TV rehearsal")
        return repo

    def test_baseline_check_rejects_tag_left_on_a_finished_rehearsal(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self.baseline_repo(Path(directory))
            git(repo, "tag", "factory-baseline", "HEAD")
            result = baseline_check(repo)
            self.assertEqual(result.level, "FAIL")
            self.assertIn("test_device_mode.py", result.detail)
            self.assertIn("rerun setup_demo.sh", result.detail)

    def test_baseline_check_accepts_the_mobile_workpiece(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self.baseline_repo(Path(directory))
            baseline = git(repo, "rev-list", "--max-count=1", "--grep=^chore: establish", "HEAD")
            git(repo, "tag", "factory-baseline", baseline)
            self.assertEqual(baseline_check(repo).level, "PASS")

    def test_baseline_check_reports_an_unrecoverable_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            repo.mkdir()
            git(repo, "init", "-q", "-b", "main")
            git(repo, "config", "user.name", "Factory Test")
            git(repo, "config", "user.email", "factory@example.test")
            (repo / "demo-app/tests").mkdir(parents=True)
            (repo / "demo-app/tests/test_rails.py").write_text("def test_tv():\n    assert True\n")
            git(repo, "add", ".")
            git(repo, "commit", "-qm", "chore: import workshop without history")
            git(repo, "tag", "factory-baseline", "HEAD")
            result = baseline_check(repo)
            self.assertEqual(result.level, "FAIL")
            self.assertIn("re-clone", result.detail)

    def test_setup_repoints_a_baseline_tag_left_on_a_rehearsal(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self.baseline_repo(Path(directory))
            (repo / "factory").mkdir()
            (repo / "factory/orchestrator.py").write_text("")
            (repo / "demo-app/app.py").write_text("")
            (repo / "demo-app/requirements.txt").write_text("")
            # The script resolves its repository from its own location, so it has
            # to run from a copy inside the fixture rather than from the checkout.
            script = repo / "factory/setup_demo.sh"
            script.write_bytes((Path(__file__).parents[1] / "setup_demo.sh").read_bytes())
            script.chmod(0o755)
            # A stub interpreter keeps the dependency install out of a unit test.
            stub = repo / ".factory/venv/bin"
            stub.mkdir(parents=True)
            (stub / "python").write_text("#!/bin/sh\nexit 0\n")
            (stub / "python").chmod(0o755)
            git(repo, "add", ".")
            git(repo, "commit", "-qm", "chore: add factory scaffolding")
            rehearsal = git(repo, "rev-parse", "HEAD")
            git(repo, "tag", "factory-baseline", rehearsal)
            proc = subprocess.run(
                ["sh", str(script), "--scenario", "recipe-rebrand", "--force"],
                cwd=repo, text=True, capture_output=True, timeout=120,
            )
            tagged = git(repo, "rev-parse", "refs/tags/factory-baseline^{commit}")
            expected = git(repo, "rev-list", "--max-count=1", "--grep=^chore: establish", "HEAD")
            self.assertEqual(tagged, expected, proc.stdout + proc.stderr)
            self.assertNotEqual(tagged, rehearsal)

    def test_start_over_clears_workshop_state_but_keeps_local_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            repo.mkdir()
            git(repo, "init", "-q", "-b", "main")
            git(repo, "config", "user.name", "Factory Test")
            git(repo, "config", "user.email", "factory@example.test")
            (repo / "demo-app").mkdir()
            (repo / "demo-app/app.py").write_text("")
            (repo / "demo-app/requirements.txt").write_text("")
            (repo / "factory").mkdir()
            (repo / "factory/orchestrator.py").write_text("")
            git(repo, "add", ".")
            git(repo, "commit", "-qm", "chore: establish factory workshop baseline")
            (repo / "demo-app/finished.txt").write_text("rehearsal\n")
            git(repo, "add", ".")
            git(repo, "commit", "-qm", "feat: finish rehearsal")

            script = repo / "factory/setup_demo.sh"
            script.write_bytes((Path(__file__).parents[1] / "setup_demo.sh").read_bytes())
            script.chmod(0o755)
            stub = repo / ".factory/venv/bin"
            stub.mkdir(parents=True)
            (stub / "python").write_text("#!/bin/sh\nexit 0\n")
            (stub / "python").chmod(0o755)
            (repo / ".factory/plans/run").mkdir(parents=True)
            (repo / ".factory/plans/run/manifest.json").write_text("{}\n")
            (repo / ".factory/rehearsal/run").mkdir(parents=True)
            (repo / ".factory/rehearsal/run/tickets.json").write_text("[]\n")
            (repo / ".factory/control-center/evidence-run").mkdir(parents=True)
            (repo / ".factory/control-center/evidence-run/evidence-manifest.json").write_text("{}\n")
            (repo / ".factory/control-center/workshop-prd.md").write_text("# PRD\n")
            (repo / ".factory/control-center/factory-canvas.md").write_text("# Canvas\n")
            (repo / ".factory/control-center/operation.json").write_text("{}\n")
            (repo / ".factory/planning-state.json").write_text("{}\n")
            (repo / ".factory/local.toml").write_text("agent = 'claude'\n")

            proc = subprocess.run(
                ["sh", str(script), "--scenario", "recipe-rebrand", "--force", "--start-over"],
                cwd=repo, text=True, capture_output=True, timeout=120,
            )

            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertFalse((repo / ".factory/plans").exists())
            self.assertFalse((repo / ".factory/rehearsal").exists())
            self.assertFalse((repo / ".factory/planning-state.json").exists())
            self.assertFalse((repo / ".factory/control-center/workshop-prd.md").exists())
            self.assertFalse((repo / ".factory/control-center/factory-canvas.md").exists())
            self.assertTrue((repo / ".factory/control-center/operation.json").is_file())
            self.assertTrue((repo / ".factory/local.toml").is_file())
            state = json.loads((repo / ".factory/state.json").read_text())
            self.assertEqual(state["tickets"], [])

    def test_recipe_mobile_ticket_fails_verification_once_then_passes_with_receipts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            source = Path(__file__).parents[2]
            shutil.copytree(source / "factory", repo / "factory")
            shutil.copy2(source / "factory.project.toml", repo / "factory.project.toml")
            baseline_archive = root / "baseline.tar"
            subprocess.run([
                "git", "archive", "--format=tar", "factory-baseline",
                "demo-app", "-o", str(baseline_archive),
            ], cwd=source, check=True)
            subprocess.run([
                "tar", "-xf", str(baseline_archive), "-C", str(repo),
            ], check=True)
            for prerequisite in ("1", "2"):
                shutil.copytree(
                    source / "factory/scenarios/recipe-rebrand/steps" / prerequisite / "demo-app",
                    repo / "demo-app",
                    dirs_exist_ok=True,
                )
            ticket = {
                "number": 3,
                "title": "Build the mobile TableStory experience",
                "labels": ["agent-ready"],
                "mock_action": "recipe-mobile",
                "body": (
                    "## Spec\nBuild mobile browse, detail, and cookbook behavior.\n\n"
                    "## Acceptance criteria\n- TableStory renders\n- Recipe detail opens\n\n"
                    "factory-plan:retry-demo:T3\n\nagent: mock"
                ),
            }
            (repo / "factory/scenarios/recipe-rebrand/tickets.json").write_text(
                json.dumps([ticket], indent=2) + "\n"
            )
            (repo / ".gitignore").write_text(".factory/\n")
            install_approved_charter(repo)
            git(repo, "init", "-q", "-b", "main")
            git(repo, "config", "user.name", "Factory Test")
            git(repo, "config", "user.email", "factory@example.test")
            git(repo, "add", ".")
            git(repo, "commit", "-qm", "baseline")
            args = SimpleNamespace(
                repo=str(repo),
                qa_agent=None,
                no_qa=False,
                mock=True,
                project_number=None,
                review_qa_tests=False,
                scenario="recipe-rebrand",
                agent="mock",
                dry_run=False,
                max_parallel=1,
                once=True,
                profile="standard",
            )

            Factory(args).run_loop()

            state = json.loads((repo / ".factory/state.json").read_text())
            waiting = state["tickets"][0]
            self.assertEqual(waiting["status"], "In Review", waiting.get("failure"))
            self.assertEqual(waiting["attempt"], 2)
            self.assertEqual(waiting["qa_evidence"]["red"]["result"], "RED PROVED")
            self.assertEqual(waiting["qa_evidence"]["green"]["result"], "GREEN PROVED")
            self.assertEqual(
                waiting["qa_evidence"]["focused_test_command_sha256"],
                Factory._command_sha256(waiting["qa_evidence"]["focused_test_command"]),
            )
            self.assertTrue(any(item["note"].startswith("Retry 1") for item in waiting["history"]))
            receipts = [json.loads((repo / path).read_text()) for path in waiting["receipts"]]
            verification = [item for item in receipts if item["role"] == "verification"]
            self.assertEqual([item["claimed_result"] for item in verification], ["Verification failed", "Verification passed"])
            self.assertEqual(
                verification[0]["unresolved_risks"],
                ["Required verification did not pass; inspect gate results in factory state."],
            )
            self.assertEqual(verification[1]["unresolved_risks"], [])
            self.assertIn("RED PROVED", " ".join(verification[1]["verification"]))
            self.assertIn("GREEN PROVED", " ".join(verification[1]["verification"]))
            self.assertEqual(waiting["code_review"]["result"]["decision"], "APPROVE")
            self.assertTrue((repo / waiting["code_review"]["artifact"]).is_file())
            self.assertNotEqual(receipts[-1]["role"], "human_review")

            human_merge_ticket(repo, 3, mock=True, project_number=None, assume_yes=True)

            completed = json.loads((repo / ".factory/state.json").read_text())["tickets"][0]
            merge_event = json.loads((repo / ".factory/merge-events/3.json").read_text())
            receipts = [json.loads((repo / path).read_text()) for path in completed["receipts"]]
            self.assertEqual(completed["status"], "Done", completed.get("failure"))
            self.assertEqual(merge_event["approved_head"], completed["approved_head"])
            self.assertRegex(merge_event["merged_head"], r"^[a-f0-9]{40}$")
            self.assertEqual(receipts[-1]["role"], "human_review")
            self.assertFalse((repo / "demo-app/rehearsal-attempt.txt").exists())

    def test_code_review_rework_stops_at_human_merge_gate_then_exact_head_can_merge(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            source = Path(__file__).parents[2]
            shutil.copytree(source / "factory", repo / "factory")
            shutil.copy2(source / "factory.project.toml", repo / "factory.project.toml")
            baseline_archive = root / "baseline.tar"
            subprocess.run([
                "git", "archive", "--format=tar", "factory-baseline",
                "demo-app", "-o", str(baseline_archive),
            ], cwd=source, check=True)
            subprocess.run(["tar", "-xf", str(baseline_archive), "-C", str(repo)], check=True)
            ticket = {
                "number": 1,
                "title": "Deliver searchable recipe data and API contracts",
                "labels": ["agent-ready"],
                "mock_action": "recipe-api",
                "body": (
                    "## Spec\nAdd deterministic recipe data and lookup APIs.\n\n"
                    "## Acceptance criteria\n- Recipe IDs are unique.\n\n"
                    "factory-plan:review-loop:T1\n\nagent: mock"
                ),
            }
            (repo / "factory/scenarios/recipe-rebrand/tickets.json").write_text(
                json.dumps([ticket], indent=2) + "\n"
            )
            (repo / ".gitignore").write_text(".factory/\n__pycache__/\n*.pyc\n")
            install_approved_charter(repo)
            git(repo, "init", "-q", "-b", "main")
            git(repo, "config", "user.name", "Factory Test")
            git(repo, "config", "user.email", "factory@example.test")
            git(repo, "add", ".")
            git(repo, "commit", "-qm", "baseline")
            args = SimpleNamespace(
                repo=str(repo), qa_agent=None, no_qa=False, mock=True,
                project_number=None, review_qa_tests=False,
                scenario="recipe-rebrand", agent="mock", dry_run=False,
                max_parallel=1, once=True, profile="standard",
            )

            Factory(args).run_loop()

            state = json.loads((repo / ".factory/state.json").read_text())
            waiting = state["tickets"][0]
            self.assertEqual(waiting["status"], "In Review", waiting.get("failure"))
            self.assertEqual(waiting["attempt"], 2)
            self.assertTrue(any(item["note"].startswith("Retry 1") for item in waiting["history"]))
            receipts = [json.loads((repo / path).read_text()) for path in waiting["receipts"]]
            reviews = [item for item in receipts if item["role"] == "code_review"]
            self.assertEqual(
                [item["output_revisions"]["decision"] for item in reviews],
                ["REQUEST_CHANGES", "APPROVE"],
            )
            self.assertNotEqual(receipts[-1]["role"], "human_review")
            self.assertEqual(waiting["merge_authority"], "human")
            self.assertEqual(waiting["approved_head"], waiting["code_review"]["head"])

            human_merge_ticket(repo, 1, mock=True, project_number=None, assume_yes=True)

            completed = json.loads((repo / ".factory/state.json").read_text())["tickets"][0]
            receipts = [json.loads((repo / path).read_text()) for path in completed["receipts"]]
            self.assertEqual(completed["status"], "Done", completed.get("failure"))
            self.assertEqual(receipts[-1]["role"], "human_review")
            self.assertIn("Recipe IDs must be unique", (repo / "demo-app/recipe_api.py").read_text())

    def test_autonomous_demo_requires_opt_in_then_records_supervisor_merge(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            source = Path(__file__).parents[2]
            shutil.copytree(source / "factory", repo / "factory")
            shutil.copy2(source / "factory.project.toml", repo / "factory.project.toml")
            baseline_archive = root / "baseline.tar"
            subprocess.run([
                "git", "archive", "--format=tar", "factory-baseline",
                "demo-app", "-o", str(baseline_archive),
            ], cwd=source, check=True)
            subprocess.run(["tar", "-xf", str(baseline_archive), "-C", str(repo)], check=True)
            ticket = {
                "number": 1,
                "title": "Autonomous Demo recipe API slice",
                "labels": ["agent-ready"],
                "mock_action": "recipe-api",
                "body": (
                    "## Spec\nAdd the recipe API.\n\n"
                    "## Acceptance criteria\n- Recipe data is available.\n\n"
                    "factory-plan:autonomous-demo:T1\n\nagent: mock"
                ),
            }
            (repo / "factory/scenarios/recipe-rebrand/tickets.json").write_text(
                json.dumps([ticket], indent=2) + "\n"
            )
            (repo / ".gitignore").write_text(".factory/\n__pycache__/\n*.pyc\n")
            install_approved_charter(repo, merge_authority="supervisor")
            git(repo, "init", "-q", "-b", "main")
            git(repo, "config", "user.name", "Factory Test")
            git(repo, "config", "user.email", "factory@example.test")
            git(repo, "add", ".")
            git(repo, "commit", "-qm", "baseline")
            args = SimpleNamespace(
                repo=str(repo), qa_agent=None, no_qa=False, mock=True,
                project_number=None, review_qa_tests=False,
                scenario="recipe-rebrand", agent="mock", dry_run=False,
                max_parallel=1, once=True, profile="autonomous-demo",
                allow_autonomous_merge=False,
            )

            with self.assertRaisesRegex(ValueError, "explicit autonomous-merge opt-in"):
                Factory(args)

            args.allow_autonomous_merge = True
            Factory(args).run_loop()

            state = json.loads((repo / ".factory/state.json").read_text())
            completed = state["tickets"][0]
            receipts = [json.loads((repo / path).read_text()) for path in completed["receipts"]]
            self.assertEqual(completed["status"], "Done", completed.get("failure"))
            self.assertEqual(completed["merge_authority"], "supervisor")
            self.assertEqual(completed["merge_executed_by"], "supervisor")
            self.assertTrue(state["governance"]["explicit_autonomy"])
            self.assertEqual(receipts[-1]["role"], "supervisor_merge")

    def test_charter_review_path_keeps_human_merge_in_autonomous_demo(self):
        factory = Factory.__new__(Factory)
        factory.profile = {"merge_authority": "supervisor"}

        self.assertEqual(
            factory.effective_merge_authority({
                "triage": {"controls": {"requires_human_approval": True}},
            }),
            "human",
        )
        self.assertEqual(
            factory.effective_merge_authority({
                "triage": {"controls": {"requires_human_approval": False}},
            }),
            "supervisor",
        )

    def test_live_deterministic_reviewer_requires_release_marker(self):
        factory = Factory.__new__(Factory)
        factory.review_agent = "mock-review"
        factory.args = SimpleNamespace(mock=False, release_smoke_review=True)

        failure = factory.run_code_review(
            {"body": "ordinary Ticket"}, Path("/unused"), "a" * 40,
            "https://github.test/pull/1",
        )

        self.assertIn("restricted to the marked disposable release smoke", failure)

    def test_lean_and_assured_profiles_execute_complete_role_and_gate_sequences(self):
        expected_roles = {
            "lean": ["implementation", "verification", "human_review"],
            "assured": [
                "supervisor",
                "qa",
                "implementation",
                "cleanup",
                "architecture_conformance",
                "hardening",
                "verification",
                "critic",
                "negative_proof",
                "final_verifier",
                "code_review",
                "supervisor",
                "human_review",
            ],
        }
        for profile_name, roles in expected_roles.items():
            with self.subTest(profile=profile_name), tempfile.TemporaryDirectory() as directory:
                repo = Path(directory) / "repo"
                source = Path(__file__).parents[2]
                shutil.copytree(source / "factory", repo / "factory")
                shutil.copy2(source / "factory.project.toml", repo / "factory.project.toml")
                baseline_archive = Path(directory) / "baseline.tar"
                subprocess.run([
                    "git", "archive", "--format=tar", "factory-baseline",
                    "demo-app", "-o", str(baseline_archive),
                ], cwd=source, check=True)
                subprocess.run([
                    "tar", "-xf", str(baseline_archive), "-C", str(repo),
                ], check=True)
                ticket = {
                    "number": 1,
                    "title": f"{profile_name.title()} recipe API slice",
                    "labels": ["agent-ready"],
                    "mock_action": "recipe-api",
                    "body": (
                        "## Spec\nAdd the recipe API.\n\n"
                        "## Acceptance criteria\n- Recipe data is available.\n\n"
                        f"factory-plan:{profile_name}-profile:T1\n\nagent: mock"
                    ),
                }
                (repo / "factory/scenarios/recipe-rebrand/tickets.json").write_text(
                    json.dumps([ticket], indent=2) + "\n"
                )
                (repo / ".gitignore").write_text(".factory/\n__pycache__/\n*.pyc\n")
                install_approved_charter(repo)
                git(repo, "init", "-q", "-b", "main")
                git(repo, "config", "user.name", "Factory Test")
                git(repo, "config", "user.email", "factory@example.test")
                git(repo, "add", ".")
                git(repo, "commit", "-qm", "baseline")
                args = SimpleNamespace(
                    repo=str(repo),
                    qa_agent=None,
                    no_qa=False,
                    mock=True,
                    project_number=None,
                    review_qa_tests=False,
                    scenario="recipe-rebrand",
                    agent="mock",
                    dry_run=False,
                    max_parallel=1,
                    once=True,
                    profile=profile_name,
                )

                Factory(args).run_loop()

                waiting = json.loads((repo / ".factory/state.json").read_text())["tickets"][0]
                self.assertEqual(waiting["status"], "In Review", waiting.get("failure"))

                human_merge_ticket(repo, 1, mock=True, project_number=None, assume_yes=True)

                completed = json.loads((repo / ".factory/state.json").read_text())["tickets"][0]
                receipts = [json.loads((repo / path).read_text()) for path in completed["receipts"]]
                self.assertEqual(completed["status"], "Done", completed.get("failure"))
                self.assertEqual([receipt["role"] for receipt in receipts], roles)
                self.assertTrue(completed["gate_results"])
                self.assertTrue(all(
                    gate["exit_code"] == 0
                    for gate in completed["gate_results"]
                    if gate["required"]
                ))
                self.assertEqual(bool(completed["qa_tests"]), profile_name == "assured")


if __name__ == "__main__":
    unittest.main()
