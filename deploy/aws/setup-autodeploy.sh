#!/usr/bin/env bash
set -euo pipefail

deployment_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

required=(
    AWS_REGION GITHUB_REPOSITORY_URL GITHUB_TOKEN_SECRET_ARN BEDROCK_MODEL_ID
    BEDROCK_MODEL_RESOURCE_ARNS FACTORY_DOMAIN_NAME ROUTE53_HOSTED_ZONE_ID
    ACM_CERTIFICATE_ARN COGNITO_DOMAIN_PREFIX
)
for name in "${required[@]}"; do
    if [[ -z "${!name:-}" ]]; then
        echo "${name} is required. Export deploy/aws/config.env first." >&2
        exit 2
    fi
done

for command in aws gh git; do
    if ! command -v "${command}" >/dev/null 2>&1; then
        echo "${command} is required." >&2
        exit 2
    fi
done

aws_args=(--region "${AWS_REGION}")
if [[ -n "${AWS_PROFILE:-}" ]]; then
    aws_args+=(--profile "${AWS_PROFILE}")
fi

gh auth status >/dev/null
account_id="$(aws "${aws_args[@]}" sts get-caller-identity --query Account --output text)"
source_repository="${AUTO_DEPLOY_SOURCE_REPOSITORY:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}"
source_branch="${AUTO_DEPLOY_BRANCH:-codex/feat-aws-github-cloud}"
bootstrap_stack="${AUTO_DEPLOY_BOOTSTRAP_STACK:-software-refactory-github-deploy}"
registry_stack="${FACTORY_REGISTRY_STACK:-software-refactory-registry}"
factory_stack="${FACTORY_STACK:-software-refactory}"
ecr_repository="${FACTORY_ECR_REPOSITORY:-software-refactory}"
github_subject="${GITHUB_OIDC_SUBJECT:-repo:${source_repository}:ref:refs/heads/${source_branch}}"
encoded_branch="${source_branch//\//%2F}"

if ! gh api "repos/${source_repository}/branches/${encoded_branch}/protection" >/dev/null 2>&1; then
    echo "WARNING: ${source_repository}:${source_branch} is not protected." >&2
    echo "Anyone who can push to it can change code executed by the AWS deployment role." >&2
fi

provider_arn=""
provider_parameters=("CreateGitHubOidcProvider=true")
bootstrap_provider_mode="$(aws "${aws_args[@]}" cloudformation describe-stacks \
    --stack-name "${bootstrap_stack}" \
    --query 'Stacks[0].Parameters[?ParameterKey==`CreateGitHubOidcProvider`].ParameterValue' \
    --output text 2>/dev/null || true)"
if [[ "${bootstrap_provider_mode}" != "true" ]]; then
    for candidate in $(aws "${aws_args[@]}" iam list-open-id-connect-providers \
        --query 'OpenIDConnectProviderList[].Arn' --output text); do
        provider_url="$(aws "${aws_args[@]}" iam get-open-id-connect-provider \
            --open-id-connect-provider-arn "${candidate}" --query Url --output text)"
        if [[ "${provider_url}" == "token.actions.githubusercontent.com" ]]; then
            provider_arn="${candidate}"
            break
        fi
    done
    if [[ -n "${provider_arn}" ]]; then
        provider_parameters=(
            "CreateGitHubOidcProvider=false"
            "ExistingGitHubOidcProviderArn=${provider_arn}"
        )
    fi
fi

echo "Creating the exact-branch AWS deployment roles..."
aws "${aws_args[@]}" cloudformation deploy \
    --stack-name "${bootstrap_stack}" \
    --template-file "${deployment_dir}/github-autodeploy.yaml" \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
        "GitHubOidcSubject=${github_subject}" \
        "FactoryStackName=${factory_stack}" \
        "RegistryStackName=${registry_stack}" \
        "EcrRepositoryName=${ecr_repository}" \
        "${provider_parameters[@]}" \
    --no-fail-on-empty-changeset

deployment_role_arn="$(aws "${aws_args[@]}" cloudformation describe-stacks \
    --stack-name "${bootstrap_stack}" \
    --query 'Stacks[0].Outputs[?OutputKey==`GitHubDeploymentRoleArn`].OutputValue' \
    --output text)"
cloudformation_role_arn="$(aws "${aws_args[@]}" cloudformation describe-stacks \
    --stack-name "${bootstrap_stack}" \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFormationServiceRoleArn`].OutputValue' \
    --output text)"

set_variable() {
    local name="$1"
    local value="$2"
    gh variable set "${name}" --repo "${source_repository}" --body "${value}"
}

echo "Configuring non-secret GitHub repository variables..."
set_variable AWS_REGION "${AWS_REGION}"
set_variable AWS_ACCOUNT_ID "${account_id}"
set_variable AWS_DEPLOY_ROLE_ARN "${deployment_role_arn}"
set_variable AWS_CLOUDFORMATION_ROLE_ARN "${cloudformation_role_arn}"
set_variable FACTORY_REGISTRY_STACK "${registry_stack}"
set_variable FACTORY_STACK "${factory_stack}"
set_variable FACTORY_TARGET_REPOSITORY_URL "${GITHUB_REPOSITORY_URL}"
set_variable FACTORY_GITHUB_TOKEN_SECRET_ARN "${GITHUB_TOKEN_SECRET_ARN}"
set_variable BEDROCK_MODEL_ID "${BEDROCK_MODEL_ID}"
set_variable BEDROCK_MODEL_RESOURCE_ARNS "${BEDROCK_MODEL_RESOURCE_ARNS}"
set_variable FACTORY_DOMAIN_NAME "${FACTORY_DOMAIN_NAME}"
set_variable ROUTE53_HOSTED_ZONE_ID "${ROUTE53_HOSTED_ZONE_ID}"
set_variable ACM_CERTIFICATE_ARN "${ACM_CERTIFICATE_ARN}"
set_variable COGNITO_DOMAIN_PREFIX "${COGNITO_DOMAIN_PREFIX}"
set_variable FACTORY_GIT_USER_NAME "${FACTORY_GIT_USER_NAME:-Software Re-Factory}"
set_variable FACTORY_GIT_USER_EMAIL "${FACTORY_GIT_USER_EMAIL:-factory@example.invalid}"
if [[ -n "${FACTORY_TASK_CPU:-}" ]]; then
    set_variable FACTORY_TASK_CPU "${FACTORY_TASK_CPU}"
fi
if [[ -n "${FACTORY_TASK_MEMORY:-}" ]]; then
    set_variable FACTORY_TASK_MEMORY "${FACTORY_TASK_MEMORY}"
fi
if [[ -n "${REVIEWER_TOKEN_SECRET_ARN:-}" ]]; then
    set_variable FACTORY_REVIEWER_TOKEN_SECRET_ARN "${REVIEWER_TOKEN_SECRET_ARN}"
fi

echo
echo "Automatic deployment is configured for ${source_repository}:${source_branch}."
echo "AWS account: ${account_id}"
echo "Trusted OIDC subject: ${github_subject}"
echo "Push the workflow to that branch to start the first deployment."
