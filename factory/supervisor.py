"""Validated coordination between the ticket scheduler and a Supervisor role.

Ticket worker roles never mutate lifecycle state or message one another directly. The
orchestrator turns their observed results into Handoff Receipts. At each
dispatch checkpoint this module gives those receipts and the dependency-ready
tickets to a supervisor adapter, validates its structured decision, and returns
only the commands the scheduler is allowed to apply.
"""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from factory_contracts import role_input
from factory_charter import FactoryCharter
from adapter_capabilities import role_environment
from json_response import extract_last_json_object
from adapter_diagnostics import agent_failure_detail
from agent_context import CONTEXT_ACTIVITY, CONTEXT_RECOVERY, claude_configuration_issue, isolated_template, is_context_error, prepare_context


SCHEMA_VERSION = 1
MAX_MESSAGE = 1200
MAX_EVENTS = 50


class SupervisorError(RuntimeError):
    """The supervisor could not produce a safe scheduling decision."""


def adapter_error(code: int, output: str, log: Path, repo: Path) -> SupervisorError:
    detail = agent_failure_detail(output, limit=1000, fallback=False)
    return SupervisorError(
        f"Supervisor adapter exited with code {code}; inspect {log.relative_to(repo)}."
        + (f"\n{detail}" if detail else "")
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path: Path, default):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return default


