"""Shared readiness checks for the supported Pi CLI authentication modes."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from adapter_capabilities import role_environment

SETTINGS_PATH = Path.home() / ".pi" / "agent" / "settings.json"
PROVIDER_ENV_KEYS = (
    "PI_API_KEY",
    "GOOGLE_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GROQ_API_KEY",
    "MISTRAL_API_KEY",
    "OPENROUTER_API_KEY",
    "XAI_API_KEY",
    "ZAI_API_KEY",
)
PROVIDERS_BY_ENV_KEY = {
    "GOOGLE_API_KEY": "google",
    "ANTHROPIC_API_KEY": "anthropic",
    "OPENAI_API_KEY": "openai",
    "GROQ_API_KEY": "groq",
    "MISTRAL_API_KEY": "mistral",
    "OPENROUTER_API_KEY": "openrouter",
    "XAI_API_KEY": "xai",
    "ZAI_API_KEY": "zai",
}


def pi_default_provider(environment: dict[str, str] | None = None) -> str | None:
    """Resolve the provider Pi will use: saved default, then known API keys."""
    source = os.environ if environment is None else environment
    override = source.get("PI_PROVIDER", "").strip()
    if override:
        return override
    try:
        settings = json.loads(SETTINGS_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        settings = {}
    provider = settings.get("defaultProvider") or settings.get("default_provider")
    if isinstance(provider, str) and provider.strip():
        return provider.strip()
    for key in PROVIDER_ENV_KEYS:
        if source.get(key, "").strip():
            return PROVIDERS_BY_ENV_KEY.get(key, "custom")
    return None


def pi_auth_ready(binary: str, environment: dict[str, str] | None = None) -> tuple[bool, str]:
    """Check Pi credentials for the configured provider via `pi auth check`."""
    provider = pi_default_provider(environment)
    if not provider:
        return False, "no default provider configured; set defaultProvider in ~/.pi/agent/settings.json or PI_PROVIDER"
    try:
        result = subprocess.run(
            [binary, "auth", "check", "--provider", provider, "--json"],
            text=True, capture_output=True, timeout=30,
            env=role_environment("PI_API_KEY"),
        )
    except (OSError, subprocess.TimeoutExpired):
        return False, "could not run `pi auth check`"
    output = result.stdout + result.stderr
    try:
        report = json.loads(output)
    except json.JSONDecodeError:
        return False, "pi auth check returned an unreadable response"
    if report.get("status") == "ready":
        model = report.get("model") or pi_default_provider(environment)
        return True, f"{binary} (provider {model})"
    reason = report.get("reason") or "credentials not ready"
    return False, f"provider {provider} not ready: {reason}; run pi interactively once to configure credentials"


def pi_environment(*additional: str) -> dict[str, str]:
    """Build the constrained Pi environment, forwarding provider credentials."""
    keys = {key for key in PROVIDER_ENV_KEYS if os.environ.get(key, "").strip()}
    environment = role_environment(*keys, *additional)
    return environment
