# Automatically deploy the Factory from GitHub

This guide connects the `codex/feat-aws-github-cloud` branch to one AWS
account. After the one-time setup, every push to that branch builds an
immutable container image, pushes it to Amazon ECR, and updates the Factory
CloudFormation stacks.

GitHub does not store an AWS access key. The workflow requests a short-lived
AWS session through OpenID Connect (OIDC). AWS accepts that request only when
it comes from this repository and this exact branch.

## What you configure once

```text
push to codex/feat-aws-github-cloud
                 │
                 ▼
GitHub Actions requests an OIDC identity token
                 │ exact repository + exact branch
                 ▼
AWS deployment role
  ├── pushes the new image to the Factory ECR repository
  └── asks a dedicated CloudFormation role to update two stacks
                 │
                 ▼
ECS replaces the Factory task; EFS preserves its workspace and state
```

The GitHub Actions workflow is a deployment Adapter around the existing
`deploy/aws/deploy.sh` Interface. Local and automatic deployment therefore use
the same build, ECR, and CloudFormation path.

## Before you begin

Complete the AWS prerequisites and configuration in [INSTALL.md](INSTALL.md).
In particular, you need:

- an authenticated AWS CLI identity that can create IAM roles and an OIDC
  provider;
- an authenticated GitHub CLI identity with repository administration access;
- a completed, uncommitted `deploy/aws/config.env` file;
- the GitHub service token already stored in AWS Secrets Manager; and
- Docker only for local deployment. GitHub-hosted runners already provide it.

Protect `codex/feat-aws-github-cloud` before enabling automatic deployment.
Restrict who can push, require pull-request review, and require the existing
test workflow. Anyone who can change code on this branch can change what runs
in the AWS deployment session.

## Step 1: Authenticate both command-line tools

Sign in to the AWS account that will run the Factory. Use your normal SSO or
federated login; do not create a permanent access key for GitHub.

```bash
aws sso login --profile workshop-admin
export AWS_PROFILE=workshop-admin
aws sts get-caller-identity
```

If you do not use an AWS CLI profile, omit the first two commands and verify
the currently selected identity with `aws sts get-caller-identity`.

Then authenticate GitHub CLI and verify the repository:

```bash
gh auth login
gh auth status
gh repo view giolaq/software-refactory-workshop
```

Stop if either identity points to the wrong account or repository.

## Step 2: Load the Factory configuration

Load the same non-secret settings used by a manual deployment:

```bash
set -a
source deploy/aws/config.env
set +a
```

Check the two deployment coordinates:

```bash
export AUTO_DEPLOY_SOURCE_REPOSITORY=giolaq/software-refactory-workshop
export AUTO_DEPLOY_BRANCH=codex/feat-aws-github-cloud
```

`AUTO_DEPLOY_SOURCE_REPOSITORY` is the repository that contains this workflow.
`GITHUB_REPOSITORY_URL` in `config.env` is the product repository the running
Factory operates on. They can be different repositories.

## Step 3: Create the deployment connection

Run the one-time setup helper:

```bash
bash deploy/aws/setup-autodeploy.sh
```

The helper performs four bounded operations:

1. Reuses the account's GitHub OIDC provider, or creates it if none exists.
2. Creates a GitHub deployment role trusted only for the exact OIDC subject.
3. Creates a dedicated CloudFormation service role for the Factory templates.
4. Writes non-secret deployment settings to GitHub repository variables.

It does not read the GitHub service token from Secrets Manager and does not
copy that token to GitHub. The workflow receives only the secret ARN; ECS
retrieves the token when the Factory task starts.

The default trusted subject is:

```text
repo:giolaq/software-refactory-workshop:ref:refs/heads/codex/feat-aws-github-cloud
```

Some repositories opt in to GitHub's immutable organization and repository ID
claims. For those repositories, set the complete subject before running the
helper. Keep it exact; do not replace any component with `*`.

```bash
export GITHUB_OIDC_SUBJECT='repo:OWNER@OWNER_ID/REPOSITORY@REPOSITORY_ID:ref:refs/heads/codex/feat-aws-github-cloud'
bash deploy/aws/setup-autodeploy.sh
```

## Step 4: Review the GitHub variables

Open **GitHub repository → Settings → Secrets and variables → Actions →
Variables**. The helper creates these values:

