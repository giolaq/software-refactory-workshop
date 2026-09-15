# Software (re)-Factory Workshop

Release: `workshop-v1.2.4`

Software (re)-Factory helps you use coding agents to turn requirements into
reviewed changes in a GitHub repository. You describe the result, review the
plan and tests, and decide what to merge. The factory coordinates the work,
runs checks, and shows what is happening in a local web Control Center.

This repository includes the factory, the Control Center, a step-by-step
workshop website, and the Pocket Cinema starting app. The three-hour workshop
transforms Pocket Cinema into TableStory, a recipe app. The factory is generic:
Live mode can use your own repository and PRD instead of the sample app.

Everything needed for the workshop runs locally with GitHub and your chosen
coding-agent CLI. AWS is optional.

## Quick configuration and run

### 1. Install the tools and sign in

Use macOS, Linux, or Windows with WSL2. On Windows, run the commands inside WSL2.
You need:

- Python 3.11+ with `venv`, Node.js 22.13+, Git, and GitHub CLI (`gh`).
- A modern browser, ports `5000` and `5050` available, and network access to
  GitHub and your agent provider.
- A GitHub account that can create repositories, issues, branches, pull
  requests, and GitHub Projects.
- One installed and authenticated coding CLI: Claude Code, Codex, or Cursor.
  Live use follows your provider's subscription and limits.

Sign in to GitHub and grant Projects access:

```sh
gh auth login --web --git-protocol https --scopes project
```

If you are already signed in, check `gh auth status` and add Projects access
with `gh auth refresh -s project` if needed. Set your Git commit name and email
if they are not configured.

