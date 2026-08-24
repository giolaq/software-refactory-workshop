"""Shared readiness checks for supported Codex CLI authentication modes."""

from __future__ import annotations


def codex_auth_ready(returncode: int, output: str) -> bool:
    """Accept saved-login success or an explicit managed-credentials response."""
    if returncode == 0:
        return True
    normalized = output.lower()
    return "login is not required" in normalized and "managed credentials" in normalized
