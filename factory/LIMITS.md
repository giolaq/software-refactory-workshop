# Production boundaries

The Software (re)-Factory is an orchestration and teaching system. It does not
turn a local coding CLI into a security sandbox.

## Enforced controls

- The Control Center listens on loopback and accepts only registered actions.
- Each Ticket uses a separate Git worktree and a deterministic remote claim.
- Adapter processes receive only their declared environment allowlist and
  credential names.
- Adapter Protocol records reject malformed lifecycle transitions and private
  reasoning fields. Compatibility commands remain process-level integrations;
  their declared capabilities must match what the wrapper really enforces.
- Planning and supported review adapters run with read-only CLI settings.
  Every read-only role also has its Git head and worktree status checked.
- The human-owned Factory Charter separates paths agents must never modify
  from paths that require explicit human approval.
- Remote summaries are versioned, bounded, and exclude raw prompts, logs,
  environment values, and hidden model reasoning.
- Standard and Assured stop at a human exact-revision merge decision.
- A `requires_human_approval` path stops at that human decision even in an
  explicitly opted-in Autonomous Demo run.
- Raw feedback, triggers, compounding reports, and the merge steward can only
  propose a next action. They cannot dispatch, weaken the Charter, waive gates,
  resolve semantic conflicts, or merge.

## Trusted boundary

Project Contract setup commands, verification gates, and adapter templates are
trusted repository configuration. Review them before running `factory
environment prepare` or a Live Run. They can execute shell commands with the
operator's local user permissions.

Git worktrees isolate Git state. They do not isolate processes, the network,
CPU or memory, credentials stored in a user's home directory, or the host file
system outside the worktree. An adapter capability records the expected
filesystem mode, working roots, network use, environment allowlist, timeout,
credential names, and `local`, `container`, or `hosted` execution environment.
The `container` and `hosted` values are interfaces for adapters that enforce
those boundaries; selecting the value does not make the built-in local command
containerized.

The local development-environment provider records and checks the existing
checkout. It does not create a VM, container, short-lived identity, or network
policy. `prepare` and gates still execute trusted repository commands with the
operator's permissions. `reset` and `destroy` clear only provider-owned local
state and previews; they do not roll back source or delete GitHub evidence.

## Identity and service limits

- GitHub permissions come from the authenticated `gh` identity. Use a
  disposable repository for the workshop and protect the default branch.
- A comment from the Code Review adapter is not necessarily a formal branch-protection
  approval, especially when the PR author and reviewer identity are the same.
- Claude, Codex, Cursor, and custom providers retain their own account,
  telemetry, model-log, rate-limit, and data-handling policies.
- The built-in Cursor adapter uses headless Agent mode with `--force` for
  Implementation and QA, and read-only Ask mode for planning, supervision, and
  review. Cursor permissions and sandbox settings remain a separate provider
  boundary; review them before a Live Run.
- Live agents intentionally have no presentation timeout. The operator owns
  provider cost and may stop a run from the Control Center.
- Hidden chain-of-thought is neither requested nor exported. The UI shows tool
  progress, bounded output, decisions, and evidence that the adapter exposes.
- Trigger authentication belongs to the calling integration. The factory
  validates and deduplicates the bounded event, but does not make an
  unauthenticated public webhook endpoint safe.
- `factory.workspace.toml` coordinates named local checkouts and revisions. It
  is not a distributed transaction, release manager, or service provisioner.
- Usage and cost remain `unavailable` unless an adapter supplies trustworthy
  provider values; the factory does not estimate them.

## Recommended production additions

For higher-consequence work, supply a container or hosted-runner adapter,
short-lived scoped identities, egress controls, protected environments,
required independent GitHub reviewers, signed artifacts, centralized audit
retention, and organization-specific security gates. Keep human merge as the
default unless an accountable owner explicitly accepts another policy.
