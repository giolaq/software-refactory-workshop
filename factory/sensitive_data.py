"""Shared credential detection and redaction for release and evidence paths."""

from __future__ import annotations

import re


CREDENTIAL_PATTERNS = (
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bBearer[ \t]+[A-Za-z0-9._~+/=-]{20,}", re.IGNORECASE),
)
SENSITIVE_ASSIGNMENT_PATTERN = re.compile(
    r"\b(?:"
    r"OPENAI_API_KEY|ANTHROPIC_API_KEY|GITHUB_TOKEN|GH_TOKEN|"
    r"AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|AWS_SESSION_TOKEN|AWS_SECURITY_TOKEN|"
    r"AZURE_[A-Z0-9_]*(?:API_KEY|ACCESS_KEY|PRIVATE_KEY|PASSWORD|TOKEN|SECRET)"
    r")[ \t]*[:=][ \t]*[\"']?(?P<value>[^ \t\r\n\"']{8,})"
)
SAFE_ASSIGNMENT_PREFIXES = ("$", "?", "<", "arn:aws:secretsmanager:")
SAFE_ASSIGNMENT_VALUES = {
    "change-me",
    "changeme",
    "example-value",
    "placeholder",
    "replace-me",
}


def _is_exposed_assignment(match: re.Match[str]) -> bool:
    value = match.group("value").casefold()
    if value.startswith(SAFE_ASSIGNMENT_PREFIXES):
        return False
    return value not in SAFE_ASSIGNMENT_VALUES


def redact_credentials(value: str) -> str:
    result = value
    for pattern in CREDENTIAL_PATTERNS:
        result = pattern.sub("[REDACTED]", result)
    return SENSITIVE_ASSIGNMENT_PATTERN.sub(
        lambda match: "[REDACTED]" if _is_exposed_assignment(match) else match.group(0),
        result,
    )


def contains_credentials(value: str) -> bool:
    if any(pattern.search(value) for pattern in CREDENTIAL_PATTERNS):
        return True
    return any(
        _is_exposed_assignment(match)
        for match in SENSITIVE_ASSIGNMENT_PATTERN.finditer(value)
    )
