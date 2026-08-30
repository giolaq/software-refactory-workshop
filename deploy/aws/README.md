# Run Software (re)-Factory on AWS and GitHub

This deployment runs one authenticated Factory Control Center for one GitHub
repository. AWS supplies compute, durable storage, authentication, logs, and
model inference. GitHub remains the system of record for source code, Issues,
Projects, pull requests, review comments, and merged history.

For a copy-and-follow installation from an empty terminal to the first Live
run, use [INSTALL.md](INSTALL.md). This document is the architecture, security,
and operations reference.

After the first installation, use [AUTODEPLOY.md](AUTODEPLOY.md) to connect the
`codex/feat-aws-github-cloud` branch to AWS with short-lived GitHub OIDC
credentials. Every push then rebuilds and updates the same CloudFormation
stacks through the same `deploy.sh` interface.

This is a single-tenant team deployment. It is suitable for a workshop,
internal evaluation, or a small trusted engineering team. It is not a
multi-tenant service and does not treat arbitrary repository code as trusted.

## Architecture

```text
Operator browser
      │ HTTPS
      ▼
Application Load Balancer ── Cognito hosted login
      │ authenticated request
      ▼
ECS Fargate service (exactly one task)
      ├── Control Center and factory orchestrator
      ├── bounded Amazon Bedrock Agent Adapter
      ├── GitHub CLI ───────────────► GitHub repository + Project + PRs
      ├── task IAM role ────────────► Amazon Bedrock
      ├── /workspace ───────────────► encrypted EFS access point
      └── stdout/stderr ────────────► CloudWatch Logs
```

The one-task constraint is intentional. Local JSON state and Git worktrees are
durable on EFS, but they do not use distributed locking. Do not increase the
ECS desired count above 1. Deploy a separate stack for another repository or
team.

The Fargate task uses public subnets for low-cost outbound access to GitHub and
Bedrock. It receives a public IP, but its security group accepts no inbound
connection; the ALB is the only ingress path. A production hardening pass can
move tasks to private subnets and add NAT or VPC endpoints.

## What the templates create

`registry.yaml` creates:

- an encrypted ECR repository;
- immutable image tags and scan-on-push; and
- a lifecycle rule that keeps the latest 20 images.

`factory.yaml` creates:

- a VPC, two public subnets, routing, and least-reachability security groups;
- an HTTPS ALB protected by a Cognito user pool;
- one ECS Fargate service with deployment rollback and ECS Exec enabled;
- an encrypted EFS file system and access point for the checkout, worktrees,
  `.factory` state, and logs;
- task and execution IAM roles, scoped to configured Bedrock model ARNs, EFS,
  ECS Exec channels, ECR, logs, and named GitHub secrets;
- a CloudWatch log group with finite retention; and
- a Route 53 alias for the Control Center hostname.

EFS has `Retain` deletion policies and AWS Backup enabled. Deleting the stack
does not delete the workspace. Delete the retained file system explicitly only
after you have preserved anything you need.

## Prerequisites

Prepare these items before deployment:

1. An AWS account and an operator identity that can deploy CloudFormation,
   IAM, VPC, ECS, ECR, EFS, ELB, Cognito, Route 53, ACM, CloudWatch Logs, and
   Secrets Manager resources.
2. AWS CLI v2, Docker, Git, and `jq` on the deployment machine.
3. One AWS Region where the selected Amazon Bedrock model is available. Enable
   model access and note its runtime model or inference-profile ID. Verify the
   current ID and Region support in the
   [Amazon Bedrock model catalog](https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html).
4. A public Route 53 hosted zone and an issued ACM certificate for the chosen
   Control Center hostname. The certificate must be in the deployment Region.
5. A GitHub repository. Existing and empty repositories are both supported.
6. A GitHub token for the factory service identity. For the complete Live
   workflow, a classic PAT is the most predictable workshop option. Grant only
   the required scopes: `repo`, `project`, and `read:org` when an organization
   owns the repository. Restrict organization access and token lifetime.
7. Optionally, a second token owned by a different GitHub identity when formal
   independent pull-request approval is required. Without it, the factory
   publishes a labelled review comment and preserves the human merge gate.

The supplied image includes Python, Node.js, Git, GitHub CLI, `jq`, build tools,
`pytest`, and the AWS SDK. If the target Project Contract requires Java, Go,
Rust, Playwright browsers, database clients, or other system packages, extend
`Dockerfile` and rebuild the image. Do not grant the task host access merely to
avoid declaring a dependency.

Do not put either GitHub token in an environment file or CloudFormation
parameter. ECS injects the token directly from Secrets Manager. Bedrock uses
the ECS task IAM role; no long-lived AWS key is stored in the container.

## 1. Store the GitHub token

Run the helper. It prompts without echo and uploads the token from a temporary
mode-0600 file, so the token is not passed in a command argument.

```bash
export AWS_REGION=eu-west-2
# export AWS_PROFILE=workshop-admin
bash deploy/aws/configure-github-secret.sh
```

Copy the printed ARN. To add a distinct reviewer identity, run the helper again
with another name:

```bash
bash deploy/aws/configure-github-secret.sh software-refactory/reviewer-token
```

## 2. Configure the deployment

Copy the non-secret example, edit every placeholder, and export it:

```bash
cp deploy/aws/config.example.env deploy/aws/config.env
set -a
source deploy/aws/config.env
set +a
```

Do not commit `config.env`. It contains resource identifiers, not token values,
but it is still operator-specific. The repository ignores it.

For `BEDROCK_MODEL_RESOURCE_ARNS`, supply every ARN required by the selected
runtime ID. A foundation model normally needs its foundation-model ARN. A
cross-Region inference profile can require both the inference-profile ARN and
the foundation-model ARNs to which it routes. The task IAM policy can invoke
only this list. AWS documents the destination-model lookup in
[Supported Regions and models for inference profiles](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-support.html).