Sign in to **only the agent you will use**: `claude auth login`, `codex login`,
or `agent login` for Cursor. See the [workshop prerequisites](https://software-refactory-workshop.vercel.app/#prerequisites)
for installation instructions. The authenticated CLI path does not require
Docker, AWS, or entering an OpenAI API key in the factory.

### 2. Download and start the factory

For this release, run the following in the folder where you keep your projects.
If your facilitator supplies a different session tag, use that tag instead.

```sh
git clone --branch workshop-v1.2.4 https://github.com/giolaq/software-refactory-workshop.git software-refactory-control
cd software-refactory-control
./setup_demo.sh --scenario recipe-rebrand
./factory/factory control-center
```

Run the setup script only in this fresh workshop checkout. It installs
dependencies and restores the sample app to its starting state; it does not
create GitHub tickets. Do not rerun it to restart an active run. Use the
Control Center's **Reset run** action instead.

Open [the local Control Center](http://127.0.0.1:5050/) and leave the terminal
running. Opening its HTML file directly will not provide a working factory.

### 3. Connect your product repository

Create an empty, private repository in [GitHub → New repository](https://github.com/new),
for example `factory-tablestory-workshop`. Use your own account and leave README,
`.gitignore`, and license unselected. Copy its URL; you do not need to clone it.
Keep this product repository separate from the factory checkout above.

Create a new GitHub Project under the same account: **Your profile → Projects →
New project → Board**. Name it `TableStory workshop`, select **Create project**,
and copy the board URL from your browser. Use a dedicated board; the factory
configures its Status columns and adds tickets after you approve the plan.

In the Control Center, open **Setup → Connection**:

1. **Connect:** select **Live**, **Standard**, and your agent preset. Paste your
   product repository URL and paste the board URL into **GitHub Project URL or
   number** (the number is extracted automatically). Select **Seed the guided Pocket Cinema starter**,
   and select **Save and connect**. This copies the starting app, not tickets.
2. **Create contract:** select **Create contract** to generate the repository
   settings and operating rules.
3. **Review and approve:** read **Review repository model** and **Review operating
   policy**, then select **Approve contract and continue**. Keep human QA
   approval and human merge enabled for the workshop.

The factory prepares the environment and checks readiness. Continue when Setup
says **Approved and ready**. If it stops, open **Activity and CLI output**, fix
the first `[FAIL]`, then retry. Use the [recovery table](https://software-refactory-workshop.vercel.app/#preflight-recovery)
for common errors; do not skip a failed check.

For your own existing product, connect its repository and leave **Seed the
guided Pocket Cinema starter** unchecked. Review the generated contract before
approving it, and use your own PRD.

### 4. Begin the workshop

Open the starting app using [Check the starting app](https://software-refactory-workshop.vercel.app/#baseline).
Then paste [the complete recipe PRD](recipe-app-prd.md) into **Plan → Requirements**
and select **Start Product Review**.

Follow the walkthrough below to understand each stage. Keep the
[workshop website](https://software-refactory-workshop.vercel.app/) open for
the exact clicks, expected results, and recovery instructions. Setup is complete;
delivery starts later, after you approve the plan and acceptance tests.

## Workshop walkthrough

By **nominal workshop**, I mean the normal path when everything works, using **Standard Live**: real agents, your own GitHub repository, and human approval before merging.

The story is simple: **a food company wants to transform Pocket Cinema into TableStory, a recipe app.** We use the factory to plan, build, and check that transformation.

### 1. See the starting point and the goal

You show Pocket Cinema and a prepared example of TableStory.

Attendees understand what must change: recipes instead of movies, ingredient search, cooking instructions, saved recipes, branding, and mobile/TV behavior.

**What’s happening:** we establish the product goal before discussing tools.

### 2. Connect and prepare the factory

Each attendee connects their own GitHub repository and selects their coding agent.

The factory creates a **contract**: settings describing where it can work, which checks to run, and what requires approval. The attendee reviews and approves it. The factory prepares the environment and checks readiness.

**What’s happening:** we give the factory a workplace and rules. No product implementation starts yet.

### 3. Check the existing app

Attendees open Pocket Cinema and try it.

**What’s happening:** they establish the baseline. Later, they can compare the actual transformation with what existed before.

### 4. Give the factory the requirements

Attendees paste the complete recipe-app PRD into the Control Center.

The PRD describes the desired product, its behavior, and its limits.

**What’s happening:** we tell the factory what outcome we want. We have not created implementation tickets yet.

### 5. Review the product understanding

The **Product Review agent** reads the PRD and explains what it understands.

Attendees check that understanding, request corrections if needed, and approve it.

For example: does “save a recipe” mean saving it in My Cookbook? Does it require an account? What should happen after a reload?

**What’s happening:** a human confirms that the factory is solving the right problem.

### 6. Review how the product will be built

The remaining planning agents prepare three things:

- **System Architecture:** which parts of the application handle each responsibility.
- **Program Design:** the data structures, interfaces, and code organization.
- **Vertical Slices:** manageable pieces of work that together deliver the transformation.

Attendees review these plans and can request revisions before proceeding.

**What’s happening:** we agree on the approach before agents start changing production code.

### 7. Approve the plan and create tickets

Once attendees approve the complete plan, the factory publishes its tickets to GitHub and adds them to GitHub Projects.

Each ticket describes a piece of work, its acceptance criteria, and any prerequisites.

**What’s happening:** the approved plan becomes executable work. The tickets come from the PRD and planning agents; Live does not require a fixed ticket count.

### 8. Create and approve acceptance tests

Attendees start one cycle. The **QA agent** writes tests for an eligible ticket before implementation begins.

The factory runs those tests against the starting code. They should fail because the requested behavior is missing.

Attendees inspect the tests and approve them when they make sense.

**What’s happening:** we define how to recognize success before asking another agent to implement it.

A missing test dependency is not useful evidence. “The ingredient search returned the wrong recipes” can be.

### 9. Start implementation

Attendees select **Run factory**.

The factory selects ready tickets. An **Implementation agent** changes the code in its assigned Git worktree—a separate checkout for that ticket.

It must satisfy the ticket and the approved tests without weakening those tests.

**What’s happening:** agents build the agreed changes, while the factory manages dependencies and records progress.

### 10. Check the work and repair failures

The factory runs the required checks.

If a check fails, the implementation agent receives the failure details and can repair the change within the configured retry limits. If human input is necessary, the factory stops at that decision.

Attendees inspect the ticket’s status, logs, and evidence.

**What’s happening:** the factory checks proposed work instead of treating “the agent finished” as success.

The workshop break happens while healthy agents can continue working.

### 11. Review and merge each change

The **Code Review agent** examines the actual candidate code.

If it requests changes, the implementation agent fixes them, and checks and review run again.

Once the candidate is ready, the attendee inspects the diff, tests, and review, then decides whether to select **Merge exact revision**.

**What’s happening:** the agent provides a review; the human decides whether to accept that specific version.

Merging a prerequisite can unlock another ticket. Steps 8–11 repeat as needed; attendees should handle approvals when they become ready.

### 12. Test the complete transformed product

Attendees run the merged application and try the recipe experience:

Find a recipe by ingredient, read its cooking steps, save it, and remove it from My Cookbook.

They also check the remaining approved scope, including APIs, branding, mobile/TV behavior, and removal of movie-specific behavior.

**What’s happening:** we verify that the pieces work together as a product, not merely that individual tickets passed.

### 13. Save the results and examine the effort

Attendees export the run evidence and look at completed work, retries, waiting, human review effort, and available usage information.

If anything remains unfinished, they record where to resume.

**What’s happening:** we establish what was actually achieved and what it took. Completing the workshop does not automatically mean every Live run finished.

### 14. Apply the lesson to their own team

Each attendee chooses a possible team use case and describes:

- What change they would try.
- What evidence would justify accepting it.
- Who would review it and handle failures.
- How they would decide whether the experiment was worthwhile.

**What’s happening:** the exercise becomes a practical next step for their work.

The whole workshop comes down to this:

**Agree on the change. Let agents build it. Inspect the evidence. Decide whether to accept it.**

In Standard, ordinary factory code coordinates this process. There is no AI Supervisor making scheduling or merge decisions.

## v1.2.3 highlights

- Planning validates generated references and provides bounded recovery from
  provider context-limit failures.
- Setup accepts a GitHub Project board URL and extracts its number. The guide
  explains how to create the board before connecting.
- The Control Center uses Current phase and Next safe action without a
  separate Attention Queue; workshop screenshots match the updated interface.
- Two new greenfield PRDs are available: [BorrowBox](borrowbox-prd.md), an
  equipment lending desk, and [TrailMix](trailmix-prd.md), a conference agenda
  planner. Both require Live agents and a separate empty repository.

## v1.2.2 highlights

- Standard delivery uses one deterministic scheduler and unified,
  revision-bound review evidence; Assured and Autonomous Demo keep their
  supervisor capabilities.
- The workshop guide now separates product-plan review, optional revision, and
  approval so attendees approve the version they actually read.
- The Control Center keeps the candidate evidence and exact-revision merge
  decision visible before lower-level execution details.

## v1.2.0 highlights

- Adapter Protocol v1 adds versioned assignments, normalized progress and
  results, capability negotiation, and a custom-adapter conformance report.
- The local environment provider makes setup reproducible through provision,
  prepare, health, preview, reset, and destroy evidence.
- Raw feedback and external triggers enter non-dispatching, evidence-backed
  intake. Repeated run evidence produces human-reviewed improvement proposals.
- The merge steward can synchronize and re-verify an approved candidate but
  cannot resolve semantic conflicts or merge it.
- The Control Center and workshop now teach the five replaceable factory layers
  while keeping the core Setup, Plan, Deliver, and Review path concise.

## Optional AWS deployment

To run the same single-repository factory with an authenticated Control Center,
durable worktrees, CloudWatch logs, and a native Amazon Bedrock adapter, follow
the [AWS + GitHub deployment guide](deploy/aws/README.md). The CloudFormation
edition keeps GitHub as the Issue, Project, pull-request, and merge system of
record; it does not change the local workshop path.

Use the [step-by-step AWS installation guide](deploy/aws/INSTALL.md) when
setting up the cloud edition for the first time.

Use the [AWS automatic deployment guide](deploy/aws/AUTODEPLOY.md) to rebuild
and update the cloud Factory on every push to the AWS feature branch. GitHub
uses a short-lived, exact-branch OIDC session instead of stored AWS keys.
The cloud guide also provides guarded `status`, `pause`, `resume`, and teardown
commands so workshop infrastructure does not need to run continuously.

## Further reading

- Follow the commands, clicks, and recovery instructions on the [workshop website](https://software-refactory-workshop.vercel.app/). Use the [speaker narrative](factory/WORKSHOP_NARRATIVE.md) for the concepts and discussion. See [workshop website development](workshop-guide/README.md) to run or edit the guide locally.
- Use the [factory quickstart](factory/README.md) for the operator reference.
- Use the [configuration guide](factory/CONFIGURATION.md) to select Claude,
  Codex, Cursor, or register your own Supervisor, Implementation, QA, and Code Review adapters,
  model wrapper, and execution environment.
- Use the [Cursor CLI guide](factory/CURSOR.md) to install Cursor, select the
  one-click preset, understand Ask versus Agent mode, and configure permissions.
- Use the [Control Center guide](factory/CONTROL_CENTER.md) to inspect tests,
  code-review findings, and the exact candidate before your merge decision.
  Standard schedules ready work without a supervisor invocation. Assured and
  Autonomous Demo retain agent supervision.
- Follow the [repository issue listener guide](factory/ISSUE_LISTENER.md) to
  admit and implement new user-created GitHub issues from the Control Center.
- Read the [Factory interface guide](factory/INTERFACES.md) for the five-layer
  model, Adapter Protocol v1, environment lifecycle, governed intake,
  compounding reports, merge steward, triggers, and workspace contract.
- Read the [simplified Control Center design](factory/CONTROL_CENTER_SIMPLIFIED_DESIGN.md)
  for its navigation, interaction hierarchy, and progressive-disclosure rules.
- Read the [planning pipeline guide](factory/PLANNING.md) for prompts, artifacts,
  approvals, traceability, and stale-plan behavior.
- Compare the executable [Factory Profiles and role topology](factory/README.md#choose-a-factory-profile).
- Use the [facilitator runbook](factory/FACILITATOR.md) for the three-hour
  schedule, live fallback, and release checklist.
