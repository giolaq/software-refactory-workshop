"""Preflight diagnostics for a reliable Software (re)-Factory workshop."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from factory_contracts import profile as factory_profile
from factory_charter import FactoryCharter, FactoryCharterError
from codex_cli import (
    codex_auth_ready,
    codex_region_environment,
    codex_uses_managed_bedrock,
)
from cursor_cli import cursor_candidates, probe_cursor_cli
from github_repository import (
    GitHubRepositoryError,
    parse_github_repository,
    repository_from_remote,
)
from project_contract import CONTRACT_PATH, ProjectContract, ProjectContractError


@dataclass
class Check:
    level: str
    name: str
    detail: str


def command(args: list[str], cwd: Path, timeout: int = 15, env=None):
    try:
        return subprocess.run(
            args, cwd=cwd, text=True, capture_output=True, timeout=timeout, env=env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return type("CommandFailure", (), {"returncode": 127, "stdout": "", "stderr": str(exc)})()


def version_tuple(raw: str) -> tuple[int, ...]:
    digits = []
    for part in raw.strip().lstrip("v").split("."):
        number = "".join(character for character in part if character.isdigit())
        if not number:
            break
        digits.append(int(number))
    return tuple(digits)


def node_engine_requirement(
    repo: Path, source_roots: tuple[str, ...],
) -> tuple[tuple[int, ...], str, str] | None:
    """Return the strongest explicit Node lower bound in project manifests."""
    manifests = [repo / "package.json"]
    manifests.extend(
        repo / root / "package.json" for root in source_roots if root != "."
    )
    requirements = []
    for manifest in dict.fromkeys(manifests):
        if not manifest.is_file():
            continue
        try:
            value = json.loads(manifest.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        raw = (value.get("engines") or {}).get("node")
        if not isinstance(raw, str):
            continue
        match = re.search(r">=\s*v?(\d+(?:\.\d+){0,2})", raw)
        if not match:
            continue
        parsed = version_tuple(match.group(1))
        if parsed:
            requirements.append((parsed, match.group(1), manifest.relative_to(repo).as_posix()))
    return max(requirements, key=lambda item: item[0]) if requirements else None


def node_tool_check(repo: Path, source_roots: tuple[str, ...], executable: str | None) -> Check:
    requirement = node_engine_requirement(repo, source_roots)
    required_text = f" >= {requirement[1]}" if requirement else ""
    if not executable:
        return Check("FAIL", "tool: node", f"not found; install Node.js{required_text}")
    result = command([executable, "--version"], repo)
    actual_text = (result.stdout or result.stderr).strip()
    actual = version_tuple(actual_text)
    if result.returncode != 0 or not actual:
        return Check("FAIL", "tool: node", f"cannot read version from {executable}: {actual_text or 'no output'}")
    if requirement and actual < requirement[0]:
        return Check(
            "FAIL", "tool: node",
            f"{actual_text}; requires >= {requirement[1]} from {requirement[2]}. "
            "Install the required Node.js version, then retry automatic setup",
        )
    detail = f"{executable} ({actual_text})"
    if requirement:
        detail += f"; satisfies >= {requirement[1]} from {requirement[2]}"
    return Check("PASS", "tool: node", detail)


def port_check(port: int) -> Check:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
    except OSError:
        return Check("WARN", f"port {port}", "already in use; choose another workshop port")
    finally:
        sock.close()
    return Check("PASS", f"port {port}", "available")


def codex_candidates() -> list[str]:
    return list(dict.fromkeys(filter(None, [
        shutil.which("codex"),
        "/Applications/ChatGPT.app/Contents/Resources/codex",
    ])))


BASELINE_SUBJECT = "chore: establish factory workshop baseline"


REHEARSAL_ONLY_TESTS = (
    "demo-app/tests/test_device_mode.py",
    "demo-app/tests/test_rails.py",
    "demo-app/tests/test_tv_detail.py",
)


def baseline_check(repo: Path) -> Check:
    """Confirm factory-baseline holds the mobile workpiece, not a finished rehearsal.

    A baseline carrying rehearsal-era tests grades fresh tickets against a
    product they legitimately replaced, so every scenario stalls on gate
    failures the agent cannot fix.
    """
    tagged = command(["git", "rev-parse", "--verify", "--quiet", "refs/tags/factory-baseline^{commit}"], repo)
    revision = tagged.stdout.strip()
    if tagged.returncode != 0 or not revision:
        return Check("WARN", "factory baseline", "tag missing; run setup once")

    listing = command(["git", "ls-tree", "-r", "--name-only", revision, "--", "demo-app"], repo)
    if listing.returncode != 0:
        return Check("FAIL", "factory baseline", listing.stderr.strip() or "cannot read tagged tree")
    tracked = set(listing.stdout.split())
    stale = sorted(path for path in REHEARSAL_ONLY_TESTS if path in tracked)
    if not stale:
        return Check("PASS", "factory baseline", f"mobile workpiece at {revision[:7]}")

    recoverable = command(["git", "rev-list", "--max-count=1", f"--grep=^{BASELINE_SUBJECT}$", "HEAD"], repo)
    wanted = recoverable.stdout.strip()
    remedy = (
        "rerun setup_demo.sh to repoint it"
        if wanted and wanted != revision
        else "re-clone from origin; this checkout has no mobile baseline to restore"
    )
    return Check("FAIL", "factory baseline", f"{revision[:7]} still carries {', '.join(stale)}; {remedy}")


def required_agent_names(
    cfg: dict, profile_name: str, implementation_agent: str,
    qa_agent: str | None, supervisor_agent: str | None, planning_agent: str,
    review_agent: str | None = None,
) -> set[str | None]:
    roles = factory_profile(profile_name)["execution_roles"]
    required = {implementation_agent, planning_agent}
    if "qa" in roles:
        required.add(qa_agent or cfg.get("qa", {}).get("agent"))
    if "supervisor" in roles:
        required.add(supervisor_agent or cfg.get("supervisor", {}).get("agent"))
    if "code_review" in roles:
        required.add(review_agent or cfg.get("review", {}).get("agent"))
    return required


class DiagnosticSuite:
    """Collect workshop readiness checks behind one stable diagnostic interface.

    Each collector owns one operational boundary.  This keeps repository,
    GitHub, adapter, and quality-gate policy independent while preserving the
    ordered report consumed by the CLI and Control Center.
    """

    def __init__(
        self, repo: Path, cfg: dict, *, full: bool, implementation_agent: str,
        qa_agent: str | None, supervisor_agent: str | None,
        review_agent: str | None, planning_agent: str, profile_name: str,
        github_repository: str | None,
    ) -> None:
        self.repo = repo
        self.cfg = cfg
        self.full = full
        self.implementation_agent = implementation_agent
        self.qa_agent = qa_agent
        self.supervisor_agent = supervisor_agent
        self.review_agent = review_agent
        self.planning_agent = planning_agent
        self.profile_name = profile_name
        self.checks: list[Check] = []
        self.project, self.contract_error = self._load_project()
        self.configured_repository = self._configured_repository(github_repository)
        self.venv_python = repo / ".factory/venv/bin/python"

    def _load_project(self) -> tuple[ProjectContract, str]:
        try:
            return ProjectContract.load(self.repo), ""
        except ProjectContractError as exc:
            return ProjectContract.detect(self.repo), str(exc)

    @staticmethod
    def _configured_repository(github_repository: str | None):
        if not github_repository:
            return None
        try:
            return parse_github_repository(github_repository)
        except GitHubRepositoryError:
            return None

    def run(self) -> int:
        self._collect_project_contract()
        self._collect_git()
        self._collect_runtime()
        self._collect_github()
        self._collect_agents()
        self._collect_quality()
        return self._render()

    def _collect_project_contract(self) -> None:
        project = self.project
        missing_roots = [
            root for root in project.source_roots
            if root != "." and not (self.repo / root).exists()
        ]
        self.checks.append(Check(
            "FAIL" if missing_roots else "PASS", "workspace",
            ", ".join(missing_roots) if missing_roots else str(self.repo),
        ))
        contract_path = self.repo / CONTRACT_PATH
        contract_level = (
            "PASS" if contract_path.is_file() and not self.contract_error
            else "FAIL" if self.full else "WARN"
        )
        contract_detail = (
            str(contract_path) if contract_level == "PASS"
            else self.contract_error or "run `factory init` and review the generated contract"
        )
        self.checks.append(Check(contract_level, "Project Contract", contract_detail))
        try:
            charter = FactoryCharter.load(self.repo, require_approved=True)
            selected_profile = factory_profile(self.profile_name)
            governance = charter.governance(
                self.profile_name,
                explicit_autonomy=bool(selected_profile.get("requires_explicit_opt_in")),
            )
            charter_level = "PASS"
            charter_detail = (
                f"approved {governance['charter_sha256'][:12]} · "
                f"{governance['merge_authority']} merge · {governance['gate_level']} gates"
            )
        except (FactoryCharterError, ValueError) as exc:
            charter_level, charter_detail = "FAIL", str(exc)
        self.checks.append(Check(charter_level, "Factory Charter", charter_detail))

    def _collect_git(self) -> None:
        git = command(["git", "rev-parse", "--show-toplevel"], self.repo)
        self.checks.append(Check(
            "PASS" if git.returncode == 0 else "FAIL", "Git repository",
            git.stdout.strip() or git.stderr.strip(),
        ))
        if git.returncode != 0:
            return
        dirty = command(["git", "status", "--porcelain"], self.repo).stdout.strip()
        self.checks.append(Check("FAIL" if dirty else "PASS", "clean checkout", dirty or "no uncommitted files"))
        branch = command(["git", "branch", "--show-current"], self.repo).stdout.strip()
        self.checks.append(Check("PASS" if branch else "FAIL", "current branch", branch or "detached HEAD"))
        if self.full:
            origin = command(["git", "remote", "get-url", "origin"], self.repo)
            self.checks.append(Check("PASS" if origin.returncode == 0 else "FAIL", "origin remote", origin.stdout.strip() or "not configured"))
            origin_repository = repository_from_remote(origin.stdout.strip())
            repository_matches = bool(
                self.configured_repository and origin_repository
                and self.configured_repository.slug.lower() == origin_repository.slug.lower()
            )
            detail = (
                self.configured_repository.url if repository_matches
                else "save the attendee repository URL in Connect or with `factory configure --github-repository URL`"
            )
            self.checks.append(Check("PASS" if repository_matches else "FAIL", "GitHub repository target", detail))
        if self.project.reset_command and any("setup_demo.sh" in item for item in self.project.reset_command):
            self.checks.append(baseline_check(self.repo))

    def _collect_runtime(self) -> None:
        python_ok = sys.version_info >= (3, 11)
        self.checks.append(Check(
            "PASS" if python_ok else "FAIL", "Python",
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        ))
        self.checks.append(Check(
            "PASS", "execution Python",
            str(self.venv_python) if self.venv_python.is_file() else sys.executable,
        ))
        tools = self.project.required_tools if self.full else tuple(
            tool for tool in self.project.required_tools if tool == "node"
        )
        for tool in tools:
            found = sys.executable if tool in {"python", "python3"} else shutil.which(tool)
            if tool == "node":
                self.checks.append(node_tool_check(self.repo, self.project.source_roots, found))
            else:
                self.checks.append(Check("PASS" if found else "FAIL", f"tool: {tool}", found or "not found"))

    def _collect_github(self) -> None:
        if not self.full:
            return
        gh = shutil.which("gh")
        self.checks.append(Check("PASS" if gh else "FAIL", "GitHub CLI", gh or "install gh"))
        if not gh:
            return
        auth = command([gh, "auth", "status"], self.repo)
        auth_text = (auth.stdout + auth.stderr).strip()
        self.checks.append(Check("PASS" if auth.returncode == 0 else "FAIL", "GitHub authentication", "authenticated" if auth.returncode == 0 else auth_text))
        scope_ok = "project" in auth_text.lower()
        self.checks.append(Check("PASS" if scope_ok else "FAIL", "GitHub Projects scope", "project scope present" if scope_ok else "run gh auth refresh -s project"))
        target = [self.configured_repository.slug] if self.configured_repository else []
        view = command([gh, "repo", "view", *target, "--json", "nameWithOwner,defaultBranchRef"], self.repo)
        if view.returncode != 0:
            self.checks.append(Check("FAIL", "GitHub repository", view.stderr.strip() or "no connected repository"))
            return
        repo_details = json.loads(view.stdout)
        default = (repo_details.get("defaultBranchRef") or {}).get("name") or "main"
        current = command(["git", "branch", "--show-current"], self.repo).stdout.strip()
        self.checks.append(Check(
            "PASS" if self.project.default_branch == default else "FAIL",
            "Project Contract branch", f"contract `{self.project.default_branch}`; GitHub `{default}`",
        ))
        self.checks.append(Check("PASS" if current == default else "FAIL", "default branch", f"local `{current}`; GitHub `{default}`"))
        remote = command(["git", "ls-remote", "origin", f"refs/heads/{default}"], self.repo)
        remote_sha = remote.stdout.split()[0] if remote.returncode == 0 and remote.stdout.split() else ""
        local_sha = command(["git", "rev-parse", "HEAD"], self.repo).stdout.strip()
        self.checks.append(Check(
            "PASS" if remote_sha == local_sha else "FAIL", "branch synchronization",
            "local HEAD matches GitHub" if remote_sha == local_sha else f"local {local_sha[:8]} vs remote {remote_sha[:8] or 'unknown'}",
        ))
        owner = repo_details["nameWithOwner"].split("/", 1)[0]
        projects = command([gh, "project", "list", "--owner", owner, "--format", "json"], self.repo)
        self.checks.append(Check("PASS" if projects.returncode == 0 else "FAIL", "GitHub Project access", "accessible" if projects.returncode == 0 else projects.stderr.strip()))
        self._collect_reviewer_identity(gh)

    def _collect_reviewer_identity(self, gh: str) -> None:
        if "code_review" not in factory_profile(self.profile_name)["execution_roles"]:
            return
        reviewer_token = os.environ.get("FACTORY_REVIEW_GH_TOKEN", "").strip()
        if not reviewer_token:
            self.checks.append(Check(
                "WARN", "GitHub reviewer identity",
                "FACTORY_REVIEW_GH_TOKEN not set; self-reviews use a labelled Factory comment",
            ))
            return
        author = command([gh, "api", "user", "--jq", ".login"], self.repo)
        reviewer = command(
            [gh, "api", "user", "--jq", ".login"], self.repo,
            env={**os.environ, "GH_TOKEN": reviewer_token},
        )
        distinct = (
            author.returncode == 0 and reviewer.returncode == 0
            and author.stdout.strip() != reviewer.stdout.strip()
        )
        detail = (
            f"{reviewer.stdout.strip()} can submit formal reviews"
            if distinct else "token must belong to a different GitHub account"
        )
        self.checks.append(Check("PASS" if distinct else "WARN", "GitHub reviewer identity", detail))

    def _required_agents(self) -> set[str | None]:
        return required_agent_names(
            self.cfg, self.profile_name, self.implementation_agent,
            self.qa_agent, self.supervisor_agent, self.planning_agent,
            self.review_agent,
        )

    def _collect_agents(self) -> None:
        if not self.full:
            return
        required_agents = self._required_agents()
        probes = {
            "codex": self._probe_codex,
            "claude": self._probe_claude,
            "cursor": self._probe_cursor,
        }
        if "bedrock" in required_agents:
            probes["bedrock"] = self._probe_bedrock
        for name, probe in probes.items():
            available, detail = probe()
            required = name in required_agents
            self.checks.append(Check(
                "PASS" if available else "FAIL" if required else "WARN",
                f"{name} adapter", detail,
            ))
        for name in sorted(required_agents - {*probes, None}):
            registered = name in self.cfg.get("agents", {})
            detail = (
                "registered in factory/factory.toml; run the adapter command once to verify its own authentication"
                if registered else "not registered in factory/factory.toml [agents]"
            )
            self.checks.append(Check("PASS" if registered else "FAIL", f"{name} adapter", detail))
        self._collect_execution_boundaries(required_agents)

    def _probe_codex(self) -> tuple[bool, str]:
        detail = "not installed or not signed in; install Codex CLI if needed, then run `codex login`"
        for candidate in codex_candidates():
            status = command([candidate, "login", "status"], self.repo)
            help_result = command([candidate, "exec", "--help"], self.repo)
            auth_output = status.stdout + status.stderr
            if not codex_auth_ready(status.returncode, auth_output) or help_result.returncode != 0:
                continue
            if not codex_uses_managed_bedrock(auth_output):
                return True, candidate
            region = codex_region_environment().get("AWS_REGION", "")
            if region:
                return True, f"{candidate} (managed Bedrock; region {region})"
            detail = "managed Bedrock credentials require an AWS region; set AWS_REGION or configure a region in ~/.aws/config"
        return False, detail

    def _probe_claude(self) -> tuple[bool, str]:
        found = shutil.which("claude")
        if not found:
            return False, "not installed"
        status = command([found, "auth", "status", "--text"], self.repo)
        help_result = command([found, "--help"], self.repo)
        structured = "--json-schema" in help_result.stdout + help_result.stderr
        if status.returncode:
            return False, "not signed in; run claude auth login"
        if self.planning_agent == "claude" and not structured:
            return False, "update Claude Code; --json-schema is required for planning"
        return True, found

    def _probe_cursor(self) -> tuple[bool, str]:
        details = []
        candidates = cursor_candidates()
        for candidate in candidates:
            ready, detail = probe_cursor_cli(candidate, self.repo)
            if ready:
                return True, detail
            details.append(detail)
        if details:
            return False, details[-1]
        return False, "not installed; install Cursor CLI, then run `agent login`"

    @staticmethod
    def _probe_bedrock() -> tuple[bool, str]:
        region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
        model = os.environ.get("FACTORY_BEDROCK_MODEL_ID", "").strip()
        if not region:
            return False, "set AWS_REGION or AWS_DEFAULT_REGION"
        if not model:
            return False, "set FACTORY_BEDROCK_MODEL_ID"
        if importlib.util.find_spec("boto3") is None:
            return False, "install boto3"
        return True, f"{model} in {region}; credentials resolved by the AWS SDK at invocation"

    def _collect_execution_boundaries(self, required_agents: set[str | None]) -> None:
        for name in sorted(item for item in required_agents if item):
            capability = self.cfg.get("agent_capabilities", {}).get(name)
            if not capability:
                self.checks.append(Check(
                    "FAIL", f"{name} execution boundary",
                    "missing [agent_capabilities] declaration",
                ))
                continue
            read_only = "native read-only" if capability.supports_read_only else "mutation detection only"
            detail = (
                f"{capability.execution_environment}; {capability.filesystem_mode}; "
                f"roots {', '.join(capability.allowed_working_roots)}; "
                f"network {capability.network_expectation}; {read_only}"
            )
            self.checks.append(Check(
                "PASS" if capability.supports_read_only else "WARN",
                f"{name} execution boundary", detail,
            ))

    def _collect_quality(self) -> None:
        self.checks.extend(port_check(port) for port in (*self.project.ports, 5050))
        qa = self.cfg.get("qa", {})
        roots = qa.get("test_roots")
        patterns = qa.get("test_file_patterns", list(self.project.test_file_patterns))
        qa_valid = (
            qa.get("agent") in self.cfg.get("agents", {})
            and isinstance(qa.get("max_retries"), int)
            and qa.get("max_retries") >= 0
            and isinstance(roots, list) and bool(roots)
            and all(
                isinstance(root, str) and root
                and not PurePosixPath(root).is_absolute()
                and ".." not in PurePosixPath(root).parts
                for root in roots
            )
            and isinstance(patterns, list) and bool(patterns)
            and all(isinstance(pattern, str) and "{ticket}" in pattern for pattern in patterns)
        )
        self.checks.append(Check("PASS" if qa_valid else "FAIL", "QA configuration", "valid" if qa_valid else "invalid agent, retries, or test roots"))
        gates = self.cfg.get("gate", [])
        valid_gates = bool(gates) and all(gate.get("name") and gate.get("cmd") for gate in gates)
        self.checks.append(Check("PASS" if valid_gates else "FAIL", "verification gates", f"{len(gates)} configured" if valid_gates else "invalid or empty gate list"))
        if self.full and valid_gates:
            self._run_gates(gates)

    def _run_gates(self, gates: list[dict]) -> None:
        python = str(self.venv_python) if self.venv_python.is_file() else sys.executable
        for gate in gates:
            rendered = self.project.render_command(gate["cmd"], python=python)
            result = command(["/bin/sh", "-c", rendered], self.repo, timeout=300)
            detail = "passed" if result.returncode == 0 else (result.stdout + result.stderr)[-500:].strip()
            self.checks.append(Check("PASS" if result.returncode == 0 else "FAIL", f"gate: {gate['name']}", detail))

    def _render(self) -> int:
        width = max(len(check.name) for check in self.checks)
        for check in self.checks:
            print(f"[{check.level:<4}] {check.name:<{width}}  {check.detail}")
        counts = {
            level: sum(check.level == level for check in self.checks)
            for level in ("PASS", "WARN", "FAIL")
        }
        print(f"\nDoctor: {counts['PASS']} passed, {counts['WARN']} warnings, {counts['FAIL']} failures")
        return 1 if counts["FAIL"] else 0


def run_doctor(
    repo: Path, cfg: dict, *, full=False, implementation_agent="codex",
    qa_agent=None, supervisor_agent=None, review_agent=None,
    planning_agent="codex", profile_name="standard", github_repository=None,
) -> int:
    """Run the stable diagnostic interface used by both CLI and Control Center."""
    return DiagnosticSuite(
        repo, cfg, full=full, implementation_agent=implementation_agent,
        qa_agent=qa_agent, supervisor_agent=supervisor_agent,
        review_agent=review_agent, planning_agent=planning_agent,
        profile_name=profile_name, github_repository=github_repository,
    ).run()
