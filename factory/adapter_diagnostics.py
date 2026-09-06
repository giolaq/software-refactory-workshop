"""Bounded, credential-redacted adapter diagnostics for operator recovery."""
import re

from sensitive_data import redact_credentials


def agent_failure_detail(output: str, limit: int = 2000, *, fallback: bool = True) -> str:
    """Prefer terminal errors; callers can exclude arbitrary output entirely."""
    redacted = redact_credentials(output.strip())
    errors = []
    for line in redacted.splitlines():
        line = line.strip()
        if re.match(r"(?i)^(?:error|fatal(?: error)?):", line) and line not in errors:
            errors.append(line)
    if errors:
        return "\n".join(errors[-5:])[:limit]
    return redacted[-limit:] if fallback else ""
