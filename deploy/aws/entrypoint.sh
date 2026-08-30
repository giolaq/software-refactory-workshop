#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_REPOSITORY_URL:?GITHUB_REPOSITORY_URL is required}"
: "${GH_TOKEN:?GH_TOKEN is required}"
: "${FACTORY_BEDROCK_MODEL_ID:?FACTORY_BEDROCK_MODEL_ID is required}"
: "${FACTORY_CONTROL_CENTER_PUBLIC_ORIGIN:?FACTORY_CONTROL_CENTER_PUBLIC_ORIGIN is required}"

workspace_root="${FACTORY_WORKSPACE_ROOT:-/workspace}"
repository_path="${workspace_root}/product"
repository_marker="${workspace_root}/.factory-cloud-repository"

mkdir -p "${workspace_root}"
git config --global user.name "${FACTORY_GIT_USER_NAME:-Software Re-Factory}"
git config --global user.email "${FACTORY_GIT_USER_EMAIL:-factory@example.invalid}"
git config --global --add safe.directory "${repository_path}"
gh auth setup-git

expected_repository="$(gh repo view "${GITHUB_REPOSITORY_URL}" --json nameWithOwner --jq .nameWithOwner)"
if [[ -f "${repository_marker}" ]]; then
    configured_repository="$(tr -d '\r\n' < "${repository_marker}")"
    if [[ "${configured_repository}" != "${expected_repository}" ]]; then
        echo "Persistent workspace belongs to ${configured_repository}, not ${expected_repository}." >&2
        echo "Deploy a separate stack or replace its EFS volume to change repositories." >&2
        exit 2
    fi
fi

if [[ ! -d "${repository_path}/.git" ]]; then
    if [[ -e "${repository_path}" ]]; then
        echo "${repository_path} exists but is not a Git checkout; refusing to overwrite it." >&2
        exit 2
    fi
    gh repo clone "${GITHUB_REPOSITORY_URL}" "${repository_path}"
else
    actual_repository="$(cd "${repository_path}" && gh repo view --json nameWithOwner --jq .nameWithOwner)"
    if [[ "${actual_repository}" != "${expected_repository}" ]]; then
        echo "Existing checkout is ${actual_repository}, not ${expected_repository}." >&2
        exit 2
    fi
fi

printf '%s\n' "${expected_repository}" > "${repository_marker}"
cd "${repository_path}"

exec /opt/software-refactory/factory/factory control-center \
    --repo "${repository_path}" \
    --host 0.0.0.0 \
    --port "${PORT:-5050}" \
    --no-open
