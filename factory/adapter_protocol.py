"""Versioned seam between the Factory control plane and Agent Adapters.

Legacy command adapters remain valid. Protocol-aware adapters receive a
versioned assignment and may emit bounded ``FACTORY_EVENT`` JSON lines. The
orchestrator synthesizes lifecycle events for legacy adapters so callers and
the Control Center consume one event interface.
"""

from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path


PROTOCOL_VERSION = 1
EVENT_PREFIX = "FACTORY_EVENT "
RESULT_PREFIX = "FACTORY_RESULT "
EVENT_TYPES = {
    "started",
    "status",
    "tool_activity",
    "artifact",
    "waiting",
    "warning",
    "blocked",
    "completed",
    "usage",
}
FEATURES = {
    "structured-planning",
    "native-read-only",
    "progress-events",
    "cancellation",
    "session-resume",
    "browser",
    "subagents",
    "container-execution",
    "hosted-execution",
    "usage-telemetry",
}
CAPABILITIES = {
    "read-only",
    "workspace-write",
    "progress-events",
    "structured-output",
    "browser",
}
SHA256 = re.compile(r"[a-f0-9]{64}")
MAX_MESSAGE = 1000
MAX_ARTIFACTS = 50
OUTCOMES = {"success", "blocked", "failed", "cancelled", "timed-out"}


class AdapterProtocolError(ValueError):
    """Raised when an adapter crosses the protocol seam with invalid data."""


def _text(value, label: str, *, maximum=300) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AdapterProtocolError(f"{label} must be a non-empty string")
    value = value.strip()
    if len(value) > maximum:
        raise AdapterProtocolError(f"{label} must be bounded to {maximum} characters")
    return value


def _string_list(value, label: str, *, allowed: set[str] | None = None) -> list[str]:
    if not isinstance(value, (list, tuple)) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise AdapterProtocolError(f"{label} must contain strings")
    normalized = list(dict.fromkeys(
        _text(item, f"{label} entry", maximum=1000) for item in value
    ))
    if len(normalized) > MAX_ARTIFACTS:
        raise AdapterProtocolError(f"{label} must be bounded to {MAX_ARTIFACTS} entries")
    if allowed is not None and not set(normalized) <= allowed:
        unknown = sorted(set(normalized) - allowed)
        raise AdapterProtocolError(f"{label} contains unsupported values: {', '.join(unknown)}")
    return normalized


def _usage(value, label: str) -> dict[str, int | float]:
    if not isinstance(value, dict) or len(value) > 20:
        raise AdapterProtocolError(f"{label} must map at most 20 metrics to numbers")
    normalized = {}
    for name, amount in value.items():
        metric = _text(name, f"{label} metric", maximum=80)
        if (
            not isinstance(amount, (int, float))
            or isinstance(amount, bool)
            or not math.isfinite(amount)
            or amount < 0
        ):
            raise AdapterProtocolError(
                f"{label} values must be finite non-negative numbers"
            )
        normalized[metric] = amount
    return dict(sorted(normalized.items()))


def build_assignment(
    *,
    run_id: str,
    role: str,
    ticket: int | None,
    attempt: int,
    repository: str,
    working_root: str,
    prompt_ref: str,
    profile: str,
    charter_sha256: str,
    policy_hashes: dict[str, str],
    requested_capabilities: list[str] | tuple[str, ...],
) -> dict:
    """Return the complete protocol assignment an adapter may rely on."""
    if ticket is not None and (not isinstance(ticket, int) or isinstance(ticket, bool) or ticket < 1):
        raise AdapterProtocolError("ticket must be a positive integer or null")
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt < 1:
        raise AdapterProtocolError("attempt must be a positive integer")
    if not isinstance(charter_sha256, str) or not SHA256.fullmatch(charter_sha256):
        raise AdapterProtocolError("charter_sha256 must be a lowercase SHA-256")
    if not isinstance(policy_hashes, dict) or len(policy_hashes) > 50:
        raise AdapterProtocolError(
            "policy_hashes must map at most 50 names to lowercase SHA-256 values"
        )
    normalized_hashes = {}
    for name, value in policy_hashes.items():
        normalized_name = _text(name, "policy hash name", maximum=80)
        if normalized_name in normalized_hashes:
            raise AdapterProtocolError("policy hash names must be unique")
        if not isinstance(value, str) or not SHA256.fullmatch(value):
            raise AdapterProtocolError(
                "policy_hashes must map names to lowercase SHA-256 values"
            )
        normalized_hashes[normalized_name] = value
    return {
        "schema_version": PROTOCOL_VERSION,
        "run_id": _text(run_id, "run_id"),
        "role": _text(role, "role", maximum=80),
        "ticket": ticket,
        "attempt": attempt,
        "repository": _text(repository, "repository", maximum=1000),
        "working_root": _text(working_root, "working_root", maximum=1000),
        "prompt_ref": _text(prompt_ref, "prompt_ref", maximum=1000),
        "profile": _text(profile, "profile", maximum=80),
        "charter_sha256": charter_sha256,
        "policy_hashes": dict(sorted(normalized_hashes.items())),
        "requested_capabilities": _string_list(
            requested_capabilities,
            "requested_capabilities",
            allowed=CAPABILITIES,
        ),
    }


