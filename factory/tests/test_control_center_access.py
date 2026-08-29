import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import urlopen
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]))

from control_center_access import ControlCenterAccessPolicy
from control_center import ControlCenter, ControlCenterServer


class HeaderMap(dict):
    def get(self, key, default=None):
        for name, value in self.items():
            if name.lower() == key.lower():
                return value
        return default


class ControlCenterAccessPolicyTests(unittest.TestCase):
    def test_local_policy_rejects_remote_hosts(self):
        policy = ControlCenterAccessPolicy()
        policy.validate_request(HeaderMap(Host="localhost:5050", Origin="http://localhost:5050"))
        with self.assertRaisesRegex(ValueError, "only from this computer"):
            policy.validate_request(HeaderMap(Host="factory.example.com"))
        with self.assertRaisesRegex(ValueError, "must bind to localhost"):
            policy.validate_bind_host("0.0.0.0")

    def test_hosted_policy_requires_exact_origin_and_alb_identity(self):
        policy = ControlCenterAccessPolicy("https://factory.example.com")
        headers = HeaderMap(
            Host="factory.example.com",
            Origin="https://factory.example.com",
            **{"X-Amzn-Oidc-Identity": "subject-123"},
        )
        policy.validate_request(headers)
        policy.validate_bind_host("0.0.0.0")
        with self.assertRaisesRegex(ValueError, "requires ALB"):
            policy.validate_request(HeaderMap(Host="factory.example.com"))
        with self.assertRaisesRegex(ValueError, "Cross-origin"):
            policy.validate_request(HeaderMap(
                Host="factory.example.com", Origin="https://evil.example",
                **{"X-Amzn-Oidc-Identity": "subject-123"},
            ))

    def test_public_origin_must_be_https_origin(self):
        with patch.dict(os.environ, {"FACTORY_CONTROL_CENTER_PUBLIC_ORIGIN": "http://example.com/path"}):
            with self.assertRaisesRegex(ValueError, "HTTPS origin"):
                ControlCenterAccessPolicy.from_environment()

    def test_health_endpoint_contains_no_repository_data_and_needs_no_browser_auth(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {
                "FACTORY_CONTROL_CENTER_PUBLIC_ORIGIN": "https://factory.example.com",
            }, clear=True):
                center = ControlCenter(Path(directory))
            server = ControlCenterServer(("127.0.0.1", 0), center)
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                with urlopen(
                    f"http://127.0.0.1:{server.server_port}/healthz", timeout=2,
                ) as response:
                    self.assertEqual(response.read(), b'{"status": "healthy"}')
            finally:
                server.shutdown()
                server.server_close()
                center.shutdown()
                worker.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
