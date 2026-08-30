import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1]))

from sensitive_data import contains_credentials, redact_credentials


class SensitiveDataTests(unittest.TestCase):
    def test_ordinary_aws_configuration_is_not_a_credential(self):
        value = "\n".join(
            (
                "AWS_REGION=eu-west-2",
                "AWS_PROFILE=workshop-admin",
                "GITHUB_REPOSITORY_URL=https://github.com/example/project",
                "GITHUB_TOKEN_SECRET_ARN=arn:aws:secretsmanager:eu-west-2:123456789012:secret:factory/github-token-example",
                "region=${AWS_REGION:-${AWS_DEFAULT_REGION:-}}",
                "token=${GH_TOKEN:?GH_TOKEN is required}",
            )
        )

        self.assertFalse(contains_credentials(value))
        self.assertEqual(redact_credentials(value), value)

    def test_provider_secret_assignments_remain_protected(self):
        assignments = (
            "OPENAI" + "_API_KEY=workshop-secret-value",
            "GH" + "_TOKEN=workshop-github-secret",
            "AWS_SECRET" + "_ACCESS_KEY=workshop-aws-secret",
            "AZURE_CLIENT" + "_SECRET=workshop-azure-secret",
        )

        for assignment in assignments:
            with self.subTest(assignment=assignment):
                self.assertTrue(contains_credentials(assignment))
                self.assertEqual(redact_credentials(assignment), "[REDACTED]")

    def test_known_token_shapes_are_detected_without_an_assignment(self):
        token = "ghp_" + ("a" * 24)

        self.assertTrue(contains_credentials(f"token output: {token}"))
        self.assertEqual(redact_credentials(token), "[REDACTED]")


if __name__ == "__main__":
    unittest.main()