def validate_event(value: dict) -> dict:
    """Validate adapter-supplied event content before control-plane enrichment."""
    if not isinstance(value, dict):
        raise AdapterProtocolError("adapter event must be an object")
    if value.get("schema_version") != PROTOCOL_VERSION:
        raise AdapterProtocolError(f"adapter event schema_version must be {PROTOCOL_VERSION}")
    event_type = value.get("type")
    if event_type not in EVENT_TYPES:
        raise AdapterProtocolError(f"adapter event type is unsupported: {event_type}")
    message = value.get("message", "")
    if message:
        _text(message, "event message", maximum=MAX_MESSAGE)
    elif event_type not in {"started", "completed", "usage"}:
        raise AdapterProtocolError("adapter event message is required")
    allowed = {"schema_version", "type", "message", "tool", "artifact", "artifacts", "usage"}
    unknown = set(value) - allowed
    if unknown:
        raise AdapterProtocolError(f"adapter event contains unsupported fields: {', '.join(sorted(unknown))}")
    normalized = {
        "schema_version": PROTOCOL_VERSION,
        "type": event_type,
    }
    if message:
        normalized["message"] = message.strip()
    if "tool" in value:
        normalized["tool"] = _text(value["tool"], "event tool", maximum=120)
    if "artifact" in value:
        normalized["artifact"] = _text(value["artifact"], "event artifact", maximum=1000)
    if "artifacts" in value:
        normalized["artifacts"] = _string_list(value["artifacts"], "event artifacts")
    if "usage" in value:
        normalized["usage"] = _usage(value["usage"], "event usage")
    return normalized


def validate_result(value: dict) -> dict:
    """Validate the single bounded final result from a protocol-aware Adapter."""
    if not isinstance(value, dict):
        raise AdapterProtocolError("adapter result must be an object")
    allowed = {
        "schema_version", "outcome", "output_revisions", "artifacts",
        "verification_claims", "unresolved_risks", "usage",
    }
    unknown = set(value) - allowed
    if unknown:
        raise AdapterProtocolError(
            "adapter result contains unsupported fields: " + ", ".join(sorted(unknown))
        )
    if value.get("schema_version") != PROTOCOL_VERSION:
        raise AdapterProtocolError(f"adapter result schema_version must be {PROTOCOL_VERSION}")
    outcome = value.get("outcome")
    if outcome not in OUTCOMES:
        raise AdapterProtocolError("adapter result outcome is invalid")
    revisions = value.get("output_revisions")
    if not isinstance(revisions, dict) or len(revisions) > 20 or not all(
        isinstance(name, str) and name.strip()
        and isinstance(revision, str)
        and re.fullmatch(r"[a-f0-9]{7,64}", revision)
        for name, revision in revisions.items()
    ):
        raise AdapterProtocolError("output_revisions must map bounded names to Git revisions")
    normalized = {
        "schema_version": PROTOCOL_VERSION,
        "outcome": outcome,
        "output_revisions": dict(sorted(revisions.items())),
        "artifacts": _string_list(value.get("artifacts", []), "result artifacts"),
        "verification_claims": _string_list(
            value.get("verification_claims", []), "verification_claims",
        ),
        "unresolved_risks": _string_list(
            value.get("unresolved_risks", []), "unresolved_risks",
        ),
    }
    if "usage" in value:
        normalized["usage"] = _usage(value["usage"], "result usage")
    return normalized


