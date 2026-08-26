# Software (re)-Factory Workshop

Release: `workshop-v1.1.2`

This repository contains the reference factory orchestrator and the Pocket
Cinema refactoring workpiece. A four-expert planning pipeline turns each PRD
into Product Review, System Architecture, Program Design, and Vertical Slices
contracts before a human can publish tickets.

Pocket Cinema is the deterministic workshop pack. In Live mode, the same
factory can target a separate existing Git repository and any PRD after
`factory init --repo /path/to/project` creates its reviewable Project Contract.

## v1.1.2 highlights

- `factory recover` restores the latest pre-reset checkpoint or reconstructs
  the latest Live run, including returning the checkout to its default branch.
- Protected Acceptance Tests can be revised from written human feedback before
  approval while preserving revision history and causal RED evidence.
- Every retry requires a recorded reason that is shown in Ticket details and
  passed to the Supervisor and replacement agents.
- Blocked Tickets explain why they stopped, propose a recovery, and can offer
  an editable GitHub Ticket correction that is validated and saved before
  retry. Periodic refresh preserves log and editor scroll positions.

- Start the self-guided experience with the [workshop website](workshop-guide/README.md).
- Use the [factory quickstart](factory/README.md) for the operator reference.
- Use the [configuration guide](factory/CONFIGURATION.md) to select Claude,
  Codex, Cursor, or register your own Supervisor, Implementation, QA, and Code Review adapters,
  model wrapper, and execution environment.
- Use the [Control Center guide](factory/CONTROL_CENTER.md) to inspect how worker
  Handoff Receipts become validated supervisor dispatch commands and how a
  separate Code Review role requests repairs or approves an exact candidate
  before the Supervisor recommends that exact revision for a human merge.
- Read the [planning pipeline guide](factory/PLANNING.md) for prompts, artifacts,
approvals, traceability, and stale-plan behavior.
- Compare the executable [Factory Profiles and role topology](factory/README.md#choose-a-factory-profile).
- Use the [facilitator runbook](factory/FACILITATOR.md) for the 100-minute
  schedule, live fallback, and release checklist.
