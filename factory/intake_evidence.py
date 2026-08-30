"""Evidence-backed intake proposals for raw product feedback.

The evaluator does not execute commands and cannot dispatch implementation. It
turns bounded, operator-reviewed evidence into one proposed classification for
a named person to accept or correct.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


CLASSIFICATIONS = {
    "READY_TO_IMPLEMENT", "READY_TO_PLAN", "NEEDS_INFORMATION", "WAIT",
}
REPRODUCTION_FAILURES = {"product_failure", "acceptance_failure"}


class IntakeError(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _bounded(value, limit: int = 2000):
    if isinstance(value, str):
        return value[:limit]
    if isinstance(value, list):
        return [_bounded(item, limit) for item in value[:50]]
    if isinstance(value, dict):
        return {
            str(key)[:100]: _bounded(item, limit)
            for key, item in list(value.items())[:50]
            if str(key).lower() not in {
                "token", "access_token", "password", "secret", "authorization",
                "raw_prompt", "hidden_reasoning", "environment_values",
            }
        }
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)[:limit]


class IntakeEvaluator:
    """Classify feedback and retain sanitized evaluation cases."""

    def __init__(self, repo: Path):
        self.repo = repo.resolve()
        self.case_path = self.repo / ".factory/intake/cases.jsonl"

    def _append(self, record: dict) -> None:
        self.case_path.parent.mkdir(parents=True, exist_ok=True)
        with self.case_path.open("a") as stream:
            stream.write(json.dumps(_bounded(record), sort_keys=True) + "\n")

    def evaluate(self, raw_request: dict) -> dict:
        if not isinstance(raw_request, dict):
            raise IntakeError("intake request must be an object")
        request = _bounded(raw_request)
        kind = str(request.get("kind") or "unknown").lower()
        title = str(request.get("title") or "").strip()
        description = str(request.get("description") or "").strip()
        if not title or not description:
            missing = [name for name, value in (
                ("title", title), ("description", description),
            ) if not value]
        else:
            missing = []

        reproduction = request.get("reproduction")
        if reproduction is not None and not isinstance(reproduction, dict):
            raise IntakeError("reproduction must be an object")
        if isinstance(reproduction, dict) and reproduction.get("command") and not reproduction.get("reviewed"):
            raise IntakeError(
                "reproduction commands must be reviewed by an operator; attached code is never executed by intake"
            )

        classification = "READY_TO_PLAN"
        rationale = "A feature or product change needs governed planning before Ticket publication."
        if kind in {"bug", "defect", "incident"}:
            required = (
                "affected_revision", "latest_revision", "environment",
                "reproduction", "acceptance_criteria", "file_ownership",
            )
            missing.extend(name for name in required if not request.get(name))
            external = request.get("required_external_information") or []
            if external:
                classification = "NEEDS_INFORMATION"
                rationale = "External data or a human decision is required before reproduction can be trusted."
            elif missing:
                classification = "NEEDS_INFORMATION"
                rationale = "The bug lacks the revision, environment, reproduction, or ownership evidence required for admission."
            elif (
                reproduction.get("exit_code") in (None, 0)
                or reproduction.get("failure_kind") not in REPRODUCTION_FAILURES
                or not str(reproduction.get("bounded_output") or "").strip()
            ):
                classification = "WAIT"
                rationale = "The supplied result is not a causal product reproduction; collection, environment, and unrelated failures do not count."
            else:
                classification = "READY_TO_IMPLEMENT"
                rationale = "A reviewed focused reproduction fails for a product reason on named revisions with bounded acceptance evidence."
        elif kind not in {"feature", "enhancement", "product", "request"}:
            classification = "NEEDS_INFORMATION"
            rationale = "A person must identify whether this is a product change, defect, or external dependency."
            if "kind" not in missing:
                missing.append("kind")

        canonical = json.dumps(request, sort_keys=True, separators=(",", ":"))
        case_id = hashlib.sha256((canonical + _now()).encode()).hexdigest()[:16]
        proposal = {
            "schema_version": 1,
            "case_id": case_id,
            "created_at": _now(),
            "classification": classification,
            "original_classification": classification,
            "rationale": rationale,
            "missing": sorted(set(missing)),
            "duplicate_candidates": request.get("duplicate_candidates", []),
            "required_external_information": request.get("required_external_information", []),
            "source_ref": request.get("source_ref", ""),
            "request": request,
            "human_review_required": True,
            "decision_authority": "human",
            "may_dispatch": False,
            "status": "proposed",
        }
        self._append(proposal)
        return proposal

    def correct(self, case_id: str, classification: str, reason: str) -> dict:
        if classification not in CLASSIFICATIONS:
            raise IntakeError("unknown intake classification")
        if not str(reason).strip():
            raise IntakeError("a human correction requires a reason")
        original = None
        try:
            lines = self.case_path.read_text().splitlines()
        except OSError:
            lines = []
        for line in lines:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("case_id") == case_id and record.get("status") == "proposed":
                original = record
                break
        if original is None:
            raise IntakeError("intake case not found")
        correction = {
            "schema_version": 1,
            "case_id": case_id,
            "created_at": _now(),
            "status": "human-correction",
            "original_classification": original["classification"],
            "classification": classification,
            "reason": str(reason)[:2000],
            "decision_authority": "human",
            "may_dispatch": False,
        }
        self._append(correction)
        return correction

    def latest(self, source_ref: str) -> dict | None:
        try:
            lines = self.case_path.read_text().splitlines()
        except OSError:
            return None
        for line in reversed(lines):
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (
                record.get("status") == "proposed"
                and record.get("source_ref") == source_ref
            ):
                return record
        return None


def request_from_github_issue(issue: dict, *, latest_revision: str) -> dict:
    """Extract bounded evidence fields without executing text or attachments."""
    body = str(issue.get("body") or "")
    labels = {str(label).lower() for label in issue.get("labels", [])}
    kind = "bug" if labels & {"bug", "defect", "incident"} else "feature"

    def section(name: str) -> str:
        match = re.search(
            rf"(?ims)^##[ \t]+{re.escape(name)}[ \t]*\n(.*?)(?=^##[ \t]+|\Z)",
            body,
        )
        return (match.group(1).strip() if match else "")[:2000]

    acceptance = [
        line.lstrip("-* ").strip()
        for line in section("Acceptance criteria").splitlines()
        if line.strip().startswith(("-", "*"))
    ]
    ownership = [
        line.lstrip("-* `").rstrip("` ").strip()
        for line in section("File ownership").splitlines()
        if line.strip().startswith(("-", "*"))
    ]
    reproduction_command = section("Reproduction command").strip("` \n")
    reproduction_output = section("Reproduction result")
    affected_revision = section("Affected revision").strip("` \n")
    environment = section("Environment")
    return {
        "source_ref": str(issue.get("url") or f"github-issue:{issue.get('number', '')}"),
        "kind": kind,
        "title": str(issue.get("title") or ""),
        "description": section("Spec") or body[:2000],
        "affected_revision": affected_revision,
        "latest_revision": latest_revision,
        "environment": environment,
        "reproduction": ({
            "command": reproduction_command,
            "exit_code": 1 if reproduction_output else None,
            "failure_kind": "product_failure" if reproduction_output else "",
            "bounded_output": reproduction_output,
            "reviewed": bool(reproduction_command and reproduction_output),
        } if kind == "bug" else None),
        "acceptance_criteria": acceptance,
        "file_ownership": ownership,
        "duplicate_candidates": [],
    }
