"""Shared readiness checks for supported Codex CLI authentication modes."""

from __future__ import annotations

import configparser
import os
from collections.abc import Mapping
from pathlib import Path

from adapter_capabilities import role_environment


def codex_uses_managed_bedrock(output: str) -> bool:
    """Identify the managed Amazon Bedrock wrapper response."""
    normalized = output.lower()
    return (
        "login is not required" in normalized
        and "bedrock" in normalized
        and "managed credentials" in normalized
    )


def codex_auth_ready(returncode: int, output: str) -> bool:
    """Accept saved-login success or an explicit managed-credentials response."""
    if returncode == 0:
        return True
    return codex_uses_managed_bedrock(output)


def codex_region_environment(
    environment: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Resolve Bedrock's region without forwarding AWS credentials."""
    source = os.environ if environment is None else environment
    region = source.get("AWS_REGION", "").strip()
    if not region:
        region = source.get("AWS_DEFAULT_REGION", "").strip()
    if not region:
        home = source.get("HOME", "").strip()
        configured_path = source.get("AWS_CONFIG_FILE", "").strip()
        if configured_path.startswith("~/") and home:
            config_path = Path(home) / configured_path[2:]
        elif configured_path:
            config_path = Path(configured_path).expanduser()
        elif home:
            config_path = Path(home) / ".aws" / "config"
        else:
            config_path = None
        profile = (
            source.get("AWS_PROFILE", "").strip()
            or source.get("AWS_DEFAULT_PROFILE", "").strip()
            or "default"
        )
        section = "default" if profile == "default" else f"profile {profile}"
        if config_path is not None and config_path.is_file():
            parser = configparser.ConfigParser(interpolation=None, strict=False)
            try:
                parser.read(config_path)
                region = parser.get(section, "region", fallback="").strip()
            except (configparser.Error, OSError):
                region = ""
    if not region:
        return {}
    return {"AWS_REGION": region, "AWS_DEFAULT_REGION": region}


def codex_environment(*additional: str) -> dict[str, str]:
    """Build the constrained Codex environment with resolved region metadata."""
    environment = role_environment(
        "CODEX_HOME",
        "XDG_CONFIG_HOME",
        "XDG_CACHE_HOME",
        "AWS_REGION",
        "AWS_DEFAULT_REGION",
        *additional,
    )
    environment.update(codex_region_environment())
    return environment
