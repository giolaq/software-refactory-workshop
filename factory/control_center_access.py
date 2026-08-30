"""Access policy for local and ALB-authenticated Control Center deployments.

The HTTP server stays deliberately small.  Authentication remains an outer
boundary: loopback is trusted locally, while the AWS deployment trusts only
requests that an Application Load Balancer has authenticated with Cognito.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse


LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost"})


@dataclass(frozen=True)
class ControlCenterAccessPolicy:
    """Validate one of the two supported deployment boundaries."""

    public_origin: str | None = None

    @classmethod
    def from_environment(cls) -> "ControlCenterAccessPolicy":
        raw = os.environ.get("FACTORY_CONTROL_CENTER_PUBLIC_ORIGIN", "").strip()
        if not raw:
            return cls()
        parsed = urlparse(raw)
        if parsed.scheme != "https" or not parsed.hostname or parsed.path not in {"", "/"}:
            raise ValueError(
                "FACTORY_CONTROL_CENTER_PUBLIC_ORIGIN must be an HTTPS origin without a path"
            )
        if parsed.query or parsed.fragment or parsed.username or parsed.password:
            raise ValueError("FACTORY_CONTROL_CENTER_PUBLIC_ORIGIN must contain only scheme and host")
        return cls(raw.rstrip("/"))

    @property
    def hosted(self) -> bool:
        return self.public_origin is not None

    def validate_bind_host(self, host: str) -> None:
        allowed = LOCAL_HOSTS | ({"0.0.0.0"} if self.hosted else set())
        if host not in allowed:
            if self.hosted:
                raise ValueError("Hosted Control Center must bind to 0.0.0.0 or localhost")
            raise ValueError("The unauthenticated Control Center must bind to localhost")

    def validate_request(self, headers) -> None:
        host = headers.get("Host", "").split(":", 1)[0].strip("[]").lower()
        origin = headers.get("Origin")
        if not self.hosted:
            if host not in LOCAL_HOSTS:
                raise ValueError("The Control Center accepts requests only from this computer")
            if origin and urlparse(origin).hostname not in LOCAL_HOSTS:
                raise ValueError("Cross-origin Control Center requests are not allowed")
            return

        expected = urlparse(self.public_origin).hostname
        if host != expected:
            raise ValueError("The request host does not match the configured Control Center origin")
        if origin and origin.rstrip("/") != self.public_origin:
            raise ValueError("Cross-origin Control Center requests are not allowed")
        if not headers.get("X-Amzn-Oidc-Identity"):
            raise ValueError("The hosted Control Center requires ALB Cognito authentication")
