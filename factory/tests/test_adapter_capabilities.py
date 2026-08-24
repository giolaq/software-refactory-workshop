import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).parents[1]))

from adapter_capabilities import load_capabilities
from factory_charter import FactoryCharter
from orchestrator import Factory
from project_contract import ProjectContract


class AdapterCapabilityTests(unittest.TestCase):
    def test_role_environment_omits_unrelated_credentials(self):
        capabilities = load_capabilities({
            "worker": {
                "environment_allowlist": ["PATH", "ROLE_TOKEN"],
                "credential_names": ["ROLE_TOKEN"],
            },
        }, {"worker": "worker {prompt}"})
        factory = Factory.__new__(Factory)
        factory.capabilities = capabilities
        with mock.patch.dict(os.environ, {
            "PATH": "/usr/bin", "ROLE_TOKEN": "needed",
            "AWS_SECRET_ACCESS_KEY": "must-not-leak",
        }, clear=True):
            environment = factory.adapter_environment("worker")

        self.assertEqual(environment["ROLE_TOKEN"], "needed")
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", environment)

    def test_codex_environment_resolves_region_without_forwarding_credentials(self):
        capabilities = load_capabilities({
            "codex": {
                "environment_allowlist": ["PATH", "HOME", "AWS_REGION", "AWS_DEFAULT_REGION"],
            },
        }, {"codex": "codex {prompt}"})
        factory = Factory.__new__(Factory)
        factory.capabilities = capabilities
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            config = home / ".aws/config"
            config.parent.mkdir()
            config.write_text("[default]\nregion = us-east-1\n")
            with mock.patch.dict(os.environ, {
                "PATH": "/usr/bin",
                "HOME": str(home),
                "AWS_SECRET_ACCESS_KEY": "must-not-leak",
            }, clear=True):
                environment = factory.adapter_environment("codex")

        self.assertEqual(environment["AWS_REGION"], "us-east-1")
        self.assertEqual(environment["AWS_DEFAULT_REGION"], "us-east-1")
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", environment)

    def test_read_only_template_is_a_declared_capability(self):
        capability = load_capabilities({
            "worker": {"read_only_template": "worker --read-only {prompt}"},
        }, {"worker": "worker {prompt}"})["worker"]
        self.assertTrue(capability.supports_read_only)


if __name__ == "__main__":
    unittest.main()
