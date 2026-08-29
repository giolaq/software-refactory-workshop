# Install and run Software (re)-Factory on AWS

At the end of this guide, you will open an HTTPS URL, sign in with a Cognito
account, paste a PRD, review four planning artifacts, publish tickets to a
GitHub Project, and run those tickets with Amazon Bedrock.

The installation creates one factory for one GitHub repository. Use a separate
CloudFormation stack for another repository.

## Before you start

You need:

- an AWS account where you can create IAM, VPC, ECS, ECR, EFS, ALB, Cognito,
  Route 53, ACM, CloudWatch, and Secrets Manager resources;
- a domain managed by a public Route 53 hosted zone;
- a GitHub repository that the factory may change;
- permission to create a GitHub personal access token;
- Git, Docker, AWS CLI v2, and `jq` on your computer; and
- this repository checked out locally.

The AWS deployment identity has broad infrastructure permissions because it
creates task roles and networking. Use a temporary administrator-approved role
for installation. Do not create access keys for the AWS root user.

The factory incurs AWS charges while it is running. The main recurring items
are the ALB, Fargate task, EFS, CloudWatch Logs, Route 53, and Bedrock model
usage. Follow the cleanup section when the deployment is no longer needed.

## Step 1: Open the factory repository

If you do not already have the repository:

```bash
git clone https://github.com/giolaq/software-refactory-workshop.git
cd software-refactory-workshop
```

If you are testing the cloud branch before it is merged:

```bash
git switch codex/feat-aws-github-cloud
```

Confirm that the deployment files exist:

```bash
test -f deploy/aws/factory.yaml
test -f deploy/aws/deploy.sh
test -f deploy/aws/config.example.env
```

No output means the files are present.

## Step 2: Install the local tools

On macOS with Homebrew:

```bash
brew install awscli jq
brew install --cask docker
```

Open Docker Desktop and wait until it reports that the engine is running.

On another operating system, install:

