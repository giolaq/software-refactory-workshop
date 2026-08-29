# Factory interfaces

Release: `workshop-v1.2.0`

Software (re)-Factory is a delivery system, not a collection of agents. Its
interfaces separate responsibilities that change for different reasons. A
team can replace an Agent Adapter or execution provider without silently
changing the Product, Ticket, evidence, or human-decision contracts.

## The five layers

| Layer | Workshop implementation | Interface evidence | Failure owner |
| --- | --- | --- | --- |
| Compute | The attendee machine and isolated Git worktrees | process identity, allowed roots, timeout, cancellation | operator or compute provider |
| Development environment | Project Contract and local environment provider | revision, contract hash, tools, setup, gates, ports, preview | repository owner |
| Inner harness | Claude, Codex, Cursor, mock, or a custom Agent Adapter | Adapter Protocol assignment, events, result, capabilities | adapter owner |
| Outer harness | Agent Roles, Factory Profile, Charter, planning, QA, retries, review, and Handoff Receipts | approved policy and revision-bound evidence | workshop team or delivery owner |
| Control plane | Orchestrator, Control Center, GitHub Projects, claims, triggers, and Supervisor | lifecycle state, decisions, claims, bounded remote summaries | factory operator |

The local provider and Git worktrees isolate changes for coordination. They are
not a security sandbox. Use a container or hosted isolation provider when
untrusted code must not share the operator's machine.

## Adapter Protocol v1

The protocol boundary is between the control plane and an inner harness. A
protocol-aware adapter receives a JSON assignment and emits normalized progress
events plus one final result. Compatibility command adapters remain supported.

### Assignment

An assignment names the run, invocation, Agent Role, Ticket, attempt, repository
or worktree, prompt reference, Factory Profile, Charter and policy hashes,
timeout, execution environment, filesystem mode, allowed roots, network
expectation, environment allowlist, and credential names.

Assignments are written below `.factory/assignments/<run-id>/`. They contain
references and policy, not hidden model reasoning or unrestricted credentials.

### Events

Protocol adapters may emit lines prefixed with `FACTORY_EVENT ` followed by a
JSON object. Event types are bounded to:

- `started`, `status`, `tool_activity`, and `artifact`;
- `waiting`, `warning`, and `blocked`; and
- `completed`.

Events must follow a valid lifecycle. An event after a terminal event, a second
`started` event, or an unknown event type fails conformance. Normalized events
are retained below `.factory/events/<run-id>/`.

### Result

Exactly one line prefixed with `FACTORY_RESULT ` must report:

- outcome: `success`, `blocked`, `failed`, `cancelled`, or `timed-out`;
- output revisions and bounded artifact references;
- verification claims and unresolved risks; and
- optional provider-reported model, tokens, duration, or cost.

Missing usage is recorded as unavailable. The factory does not estimate it.
The result cannot contain private reasoning. Validated results are retained
below `.factory/results/<run-id>/`.

### Capabilities and conformance

Each adapter declares a protocol version, execution environment, filesystem
mode, and supported features. The current vocabulary is
`structured-planning`, `native-read-only`, `progress-events`, `cancellation`,
`session-resume`, `browser`, `subagents`, `container-execution`,
`hosted-execution`, and `usage-telemetry`.

The Control Center shows unsupported features as unavailable; roles do not gain
authority when an adapter offers more features.

Run the conformance report for every configured adapter:

```bash
./factory/factory adapter-check
```

See `factory/examples/custom-adapter.toml` and
`factory/examples/custom_protocol_adapter.py` for a minimal protocol-aware
adapter.

## Development-environment provider

The provider turns the committed Project Contract into a reproducible local
lifecycle:

```text
provision → prepare → health → preview → reset → destroy
```

Every operation reports the governed revision and Project Contract hash.

- `provision` records the checkout and contract. It reports drift rather than
  silently rewriting the repository.
- `prepare` runs only reviewed setup commands and always requires explicit
  human approval because they execute with local permissions.
- `health` checks declared tools, roots, ports, and gates and identifies the
  first failing boundary.
- `preview` owns one local application process and records its command, URL,
  log, and stop action.
- `reset` stops the provider-owned preview and clears provider state. It keeps
  source code and GitHub evidence.
- `destroy` removes provider-owned local state. It never deletes the remote
  repository, Issues, Project, pull requests, or review evidence.

Use the **Development environment** card in **Setup → Connection**, or run:

