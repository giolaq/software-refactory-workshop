import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parents[1]))

from github_repository import (
    GitHubRepositoryError,
    bootstrap_empty_workshop_repository,
    checkout_github_repository,
    connect_github_repository,
    managed_checkout_path,
    parse_github_repository,
)


def completed(command, returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(command, returncode, stdout, stderr)


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()


class GitHubRepositoryTests(unittest.TestCase):
    def test_normalizes_https_ssh_and_owner_name_inputs(self):
        expected = "https://github.com/example/workshop"
        for value in (
            expected,
            expected + ".git",
            "git@github.com:example/workshop.git",
            "example/workshop",
        ):
            with self.subTest(value=value):
                self.assertEqual(parse_github_repository(value).url, expected)

    def test_rejects_non_github_and_command_like_values(self):
        for value in (
            "https://gitlab.com/example/workshop",
            "https://github.com/example/workshop/issues",
            "example/workshop; rm -rf repo",
        ):
            with self.subTest(value=value):
                with self.assertRaises(GitHubRepositoryError):
                    parse_github_repository(value)

    def test_connect_rejects_a_different_origin_instead_of_rewriting_it(self):
        calls = []

        def runner(command, **kwargs):
            calls.append(command)
            if command[:3] == ["gh", "repo", "view"]:
                return completed(command, stdout=json.dumps({"nameWithOwner": "attendee/demo"}))
            if command[:4] == ["git", "remote", "get-url", "origin"]:
                return completed(command, stdout="https://github.com/giolaq/software-refactory-workshop.git\n")
            return completed(command)

        with tempfile.TemporaryDirectory() as directory, mock.patch(
            "github_repository.shutil.which", return_value="/usr/local/bin/gh",
        ):
            with self.assertRaisesRegex(GitHubRepositoryError, "different GitHub repository"):
                connect_github_repository(
                    Path(directory), "https://github.com/attendee/demo", runner=runner,
                )

        self.assertNotIn("set-url", [part for call in calls for part in call])

    def test_checkout_clones_to_an_isolated_managed_path(self):
        calls = []

        def runner(command, **kwargs):
            calls.append(command)
            if command[:3] == ["gh", "repo", "view"]:
                return completed(command, stdout=json.dumps({"nameWithOwner": "attendee/demo"}))
            if command[:3] == ["gh", "repo", "clone"]:
                destination = Path(command[4])
                (destination / ".git").mkdir(parents=True)
            return completed(command)

        with tempfile.TemporaryDirectory() as directory, mock.patch(
            "github_repository.shutil.which", return_value="/usr/local/bin/gh",
        ):
            root = Path(directory)
            expected = managed_checkout_path(root, parse_github_repository("attendee/demo"))
            result = checkout_github_repository(root, "https://github.com/attendee/demo", runner=runner)

        self.assertEqual(Path(result["path"]), expected)
        self.assertEqual(result["action"], "cloned")
        self.assertIn(["gh", "repo", "clone", "attendee/demo", str(expected)], calls)

    def test_bootstrap_populates_an_empty_repository_with_workshop_history_and_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            remote = root / "attendee.git"
            target = root / "target"
            source.mkdir()
            git(source, "init", "-q", "-b", "main")
            git(source, "config", "user.name", "Factory Test")
            git(source, "config", "user.email", "factory@example.test")
            for relative in (
                "factory/factory",
                "factory.project.toml",
                "factory.charter.toml",
                "demo-app/app.py",
            ):
                path = source / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"{relative}\n")
            (source / ".gitignore").write_text(".factory/\n")
            git(source, "add", ".")
            git(source, "commit", "-q", "-m", "workshop source")
            source_head = git(source, "rev-parse", "HEAD")
            git(source, "tag", "factory-baseline")
            git(root, "init", "-q", "--bare", str(remote))
            git(root, "clone", "-q", str(remote), str(target))
            local_config = target / ".factory/local.toml"
            local_config.parent.mkdir(parents=True)
            local_config.write_text('preset = "claude-workshop"\n')

            result = bootstrap_empty_workshop_repository(target, source)

            self.assertEqual(result["commit"], source_head)
            self.assertEqual(git(target, "rev-parse", "HEAD"), source_head)
            self.assertEqual(git(target, "rev-parse", "factory-baseline"), source_head)
            self.assertEqual(git(target, "status", "--porcelain"), "")
            self.assertTrue((target / "demo-app/app.py").is_file())
            self.assertTrue(local_config.is_file())
            self.assertEqual(
                git(root, "--git-dir", str(remote), "rev-parse", "refs/heads/main"),
                source_head,
            )

    def test_bootstrap_refuses_a_repository_that_already_has_a_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            target = root / "target"
            for repo in (source, target):
                repo.mkdir()
                git(repo, "init", "-q", "-b", "main")
                git(repo, "config", "user.name", "Factory Test")
                git(repo, "config", "user.email", "factory@example.test")
            for relative in (
                "factory/factory",
                "factory.project.toml",
                "factory.charter.toml",
                "demo-app/app.py",
            ):
                path = source / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"{relative}\n")
            git(source, "add", ".")
            git(source, "commit", "-q", "-m", "workshop source")
            git(source, "tag", "factory-baseline")
            (target / "README.md").write_text("# Existing project\n")
            git(target, "add", ".")
            git(target, "commit", "-q", "-m", "existing project")

            with self.assertRaisesRegex(GitHubRepositoryError, "already has a commit"):
                bootstrap_empty_workshop_repository(target, source)

    def test_bootstrap_refuses_remote_refs_created_after_the_empty_clone(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            seed = root / "seed"
            remote = root / "attendee.git"
            target = root / "target"
            for repo in (source, seed):
                repo.mkdir()
                git(repo, "init", "-q", "-b", "main")
                git(repo, "config", "user.name", "Factory Test")
                git(repo, "config", "user.email", "factory@example.test")
            for relative in (
                "factory/factory",
                "factory.project.toml",
                "factory.charter.toml",
                "demo-app/app.py",
            ):
                path = source / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"{relative}\n")
            git(source, "add", ".")
            git(source, "commit", "-q", "-m", "workshop source")
            git(source, "tag", "factory-baseline")
            git(root, "init", "-q", "--bare", str(remote))
            git(root, "clone", "-q", str(remote), str(target))
            (seed / "README.md").write_text("# Existing project\n")
            git(seed, "add", ".")
            git(seed, "commit", "-q", "-m", "existing project")
            git(seed, "remote", "add", "origin", str(remote))
            git(seed, "push", "-q", "origin", "main")

            with self.assertRaisesRegex(GitHubRepositoryError, "not empty"):
                bootstrap_empty_workshop_repository(target, source)

            self.assertFalse((target / "demo-app/app.py").exists())


if __name__ == "__main__":
    unittest.main()