- [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- [Docker](https://docs.docker.com/engine/install/)
- [Git](https://git-scm.com/downloads)
- [`jq`](https://jqlang.github.io/jq/download/)

Check the tools:

```bash
aws --version
docker version
git --version
jq --version
```

Stop here if `docker version` says it cannot connect to the Docker daemon.
Start Docker Desktop, then repeat the check.

## Step 3: Sign in to AWS

If your organization uses AWS IAM Identity Center, configure a named profile.
Ask your AWS administrator for the SSO start URL and SSO Region.

```bash
aws configure sso --profile software-refactory
aws sso login --profile software-refactory
export AWS_PROFILE=software-refactory
```

Choose one AWS Region for the entire deployment. This example uses London:

```bash
export AWS_REGION=eu-west-2
```

Confirm the account and role before creating anything:

```bash
aws sts get-caller-identity
```

Check the returned account ID. If it is the wrong AWS account, stop and correct
the profile.

If you already use another authenticated AWS profile, export that profile name
instead. The official AWS CLI flow uses `aws configure sso` followed by
`aws sso login`; it provides temporary credentials rather than long-lived
access keys.

## Step 4: Prepare the GitHub repository

Create a repository on GitHub or choose an existing one. The repository can be
empty. Record its full HTTPS URL, for example:

```text
https://github.com/your-name/recipe-app
```

Create a service token:

1. Open GitHub **Settings**.
2. Open **Developer settings → Personal access tokens → Tokens (classic)**.
3. Select **Generate new token (classic)**.
4. Give it a short expiration date.
5. Select `repo` and `project`.
6. Select `read:org` only if an organization owns the repository.
7. Generate and copy the token.
8. If the organization enforces SAML SSO, authorize the token for that
   organization.

The `project` scope is required because the factory creates and updates GitHub
Projects. A classic token is the simplest option for the workshop. A GitHub App
is a better long-term service identity, but requires a separate installation
and permission design.

Do not paste the token into `config.env`.

## Step 5: Store the GitHub token in AWS

Run the included secret helper:

```bash
bash deploy/aws/configure-github-secret.sh
```

Paste the token at the prompt and press Enter. The terminal does not echo it.
The command prints a Secrets Manager ARN similar to:

```text
arn:aws:secretsmanager:eu-west-2:123456789012:secret:software-refactory/github-token-AbCdEf
```

Copy this ARN. You will add it to `config.env` as
`GITHUB_TOKEN_SECRET_ARN`.

For independent formal GitHub reviews, repeat the command with a token owned by
a different GitHub account:

```bash
bash deploy/aws/configure-github-secret.sh software-refactory/reviewer-token
```

Copy that ARN as `REVIEWER_TOKEN_SECRET_ARN`. This second identity is optional.

Checkpoint:

```bash
aws secretsmanager describe-secret \
  --secret-id software-refactory/github-token \
  --query '{Name:Name,ARN:ARN}'
```

This displays metadata only. It does not print the token.

## Step 6: Prepare Amazon Bedrock

Open the Amazon Bedrock console in the same Region as `AWS_REGION`.

1. Open **Model catalog**.
2. Choose a model that supports the Converse API and tool use. The supplied
   example uses **Anthropic Claude Sonnet 4.6**.
3. For the first Anthropic model used by the AWS account, submit Anthropic's
   first-time-use form. AWS currently enables foundation-model access by
   default when the account has the required Marketplace permissions, but the
   Anthropic form remains required once per account or organization.
4. Open the model in the playground and send a short test prompt.

For the in-Region Sonnet 4.6 example, set:

```bash
export BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-6
```

Ask AWS for the exact model ARN:

```bash
aws bedrock get-foundation-model \
  --model-identifier "$BEDROCK_MODEL_ID" \
  --query 'modelDetails.modelArn' \
  --output text
```

Copy the output. It becomes `BEDROCK_MODEL_RESOURCE_ARNS`.

Optional command-line test:

```bash
aws bedrock-runtime converse \
  --model-id "$BEDROCK_MODEL_ID" \
  --messages '[{"role":"user","content":[{"text":"Reply with READY"}]}]' \
  --inference-config '{"maxTokens":20}' \
  --query 'output.message.content[0].text' \
  --output text
```

Run this optional test only if your deployment identity may invoke Bedrock. The
playground test is the account-access checkpoint; the CloudFormation stack
creates a separate task role for the running factory. An `AccessDeniedException`
usually means either the local deployment role cannot invoke models or the
Anthropic form, Marketplace permissions, account payment method, Region, or
model access is incomplete.

If you use a geographic or global inference profile, use its profile ID for
`BEDROCK_MODEL_ID`. Add the profile ARN and every destination foundation-model
ARN to `BEDROCK_MODEL_RESOURCE_ARNS`, separated by commas and without spaces.

## Step 7: Prepare DNS and the HTTPS certificate

Choose a hostname below a domain in Route 53. For example, if the hosted zone
is `example.com`, use:

```text
factory.example.com
```

In the Route 53 console:

1. Open **Hosted zones**.
2. Select the parent zone.
3. Copy its **Hosted zone ID**.

In AWS Certificate Manager, in the same Region as `AWS_REGION`:

1. Select **Request a certificate**.
2. Select **Request a public certificate**.
3. Enter the exact factory hostname.
4. Choose **DNS validation**.
5. Request the certificate.
6. Select **Create records in Route 53** when ACM offers it.
7. Wait until the certificate status is **Issued**.
8. Copy the certificate ARN.

Checkpoint:

```bash
aws acm describe-certificate \
  --certificate-arn YOUR_CERTIFICATE_ARN \
  --query 'Certificate.Status' \
  --output text
```

Do not deploy until this prints `ISSUED`.

Choose a Cognito domain prefix. It must contain only lowercase letters,
numbers, and hyphens and must be unique in the Region. For example:

```text
software-refactory-your-team
```

## Step 8: Create `config.env`

Copy the example:

```bash
cp deploy/aws/config.example.env deploy/aws/config.env
```

Open `deploy/aws/config.env` in your editor. Replace every placeholder. A
complete file looks like this:

```bash
AWS_REGION=eu-west-2
AWS_PROFILE=software-refactory

FACTORY_REGISTRY_STACK=software-refactory-registry
FACTORY_STACK=software-refactory

GITHUB_REPOSITORY_URL=https://github.com/your-name/recipe-app
GITHUB_TOKEN_SECRET_ARN=arn:aws:secretsmanager:eu-west-2:123456789012:secret:software-refactory/github-token-AbCdEf
# REVIEWER_TOKEN_SECRET_ARN=arn:aws:secretsmanager:eu-west-2:123456789012:secret:software-refactory/reviewer-token-XyZ123

BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-6
BEDROCK_MODEL_RESOURCE_ARNS=arn:aws:bedrock:eu-west-2::foundation-model/anthropic.claude-sonnet-4-6

FACTORY_DOMAIN_NAME=factory.example.com
ROUTE53_HOSTED_ZONE_ID=Z0123456789EXAMPLE
ACM_CERTIFICATE_ARN=arn:aws:acm:eu-west-2:123456789012:certificate/00000000-0000-0000-0000-000000000000
COGNITO_DOMAIN_PREFIX=software-refactory-your-team

FACTORY_GIT_USER_NAME="Software Re-Factory"
FACTORY_GIT_USER_EMAIL=factory@example.com
```

The file must not contain the GitHub token itself.

Load the settings:

```bash
set -a
source deploy/aws/config.env
set +a
```

Confirm the important non-secret values:

```bash
printf 'Account: %s\nRegion: %s\nRepository: %s\nURL: https://%s\n' \
  "$(aws sts get-caller-identity --query Account --output text)" \
  "$AWS_REGION" \
  "$GITHUB_REPOSITORY_URL" \
  "$FACTORY_DOMAIN_NAME"
```

## Step 9: Deploy the factory

Confirm Docker is running:

```bash
docker info >/dev/null
```

Deploy:

```bash
bash deploy/aws/deploy.sh
```

The script:

1. creates or updates the ECR registry;
2. builds the factory container;
3. pushes an immutable image tag;
4. deploys the VPC, authentication, ECS, EFS, IAM, logs, and DNS stack; and
5. prints the Control Center URL.

Keep the terminal open. If CloudFormation fails, start with the first error,
not the last cascade of cancelled resources.

Checkpoint:

```bash
aws cloudformation describe-stacks \
  --stack-name "$FACTORY_STACK" \
  --query 'Stacks[0].StackStatus' \
  --output text
```

The expected result is `CREATE_COMPLETE` or `UPDATE_COMPLETE`.

Get the URL again at any time:

```bash
aws cloudformation describe-stacks \
  --stack-name "$FACTORY_STACK" \
  --query 'Stacks[0].Outputs[?OutputKey==`ControlCenterUrl`].OutputValue' \
  --output text
```

## Step 10: Create your Control Center user

Create the first Cognito operator:

```bash
bash deploy/aws/create-operator.sh "$FACTORY_STACK" you@example.com
```

Cognito emails a temporary password. Open the Control Center URL, enter your
email and temporary password, then choose a permanent password. Enroll a TOTP
authenticator if you want MFA for the account.

If the email does not arrive, inspect the user:

```bash
pool_id="$(aws cloudformation describe-stacks \
  --stack-name "$FACTORY_STACK" \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)"
aws cognito-idp admin-get-user --user-pool-id "$pool_id" --username you@example.com
```

## Step 11: Configure the factory in the browser

After signing in:

1. Open **Setup → Connection**.
2. Set **Run mode** to **Live**.
3. Select **Amazon Bedrock on AWS** under **Agent preset**.
4. Confirm the GitHub repository URL from `config.env`.
5. Leave **Seed the guided Pocket Cinema starter** unchecked for an existing
   application. Select it only for an empty workshop repository where you want
   the guided starter application.
6. Select **Save configuration**.
7. Select **Create Project Contract** if the repository does not have one.
8. Review its source roots, test roots, setup commands, gates, ports, and
   protected paths.
9. Review and approve the **Factory Charter**.
10. Publish the setup commit when prompted.
11. Provision the development environment.
12. Approve and run only the setup commands listed in the Project Contract.
13. Run the environment health check.
14. Select **Run preflight** or **Check readiness**.

Do not continue while readiness shows a failure. Expand **Activity and CLI
output**, correct the first failure, and repeat the same action.

## Step 12: Run a PRD through the factory

Use the browser for the complete flow:

1. Open **PRD**.
2. Paste or write the PRD.
3. Start Product Review.
4. Read the Product Review artifact. Approve it or request a focused revision.
5. Continue planning.
6. Review System Architecture, Program Design, and Vertical Slices.
7. Approve the aligned planning package.
8. Create or select the GitHub Project when prompted.
9. Publish the generated tickets.
10. Open the GitHub Project in a second tab and confirm the tickets are visible.
11. Start delivery from the Control Center.
12. Watch **Factory progress**, ticket state, Supervisor decisions, Agent
    activity, QA evidence, verification gates, and Code Review.
13. When a ticket reaches its human gate, inspect the exact diff and evidence.
14. Merge the approved pull request as the human operator.

The normal sequence is:

```text
PRD → four expert artifacts → human alignment → GitHub tickets
    → QA → implementation → verification → code review → human merge
```

## Step 13: Check logs and service health

Follow the container output:

```bash
aws logs tail "/software-refactory/$FACTORY_STACK" --follow
```

Check the ECS service:

```bash
aws ecs describe-services \
  --cluster "$FACTORY_STACK-cluster" \
  --services "$FACTORY_STACK-service" \
  --query 'services[0].{Running:runningCount,Desired:desiredCount,Events:events[0:5]}'
```

The healthy steady state is one desired task and one running task.

To restart the service without deleting its EFS workspace:

```bash
aws ecs update-service \
  --cluster "$FACTORY_STACK-cluster" \
  --service "$FACTORY_STACK-service" \
  --force-new-deployment
```

Use this restart after rotating a GitHub secret. ECS reads injected secret
values only when a new task starts.

## Common installation failures

### `NoCredentials` or `ExpiredToken`

```bash
aws sso login --profile "$AWS_PROFILE"
aws sts get-caller-identity
```

### Docker cannot connect

Start Docker Desktop. Repeat `docker info` before `deploy.sh`.

### The certificate is not issued

Open ACM in the deployment Region. Confirm that the validation CNAME exists in
the Route 53 public hosted zone and wait for status **Issued**.

### Bedrock returns `AccessDeniedException`

Check all of these:

- AWS Region matches the model's supported Region;
- the Anthropic first-time-use form was submitted;
- AWS Marketplace prerequisites and the account payment method are valid;
- `BEDROCK_MODEL_ID` is the runtime ID, not the display name; and
- `BEDROCK_MODEL_RESOURCE_ARNS` includes every ARN used by an inference
  profile.

After correcting the configuration, run `deploy.sh` again.

### GitHub authentication fails

Create a new short-lived token with `repo` and `project`, authorize organization
SSO if required, update the existing secret with
`configure-github-secret.sh`, then force a new ECS deployment.

### GitHub Project access fails

The token needs the `project` scope for Project mutations. `read:project` is not
enough for creating and updating the workshop board.

### The task starts and then stops

Read the CloudWatch log first:

```bash
aws logs tail "/software-refactory/$FACTORY_STACK" --since 30m
```

The common causes are an invalid GitHub token, inaccessible repository, wrong
Bedrock model setting, or a persistent workspace that belongs to another
repository.

### The workspace belongs to another repository

One stack owns one repository. Do not overwrite the retained workspace. Deploy
a new stack with a different `FACTORY_STACK`, domain name, and Cognito prefix.

## Update the factory

Pull the new source and redeploy:

```bash
git pull --ff-only
set -a
source deploy/aws/config.env
set +a
bash deploy/aws/deploy.sh
```

The script pushes a new immutable image and updates the ECS task definition.
EFS preserves the repository checkout, worktrees, factory state, and logs.

## Remove the deployment

Delete the main stack:

```bash
aws cloudformation delete-stack --stack-name "$FACTORY_STACK"
aws cloudformation wait stack-delete-complete --stack-name "$FACTORY_STACK"
```

The EFS file system is deliberately retained. Find its ID in the old stack
outputs or the EFS console. Back it up, then delete it explicitly when you are
certain its checkout, worktrees, evidence, and logs are no longer needed.

Delete the registry stack when its images are no longer needed:

```bash
aws cloudformation delete-stack --stack-name "$FACTORY_REGISTRY_STACK"
```

Finally, delete the GitHub secrets from Secrets Manager if this factory will
not be recreated.

## Installation is complete when

- the CloudFormation stack is `CREATE_COMPLETE` or `UPDATE_COMPLETE`;
- ECS shows one desired and one running task;
- the Control Center opens over HTTPS and requires Cognito login;
- **Check readiness** has no failures;
- a Bedrock Product Review artifact completes;
- generated tickets appear in the selected GitHub Project; and
- GitHub contains the resulting branches, pull requests, reviews, and human
  merge decisions.
