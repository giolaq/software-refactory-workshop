# Software (re)-Factory Workshop

Release: `workshop-v1.2.1`

This repository contains the reference factory orchestrator and the Pocket
Cinema refactoring workpiece. A four-expert planning pipeline turns each PRD
into Product Review, System Architecture, Program Design, and Vertical Slices
contracts before a human can publish tickets.

Pocket Cinema is the deterministic workshop pack. In Live mode, the same
factory can target a separate existing Git repository and any PRD after
`factory init --repo /path/to/project` creates its reviewable Project Contract.

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

Start the local Control Center with:

```sh
./factory/factory control-center
```

Then use <http://127.0.0.1:5050/>. Keep that process running while operating
the factory; opening the HTML file directly does not provide live factory data.

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

- Follow the commands, clicks, and recovery instructions on the [workshop website](workshop-guide/README.md). Use the [speaker narrative](factory/WORKSHOP_NARRATIVE.md) for the concepts and discussion.
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
