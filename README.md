# Software (re)-Factory Workshop

Release: `workshop-v1.1.3`

This repository contains the reference factory orchestrator and the Pocket
Cinema refactoring workpiece. A four-expert planning pipeline turns each PRD
into Product Review, System Architecture, Program Design, and Vertical Slices
contracts before a human can publish tickets.

Pocket Cinema is the deterministic workshop pack. In Live mode, the same
factory can target a separate existing Git repository and any PRD after
`factory init --repo /path/to/project` creates its reviewable Project Contract.

## v1.1.3 highlights

- The Control Center now presents one four-stage operator workflow: **Setup**,
  **Plan**, **Deliver**, and **Review**.
- The current state and next safe action lead every run. Empty decision queues
  disappear, PRD drafts save automatically, and Planning shows only the action
  that is currently available.
- Supervisor activity, repository monitoring, advanced role configuration,
  run options, diagnostics, and CLI output remain available through progressive
  disclosure instead of competing with the primary workflow.
- Control Center assets work with relative paths for reliable local previews.

Start the local Control Center with:

```sh
./factory/factory control-center
```

Then use <http://127.0.0.1:5050/>. Keep that process running while operating
the factory; opening the HTML file directly does not provide live factory data.

- Start the self-guided experience with the [workshop website](workshop-guide/README.md).
- Use the [factory quickstart](factory/README.md) for the operator reference.
- Use the [configuration guide](factory/CONFIGURATION.md) to select Claude,
  Codex, Cursor, or register your own Supervisor, Implementation, QA, and Code Review adapters,
  model wrapper, and execution environment.
- Use the [Control Center guide](factory/CONTROL_CENTER.md) to inspect how worker
  Handoff Receipts become validated supervisor dispatch commands and how a
  separate Code Review role requests repairs or approves an exact candidate
  before the Supervisor recommends that exact revision for a human merge.
- Read the [simplified Control Center design](factory/CONTROL_CENTER_SIMPLIFIED_DESIGN.md)
  for its navigation, interaction hierarchy, and progressive-disclosure rules.
- Read the [planning pipeline guide](factory/PLANNING.md) for prompts, artifacts,
  approvals, traceability, and stale-plan behavior.
- Compare the executable [Factory Profiles and role topology](factory/README.md#choose-a-factory-profile).
- Use the [facilitator runbook](factory/FACILITATOR.md) for the 100-minute
  schedule, live fallback, and release checklist.
