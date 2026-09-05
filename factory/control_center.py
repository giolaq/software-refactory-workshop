#!/usr/bin/env python3
"""Local web control plane for the Software (re)-Factory.

The server exposes a small allowlisted API over the existing ``factory`` CLI.
It binds to loopback by default, never accepts arbitrary shell commands, and
keeps agent credentials in their normal CLI stores rather than the browser.
"""

from __future__ import annotations

import json
import mimetypes
import os
import re
import shlex
import signal
import socket
import subprocess
import sys
import threading
import time
import tomllib
import uuid
import webbrowser
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from urllib.parse import parse_qs, urlparse

from control_center_access import ControlCenterAccessPolicy

from session_config import (
    AGENT_NAME,
    FACTORY_PROFILES,
    PLANNING_AGENTS,
    PRESETS,
    load_session_config,
)
from github_repository import (
    managed_checkout_path,
    parse_github_repository,
    repository_from_remote,
)
from factory_charter import CHARTER_PATH, FactoryCharter, FactoryCharterError
from human_attention import human_attention_snapshot
from planning_presentation import (
    REPLAN_REQUIRED_STATUSES,
    planning_blocking_stage,
    planning_can_continue,
    planning_failed_stage,
    planning_presentation,
    planning_recovery,
)
from project_contract import CONTRACT_PATH, ProjectContract, ProjectContractError
from environment_provider import EnvironmentProviderError, LocalEnvironmentProvider
from merge_steward import MergeSteward
from workspace_contract import WorkspaceContract, WorkspaceContractError
from orchestrator import (
    current_runtime_is_latest,
    factory_execution_mode,
    latest_recovery_checkpoint,
    load_config,
    ticket_diff_budget,
    ticket_recovery,
)
from triage import declared_paths


PLAN_ID = re.compile(r"[a-f0-9]{8,64}")
SCENARIOS = {"recipe-rebrand", "tv"}
DEFAULT_AGENTS = {"bedrock", "claude", "codex", "cursor", "mock", "mock-qa", "mock-supervisor", "mock-review"}
REVISION_STAGE_ALIASES = {
    "product_review": "product",
    "system_architecture": "architecture",
    "program_design": "program",
    "vertical_slices": "slices",
}
MAX_BODY = 256_000
MAX_ARTIFACT = 512_000
MAX_PLANNING_FEEDBACK = 12_000
ACTION_REGISTRY = frozenset({
    "doctor", "init-project", "approve-contract", "approve-charter", "publish-setup",
    "configure", "plan", "restart-plan", "revise-product", "revise-stage",
    "approve-product", "approve-stage", "continue-plan", "publish-plan",
    "approve-tests", "request-test-changes", "merge",
    "run", "run-once", "dry-run", "retry", "save-ticket-and-retry",
    "release-claim", "evidence", "start-app",
    "monitor", "publish-monitor", "recover-latest", "reset-run", "reset-all",
    "listen", "environment-provision", "environment-prepare",
    "environment-health", "environment-reset",
    "improve-report", "workspace-check",
    "approve-intake",
    "steward-sync",
})
ACTION_BUILDERS = {
    **dict.fromkeys({
        "doctor", "init-project", "approve-contract", "approve-charter", "publish-setup",
        "start-app", "environment-provision", "environment-prepare",
        "environment-health", "environment-reset", "improve-report",
        "workspace-check", "approve-intake", "steward-sync",
    }, "_build_setup_command"),
    "configure": "_build_configure_command",
    **dict.fromkeys({
        "plan", "restart-plan", "revise-product", "revise-stage",
        "approve-product", "approve-stage", "continue-plan", "publish-plan",
    }, "_build_planning_command"),
    **dict.fromkeys({
        "approve-tests", "request-test-changes", "merge", "run", "listen",
        "run-once", "dry-run",
    }, "_build_delivery_command"),
    "save-ticket-and-retry": "_build_ticket_correction_command",
    "retry": "_build_retry_command",
    **dict.fromkeys({
        "release-claim", "evidence", "monitor", "publish-monitor",
        "recover-latest", "reset-run", "reset-all",
    }, "_build_operations_command"),
}


def _first_fail(output: str) -> str:
    for line in output.splitlines():
        stripped = line.strip()
        if re.match(r"^\[FAIL\s*\]", stripped, re.IGNORECASE):
            return stripped
    return ""


def _default_branch_from_failure(diagnostic: str) -> str:
    match = re.search(r"(?:GitHub|remote)\s+`([^`]+)`", diagnostic)
    return match.group(1) if match else "main"


def _readiness_recovery(diagnostic: str) -> tuple[str, str]:
    """Map one Doctor failure to the smallest safe operator action."""
    lowered = diagnostic.lower()
    if "codex adapter" in lowered:
        return (
            "Inner harness",
            "Install Codex CLI if it is missing, run `codex login`, then retry automatic setup.",
        )
    if "claude adapter" in lowered:
        return (
            "Inner harness",
            "Install Claude Code if it is missing, run `claude auth login`, then retry automatic setup.",
        )
    if "cursor adapter" in lowered:
        return (
            "Inner harness",
            "Install the current Cursor CLI if it is missing, run `agent login` and `agent status`, then retry automatic setup.",
        )
    if "default branch" in lowered or "branch synchronization" in lowered:
        branch = _default_branch_from_failure(diagnostic)
        return (
            "Development environment",
            "Save work you need to keep. In the product checkout run `git fetch origin`, "
            f"`git switch {branch}`, and `git pull --ff-only origin {branch}`, then retry automatic setup.",
        )
    if "clean checkout" in lowered:
        return (
            "Development environment",
            "Commit or stash work you need to keep in the product checkout. Do not discard it, then retry automatic setup.",
        )
    if "github repository target" in lowered or "origin remote" in lowered:
        return (
            "Control plane",
            "In Setup → Connection, paste the full product repository URL and select Save and connect, then retry automatic setup.",
        )
    if "github projects scope" in lowered:
        return (
            "Control plane",
            "Run `gh auth refresh -s project`, finish browser authorization, then retry automatic setup.",
        )
    if "project contract" in lowered or "factory charter" in lowered:
        return (
            "Outer harness",
            "Return to Setup → Connection, create the repository contract, review the repository model and operating policy, then approve it.",
        )
    if "tool: node" in lowered or "node.js" in lowered:
        return (
            "Development environment",
            "Install the Node.js version reported by Doctor, confirm it with `node --version`, then retry automatic setup.",
        )
    if "no module named pytest" in lowered or "gate: api-tests" in lowered:
        return (
            "Development environment",
            "Run the setup command recorded in the Project Contract to install test dependencies, then retry automatic setup.",
        )
    return (
        "Development environment",
        "Correct the reported repository, tool, dependency, service, or gate failure, then retry automatic setup.",
    )
COMPANION_ACTIONS = frozenset({
    "approve-tests", "request-test-changes", "merge", "retry",
    "save-ticket-and-retry", "approve-intake", "steward-sync",
})


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return default


def tail_text(path: Path, limit: int = 80_000) -> str:
    try:
        data = path.read_bytes()
    except OSError:
        return ""
    if len(data) > limit:
        return "… earlier output omitted …\n" + data[-limit:].decode("utf-8", errors="replace")
    return data.decode("utf-8", errors="replace")


def run_text(command: list[str], cwd: Path) -> str:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else ""


class InputError(ValueError):
    """A safe, user-visible API validation failure."""


