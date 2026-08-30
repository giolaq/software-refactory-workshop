"""Optional multi-repository workspace coordination contract."""

from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path, PurePosixPath


WORKSPACE_PATH = Path("factory.workspace.toml")
ACCESS = {"read-only", "write"}


class WorkspaceContractError(ValueError):
    pass


def _revision(path: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=path, text=True,
        capture_output=True, check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


class WorkspaceContract:
    def __init__(self, root: Path, *, configured: bool, name: str, repositories: list[dict], services: list[dict] | None = None):
        self.root = root.resolve()
        self.configured = configured
        self.name = name
        self.repositories = repositories
        self.services = services or []
        self._validate()

    @classmethod
    def load(cls, repo: Path) -> "WorkspaceContract":
        repo = repo.resolve()
        path = repo / WORKSPACE_PATH
        if not path.is_file():
            return cls(repo, configured=False, name=repo.name, repositories=[{
                "name": repo.name,
                "path": ".",
                "revision": _revision(repo),
                "access": "write",
                "ticket_target": True,
                "dependencies": [],
                "verification": [],
            }])
        try:
            raw = tomllib.loads(path.read_text())
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise WorkspaceContractError(f"invalid {WORKSPACE_PATH}: {exc}") from exc
        if raw.get("version") != 1:
            raise WorkspaceContractError("workspace version must be 1")
        return cls(
            repo,
            configured=True,
            name=str(raw.get("name") or repo.name),
            repositories=raw.get("repositories") or [],
            services=raw.get("services") or [],
        )

    def _validate(self) -> None:
        if not self.repositories:
            raise WorkspaceContractError("workspace must declare at least one repository")
        names = []
        ticket_targets = 0
        for item in self.repositories:
            if not isinstance(item, dict):
                raise WorkspaceContractError("each repository must be a table")
            name = str(item.get("name") or "")
            path = PurePosixPath(str(item.get("path") or ""))
            if not name or name in names:
                raise WorkspaceContractError("repository names must be non-empty and unique")
            if path.is_absolute() or not str(path):
                raise WorkspaceContractError(f"repository {name} path must be relative")
            if item.get("access") not in ACCESS:
                raise WorkspaceContractError(f"repository {name} access must be read-only or write")
            if item.get("ticket_target"):
                ticket_targets += 1
                if item.get("access") != "write":
                    raise WorkspaceContractError("the Ticket repository must be writable")
            names.append(name)
        if ticket_targets != 1:
            raise WorkspaceContractError("workspace must name exactly one Ticket repository")
        known = set(names)
        for item in self.repositories:
            unknown = set(item.get("dependencies") or []) - known
            if unknown:
                raise WorkspaceContractError(
                    f"repository {item['name']} has unknown dependencies: {', '.join(sorted(unknown))}"
                )

    def ticket_repository(self) -> str:
        return next(item["name"] for item in self.repositories if item.get("ticket_target"))

    def check(self) -> dict:
        checks = []
        revisions = {}
        for item in self.repositories:
            path = (self.root / item["path"]).resolve()
            owner = str(item.get("owner") or "repository owner")[:120]
            if not path.is_dir():
                checks.append({
                    "status": "FAIL", "repository": item["name"],
                    "detail": f"missing repository at {path}",
                    "owner": owner,
                })
                continue
            actual = _revision(path)
            expected = str(item.get("revision") or "")
            status = "PASS" if actual and (not expected or actual == expected) else "FAIL"
            detail = actual if status == "PASS" else f"expected {expected or 'a readable revision'}, found {actual or 'none'}"
            checks.append({
                "status": status, "repository": item["name"],
                "detail": detail, "owner": owner,
            })
            if actual:
                revisions[item["name"]] = actual
        for service in self.services:
            if not isinstance(service, dict) or not service.get("required") or service.get("health_url"):
                continue
            checks.append({
                "status": "FAIL",
                "service": str(service.get("name") or "unnamed")[:120],
                "detail": "required service has no health interface",
                "owner": str(service.get("owner") or "service owner")[:120],
            })
        failed = [item for item in checks if item["status"] == "FAIL"]
        return {
            "schema_version": 1,
            "name": self.name,
            "configured": self.configured,
            "status": "blocked" if failed else "ready",
            "ticket_repository": self.ticket_repository(),
            "revisions": revisions,
            "checks": checks,
            "recovery_action": (
                f"{failed[0].get('owner', 'workspace owner')}: {failed[0]['detail']}"
                if failed else "No recovery required."
            ),
            "may_dispatch": not failed,
        }

    def require_ready(self) -> dict:
        """Fail before dispatch when the workspace contract is not satisfied."""
        report = self.check()
        if report["status"] == "blocked":
            first = next(item for item in report["checks"] if item["status"] == "FAIL")
            raise WorkspaceContractError(
                "Workspace blocked before dispatch; "
                f"{first.get('owner', 'workspace owner')} must resolve: {first['detail']}"
            )
        return report