class AdapterEventJournal:
    """Deep module that normalizes adapter lifecycle into one append-only log."""

    def __init__(self, path: Path, *, run_id: str, role: str, ticket: int | None):
        self.path = path
        self.run_id = _text(run_id, "run_id")
        self.role = _text(role, "role", maximum=80)
        self.ticket = ticket
        self.started_event = False
        self.terminal_event: dict | None = None

    def _write(self, event: dict) -> dict:
        enriched = {
            **event,
            "run_id": self.run_id,
            "role": self.role,
            "ticket": self.ticket,
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as stream:
            stream.write(json.dumps(enriched, sort_keys=True) + "\n")
        return enriched

    def started(self, *, adapter: str) -> dict:
        if self.started_event:
            raise AdapterProtocolError("adapter lifecycle already started")
        self.started_event = True
        return self._write({
            "schema_version": PROTOCOL_VERSION,
            "type": "started",
            "message": f"{_text(adapter, 'adapter', maximum=80)} adapter started",
        })

    def observe(self, line: str) -> dict | None:
        if not isinstance(line, str) or not line.startswith(EVENT_PREFIX):
            return None
        try:
            supplied = json.loads(line[len(EVENT_PREFIX):].strip())
        except json.JSONDecodeError as exc:
            raise AdapterProtocolError(f"adapter event is invalid JSON: {exc}") from exc
        if not self.started_event:
            raise AdapterProtocolError("adapter event arrived before started")
        if self.terminal_event is not None:
            raise AdapterProtocolError("adapter event arrived after a terminal transition")
        event = self._write(validate_event(supplied))
        if event["type"] in {"completed", "blocked"}:
            self.terminal_event = event
        return event

    def finished(self, *, exit_code: int, artifacts: list[str] | None = None) -> dict:
        if not isinstance(exit_code, int):
            raise AdapterProtocolError("exit_code must be an integer")
        if self.terminal_event is not None:
            expected = "completed" if exit_code == 0 else "blocked"
            if self.terminal_event.get("type") != expected:
                raise AdapterProtocolError(
                    "adapter terminal event does not match the process outcome"
                )
            return self.terminal_event
        event_type = "completed" if exit_code == 0 else "blocked"
        message = "Adapter completed" if exit_code == 0 else f"Adapter exited with code {exit_code}"
        event = {
            "schema_version": PROTOCOL_VERSION,
            "type": event_type,
            "message": message,
        }
        if artifacts:
            event["artifacts"] = _string_list(artifacts, "artifacts")
        self.terminal_event = self._write(event)
        return self.terminal_event


def conformance_report(name: str, command_template: str, capability: dict) -> dict:
    """Check the static interface every configured command adapter must satisfy."""
    errors = []
    try:
        adapter = _text(name, "adapter name", maximum=80)
    except AdapterProtocolError as exc:
        adapter = str(name)
        errors.append(str(exc))
    if not isinstance(command_template, str) or "{prompt}" not in command_template:
        errors.append("command template must include {prompt}")
    version = capability.get("protocol_version", PROTOCOL_VERSION) if isinstance(capability, dict) else None
    if version != PROTOCOL_VERSION:
        errors.append(f"protocol_version must be {PROTOCOL_VERSION}")
    raw_features = capability.get("features", []) if isinstance(capability, dict) else []
    try:
        features = _string_list(raw_features, "features", allowed=FEATURES)
    except AdapterProtocolError as exc:
        features = []
        errors.append(str(exc))
    protocol_mode = "{assignment}" in command_template if isinstance(command_template, str) else False
    assignment_features = {
        "progress-events", "cancellation", "session-resume", "usage-telemetry",
    }
    if set(features) & assignment_features and not protocol_mode:
        errors.append("protocol features require the command template to include {assignment}")
    return {
        "schema_version": PROTOCOL_VERSION,
        "adapter": adapter,
        "compatible": not errors,
        "mode": "protocol-v1" if protocol_mode else "legacy-command",
        "features": features,
        "errors": errors,
    }
