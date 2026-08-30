#!/usr/bin/env bash
set -euo pipefail

region="${AWS_REGION:-${AWS_DEFAULT_REGION:-}}"
if [[ -z "${region}" ]]; then
    echo "Set AWS_REGION before creating the secret." >&2
    exit 2
fi

secret_name="${1:-software-refactory/github-token}"
aws_args=(--region "${region}")
if [[ -n "${AWS_PROFILE:-}" ]]; then
    aws_args+=(--profile "${AWS_PROFILE}")
fi

read -r -s -p "GitHub token for ${secret_name}: " github_token
printf '\n'
if [[ -z "${github_token}" ]]; then
    echo "Token cannot be empty." >&2
    exit 2
fi

secret_file="$(mktemp)"
trap 'rm -f "${secret_file}"' EXIT
chmod 600 "${secret_file}"
printf '%s' "${github_token}" > "${secret_file}"
unset github_token

if aws "${aws_args[@]}" secretsmanager describe-secret --secret-id "${secret_name}" >/dev/null 2>&1; then
    result="$(aws "${aws_args[@]}" secretsmanager put-secret-value \
        --secret-id "${secret_name}" --secret-string "file://${secret_file}")"
else
    result="$(aws "${aws_args[@]}" secretsmanager create-secret \
        --name "${secret_name}" --description "GitHub token for Software Re-Factory" \
        --secret-string "file://${secret_file}")"
fi

printf '%s' "${result}" | jq -r '.ARN'
