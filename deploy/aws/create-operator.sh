#!/usr/bin/env bash
set -euo pipefail

stack_name="${1:-${FACTORY_STACK:-software-refactory}}"
email="${2:-}"
region="${AWS_REGION:-${AWS_DEFAULT_REGION:-}}"
if [[ -z "${region}" || -z "${email}" ]]; then
    echo "Usage: AWS_REGION=eu-west-2 $0 [STACK_NAME] operator@example.com" >&2
    exit 2
fi

aws_args=(--region "${region}")
if [[ -n "${AWS_PROFILE:-}" ]]; then
    aws_args+=(--profile "${AWS_PROFILE}")
fi
pool_id="$(aws "${aws_args[@]}" cloudformation describe-stacks \
    --stack-name "${stack_name}" \
    --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
    --output text)"

aws "${aws_args[@]}" cognito-idp admin-create-user \
    --user-pool-id "${pool_id}" \
    --username "${email}" \
    --user-attributes "Name=email,Value=${email}" "Name=email_verified,Value=true" \
    --desired-delivery-mediums EMAIL
