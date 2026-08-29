"""Reproducible development-environment lifecycle for the local adapter.

The provider consumes one reviewed Project Contract. It never edits tracked
source configuration, never invents setup commands, and confines its own state,
logs, and preview ownership to ``.factory/environment``.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from project_contract import CONTRACT_PATH, ProjectContract


ACTIONS = {"provision", "prepare", "health", "preview", "reset", "destroy"}


class EnvironmentProviderError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


class LocalEnvironmentProvider:
    """Execute a complete local environment lifecycle through one interface."""

    provider = "local"

    def __init__(self, repo: Path, project: ProjectContract | None = None):
        self.repo = repo.resolve()
        self.project = project or ProjectContract.load(self.repo, require=True)
        self.runtime = self.repo / ".factory/environment"
        self.state_path = self.runtime / "state.json"
        self._preview_process: subprocess.Popen | None = None
        self._preview_stream = None

    def execute(
        self,
        action: str,
        *,
        approved: bool = False,
        run_gates: bool = False,
        command: str = "",
        port: int | None = None,
    ) -> dict:
        """Apply one lifecycle action and return its bounded evidence."""
        if action not in ACTIONS:
            raise EnvironmentProviderError(
                "unknown environment action; choose " + ", ".join(sorted(ACTIONS))
            )
        if action == "provision":
            return self._provision()
        if action == "prepare":
            self._require_status("prepare", {"provisioned", "prepared", "blocked", "healthy"}, "provision")
            return self._prepare(approved=approved)
        if action == "health":
            self._require_status("health", {"prepared", "blocked", "healthy"}, "prepare")
            return self._health(run_gates=run_gates)
        if action == "preview":
            self._require_status("preview", {"healthy", "running"}, "healthy")
            return self._preview(command=command, port=port)
        if action == "reset":
            return self._reset()
        return self._destroy()

    def snapshot(self) -> dict:
        try:
            value = json.loads(self.state_path.read_text())
        except (OSError, json.JSONDecodeError):
            return {
                "schema_version": 1,
                "provider": self.provider,
                "status": "not-provisioned",
                "project": self.project.name,
                "actions": sorted(ACTIONS),
            }
        return value if isinstance(value, dict) else {}

    def _contract_sha256(self) -> str:
        path = self.repo / CONTRACT_PATH
        if not path.is_file():
            raise EnvironmentProviderError(
                f"Project Contract not found at {path}; initialize the repository first"
            )
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _revision(self) -> str:
        revision = _git(self.repo, "rev-parse", "HEAD")
        if not revision:
            raise EnvironmentProviderError("repository has no readable Git revision")
        return revision

    def _write(self, value: dict) -> dict:
        self.runtime.mkdir(parents=True, exist_ok=True)
        value = {
            **value,
            "schema_version": 1,
            "provider": self.provider,
            "project": self.project.name,
            "updated_at": _now(),
            "actions": sorted(ACTIONS),
        }
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(value, indent=2) + "\n")
        os.replace(temporary, self.state_path)
        return value

    def _base(self) -> dict:
        existing = self.snapshot()
        return {
            **existing,
            "revision": self._revision(),
            "contract_sha256": self._contract_sha256(),
        }

    def _require_status(self, action: str, allowed: set[str], required: str) -> None:
        status = str(self.snapshot().get("status") or "not-provisioned")
        if status not in allowed:
            raise EnvironmentProviderError(
                f"cannot {action} while environment status is {status}; complete {required} first"
            )

    def _assert_binding(self) -> None:
        state = self.snapshot()
        bound_revision = state.get("revision")
        bound_contract = state.get("contract_sha256")
        current_revision = self._revision()
        current_contract = self._contract_sha256()
        if bound_revision != current_revision:
            raise EnvironmentProviderError(
                "repository revision drifted after provision; reset provider state and provision the intended revision"
            )
        if bound_contract != current_contract:
            raise EnvironmentProviderError(
                "Project Contract drifted after provision; review it, reset provider state, and provision again"
            )

    def _provision(self) -> dict:
        existing = self.snapshot()
        revision = self._revision()
        contract_sha256 = self._contract_sha256()
        bound = existing.get("status") not in {None, "not-provisioned", "reset", "destroyed"}
        drift = []
        if bound and existing.get("revision") not in {None, revision}:
            drift.append("repository revision")
        if bound and existing.get("contract_sha256") not in {None, contract_sha256}:
            drift.append("Project Contract")
        if drift:
            return self._write({
                **existing,
                "status": "blocked",
                "phase": "provision",
                "failure": f"{' and '.join(drift)} drifted after provision; reset provider state before rebinding",
                "observed_revision": revision,
                "observed_contract_sha256": contract_sha256,
            })
        return self._write({
            **existing,
            "revision": revision,
            "contract_sha256": contract_sha256,
            "status": "provisioned",
            "provisioned_at": _now(),
            "working_root": str(self.repo),
            "execution_environment": "local",
        })

    def _python(self) -> str:
        managed = self.repo / ".factory/venv/bin/python"
        return str(managed if managed.is_file() else Path(sys.executable))

    def _prepare(self, *, approved: bool) -> dict:
        if self.project.setup_commands and not approved:
            raise EnvironmentProviderError(
                "explicit human approval is required before Project Contract setup commands run"
            )
        self._assert_binding()
        base = self._base()
        log = self.runtime / "prepare.log"
        self.runtime.mkdir(parents=True, exist_ok=True)
        results = []
        with log.open("w") as stream:
            for configured in self.project.setup_commands:
                rendered = self.project.render_command(configured, python=self._python())
                result = subprocess.run(
                    rendered,
                    cwd=self.repo,
                    text=True,
                    shell=True,
                    executable="/bin/sh",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
                output = (result.stdout or "")[-4000:]
                stream.write(f"$ {rendered}\n{output}\n")
                results.append({
                    "command": configured,
                    "exit_code": result.returncode,
                    "output": output,
                })
                if result.returncode:
                    self._write({
                        **base,
                        "status": "blocked",
                        "phase": "prepare",
                        "setup_results": results,
                        "failure": f"Setup command exited with {result.returncode}: {configured}",
                    })
                    raise EnvironmentProviderError(
                        f"setup command exited with {result.returncode}: {configured}"
                    )
        return self._write({
            **base,
            "status": "prepared",
            "phase": "prepare",
            "prepared_at": _now(),
            "setup_results": results,
            "prepare_log": str(log.relative_to(self.repo)),
        })

    @staticmethod
    def _port_available(port: int) -> bool:
        with socket.socket() as handle:
            handle.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                handle.bind(("127.0.0.1", port))
            except OSError:
                return False
        return True

    def _health(self, *, run_gates: bool) -> dict:
        checks = []
        current = self.snapshot()

        def add(status: str, name: str, detail: str):
            checks.append({"status": status, "name": name, "detail": detail[-2000:]})

        try:
            revision = self._revision()
            bound_revision = current.get("revision")
            if bound_revision and revision != bound_revision:
                add("FAIL", "repository revision drift", f"provisioned {bound_revision}; observed {revision}")
            else:
                add("PASS", "repository revision", revision)
        except EnvironmentProviderError as exc:
            revision = ""
            add("FAIL", "repository revision", str(exc))
        try:
            contract_hash = self._contract_sha256()
            bound_contract = current.get("contract_sha256")
            if bound_contract and contract_hash != bound_contract:
                add("FAIL", "Project Contract drift", f"provisioned {bound_contract}; observed {contract_hash}")
            else:
                add("PASS", "Project Contract", contract_hash)
        except EnvironmentProviderError as exc:
            contract_hash = ""
            add("FAIL", "Project Contract", str(exc))
        for tool in self.project.required_tools:
            resolved = shutil.which(tool)
            add("PASS" if resolved else "FAIL", f"tool: {tool}", resolved or f"{tool} not found")
        for root in dict.fromkeys((*self.project.source_roots, *self.project.test_roots)):
            path = self.repo if root == "." else self.repo / root
            add("PASS" if path.exists() else "FAIL", f"root: {root}", str(path))
        for configured_port in self.project.ports:
            available = self._port_available(configured_port)
            add(
                "PASS" if available else "WARN",
                f"port: {configured_port}",
                "available" if available else "already in use; stop the owner or use the active preview",
            )
        if run_gates:
            for gate in self.project.gates:
                rendered = self.project.render_command(gate["cmd"], python=self._python())
                result = subprocess.run(
                    rendered,
                    cwd=self.repo,
                    text=True,
                    shell=True,
                    executable="/bin/sh",
                    capture_output=True,
                )
                status = "PASS" if result.returncode == 0 else (
                    "FAIL" if gate.get("required", True) else "WARN"
                )
                add(
                    status,
                    f"gate: {gate['name']}",
                    (result.stdout + result.stderr).strip() or f"exit {result.returncode}",
                )
        status = "blocked" if any(check["status"] == "FAIL" for check in checks) else "healthy"
        return self._write({
            **current,
            "status": status,
            "phase": "health",
            "observed_revision": revision,
            "observed_contract_sha256": contract_hash,
            "checked_at": _now(),
            "checks": checks,
            "run_gates": run_gates,
        })

    def _preview(self, *, command: str, port: int | None) -> dict:
        if not isinstance(command, str) or not command.strip():
            raise EnvironmentProviderError("preview requires an explicit reviewed command")
        current = self.snapshot()
        if current.get("preview", {}).get("pid"):
            self._stop_preview(current)
        self.runtime.mkdir(parents=True, exist_ok=True)
        log = self.runtime / "preview.log"
        stream = log.open("w")
        process = subprocess.Popen(
            command,
            cwd=self.repo,
            text=True,
            shell=True,
            executable="/bin/sh",
            stdout=stream,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        self._preview_process = process
        self._preview_stream = stream
        time.sleep(0.15)
        if process.poll() is not None:
            stream.close()
            raise EnvironmentProviderError(
                f"preview exited with code {process.returncode}; inspect {log}"
            )
        selected_port = port or (self.project.ports[0] if self.project.ports else None)
        urls = ([{
            "label": "Application preview",
            "url": f"http://127.0.0.1:{selected_port}",
        }] if selected_port else [])
        return self._write({
            **self._base(),
            "status": "running",
            "phase": "preview",
            "pid": process.pid,
            "preview": {
                "pid": process.pid,
                "command": command.strip(),
                "urls": urls,
                "log": str(log.relative_to(self.repo)),
                "started_at": _now(),
                "stop_action": "factory environment reset",
            },
        })

    def _stop_preview(self, state: dict) -> bool:
        preview = state.get("preview") if isinstance(state, dict) else {}
        pid = preview.get("pid") if isinstance(preview, dict) else None
        if not isinstance(pid, int) or pid < 2:
            return False
        try:
            os.killpg(pid, signal.SIGTERM)
        except ProcessLookupError:
            return False
        except PermissionError as exc:
            raise EnvironmentProviderError(f"cannot stop owned preview process {pid}: {exc}") from exc
        if self._preview_process is not None and self._preview_process.pid == pid:
            try:
                self._preview_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(pid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    pass
                self._preview_process.wait(timeout=2)
            finally:
                if self._preview_stream is not None:
                    self._preview_stream.close()
                self._preview_process = None
                self._preview_stream = None
            return True
        for _ in range(20):
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return True
            time.sleep(0.05)
        # A provider resumed in another process cannot reap the original child.
        # The owned process group received SIGTERM; do not signal an unrelated
        # reused PID after the bounded observation window.
        return True

    def _reset(self) -> dict:
        state = self.snapshot()
        stopped = self._stop_preview(state)
        return self._write({
            **self._base(),
            "status": "reset",
            "phase": "reset",
            "preview": {},
            "preview_stopped": stopped,
            "reset_scope": [".factory/environment preview process and provider state"],
        })

    def _destroy(self) -> dict:
        state = self.snapshot()
        stopped = self._stop_preview(state)
        shutil.rmtree(self.runtime, ignore_errors=True)
        return {
            "schema_version": 1,
            "provider": self.provider,
            "project": self.project.name,
            "status": "destroyed",
            "preview_stopped": stopped,
            "destroyed_at": _now(),
            "preserved": ["tracked source", "GitHub issues", "pull requests", "claims"],
        }
