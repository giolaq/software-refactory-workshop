import json
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).parents[1]))

from control_center import ControlCenter, ControlCenterServer, InputError, planning_recovery
from factory_charter import FactoryCharter
from orchestrator import parser
from project_contract import ProjectContract


class ControlCenterTests(unittest.TestCase):
    def make_repo(self, directory: str) -> Path:
        repo = Path(directory)
        (repo / "factory/control_center").mkdir(parents=True)
        factory = repo / "factory/factory"
        factory.write_text("#!/bin/sh\nprintf 'factory args: %s\\n' \"$*\"\n")
        factory.chmod(0o755)
        (repo / "factory/factory.toml").write_text(
            "[agents]\nmy-agent = './tools/my-agent {prompt}'\n"
        )
        (repo / "factory/FACTORY_CANVAS.md").write_text("# Factory Canvas\n")
        return repo

    def write_plan_manifest(self, center: ControlCenter, plan: str, planning_agent: str):
        run = center.repo / ".factory/plans" / plan
        run.mkdir(parents=True, exist_ok=True)
        (run / "manifest.json").write_text(json.dumps({
            "plan_id": plan,
            "planning_agent": planning_agent,
        }))

    def test_parser_exposes_loopback_control_center(self):
        args = parser().parse_args(["control-center", "--no-open"])

        self.assertEqual(args.host, "127.0.0.1")
        self.assertEqual(args.port, 5050)
        self.assertTrue(args.no_open)

    def test_parser_exposes_recover_command(self):
        args = parser().parse_args([
            "recover", "--repo", "/tmp/workshop",
            "--project-number", "15", "--yes",
        ])

        self.assertEqual(args.command, "recover")
        self.assertEqual(args.project_number, 15)
        self.assertTrue(args.yes)

    def test_parser_exposes_protected_qa_recovery(self):
        args = parser().parse_args([
            "retry", "6", "--repo", "/tmp/workshop", "--reset-qa",
            "--reason", "Regenerate the defective protected QA evidence",
            "--yes",
        ])

        self.assertEqual(args.command, "retry")
        self.assertEqual(args.issue, 6)
        self.assertTrue(args.reset_qa)
        self.assertTrue(args.yes)

    def test_parser_exposes_human_qa_revision_feedback(self):
        args = parser().parse_args([
            "request-test-changes",
            "6",
            "--repo",
            "/tmp/workshop",
            "--feedback",
            "Cover the public boundary instead of internals.",
            "--yes",
        ])

        self.assertEqual(args.command, "request-test-changes")
        self.assertEqual(args.issue, 6)
        self.assertIn("public boundary", args.feedback)
        self.assertTrue(args.yes)

    def test_control_center_builds_human_qa_revision_command(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            state = center.repo / ".factory/state.json"
            state.parent.mkdir(parents=True, exist_ok=True)
            state.write_text(json.dumps({
                "mode": "mock",
                "tickets": [{
                    "number": 6,
                    "status": "QA Review",
                    "qa_commit": "a" * 40,
                }],
            }))

            _, commands = center.build_commands("request-test-changes", {
                "issue": 6,
                "mode": "rehearsal",
                "feedback": "Cover the public boundary instead of internals.",
            })

            command = commands[0]
            self.assertIn("request-test-changes", command)
            self.assertIn("--feedback", command)
            self.assertIn(
                "Cover the public boundary instead of internals.",
                command,
            )
            self.assertIn("--yes", command)

            javascript = (
                Path(__file__).parents[1] / "control_center/app.js"
            ).read_text()
            self.assertIn("Request test changes", javascript)
            self.assertIn("qa-revision-feedback", javascript)

    def test_completed_node_application_is_detected_and_can_be_started(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            ProjectContract.detect(center.repo).write()
            (center.repo / "package.json").write_text(json.dumps({
                "name": "attendee-app",
                "scripts": {
                    "start": "node src/server.mjs",
                    "test": "node --test",
                },
            }))
            (center.repo / "README.md").write_text(
                "# Attendee app\n\n"
                "Run `npm start`, then open http://127.0.0.1:3000.\n"
            )

            with patch.object(center, "_port_available", return_value=True):
                application = center.application_instructions()
                title, commands = center.build_commands("start-app", {})

            self.assertTrue(application["available"])
            self.assertEqual(application["kind"], "node")
            self.assertIn("npm start", application["command"])
            self.assertEqual(application["urls"], [{
                "label": "Application",
                "url": "http://127.0.0.1:3000",
            }])
            self.assertEqual(title, "Run the completed application")
            self.assertEqual(commands, [["npm", "start"]])

    def test_completed_application_uses_an_available_port_when_documented_port_is_busy(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            ProjectContract.detect(center.repo).write()
            (center.repo / "package.json").write_text(json.dumps({
                "scripts": {"start": "node src/server.mjs"},
            }))
            (center.repo / "README.md").write_text(
                "Open http://127.0.0.1:3000 after `npm start`.\n"
            )

            with patch.object(
                center, "_port_available",
                side_effect=lambda port: port == 3001,
            ):
                application = center.application_instructions()
                _, commands = center.build_commands("start-app", {})

            self.assertEqual(application["preferred_port"], 3000)
            self.assertEqual(application["port"], 3001)
            self.assertIn("PORT=3001 npm start", application["command"])
            self.assertEqual(
                application["urls"][0]["url"],
                "http://127.0.0.1:3001",
            )
            self.assertEqual(
                commands,
                [["env", "PORT=3001", "npm", "start"]],
            )

    def test_vite_application_installs_dependencies_and_uses_the_selected_port(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            (center.repo / "package.json").write_text(json.dumps({
                "scripts": {"start": "vite"},
                "dependencies": {"three": "0.180.0"},
                "devDependencies": {"vite": "8.2.2"},
            }))
            (center.repo / "package-lock.json").write_text("{}\n")
            ProjectContract.detect(center.repo).write()

            with patch.object(center, "_port_available", return_value=True):
                application = center.application_instructions()
                _, commands = center.build_commands("start-app", {})

            self.assertIn("npm ci\nnpm start --", application["command"])
            self.assertEqual(commands, [
                ["npm", "ci"],
                [
                    "npm", "start", "--",
                    "--host", "127.0.0.1",
                    "--port", "3000",
                    "--strictPort",
                ],
            ])

    def test_vite_application_repairs_an_incomplete_dependency_install(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            (center.repo / "package.json").write_text(json.dumps({
                "scripts": {"start": "vite"},
                "devDependencies": {"vite": "8.2.2"},
            }))
            (center.repo / "package-lock.json").write_text("{}\n")
            (center.repo / "node_modules/vite").mkdir(parents=True)
            ProjectContract.detect(center.repo).write()

            with patch.object(center, "_port_available", return_value=True):
                _, commands = center.build_commands("start-app", {})

            self.assertEqual(commands[0], ["npm", "ci"])

    def test_start_app_refuses_a_repository_without_a_supported_entrypoint(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            ProjectContract.detect(center.repo).write()

            self.assertFalse(center.application_instructions()["available"])
            with self.assertRaisesRegex(
                InputError, "No supported application entry point",
            ):
                center.build_commands("start-app", {})

    def test_failed_app_start_explains_missing_dependencies_and_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            log = center.repo / ".factory/logs/start-app.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text(
                "$ npm start\n\n"
                "> attendee-app@1.0.0 start\n"
                "> vite\n\n"
                "sh: vite: command not found\n"
            )
            center.operation = {
                "action": "start-app",
                "status": "failed",
                "exit_code": 127,
                "command": "npm start",
                "error": "The operation failed. Read the final log lines for the cause.",
                "log": str(log),
            }

            operation = center.operation_snapshot()

            self.assertIn("missing installed Node dependencies", operation["failure"]["cause"])
            self.assertIn("Choose Start app again", operation["failure"]["recovery"])
            self.assertIn(operation["failure"]["cause"], operation["error"])

    def test_external_repository_uses_the_bundled_control_plane_and_can_be_initialized(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
            (repo / "src").mkdir()
            (repo / "src/main.py").write_text("print('hello')\n")

            center = ControlCenter(repo)
            title, commands = center.build_commands("init-project", {})
            snapshot = center.snapshot()

            self.assertEqual(title, "Initialize Project Contract")
            self.assertIn(str(repo.resolve()), commands[0])
            self.assertTrue(center.factory.is_file())
            self.assertNotEqual(center.factory, repo / "factory/factory")
            self.assertEqual(snapshot["project"]["source_roots"], ["src"])
            self.assertFalse(snapshot["project"]["configured"])

    def test_charter_is_a_visible_explicit_human_gate_before_planning(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            project = ProjectContract.detect(center.repo)
            project.write()
            FactoryCharter.draft(center.repo, project).write()

            draft = center.snapshot()
            title, commands = center.build_commands("approve-charter", {})

            self.assertTrue(draft["charter"]["configured"])
            self.assertFalse(draft["charter"]["approved"])
            self.assertEqual(draft["journey"]["next"]["label"], "Review Factory Charter")
            self.assertEqual(title, "Approve Factory Charter")
            self.assertIn("approve-charter", commands[0])
            self.assertIn("--yes", commands[0])

            FactoryCharter.load(center.repo).approve()
            approved = center.snapshot()
            self.assertTrue(approved["charter"]["approved"])
            self.assertNotEqual(approved["charter"]["policy_sha256"], "")

            publish_title, publish_commands = center.build_commands("publish-setup", {})
            self.assertEqual(publish_title, "Publish repository setup")
            self.assertIn("publish-setup", publish_commands[0])
            self.assertIn("--yes", publish_commands[0])

    def test_monitor_actions_are_registered_and_publication_is_live_only(self):
        with tempfile.TemporaryDirectory() as temp:
            center = ControlCenter(self.make_repo(temp))
            title, commands = center.build_commands("monitor", {"mode": "rehearsal"})
            self.assertEqual(title, "Preview repository health")
            self.assertIn("monitor", commands[0])
            self.assertIn("--json", commands[0])
            with self.assertRaises(InputError):
                center.build_commands("publish-monitor", {"mode": "rehearsal"})
            title, commands = center.build_commands("publish-monitor", {"mode": "live"})
            self.assertEqual(title, "Publish monitor findings")
            self.assertIn("--publish", commands[0])

    def test_configuration_is_allowlisted_and_never_uses_a_shell_command(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))

            title, commands = center.build_commands("configure", {
                "profile": "standard",
                "planning_agent": "claude",
                "agent": "my-agent",
                "qa_agent": "codex",
                "supervisor_agent": "my-agent",
                "review_agent": "my-agent",
                "review_qa_tests": True,
                "max_parallel": 2,
            })

            self.assertEqual(title, "Save factory configuration")
            self.assertIsInstance(commands[0], list)
            self.assertIn("my-agent", commands[0])
            self.assertIn("--supervisor-agent", commands[0])
            self.assertIn("--review-agent", commands[0])
            self.assertIn("--review-qa-tests", commands[0])
            self.assertNotIn("sh", commands[0])

            with self.assertRaisesRegex(InputError, "Unknown agent adapter"):
                center.build_commands("configure", {"agent": "codex; rm -rf repo"})

    def test_live_configuration_requires_and_connects_an_explicit_repository_url(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))

            with self.assertRaisesRegex(InputError, "repository URL"):
                center.build_commands("configure", {
                    "mode": "live", "preset": "claude-workshop",
                })
            _, commands = center.build_commands("configure", {
                "mode": "live",
                "preset": "claude-workshop",
                "github_repository": "git@github.com:attendee/workshop.git",
            })

            self.assertEqual(commands[0][1], "checkout")
            self.assertIn("https://github.com/attendee/workshop", commands[0])
            self.assertIn("--github-repository", commands[1])
            self.assertIn("https://github.com/attendee/workshop", commands[1])
            self.assertIn("--repo", commands[1])

            _, commands = center.build_commands("configure", {
                "mode": "live",
                "preset": "claude-workshop",
                "github_repository": "https://github.com/attendee/workshop",
                "bootstrap_workshop": True,
            })

            self.assertEqual([command[1] for command in commands], [
                "checkout", "bootstrap-workshop", "configure",
            ])
            self.assertIn(str(center.repo), commands[1])
            self.assertIn("--source", commands[1])

    def test_connected_empty_repository_can_request_workshop_bootstrap(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self.make_repo(directory)
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
            subprocess.run(
                ["git", "remote", "add", "origin", "https://github.com/attendee/workshop.git"],
                cwd=repo,
                check=True,
            )
            center = ControlCenter(repo)

            _, commands = center.build_commands("configure", {
                "mode": "live",
                "preset": "claude-workshop",
                "github_repository": "https://github.com/attendee/workshop",
                "bootstrap_workshop": True,
            })

            self.assertEqual([command[1] for command in commands], [
                "bootstrap-workshop", "configure",
            ])
            self.assertIn(str(repo.resolve()), commands[0])

    def test_successful_live_configuration_activates_the_managed_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            host = self.make_repo(directory)
            factory = host / "factory/factory"
            factory.write_text(
                "#!/bin/sh\n"
                "if [ \"$1\" = checkout ]; then\n"
                "  shift 2\n"
                "  shift\n"
                "  mkdir -p \"$1/attendee/workshop/.git\"\n"
                "fi\n"
                "printf 'factory args: %s\\n' \"$*\"\n"
            )
            factory.chmod(0o755)
            center = ControlCenter(host)

            center.start("configure", {
                "mode": "live",
                "preset": "claude-workshop",
                "github_repository": "https://github.com/attendee/workshop",
            })
            deadline = time.monotonic() + 3
            while center.operation_snapshot().get("status") == "running" and time.monotonic() < deadline:
                time.sleep(0.02)

            target = center.repository_root / "attendee/workshop"
            self.assertEqual(center.operation_snapshot()["status"], "succeeded")
            self.assertEqual(center.repo, target.resolve())
            self.assertEqual(ControlCenter(host).repo, target.resolve())

    def test_planning_requires_a_saved_prd_and_uses_mock_explicitly(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            with self.assertRaisesRegex(InputError, "Save the PRD"):
                center.build_commands("plan", {"mode": "rehearsal"})

            center.save_prd("# Recipe app\n\nBuild a recipe discovery experience.")
            _, commands = center.build_commands("plan", {
                "mode": "rehearsal", "profile": "standard",
            })

            self.assertEqual(commands[0][1], "plan")
            self.assertIn(str(center.prd_path), commands[0])
            self.assertIn("--mock", commands[0])

    def test_planning_uses_the_profile_saved_for_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            local = center.repo / ".factory/local.toml"
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_text('profile = "lean"\n')
            center.save_prd("# Recipe app\n")

            _, commands = center.build_commands("plan", {
                "mode": "rehearsal", "profile": "assured",
            })

            self.assertIn("lean", commands[0])
            self.assertNotIn("assured", commands[0])

    def test_autonomous_demo_requires_a_transient_visible_opt_in_for_plan_and_run(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            local = center.repo / ".factory/local.toml"
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_text('profile = "autonomous-demo"\n')
            center.save_prd("# Deliberately autonomous workshop contrast\n")

            for action in ("plan", "run"):
                with self.subTest(action=action):
                    with self.assertRaisesRegex(InputError, "delegates final merge accountability"):
                        center.build_commands(action, {"mode": "rehearsal"})
                    _, commands = center.build_commands(action, {
                        "mode": "rehearsal",
                        "allow_autonomous_merge": True,
                    })
                    self.assertIn("--allow-autonomous-merge", commands[0])

            html = (Path(__file__).parents[1] / "control_center/index.html").read_text()
            javascript = (Path(__file__).parents[1] / "control_center/app.js").read_text()
            self.assertIn('value="autonomous-demo"', html)
            self.assertIn('id="autonomous-merge-opt-in"', html)
            self.assertIn("delegates final merge accountability", html)
            self.assertIn("allow_autonomous_merge", javascript)

    def test_human_gate_commands_are_noninteractive(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            plan = "a" * 12
            self.write_plan_manifest(center, plan, "mock")

            _, product = center.build_commands("approve-product", {"plan_id": plan})
            _, tests = center.build_commands("approve-tests", {"issue": 7})
            _, merge = center.build_commands("merge", {"issue": 7, "mode": "rehearsal"})
            _, retry = center.build_commands("retry", {
                "issue": 7,
                "mode": "rehearsal",
                "budget_lines": 1400,
                "reason": "The approved browser workflow remains one outcome",
            })
            _, publish = center.build_commands("publish-plan", {
                "plan_id": plan, "mode": "rehearsal", "scenario": "recipe-rebrand",
            })

            self.assertIn("--yes", product[0])
            self.assertIn("--yes", tests[0])
            self.assertIn("--yes", merge[0])
            self.assertIn("--mock", merge[0])
            self.assertIn("--budget-lines", retry[0])
            self.assertIn("--reason", retry[0])
            self.assertIn("--yes", retry[0])
            self.assertIn("--yes", publish[0])
            self.assertIn("approve-rehearsal", publish[0])

    def test_control_center_builds_only_the_dedicated_qa_recovery_command(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            state = center.repo / ".factory/state.json"
            state.parent.mkdir(parents=True, exist_ok=True)
            state.write_text(json.dumps({
                "mode": "mock",
                "tickets": [{
                    "number": 6,
                    "status": "Blocked",
                    "failure": (
                        "QA_EVIDENCE_DEFECT: the protected test harness is defective."
                    ),
                }],
            }))

            _, commands = center.build_commands("retry", {
                "issue": 6,
                "mode": "rehearsal",
                "reset_qa": True,
                "reason": "Regenerate the defective protected QA evidence",
            })

            self.assertIn("--reset-qa", commands[0])
            self.assertIn("--yes", commands[0])

            state.write_text(json.dumps({
                "mode": "mock",
                "tickets": [{
                    "number": 7,
                    "status": "Blocked",
                    "failure": "A required gate failed.",
                }],
            }))
            with self.assertRaisesRegex(InputError, "Reason is required"):
                center.build_commands("retry", {
                    "issue": 7,
                    "mode": "rehearsal",
                })
            with self.assertRaisesRegex(
                InputError, "available only.*QA evidence defect",
            ):
                center.build_commands("retry", {
                    "issue": 7,
                    "mode": "rehearsal",
                    "reset_qa": True,
                    "reason": "Regenerate the defective protected QA evidence",
                })

    def test_control_center_saves_a_validated_ticket_correction_before_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            subprocess.run(
                ["git", "init", "-q", "-b", "main"],
                cwd=center.repo,
                check=True,
            )
            subprocess.run(
                [
                    "git", "remote", "add", "origin",
                    "https://github.com/attendee/workshop.git",
                ],
                cwd=center.repo,
                check=True,
            )
            local = center.repo / ".factory/local.toml"
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_text(
                'github_repository = "https://github.com/attendee/workshop"\n'
                "project_number = 16\n"
            )
            body = (
                "## Spec\n\nCreate the npm lifecycle.\n\n"
                "## Acceptance criteria\n\n- [ ] npm test passes.\n\n"
                "## File ownership\n\n- package.json\n\n"
                "<!-- factory-plan:abc12345:TOOLING -->\n"
                "<!-- factory-governance:v1;profile=standard;"
                f"charter={'a' * 64};merge=human -->\n"
            )
            state = center.repo / ".factory/state.json"
            state.write_text(json.dumps({
                "mode": "live",
                "tickets": [{
                    "number": 1,
                    "status": "Blocked",
                    "body": body,
                    "failure": (
                        "TICKET_SCOPE_CONFLICT: .gitignore is outside Ticket "
                        "#1 ownership."
                    ),
                    "triage": {"declared_paths": ["package.json"]},
                    "history": [],
                }],
            }))
            proposal = body.replace(
                "- package.json",
                "- package.json\n- .gitignore",
            )

            title, commands = center.build_commands("save-ticket-and-retry", {
                "issue": 1,
                "mode": "live",
                "ticket_body": proposal,
                "reason": (
                    "Added .gitignore ownership so generated outputs remain untracked"
                ),
            })

            self.assertEqual(title, "Save correction and retry ticket #1")
            self.assertEqual(commands[0][:3], ["gh", "issue", "edit"])
            self.assertIn("attendee/workshop", commands[0])
            correction_file = Path(commands[0][commands[0].index("--body-file") + 1])
            self.assertEqual(correction_file.read_text().strip(), proposal.strip())
            self.assertEqual(commands[1][1:3], ["retry", "1"])
            self.assertIn("--project-number", commands[1])
            self.assertIn("--reason", commands[1])

            without_marker = proposal.replace(
                "<!-- factory-governance:v1;profile=standard;"
                f"charter={'a' * 64};merge=human -->",
                "",
            )
            with self.assertRaisesRegex(
                InputError, "identity and governance markers",
            ):
                center.build_commands("save-ticket-and-retry", {
                    "issue": 1,
                    "mode": "live",
                    "ticket_body": without_marker,
                    "reason": "Save the reviewed Ticket correction",
                })

            without_required_path = proposal.replace(
                "- .gitignore",
                "- README.md",
            )
            with self.assertRaisesRegex(InputError, "must add these paths"):
                center.build_commands("save-ticket-and-retry", {
                    "issue": 1,
                    "mode": "live",
                    "ticket_body": without_required_path,
                    "reason": "Save the reviewed Ticket correction",
                })

            with self.assertRaisesRegex(InputError, "requires a Live GitHub run"):
                center.build_commands("save-ticket-and-retry", {
                    "issue": 1,
                    "mode": "rehearsal",
                    "ticket_body": proposal,
                    "reason": "Save the reviewed Ticket correction",
                })

    def test_live_merge_rejects_persisted_rehearsal_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            state_path = center.repo / ".factory/state.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps({
                "mode": "mock",
                "tickets": [{
                    "number": 5,
                    "status": "In Review",
                    "review_ref": "rehearsal://ticket/5/attempt/1",
                    "pr_url": "",
                }],
            }))

            self.assertEqual(center.snapshot()["factory"]["execution_mode"], "rehearsal")
            with self.assertRaisesRegex(
                InputError,
                "belongs to a Rehearsal run.*Control Center is set to Live",
            ):
                center.build_commands("merge", {"issue": 5, "mode": "live"})

            _, rehearsal = center.build_commands(
                "merge", {"issue": 5, "mode": "rehearsal"},
            )
            self.assertIn("--mock", rehearsal[0])

    def test_blocked_ticket_ui_never_offers_an_impossible_blind_retry(self):
        javascript = (Path(__file__).parents[1] / "control_center/app.js").read_text()
        styles = (Path(__file__).parents[1] / "control_center/styles.css").read_text()

        self.assertIn('budget.status === "exceeded"', javascript)
        self.assertIn("Approve exception and retry", javascript)
        self.assertIn("Protected QA", javascript)
        self.assertIn("retry-with-budget", javascript)
        self.assertIn("Regenerate QA tests and retry", javascript)
        self.assertIn("retry-reset-qa", javascript)
        self.assertIn('id="retry-reason"', javascript)
        self.assertIn("Latest retry reason", javascript)
        self.assertIn("why another attempt can succeed", javascript)
        self.assertIn("Why it stopped", javascript)
        self.assertIn("Proposed recovery", javascript)
        self.assertIn("Suggested retry reason", javascript)
        self.assertIn("Proposed ticket body", javascript)
        self.assertIn("Save ticket and retry", javascript)
        self.assertIn('action("save-ticket-and-retry"', javascript)
        self.assertIn("Reload issue and retry", javascript)
        self.assertIn("Reload contract and retry", javascript)
        self.assertIn("Release abandoned claim", javascript)
        self.assertIn('recoveryInfo.kind === "dependency"', javascript)
        self.assertIn('recoveryInfo.kind === "review_publication"', javascript)
        self.assertIn("Inspect reviewed pull request", javascript)
        self.assertIn("Do not retry:", javascript)
        self.assertIn('recoveryInfo.kind === "candidate_verification"', javascript)
        self.assertIn("Re-verify saved candidate", javascript)
        self.assertIn("Passing candidate preserved", javascript)
        self.assertIn('recoveryInfo.kind === "revision_rebuild"', javascript)
        self.assertIn("Rebuild and retry", javascript)
        self.assertIn("Create a replacement Ticket", javascript)
        self.assertIn(".recovery-panel", styles)
        self.assertIn(".recovery-guidance", styles)
        self.assertIn(".ticket-correction-editor", styles)

    def test_completed_application_ui_has_start_stop_and_copy_controls(self):
        html = (Path(__file__).parents[1] / "control_center/index.html").read_text()
        javascript = (Path(__file__).parents[1] / "control_center/app.js").read_text()
        styles = (Path(__file__).parents[1] / "control_center/styles.css").read_text()

        self.assertIn('id="start-app"', html)
        self.assertIn('id="stop-app"', html)
        self.assertIn('id="copy-run-command"', html)
        self.assertIn('action("start-app")', javascript)
        self.assertIn('operation.action === "start-app"', javascript)
        self.assertIn("The application is running. Open it", javascript)
        self.assertIn("Why it failed", html)
        self.assertIn("What to do", html)
        self.assertIn("operation.failure?.cause", javascript)
        self.assertIn(".operation-failure", styles)
        self.assertIn(".run-app-grid > .surface { min-width: 0;", styles)
        self.assertIn(
            ".run-app-grid { grid-template-columns: minmax(0,1fr); }",
            styles,
        )

    def test_periodic_snapshot_refresh_preserves_open_ticket_reader_position(self):
        javascript = (Path(__file__).parents[1] / "control_center/app.js").read_text()
        styles = (Path(__file__).parents[1] / "control_center/styles.css").read_text()

        self.assertIn("renderDrawer({ preservePosition: true })", javascript)
        self.assertIn("function captureDrawerPosition()", javascript)
        self.assertIn("function restoreDrawerPosition(position)", javascript)
        self.assertIn("drawerNearBottom", javascript)
        self.assertIn('$$("pre", content)', javascript)
        self.assertIn('$$("input, textarea, select", content)', javascript)
        self.assertIn("top: element.scrollTop", javascript)
        self.assertIn("field.scrollTop = saved.nearBottom", javascript)
        self.assertIn("field.scrollLeft = saved.left", javascript)
        self.assertIn("if (!preservePosition)", javascript)
        self.assertIn(".drawer > header { position: static;", styles)
        self.assertIn(".drawer-tabs { top: 0;", styles)

    def test_charter_selected_expert_gate_has_a_validated_control_center_action(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            self.write_plan_manifest(center, "a1b2c3d4", "mock")

            title, commands = center.build_commands("approve-stage", {
                "plan_id": "a1b2c3d4",
                "stage": "system_architecture",
            })

            self.assertEqual(title, "Approve System Architecture")
            self.assertEqual(
                commands[0][-4:],
                ["approve-stage", "architecture", "a1b2c3d4", "--yes"],
            )
            with self.assertRaisesRegex(InputError, "[Aa]rchitecture or program"):
                center.build_commands("approve-stage", {
                    "plan_id": "a1b2c3d4",
                    "stage": "vertical_slices",
                })

    def test_journey_names_a_charter_selected_intermediate_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            planning = {
                "plan_id": "a" * 12,
                "status": "awaiting_system_architecture_approval",
                "approvals": {"product": {"artifact_sha256": "a" * 64}},
                "stages": [],
            }

            journey = center.journey(
                planning, {"tickets": []}, {}, {"saved": True}, [],
            )

            self.assertEqual(journey["headline"], "System Architecture needs your approval")
            self.assertEqual(journey["next"]["label"], "Review System Architecture")
            self.assertEqual(journey["next"]["view"], "planning")

    def test_blocked_planning_can_retry_with_another_live_adapter(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            plan = "a" * 12
            self.write_plan_manifest(center, plan, "claude")

            title, commands = center.build_commands("continue-plan", {
                "plan_id": plan,
                "planning_agent": "codex",
            })

            self.assertEqual(title, "Run architecture and delivery planning")
            self.assertEqual(commands[0][-2:], ["--planning-agent", "codex"])
            with self.assertRaisesRegex(InputError, "Claude or Codex"):
                center.build_commands("continue-plan", {
                    "plan_id": plan,
                    "planning_agent": "cursor",
                })

    def test_blocked_expert_decisions_revise_the_stage_then_resume_planning(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            plan = "a" * 12
            self.write_plan_manifest(center, plan, "claude")

            title, commands = center.build_commands("revise-stage", {
                "plan_id": plan,
                "mode": "rehearsal",
                "stage": "system_architecture",
                "feedback": "Use this repository and keep analytics disabled for v1.",
            })

            self.assertEqual(title, "Resolve System Architecture decisions")
            self.assertEqual(len(commands), 2)
            self.assertEqual(commands[0][1:4], ["revise", plan, "architecture"])
            self.assertIn("--feedback-file", commands[0])
            self.assertEqual(commands[1][1:], ["continue-plan", plan])
            self.assertNotIn("--mock", commands[0])
            self.assertNotIn("--mock", commands[1])

            with self.assertRaisesRegex(InputError, "blocked technical"):
                center.build_commands("revise-stage", {
                    "plan_id": plan,
                    "stage": "product_review",
                    "feedback": "Answer",
                })

    def test_many_product_blocking_decisions_use_a_compact_feedback_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            plan = "a" * 12
            self.write_plan_manifest(center, plan, "claude")
            questions = [
                f"Question {index}: " + ("Clarify this product decision. " * 8)
                for index in range(1, 21)
            ]
            planning_state = center.repo / ".factory/planning-state.json"
            planning_state.write_text(json.dumps({
                "plan_id": plan,
                "status": "blocked",
                "stages": [{
                    "id": "product_review",
                    "status": "blocked",
                    "questions": questions,
                }],
            }))
            decisions = [
                f"Use the documented default for decision {index}."
                for index in range(1, 21)
            ]

            title, commands = center.build_commands("revise-product", {
                "plan_id": plan,
                "decisions": decisions,
            })

            feedback_path = Path(commands[0][commands[0].index("--feedback-file") + 1])
            feedback = feedback_path.read_text()
            self.assertEqual(title, "Revise Product Review")
            self.assertIn("1. Use the documented default for decision 1.", feedback)
            self.assertIn("20. Use the documented default for decision 20.", feedback)
            self.assertNotIn(questions[0], feedback)
            self.assertLess(len(feedback), 4000)

    def test_legacy_product_question_payload_has_room_for_normal_answers(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            plan = "a" * 12
            self.write_plan_manifest(center, plan, "claude")
            feedback = "\n".join(
                f"{index}. Question: {'Clarify this product decision. ' * 8}\n"
                f"Decision: Use the documented default for decision {index}."
                for index in range(1, 21)
            )

            title, commands = center.build_commands("revise-product", {
                "plan_id": plan,
                "feedback": feedback,
            })

            self.assertEqual(title, "Revise Product Review")
            self.assertIn("--feedback-file", commands[0])

    def test_reset_actions_are_rehearsal_only_and_full_reset_requires_a_phrase(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            (center.repo / "setup_demo.sh").write_text("#!/bin/sh\n")

            _, run_reset = center.build_commands("reset-run", {"mode": "rehearsal"})
            self.assertIn("--scenario", run_reset[0])
            self.assertNotIn("--start-over", run_reset[0])

            with self.assertRaisesRegex(InputError, "START OVER"):
                center.build_commands("reset-all", {"mode": "rehearsal"})
            _, full_reset = center.build_commands("reset-all", {
                "mode": "rehearsal", "confirm": "START OVER",
            })
            self.assertIn("--start-over", full_reset[0])

            with self.assertRaisesRegex(InputError, "fresh workshop repository"):
                center.build_commands("reset-run", {"mode": "live"})

            title, live_local_reset = center.build_commands("reset-run", {
                "mode": "live", "local_only": True, "scenario": "recipe-rebrand",
            })
            self.assertEqual(title, "Reset local Live Run state")
            self.assertIn("--scenario", live_local_reset[0])
            self.assertIn("--local-state-only", live_local_reset[0])

            _, live_local_start_over = center.build_commands("reset-all", {
                "mode": "live", "local_only": True,
                "scenario": "recipe-rebrand", "confirm": "START OVER",
            })
            self.assertIn("--start-over", live_local_start_over[0])

            title, recover = center.build_commands("recover-latest", {})
            self.assertEqual(title, "Recover latest Factory state")
            self.assertIn("recover", recover[0])
            self.assertIn("--yes", recover[0])

    def test_snapshot_exposes_latest_recovery_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            checkpoint = (
                center.repo
                / ".factory/recovery/checkpoints/20260826T100000Z-a1b2c3"
            )
            checkpoint.mkdir(parents=True)
            (checkpoint / "manifest.json").write_text(json.dumps({
                "schema_version": 1,
                "checkpoint_id": checkpoint.name,
                "kind": "reset",
                "created_at": "2026-08-26T10:00:00+00:00",
                "entries": ["state.json"],
                "mode": "live",
                "run_id": "run-1",
                "ticket_count": 6,
                "plan_id": "plan-1",
            }))

            recovery = center.snapshot()["recovery"]

            self.assertTrue(recovery["available"])
            self.assertEqual(recovery["source"], "checkpoint")
            self.assertEqual(recovery["checkpoint_id"], checkpoint.name)
            self.assertEqual(recovery["ticket_count"], 6)

    def test_snapshot_does_not_offer_an_older_checkpoint_over_current_state(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            runtime = center.repo / ".factory"
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "state.json").write_text(json.dumps({
                "updated_at": "2026-08-26T11:00:00+00:00",
                "tickets": [{"number": 4, "status": "Backlog"}],
            }))
            checkpoint = (
                runtime
                / "recovery/checkpoints/20260826T100000Z-a1b2c3"
            )
            payload = checkpoint / "runtime"
            payload.mkdir(parents=True)
            (payload / "state.json").write_text(json.dumps({
                "updated_at": "2026-08-26T10:00:00+00:00",
                "tickets": [{"number": 4, "status": "Ready"}],
            }))
            (checkpoint / "manifest.json").write_text(json.dumps({
                "schema_version": 1,
                "checkpoint_id": checkpoint.name,
                "kind": "reset",
                "created_at": "2026-08-26T10:05:00+00:00",
                "entries": ["state.json"],
                "mode": "live",
                "run_id": "run-1",
                "ticket_count": 1,
                "plan_id": "plan-1",
            }))

            recovery = center.snapshot()["recovery"]

            self.assertFalse(recovery["available"])
            self.assertEqual(recovery["source"], "current")

    def test_live_publication_reuses_the_saved_github_project(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            local = center.repo / ".factory/local.toml"
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_text("project_number = 42\n")
            self.write_plan_manifest(center, "a" * 12, "claude")

            _, commands = center.build_commands("publish-plan", {
                "plan_id": "a" * 12,
                "mode": "live",
                "project_title": "Ignored when a Project is connected",
            })

            self.assertIn("--project-number", commands[0])
            self.assertIn("42", commands[0])
            self.assertNotIn("--new-project-title", commands[0])

    def test_artifacts_cannot_escape_factory_evidence_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            log = center.repo / ".factory/logs/agent.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text("safe log\n")

            self.assertEqual(center.artifact(".factory/logs/agent.log"), "safe log\n")
            with self.assertRaisesRegex(InputError, "Invalid artifact path"):
                center.artifact("../private-key")
            with self.assertRaisesRegex(InputError, "Only factory evidence"):
                center.artifact(".factory/local.toml")

            private = center.repo / ".factory/local.toml"
            private.write_text("secret = 'not for the browser'\n")
            (center.repo / ".factory/logs/private-link").symlink_to(private)
            with self.assertRaisesRegex(InputError, "Artifact not found"):
                center.artifact(".factory/logs/private-link")

    def test_operation_runner_streams_an_allowlisted_command(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))

            operation = center.start("doctor", {"full": True})
            deadline = time.monotonic() + 2
            while center.operation_snapshot().get("status") == "running" and time.monotonic() < deadline:
                time.sleep(0.01)
            finished = center.operation_snapshot()

            self.assertEqual(operation["action"], "doctor")
            self.assertEqual(finished["status"], "succeeded")
            self.assertIn("factory args: doctor --full", finished["output"])

    def test_human_gates_can_unblock_a_running_factory_operation(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            factory = center.repo / "factory/factory"
            factory.write_text(
                "#!/bin/sh\n"
                "if [ \"$1\" = run ]; then\n"
                "  mkdir -p .factory/qa-approvals .factory/merged\n"
                "  while [ ! -f .factory/qa-approvals/1 ]; do sleep 0.05; done\n"
                "  while [ ! -f .factory/merged/1 ]; do sleep 0.05; done\n"
                "  exit 0\n"
                "fi\n"
                "if [ \"$1\" = approve-tests ]; then\n"
                "  mkdir -p .factory/qa-approvals\n"
                "  : > .factory/qa-approvals/\"$2\"\n"
                "  printf 'approved ticket %s\\n' \"$2\"\n"
                "  exit 0\n"
                "fi\n"
                "if [ \"$1\" = retry ]; then\n"
                "  printf 'retry queued for ticket %s\\n' \"$2\"\n"
                "  exit 0\n"
                "fi\n"
                "if [ \"$1\" = merge ]; then\n"
                "  mkdir -p .factory/merged\n"
                "  : > .factory/merged/\"$2\"\n"
                "  printf 'merged ticket %s\\n' \"$2\"\n"
                "  exit 0\n"
                "fi\n"
                "exit 2\n"
            )
            factory.chmod(0o755)

            center.start("run", {"mode": "rehearsal"})
            deadline = time.monotonic() + 2
            while center.process is None and time.monotonic() < deadline:
                time.sleep(0.01)

            with self.assertRaisesRegex(InputError, "Another factory operation"):
                center.start("doctor", {})
            approval = center.start("approve-tests", {"issue": 1})

            self.assertEqual(approval["companion"]["action"], "approve-tests")
            self.assertEqual(approval["companion"]["status"], "succeeded")
            retry = center.start("retry", {
                "issue": 4,
                "mode": "rehearsal",
                "reason": "Re-run the repaired verification gate",
            })
            self.assertEqual(retry["companion"]["action"], "retry")
            self.assertEqual(retry["companion"]["status"], "succeeded")
            merge = center.start("merge", {"issue": 1, "mode": "rehearsal"})

            self.assertEqual(merge["companion"]["action"], "merge")
            self.assertEqual(merge["companion"]["status"], "succeeded")
            deadline = time.monotonic() + 2
            while center.operation_snapshot().get("status") == "running" and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertEqual(center.operation_snapshot()["status"], "succeeded")

    def test_shutdown_stops_and_joins_an_active_factory_process(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            factory = center.repo / "factory/factory"
            factory.write_text("#!/bin/sh\nprintf 'started\\n'\nsleep 30\n")

            center.start("doctor", {})
            deadline = time.monotonic() + 2
            while center.process is None and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertIsNotNone(center.process)

            center.shutdown(timeout=2)

            self.assertIsNone(center.process)
            self.assertIsNone(center.worker)
            self.assertEqual(center.operation_snapshot()["status"], "stopped")

    def test_restart_recovers_an_operation_interrupted_while_stopping(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self.make_repo(directory)
            center = ControlCenter(repo)
            center.operation_path.write_text(json.dumps({"status": "stopping"}))

            recovered = ControlCenter(repo).operation_snapshot()

            self.assertEqual(recovered["status"], "interrupted")
            self.assertIn("restarted while this operation was running", recovered["error"])

    def test_http_api_serves_state_and_rejects_foreign_origins(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            server = ControlCenterServer(("127.0.0.1", 0), center)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                with urlopen(base + "/api/snapshot", timeout=2) as response:
                    snapshot = json.load(response)
                self.assertEqual(snapshot["repo"]["name"], Path(directory).name)

                request = Request(
                    base + "/api/prd",
                    data=json.dumps({"text": "# Safe PRD"}).encode(),
                    headers={"Content-Type": "application/json"},
                    method="PUT",
                )
                with urlopen(request, timeout=2) as response:
                    saved = json.load(response)
                self.assertTrue(saved["saved"])

                foreign = Request(base + "/api/snapshot", headers={"Origin": "https://example.com"})
                try:
                    urlopen(foreign, timeout=2)
                except HTTPError as error:
                    self.assertEqual(error.code, 400)
                    error.close()
                else:
                    self.fail("A foreign origin must not access the Control Center")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

    def test_snapshot_combines_planning_ticket_and_operation_state(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            project = ProjectContract.detect(center.repo)
            project.write()
            charter = FactoryCharter.draft(center.repo, project)
            charter.write()
            charter.approve()
            (center.repo / ".factory/planning-state.json").write_text(json.dumps({"plan_id": "abc12345"}))
            (center.repo / ".factory/state.json").write_text(json.dumps({"tickets": [{"number": 1, "status": "Done"}]}))
            supervisor = center.repo / ".factory/supervisor/state.json"
            supervisor.parent.mkdir(parents=True)
            supervisor.write_text(json.dumps({"status": "ready", "latest": {"id": "supervisor-1"}}))

            snapshot = center.snapshot()

            self.assertEqual(snapshot["planning"]["plan_id"], "abc12345")
            self.assertEqual(snapshot["factory"]["tickets"][0]["status"], "Done")
            self.assertIn("adapters", snapshot)
            self.assertIn("operation", snapshot)
            self.assertEqual(snapshot["supervisor"]["latest"]["id"], "supervisor-1")
            self.assertEqual(snapshot["journey"]["phase_label"], "Plan")

    def test_snapshot_classifies_each_blocked_ticket_for_the_recovery_ui(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            project = ProjectContract.detect(center.repo)
            project.write()
            charter = FactoryCharter.draft(center.repo, project)
            charter.write()
            charter.approve()
            (center.repo / ".factory/planning-state.json").write_text(json.dumps({
                "plan_id": "abc12345",
                "status": "published",
                "mode": "live",
            }))
            state = center.repo / ".factory/state.json"
            state.write_text(json.dumps({"tickets": [
                {
                    "number": 5,
                    "title": "Complete the workflow",
                    "status": "Blocked",
                    "phase": "triage",
                    "failure": "Add a Spec and an observable Acceptance criterion.",
                    "history": [],
                },
                {
                    "number": 6,
                    "title": "Bound the implementation",
                    "status": "Blocked",
                    "phase": "verifying",
                    "failure": "DIFF_BUDGET_EXCEEDED: implementation is too large.",
                    "history": [],
                },
            ]}))

            snapshot = center.snapshot()

            tickets = {
                ticket["number"]: ticket
                for ticket in snapshot["factory"]["tickets"]
            }
            self.assertEqual(
                tickets[5]["recovery"]["action"], "edit_ticket_and_retry",
            )
            self.assertEqual(
                tickets[5]["next_human_action"], "edit_ticket_and_retry",
            )
            self.assertEqual(
                tickets[5]["recovery"]["cause"],
                "Add a Spec and an observable Acceptance criterion.",
            )
            self.assertIn(
                "observable Acceptance criteria",
                tickets[5]["recovery"]["solution"],
            )
            self.assertEqual(
                tickets[6]["recovery"]["action"], "approve_budget_or_split",
            )
            self.assertFalse(tickets[6]["recovery"]["retry_allowed"])
            decision = next(
                item for item in snapshot["decisions"]
                if item.get("ticket", {}).get("number") == 5
            )
            self.assertEqual(
                decision["ticket"]["recovery"]["kind"],
                "ticket_specification",
            )
            self.assertEqual(
                snapshot["journey"]["next"]["detail"],
                tickets[5]["recovery"]["summary"],
            )

    def test_snapshot_uses_the_plan_manifest_as_the_authoritative_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            plan = "a" * 12
            self.write_plan_manifest(center, plan, "claude")
            (center.repo / ".factory/planning-state.json").write_text(json.dumps({
                "plan_id": plan,
                "mode": "rehearsal",
            }))

            planning = center.snapshot()["planning"]

            self.assertEqual(planning["planning_agent"], "claude")
            self.assertEqual(planning["mode"], "live")

    def test_blocked_approved_planning_exposes_a_retry_path(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            planning = {
                "plan_id": "abc12345",
                "status": "blocked",
                "approvals": {"product": {"approved_at": "now"}, "alignment": None},
                "stages": [
                    {"id": "product_review", "status": "complete"},
                    {"id": "system_architecture", "status": "complete"},
                    {
                        "id": "program_design",
                        "title": "Program Design",
                        "status": "blocked",
                        "failure_kind": "agent",
                        "error": "The adapter process exited unexpectedly.",
                    },
                    {"id": "vertical_slices", "status": "pending"},
                ],
            }
            failed_publication = {
                "status": "failed",
                "action": "publish-plan",
                "title": "Publish tickets to GitHub",
                "error": "The operation failed.",
            }

            journey = center.journey(
                planning, {"tickets": []}, failed_publication,
                {"saved": True}, [],
            )

            self.assertEqual(journey["phase_label"], "Plan")
            self.assertEqual(journey["next"]["view"], "planning")
            self.assertEqual(journey["next"]["label"], "Open expert recovery")

            planning_state = center.repo / ".factory/planning-state.json"
            planning_state.write_text(json.dumps(planning))
            snapshot = center.snapshot()
            self.assertFalse(snapshot["planning"]["can_continue"])
            self.assertEqual(snapshot["planning"]["continue_label"], "Open recovery options")

    def test_blocking_questions_require_control_center_decisions_instead_of_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            planning = {
                "plan_id": "abc12345",
                "status": "blocked",
                "approvals": {"product": {"approved_at": "now"}, "alignment": None},
                "stages": [
                    {"id": "product_review", "title": "Product Review", "status": "complete", "questions": []},
                    {"id": "system_architecture", "title": "System Architecture", "status": "blocked", "questions": ["Where does it live?"]},
                    {"id": "program_design", "title": "Program Design", "status": "pending", "questions": []},
                    {"id": "vertical_slices", "title": "Vertical Slices", "status": "pending", "questions": []},
                ],
            }
            (center.repo / ".factory/planning-state.json").write_text(json.dumps(planning))

            snapshot = center.snapshot()
            journey = center.journey(
                planning,
                {"tickets": []},
                {"status": "failed", "action": "continue-plan"},
                {"saved": True},
                [],
            )

            self.assertFalse(snapshot["planning"]["can_continue"])
            self.assertTrue(snapshot["planning"]["requires_decisions"])
            self.assertEqual(snapshot["planning"]["blocked_stage"], "system_architecture")
            self.assertEqual(snapshot["planning"]["failed_stage"], "")
            self.assertEqual(snapshot["planning"]["recovery"], {})
            self.assertEqual(snapshot["planning"]["continue_label"], "Answer expert questions")
            self.assertEqual(
                snapshot["factory"]["human_attention"]["planning_questions"], 1,
            )
            self.assertEqual(
                snapshot["factory"]["human_attention"]["awaiting_human"], 1,
            )
            self.assertEqual(journey["headline"], "System Architecture is waiting for you")
            self.assertEqual(journey["next"]["label"], "Answer blocked questions")

    def test_snapshot_centralizes_planning_state_presentation_for_every_caller(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            planning = {
                "plan_id": "abc12345",
                "status": "awaiting_system_architecture_approval",
                "approvals": {
                    "product": {"approved_at": "now"},
                    "system_architecture": None,
                    "alignment": None,
                },
                "governance": {
                    "planning_approvals": [
                        "product_review",
                        "system_architecture",
                        "alignment",
                    ],
                },
                "stages": [
                    {"id": "product_review", "title": "Product Review", "status": "complete"},
                    {"id": "system_architecture", "title": "System Architecture", "status": "complete"},
                    {"id": "program_design", "title": "Program Design", "status": "pending"},
                    {"id": "vertical_slices", "title": "Vertical Slices", "status": "pending"},
                ],
            }
            (center.repo / ".factory/planning-state.json").write_text(json.dumps(planning))

            snapshot = center.snapshot()
            presentation = snapshot["planning"]["presentation"]

            self.assertEqual(presentation["state"], "system_architecture_approval")
            self.assertEqual(presentation["continue_label"], "Review System Architecture")
            self.assertEqual(presentation["selected_stage"], "system_architecture_gate")
            self.assertEqual(
                presentation["decision"],
                {
                    "kind": "approval",
                    "title": "Approve System Architecture",
                    "text": "Confirm the exact expert artifact before downstream planning continues.",
                    "view": "planning",
                    "planning": "system_architecture_gate",
                    "queue_status": "System Architecture Review",
                    "queue_kind": "approval",
                },
            )
            self.assertEqual(
                [item["id"] for item in presentation["sequence"]],
                [
                    "product_review",
                    "product_review_gate",
                    "system_architecture",
                    "system_architecture_gate",
                    "program_design",
                    "vertical_slices",
                    "alignment_gate",
                ],
            )
            journey = center.journey(
                snapshot["planning"],
                snapshot["factory"],
                {"status": "idle"},
                {"saved": True},
                [],
            )
            self.assertEqual(journey["headline"], "System Architecture needs your approval")
            self.assertEqual(
                snapshot["factory"]["human_attention"]["oldest"]["status"],
                "System Architecture Review",
            )

    def test_paused_planning_decision_routes_to_the_exact_planning_gate_once(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            planning = {
                "plan_id": "abc12345",
                "status": "awaiting_product_approval",
                "updated_at": "2026-08-24T12:00:00+00:00",
                "approvals": {"product": None, "alignment": None},
                "stages": [{
                    "id": "product_review",
                    "title": "Product Review",
                    "status": "complete",
                    "questions": [],
                }],
            }
            (center.repo / ".factory/planning-state.json").write_text(json.dumps(planning))
            charter = {
                "configured": True,
                "approved": True,
                "max_awaiting_human_review": 1,
                "max_blocked_for_human": 2,
                "oldest_review_hours": 24,
            }

            with patch.object(center, "factory_charter", return_value=charter):
                snapshot = center.snapshot()

            self.assertTrue(snapshot["factory"]["human_attention"]["dispatch_paused"])
            self.assertEqual(len(snapshot["decisions"]), 1)
            decision = snapshot["decisions"][0]
            self.assertEqual(decision["title"], "NEEDS YOU · Dispatch paused")
            self.assertEqual(decision["view"], "planning")
            self.assertEqual(decision["planning"], "product_review_gate")

    def test_validation_failure_exposes_rejected_artifact_and_guided_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            planning = {
                "plan_id": "abc12345",
                "status": "blocked",
                "approvals": {"product": {"approved_at": "now"}, "alignment": None},
                "stages": [
                    {"id": "product_review", "title": "Product Review", "status": "complete", "questions": []},
                    {"id": "system_architecture", "title": "System Architecture", "status": "complete", "questions": []},
                    {"id": "program_design", "title": "Program Design", "status": "complete", "questions": []},
                    {
                        "id": "vertical_slices",
                        "title": "Vertical Slices",
                        "status": "blocked",
                        "questions": [],
                        "failure_kind": "validation",
                        "error": "T1 references unknown IDs: C1",
                        "validation_error": "T1 references unknown IDs: C1",
                        "rejected_artifact": ".factory/plans/abc12345/rejected/vertical_slices-attempt-1.json",
                    },
                ],
            }
            (center.repo / ".factory/planning-state.json").write_text(json.dumps(planning))

            snapshot = center.snapshot()
            journey = center.journey(
                planning,
                {"tickets": []},
                {"status": "failed", "action": "continue-plan"},
                {"saved": True},
                [],
            )

            self.assertEqual(snapshot["planning"]["failed_stage"], "vertical_slices")
            self.assertFalse(snapshot["planning"]["can_continue"])
            self.assertTrue(snapshot["planning"]["requires_correction"])
            self.assertEqual(
                snapshot["planning"]["continue_label"],
                "Enter a correction for Vertical Slices",
            )
            self.assertEqual(journey["headline"], "Vertical Slices failed validation")
            self.assertIn("T1 references unknown IDs: C1", journey["detail"])
            self.assertEqual(journey["next"]["view"], "planning")
            self.assertIn("with correction", journey["next"]["label"])

    def test_provider_capacity_failure_disables_blind_retry_and_offers_adapter_switch(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            plan = "a" * 12
            self.write_plan_manifest(center, plan, "claude")
            planning = {
                "plan_id": plan,
                "status": "blocked",
                "approvals": {"product": {"approved_at": "now"}, "alignment": None},
                "stages": [
                    {"id": "product_review", "title": "Product Review", "status": "complete", "questions": []},
                    {
                        "id": "system_architecture",
                        "title": "System Architecture",
                        "status": "blocked",
                        "questions": [],
                        "failure_kind": "agent",
                        "error": "You've hit your session limit · resets 2:40pm (Europe/London)",
                    },
                ],
            }
            (center.repo / ".factory/planning-state.json").write_text(json.dumps(planning))

            snapshot = center.snapshot()

            self.assertFalse(snapshot["planning"]["can_continue"])
            self.assertEqual(snapshot["planning"]["continue_label"], "Open recovery options")
            self.assertEqual(snapshot["planning"]["recovery"]["kind"], "provider_capacity")
            self.assertFalse(snapshot["planning"]["recovery"]["retry_same_adapter"])
            self.assertIn("codex", snapshot["planning"]["recovery"]["alternative_adapters"])
            journey = center.journey(
                {**planning, "planning_agent": "claude"},
                {"tickets": []},
                {"status": "failed", "action": "continue-plan"},
                {"saved": True},
                [],
            )
            self.assertEqual(journey["next"]["label"], "Switch planning adapter or wait")

    def test_unknown_agent_failure_has_an_explicit_same_adapter_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            plan = "b" * 12
            self.write_plan_manifest(center, plan, "claude")
            planning = {
                "plan_id": plan,
                "status": "blocked",
                "approvals": {"product": {"approved_at": "now"}, "alignment": None},
                "stages": [
                    {"id": "product_review", "title": "Product Review", "status": "complete", "questions": []},
                    {
                        "id": "system_architecture",
                        "title": "System Architecture",
                        "status": "blocked",
                        "questions": [],
                        "failure_kind": "agent",
                        "error": "The agent process exited unexpectedly.",
                    },
                ],
            }
            (center.repo / ".factory/planning-state.json").write_text(json.dumps(planning))

            snapshot = center.snapshot()

            self.assertFalse(snapshot["planning"]["can_continue"])
            self.assertEqual(snapshot["planning"]["recovery"]["kind"], "agent_process")
            self.assertTrue(snapshot["planning"]["recovery"]["retry_same_adapter"])
            self.assertEqual(snapshot["planning"]["continue_label"], "Open recovery options")

    def test_repeated_agent_failure_stops_blind_retry_and_recommends_a_switch(self):
        recovery = planning_recovery(
            {
                "id": "system_architecture",
                "status": "blocked",
                "failure_kind": "agent",
                "failure_count": 2,
                "error": "The agent process exited unexpectedly.",
            },
            "claude",
            ["claude", "codex"],
        )

        self.assertEqual(recovery["kind"], "repeated_agent_failure")
        self.assertEqual(recovery["recommended_action"], "switch_adapter")
        self.assertEqual(recovery["recommended_adapter"], "codex")
        self.assertEqual(recovery["attempts"], 2)
        self.assertFalse(recovery["retry_same_adapter"])
        self.assertIn("failed 2 times", recovery["summary"])

    def test_stale_governance_requires_a_control_center_replan_instead_of_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            project = ProjectContract.detect(center.repo)
            project.write()
            charter = FactoryCharter.draft(center.repo, project)
            charter.write()
            charter.approve()
            center.prd_path.parent.mkdir(parents=True, exist_ok=True)
            center.prd_path.write_text("# Current PRD\n")
            plan = "a" * 12
            self.write_plan_manifest(center, plan, "claude")
            planning = {
                "plan_id": plan,
                "status": "stale_factory_charter",
                "approvals": {"product": None, "alignment": None},
                "stages": [
                    {
                        "id": "product_review",
                        "title": "Product Review",
                        "status": "complete",
                        "questions": [],
                    },
                    {
                        "id": "system_architecture",
                        "title": "System Architecture",
                        "status": "blocked",
                        "questions": [],
                        "failure_kind": "agent",
                        "error": "Planning Run predates Factory Charter governance",
                    },
                ],
            }
            (center.repo / ".factory/planning-state.json").write_text(json.dumps(planning))

            snapshot = center.snapshot()

            self.assertTrue(snapshot["planning"]["requires_replan"])
            self.assertFalse(snapshot["planning"]["can_continue"])
            self.assertEqual(
                snapshot["planning"]["continue_label"],
                "Restart planning with current governance",
            )
            self.assertEqual(snapshot["journey"]["headline"], "Planning governance changed")
            self.assertEqual(snapshot["journey"]["next"]["label"], "Restart planning safely")
            self.assertEqual(snapshot["journey"]["next"]["view"], "planning")

    def test_restart_plan_preserves_the_prd_and_live_planning_adapter(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            center.prd_path.parent.mkdir(parents=True, exist_ok=True)
            center.prd_path.write_text("# Current PRD\n")
            plan = "a" * 12
            self.write_plan_manifest(center, plan, "claude")
            (center.repo / ".factory/planning-state.json").write_text(json.dumps({
                "plan_id": plan,
                "status": "stale_factory_charter",
            }))

            title, commands = center.build_commands("restart-plan", {"plan_id": plan})

            self.assertEqual(title, "Restart planning with current governance")
            self.assertEqual(commands[0][1:3], ["plan", str(center.prd_path)])
            self.assertIn("--planning-agent", commands[0])
            self.assertIn("claude", commands[0])
            self.assertNotIn("--mock", commands[0])

    def test_restart_plan_rejects_a_non_stale_planning_run(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            center.prd_path.parent.mkdir(parents=True, exist_ok=True)
            center.prd_path.write_text("# Current PRD\n")
            plan = "a" * 12
            self.write_plan_manifest(center, plan, "claude")
            (center.repo / ".factory/planning-state.json").write_text(json.dumps({
                "plan_id": plan,
                "status": "blocked",
            }))

            with self.assertRaisesRegex(InputError, "does not require a full restart"):
                center.build_commands("restart-plan", {"plan_id": plan})

    def test_published_plan_never_advertises_a_blocked_expert_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            planning = {
                "plan_id": "abc12345",
                "status": "published",
                "approvals": {
                    "product": {"approved_at": "now"},
                    "alignment": {"approved_at": "now"},
                },
                "stages": [
                    {"id": "product_review", "status": "complete", "questions": []},
                    {"id": "system_architecture", "status": "complete", "questions": []},
                    {"id": "program_design", "status": "complete", "questions": []},
                    {"id": "vertical_slices", "status": "complete", "questions": []},
                ],
            }
            (center.repo / ".factory/planning-state.json").write_text(json.dumps(planning))
            run_dir = center.repo / ".factory/plans/abc12345"
            run_dir.mkdir(parents=True)
            (run_dir / "04-vertical-slices.json").write_text(json.dumps({
                "tickets": [
                    {"key": "ONE", "title": "First ticket", "agent": "codex", "dependencies": []},
                    {"key": "TWO", "title": "Second ticket", "agent": "codex", "dependencies": ["ONE"]},
                ],
                "publication": {
                    "repository": "attendee/project",
                    "project_number": 15,
                    "issues": {"ONE": 1, "TWO": 2},
                },
            }))

            snapshot = center.snapshot()

            self.assertFalse(snapshot["planning"]["can_continue"])
            self.assertEqual(snapshot["planning"]["continue_label"], "Planning complete")
            self.assertFalse(snapshot["planning"]["failed_stage"])
            self.assertEqual(snapshot["planning"]["publication"]["ticket_count"], 2)
            self.assertEqual(snapshot["planning"]["publication"]["project_number"], 15)
            self.assertEqual(
                snapshot["planning"]["publication"]["tickets"][1]["dependencies"],
                [1],
            )
            self.assertEqual(
                snapshot["planning"]["publication"]["tickets"][1]["url"],
                "https://github.com/attendee/project/issues/2",
            )

    def test_alignment_approved_live_plan_offers_duplicate_safe_publication_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            planning = {
                "plan_id": "abc12345",
                "mode": "live",
                "status": "alignment_approved",
                "approvals": {
                    "product": {"approved_at": "now"},
                    "alignment": {"approved_at": "now"},
                },
                "stages": [
                    {"id": "product_review", "status": "complete", "questions": []},
                    {"id": "system_architecture", "status": "complete", "questions": []},
                    {"id": "program_design", "status": "complete", "questions": []},
                    {"id": "vertical_slices", "status": "complete", "questions": []},
                ],
            }
            (center.repo / ".factory/planning-state.json").write_text(json.dumps(planning))

            snapshot = center.snapshot()
            journey = center.journey(
                snapshot["planning"],
                {"tickets": [{"number": 1, "status": "Backlog"}]},
                {"status": "idle"},
                {"saved": True},
                [],
                config={"preset": "codex-workshop"},
                project={"configured": True, "valid": True, "committed": True},
                charter={"approved": True},
            )

        self.assertEqual(snapshot["planning"]["presentation"]["state"], "publication_pending")
        self.assertEqual(
            snapshot["planning"]["presentation"]["continue_label"],
            "Retry ticket publication",
        )
        self.assertEqual(
            journey["next"]["label"],
            "Retry ticket publication",
        )
        javascript = (Path(__file__).parents[1] / "control_center/app.js").read_text()
        self.assertIn('"awaiting_alignment_approval", "alignment_approved"', javascript)
        self.assertIn("Retrying reuses any plan-marked GitHub issues", javascript)

    def test_lean_snapshot_marks_supervisor_disabled_before_a_run(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            local = center.repo / ".factory/local.toml"
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_text('profile = "lean"\n')

            snapshot = center.snapshot()

            self.assertEqual(snapshot["supervisor"]["status"], "disabled")

    def test_journey_names_the_active_role_and_human_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            planning = {
                "plan_id": "abc12345",
                "status": "alignment_approved",
                "approvals": {"product": {"at": "now"}, "alignment": {"at": "now"}},
            }
            prd = {"saved": True}
            active_factory = {"tickets": [{
                "number": 3, "title": "Recipe details", "status": "In Progress",
                "phase": "qa", "qa_attempt": 1,
            }]}
            running = {"status": "running", "action": "run", "title": "Run the factory"}

            active = center.journey(planning, active_factory, running, prd, [])
            self.assertEqual(active["phase_label"], "Build & verify")
            self.assertEqual(active["ticket"], 3)
            self.assertIn("Independent QA", active["headline"])

            active_factory["tickets"][0]["status"] = "QA Review"
            review = center.journey(planning, active_factory, running, prd, [])
            self.assertEqual(review["state"], "attention")
            self.assertIn("need approval", review["headline"])
            self.assertEqual(review["next"]["view"], "tickets")

            active_factory["tickets"].append({
                "number": 4, "title": "Ready slice", "status": "Ready",
            })
            active_factory["human_attention"] = {
                "dispatch_paused": True,
                "reason": "human review queue 3 / limit 3",
                "oldest": {"ticket": 3, "status": "QA Review"},
            }
            paused = center.journey(planning, active_factory, {}, prd, [])
            self.assertEqual(paused["headline"], "NEEDS YOU — new dispatch is paused")
            self.assertIn("queue 3 / limit 3", paused["detail"])
            self.assertEqual(paused["ticket"], 3)

            active_factory["human_attention"] = {
                "dispatch_paused": True,
                "reason": "human decision queue 3 / limit 3",
                "oldest": {
                    "ticket": None,
                    "plan_id": "abc12345",
                    "status": "Product Review",
                },
            }
            planning_paused = center.journey(planning, active_factory, {}, prd, [])
            self.assertEqual(planning_paused["next"]["view"], "planning")
            self.assertIn("Product Review", planning_paused["next"]["label"])

    def test_control_center_can_release_only_a_recorded_live_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            center = ControlCenter(self.make_repo(directory))
            title, commands = center.build_commands("release-claim", {
                "mode": "live",
                "issue": 8,
                "owner_run_id": "run-owner-1",
                "reason": "Operator confirmed the runner was abandoned",
            })

            self.assertEqual(title, "Release abandoned claim for ticket #8")
            self.assertIn("release-claim", commands[0])
            self.assertIn("--owner-run-id", commands[0])
            self.assertIn("run-owner-1", commands[0])
            self.assertIn("--yes", commands[0])

    def test_frontend_contains_the_complete_operator_workflow(self):
        frontend = Path(__file__).parents[1] / "control_center"
        source = (frontend / "index.html").read_text()
        javascript = (frontend / "app.js").read_text()
        backend = (Path(__file__).parents[1] / "control_center.py").read_text()

        for label in (
            "Connect the factory",
            "Define the outcome",
            "Review the plan",
            "Operate the factory",
            "Run the completed app",
            "Live log",
            "Diff",
            "Start the server",
            "Current phase",
            "Reset or start again",
            "Start workshop over",
            "System health",
            "Needs your decision",
            "Activity and CLI output",
            "Active lanes",
            "All lanes",
            "Supervisor",
            "Handoff Receipts",
            "GitHub repository URL",
            "Monitor repository health",
            "Read-only by contract",
            "Needs review",
            "Seed the guided Pocket Cinema starter",
        ):
            self.assertIn(label, source)

        self.assertIn(
            "Factory runtime and workshop documentation stay in this control checkout",
            source,
        )
        self.assertIn("app.selectedPlanning !== selectedId", javascript)
        self.assertNotIn("app.selectedPlanning === id", javascript)
        self.assertIn("planning.presentation?.selected_stage", javascript)
        self.assertIn("if (item.planning)", javascript)
        self.assertNotIn('id="planning-profile"', source)
        self.assertIn('id="connect-mode"', source)
        self.assertIn('full: mode() === "live"', javascript)
        self.assertIn("planning.can_continue", javascript)
        self.assertIn("planning.presentation?.continue_label", javascript)
        self.assertIn("const decisions = data.decisions || [];", javascript)
        self.assertNotIn("planning.presentation?.decision", javascript)
        self.assertIn("planning.presentation?.sequence", javascript)
        self.assertNotIn("planning.status === `awaiting_${stage}_approval`", javascript)
        self.assertIn("renderExpertPanel", javascript)
        self.assertIn("Answer every blocking question", javascript)
        self.assertIn('action(actionName, { stage: item.id, decisions: answers })', javascript)
        self.assertNotIn("Question: ${question}", javascript)
        self.assertIn('id="planning-recovery-feedback"', javascript)
        self.assertIn("Apply correction and continue", javascript)
        self.assertIn("Switch adapter and continue", javascript)
        self.assertIn("Fix with", javascript)
        self.assertIn("Same-adapter retry disabled", javascript)
        self.assertIn("Retry same adapter", javascript)
        self.assertIn('action("revise-stage", { stage: item.id, feedback })', javascript)
        self.assertIn("Restart planning safely", javascript)
        self.assertIn('action("restart-plan")', javascript)
        self.assertIn("Causal acceptance evidence", javascript)
        self.assertIn("RED NOT PROVED", javascript)
        self.assertIn("GREEN NOT PROVED", javascript)
        self.assertIn("NEEDS YOU · Dispatch paused", backend)
        self.assertIn("Release abandoned claim", javascript)
        self.assertIn("Merge exact revision", javascript)
        self.assertIn("mergeState.allowed", javascript)
        self.assertIn("Live pull request is missing", javascript)
        self.assertIn("data-open-ticket-reset", javascript)
        self.assertIn('id="recover-latest"', source)
        self.assertIn('action("recover-latest")', javascript)
        self.assertIn("Current local Factory state will be saved as an undo checkpoint", javascript)
        self.assertIn("No local checkpoint is available", javascript)
        self.assertIn('action("merge", { issue: ticket.number })', javascript)
        self.assertIn("renderMonitor", javascript)
        self.assertIn("finding.summary || finding.title || finding.id", javascript)
        self.assertIn("payload.mode = mode()", javascript)
        self.assertIn('setSignal("#system-operation"', javascript)
        self.assertIn('setConnection("reconnecting")', javascript)
        self.assertIn("syncOperationPolling(data.operation || {})", javascript)
        self.assertIn("window.setInterval(() => refreshSnapshot(), 1500)", javascript)
        self.assertIn('document.addEventListener("visibilitychange"', javascript)
        self.assertIn('planning.project || "Factory Delivery"', javascript)
        self.assertNotIn('project_title: "TableStory Workshop"', javascript)
        self.assertIn("approved ${publishedCount === 1", javascript)
        self.assertIn("Run one cycle to load the tickets", javascript)
        self.assertIn('status: ticket.dependencies?.length ? "Backlog" : "Ready"', javascript)
        self.assertIn('phase: "Published"', javascript)
        self.assertIn('target="_blank" rel="noreferrer"', javascript)
        self.assertIn('id="ticket-load-state"', source)
        self.assertIn('localStorage.setItem("factory-board-mode"', javascript)
        self.assertIn('["running", "stopping", "failed"].includes(status)', javascript)

    def test_ticket_board_headers_stay_in_flow_and_cards_are_contained(self):
        frontend = Path(__file__).parents[1] / "control_center"
        stylesheet = (frontend / "styles.css").read_text()
        javascript = (frontend / "app.js").read_text()

        self.assertIn("grid-auto-columns: minmax(248px,280px)", stylesheet)
        self.assertIn(".ticket-column > header { position: relative;", stylesheet)
        self.assertNotIn(".ticket-column > header { position: sticky;", stylesheet)
        self.assertIn(".ticket-card { display: block; width: 100%; min-width: 0;", stylesheet)
        self.assertIn("No tickets in this state", javascript)

    def test_simplified_control_center_prioritizes_one_operator_workflow(self):
        frontend = Path(__file__).parents[1] / "control_center"
        source = (frontend / "index.html").read_text()
        javascript = (frontend / "app.js").read_text()
        styles = (frontend / "styles.css").read_text()

        for label in ("Setup", "Plan", "Deliver", "Review", "More tools"):
            self.assertIn(label, source)
        self.assertIn('class="workflow-nav"', source)
        self.assertIn('href="./styles.css"', source)
        self.assertIn('src="./app.js"', source)
        self.assertIn("Advanced role settings", source)
        self.assertIn("Your draft saves automatically", source)
        self.assertNotIn('id="global-next"', source)
        self.assertNotIn('id="open-reset-overview"', source)
        self.assertNotIn('id="command-help"', source)
        self.assertNotIn('id="save-prd"', source)
        self.assertNotIn('id="planning-mode"', source)
        self.assertIn("function schedulePrdSave()", javascript)
        self.assertIn('$("#attention-surface").hidden = decisions.length === 0', javascript)
        self.assertIn('$("#continue-plan").hidden = !planning.can_continue', javascript)
        self.assertIn("grid-template-columns: repeat(4,1fr)", styles)

    def test_factory_progress_pulses_only_the_current_running_phase(self):
        frontend = Path(__file__).parents[1] / "control_center"
        source = (frontend / "index.html").read_text()
        javascript = (frontend / "app.js").read_text()
        styles = (frontend / "styles.css").read_text()

        self.assertIn(">Delivery trace<", source)
        self.assertNotIn(">Workshop progress<", source)
        self.assertIn(
            'journey.state === "running" && phase.status === "current"',
            javascript,
        )
        self.assertIn('${isRunning ? " running" : ""}', javascript)
        self.assertIn(".journey-step.running i", styles)
        self.assertIn("@keyframes active-phase-pulse", styles)
        self.assertIn(
            ".journey-step.running i, .now-pulse.running, .signal-dot.live, .operation-surface.running .operation-summary-mark { animation: none; }",
            styles,
        )


if __name__ == "__main__":
    unittest.main()
