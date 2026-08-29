"""Validated execution-boundary declarations for replaceable Agent Adapters."""

from __future__ import annotations

from dataclasses import dataclass
import os

from adapter_protocol import FEATURES, PROTOCOL_VERSION, conformance_report


FILESYSTEM_MODES = {"read-only", "workspace-write"}
EXECUTION_ENVIRONMENTS = {"local", "container", "hosted"}
NETWORK_EXPECTATIONS = {"none", "provider-only", "required", "unrestricted"}
BASE_ENVIRONMENT = ("PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "TERM", "USER", "LOGNAME", "SHELL")


def role_environment(*additional: str) -> dict[str, str]:
    allowed = set(BASE_ENVIRONMENT) | set(additional)
    return {name: value for name, value in os.environ.items() if name in allowed}


@dataclass(frozen=True)
class AdapterCapability:
    name: str
    protocol_version: int
    features: frozenset[str]
    execution_environment: str
    filesystem_mode: str
    allowed_working_roots: tuple[str, ...]
    network_expectation: str
    environment_allowlist: tuple[str, ...]
    credential_names: tuple[str, ...]
    timeout_seconds: int | None
    read_only_template: str

    @property
    def supports_read_only(self) -> bool:
        return bool(self.read_only_template) or self.filesystem_mode == "read-only"

    def supports(self, feature: str) -> bool:
        return feature in self.features

    def as_dict(self) -> dict:
        return {
            "protocol_version": self.protocol_version,
            "features": sorted(self.features),
            "execution_environment": self.execution_environment,
            "filesystem_mode": self.filesystem_mode,
            "allowed_working_roots": list(self.allowed_working_roots),
            "network_expectation": self.network_expectation,
            "environment_allowlist": list(self.environment_allowlist),
            "credential_names": list(self.credential_names),
            "timeout_seconds": self.timeout_seconds,
            "supports_read_only": self.supports_read_only,
        }


def load_capabilities(raw: dict, agents: dict) -> dict[str, AdapterCapability]:
    capabilities = {}
    for name in agents:
        supplied = raw.get(name, {}) if isinstance(raw, dict) else {}
        if not isinstance(supplied, dict):
            raise ValueError(f"agent_capabilities.{name} must be a table")
        environment = supplied.get("execution_environment", "local")
        protocol_version = supplied.get("protocol_version", PROTOCOL_VERSION)
        features = supplied.get("features", [])
        filesystem = supplied.get("filesystem_mode", "workspace-write")
        network = supplied.get("network_expectation", "provider-only")
        roots = supplied.get("allowed_working_roots", ["worktree"])
        allowlist = supplied.get("environment_allowlist", list(BASE_ENVIRONMENT))
        credentials = supplied.get("credential_names", [])
        timeout = supplied.get("timeout_seconds")
        read_only = supplied.get("read_only_template", "")
        if protocol_version != PROTOCOL_VERSION:
            raise ValueError(
                f"agent_capabilities.{name}.protocol_version must be {PROTOCOL_VERSION}"
            )
        if not isinstance(features, list) or not all(
            isinstance(item, str) and item in FEATURES for item in features
        ):
            raise ValueError(f"agent_capabilities.{name}.features is invalid")
        if environment not in EXECUTION_ENVIRONMENTS:
            raise ValueError(f"agent_capabilities.{name}.execution_environment is invalid")
        if filesystem not in FILESYSTEM_MODES:
            raise ValueError(f"agent_capabilities.{name}.filesystem_mode is invalid")
        if network not in NETWORK_EXPECTATIONS:
            raise ValueError(f"agent_capabilities.{name}.network_expectation is invalid")
        if not isinstance(roots, list) or not roots or not all(isinstance(item, str) and item for item in roots):
            raise ValueError(f"agent_capabilities.{name}.allowed_working_roots is invalid")
        if not isinstance(allowlist, list) or not all(isinstance(item, str) and item for item in allowlist):
            raise ValueError(f"agent_capabilities.{name}.environment_allowlist is invalid")
        if not isinstance(credentials, list) or not all(isinstance(item, str) and item for item in credentials):
            raise ValueError(f"agent_capabilities.{name}.credential_names is invalid")
        if timeout is not None and (not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1):
            raise ValueError(f"agent_capabilities.{name}.timeout_seconds must be positive or omitted")
        if not isinstance(read_only, str):
            raise ValueError(f"agent_capabilities.{name}.read_only_template must be a string")
        conformance = conformance_report(name, agents[name], supplied)
        if not conformance["compatible"]:
            raise ValueError(
                f"agent_capabilities.{name} is incompatible: "
                + "; ".join(conformance["errors"])
            )
        capabilities[name] = AdapterCapability(
            name=name,
            protocol_version=protocol_version,
            features=frozenset(features),
            execution_environment=environment,
            filesystem_mode=filesystem,
            allowed_working_roots=tuple(roots),
            network_expectation=network,
            environment_allowlist=tuple(dict.fromkeys((*BASE_ENVIRONMENT, *allowlist))),
            credential_names=tuple(credentials),
            timeout_seconds=timeout,
            read_only_template=read_only,
        )
    return capabilities
