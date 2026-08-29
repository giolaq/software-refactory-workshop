import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from trigger_contract import TriggerError, TriggerRegistry
from workspace_contract import WorkspaceContract, WorkspaceContractError


class TriggerRegistryTests(unittest.TestCase):
    def test_authenticated_event_is_idempotent_and_only_proposes_intake(self):
        with tempfile.TemporaryDirectory() as directory:
            registry = TriggerRegistry(Path(directory))
            first = registry.propose(
                "webhook", "delivery-7", {"kind": "bug", "title": "Crash"},
                authenticated=True,
            )
            replay = registry.propose(
                "webhook", "delivery-7", {"kind": "bug", "title": "Crash"},
                authenticated=True,
            )
            self.assertEqual(first["status"], "proposed")
            self.assertFalse(first["may_dispatch"])
            self.assertEqual(replay["status"], "duplicate")
            self.assertEqual(first["trigger_id"], replay["trigger_id"])

    def test_external_trigger_requires_authentication_and_conflicting_replay_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            registry = TriggerRegistry(Path(directory))
            with self.assertRaisesRegex(TriggerError, "authenticated"):
                registry.propose("schedule", "nightly", {}, authenticated=False)
            registry.propose("webhook", "same", {"value": 1}, authenticated=True)
            with self.assertRaisesRegex(TriggerError, "different payload"):
                registry.propose("webhook", "same", {"value": 2}, authenticated=True)

    def test_trigger_rejects_secrets_and_unbounded_payloads(self):
        with tempfile.TemporaryDirectory() as directory:
            registry = TriggerRegistry(Path(directory))
            with self.assertRaisesRegex(TriggerError, "sensitive"):
                registry.propose(
                    "webhook", "secret-event", {"authorization": "Bearer secret"},
                    authenticated=True,
                )
            with self.assertRaisesRegex(TriggerError, "bounded"):
                registry.propose(
                    "webhook", "large-event", {"body": "x" * 70_000},
                    authenticated=True,
                )


class WorkspaceContractTests(unittest.TestCase):
    def make_repo(self, root: Path, name: str) -> Path:
        repo = root / name
        repo.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "factory@example.com"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Factory Test"], cwd=repo, check=True)
        (repo / "README.md").write_text(name + "\n")
        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "baseline"], cwd=repo, check=True)
        return repo

    def test_single_repository_is_the_default_without_extra_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self.make_repo(Path(directory), "app")
            contract = WorkspaceContract.load(repo)
            self.assertFalse(contract.configured)
            self.assertEqual(contract.repositories[0]["path"], ".")
            self.assertTrue(contract.repositories[0]["ticket_target"])
            self.assertEqual(contract.check()["status"], "ready")

    def test_multi_repository_contract_names_revisions_ownership_and_ticket_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            app = self.make_repo(root, "app")
            api = self.make_repo(root, "api")
            app_rev = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=app, text=True).strip()
            api_rev = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=api, text=True).strip()
            (app / "factory.workspace.toml").write_text(
                "version = 1\nname = 'recipe-workspace'\n"
                "[[repositories]]\nname = 'app'\npath = '.'\nrevision = '" + app_rev + "'\naccess = 'write'\nticket_target = true\n"
                "[[repositories]]\nname = 'api'\npath = '../api'\nrevision = '" + api_rev + "'\naccess = 'read-only'\nticket_target = false\n"
                "dependencies = ['app']\nverification = ['python -m unittest']\n"
            )
            contract = WorkspaceContract.load(app)
            report = contract.check()
            self.assertEqual(report["status"], "ready")
            self.assertEqual(report["revisions"]["api"], api_rev)
            self.assertEqual(contract.ticket_repository(), "app")

    def test_missing_repository_blocks_before_implementation(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self.make_repo(Path(directory), "app")
            (repo / "factory.workspace.toml").write_text(
                "version = 1\nname = 'broken'\n"
                "[[repositories]]\nname = 'missing'\npath = '../missing'\nrevision = 'abc'\naccess = 'write'\nticket_target = true\n"
            )
            report = WorkspaceContract.load(repo).check()
            self.assertEqual(report["status"], "blocked")
            self.assertIn("missing", report["recovery_action"])
            self.assertIn("repository owner", report["recovery_action"])
            self.assertEqual(report["checks"][0]["owner"], "repository owner")
            with self.assertRaisesRegex(WorkspaceContractError, "before dispatch"):
                WorkspaceContract.load(repo).require_ready()

    def test_required_service_without_health_interface_names_its_owner(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self.make_repo(Path(directory), "app")
            revision = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=repo, text=True,
            ).strip()
            (repo / "factory.workspace.toml").write_text(
                "version = 1\nname = 'service-workspace'\n"
                "[[repositories]]\nname = 'app'\npath = '.'\nrevision = '" + revision + "'\n"
                "access = 'write'\nticket_target = true\n"
                "[[services]]\nname = 'catalog'\nrequired = true\nowner = 'platform-team'\n"
            )

            report = WorkspaceContract.load(repo).check()

            self.assertEqual(report["status"], "blocked")
            service = next(item for item in report["checks"] if item.get("service"))
            self.assertEqual(service["owner"], "platform-team")


if __name__ == "__main__":
    unittest.main()
