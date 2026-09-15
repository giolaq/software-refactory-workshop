"""Revision-bound approval inbox; only the runner changes delivery state."""

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path


def approval_fingerprint(ticket: dict) -> str:
    reviewed = {key: ticket.get(key) for key in (
        "number", "body", "spec_sha256", "qa_commit", "qa_tests", "qa_evidence",
    )}
    return hashlib.sha256(json.dumps(reviewed, sort_keys=True).encode()).hexdigest()


def pending_approval(repo: Path, ticket: dict) -> dict | None:
    if ticket.get("status") != "QA Review":
        return None
    try:
        value = json.loads((repo / ".factory/qa-approvals" / str(ticket["number"])).read_text())
    except (OSError, ValueError):
        return None
    if (isinstance(value, dict) and value.get("schema_version") == 1
            and value.get("fingerprint") == approval_fingerprint(ticket)):
        return value
    return None


def queue_approval(repo: Path, ticket: dict) -> None:
    marker = repo / ".factory/qa-approvals" / str(ticket["number"])
    marker.parent.mkdir(parents=True, exist_ok=True)
    temporary = marker.with_name(f".{marker.name}-{uuid.uuid4().hex}.tmp")
    receipt = {
        "schema_version": 1, "ticket": ticket["number"],
        "qa_commit": ticket["qa_commit"], "fingerprint": approval_fingerprint(ticket),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        temporary.write_text(json.dumps(receipt, indent=2) + "\n")
        os.replace(temporary, marker)
    finally:
        temporary.unlink(missing_ok=True)