def _write_json(path: Path, value: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    os.replace(temporary, path)


def _message(value, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SupervisorError(f"Supervisor decision requires {field}.")
    value = value.strip()
    if len(value) > MAX_MESSAGE:
        raise SupervisorError(f"Supervisor {field} is longer than {MAX_MESSAGE} characters.")
    return value


def extract_decision(output: str) -> dict:
    """Return the last JSON object with the supervisor decision fields."""
    value = extract_last_json_object(
        output, {"schema_version", "summary", "dispatch", "block"},
    )
    if value is None:
        raise SupervisorError("Supervisor did not return a structured JSON decision.")
    return value


def validate_decision(raw: dict, candidates: set[int], max_parallel: int) -> dict:
    """Validate and normalize the small interface the scheduler accepts."""
    expected = {"schema_version", "summary", "dispatch", "block"}
    if set(raw) != expected:
        raise SupervisorError(
            "Supervisor decision fields must be exactly " + ", ".join(sorted(expected)) + "."
        )
    if raw["schema_version"] != SCHEMA_VERSION:
        raise SupervisorError(f"Supervisor schema_version must be {SCHEMA_VERSION}.")
    if not isinstance(raw["dispatch"], list) or not isinstance(raw["block"], list):
        raise SupervisorError("Supervisor dispatch and block must be lists.")

    dispatch = []
    dispatched = set()
    for item in raw["dispatch"]:
        if not isinstance(item, dict) or set(item) != {"ticket", "instruction"}:
            raise SupervisorError("Each dispatch must contain ticket and instruction.")
        number = item["ticket"]
        if not isinstance(number, int) or isinstance(number, bool) or number not in candidates:
            raise SupervisorError(f"Supervisor tried to dispatch unavailable ticket #{number}.")
        if number in dispatched:
            raise SupervisorError(f"Supervisor dispatched ticket #{number} more than once.")
        dispatched.add(number)
        dispatch.append({"ticket": number, "instruction": _message(item["instruction"], "instruction")})
    if len(dispatch) > max_parallel:
        raise SupervisorError(
            f"Supervisor dispatched {len(dispatch)} tickets; the configured limit is {max_parallel}."
        )

    blocked = []
    blocked_numbers = set()
    for item in raw["block"]:
        if not isinstance(item, dict) or set(item) != {"ticket", "reason"}:
            raise SupervisorError("Each block command must contain ticket and reason.")
        number = item["ticket"]
        if not isinstance(number, int) or isinstance(number, bool) or number not in candidates:
            raise SupervisorError(f"Supervisor tried to block unavailable ticket #{number}.")
        if number in dispatched or number in blocked_numbers:
            raise SupervisorError(f"Supervisor issued conflicting commands for ticket #{number}.")
        blocked_numbers.add(number)
        blocked.append({"ticket": number, "reason": _message(item["reason"], "block reason")})

    if candidates and not dispatch and blocked_numbers != candidates:
        raise SupervisorError(
            "Supervisor must dispatch work or explicitly block every ready ticket; silent stalls are rejected."
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "summary": _message(raw["summary"], "summary"),
        "dispatch": dispatch,
        "block": blocked,
        "deferred": sorted(candidates - dispatched - blocked_numbers),
    }


def extract_merge_decision(output: str) -> dict:
    """Return the last structured Supervisor merge decision."""
    required = {"schema_version", "summary", "action", "ticket", "pull_request", "candidate_head"}
    value = extract_last_json_object(output, required)
    if value is None:
        raise SupervisorError("Supervisor did not return a structured merge decision.")
    return value


def validate_merge_decision(raw: dict, ticket: dict) -> dict:
    """Validate the only post-review commands the orchestrator accepts."""
    expected = {"schema_version", "summary", "action", "ticket", "pull_request", "candidate_head"}
    if set(raw) != expected:
        raise SupervisorError(
            "Supervisor merge fields must be exactly " + ", ".join(sorted(expected)) + "."
        )
    if raw["schema_version"] != SCHEMA_VERSION:
        raise SupervisorError(f"Supervisor schema_version must be {SCHEMA_VERSION}.")
    action = raw["action"]
    if action not in {"MERGE", "BLOCK"}:
        raise SupervisorError("Supervisor merge action must be MERGE or BLOCK.")
    number = ticket.get("number")
    review = ticket.get("code_review", {}).get("result", {})
    publication = ticket.get("code_review", {}).get("publication", {})
    expected_head = ticket.get("code_review", {}).get("head", "")
    expected_pr = ticket.get("pr_url") or ticket.get("review_ref", "")
    required_gates = [
        gate for gate in ticket.get("gate_results", []) if gate.get("required", True)
    ]
    gates_pass = bool(required_gates) and all(
        gate.get("exit_code") == 0 for gate in required_gates
    )
    if review.get("decision") != "APPROVE":
        raise SupervisorError("Supervisor cannot merge without Code Review role approval.")
    if not publication.get("published"):
        raise SupervisorError("Supervisor cannot merge before the review decision is published.")
    if not gates_pass:
        raise SupervisorError("Supervisor cannot merge without passing required gates.")
    if raw["ticket"] != number:
        raise SupervisorError(f"Supervisor merge command targets the wrong Ticket #{raw['ticket']}.")
    if raw["pull_request"] != expected_pr:
        raise SupervisorError("Supervisor merge command targets an unexpected pull request.")
    if raw["candidate_head"] != expected_head:
        raise SupervisorError("Supervisor merge command targets a stale candidate commit.")
    return {
        "schema_version": SCHEMA_VERSION,
        "summary": _message(raw["summary"], "merge summary"),
        "action": action,
        "ticket": number,
        "pull_request": expected_pr,
        "candidate_head": expected_head,
    }


class AgentSupervisor:
    """Deep module that turns agent reports into safe scheduler directives.

    The public interface is ``coordinate(tickets, max_parallel)``. Adapter
    invocation, isolated worktrees, receipt collection, prompt construction,
    schema validation, and the durable decision journal stay inside.
    """

    def __init__(
        self,
        repo: Path,
        *,
        agent: str,
        template: str,
        python: str,
        codex_bin: str,
        scenario: str,
        mock: bool,
        agent_timeout: int,
        environment: dict[str, str] | None = None,
        invoke: Callable[[Path], tuple[int, str]] | None = None,
    ):
        self.repo = repo.resolve()
        self.agent = agent
        self.template = template
        self.python = python
        self.codex_bin = codex_bin
        self.scenario = scenario
        self.mock = mock
        self.agent_timeout = agent_timeout
        self.environment = dict(environment if environment is not None else role_environment())
        self.invoke = invoke
        self.directory = self.repo / ".factory" / "supervisor"
        self.state_path = self.directory / "state.json"
        self.charter = FactoryCharter.load(self.repo, require_approved=True)
        self._authority_lock = threading.Lock()

    def coordinate(self, tickets: list[dict], max_parallel: int) -> dict:
        with self._authority_lock:
            return self._coordinate(tickets, max_parallel)

    def _coordinate(self, tickets: list[dict], max_parallel: int) -> dict:
        candidates = {int(ticket["number"]) for ticket in tickets if ticket.get("status") == "Ready"}
        if not candidates:
            raise SupervisorError("Supervisor requires at least one dependency-ready ticket.")
        state = _read_json(self.state_path, {"events": []})
        sequence = int(state.get("review_count", 0)) + 1
        supervisor_input = self._input(tickets, max_parallel)
        serialized = json.dumps(supervisor_input, sort_keys=True, separators=(",", ":"))
        input_hash = hashlib.sha256(serialized.encode()).hexdigest()
        prompt = self._prompt(sequence, supervisor_input)
        log = self.repo / ".factory" / "logs" / f"supervisor-{sequence}.log"
        running = {
            **state,
            "enabled": True,
            "agent": self.agent,
            "status": "running",
            "review_count": sequence,
            "updated_at": _now(),
            "current_prompt": str(prompt.relative_to(self.repo)),
            "current_log": str(log.relative_to(self.repo)),
            "error": "",
        }
        _write_json(self.state_path, running)
        attempts = []
        try:
            code, output = self.invoke(prompt) if self.invoke else self._invoke(prompt, sequence)
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text(output)
            if code:
                raise adapter_error(code, output, log, self.repo)
            attempts.append({
                "prompt": str(prompt.relative_to(self.repo)),
                "log": str(log.relative_to(self.repo)),
                "validation_error": "",
            })
            try:
                decision = validate_decision(extract_decision(output), candidates, max_parallel)
            except SupervisorError as first_error:
                attempts[-1]["validation_error"] = str(first_error)
                prompt = self._repair_prompt(sequence, prompt, output, first_error)
                log = self.repo / ".factory" / "logs" / f"supervisor-{sequence}-repair-1.log"
                running.update(
                    updated_at=_now(),
                    current_prompt=str(prompt.relative_to(self.repo)),
                    current_log=str(log.relative_to(self.repo)),
                    error=str(first_error),
                )
                _write_json(self.state_path, running)
                code, output = self.invoke(prompt) if self.invoke else self._invoke(prompt, sequence)
                log.parent.mkdir(parents=True, exist_ok=True)
                log.write_text(output)
                if code:
                    raise adapter_error(code, output, log, self.repo)
                attempts.append({
                    "prompt": str(prompt.relative_to(self.repo)),
                    "log": str(log.relative_to(self.repo)),
                    "validation_error": "",
                })
                try:
                    decision = validate_decision(extract_decision(output), candidates, max_parallel)
                except SupervisorError as repair_error:
                    attempts[-1]["validation_error"] = str(repair_error)
                    raise
        except Exception as exc:
            error = exc if isinstance(exc, SupervisorError) else SupervisorError(str(exc))
            running.update(
                status="failed",
                updated_at=_now(),
                error=str(error),
                attempts=attempts,
            )
            _write_json(self.state_path, running)
            raise error

        decision.update({
            "id": f"supervisor-{sequence}",
            "kind": "dispatch",
            "at": _now(),
            "agent": self.agent,
            "input_hash": input_hash,
            "prompt": str(prompt.relative_to(self.repo)),
            "log": str(log.relative_to(self.repo)),
            "attempts": attempts,
            "worker_reports": supervisor_input["worker_reports"],
        })
        events = [*state.get("events", []), decision][-MAX_EVENTS:]
        _write_json(self.state_path, {
            "enabled": True,
            "agent": self.agent,
            "status": "ready",
            "review_count": sequence,
            "updated_at": decision["at"],
            "current_prompt": decision["prompt"],
            "current_log": decision["log"],
            "error": "",
            "latest": decision,
            "events": events,
        })
        return decision

    def authorize_merge(self, ticket: dict) -> dict:
        """Return one validated MERGE or BLOCK command for an approved PR."""
        with self._authority_lock:
            return self._authorize_merge(ticket)

    def _authorize_merge(self, ticket: dict) -> dict:
        """Run one serialized merge checkpoint against durable Supervisor state."""
        # Validate invariants before an agent is allowed to consider the merge.
        baseline = {
            "schema_version": SCHEMA_VERSION,
            "summary": "Validate merge candidate.",
            "action": "BLOCK",
            "ticket": ticket.get("number"),
            "pull_request": ticket.get("pr_url") or ticket.get("review_ref", ""),
            "candidate_head": ticket.get("code_review", {}).get("head", ""),
        }
        validate_merge_decision(baseline, ticket)
        state = _read_json(self.state_path, {"events": []})
        sequence = int(state.get("review_count", 0)) + 1
        merge_input = self._merge_input(ticket)
        serialized = json.dumps(merge_input, sort_keys=True, separators=(",", ":"))
        input_hash = hashlib.sha256(serialized.encode()).hexdigest()
        prompt = self._merge_prompt(sequence, merge_input)
        log = self.repo / ".factory" / "logs" / f"supervisor-merge-{sequence}.log"
        running = {
            **state,
            "enabled": True,
            "agent": self.agent,
            "status": "running",
            "review_count": sequence,
            "updated_at": _now(),
            "current_prompt": str(prompt.relative_to(self.repo)),
            "current_log": str(log.relative_to(self.repo)),
            "error": "",
        }
        _write_json(self.state_path, running)
        try:
            code, output = self.invoke(prompt) if self.invoke else self._invoke(prompt, sequence)
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text(output)
            if code:
                raise adapter_error(code, output, log, self.repo)
            decision = validate_merge_decision(extract_merge_decision(output), ticket)
        except Exception as exc:
            error = exc if isinstance(exc, SupervisorError) else SupervisorError(str(exc))
            running.update(status="failed", updated_at=_now(), error=str(error))
            _write_json(self.state_path, running)
            raise error
        decision.update({
            "id": f"supervisor-merge-{sequence}",
            "kind": "merge",
            "at": _now(),
            "agent": self.agent,
            "input_hash": input_hash,
            "prompt": str(prompt.relative_to(self.repo)),
            "log": str(log.relative_to(self.repo)),
            "worker_reports": self._reports(ticket),
            "dispatch": [],
            "block": (
                [{"ticket": ticket["number"], "reason": decision["summary"]}]
                if decision["action"] == "BLOCK" else []
            ),
            "deferred": [],
        })
        events = [*state.get("events", []), decision][-MAX_EVENTS:]
        _write_json(self.state_path, {
            "enabled": True,
            "agent": self.agent,
            "status": "ready",
            "review_count": sequence,
            "updated_at": decision["at"],
            "current_prompt": decision["prompt"],
            "current_log": decision["log"],
            "error": "",
            "latest": decision,
            "events": events,
        })
        return decision

    def _input(self, tickets: list[dict], max_parallel: int) -> dict:
        ready = []
        ticket_state = []
        reports = []
        for ticket in sorted(tickets, key=lambda value: int(value["number"])):
            compact = {
                "number": int(ticket["number"]),
                "title": ticket.get("title", ""),
                "status": ticket.get("status", "Backlog"),
                "phase": ticket.get("phase", ""),
                "dependencies": ticket.get("dependencies", []),
                "attempt": ticket.get("attempt", 0),
                "failure": ticket.get("failure", "")[-1200:],
                "retry_reason": ticket.get("last_retry_reason", "")[-1200:],
            }
            ticket_state.append(compact)
            if ticket.get("status") == "Ready":
                ready.append({**compact, "specification": ticket.get("body", "")[:5000]})
            reports.extend(self._reports(ticket))
        return {
            "schema_version": SCHEMA_VERSION,
            "profile": "ticket-delivery",
            "max_parallel": max_parallel,
            "ready_tickets": ready,
            "ticket_state": ticket_state,
            "worker_reports": reports[-32:],
        }

    def _merge_input(self, ticket: dict) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "profile": "pull-request-merge",
            "ticket": int(ticket["number"]),
            "title": ticket.get("title", ""),
            "specification": ticket.get("body", ""),
            "dependencies": ticket.get("dependencies", []),
            "diff_budget": ticket.get("diff_budget"),
            "operator_retry_reason": ticket.get("last_retry_reason", ""),
            "review_evidence": ticket.get("review_evidence", []),
            "pull_request": ticket.get("pr_url") or ticket.get("review_ref", ""),
            "candidate_head": ticket.get("code_review", {}).get("head", ""),
            "code_review": ticket.get("code_review", {}).get("result", {}),
            "review_publication": ticket.get("code_review", {}).get("publication", {}),
            "required_gates": [
                {
                    "name": gate.get("name", ""),
                    "required": gate.get("required", True),
                    "exit_code": gate.get("exit_code"),
                }
                for gate in ticket.get("gate_results", [])
            ],
            "worker_reports": self._reports(ticket),
        }

    def _reports(self, ticket: dict) -> list[dict]:
        reports = []
        receipt_root = (self.repo / ".factory" / "receipts").resolve()
        for reference in ticket.get("receipts", [])[-4:]:
            path = (self.repo / reference).resolve()
            if not path.is_relative_to(receipt_root):
                continue
            receipt = _read_json(path, {})
            if not isinstance(receipt, dict) or receipt.get("ticket") != ticket.get("number"):
                continue
            reports.append({
                "ticket": receipt.get("ticket"),
                "role": receipt.get("role", ""),
                "phase": receipt.get("phase", ""),
                "claimed_result": receipt.get("claimed_result", ""),
                "verification": receipt.get("verification", []),
                "unresolved_risks": receipt.get("unresolved_risks", []),
                "output_revisions": receipt.get("output_revisions", {}),
                "receipt": reference,
            })
        return reports

    def _prompt(self, sequence: int, supervisor_input: dict) -> Path:
        path = self.repo / ".factory" / "prompts" / f"supervisor-{sequence}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        contract = role_input(self.repo, "supervisor")["text"]
        charter = self.charter.context()
        payload = json.dumps(supervisor_input, indent=2)
        path.write_text(
            "# Supervisor role coordination checkpoint\n\n"
            "Coordinate only the dependency-ready Tickets in the supplied state. Ticket worker roles report "
            "through Handoff Receipts. Select a safe dispatch wave, reduce concurrency when coordination "
            "requires it, and give each dispatched Ticket one concise instruction of at most 1200 "
            "characters. The Ticket already carries its approved scope, so do not repeat its specification; "
            "use the instruction only for coordination guidance. Block a Ticket only "
            "when its reports or current state show a concrete risk that requires intervention.\n\n"
            "This checkpoint runs between worker waves: max_parallel is the available capacity for this next wave. "
            "Historical dispatch receipts do not prove a worker is still running. Current ticket_state and "
            "ready_tickets take precedence after recovery; do not reserve slots for old dispatches or "
            "treat a Done Ticket's historical human_review phase as a pending merge.\n\n"
            "You cannot change scope, dependencies, lifecycle state, tests, gates, human approvals, or "
            "repository policy. A Charter `requires_human_approval` path requires a human merge; it does "
            "not require approval before a worker edits that path. The orchestrator validates and applies "
            "your proposed commands.\n\n"
            "## Approved Factory Charter\n\n```json\n"
            f"{charter}\n```\n\n"
            f"{contract}\n"
            "## Supervisor input\n\n<supervisor-input>\n"
            f"{payload}\n"
            "</supervisor-input>\n\n"
            "## Required response\n\nReturn exactly one JSON object and no Markdown:\n\n"
            '{"schema_version":1,"summary":"...","dispatch":[{"ticket":1,'
            '"instruction":"..."}],"block":[{"ticket":2,"reason":"..."}]}\n'
        )
        return path

    def _repair_prompt(
        self,
        sequence: int,
        original_prompt: Path,
        previous_output: str,
        error: SupervisorError,
    ) -> Path:
        path = self.repo / ".factory" / "prompts" / f"supervisor-{sequence}-repair-1.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            original_prompt.read_text()
            + "\n\n## Validation repair\n\n"
            + "The previous response was rejected by the deterministic supervisor contract. "
            + "Return a corrected replacement for the same decision. Preserve the intended dispatch or "
            + "block outcome, but fix the validation error. Do not repeat the Ticket specification in an "
            + "instruction; keep every summary, instruction, and block reason at or below 1200 characters.\n\n"
            + f"Validation error: {error}\n\n"
            + "<rejected-response>\n"
            + previous_output
            + "\n</rejected-response>\n"
        )
        return path

    def _merge_prompt(self, sequence: int, merge_input: dict) -> Path:
        path = self.repo / ".factory" / "prompts" / f"supervisor-merge-{sequence}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        contract = role_input(self.repo, "supervisor_merge")["text"]
        charter = self.charter.context()
        payload = json.dumps(merge_input, indent=2)
        path.write_text(
            "# Supervisor role merge checkpoint\n\n"
            "Decide whether the pull request approved by the Code Review role is ready for the merge handoff. "
            "Check the candidate revision, required gate evidence, review approval, and unresolved risks. "
            "Evaluate acceptance against the supplied Ticket specification and dependencies. "
            "Do not invent dependencies or require future integration work explicitly owned by another "
            "Ticket before this scoped handoff. Preserve those release follow-ups in the summary; "
            "do not claim them verified. Missing acceptance within this Ticket's own scope still blocks. "
            "Use the supplied revision-bound diff_budget measurement. Operator retry feedback is a "
            "claim to assess against the evidence, not review approval or permission to merge. "
            "Attached review reports identify their author, content hash, and the candidate they "
            "were submitted for. Assess their contents and any recorded errors. Neither operator "
            "nor implementation-authored reports supply independent verification or human approval. "
            "The structured Code Review decision is the Factory approval evidence. A published labelled "
            "Factory comment with `official: false` is the expected GitHub self-review fallback and is not "
            "a blocker by itself. Require a formal GitHub approval only when the supplied evidence says "
            "branch protection requires one; do not infer that requirement from the publication mode. "
            "Return MERGE only when all evidence refers to the same candidate and no blocking risk remains. "
            "Return BLOCK otherwise. MERGE is a readiness recommendation, not permission to execute "
            "a merge. When the Charter or path policy requires human merge authority, MERGE sends the "
            "exact revision to human review; it does not supply that approval. Do not BLOCK solely "
            "because human approval is still pending. Block missing or inconsistent evidence and "
            "substantive unresolved risks. You do not run GitHub commands; the orchestrator validates "
            "the recommendation and retains the configured human approval gate.\n\n"
            "## Approved Factory Charter\n\n```json\n"
            f"{charter}\n```\n\n"
            f"{contract}\n"
            "## Merge input\n\n<merge-supervisor-input>\n"
            f"{payload}\n"
            "</merge-supervisor-input>\n\n"
            "## Required response\n\nReturn exactly one JSON object and no Markdown:\n\n"
            '{"schema_version":1,"summary":"...","action":"MERGE|BLOCK",'
            '"ticket":1,"pull_request":"https://github.com/.../pull/1",'
            '"candidate_head":"full-git-sha"}\n'
        )
        return path

    def _invoke(self, prompt: Path, sequence: int) -> tuple[int, str]:
        if self.agent == "claude" and (issue := claude_configuration_issue()):
            return 2, issue
        worktree = self.repo.parent / f"{self.repo.name}-supervisor-wt"
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree)],
            cwd=self.repo, text=True, capture_output=True,
        )
        subprocess.run(["git", "worktree", "prune"], cwd=self.repo, check=False)
        added = subprocess.run(
            ["git", "worktree", "add", "--detach", str(worktree), "HEAD"],
            cwd=self.repo, text=True, capture_output=True,
        )
        if added.returncode:
            raise SupervisorError((added.stdout + added.stderr).strip())
        try:
            source_prompt = prompt
            if self.agent in {"claude", "codex", "cursor"}:
                original = prompt.read_text()
                bounded = prepare_context(original, worktree)
                if bounded != original:
                    prompt = prompt.with_name(prompt.stem + "-file-backed.md")
                    prompt.write_text(bounded)
            template = isolated_template(self.agent, self.template)
            command = template.format(
                prompt=shlex.quote(str(prompt)),
                ticket=0,
                python=shlex.quote(self.python),
                codex=shlex.quote(self.codex_bin or "codex"),
                scenario=shlex.quote(self.scenario),
                attempt=sequence,
                repo=shlex.quote(str(worktree)),
                worktree=shlex.quote(str(worktree)),
                factory_dir=shlex.quote(str(Path(__file__).parent)),
            )
            try:
                result = subprocess.run(
                    command,
                    cwd=worktree,
                    text=True,
                    shell=True,
                    executable="/bin/sh",
                    capture_output=True,
                    timeout=self.agent_timeout if self.mock else None,
                    env=self.environment.copy(),
                )
                output = result.stdout + result.stderr
                if result.returncode and is_context_error(output) and self.agent in {"claude", "codex", "cursor"}:
                    source_prompt.with_suffix(".context-error.log").write_text(output)
                    if self.charter.max_retries > 0:
                        print(CONTEXT_ACTIVITY, flush=True)
                        recovery_prompt = source_prompt.with_name(source_prompt.stem + "-context-recovery.md")
                        recovery_prompt.write_text(prepare_context(source_prompt.read_text(), worktree, force=True))
                        command = command.replace(shlex.quote(str(prompt)), shlex.quote(str(recovery_prompt)), 1)
                        result = subprocess.run(
                            command, cwd=worktree, text=True, shell=True, executable="/bin/sh",
                            capture_output=True, timeout=self.agent_timeout if self.mock else None,
                            env=self.environment.copy(),
                        )
                        output = result.stdout + result.stderr
                    if result.returncode and is_context_error(output):
                        output += "\n" + CONTEXT_RECOVERY
                return result.returncode, output
            except subprocess.TimeoutExpired as exc:
                stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
                stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
                output = stdout + stderr
                return 124, output + f"\nSupervisor timed out after {self.agent_timeout}s.\n"
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(worktree)],
                cwd=self.repo, text=True, capture_output=True,
            )
            subprocess.run(["git", "worktree", "prune"], cwd=self.repo, check=False)