class ControlCenter:
    def __init__(self, repo: Path):
        try:
            self.access_policy = ControlCenterAccessPolicy.from_environment()
        except ValueError as exc:
            raise InputError(str(exc)) from exc
        self.control_repo = repo.resolve()
        repository_factory = self.control_repo / "factory" / "factory"
        self.factory = (
            repository_factory if repository_factory.is_file()
            else Path(__file__).with_name("factory")
        )
        self.assets = Path(__file__).with_name("control_center")
        self.control_runtime = self.control_repo / ".factory" / "control-center"
        self.control_runtime.mkdir(parents=True, exist_ok=True)
        (self.control_repo / ".factory" / "logs").mkdir(parents=True, exist_ok=True)
        self.operation_path = self.control_runtime / "operation.json"
        self.active_repository_path = self.control_runtime / "active-repository.json"
        self.repository_root = self.control_repo / ".factory" / "repositories"
        self.lock = threading.RLock()
        self.companion_lock = threading.Lock()
        self._stream_lock = threading.Lock()
        self._stream_value = None
        self._stream_at = 0.0
        self.process: subprocess.Popen | None = None
        self.worker: threading.Thread | None = None
        self._pending_activation: Path | None = None
        self._application_port: int | None = None
        self._bind_repo(self._saved_active_repo() or self.control_repo)
        self.operation: dict = read_json(self.operation_path, {})
        if self.operation.get("status") in {"running", "stopping"}:
            self.operation.update(
                status="interrupted",
                finished_at=utc_now(),
                error="The control center restarted while this operation was running.",
            )
            self._save_operation()

    def _saved_active_repo(self) -> Path | None:
        raw = read_json(self.active_repository_path, {}).get("path", "")
        if not isinstance(raw, str) or not raw:
            return None
        candidate = Path(raw).resolve()
        try:
            candidate.relative_to(self.repository_root.resolve())
        except ValueError:
            return None
        return candidate if (candidate / ".git").exists() else None

    def _bind_repo(self, repo: Path):
        resolved = repo.resolve()
        if getattr(self, "repo", None) != resolved:
            self._application_port = None
        self.repo = resolved
        self.runtime = self.repo / ".factory" / "control-center"
        self.runtime.mkdir(parents=True, exist_ok=True)
        (self.repo / ".factory" / "logs").mkdir(parents=True, exist_ok=True)
        self.prd_path = self.runtime / "workshop-prd.md"
        self.canvas_path = self.runtime / "factory-canvas.md"

    def _activate_repo(self, repo: Path):
        candidate = repo.resolve()
        try:
            candidate.relative_to(self.repository_root.resolve())
        except ValueError as exc:
            raise InputError("Managed repository is outside the Control Center workspace.") from exc
        if not (candidate / ".git").exists():
            raise InputError(f"Managed repository checkout is missing: {candidate}")
        temp = self.active_repository_path.with_suffix(".tmp")
        temp.write_text(json.dumps({"path": str(candidate)}, indent=2) + "\n")
        os.replace(temp, self.active_repository_path)
        self._bind_repo(candidate)

    def _save_operation(self):
        temp = self.operation_path.with_suffix(".tmp")
        temp.write_text(json.dumps(self.operation, indent=2) + "\n")
        os.replace(temp, self.operation_path)

    def adapters(self) -> list[str]:
        names = set(DEFAULT_AGENTS)
        for path in (
            Path(__file__).with_name("factory.toml"),
            self.repo / "factory" / "factory.toml",
        ):
            try:
                names.update(tomllib.loads(path.read_text()).get("agents", {}))
            except (OSError, tomllib.TOMLDecodeError):
                pass
        return sorted(names)

    def adapter_details(self) -> dict:
        """Expose honest Adapter Protocol declarations without running a model."""
        try:
            config = load_config(self.repo)
        except (OSError, ValueError, ProjectContractError):
            return {}
        return {
            name: capability.as_dict()
            for name, capability in sorted(config["agent_capabilities"].items())
        }

    def environment_snapshot(self) -> dict:
        """Return provider-owned environment state without repairing drift."""
        try:
            return LocalEnvironmentProvider(self.repo).snapshot()
        except (OSError, ValueError, ProjectContractError, EnvironmentProviderError) as exc:
            return {
                "schema_version": 1,
                "provider": "local",
                "status": "not-configured",
                "actions": [],
                "error": str(exc),
            }

    def workspace_snapshot(self) -> dict:
        try:
            return WorkspaceContract.load(self.repo).check()
        except (OSError, ValueError, WorkspaceContractError) as exc:
            return {
                "schema_version": 1,
                "status": "blocked",
                "configured": False,
                "checks": [],
                "recovery_action": str(exc),
                "may_dispatch": False,
            }

    def improvements_snapshot(self) -> dict:
        report = read_json(self.repo / ".factory/improvements/report.json", {})
        if not report:
            return {
                "schema_version": 1,
                "status": "not-generated",
                "suggestions": [],
                "observation_count": 0,
            }
        return {**report, "status": "review-required" if report.get("suggestions") else "current"}

    def triggers_snapshot(self) -> dict:
        records = []
        for path in sorted((self.repo / ".factory/triggers").glob("*.json")):
            value = read_json(path, {})
            if value:
                records.append({
                    key: value.get(key)
                    for key in ("trigger_id", "source", "event_id", "status", "received_at")
                })
        return {"proposal_count": len(records), "latest": records[-10:]}

    @staticmethod
    def merge_steward_snapshot(ticket: dict) -> dict:
        if ticket.get("status") != "In Review":
            return {"state": "not-applicable", "merge_authority": "human", "may_merge": False}
        head = str(ticket.get("pr_head") or ticket.get("approved_head") or "")
        review = ticket.get("code_review") or {}
        result = review.get("result") if isinstance(review.get("result"), dict) else {}
        return MergeSteward().assess({
            "candidate_head": head,
            "reviewed_head": str(ticket.get("approved_head") or review.get("candidate_sha") or ""),
            "candidate_base": ticket.get("base_sha", ""),
            "default_branch_head": ticket.get("base_sha", ""),
            "required_gates": [
                {
                    "name": gate.get("name", "gate"),
                    "status": "passed" if gate.get("classification") == "PASS" else "failed",
                    "revision": head,
                }
                for gate in ticket.get("gate_results", []) if gate.get("required", True)
            ],
            "review_decision": (
                "approved" if str(result.get("decision") or "").upper() == "APPROVE" else "changes-requested"
            ),
            "unresolved_comments": result.get("comments", []),
            "protected_paths_changed": bool(ticket.get("protected_paths_changed")),
            "acceptance_evidence_sha256": ticket.get("qa_commit", ""),
            "reviewed_acceptance_evidence_sha256": ticket.get("qa_commit", ""),
            "branch_protection": ticket.get("branch_protection", "passed"),
        })

    def repo_info(self) -> dict:
        raw_remote = run_text(["git", "remote", "get-url", "origin"], self.repo)
        remote = re.sub(r"(https?://)[^/@]+@", r"\1", raw_remote)
        branch = run_text(["git", "branch", "--show-current"], self.repo)
        dirty = bool(run_text(["git", "status", "--porcelain"], self.repo))
        connected = repository_from_remote(remote)
        configured_url = self.session_config().get("github_repository", "")
        configured = parse_github_repository(configured_url) if configured_url else None
        matches = bool(
            configured and connected and configured.slug.lower() == connected.slug.lower()
        )
        return {
            "name": self.repo.name,
            "path": str(self.repo),
            "branch": branch or "detached",
            "head": run_text(["git", "rev-parse", "HEAD"], self.repo),
            "remote": remote,
            "github_url": configured.url if configured else (connected.url if connected else ""),
            "github_repository": configured.url if configured else "",
            "github_connected": matches,
            "dirty": dirty,
        }

    def session_config(self) -> dict:
        try:
            return load_session_config(self.repo)
        except ValueError:
            return {}

    def project_contract(self) -> dict:
        configured = (self.repo / CONTRACT_PATH).is_file()
        try:
            contract = ProjectContract.load(self.repo)
            error = ""
        except ProjectContractError as exc:
            contract = ProjectContract.detect(self.repo)
            error = str(exc)
        governed_paths = [str(CONTRACT_PATH), str(CHARTER_PATH)]
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", *governed_paths],
            cwd=self.repo,
            text=True,
            capture_output=True,
            check=False,
        )
        unchanged = subprocess.run(
            ["git", "status", "--porcelain", "--", *governed_paths],
            cwd=self.repo,
            text=True,
            capture_output=True,
            check=False,
        )
        committed = tracked.returncode == 0 and unchanged.returncode == 0 and not unchanged.stdout.strip()
        return {
            "configured": configured,
            "valid": not error,
            "committed": committed,
            "error": error,
            "path": str(CONTRACT_PATH),
            "text": (
                (self.repo / CONTRACT_PATH).read_text()[:64_000]
                if configured else ""
            ),
            "name": contract.name,
            "source_roots": list(contract.source_roots),
            "test_roots": list(contract.test_roots),
            "gates": [gate["name"] for gate in contract.gates],
            "required_tools": list(contract.required_tools),
            "setup_commands": list(contract.setup_commands),
        }

    def factory_charter(self) -> dict:
        configured = (self.repo / CHARTER_PATH).is_file()
        if not configured:
            return {
                "configured": False,
                "valid": False,
                "approved": False,
                "error": "Create the Project Contract and Factory Charter before planning.",
                "path": str(CHARTER_PATH),
                "policy_sha256": "",
            }
        try:
            charter = FactoryCharter.load(self.repo)
            approval_error = ""
            try:
                charter.assert_approved()
                approved = True
            except FactoryCharterError as exc:
                approved = False
                approval_error = str(exc)
            return {
                "configured": True,
                "valid": True,
                "approved": approved,
                "error": approval_error,
                "path": str(CHARTER_PATH),
                "text": (self.repo / CHARTER_PATH).read_text()[:64_000],
                "policy_sha256": charter.policy_sha256(),
                "consequence_tier": charter.consequence_tier,
                "merge_authority": charter.merge_authority,
                "gate_level": charter.gate_level,
                "planning_approvals": list(charter.planning_approvals),
                "max_diff_lines": charter.max_diff_lines,
                "max_awaiting_human_review": charter.max_awaiting_human_review,
                "max_blocked_for_human": charter.max_blocked_for_human,
                "oldest_review_hours": charter.oldest_review_hours,
            }
        except FactoryCharterError as exc:
            return {
                "configured": True,
                "valid": False,
                "approved": False,
                "error": str(exc),
                "path": str(CHARTER_PATH),
                "text": (self.repo / CHARTER_PATH).read_text()[:64_000],
                "policy_sha256": "",
            }

    def prd(self) -> dict:
        candidates = [
            self.repo / "PRD.md", self.repo / "prd.md",
            self.repo / "requirements.md", self.repo / "recipe-app-prd.md",
        ]
        source = self.prd_path if self.prd_path.is_file() else next(
            (path for path in candidates if path.is_file()), self.prd_path,
        )
        text = source.read_text() if source.is_file() else "# Product requirements document\n\n"
        return {
            "path": str(source.relative_to(self.repo)), "text": text,
            "saved": self.prd_path.is_file(),
        }

    def save_prd(self, text: str) -> dict:
        if not isinstance(text, str) or not text.strip():
            raise InputError("The PRD cannot be empty.")
        if len(text.encode()) > MAX_BODY:
            raise InputError("The PRD is too large for the workshop control center.")
        temp = self.prd_path.with_suffix(".tmp")
        temp.write_text(text.rstrip() + "\n")
        os.replace(temp, self.prd_path)
        return self.prd()

    def latest_plan_id(self) -> str:
        return str(read_json(self.repo / ".factory" / "plans" / "latest.json", {}).get("plan_id", ""))

    def evidence_files(self) -> list[dict]:
        candidates = []
        paths = list(self.runtime.glob("evidence-*/**/*"))
        if self.canvas_path.is_file():
            paths.append(self.canvas_path)
        for path in paths:
            if path.is_file():
                stat = path.stat()
                candidates.append({
                    "path": str(path.relative_to(self.repo)),
                    "name": path.name,
                    "size": stat.st_size,
                    "updated_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(timespec="seconds"),
                })
        return sorted(candidates, key=lambda item: item["updated_at"], reverse=True)

    def _documented_application_urls(
        self,
        contract: ProjectContract,
        default_port: int,
    ) -> tuple[list[dict], int, int]:
        urls = []
        seen = set()
        readme = next(
            (
                candidate for candidate in (
                    self.repo / "README.md",
                    self.repo / "README",
                    self.repo / "readme.md",
                )
                if candidate.is_file()
            ),
            None,
        )
        if readme:
            try:
                text = readme.read_text(errors="replace")[:256_000]
            except OSError:
                text = ""
            for raw in re.findall(
                r"https?://(?:127\.0\.0\.1|localhost):[1-9]\d{0,4}(?:/[^\s`<>\"']*)?",
                text,
                flags=re.IGNORECASE,
            ):
                candidate = raw.rstrip(".,;)]}")
                parsed = urlparse(candidate)
                if parsed.hostname not in {"127.0.0.1", "localhost"}:
                    continue
                try:
                    port = parsed.port
                except ValueError:
                    continue
                if not port or candidate in seen:
                    continue
                seen.add(candidate)
                urls.append({"label": "Application", "url": candidate})
        for port in contract.ports:
            candidate = f"http://127.0.0.1:{port}/"
            if candidate not in seen:
                seen.add(candidate)
                urls.append({"label": f"Port {port}", "url": candidate})
        if not urls:
            urls.append({
                "label": "Application",
                "url": f"http://127.0.0.1:{default_port}/",
            })
        preferred_port = urlparse(urls[0]["url"]).port or default_port
        selected_port = self._select_application_port(preferred_port)
        if selected_port != preferred_port:
            for item in urls:
                parsed = urlparse(item["url"])
                try:
                    item_port = parsed.port
                except ValueError:
                    continue
                if (
                    parsed.hostname in {"127.0.0.1", "localhost"}
                    and item_port == preferred_port
                ):
                    item["url"] = parsed._replace(
                        netloc=f"{parsed.hostname}:{selected_port}",
                    ).geturl()
        return urls, preferred_port, selected_port

    @staticmethod
    def _port_available(port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                probe.bind(("127.0.0.1", port))
        except OSError:
            return False
        return True

    def _select_application_port(self, preferred_port: int) -> int:
        if self._application_port is not None:
            return self._application_port
        for port in range(preferred_port, min(preferred_port + 100, 65_536)):
            if self._port_available(port):
                self._application_port = port
                return port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(("127.0.0.1", 0))
            self._application_port = int(probe.getsockname()[1])
        return self._application_port

    @staticmethod
    def _node_script_executable(script: str) -> str:
        try:
            tokens = shlex.split(script)
        except ValueError:
            return ""
        if tokens and tokens[0] == "env":
            tokens = tokens[1:]
        for token in tokens:
            if "=" in token and not token.startswith(("./", "../", "/")):
                name, _, _ = token.partition("=")
                if name.replace("_", "").isalnum():
                    continue
            return Path(token).name
        return ""

    def _node_dependency_setup(
        self,
        package: dict,
        script: str,
    ) -> list[str] | None:
        dependencies = {
            name
            for section in ("dependencies", "devDependencies")
            for name in (
                package.get(section, {})
                if isinstance(package.get(section), dict)
                else {}
            )
            if isinstance(name, str) and name
        }
        if not dependencies:
            return None

        modules = self.repo / "node_modules"
        missing = not modules.is_dir() or any(
            not modules.joinpath(*name.split("/")).exists()
            for name in dependencies
        )
        executable = self._node_script_executable(script)
        if (
            not missing
            and executable in dependencies
            and not (modules / ".bin" / executable).exists()
        ):
            missing = True
        if not missing:
            return None
        return [
            "npm",
            "ci" if (self.repo / "package-lock.json").is_file() else "install",
        ]

    def _application_entrypoint(self) -> dict | None:
        contract = ProjectContract.load(self.repo)
        package_path = self.repo / "package.json"
        if package_path.is_file():
            try:
                package = json.loads(package_path.read_text())
            except (OSError, json.JSONDecodeError):
                package = {}
            scripts = package.get("scripts") if isinstance(package, dict) else {}
            if isinstance(scripts, dict):
                selected = next(
                    (
                        script for script in ("start", "dev", "serve")
                        if isinstance(scripts.get(script), str)
                        and scripts[script].strip()
                    ),
                    "",
                )
                if selected:
                    base_command = (
                        ["npm", "start"]
                        if selected == "start" else
                        ["npm", "run", selected]
                    )
                    script = scripts[selected]
                    setup_command = self._node_dependency_setup(package, script)
                    urls, preferred_port, selected_port = (
                        self._documented_application_urls(
                            contract,
                            contract.ports[0] if contract.ports else 3000,
                        )
                    )
                    if self._node_script_executable(script) == "vite":
                        command = [
                            *base_command,
                            "--",
                            "--host", "127.0.0.1",
                            "--port", str(selected_port),
                            "--strictPort",
                        ]
                        display_command = shlex.join(command)
                    else:
                        command = (
                            ["env", f"PORT={selected_port}", *base_command]
                            if selected_port != preferred_port else
                            base_command
                        )
                        display_command = (
                            f"PORT={selected_port} {shlex.join(base_command)}"
                            if selected_port != preferred_port else
                            shlex.join(base_command)
                        )
                    commands = [setup_command, command] if setup_command else [command]
                    return {
                        "argv": command,
                        "command": (
                            f"cd {shlex.quote(str(self.repo))}\n"
                            + "\n".join(shlex.join(item) for item in commands[:-1])
                            + ("\n" if len(commands) > 1 else "")
                            + display_command
                        ),
                        "prepare_argv": commands[:-1],
                        "urls": urls,
                        "kind": "node",
                        "preferred_port": preferred_port,
                        "port": selected_port,
                    }
        python = self.control_repo / ".factory" / "venv" / "bin" / "python"
        if not python.is_file():
            python = Path(sys.executable)
        entrypoint = next(
            (
                candidate for candidate in (
                    self.repo / "demo-app" / "app.py",
                    self.repo / "app.py",
                )
                if candidate.is_file()
            ),
            None,
        )
        if entrypoint is None:
            return None
        relative = entrypoint.relative_to(self.repo)
        base_command = [str(python), str(relative)]
        urls, preferred_port, selected_port = self._documented_application_urls(
            contract, contract.ports[0] if contract.ports else 5000,
        )
        command = (
            ["env", f"PORT={selected_port}", *base_command]
            if selected_port != preferred_port else
            base_command
        )
        if relative == Path("demo-app/app.py"):
            base_url = urls[0]["url"]
            separator = "&" if "?" in base_url else "?"
            urls.append({
                "label": "Television",
                "url": f"{base_url}{separator}mode=tv",
            })
        return {
            "argv": command,
            "command": (
                f"cd {shlex.quote(str(self.repo))}\n"
                + (
                    f"PORT={selected_port} {shlex.join(base_command)}"
                    if selected_port != preferred_port else
                    shlex.join(base_command)
                )
            ),
            "urls": urls,
            "kind": "python",
            "preferred_port": preferred_port,
            "port": selected_port,
        }

    def application_instructions(self) -> dict:
        entrypoint = self._application_entrypoint()
        if entrypoint is None:
            return {
                "available": False,
                "repository": str(self.repo),
                "command": "",
                "urls": [],
            }
        return {
            "available": True,
            "repository": str(self.repo),
            "command": entrypoint["command"],
            "urls": entrypoint["urls"],
            "kind": entrypoint["kind"],
            "preferred_port": entrypoint["preferred_port"],
            "port": entrypoint["port"],
        }

    def canvas(self) -> dict:
        source = self.canvas_path if self.canvas_path.is_file() else self.repo / "factory" / "FACTORY_CANVAS.md"
        text = source.read_text() if source.is_file() else "# Factory Canvas\n\n"
        return {"path": str(self.canvas_path.relative_to(self.repo)), "text": text, "saved": self.canvas_path.is_file()}

    def save_canvas(self, text: str) -> dict:
        if not isinstance(text, str) or not text.strip():
            raise InputError("The Factory Canvas cannot be empty.")
        if len(text.encode()) > MAX_BODY:
            raise InputError("The Factory Canvas is too large.")
        temp = self.canvas_path.with_suffix(".tmp")
        temp.write_text(text.rstrip() + "\n")
        os.replace(temp, self.canvas_path)
        return self.canvas()

    def operation_snapshot(self) -> dict:
        with self.lock:
            value = dict(self.operation)
        log = value.get("log")
        log_path = Path(log) if log else None
        if log_path is not None and not log_path.is_absolute():
            log_path = self.control_repo / log_path
        value["output"] = tail_text(log_path) if log_path else ""
        if value.get("status") == "failed" and not value.get("failure"):
            guidance = self._operation_failure_guidance(
                value.get("action", ""),
                value.get("exit_code"),
                value["output"],
                value.get("command", ""),
            )
            value["failure"] = guidance
            value["error"] = f"{guidance['cause']} {guidance['recovery']}"
        return value

    @staticmethod
    def _operation_failure_guidance(
        action: str,
        exit_code: int | None,
        output: str,
        command: str,
    ) -> dict:
        plain = re.sub(r"\x1b\[[0-9;?]*[ -/]*[@-~]", "", output or "")
        lowered = plain.lower()
        if action == "start-app":
            missing_node_tool = (
                "command not found" in lowered
                or "is not recognized as an internal or external command" in lowered
            ) and any(tool in lowered for tool in ("vite", "next", "react-scripts"))
            if missing_node_tool:
                return {
                    "cause": (
                        "The final checkout is missing installed Node dependencies, "
                        "so the application package command is unavailable."
                    ),
                    "recovery": (
                        "Choose Start app again. The Control Center will install the "
                        "locked dependencies before retrying the server."
                    ),
                }
            if (
                "eaddrinuse" in lowered
                or "address already in use" in lowered
                or "port is already in use" in lowered
            ):
                return {
                    "cause": "The application could not bind its selected port because another process is using it.",
                    "recovery": (
                        "Stop the other server, refresh the Control Center so it selects "
                        "an available port, then choose Start app again."
                    ),
                }
            if (
                ("npm ci" in command or "npm install" in command)
                and ("npm error" in lowered or "npm err!" in lowered)
            ):
                return {
                    "cause": "The application dependencies could not be installed from package.json and its lockfile.",
                    "recovery": (
                        "Read the first npm error in Activity and CLI output, correct the "
                        "reported package or network problem, then choose Start app again."
                    ),
                }

        lines = [
            line.strip()
            for line in plain.splitlines()
            if line.strip() and not line.lstrip().startswith("$ ")
        ]
        first_fail = _first_fail(plain)
        diagnostic = first_fail or next(
            (
                line for line in reversed(lines)
                if any(
                    marker in line.lower()
                    for marker in ("error", "failed", "fatal", "not found", "denied")
                )
            ),
            lines[-1] if lines else "",
        )
        if first_fail:
            layer, recovery = _readiness_recovery(first_fail)
            return {
                "cause": f"{layer} readiness failure. First reported failure: {first_fail[:300]}",
                "recovery": recovery,
            }
        layer = "Control plane"
        recovery_prefix = "Repair the Control Center or GitHub connection."
        if action.startswith("environment-") or any(
            marker in lowered for marker in (
                "required tool", "no module named", "port ", "project contract",
                "dependency", "command not found",
            )
        ):
            layer = "Development environment"
            recovery_prefix = "Correct the Project Contract, tool, dependency, service, or port check."
        elif any(marker in lowered for marker in (
            "adapter not found", "not signed in", "auth login", "claude", "codex", "cursor",
        )):
            layer = "Inner harness"
            recovery_prefix = "Install or sign in to the selected Agent Adapter, then run its preflight again."
        elif any(marker in lowered for marker in ("factory charter", "policy", "governance")):
            layer = "Outer harness"
            recovery_prefix = "Review and approve the versioned policy contract before dispatch."
        suffix = f" Last output: {diagnostic[:300]}" if diagnostic else ""
        subject = "Application startup" if action == "start-app" else "The operation"
        return {
            "cause": (
                f"{layer} failure. {subject} exited with code "
                f"{exit_code if exit_code is not None else 'unknown'}.{suffix}"
            ),
            "recovery": (
                f"{recovery_prefix} Use the displayed command and Activity and CLI output "
                "to correct the first reported error, then repeat this action."
            ),
        }

    @staticmethod
    def _journey_guidance(
        phase_index: int, headline: str, detail: str, next_label: str,
        next_detail: str, next_view: str, *, state: str = "ready",
        ticket: int | None = None,
    ) -> dict:
        return {
            "phase_index": phase_index,
            "state": state,
            "headline": headline,
            "detail": detail,
            "next_label": next_label,
            "next_detail": next_detail,
            "next_view": next_view,
            "ticket": ticket,
        }

    def _resolve_journey_stage(
        self, *, connected: bool, project_ready: bool, charter_ready: bool,
        setup_published: bool, environment_ready: bool, environment: dict | None,
        prd_ready: bool, planning: dict, tickets_approved: bool,
        tickets: list[dict], delivery_done: bool, planning_journey: dict,
        supervisor: dict | None,
    ) -> dict:
        """Resolve the first applicable journey state in priority order."""
        guidance = self._journey_guidance
        if not connected:
            return guidance(
                0, "Connect this repository",
                "Choose the GitHub repository, run mode, profile, and agent preset.",
                "Open Connect", "Save the repository and factory settings.",
                "connect",
            )
        if not project_ready:
            return guidance(
                0, "Create the repository contract",
                "The factory will detect source folders, tests, gates, and operating limits for your review.",
                "Create contract",
                "Open Connect and generate the repository contract from the selected repository.",
                "connect", state="attention",
            )
        if not (charter_ready and setup_published and environment_ready):
            environment_status = (environment or {}).get("status", "not-provisioned")
            detail = (
                "Review the detected repository model and operating policy. One approval publishes "
                "the setup, prepares the environment, checks health, and runs preflight."
                if environment_status != "blocked" else
                "Automatic preparation stopped at a failed check. Read the first failure, correct "
                "it, then approve again to retry the remaining setup."
            )
            return guidance(
                0, "Review and approve the repository contract", detail,
                "Review and approve",
                "Open Connect, inspect the contract, and approve the automatic setup sequence.",
                "connect", state="attention",
            )
        if not prd_ready:
            return guidance(
                1, "Define the product outcome",
                "Review or replace the sample PRD before any planning adapter runs.",
                "Open the PRD", "Confirm the user, behavior, constraints, and evidence.",
                "prd",
            )
        if not planning.get("plan_id"):
            return guidance(
                2, "The PRD is ready for Product Review",
                "The first expert will turn the requirement into a testable product contract.",
                "Start Product Review",
                "Choose Rehearsal or Live adapters on the PRD screen.", "prd",
            )
        if not tickets_approved:
            next_step = planning_journey["next"]
            return guidance(
                planning_journey["phase_index"], planning_journey["headline"],
                planning_journey["detail"], next_step["label"], next_step["detail"],
                next_step["view"], state=planning_journey["state"],
            )
        if not tickets:
            return guidance(
                4, "Approved tickets are ready to load",
                "The plan is approved. Start the factory to load the PRD-derived tickets and begin independent QA.",
                "Open Tickets", "Run one cycle to pause after the first QA proposal.",
                "tickets",
            )
        if (supervisor or {}).get("status") == "running":
            return guidance(
                4, "The supervisor is coordinating the next dispatch wave",
                "It is reading worker Handoff Receipts and dependency-ready Tickets before issuing validated instructions.",
                "Inspect supervisor",
                "Review its input, dispatch commands, and coordination history.",
                "supervisor", state="running",
            )
        qa_review = next((ticket for ticket in tickets if ticket.get("status") == "QA Review"), None)
        if qa_review:
            number = qa_review.get("number")
            return guidance(
                4, f"Acceptance tests need approval for #{number}",
                "Implementation is paused. Inspect the Tests tab and approve only evidence that proves the ticket behavior.",
                f"Review ticket #{number}",
                "Open the ticket and inspect its protected tests.",
                "tickets", state="attention", ticket=number,
            )
        blocked = next((ticket for ticket in tickets if ticket.get("status") == "Blocked"), None)
        if blocked:
            number = blocked.get("number")
            failure = str(blocked.get("failure") or "").strip()
            detail = failure.splitlines()[-1][:420] if failure else "Read the ticket history and final log to find the recorded cause."
            recovery = blocked.get("recovery") or {}
            return guidance(
                4, f"Ticket #{number} is blocked", detail,
                f"Resolve blocker #{number}",
                recovery.get("summary") or "Review the recorded cause and available recovery action.",
                "tickets", state="blocked", ticket=number,
            )
        active = next(
            (ticket for ticket in tickets if ticket.get("status") in {"In Progress", "Verifying"}),
            None,
        )
        if active:
            number = active.get("number")
            labels = {
                "qa": "Independent QA is writing acceptance tests",
                "implementation": "The Implementation adapter is changing the code",
                "verifying": "Quality gates are checking the change",
                "cleanup": "The cleanup adapter is checking the change",
                "architecture_conformance": "Architecture conformance is being checked",
                "hardening": "The hardening adapter is checking the change",
                "final_verifier": "The final verifier is checking the change",
                "code-review": "The Code Review adapter is inspecting the candidate diff",
            }
            phase = active.get("phase", "implementation")
            return guidance(
                4, f"{labels.get(phase, 'An adapter is running')} for #{number}",
                f"{active.get('title', 'Ticket')} · attempt {active.get('attempt') or active.get('qa_attempt') or 1}.",
                f"Inspect ticket #{number}",
                "Follow its prompt, live log, diff, tests, code review, and history.",
                "tickets", state="running", ticket=number,
            )
        in_review = next((ticket for ticket in tickets if ticket.get("status") == "In Review"), None)
        if in_review:
            number = in_review.get("number")
            human_merge = in_review.get("merge_authority", "human") == "human"
            return guidance(
                4,
                f"Your exact-revision merge decision is required for #{number}"
                if human_merge else f"Autonomous Demo merge for #{number} is synchronizing",
                "Verification and code review passed. Inspect the approved head and evidence, then decide whether to merge it."
                if human_merge else "The explicitly delegated demo path is synchronizing its Supervisor-authorized merge.",
                f"Review ticket #{number}",
                "Open its exact head, review decision, gates, and merge action.",
                "tickets", state="attention" if human_merge else "running", ticket=number,
            )
        ready = [ticket for ticket in tickets if ticket.get("status") == "Ready"]
        if ready:
            return guidance(
                4, f"{len(ready)} ticket{'s are' if len(ready) != 1 else ' is'} ready",
                "Dependencies are satisfied. The next run will dispatch QA and implementation in isolated worktrees.",
                "Run the factory", "Open Tickets and start the available work.",
                "tickets",
            )
        if delivery_done:
            return guidance(
                5, "The application is ready",
                "All Tickets are Done. Start the application and open the supported layouts.",
                "Run the app", "Use the startup command and URLs on the final page.",
                "evidence", state="complete",
            )
        return guidance(
            4, "No ticket can start",
            "Inspect dependencies and ticket history. A cycle or unmet dependency may be preventing progress.",
            "Inspect Tickets", "Find the first dependency that cannot be satisfied.",
            "tickets", state="attention",
        )

    def setup_readiness(self, planning, tickets, operation, prd, config, project, charter, environment) -> dict:
        """Use persisted facts, never presentation dictionaries, for setup."""
        has_plan = bool(PLAN_ID.fullmatch(str(planning.get("plan_id", ""))))
        connected = bool(config if config is not None else self.session_config()) or has_plan or bool(tickets)
        project_ready = project is None or bool(project.get("configured") and project.get("valid"))
        charter_ready = charter is None or bool(charter.get("approved"))
        setup_published = (
            project is None
            or bool(project.get("committed"))
            or not bool((config or {}).get("github_repository"))
            or has_plan
            or bool(tickets)
        )
        setup_attempt_incomplete = (
            operation.get("action") == "approve-contract"
            and operation.get("status") in {"running", "stopping", "failed"}
        )
        environment_ready = (
            environment is None
            or (
                environment.get("status") == "healthy"
                and not setup_attempt_incomplete
            )
            or ((has_plan or bool(tickets)) and not setup_attempt_incomplete
                and (environment or {}).get("status") != "blocked")
        )
        prd_ready = bool(prd.get("saved")) or has_plan
        return {
            "connected": connected,
            "contract_ready": project_ready,
            "charter_ready": charter_ready,
            "published": setup_published,
            "environment_ready": environment_ready,
            "prd_ready": prd_ready,
            "complete": all((connected, project_ready, charter_ready, setup_published, environment_ready)),
        }

    def journey(
        self,
        planning: dict,
        factory: dict,
        operation: dict,
        prd: dict,
        evidence: list[dict],
        config: dict | None = None,
        supervisor: dict | None = None,
        project: dict | None = None,
        charter: dict | None = None,
        environment: dict | None = None,
    ) -> dict:
        tickets = factory.get("tickets", [])
        approvals = planning.get("approvals", {})
        phase_specs = [
            ("connect", "Connect", "Choose adapters and check the repository", "connect"),
            ("prd", "PRD", "Define the user outcome", "prd"),
            ("plan", "Plan", "Review expert contracts", "planning"),
            ("tickets", "Tickets", "Approve and create vertical slices", "planning"),
            ("build", "Build & verify", "Run QA, implementation, and gates", "tickets"),
            ("evidence", "Run app", "Open the completed application", "evidence"),
        ]
        setup = self.setup_readiness(
            planning, tickets, operation, prd, config, project, charter, environment,
        )
        connected = setup["connected"]
        project_ready = setup["contract_ready"]
        charter_ready = setup["charter_ready"]
        setup_published = setup["published"]
        environment_ready = setup["environment_ready"]
        prd_ready = setup["prd_ready"]
        plan_complete = planning.get("status") in {"awaiting_alignment_approval", "alignment_approved", "published"}
        tickets_approved = (
            planning.get("status") == "published"
            or (
                planning.get("mode") != "live"
                and bool(approvals.get("alignment"))
            )
        )
        delivery_done = bool(tickets) and all(ticket.get("status") == "Done" for ticket in tickets)
        completed = [
            connected and project_ready and charter_ready and setup_published and environment_ready,
            prd_ready,
            plan_complete,
            tickets_approved,
            delivery_done,
            delivery_done,
        ]

        presentation = planning.get("presentation") or planning_presentation(
            planning,
            current_adapter=(
                planning.get("planning_agent")
                or self.session_config().get("planning_agent")
                or "codex"
            ),
            adapters=self.adapters(),
        )
        resolved = self._resolve_journey_stage(
            connected=connected,
            project_ready=project_ready,
            charter_ready=charter_ready,
            setup_published=setup_published,
            environment_ready=environment_ready,
            environment=environment,
            prd_ready=prd_ready,
            planning=planning,
            tickets_approved=tickets_approved,
            tickets=tickets,
            delivery_done=delivery_done,
            planning_journey=presentation["journey"],
            supervisor=supervisor,
        )
        phase_index = resolved["phase_index"]
        state = resolved["state"]
        headline = resolved["headline"]
        detail = resolved["detail"]
        next_label = resolved["next_label"]
        next_detail = resolved["next_detail"]
        next_view = resolved["next_view"]
        ticket_number = resolved["ticket"]
        planning_journey = presentation["journey"]
        qa_review = next((ticket for ticket in tickets if ticket.get("status") == "QA Review"), None)
        blocked = next((ticket for ticket in tickets if ticket.get("status") == "Blocked"), None)
        in_review = next((ticket for ticket in tickets if ticket.get("status") == "In Review"), None)
        active = next(
            (ticket for ticket in tickets if ticket.get("status") in {"In Progress", "Verifying"}),
            None,
        )
        supervising = (supervisor or {}).get("status") == "running"
        attention = factory.get("human_attention", {})
        if attention.get("dispatch_paused"):
            phase_index = 4
            state = "attention"
            oldest = attention.get("oldest") or {}
            ticket_number = oldest.get("ticket")
            headline = "NEEDS YOU — new dispatch is paused"
            detail = (
                f"{attention.get('reason', 'Human-attention capacity is full')}. "
                "Running adapters may finish, but the factory will not create more review work."
            )
            next_label = (
                f"Open oldest decision #{ticket_number}"
                if ticket_number
                else f"Open {oldest.get('status', 'planning decision')}"
            )
            next_detail = "Complete the oldest required decision to reduce the queue and resume dispatch."
            next_view = "tickets" if ticket_number else "planning"

        operation_phase = {
            "doctor": 0, "configure": 0, "plan": 2, "restart-plan": 2, "revise-product": 2, "revise-stage": 2,
            "approve-contract": 0, "approve-charter": 0, "publish-setup": 0, "approve-product": 2, "continue-plan": 2, "publish-plan": 3,
            "approve-tests": 4, "merge": 4, "run": 4, "listen": 4, "run-once": 4, "dry-run": 4,
            "retry": 4, "evidence": 5, "reset-run": 4, "reset-all": 0,
            "release-claim": 4,
        }.get(operation.get("action"), phase_index)
        if operation.get("status") in {"running", "stopping"}:
            phase_index = operation_phase
            if qa_review or blocked or in_review or supervising:
                # A required human decision is more useful than the fact that the
                # scheduler process remains alive while it waits.
                pass
            elif active:
                state = "running"
            else:
                state = "running"
                headline = operation.get("title") or "Factory operation is running"
                detail = "Output is streaming in the operation console. You can inspect tickets while it runs."
                next_label, next_detail, next_view = "Watch live output", "The current command and its latest output are shown below.", "overview"
        elif operation.get("status") == "failed":
            state = "blocked"
            decision_kind = (presentation.get("decision") or {}).get("kind")
            if not tickets_approved and decision_kind in {
                "replan", "questions", "correction", "recovery",
            }:
                phase_index = planning_journey["phase_index"]
                state = planning_journey["state"]
                headline = planning_journey["headline"]
                detail = planning_journey["detail"]
                next_label = planning_journey["next"]["label"]
                next_detail = planning_journey["next"]["detail"]
                next_view = planning_journey["next"]["view"]
            elif operation.get("action") == "approve-contract":
                phase_index = 0
                headline = "Automatic repository setup stopped"
                detail = operation.get("error") or (
                    "Read the first failed check, correct it, then retry Step 3."
                )
                next_label = "Fix and retry setup"
                next_detail = (
                    "Open Connect. Step 3 remains active and retries the same "
                    "reviewed contract after you fix the first error."
                )
                next_view = "connect"
            else:
                phase_index = operation_phase
                headline = f"{operation.get('title') or 'The last operation'} failed"
                detail = operation.get("error") or "Read the final output lines to find the cause."
                next_label, next_detail, next_view = "Read the failure output", "Fix the first reported error, then repeat the action.", "overview"

        phases = []
        for index, (phase_id, label, description, view) in enumerate(phase_specs):
            status = "complete" if completed[index] else ("current" if index == phase_index else "pending")
            phases.append({"id": phase_id, "label": label, "description": description, "view": view, "status": status})
        return {
            "state": state,
            "phase_index": phase_index,
            "phase_number": phase_index + 1,
            "phase_count": len(phases),
            "phase_label": phases[phase_index]["label"],
            "setup": setup,
            "headline": headline,
            "detail": detail,
            "ticket": ticket_number,
            "next": {"label": next_label, "detail": next_detail, "view": next_view},
            "phases": phases,
        }

    @staticmethod
    def operator_decisions(planning: dict, factory: dict) -> list[dict]:
        """Return one authoritative, directly routable human-decision queue."""
        tickets = factory.get("tickets", [])
        attention = factory.get("human_attention", {})
        planning_decision = planning.get("presentation", {}).get("decision")
        decisions: list[dict] = []
        planning_consumed = False

        if attention.get("dispatch_paused"):
            oldest = attention.get("oldest") or {}
            ticket = next(
                (
                    item for item in tickets
                    if item.get("number") == oldest.get("ticket")
                ),
                None,
            )
            paused = {
                "title": "NEEDS YOU · Dispatch paused",
                "text": (
                    f"{attention.get('reason', 'Human-attention capacity is full')}. "
                    "Complete the oldest decision to resume new work."
                ),
                "view": "tickets" if ticket else "planning",
            }
            if ticket:
                paused["ticket"] = ticket
            elif oldest.get("plan_id") and planning_decision:
                paused.update({
                    "planning": planning_decision.get("planning", ""),
                    "view": planning_decision.get("view", "planning"),
                })
                planning_consumed = True
            decisions.append(paused)

        if planning_decision and not planning_consumed:
            decisions.append(planning_decision)
        decisions.extend({
            "title": f"Approve tests for #{ticket.get('number')}",
            "text": ticket.get("title", ""),
            "ticket": ticket,
            "view": "tickets",
        } for ticket in tickets if ticket.get("status") == "QA Review")
        decisions.extend({
            "title": f"Decide whether to merge #{ticket.get('number')}",
            "text": (
                f"Exact approved head {str(ticket.get('approved_head') or '')[:12] or 'not recorded'}"
                f" · {ticket.get('title', '')}"
            ),
            "ticket": ticket,
            "view": "tickets",
        } for ticket in tickets if (
            ticket.get("status") == "In Review"
            and ticket.get("merge_authority") == "human"
        ))
        decisions.extend({
            "title": f"Resolve blocked #{ticket.get('number')}",
            "text": ticket.get("failure") or ticket.get("title", ""),
            "ticket": ticket,
            "view": "tickets",
        } for ticket in tickets if ticket.get("status") == "Blocked")
        return decisions

    def stream_snapshot(self) -> dict:
        """Share at most one snapshot per second across status streams."""
        with self._stream_lock:
            current = time.monotonic()
            if (
                self._stream_value is None
                or current - self._stream_at >= 1
                or self._stream_value["repo"]["path"] != str(self.repo)
            ):
                self._stream_value = self.snapshot()
                self._stream_at = current
            return self._stream_value

    def snapshot(self) -> dict:
        planning = read_json(self.repo / ".factory" / "planning-state.json", {})
        plan_id = planning.get("plan_id", "")
        run_dir = self.repo / ".factory" / "plans" / plan_id
        manifest = read_json(run_dir / "manifest.json", {}) if PLAN_ID.fullmatch(plan_id) else {}
        slices = read_json(run_dir / "04-vertical-slices.json", {}) if PLAN_ID.fullmatch(plan_id) else {}
        publication = slices.get("publication") if isinstance(slices, dict) else None
        if isinstance(publication, dict):
            issues = publication.get("issues")
            issues = issues if isinstance(issues, dict) else {}
            repository = publication.get("repository", "")
            published_tickets = []
            for ticket in slices.get("tickets", []):
                key = ticket.get("key", "")
                number = issues.get(key)
                if not key or not isinstance(number, int):
                    continue
                dependencies = [
                    issues[dependency]
                    for dependency in ticket.get("dependencies", [])
                    if dependency in issues
                ]
                published_tickets.append({
                    "number": number,
                    "key": key,
                    "title": ticket.get("title", key),
                    "agent": ticket.get("agent", ""),
                    "dependencies": dependencies,
                    "url": (
                        f"https://github.com/{repository}/issues/{number}"
                        if repository else ""
                    ),
                })
            planning["publication"] = {
                "repository": repository,
                "project_number": publication.get("project_number"),
                "issues": issues,
                "ticket_count": len(issues),
                "tickets": published_tickets,
            }
        planning_agent = planning.get("planning_agent") or self.session_config().get("planning_agent") or "codex"
        if manifest.get("plan_id") == plan_id:
            planning_agent = manifest.get("planning_agent", "codex")
            planning["planning_agent"] = planning_agent
            planning["mode"] = "rehearsal" if planning_agent == "mock" else "live"
        presentation = planning_presentation(
            planning,
            current_adapter=planning_agent,
            adapters=self.adapters(),
        )
        planning["presentation"] = presentation
        # Compatibility fields keep older local Control Center assets useful
        # while every current caller reads the normalized presentation.
        for key in (
            "can_continue",
            "requires_decisions",
            "requires_correction",
            "requires_replan",
            "replan_reason",
            "blocked_stage",
            "failed_stage",
            "recovery",
            "continue_label",
        ):
            planning[key] = presentation[key]
        factory = read_json(self.repo / ".factory" / "state.json", {"tickets": []})
        factory["execution_mode"] = factory_execution_mode(factory)
        operation = self.operation_snapshot()
        prd = {key: value for key, value in self.prd().items() if key != "text"}
        evidence = self.evidence_files()
        monitor = read_json(self.repo / ".factory" / "monitor" / "report.json", {})
        config = self.session_config()
        checkpoint = latest_recovery_checkpoint(self.repo)
        current_is_latest = current_runtime_is_latest(self.repo, checkpoint)
        recovery = {
            "available": bool(
                (checkpoint and not current_is_latest)
                or (not checkpoint and config.get("github_repository"))
            ),
            "source": "current" if current_is_latest else "checkpoint" if checkpoint else (
                "github" if config.get("github_repository") else ""
            ),
            "checkpoint_id": (checkpoint or {}).get("checkpoint_id", ""),
            "created_at": (checkpoint or {}).get("created_at", ""),
            "snapshot_at": (checkpoint or {}).get("snapshot_at", ""),
            "ticket_count": (checkpoint or {}).get("ticket_count", 0),
            "plan_id": (checkpoint or {}).get("plan_id", ""),
            "mode": (checkpoint or {}).get("mode", ""),
            "github_available": bool(config.get("github_repository")),
            "project_number": config.get("project_number"),
        }
        project = self.project_contract()
        charter = self.factory_charter()
        environment = self.environment_snapshot()
        if charter.get("approved"):
            try:
                approved_charter = FactoryCharter.load(
                    self.repo, require_approved=True,
                )
                for ticket in factory.get("tickets", []):
                    if ticket.get("status") == "Blocked":
                        ticket["diff_budget"] = ticket_diff_budget(
                            self.repo, ticket, approved_charter,
                        )
                        ticket["recovery"] = ticket_recovery(ticket, self.repo)
                        ticket["next_human_action"] = ticket["recovery"]["action"]
            except FactoryCharterError:
                pass
        for ticket in factory.get("tickets", []):
            ticket["merge_steward"] = self.merge_steward_snapshot(ticket)
        factory["human_attention"] = human_attention_snapshot(
            self.repo,
            factory.get("tickets", []),
            review_limit=charter.get("max_awaiting_human_review", 3),
            blocked_limit=charter.get("max_blocked_for_human", 2),
            oldest_limit=charter.get("oldest_review_hours", 24),
            planning=planning,
        )
        decisions = self.operator_decisions(planning, factory)
        supervisor = read_json(self.repo / ".factory" / "supervisor" / "state.json", {})
        if factory.get("supervisor_agent") == "disabled" or (
            not factory.get("supervisor_agent") and config.get("profile") == "lean"
        ):
            supervisor = {"enabled": False, "status": "disabled", "events": []}
        return {
            "repo": self.repo_info(),
            "config": config,
            "project": project,
            "charter": charter,
            "adapters": self.adapters(),
            "adapter_details": self.adapter_details(),
            "environment": environment,
            "workspace": self.workspace_snapshot(),
            "improvements": self.improvements_snapshot(),
            "triggers": self.triggers_snapshot(),
            "planning": planning,
            "factory": factory,
            "supervisor": supervisor,
            "operation": operation,
            "prd": prd,
            "evidence": evidence,
            "application": self.application_instructions(),
            "monitor": monitor,
            "recovery": recovery,
            "decisions": decisions,
            "journey": self.journey(
                planning, factory, operation, prd, evidence, config, supervisor,
                project, charter, environment,
            ),
        }

    @staticmethod
    def _string(payload: dict, key: str, *, required=False, max_length=160) -> str:
        value = payload.get(key, "")
        if value is None:
            value = ""
        if not isinstance(value, str):
            raise InputError(f"{key.replace('_', ' ').title()} must be text.")
        value = value.strip()
        if required and not value:
            raise InputError(f"{key.replace('_', ' ').title()} is required.")
        if len(value) > max_length:
            raise InputError(f"{key.replace('_', ' ').title()} is too long.")
        return value

    @staticmethod
    def _positive_int(payload: dict, key: str, *, required=False) -> int | None:
        value = payload.get(key)
        if value in (None, ""):
            if required:
                raise InputError(f"{key.replace('_', ' ').title()} is required.")
            return None
        if isinstance(value, bool):
            raise InputError(f"{key.replace('_', ' ').title()} must be a positive number.")
        try:
            number = int(value)
        except (TypeError, ValueError) as exc:
            raise InputError(f"{key.replace('_', ' ').title()} must be a positive number.") from exc
        if number < 1:
            raise InputError(f"{key.replace('_', ' ').title()} must be a positive number.")
        return number

    def _plan_id(self, payload: dict) -> str:
        value = self._string(payload, "plan_id") or self.latest_plan_id()
        if not PLAN_ID.fullmatch(value):
            raise InputError("Choose a valid planning run first.")
        return value

    def _plan_uses_mock(self, plan_id: str) -> bool:
        manifest = read_json(self.repo / ".factory" / "plans" / plan_id / "manifest.json", {})
        if manifest.get("plan_id") != plan_id:
            raise InputError("Choose a valid planning run first.")
        return manifest.get("planning_agent") == "mock"

    def _blocking_decision_feedback(
        self, payload: dict, plan_id: str, stage_id: str,
    ) -> str | None:
        """Build compact revision feedback from the current blocking decisions."""
        decisions = payload.get("decisions")
        if decisions is None:
            return None
        if not isinstance(decisions, list):
            raise InputError("Decisions must be a list of text answers.")

        planning = read_json(self.repo / ".factory" / "planning-state.json", {})
        if planning.get("plan_id") != plan_id:
            raise InputError("The selected planning run is no longer current.")
        stage = next(
            (item for item in planning.get("stages", []) if item.get("id") == stage_id),
            None,
        )
        questions = stage.get("questions", []) if isinstance(stage, dict) else []
        if not questions or stage.get("status") != "blocked":
            raise InputError("This expert does not have blocking questions to answer.")
        if len(decisions) != len(questions):
            raise InputError("Answer every current blocking question before continuing.")

        answers = []
        for index, decision in enumerate(decisions, 1):
            if not isinstance(decision, str) or not decision.strip():
                raise InputError(f"Decision {index} is required.")
            answer = decision.strip()
            if len(answer) > 4000:
                raise InputError(f"Decision {index} is too long.")
            answers.append(answer)

        feedback = "\n".join([
            f"Resolve all {len(questions)} blocking questions in the rejected "
            f"{stage.get('title') or stage_id.replace('_', ' ')} artifact using these decisions:",
            "",
            *(f"{index}. {answer}" for index, answer in enumerate(answers, 1)),
        ])
        if len(feedback) > MAX_PLANNING_FEEDBACK:
            raise InputError("The combined decisions are too long.")
        return feedback

    def _mode_flags(self, payload: dict) -> list[str]:
        if payload.get("mode", "rehearsal") != "live":
            scenario = self._string(payload, "scenario") or "recipe-rebrand"
            if scenario not in SCENARIOS:
                raise InputError("Unknown rehearsal scenario.")
            return ["--mock", "--scenario", scenario]
        return []

    def _ticket_action_context(
        self,
        issue: int,
        requested_mode: str,
    ) -> dict:
        state = read_json(self.repo / ".factory" / "state.json", {"tickets": []})
        evidence_mode = factory_execution_mode(state)
        if evidence_mode == "mixed":
            raise InputError(
                "Local state contains mixed Live and Rehearsal evidence. Open Reset, clear "
                "local run state, and reload the intended run."
            )
        if evidence_mode and evidence_mode != requested_mode:
            source = "Rehearsal" if evidence_mode == "rehearsal" else "Live"
            target = "Live" if requested_mode == "live" else "Rehearsal"
            raise InputError(
                f"Ticket #{issue} belongs to a {source} run, but the Control Center is set "
                f"to {target}. Switch back to {source} to finish that run, or open Reset "
                f"and clear local run state before starting {target}."
            )
        return next(
            (
                ticket for ticket in state.get("tickets", [])
                if ticket.get("number") == issue
            ),
            {},
        )

    def _autonomous_flags(self, payload: dict) -> list[str]:
        """Require a fresh operator delegation for every Autonomous Demo start."""
        profile = self.session_config().get("profile") or "standard"
        opted_in = payload.get("allow_autonomous_merge") is True
        if profile == "autonomous-demo":
            if not opted_in:
                raise InputError(
                    "Autonomous Demo delegates final merge accountability to the "
                    "Supervisor and orchestrator. Review the warning and explicitly opt in."
                )
            return ["--allow-autonomous-merge"]
        if opted_in:
            raise InputError(
                "Autonomous merge opt-in is valid only for the Autonomous Demo profile."
            )
        return []

    def build_commands(self, action: str, payload: dict) -> tuple[str, list[list[str]]]:
        if action not in ACTION_REGISTRY:
            raise InputError("This control-center action is not registered.")
        builder_name = ACTION_BUILDERS.get(action)
        if not builder_name:
            raise InputError("This control-center action is not available.")
        self._pending_activation = None
        return getattr(self, builder_name)(action, payload)

    def _build_setup_command(
        self, action: str, payload: dict,
    ) -> tuple[str, list[list[str]]]:
        base = [str(self.factory)]
        mode = payload.get("mode", "rehearsal")
        if action == "doctor":
            return "Check readiness", [base + ["doctor"] + (["--full"] if payload.get("full") else [])]
        if action == "init-project":
            if (self.repo / CONTRACT_PATH).is_file():
                raise InputError("This repository already has a Project Contract.")
            return "Initialize Project Contract", [base + ["init", "--repo", str(self.repo)]]
        if action == "approve-contract":
            project = self.project_contract()
            if not project.get("configured") or not project.get("valid"):
                raise InputError(
                    project.get("error") or "Create a valid repository contract first."
                )
            charter = self.factory_charter()
            if not charter.get("configured") or not charter.get("valid"):
                raise InputError(
                    charter.get("error") or "Create a valid repository contract first."
                )
            live = mode == "live"
            if live and not self.session_config().get("github_repository"):
                raise InputError(
                    "Select and save a GitHub repository before approving Live setup."
                )
            command = base + [
                "approve-contract", "--repo", str(self.repo), "--yes",
            ]
            if live:
                command.append("--live")
            return "Approve and prepare repository", [command]
        if action == "approve-charter":
            charter = self.factory_charter()
            if not charter.get("configured") or not charter.get("valid"):
                raise InputError(charter.get("error") or "Create a valid Factory Charter first.")
            if charter.get("approved"):
                raise InputError("The current Factory Charter policy is already approved.")
            return "Approve Factory Charter", [
                base + ["approve-charter", "--repo", str(self.repo), "--yes"],
            ]
        if action == "publish-setup":
            charter = self.factory_charter()
            if not charter.get("approved"):
                raise InputError("Approve the exact Factory Charter before publishing setup.")
            return "Publish repository setup", [
                base + ["publish-setup", "--repo", str(self.repo), "--yes"],
            ]
        if action.startswith("environment-"):
            ProjectContract.load(self.repo, require=True)
            environment_action = action.removeprefix("environment-")
            titles = {
                "provision": "Provision development environment",
                "prepare": "Prepare development environment",
                "health": "Check development environment",
                "reset": "Reset provider-owned environment state",
            }
            command = base + ["environment", environment_action, "--repo", str(self.repo)]
            if environment_action == "prepare":
                command.append("--yes")
            if environment_action == "health":
                command.append("--gates")
            return titles[environment_action], [command]
        if action == "improve-report":
            return "Generate reviewed improvement report", [
                base + ["improve", "report", "--repo", str(self.repo), "--json"],
            ]
        if action == "workspace-check":
            return "Check repository workspace", [
                base + ["workspace-check", "--repo", str(self.repo), "--json"],
            ]
        if action == "approve-intake":
            if mode != "live":
                raise InputError("Evidence-backed intake approval requires Live mode.")
            issue = self._positive_int(payload, "issue", required=True)
            case_id = self._string(payload, "case_id", required=True, max_length=80)
            reason = self._string(payload, "reason", required=True, max_length=300)
            if len(reason) < 12:
                raise InputError("Explain why the intake evidence is sufficient.")
            return "Approve evidence-backed intake", [
                base + [
                    "approve-intake", str(issue), "--repo", str(self.repo),
                    "--case", case_id, "--reason", reason, "--yes",
                ],
            ]
        if action == "steward-sync":
            issue = self._positive_int(payload, "issue", required=True)
            return "Synchronize candidate for re-verification", [
                base + [
                    "steward", str(issue), "--repo", str(self.repo),
                    "--synchronize", "--yes", "--json",
                ],
            ]
        if action == "start-app":
            application = self._application_entrypoint()
            if application is None:
                raise InputError(
                    "No supported application entry point was detected. Add a package.json "
                    "start/dev/serve script or a Python app.py entry point."
                )
            return "Run the completed application", [
                *application.get("prepare_argv", []),
                application["argv"],
            ]
        raise InputError("This setup action is not available.")

    def _build_configure_command(
        self, action: str, payload: dict,
    ) -> tuple[str, list[list[str]]]:
        base = [str(self.factory)]
        mode = payload.get("mode", "rehearsal")
        if action == "configure":
            command = base + ["configure"]
            commands = []
            bootstrap_workshop = payload.get("bootstrap_workshop") is True
            repository = self._string(payload, "github_repository", max_length=240)
            if mode == "live" and not repository:
                repository = self.session_config().get("github_repository", "")
            if mode == "live" and not repository:
                raise InputError("Enter the GitHub repository URL before saving Live configuration.")
            if bootstrap_workshop and mode != "live":
                raise InputError("Workshop bootstrap is available only for a Live repository.")
            if mode == "live":
                try:
                    requested = parse_github_repository(repository)
                    repository = requested.url
                except ValueError as exc:
                    raise InputError(str(exc)) from exc
                current_remote = repository_from_remote(
                    run_text(["git", "remote", "get-url", "origin"], self.repo)
                )
                if not current_remote or current_remote.slug.lower() != requested.slug.lower():
                    target = managed_checkout_path(self.repository_root, requested)
                    commands.append([
                        str(self.factory), "checkout", repository,
                        "--workspace-root", str(self.repository_root),
                    ])
                    command += ["--repo", str(target)]
                    self._pending_activation = target
                else:
                    target = self.repo
                    command += ["--repo", str(self.repo)]
                if bootstrap_workshop:
                    commands.append([
                        str(self.factory), "bootstrap-workshop",
                        "--repo", str(target),
                        "--source", str(self.control_repo),
                    ])
                command += ["--github-repository", repository]
            preset = self._string(payload, "preset")
            if preset:
                if preset not in PRESETS:
                    raise InputError("Unknown agent preset.")
                command += ["--preset", preset]
            profile = self._string(payload, "profile")
            if profile:
                if profile not in FACTORY_PROFILES:
                    raise InputError("Unknown factory profile.")
                command += ["--profile", profile]
            known = set(self.adapters())
            for field, flag in (
                ("agent", "--agent"),
                ("qa_agent", "--qa-agent"),
                ("supervisor_agent", "--supervisor-agent"),
                ("review_agent", "--review-agent"),
            ):
                value = self._string(payload, field)
                if value:
                    if not AGENT_NAME.fullmatch(value) or value not in known:
                        raise InputError(f"Unknown {field.replace('_', ' ')} adapter.")
                    command += [flag, value]
            planning = self._string(payload, "planning_agent")
            if planning:
                if planning not in PLANNING_AGENTS:
                    raise InputError("Planning must use Bedrock, Claude, Codex, or Cursor.")
                command += ["--planning-agent", planning]
            parallel = self._positive_int(payload, "max_parallel")
            project = self._positive_int(payload, "project_number")
            if parallel:
                command += ["--max-parallel", str(parallel)]
            if project:
                command += ["--project-number", str(project)]
            if "review_qa_tests" in payload:
                command.append("--review-qa-tests" if payload["review_qa_tests"] else "--no-review-qa-tests")
            if len(command) == 2:
                raise InputError("Choose a preset or at least one configuration value.")
            return "Save factory configuration", commands + [command]
        raise InputError("This configuration action is not available.")

    def _build_planning_command(
        self, action: str, payload: dict,
    ) -> tuple[str, list[list[str]]]:
        base = [str(self.factory)]
        mock = payload.get("mode", "rehearsal") != "live"
        if action == "plan":
            if not self.prd_path.is_file():
                raise InputError("Save the PRD before starting Product Review.")
            profile = self.session_config().get("profile") or "standard"
            if profile not in FACTORY_PROFILES:
                raise InputError("Unknown factory profile.")
            command = (
                base + ["plan", str(self.prd_path), "--profile", profile]
                + self._autonomous_flags(payload)
            )
            if mock:
                command.append("--mock")
            return "Run Product Review", [command]
        if action == "restart-plan":
            plan = self._plan_id(payload)
            planning = read_json(self.repo / ".factory" / "planning-state.json", {})
            if planning.get("plan_id") != plan or planning.get("status") not in REPLAN_REQUIRED_STATUSES:
                raise InputError("This planning run does not require a full restart.")
            run_dir = self.repo / ".factory" / "plans" / plan
            manifest = read_json(run_dir / "manifest.json", {})
            source_prd = self.prd_path if self.prd_path.is_file() else run_dir / "source-prd.md"
            if not source_prd.is_file():
                raise InputError("The saved PRD is missing. Save it again before restarting planning.")
            profile = self.session_config().get("profile") or manifest.get("profile") or "standard"
            if profile not in FACTORY_PROFILES:
                raise InputError("The saved factory profile is no longer available.")
            command = base + ["plan", str(source_prd), "--profile", profile]
            planning_agent = manifest.get("planning_agent", "codex")
            if planning_agent == "mock":
                command.append("--mock")
            else:
                if planning_agent not in PLANNING_AGENTS:
                    raise InputError("The saved planning adapter is no longer available.")
                command += ["--planning-agent", planning_agent]
            limits = manifest.get("ticket_limits", {})
            if isinstance(limits.get("minimum"), int):
                command += ["--min-tickets", str(limits["minimum"])]
            if isinstance(limits.get("maximum"), int):
                command += ["--max-tickets", str(limits["maximum"])]
            command += self._autonomous_flags(payload)
            return "Restart planning with current governance", [command]
        if action == "revise-product":
            plan = self._plan_id(payload)
            plan_mock = self._plan_uses_mock(plan)
            feedback = self._blocking_decision_feedback(
                payload, plan, "product_review",
            ) or self._string(
                payload, "feedback", required=True,
                max_length=MAX_PLANNING_FEEDBACK,
            )
            feedback_path = self.runtime / "product-feedback.md"
            feedback_path.write_text(feedback + "\n")
            command = base + ["revise", plan, "product", "--feedback-file", str(feedback_path)]
            if plan_mock:
                command.append("--mock")
            return "Revise Product Review", [command]
        if action == "revise-stage":
            plan = self._plan_id(payload)
            plan_mock = self._plan_uses_mock(plan)
            stage = self._string(payload, "stage", required=True)
            alias = REVISION_STAGE_ALIASES.get(stage)
            if not alias or alias == "product":
                raise InputError("Choose a blocked technical planning expert.")
            feedback = self._blocking_decision_feedback(
                payload, plan, stage,
            ) or self._string(
                payload, "feedback", required=True,
                max_length=MAX_PLANNING_FEEDBACK,
            )
            feedback_path = self.runtime / f"{stage.replace('_', '-')}-feedback.md"
            feedback_path.write_text(feedback + "\n")
            revise = base + ["revise", plan, alias, "--feedback-file", str(feedback_path)]
            resume = base + ["continue-plan", plan]
            if plan_mock:
                revise.append("--mock")
                resume.append("--mock")
            title = stage.replace("_", " ").title()
            return f"Resolve {title} decisions", [revise, resume]
        if action == "approve-product":
            return "Approve product intent", [base + ["approve-product", self._plan_id(payload), "--yes"]]
        if action == "approve-stage":
            plan = self._plan_id(payload)
            stage = self._string(payload, "stage", required=True)
            aliases = {
                "system_architecture": ("architecture", "System Architecture"),
                "program_design": ("program", "Program Design"),
            }
            if stage not in aliases:
                raise InputError("Planning stage approval must be architecture or program.")
            alias, title = aliases[stage]
            return f"Approve {title}", [
                base + ["approve-stage", alias, plan, "--yes"],
            ]
        if action == "continue-plan":
            plan = self._plan_id(payload)
            command = base + ["continue-plan", plan]
            if self._plan_uses_mock(plan):
                command.append("--mock")
            else:
                planning_agent = self._string(payload, "planning_agent")
                if planning_agent:
                    if planning_agent not in PLANNING_AGENTS:
                        raise InputError("Planning retry must use Bedrock, Claude, Codex, or Cursor.")
                    command += ["--planning-agent", planning_agent]
            return "Run architecture and delivery planning", [command]
        if action == "publish-plan":
            plan = self._plan_id(payload)
            if self._plan_uses_mock(plan):
                scenario = self._string(payload, "scenario") or "recipe-rebrand"
                if scenario not in SCENARIOS:
                    raise InputError("Unknown rehearsal scenario.")
                return "Approve rehearsal tickets", [[str(self.factory), "approve-rehearsal", plan, "--yes", "--scenario", scenario]]
            command = base + ["approve", plan, "--yes"]
            project = self._positive_int(payload, "project_number") or self.session_config().get("project_number")
            title = self._string(payload, "project_title", max_length=80)
            if project:
                command += ["--project-number", str(project)]
            elif title:
                command += ["--new-project-title", title]
            return "Publish tickets to GitHub", [command]
        raise InputError("This planning action is not available.")

    def _build_delivery_command(
        self, action: str, payload: dict,
    ) -> tuple[str, list[list[str]]]:
        base = [str(self.factory)]
        mode = payload.get("mode", "rehearsal")
        mock = mode != "live"
        if action == "approve-tests":
            issue = self._positive_int(payload, "issue", required=True)
            self._ticket_action_context(issue, mode)
            return f"Approve tests for ticket #{issue}", [base + ["approve-tests", str(issue), "--yes"]]
        if action == "request-test-changes":
            issue = self._positive_int(payload, "issue", required=True)
            ticket = self._ticket_action_context(issue, mode)
            if ticket.get("status") != "QA Review":
                raise InputError(
                    f"Ticket #{issue} is {ticket.get('status') or 'not available'}, "
                    "not QA Review."
                )
            feedback = self._string(
                payload, "feedback", required=True, max_length=4000,
            )
            return f"Request revised tests for ticket #{issue}", [[
                *base,
                "request-test-changes",
                str(issue),
                "--feedback",
                feedback,
                "--yes",
            ]]
        if action == "merge":
            issue = self._positive_int(payload, "issue", required=True)
            ticket = self._ticket_action_context(issue, mode)
            review = ticket.get("code_review") or {}
            review_references = (
                str(ticket.get("review_ref") or ""),
                str(review.get("pull_request") or "") if isinstance(review, dict) else "",
            )
            if not mock and ticket and (
                not ticket.get("pr_url")
                or any(reference.startswith("rehearsal://") for reference in review_references)
            ):
                raise InputError(
                    f"Ticket #{issue} has no Live GitHub pull request. Open Reset, clear the "
                    "local Rehearsal run state, then load and rerun the Live ticket."
                )
            command = base + ["merge", str(issue), "--repo", str(self.repo), "--yes"]
            if mock:
                command.append("--mock")
            project = self._positive_int(payload, "project_number") or self.session_config().get("project_number")
            if project and not mock:
                command += ["--project-number", str(project)]
            return f"Merge exact revision for ticket #{issue}", [command]
        if action in {"run", "listen", "run-once", "dry-run"}:
            if action == "listen" and mock:
                raise InputError(
                    "Repository issue listening requires Live mode and a connected GitHub repository."
                )
            command = (
                base + ["run"] + self._mode_flags(payload)
                + self._autonomous_flags(payload)
            )
            if action == "listen":
                command.append("--listen")
            elif action == "run-once":
                command.append("--once")
            elif action == "dry-run":
                command.append("--dry-run")
            if payload.get("review_qa_tests"):
                command.append("--review-qa-tests")
            return {
                "run": "Run the factory",
                "listen": "Listen for repository issues",
                "run-once": "Run one scheduling cycle",
                "dry-run": "Preview execution waves",
            }[action], [command]
        raise InputError("This delivery action is not available.")

    def _build_ticket_correction_command(
        self, action: str, payload: dict,
    ) -> tuple[str, list[list[str]]]:
        base = [str(self.factory)]
        mode = payload.get("mode", "rehearsal")
        mock = mode != "live"
        if action == "save-ticket-and-retry":
            if mock:
                raise InputError("Saving a Ticket correction requires a Live GitHub run.")
            issue = self._positive_int(payload, "issue", required=True)
            ticket = self._ticket_action_context(issue, mode)
            if ticket.get("status") != "Blocked":
                raise InputError(
                    f"Ticket #{issue} is {ticket.get('status') or 'not available'}, "
                    "not Blocked."
                )
            recovery = ticket_recovery(ticket, self.repo)
            if (
                recovery.get("kind") != "ticket_specification"
                or not recovery.get("proposed_ticket_body")
            ):
                raise InputError(
                    "This blocker does not have a structured Ticket correction to save."
                )
            corrected_body = self._string(
                payload, "ticket_body", required=True, max_length=60_000,
            )
            current_body = str(ticket.get("body") or "").strip()
            if corrected_body == current_body:
                raise InputError(
                    "The corrected Ticket body is unchanged. Review the proposed "
                    "recovery before saving."
                )
            marker_pattern = re.compile(
                r"<!--\s*factory-(?:plan|intake|governance):.*?-->",
                re.DOTALL,
            )
            expected_markers = marker_pattern.findall(current_body)
            corrected_markers = marker_pattern.findall(corrected_body)
            if corrected_markers != expected_markers:
                raise InputError(
                    "The corrected Ticket must preserve its hidden Factory identity "
                    "and governance markers unchanged."
                )
            required_paths = list(recovery.get("required_paths") or [])
            missing_paths = sorted(set(required_paths) - set(declared_paths(corrected_body)))
            if missing_paths:
                raise InputError(
                    "The corrected Ticket must add these paths to File ownership: "
                    + ", ".join(missing_paths)
                )
            configured_url = self.session_config().get("github_repository")
            if not configured_url:
                raise InputError(
                    "Connect the Live GitHub repository before saving a Ticket correction."
                )
            if not self.repo_info().get("github_connected"):
                raise InputError(
                    "The managed checkout does not match the configured GitHub "
                    "repository. Reconnect it before saving a Ticket correction."
                )
            repository = parse_github_repository(configured_url)
            reason = self._string(
                payload, "reason", required=True, max_length=300,
            )
            if len(reason) < 12:
                raise InputError(
                    "Retry reason must explain why another attempt can succeed."
                )
            _, retry_commands = self.build_commands("retry", {
                **payload,
                "issue": issue,
                "mode": "live",
                "reason": reason,
            })
            correction_dir = (
                self.repo / ".factory" / "control-center" / "ticket-corrections"
            )
            correction_dir.mkdir(parents=True, exist_ok=True)
            correction_file = correction_dir / (
                f"ticket-{issue}-{uuid.uuid4().hex[:12]}.md"
            )
            correction_file.write_text(corrected_body.rstrip() + "\n")
            save_command = [
                "gh", "issue", "edit", str(issue),
                "--repo", repository.slug,
                "--body-file", str(correction_file),
            ]
            return f"Save correction and retry ticket #{issue}", [
                save_command,
                retry_commands[0],
            ]
        raise InputError("This ticket correction action is not available.")

    def _build_retry_command(
        self, action: str, payload: dict,
    ) -> tuple[str, list[list[str]]]:
        base = [str(self.factory)]
        mode = payload.get("mode", "rehearsal")
        mock = mode != "live"
        if action == "retry":
            issue = self._positive_int(payload, "issue", required=True)
            ticket = self._ticket_action_context(issue, mode)
            reset_qa = payload.get("reset_qa") is True
            budget_lines = self._positive_int(payload, "budget_lines")
            reason = self._string(
                payload, "reason", required=True, max_length=300,
            )
            if len(reason) < 12:
                raise InputError(
                    "Retry reason must explain why another attempt can succeed."
                )
            recovery = ticket_recovery(ticket, self.repo)
            if reset_qa and recovery.get("kind") != "qa_evidence":
                raise InputError(
                    "Protected QA regeneration is available only when the recorded "
                    "blocker is a QA evidence defect."
                )
            if reset_qa and budget_lines:
                raise InputError(
                    "QA regeneration cannot be combined with a ticket budget exception."
                )
            command = base + ["retry", str(issue), "--repo", str(self.repo)]
            if mock:
                command.append("--mock")
            project = self._positive_int(payload, "project_number") or self.session_config().get("project_number")
            if project and not mock:
                command += ["--project-number", str(project)]
            command += ["--reason", reason]
            if budget_lines:
                command += [
                    "--budget-lines", str(budget_lines),
                ]
            if reset_qa:
                command.append("--reset-qa")
            command.append("--yes")
            return f"Retry ticket #{issue}", [command]
        raise InputError("This retry action is not available.")

    def _build_operations_command(
        self, action: str, payload: dict,
    ) -> tuple[str, list[list[str]]]:
        base = [str(self.factory)]
        mode = payload.get("mode", "rehearsal")
        mock = mode != "live"
        if action == "release-claim":
            if mock:
                raise InputError("Rehearsal Tickets do not use remote claims.")
            issue = self._positive_int(payload, "issue", required=True)
            owner = self._string(payload, "owner_run_id", required=True, max_length=64)
            if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", owner):
                raise InputError("The recorded claim owner is invalid.")
            reason = self._string(payload, "reason", required=True, max_length=300)
            return f"Release abandoned claim for ticket #{issue}", [[
                str(self.factory), "release-claim", str(issue),
                "--repo", str(self.repo),
                "--owner-run-id", owner,
                "--reason", reason,
                "--yes",
            ]]
        if action == "evidence":
            plan = self._plan_id(payload)
            output = self.runtime / f"evidence-{plan}"
            return "Create evidence packet", [
                base + ["evidence", plan, "--repo", str(self.repo), "--output", str(output)],
            ]
        if action in {"monitor", "publish-monitor"}:
            command = base + ["monitor", "--repo", str(self.repo), "--json"]
            if action == "publish-monitor":
                if mock:
                    raise InputError("Monitor publication requires a connected Live GitHub repository.")
                command.append("--publish")
                return "Publish monitor findings", [command]
            return "Preview repository health", [command]
        if action == "recover-latest":
            command = [
                str(self.factory), "recover",
                "--repo", str(self.repo),
                "--yes",
            ]
            project = self.session_config().get("project_number")
            if project:
                command += ["--project-number", str(project)]
            return "Recover latest Factory state", [command]
        if action in {"reset-run", "reset-all"}:
            local_only = payload.get("local_only") is True
            if mode == "live" and not local_only:
                raise InputError("Live GitHub runs cannot be reset safely. Use a fresh workshop repository.")
            scenario = self._string(payload, "scenario") or "recipe-rebrand"
            if scenario not in SCENARIOS:
                raise InputError("Unknown rehearsal scenario.")
            command = [str(self.factory), "reset", "--repo", str(self.repo), "--scenario", scenario]
            if local_only:
                command.append("--local-state-only")
            if action == "reset-all":
                if self._string(payload, "confirm") != "START OVER":
                    raise InputError("Type START OVER to clear the workshop run.")
                command.append("--start-over")
                title = "Clear local Live Run state" if mode == "live" else "Start the workshop over"
                return title, [command]
            title = "Reset local Live Run state" if mode == "live" else "Reset ticket execution"
            return title, [command]
        raise InputError("This operations action is not available.")

    def start(self, action: str, payload: dict) -> dict:
        title, commands = self.build_commands(action, payload)
        activation = self._pending_activation
        self._pending_activation = None
        operation_repo = self.repo
        companion = False
        with self.lock:
            process_running = bool(self.process and self.process.poll() is None)
            operation_running = self.operation.get("status") in {"running", "stopping"}
            companion = (
                action in COMPANION_ACTIONS
                and self.operation.get("action") in {"run", "run-once", "listen"}
                and self.operation.get("status") == "running"
                and process_running
            )
            if (operation_running or process_running) and not companion:
                raise InputError("Another factory operation is already running.")
            if not companion:
                operation_id = uuid.uuid4().hex[:12]
                log = self.control_repo / ".factory" / "logs" / f"control-center-{operation_id}.log"
                self.operation = {
                    "id": operation_id,
                    "action": action,
                    "title": title,
                    "status": "running",
                    "started_at": utc_now(),
                    "finished_at": "",
                    "exit_code": None,
                    "command": " && ".join(shlex.join(command) for command in commands),
                    "log": str(log),
                    "error": "",
                }
                if activation is not None:
                    self.operation["target_repo"] = str(activation)
                self._save_operation()
        if companion:
            return self._run_companion(action, title, commands, operation_repo)
        worker = threading.Thread(
            target=self._run,
            args=(commands, log, operation_repo, activation),
            daemon=True,
        )
        with self.lock:
            self.worker = worker
        worker.start()
        return self.operation_snapshot()

    def _run_companion(
        self,
        action: str,
        title: str,
        commands: list[list[str]],
        operation_repo: Path,
    ) -> dict:
        companion_id = uuid.uuid4().hex[:12]
        log = (
            self.control_repo / ".factory" / "logs"
            / f"control-center-{companion_id}-{action}.log"
        )
        exit_code = 0
        output = ""
        with self.companion_lock:
            with log.open("w") as stream:
                for command in commands:
                    stream.write("$ " + shlex.join(command) + "\n\n")
                    result = subprocess.run(
                        command,
                        cwd=operation_repo,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        env={**os.environ, "PYTHONUNBUFFERED": "1"},
                    )
                    output += result.stdout
                    stream.write(result.stdout)
                    stream.flush()
                    exit_code = result.returncode
                    if exit_code:
                        break
        record = {
            "id": companion_id,
            "action": action,
            "title": title,
            "status": "succeeded" if exit_code == 0 else "failed",
            "finished_at": utc_now(),
            "exit_code": exit_code,
            "log": str(log),
        }
        with self.lock:
            self.operation.setdefault("companion_actions", []).append(record)
            self._save_operation()
        if exit_code:
            detail = output.strip()[-3000:] or f"{title} exited with code {exit_code}."
            raise InputError(detail)
        snapshot = self.operation_snapshot()
        snapshot["companion"] = record
        return snapshot

    def _run(
        self,
        commands: list[list[str]],
        log: Path,
        operation_repo: Path,
        activation: Path | None,
    ):
        exit_code = 0
        failure = ""
        try:
            with log.open("w") as stream:
                for command in commands:
                    stream.write("$ " + shlex.join(command) + "\n\n")
                    stream.flush()
                    with self.lock:
                        self.process = subprocess.Popen(
                            command,
                            cwd=operation_repo,
                            text=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            start_new_session=True,
                            env={**os.environ, "PYTHONUNBUFFERED": "1"},
                        )
                        process = self.process
                        should_stop = self.operation.get("status") == "stopping"
                    if should_stop:
                        os.killpg(process.pid, signal.SIGTERM)
                    assert process.stdout is not None
                    for line in process.stdout:
                        stream.write(line)
                        stream.flush()
                    process.stdout.close()
                    exit_code = process.wait()
                    if exit_code:
                        break
        except (OSError, subprocess.SubprocessError) as exc:
            exit_code = 127
            failure = f"Could not start the factory command: {exc}"
        finally:
            with self.lock:
                status = "stopped" if self.operation.get("status") == "stopping" else ("succeeded" if exit_code == 0 else "failed")
                if status == "succeeded" and activation is not None:
                    try:
                        self._activate_repo(activation)
                    except InputError as exc:
                        status = "failed"
                        exit_code = 1
                        failure = str(exc)
                self.operation.update(status=status, finished_at=utc_now(), exit_code=exit_code)
                if failure:
                    self.operation["error"] = failure
                    self.operation["failure"] = {
                        "cause": failure,
                        "recovery": (
                            "Check that the displayed command and required executable are "
                            "available, then repeat this action."
                        ),
                    }
                elif exit_code and status != "stopped":
                    guidance = self._operation_failure_guidance(
                        self.operation.get("action", ""),
                        exit_code,
                        tail_text(log),
                        self.operation.get("command", ""),
                    )
                    self.operation["failure"] = guidance
                    self.operation["error"] = f"{guidance['cause']} {guidance['recovery']}"
                self.process = None
                self.worker = None
                self._save_operation()

    def stop(self) -> dict:
        with self.lock:
            process = self.process
            if self.operation.get("status") != "running":
                raise InputError("No factory operation is running.")
            self.operation["status"] = "stopping"
            self._save_operation()
            if process and process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
        return self.operation_snapshot()

    def shutdown(self, timeout: float = 5.0):
        """Stop and join the active factory command before closing the server."""
        with self.lock:
            worker = self.worker
            process = self.process
            if self.operation.get("status") in {"running", "stopping"}:
                self.operation["status"] = "stopping"
                self._save_operation()
            if process and process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
        if worker and worker is not threading.current_thread():
            worker.join(timeout=timeout)
        with self.lock:
            process = self.process
        if process and process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            if worker and worker is not threading.current_thread():
                worker.join(timeout=1)

    def artifact(self, raw_path: str) -> str:
        path = PurePosixPath(raw_path)
        if path.is_absolute() or ".." in path.parts:
            raise InputError("Invalid artifact path.")
        normalized = path.as_posix()
        if normalized.startswith("./"):
            normalized = normalized[2:]
        allowed = (
            ".factory/logs/",
            ".factory/prompts/",
            ".factory/receipts/",
            ".factory/reviews/",
            ".factory/plans/",
            ".factory/control-center/",
            ".factory/evidence/",
        )
        if not normalized.startswith(allowed):
            raise InputError("Only factory evidence artifacts can be opened.")
        target = (self.repo / normalized).resolve()
        allowed_roots = [
            (self.repo / prefix.rstrip("/")).resolve()
            for prefix in allowed
        ]
        if not any(target.is_relative_to(root) for root in allowed_roots) or not target.is_file():
            raise InputError("Artifact not found.")
        data = target.read_bytes()
        if len(data) > MAX_ARTIFACT:
            data = data[-MAX_ARTIFACT:]
            return "… earlier content omitted …\n" + data.decode("utf-8", errors="replace")
        return data.decode("utf-8", errors="replace")

    def ticket_tests(self, issue: int) -> dict:
        """Read only the protected test paths at the recorded QA revision."""
        state = read_json(self.repo / ".factory/state.json", {"tickets": []})
        ticket = next((item for item in state.get("tickets", []) if item.get("number") == issue), None)
        if not ticket:
            raise InputError(f"Ticket #{issue} was not found.")
        revision = ticket.get("qa_commit", "")
        if not isinstance(revision, str) or not re.fullmatch(r"[a-f0-9]{40,64}", revision):
            raise InputError("No committed QA test proposal is available yet.")
        files = []
        for raw in ticket.get("qa_tests", {}):
            path = PurePosixPath(raw)
            if path.is_absolute() or ".." in path.parts:
                raise InputError("Invalid protected test path.")
            result = subprocess.run(
                ["git", "show", f"{revision}:{path.as_posix()}"],
                cwd=self.repo, capture_output=True, check=False,
            )
            if result.returncode:
                raise InputError("The recorded QA revision is unavailable. Fetch the ticket branch and retry.")
            if len(result.stdout) > MAX_ARTIFACT:
                raise InputError("This test is too large for the viewer. Inspect its QA revision in Git.")
            blob = subprocess.run(
                ["git", "hash-object", "--stdin"], input=result.stdout,
                cwd=self.repo, capture_output=True, check=False,
            )
            if blob.returncode or blob.stdout.decode().strip() != ticket["qa_tests"][raw]:
                raise InputError("The test content does not match the protected QA evidence. Inspect the ticket before approval.")
            files.append({"path": raw, "content": result.stdout.decode("utf-8", errors="replace")})
        return {"revision": revision, "files": files}

    def ticket_diff(self, issue: int) -> str:
        state = read_json(self.repo / ".factory" / "state.json", {"tickets": []})
        ticket = next((item for item in state.get("tickets", []) if int(item.get("number", -1)) == issue), None)
        if not ticket:
            raise InputError(f"Ticket #{issue} was not found.")
        worktree = self.repo.parent / f"{self.repo.name}-wt-{issue}"
        base = ticket.get("base_sha")
        branch = ticket.get("branch")
        cwd = worktree if worktree.is_dir() else self.repo
        target = "HEAD" if worktree.is_dir() else branch
        if (
            not isinstance(base, str)
            or not re.fullmatch(r"[a-f0-9]{7,64}", base)
            or not isinstance(target, str)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,255}", target)
        ):
            return "A Git diff is not available yet."
        command = ["git", "diff", "--no-ext-diff", "--unified=3", f"{base}..{target}", "--"]
        result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
        if result.returncode:
            return result.stderr.strip() or "The ticket branch is no longer available."
        value = result.stdout
        return value[-MAX_ARTIFACT:] if len(value) > MAX_ARTIFACT else (value or "No committed changes yet.")


