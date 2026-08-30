import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class AwsAutodeployContractTests(unittest.TestCase):
    def read(self, relative_path: str) -> str:
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def test_workflow_is_exact_branch_oidc_deployment(self):
        workflow = self.read(".github/workflows/deploy-aws-factory.yml")

        self.assertIn("- codex/feat-aws-github-cloud", workflow)
        self.assertIn("id-token: write", workflow)
        self.assertIn("contents: read", workflow)
        self.assertNotIn("pull_request_target", workflow)
        self.assertNotIn("AWS_ACCESS_KEY_ID", workflow)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", workflow)
        self.assertIn("bash deploy/aws/deploy.sh", workflow)
        self.assertIn("cancel-in-progress: false", workflow)

    def test_bootstrap_trust_is_exact_and_audience_bound(self):
        template = self.read("deploy/aws/github-autodeploy.yaml")

        self.assertIn(
            "token.actions.githubusercontent.com:aud: sts.amazonaws.com",
            template,
        )
        self.assertIn(
            "token.actions.githubusercontent.com:sub: !Ref GitHubOidcSubject",
            template,
        )
        self.assertIn(
            "repo:giolaq/software-refactory-workshop:ref:refs/heads/codex/feat-aws-github-cloud",
            template,
        )
        self.assertNotIn("repo:*", template)
        self.assertIn("iam:PassedToService: cloudformation.amazonaws.com", template)

    def test_deploy_script_keeps_cloudformation_role_optional(self):
        script = self.read("deploy/aws/deploy.sh")

        self.assertIn('if [[ -n "${AWS_CLOUDFORMATION_ROLE_ARN:-}" ]]', script)
        self.assertIn("cloudformation_deploy()", script)
        self.assertEqual(script.count("cloudformation_deploy \\"), 2)
        self.assertNotIn("cloudformation_role_args", script)

    def test_capacity_override_is_optional_and_shared_by_both_paths(self):
        deploy_script = self.read("deploy/aws/deploy.sh")
        setup_script = self.read("deploy/aws/setup-autodeploy.sh")
        workflow = self.read(".github/workflows/deploy-aws-factory.yml")

        for name in ("FACTORY_TASK_CPU", "FACTORY_TASK_MEMORY"):
            self.assertIn(f'if [[ -n "${{{name}:-}}" ]]', deploy_script)
            self.assertIn(f'set_variable {name} "${{{name}}}"', setup_script)
            self.assertIn(f"{name}: ${{{{ vars.{name} }}}}", workflow)

    def test_ecr_image_uses_a_single_compatible_manifest(self):
        script = self.read("deploy/aws/deploy.sh")

        self.assertIn("docker build --platform linux/amd64", script)
        self.assertIn("--provenance=false", script)

    def test_setup_publishes_identifiers_without_reading_secret_values(self):
        script = self.read("deploy/aws/setup-autodeploy.sh")

        self.assertIn("gh variable set", script)
        self.assertIn("GITHUB_TOKEN_SECRET_ARN", script)
        self.assertNotIn("get-secret-value", script)
        self.assertNotIn("gh secret set", script)
        self.assertIn("/protection", script)
        self.assertNotIn("set_variable GITHUB_", script)
        self.assertIn("set_variable FACTORY_GITHUB_TOKEN_SECRET_ARN", script)

    def test_setup_preserves_a_provider_owned_by_the_bootstrap_stack(self):
        script = self.read("deploy/aws/setup-autodeploy.sh")

        mode_check = script.index("bootstrap_provider_mode=")
        provider_scan = script.index("iam list-open-id-connect-providers")
        self.assertLess(mode_check, provider_scan)
        self.assertIn(
            'if [[ "${bootstrap_provider_mode}" != "true" ]]',
            script,
        )


if __name__ == "__main__":
    unittest.main()
