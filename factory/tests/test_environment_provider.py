import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from environment_provider import EnvironmentProviderError, LocalEnvironmentProvider
from orchestrator import parser
from project_contract import ProjectContract


class LocalEnvironmentProviderTests(unittest.TestCase):
    def make_repo(self, directory: str, *, setup=(), required_tools=("git",)):
        repo = Path(directory)
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Factory Test"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "factory@example.test"], cwd=repo, check=True)
        (repo / "README.md").write_text("# Product\n")
        (repo / "tests").mkdir()
        contract = replace(
            ProjectContract.detect(repo),
            setup_commands=tuple(setup),
            required_tools=tuple(required_tools),
            ports=(8123,),
        )
        contract.write()
        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
        return repo, contract

    def test_local_lifecycle_records_contract_revision_health_and_reviewed_setup(self):
        with tempfile.TemporaryDirectory() as directory:
            repo, contract = self.make_repo(
                directory,
                setup=("printf prepared > prepared.txt",),
            )
            provider = LocalEnvironmentProvider(repo, contract)

            provisioned = provider.execute("provision")
            prepared = provider.execute("prepare", approved=True)
            health = provider.execute("health", run_gates=True)

            self.assertEqual(provisioned["status"], "provisioned")
            self.assertRegex(provisioned["revision"], r"^[a-f0-9]{40}$")
            self.assertRegex(provisioned["contract_sha256"], r"^[a-f0-9]{64}$")
            self.assertEqual(prepared["status"], "prepared")
            self.assertEqual((repo / "prepared.txt").read_text(), "prepared")
            self.assertEqual(health["status"], "healthy")
            self.assertTrue(all(check["status"] == "PASS" for check in health["checks"]))
            saved = json.loads((repo / ".factory/environment/state.json").read_text())
            self.assertEqual(saved["provider"], "local")
            self.assertEqual(saved["contract_sha256"], provisioned["contract_sha256"])

    def test_prepare_requires_explicit_approval_and_health_names_missing_tools(self):
        with tempfile.TemporaryDirectory() as directory:
            repo, contract = self.make_repo(
                directory,
                setup=("printf unsafe > should-not-exist.txt",),
                required_tools=("git", "factory-tool-that-does-not-exist"),
            )
            provider = LocalEnvironmentProvider(repo, contract)
            provider.execute("provision")

            with self.assertRaisesRegex(EnvironmentProviderError, "approval"):
                provider.execute("prepare")
            self.assertFalse((repo / "should-not-exist.txt").exists())
            provider.execute("prepare", approved=True)
            health = provider.execute("health")

            self.assertTrue((repo / "should-not-exist.txt").exists())
            self.assertEqual(health["status"], "blocked")
            self.assertIn(
                "factory-tool-that-does-not-exist",
                next(check["detail"] for check in health["checks"] if check["status"] == "FAIL"),
            )

    def test_preview_reset_and_destroy_touch_only_environment_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            repo, contract = self.make_repo(directory)
            provider = LocalEnvironmentProvider(repo, contract)
            provider.execute("provision")
            provider.execute("prepare", approved=True)
            provider.execute("health")

            preview = provider.execute(
                "preview",
                command=f"{sys.executable} -c 'import time; time.sleep(30)'",
            )
            reset = provider.execute("reset")
            destroyed = provider.execute("destroy")

            self.assertEqual(preview["status"], "running")
            self.assertGreater(preview["pid"], 0)
            self.assertEqual(reset["status"], "reset")
            self.assertEqual(destroyed["status"], "destroyed")
            self.assertTrue((repo / "README.md").is_file())
            self.assertFalse((repo / ".factory/environment").exists())

    def test_lifecycle_rejects_out_of_order_actions(self):
        with tempfile.TemporaryDirectory() as directory:
            repo, contract = self.make_repo(directory)
            provider = LocalEnvironmentProvider(repo, contract)

            with self.assertRaisesRegex(EnvironmentProviderError, "provision"):
                provider.execute("prepare", approved=True)
            with self.assertRaisesRegex(EnvironmentProviderError, "prepare"):
                provider.execute("health")
            provider.execute("provision")
            with self.assertRaisesRegex(EnvironmentProviderError, "healthy"):
                provider.execute("preview", command="python3 -m http.server")

    def test_provision_reports_revision_drift_instead_of_rebinding(self):
        with tempfile.TemporaryDirectory() as directory:
            repo, contract = self.make_repo(directory)
            provider = LocalEnvironmentProvider(repo, contract)
            original = provider.execute("provision")
            (repo / "README.md").write_text("# Changed product\n")
            subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "change"], cwd=repo, check=True)

            drift = provider.execute("provision")

            self.assertEqual(drift["status"], "blocked")
            self.assertIn("revision", drift["failure"])
            self.assertEqual(drift["revision"], original["revision"])
            self.assertNotEqual(drift["observed_revision"], original["revision"])

    def test_cli_parser_exposes_the_environment_lifecycle(self):
        args = parser().parse_args([
            "environment", "health", "--repo", "/tmp/product", "--gates", "--json",
        ])

        self.assertEqual(args.command, "environment")
        self.assertEqual(args.action, "health")
        self.assertTrue(args.gates)
        self.assertTrue(args.as_json)


if __name__ == "__main__":
    unittest.main()