class Handler(BaseHTTPRequestHandler):
    server: "ControlCenterServer"

    def log_message(self, format, *args):
        return

    def _json(self, value, status=HTTPStatus.OK):
        data = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def _error(self, exc: Exception, status=HTTPStatus.BAD_REQUEST):
        self._json({"error": str(exc)}, status)

    def _payload(self) -> dict:
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise InputError("Invalid request length.") from exc
        if size > MAX_BODY:
            raise InputError("Request is too large.")
        try:
            value = json.loads(self.rfile.read(size) or b"{}")
        except json.JSONDecodeError as exc:
            raise InputError("Request must contain valid JSON.") from exc
        if not isinstance(value, dict):
            raise InputError("Request body must be an object.")
        return value

    def _trusted_request(self):
        try:
            self.server.center.access_policy.validate_request(self.headers)
        except ValueError as exc:
            raise InputError(str(exc)) from exc

    def do_GET(self):
        parsed = urlparse(self.path)
        try:
            # The load balancer reaches this endpoint directly.  It contains no
            # repository data and intentionally sits outside browser auth.
            if parsed.path == "/healthz":
                return self._json({"status": "healthy"})
            self._trusted_request()
            if parsed.path == "/api/snapshot":
                return self._json(self.server.center.snapshot())
            if parsed.path == "/api/prd":
                return self._json(self.server.center.prd())
            if parsed.path == "/api/canvas":
                return self._json(self.server.center.canvas())
            if parsed.path == "/api/artifact":
                raw = parse_qs(parsed.query).get("path", [""])[0]
                return self._json({"path": raw, "content": self.server.center.artifact(raw)})
            match = re.fullmatch(r"/api/tickets/(\d+)/tests", parsed.path)
            if match:
                return self._json(self.server.center.ticket_tests(int(match.group(1))))
            match = re.fullmatch(r"/api/tickets/(\d+)/diff", parsed.path)
            if match:
                issue = int(match.group(1))
                return self._json({"issue": issue, "content": self.server.center.ticket_diff(issue)})
            if parsed.path == "/api/events":
                return self._events()
            return self._asset(parsed.path)
        except InputError as exc:
            return self._error(exc)
        except Exception as exc:  # pragma: no cover - last-resort HTTP boundary
            return self._error(exc, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_PUT(self):
        try:
            self._trusted_request()
            if self.path == "/api/prd":
                return self._json(self.server.center.save_prd(self._payload().get("text")))
            if self.path == "/api/canvas":
                return self._json(self.server.center.save_canvas(self._payload().get("text")))
            return self._error(InputError("Unknown endpoint."), HTTPStatus.NOT_FOUND)
        except InputError as exc:
            return self._error(exc)

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            self._trusted_request()
            if parsed.path == "/api/stop":
                return self._json(self.server.center.stop(), HTTPStatus.ACCEPTED)
            match = re.fullmatch(r"/api/actions/([a-z-]+)", parsed.path)
            if match:
                return self._json(self.server.center.start(match.group(1), self._payload()), HTTPStatus.ACCEPTED)
            return self._error(InputError("Unknown endpoint."), HTTPStatus.NOT_FOUND)
        except InputError as exc:
            return self._error(exc)

    def _events(self):
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        previous = ""
        last_write = 0.0
        try:
            while True:
                data = json.dumps(self.server.center.stream_snapshot())
                current = time.monotonic()
                if data != previous:
                    self.wfile.write(f"data: {data}\n\n".encode())
                    previous = data
                    last_write = current
                    self.wfile.flush()
                elif current - last_write >= 15:
                    self.wfile.write(b": keepalive\n\n")
                    last_write = current
                    self.wfile.flush()
                time.sleep(1)
        except (BrokenPipeError, ConnectionResetError):
            return

    def _asset(self, path: str):
        name = "index.html" if path in {"", "/"} else path.lstrip("/")
        pure = PurePosixPath(name)
        if pure.is_absolute() or ".." in pure.parts:
            return self._error(InputError("Invalid asset path."), HTTPStatus.NOT_FOUND)
        target = (self.server.center.assets / pure).resolve()
        if not target.is_relative_to(self.server.center.assets) or not target.is_file():
            return self._error(InputError("Page not found."), HTTPStatus.NOT_FOUND)
        data = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mimetypes.guess_type(target.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(data)


class ControlCenterServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, center: ControlCenter):
        super().__init__(address, Handler)
        self.center = center

    def handle_error(self, request, client_address):
        if isinstance(sys.exc_info()[1], (BrokenPipeError, ConnectionResetError)):
            return
        super().handle_error(request, client_address)


def serve(repo: Path, host="127.0.0.1", port=5050, open_browser=True):
    center = ControlCenter(repo)
    try:
        center.access_policy.validate_bind_host(host)
    except ValueError as exc:
        raise InputError(str(exc)) from exc
    server = ControlCenterServer((host, port), center)
    url = f"http://{host}:{server.server_port}"
    print(f"Factory Control Center: {url}", flush=True)
    print("Press Ctrl+C to stop.", flush=True)
    if open_browser:
        threading.Timer(0.35, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        center.shutdown()
        server.server_close()
