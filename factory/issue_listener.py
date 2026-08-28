"""Durable state and identity rules for opt-in repository issue intake."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_VERSION = 1
INTAKE_LABEL = "factory-intake"
INTAKE_MARKER = "<!-- factory-intake:v1;source=user -->"
FACTORY_MARKERS = {
    "plan": re.compile(r"<!--\s*factory-plan:", re.IGNORECASE),
    "monitor": re.compile(r"<!--\s*factory-monitor:", re.IGNORECASE),
    "intake": re.compile(r"<!--\s*factory-intake:", re.IGNORECASE),
    "governance": re.compile(r"<!--\s*factory-governance:", re.IGNORECASE),
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def factory_issue_kind(body: str) -> str:
    """Return the durable Factory marker carried by an issue body, if any."""
    for kind, marker in FACTORY_MARKERS.items():
        if marker.search(body or ""):
            return kind
    return ""


def is_intake_issue(body: str) -> bool:
    return factory_issue_kind(body) == "intake"


def render_intake_body(body: str, governance_marker: str) -> str:
    """Append immutable intake identity without replacing the user's request."""
    value = (body or "").rstrip()
    if not is_intake_issue(value):
        value += f"\n\n{INTAKE_MARKER}"
    if "factory-governance:" not in value:
        value += f"\n{governance_marker}"
    return value.strip() + "\n"


class RepositoryIssueListener:
    """Track a no-backlog baseline and acknowledge each later issue durably."""

    def __init__(self, repo: Path, repository: str):
        self.path = repo / ".factory" / "issue-listener.json"
        self.repository = repository
        self.state = self._load()

    def _load(self) -> dict:
        try:
            value = json.loads(self.path.read_text())
        except (OSError, json.JSONDecodeError):
            return {}
        if (
            not isinstance(value, dict)
            or value.get("schema_version") != SCHEMA_VERSION
            or value.get("repository") != self.repository
            or not isinstance(value.get("seen"), list)
        ):
            return {}
        return value

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.state, indent=2, sort_keys=True) + "\n")
        os.replace(temporary, self.path)

    def begin(self, issues: list[dict]) -> bool:
        """Start or resume listening; return True when a new baseline was made."""
        created = not self.state
        if created:
            self.state = {
                "schema_version": SCHEMA_VERSION,
                "repository": self.repository,
                "started_at": now(),
                "baseline_count": len(issues),
                "seen": sorted({
                    int(issue["number"])
                    for issue in issues
                    if issue.get("number") is not None
                }),
                "admitted": [],
                "admitted_count": 0,
                "ignored": [],
                "ignored_count": 0,
                "errors": [],
            }
        self.state.update({
            "enabled": True,
            "status": "listening",
            "resumed_at": now(),
            "last_error": "",
        })
        self._save()
        return created

    def candidates(self, issues: list[dict]) -> list[dict]:
        seen = {int(number) for number in self.state.get("seen", [])}
        self.state["last_polled_at"] = now()
        self._save()
        return sorted(
            (
                issue for issue in issues
                if issue.get("number") is not None
                and int(issue["number"]) not in seen
            ),
            key=lambda issue: int(issue["number"]),
        )

    def acknowledge(
        self,
        number: int,
        *,
        outcome: str,
        detail: str,
    ) -> None:
        number = int(number)
        seen = {int(item) for item in self.state.get("seen", [])}
        seen.add(number)
        self.state["seen"] = sorted(seen)
        record = {"number": number, "at": now(), "detail": detail}
        bucket = "admitted" if outcome == "admitted" else "ignored"
        already_recorded = any(
            int(item.get("number", -1)) == number
            for item in self.state.get(bucket, [])
        )
        values = [
            item for item in self.state.get(bucket, [])
            if int(item.get("number", -1)) != number
        ]
        values.append(record)
        self.state[bucket] = values[-100:]
        count_key = f"{bucket}_count"
        if not already_recorded:
            self.state[count_key] = int(
                self.state.get(count_key, len(values) - 1)
            ) + 1
        self.state["last_issue"] = record
        self.state["last_error"] = ""
        self._save()

    def record_refresh(self, number: int) -> None:
        self.state["last_issue"] = {
            "number": int(number),
            "at": now(),
            "detail": "Reloaded an edited repository issue for triage.",
        }
        self._save()

    def record_error(self, detail: str) -> None:
        record = {"at": now(), "detail": str(detail)[-1000:]}
        self.state["errors"] = [*self.state.get("errors", []), record][-25:]
        self.state["last_error"] = record["detail"]
        self.state["status"] = "degraded"
        self._save()

    def mark_healthy(self) -> None:
        self.state["status"] = "listening"
        self.state["last_error"] = ""
        self._save()

    def snapshot(self) -> dict:
        return {
            key: value
            for key, value in self.state.items()
            if key != "seen"
        } | {"seen_count": len(self.state.get("seen", []))}