```bash
./factory/factory environment provision --repo /path/to/product
./factory/factory environment prepare --repo /path/to/product --yes
./factory/factory environment health --repo /path/to/product --gates
./factory/factory environment preview --repo /path/to/product \
  --preview-command "python3 app.py" --port 5000
./factory/factory environment reset --repo /path/to/product
```

## Evidence-backed production intake

Raw feedback is untrusted input. It cannot dispatch implementation directly.
The intake evaluator records the affected and latest revisions, environment,
focused reproduction, duplicate candidates, missing external information,
proposed acceptance criteria, and file ownership. It classifies the proposal as
exactly one of:

- `READY_TO_IMPLEMENT`;
- `READY_TO_PLAN`;
- `NEEDS_INFORMATION`; or
- `WAIT`.

Feature requests route to planning. A bug can reach triage only after a person
approves a causal reproduction and records a reason. Collection, setup, and
unrelated failures never count as reproduction proof. Corrections preserve the
original sanitized case in `.factory/intake/cases.jsonl`.

```bash
./factory/factory intake evaluate request.json --repo /path/to/product
./factory/factory intake correct CASE_ID correction.json --repo /path/to/product
./factory/factory approve-intake ISSUE --case CASE_ID \
  --reason "Reproduction and ownership reviewed" --repo /path/to/product --yes
```

In Live mode, the issue listener uses this same proposal boundary. Existing
Issues form its baseline, and Factory-created Issues do not recursively enter
intake.

## Reviewed compounding

The factory can aggregate bounded observations across runs and propose an
improvement. A proposal requires two repeated observations or one explicit
high- or critical-severity failure. It names the evidence, expected effect,
possible regression, and verification plan.

The report collects retained planning corrections, Ticket retries, verifier
rejections, false-green Acceptance Tests, diff-budget exceptions, code-review
findings, and Monitor findings. Evidence references are deduplicated, so
regenerating a report does not manufacture a repeated signal.

```bash
./factory/factory improve report --repo /path/to/product
./factory/factory improve decide SUGGESTION_ID --decision accepted \
  --reason "Open a separate reviewed pull request" --repo /path/to/product
```

An improvement report cannot edit or approve the Factory Charter. Accepted
suggestions still require a separate human-reviewed change. Provider usage is
included only when the adapter reports trustworthy values.

## Non-authoritative merge steward

The merge steward removes mechanical queue work without owning the shipping
decision. It checks the exact candidate head, required gates, Code Review,
unresolved comments, protected paths, Acceptance Test hash, base branch, and
branch protection.

Its states are `ready-for-human-merge`, `steward-updating`, and
`human-decision-required`. When synchronization changes the candidate head, all
revision-bound gates and Code Review are revoked and must run again. Semantic
conflicts always stop for a person. The steward never merges.

```bash
./factory/factory steward ISSUE --repo /path/to/product
./factory/factory steward ISSUE --synchronize --repo /path/to/product --yes
```

Standard and Assured keep exact-revision human merge authority.

## Optional triggers and workspaces

Trigger proposals accept `schedule`, `webhook`, `issue`, `cli`, or
`control-center` events. Authentication is an external boundary; the trigger
contract validates a bounded event ID and atomically deduplicates its payload.
Replaying the same event is idempotent. Reusing an event ID with another
payload fails. A trigger always proposes intake and cannot dispatch work.

```bash
./factory/factory trigger webhook EVENT_ID event.json --authenticated \
  --repo /path/to/product
```

Single-repository operation remains the default. An optional
`factory.workspace.toml` names related repository revisions, read and write
ownership, the Ticket and pull-request target, shared services, dependency
order, and combined verification. Missing repositories, revision drift, or a
required service without a health interface block before implementation and
name the configured recovery owner.

```bash
./factory/factory workspace-check --repo /path/to/product
```

These contracts prepare a future durable remote control plane without forcing
database, worker-pool, or hosted-execution complexity into the workshop.

## Authority summary

| Interface | May propose | May decide |
| --- | --- | --- |
| Agent Adapter | artifacts, progress, result, risks | no policy or merge decisions |
| Environment provider | health, drift, preview evidence | no unreviewed setup or source deletion |
| Intake evaluator | classification and governed Ticket | no dispatch |
| Compounding engine | reviewed improvement | no Charter or configuration edit |
| Merge steward | synchronize and recommend exact revision | no semantic conflict resolution or merge |
| Trigger | deduplicated intake proposal | no lifecycle bypass |
| Human gate | approve product, policy, tests, exceptions, and exact revision | the decisions named by the Charter |

The stable rule is: extensions propose; deterministic validation and approved
policy decide; a named person remains accountable where judgment matters.