## 3. Build and deploy

```bash
bash deploy/aws/deploy.sh
```

The script performs replaceable steps behind one interface:

1. deploy or update the ECR registry stack;
2. build the Linux/AMD64 runtime image and push an immutable tag;
3. deploy or update the main CloudFormation stack; and
4. print the HTTPS Control Center URL.

A failed ECS deployment rolls back to the previous task definition. The image
tag includes the Git revision and UTC build time, so an update never overwrites
the image used by a previous deployment.

## 4. Create the first operator

The Cognito pool allows only administrators to create users. Create the first
operator after the stack succeeds:

```bash
bash deploy/aws/create-operator.sh software-refactory you@example.com
```

Cognito emails a temporary password. Open the URL printed by `deploy.sh`, sign
in, choose a permanent password, and optionally enroll a TOTP authenticator.
Repeat the command for each trusted operator.

## 5. Initialize the repository from the Control Center

The task clones `GITHUB_REPOSITORY_URL` into the EFS workspace on its first
start. It never resets an existing checkout during restart.

In the Control Center:

1. Open **Setup → Connection** and confirm the GitHub repository URL.
2. Choose the **bedrock-aws** preset. This assigns Bedrock to Planning,
   Supervisor, QA, Implementation, and Code Review with one ticket at a time.
3. If the repository does not contain `factory.project.toml`, select **Create
   Project Contract**. Review detected roots, setup commands, gates, ports, and
   protected paths before approving anything.
4. Review and approve the Factory Charter. Keep human merge authority for the
   normal Standard profile.
5. Run **Check readiness**. Fix the first failing item before planning.
6. Enter a PRD, review each of the four Bedrock planning artifacts, publish the
   generated tickets to a GitHub Project, and start delivery.

The Bedrock adapter can list, read, search, write, and delete files only inside
its assigned Git worktree. It cannot run arbitrary shell commands and does not
receive `GH_TOKEN`. The outer factory runs the Project Contract's approved
verification commands and owns every GitHub mutation.

## Operate and diagnose

Get the stack outputs:

```bash
aws cloudformation describe-stacks \
  --region "$AWS_REGION" \
  --stack-name "$FACTORY_STACK" \
  --query 'Stacks[0].Outputs'
```

Follow the service logs:

```bash
aws logs tail "/software-refactory/$FACTORY_STACK" \
  --region "$AWS_REGION" --follow
```

Force a fresh task after rotating a secret or when recovering a failed process:

```bash
cluster="$FACTORY_STACK-cluster"
service="$FACTORY_STACK-service"
aws ecs update-service --region "$AWS_REGION" \
  --cluster "$cluster" --service "$service" --force-new-deployment
```

ECS resolves injected secrets only when a task starts. Updating Secrets Manager
does not update a running container.

For emergency inspection, ECS Exec is enabled. Use it for read-only diagnosis;
normal operation and recovery should remain in the Control Center so actions
are visible in factory evidence.

## Security boundary

The deployment enforces these boundaries:

- ALB/Cognito authenticates browser traffic. The container rejects hosted
  requests without the ALB identity header and exact configured host.
- `/healthz` is the only unauthenticated endpoint and returns only health.
- the task security group accepts traffic only from the ALB security group;
- the GitHub token is stored in Secrets Manager and filtered out of Bedrock
  adapter subprocesses;
- Bedrock access is granted through task IAM and restricted to explicit model
  resource ARNs;
- EFS is encrypted, mounted with TLS through one POSIX access point, and
  retained on stack deletion; and
- CloudWatch receives process output. Prompts and repository artifacts remain
  on EFS unless the factory deliberately publishes bounded evidence to GitHub.

Important limits:

- Git worktrees coordinate changes but are not a hostile-code sandbox.
- Project Contract setup and gate commands execute in the same Fargate task as
  the control plane. Use a separate ephemeral runner before accepting untrusted
  repositories or untrusted pull requests.
- Cognito authentication does not provide per-action authorization. Every
  Cognito operator is a trusted operator for this one factory.
- public subnets reduce infrastructure complexity and NAT cost. Use private
  subnets, VPC endpoints, WAF, centralized audit logging, and organization
  controls for a production deployment.

## Update, pause, and remove

Run `deploy.sh` again to publish a new immutable image and update the service.
CloudFormation reports an empty change set as success.

For branch-driven updates, configure the exact-branch GitHub Actions path in
[AUTODEPLOY.md](AUTODEPLOY.md). Do not store long-lived AWS access keys in
GitHub.

Check the current cost state:

```bash
deploy/aws/factory-cloud status
```

Pause Fargate compute without losing the workspace:

```bash
deploy/aws/factory-cloud pause
deploy/aws/factory-cloud resume
```

Pause scales the service to zero. It stops the Fargate task charge, but the
ALB, public IPv4 addresses, EFS, Route 53, Secrets Manager, and stored logs or
images can still incur charges. A later automatic deployment can restore the
template's desired count of one.

Remove the runtime while retaining the EFS workspace and reusable deployment
setup:

```bash
deploy/aws/factory-cloud destroy
```

For a permanent teardown after the workshop, first stop active deployment
jobs, then run:

```bash
deploy/aws/factory-cloud destroy --all
```

The full path requires a separate exact confirmation. It disables automatic
deployment when GitHub CLI can identify the source repository, then deletes
the runtime, EFS recovery points and workspace, ECR images, runtime secret,
certificate, hosted zone, and OIDC bootstrap stack. It cannot remove the four
delegation records from a parent DNS provider such as Cloudflare; remove those
records manually when the command reports completion.