| Variable | Purpose |
| --- | --- |
| `AWS_REGION`, `AWS_ACCOUNT_ID` | Pins the destination account and Region. |
| `AWS_DEPLOY_ROLE_ARN` | Exact-branch role assumed by GitHub OIDC. |
| `AWS_CLOUDFORMATION_ROLE_ARN` | Role used only by CloudFormation. |
| `FACTORY_REGISTRY_STACK`, `FACTORY_STACK` | Limits updates to the two named stacks. |
| `FACTORY_TARGET_REPOSITORY_URL` | Product repository owned by the running Factory. |
| `FACTORY_GITHUB_TOKEN_SECRET_ARN` | Pointer to the runtime token in AWS Secrets Manager. |
| `FACTORY_REVIEWER_TOKEN_SECRET_ARN` | Optional pointer to the independent reviewer token. |
| `BEDROCK_MODEL_ID`, `BEDROCK_MODEL_RESOURCE_ARNS` | Model runtime and IAM scope. |
| `FACTORY_DOMAIN_NAME`, `ROUTE53_HOSTED_ZONE_ID`, `ACM_CERTIFICATE_ARN` | HTTPS endpoint. |
| `COGNITO_DOMAIN_PREFIX` | Cognito hosted-login prefix. |
| `FACTORY_GIT_USER_NAME`, `FACTORY_GIT_USER_EMAIL` | Factory commit identity. |
| `FACTORY_TASK_CPU`, `FACTORY_TASK_MEMORY` | Optional Fargate capacity override. |

These are identifiers and configuration, not credential values. Do not create
`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, or a GitHub token secret for this
workflow.

## Step 5: Trigger the first deployment

Commit and push the workflow and deployment files to the configured branch.
A push starts **Deploy Factory to AWS** automatically.

After this workflow also exists on the repository's default branch, you can
open **GitHub repository → Actions → Deploy Factory to AWS → Run workflow**
and select `codex/feat-aws-github-cloud`. GitHub does not show a manual
`workflow_dispatch` control until its workflow file exists on the default
branch. The manual run still uses the selected branch and does not bypass the
branch-scoped AWS trust policy.

Follow the job in GitHub Actions. A successful job summary links to the
Control Center. The first deployment can take several minutes because it
builds the image and creates or updates ECS resources.

## What happens on later pushes

Every push to `codex/feat-aws-github-cloud`, including documentation-only
changes, starts a deployment. Deployments are serialized. A newer push waits
for an active deployment instead of cancelling it halfway through.

The workflow:

1. checks that every required repository variable exists;
2. obtains a one-hour AWS session through OIDC;
3. builds a Linux/AMD64 image tagged with the Git commit and UTC time;
4. pushes that immutable image to ECR;
5. updates the registry and runtime stacks through CloudFormation; and
6. writes the Control Center URL to the job summary.

ECS deployment circuit breaking rolls back an unhealthy task. EFS remains
mounted by the replacement task, so the repository checkout, worktrees,
Factory state, and evidence survive normal updates.

## Diagnose a failed deployment

Start with the first red step in the GitHub Actions job.

### A repository variable is missing

Reload `deploy/aws/config.env` and run `setup-autodeploy.sh` again. The helper
updates variables and roles safely.

### AWS rejects `AssumeRoleWithWebIdentity`

Compare all three values exactly:

- the workflow repository;
- `codex/feat-aws-github-cloud`; and
- the `TrustedGitHubSubject` output of the bootstrap stack.

If the repository uses immutable ID claims, set the full immutable subject as
shown in Step 3 and rerun the helper. Do not fix this error by widening the
trust policy to every branch.

### The image build fails

Run the same Interface locally after starting Docker:

```bash
bash deploy/aws/deploy.sh
```

The local and GitHub paths intentionally share the same Dockerfile and script.

### CloudFormation rolls back

Open the failed stack in the AWS CloudFormation console and inspect the first
`CREATE_FAILED` or `UPDATE_FAILED` event. For a task startup failure, read the
Factory log group:

```bash
aws logs tail "/software-refactory/$FACTORY_STACK" \
  --region "$AWS_REGION" --since 30m
```

Correct the source or configuration and push a new commit. To restore an older
revision, revert the breaking commit and push the revert; do not force-push the
protected deployment branch.

## Disable automatic deployment

Disable **Deploy Factory to AWS** on the GitHub Actions page to stop future
runs without deleting AWS resources. The Factory already running on ECS keeps
running.

For temporary compute savings, use:

```bash
deploy/aws/factory-cloud pause
```

A later push can deploy a new task and resume the service. Disable the workflow
as well when the pause must remain in effect.

For permanent removal, stop active workflow jobs and run
`deploy/aws/factory-cloud destroy --all`. The guarded full teardown disables
the workflow when GitHub CLI can identify the source repository and removes the
bootstrap stack last. Deleting that stack removes the deployment roles and,
when this stack created it, the account's GitHub OIDC provider. Review whether
another workload shares that provider before confirming the full teardown.
