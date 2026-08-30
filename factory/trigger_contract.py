"""Authenticated, idempotent trigger proposals for governed intake."""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path


SOURCES = {"schedule", "webhook", "issue", "cli", "control-center"}
EXTERNAL_SOURCES = {"schedule", "webhook", "issue"}
EVENT_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,199}")
SENSITIVE_KEYS = {
    "authorization", "token", "access_token", "password", "secret",
    "signature", "cookie", "raw_prompt", "hidden_reasoning",
}
MAX_PAYLOAD_BYTES = 64_000


class TriggerError(ValueError):
    pass


def _bounded(value, *, depth: int = 0):
    if depth > 8:
        raise TriggerError("trigger payload must be bounded to eight nested levels")
    if isinstance(value, dict):
        if len(value) > 100:
            raise TriggerError("trigger payload must be bounded to 100 fields per object")
        normalized = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key or len(key) > 100:
                raise TriggerError("trigger payload keys must be bounded strings")
            folded = key.casefold().replace("-", "_")
            if folded in SENSITIVE_KEYS:
                raise TriggerError(f"trigger payload contains sensitive field: {key}")
            normalized[key] = _bounded(item, depth=depth + 1)
        return normalized
    if isinstance(value, list):
        if len(value) > 100:
            raise TriggerError("trigger payload must be bounded to 100 list items")
        return [_bounded(item, depth=depth + 1) for item in value]
    if isinstance(value, str):
        if len(value) > 4_000:
            raise TriggerError("trigger payload strings must be bounded to 4000 characters")
        return value
    if value is None or isinstance(value, (bool, int, float)):
        return value
    raise TriggerError("trigger payload values must be JSON-compatible")


class TriggerRegistry:
    def __init__(self, repo: Path):
        self.repo = repo.resolve()
        self.runtime = self.repo / ".factory/triggers"

    def propose(self, source: str, event_id: str, payload: dict, *, authenticated: bool) -> dict:
        if source not in SOURCES:
            raise TriggerError("unknown trigger source")
        if source in EXTERNAL_SOURCES and not authenticated:
            raise TriggerError(f"{source} triggers must be authenticated")
        if not EVENT_ID.fullmatch(str(event_id)):
            raise TriggerError("event id is invalid")
        if not isinstance(payload, dict):
            raise TriggerError("trigger payload must be an object")
        payload = _bounded(payload)
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        if len(canonical.encode()) > MAX_PAYLOAD_BYTES:
            raise TriggerError(f"trigger payload must be bounded to {MAX_PAYLOAD_BYTES} bytes")
        payload_hash = hashlib.sha256(canonical.encode()).hexdigest()
        trigger_id = hashlib.sha256(f"{source}:{event_id}".encode()).hexdigest()[:20]
        path = self.runtime / f"{trigger_id}.json"
        try:
            existing = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            existing = None
        if existing:
            if existing.get("payload_sha256") != payload_hash:
                raise TriggerError("the same event id was replayed with a different payload")
            return {**existing, "status": "duplicate"}
        value = {
            "schema_version": 1,
            "trigger_id": trigger_id,
            "source": source,
            "event_id": event_id,
            "payload_sha256": payload_hash,
            "received_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "authenticated": authenticated or source not in EXTERNAL_SOURCES,
            "status": "proposed",
            "may_dispatch": False,
            "next_interface": "evidence-backed-intake",
            "payload": payload,
        }
        self.runtime.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(
            f".{path.name}.{os.getpid()}.{secrets.token_hex(4)}.tmp"
        )
        temporary.write_text(json.dumps(value, indent=2) + "\n")
        try:
            os.link(temporary, path)
        except FileExistsError:
            temporary.unlink(missing_ok=True)
            return self.propose(source, event_id, payload, authenticated=authenticated)
        temporary.unlink(missing_ok=True)
        return value
