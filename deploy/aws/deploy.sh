#!/usr/bin/env bash
set -euo pipefail

deployment_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repository_root="$(cd "${deployment_dir}/../.." && pwd)"

required=(
    AWS_REGION GITHUB_REPOSITORY_URL GITHUB_TOKEN_SECRET_ARN BEDROCK_MODEL_ID
    BEDROCK_MODEL_RESOURCE_ARNS FACTORY_DOMAIN_NAME ROUTE53_HOSTED_ZONE_ID
    ACM_CERTIFICATE_ARN COGNITO_DOMAIN_PREFIX
)
for name in "${required[@]}"; do
    if [[ -z "${!name:-}" ]]; then
        echo "${name} is required. Copy config.example.env and export its values." >&2
        exit 2
    fi
done

registry_stack="${FACTORY_REGISTRY_STACK:-software-refactory-registry}"
factory_stack="${FACTORY_STACK:-software-refactory}"
aws_args=(--region "${AWS_REGION}")
if [[ -n "${AWS_PROFILE:-}" ]]; then
    aws_args+=(--profile "${AWS_PROFILE}")
fi

aws "${aws_args[@]}" cloudformation deploy \
    --stack-name "${registry_stack}" \
    --template-file "${deployment_dir}/registry.yaml" \
    --no-fail-on-empty-changeset

repository_uri="$(aws "${aws_args[@]}" cloudformation describe-stacks \
    --stack-name "${registry_stack}" \
    --query 'Stacks[0].Outputs[?OutputKey==`RepositoryUri`].OutputValue' \
    --output text)"
registry_host="${repository_uri%%/*}"
image_tag="$(git -C "${repository_root}" rev-parse --short=12 HEAD)-$(date -u +%Y%m%d%H%M%S)"
image_uri="${repository_uri}:${image_tag}"

aws "${aws_args[@]}" ecr get-login-password \
    | docker login --username AWS --password-stdin "${registry_host}"
docker build --platform linux/amd64 \
    --file "${deployment_dir}/Dockerfile" \
    --tag "${image_uri}" \
    "${repository_root}"
docker push "${image_uri}"

parameters=(
    "ImageUri=${image_uri}"
    "GitHubRepositoryUrl=${GITHUB_REPOSITORY_URL}"
    "GitHubTokenSecretArn=${GITHUB_TOKEN_SECRET_ARN}"
    "BedrockModelId=${BEDROCK_MODEL_ID}"
    "BedrockModelResourceArns=${BEDROCK_MODEL_RESOURCE_ARNS}"
    "DomainName=${FACTORY_DOMAIN_NAME}"
    "HostedZoneId=${ROUTE53_HOSTED_ZONE_ID}"
    "CertificateArn=${ACM_CERTIFICATE_ARN}"
    "CognitoDomainPrefix=${COGNITO_DOMAIN_PREFIX}"
    "GitUserName=${FACTORY_GIT_USER_NAME:-Software Re-Factory}"
    "GitUserEmail=${FACTORY_GIT_USER_EMAIL:-factory@example.invalid}"
)
if [[ -n "${REVIEWER_TOKEN_SECRET_ARN:-}" ]]; then
    parameters+=("ReviewerTokenSecretArn=${REVIEWER_TOKEN_SECRET_ARN}")
fi

aws "${aws_args[@]}" cloudformation deploy \
    --stack-name "${factory_stack}" \
    --template-file "${deployment_dir}/factory.yaml" \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides "${parameters[@]}" \
    --no-fail-on-empty-changeset

aws "${aws_args[@]}" cloudformation describe-stacks \
    --stack-name "${factory_stack}" \
    --query 'Stacks[0].Outputs[?OutputKey==`ControlCenterUrl`].OutputValue' \
    --output text
