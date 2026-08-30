import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "deploy" / "aws" / "factory-cloud"


class AwsLifecycleContractTests(unittest.TestCase):
    def read(self, relative_path: str) -> str:
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def test_help_documents_every_cost_state(self):
        result = subprocess.run(
            [str(SCRIPT), "--help"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("pause", result.stdout)
        self.assertIn("resume", result.stdout)
        self.assertIn("destroy", result.stdout)
        self.assertIn("destroy --all", result.stdout)
        self.assertIn("ALB and storage remain", result.stdout)

    def test_pause_and_resume_wait_for_a_stable_service(self):
        script = self.read("deploy/aws/factory-cloud")

        self.assertIn("--desired-count 0", script)
        self.assertIn("--desired-count 1", script)
        self.assertEqual(script.count("ecs wait services-stable"), 2)

    def test_destructive_paths_require_exact_interactive_confirmation(self):
        script = self.read("deploy/aws/factory-cloud")

        self.assertIn('confirm_exactly "delete ${factory_stack}"', script)
        self.assertIn('confirm_exactly "delete ${factory_domain}"', script)
        self.assertIn("Interactive confirmation is required", script)
        self.assertNotIn("--yes", script)

    def test_full_teardown_removes_every_factory_billing_anchor(self):
        script = self.read("deploy/aws/factory-cloud")

        self.assertIn("delete_efs_and_backups", script)
        self.assertIn("delete-recovery-point", script)
        self.assertIn('delete_stack_if_present "${registry_stack}"', script)
        self.assertIn("secretsmanager delete-secret", script)
        self.assertIn("acm delete-certificate", script)
        self.assertIn("route53 delete-hosted-zone", script)
        self.assertIn('delete_stack_if_present "${bootstrap_stack}"', script)
        self.assertIn("disable_autodeploy", script)

    def test_runtime_stack_retains_workspace_for_normal_destroy(self):
        template = self.read("deploy/aws/factory.yaml")

        self.assertIn("DeletionPolicy: Retain", template)
        self.assertIn("UpdateReplacePolicy: Retain", template)
        self.assertIn('echo "Runtime removed. Retained EFS workspace:', self.read("deploy/aws/factory-cloud"))


if __name__ == "__main__":
    unittest.main()
