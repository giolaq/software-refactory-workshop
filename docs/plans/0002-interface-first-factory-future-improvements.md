# Interface-first Factory and workshop future improvements

**Status:** Implemented for the local, optional-contract scope  
**Owner:** Workshop lead  
**Created:** 2026-08-29  
**Baseline:** `workshop-v1.1.3`, `main` at `8df3ad4`  
**Scope:** Factory architecture, Agent Adapter interfaces, execution
environments, intake, observability, workshop website, and narration

## Implementation record

Implemented on `codex/feat-interface-first-factory` for `workshop-v1.2.0`:

| Milestone | Implementation |
| --- | --- |
| 0 · Teach the layers | Five-layer Control Center and website map, review-bottleneck narration, provider-specific capability comparison, prototype/Vertical Slice distinction, layer recovery, and own/buy/bring-existing Canvas |
| 1 · Adapter Protocol | `adapter_protocol.py`, versioned capability declarations, normalized local assignments/events/results, compatibility wrapper, `adapter-check`, and a custom protocol adapter example |
| 2 · Environment provider | `environment_provider.py` local `provision` → `prepare` → `health` → `preview` → `reset` → `destroy` lifecycle, CLI, Control Center card, contract/revision evidence, and fail-closed tests |
| 3 · Production intake | `intake_evidence.py`, four exact classifications, sanitized retained cases, issue-listener proposal boundary, named human approval, corrections, CLI, and Control Center review |
| 4 · Compounding | `compounding_report.py`, repeated/high-severity evidence threshold, reviewed decisions, trustworthy-usage boundary, CLI, and Control Center report |
| 5 · Merge steward | `merge_steward.py`, exact-head readiness, safe candidate synchronization, automatic evidence revocation, semantic-conflict stop, CLI, and Control Center state/action |
| 6 · Triggers and workspace | idempotent trigger proposal contract, optional `factory.workspace.toml` validation, CLI, Control Center visibility, and fail-closed tests |

Deliberately deferred behind the interfaces: disposable container or hosted
providers, a database-backed multi-user control plane, remote worker leases,
service provisioning, and distributed multi-repository transactions. The plan
requires a demonstrated use case before these become default complexity. The
local workshop remains single-repository and credential-free in Rehearsal.

This roadmap complements the
[production-minded Factory roadmap](0001-production-minded-factory-and-workshop-roadmap.md).
It does not replace the existing human-owned Charter, causal QA, remote claims,
review/rework loop, or exact-revision human merge model.

## Inputs

- [Boundary: *How to Build a Software Factory for AI Coding Agents*](https://www.youtube.com/watch?v=tGbjIvvYuHE)
- [Requested video moment: interface layer first](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=3848s)
- [Detailed video analysis](../research/boundary-software-factory-video-analysis.md)
- [Current Factory architecture](../../factory/ARCHITECTURE.md)
- [Current Agent Adapter configuration](../../factory/CONFIGURATION.md)
- [Current workshop outline](../../factory/WORKSHOP_OUTLINE.md)

The video is an informal practitioner discussion, not an independent benchmark.
Its automation percentages, classifier accuracy, and infrastructure choices are
heuristics to test, not universal requirements.

## Executive direction

Evolve Software (re)-Factory as a **composable, interface-first delivery
system**. Keep its strongest properties—governed planning, independent QA,
causal evidence, bounded review, inspectable recovery, and accountable human
decisions—while making the boundaries between compute, development
environment, agent harness, and control plane explicit.

The project should teach and implement this distinction:

> A coding agent produces a change. A software factory repeatedly turns demand
> into a governed, observable, reviewable change.

The purpose is not to build every layer ourselves. Teams should be able to own,
buy, or replace individual layers without rewriting the Product → Ticket →
evidence → decision lifecycle.

## Target layer model

The workshop and documentation should introduce four architectural layers,
with the harness split into inner and outer parts:

| Layer | Responsibility | Current implementation | Future direction |
| --- | --- | --- | --- |
| Compute | Run an isolated agent workload | Attendee machine; local processes; Git worktrees; adapters may declare `local`, `container`, or `hosted` | Make execution providers real and replaceable; retain local as the workshop default |
| Development environment | Supply checkout, runtimes, dependencies, services, identity, network access, gates, and previews | Project Contract, `prepare`, `doctor`, ports, setup commands, managed checkout | Add a reproducible `provision` → `prepare` → `health` → `preview` → `reset` → `destroy` lifecycle |
| Inner harness | Execute the coding or reasoning loop | Claude, Codex, Cursor, mock, or custom command adapter | Add a versioned runner protocol and honest capability negotiation |
| Outer harness | Apply roles, prompts, policy, retries, QA, review, and evidence contracts | Profiles, Charter, roles, planning pipeline, QA, Supervisor, review/rework, Handoff Receipts | Preserve as the governed core; allow extensions to propose actions through narrow interfaces |
| Control plane | Dispatch work, expose state and traces, enforce decisions, and coordinate people and workers | Orchestrator, Control Center, GitHub Projects, remote claims, issue listener, Monitor, Evidence Packet | Add optional triggers, cross-run evaluation, usage telemetry, and durable remote workers only when required |

GitHub Projects remains the shared human work-management view. The Control
Center remains the engine-room control plane. Agent CLIs remain replaceable
inner harnesses.

## Current comparative position

### Where Software (re)-Factory is stronger

1. **Planning rigor.** Product Review, System Architecture, Program Design, and
   Vertical Slices are schema-validated, hash-bound, traceable artifacts with
   explicit human gates.
2. **Causal QA.** Independent QA proves the same focused command RED before
   implementation and GREEN afterward. Protected hashes prevent the
   implementation role from weakening accepted evidence.
3. **Human-owned governance.** The Factory Charter defines consequence, path
   policy, budgets, stop conditions, review capacity, and merge authority.
4. **Closed review loop.** Code-review comments return to implementation on the
   same branch and pull request. Required gates and exact-revision review run
   again before a merge recommendation.
5. **Coordination.** Dependency scheduling, atomic remote Ticket claims,
   worktrees, Supervisor proposals, and Handoff Receipts constrain parallel
   work.
6. **Recovery and evidence.** The Control Center explains why work stopped,
   shows the next safe action, and retains bounded evidence without exporting
   raw prompts, credentials, or hidden model reasoning.
7. **Workshop reproducibility.** Rehearsal demonstrates the topology without
   GitHub or model credentials.

### Where Software (re)-Factory is less mature

1. **Environment provisioning.** The Project Contract describes and checks an
   environment, but does not provision disposable compute, dependent services,
   identity, or preview URLs.
2. **Adapter interface depth.** Command templates and capability declarations
   do not yet form a complete versioned event, result, cancellation, and resume
   protocol.
3. **Cross-run learning.** Corrections and operational metrics are recorded but
   do not yet produce reviewed outer-harness improvement proposals.
4. **Production intake.** The Live issue listener validates Ticket structure;
   it does not prove a reproduction, check the latest revision, or deduplicate
   raw feedback before admission.
5. **Usage visibility.** Time and retry evidence exists, but trustworthy
   provider token and cost data is not normalized when available.
6. **Triggers.** UI, CLI, issue listening, and Monitor exist, but schedule and
   generic webhook inputs are not first-class governed interfaces.
7. **Multi-repository workspaces.** One Project Contract currently governs one
   target repository.
8. **Remote operations.** The Control Center is a strong local control plane,
   not a durable multi-user dispatcher with a database and worker pool.

## Design principles

1. **Interfaces first, abstractions only where substitution is valuable.** Do
   not wrap a provider API merely to hide it. Standardize factory invariants
   and expose meaningful provider-specific capabilities.
2. **Roles stay stable; adapters remain replaceable.** Changing Claude, Codex,
   Cursor, a model, or an execution provider cannot silently change authority.
3. **The orchestrator remains lifecycle authority.** Agents and extensions
   propose actions. Deterministic validation and approved policy decide what
   happens.
4. **The development environment is part of the product.** Repository setup,
   dependencies, identity, services, previews, and gates are not incidental
   prerequisites.
5. **Human attention is the scarce resource.** Optimize for small,
   evidence-rich decisions, not the number of agents or pull requests.
6. **Automate routine motion; escalate judgment.** Do not optimize for zero
   humans. Preserve explicit ownership of product intent, policy, exceptions,
   and normal shipping decisions.
7. **Learning remains reviewable.** Metrics may propose prompt, skill,
   contract, or profile changes. They must never edit the Factory Charter or
   weaken policy automatically.
8. **Production complexity is optional.** Keep the beginner path local,
   single-repository, and inspectable. Add hosted execution, triggers, and
   multi-repository coordination only for demonstrated use cases.

## Milestone 0 — Teach the layers and the review bottleneck

**Goal:** make the workshop explain what a software factory is before asking
attendees to operate it.

### Deliverables

- Add a layer diagram to the workshop website and facilitator outline:
  compute → development environment → inner harness → outer harness → control
  plane.
- Map each layer to the live workshop:
  - laptop or runner;
  - Project Contract, `prepare`, and `doctor`;
  - Claude, Codex, Cursor, or a custom adapter;
  - roles, Charter, QA, retries, and review;
  - Control Center, orchestrator, and GitHub Projects.
- Reframe setup as proving the development-environment contract.
- Associate every preflight failure with its layer and one recovery action.
- Make the central conflict explicit: generation is fast, but review capacity,
  product judgment, and accountability remain scarce.
- Show one role fulfilled by two different Agent Adapters and identify one real
  capability difference.
- Explain prototype versus delivery:
  - a prototype may be disposable and exists to clarify intent;
  - a Vertical Slice is bounded, tested, reviewed, and intended to merge.
- Finish with a build/buy/bring-existing Factory Canvas.

### Acceptance criteria

- An attendee can identify all five boxes in the layer diagram and point to the
  component used in the workshop for each one.
- An attendee can explain why a missing dependency or invalid login is an
  environment-contract failure, not a reason to retry the coding agent.
- The website never defines a factory as merely a collection of agents.
- The story presents parallelism as a cost controlled by review capacity, not
  a success metric.
- The closing exercise records what the attendee will own, buy, or replace at
  each layer.

## Milestone 1 — Define Factory Adapter Protocol v1

**Goal:** make the control-plane-to-harness boundary explicit without erasing
useful provider differences.

### Standardize

- Assignment identity: run, role, Ticket, attempt, repository or worktree,
  prompt reference, profile, Charter hash, and policy hashes.
- Declared boundaries: filesystem mode, allowed roots, network expectation,
  environment allowlist, credential names, execution environment, and timeout.
- Structured progress events: started, bounded status, tool activity, artifact,
  waiting, warning, blocked, and completed.
- Final result: outcome, output revisions, artifacts, verification claims,
  unresolved risks, and optional trustworthy usage data.
- Control behavior: cancellation, timeout, retry, and optional session resume.
- Protocol and capability versions.

### Preserve provider-specific capabilities

The capability contract should state whether an adapter supports:

- structured planning output;
- native read-only execution;
- streamed tool progress;
- resumable sessions;
- subagents;
- browser or UI verification;
- container or hosted execution; and
- reliable model, token, duration, or cost telemetry.

The Control Center must show unavailable capabilities as unavailable. It must
not imply that all adapters are equivalent.

### Compatibility

- Keep current command adapters working through a compatibility wrapper.
- Add protocol fixtures and a conformance command for custom adapters.
- Reject unknown required fields, invalid lifecycle transitions, and malformed
  final results.
- Preserve useful provider-native output locally without publishing raw traces
  to remote summaries.

### Acceptance criteria

- Claude, Codex, Cursor, mock, and one example custom adapter pass the same
  base conformance suite.
- A capability-dependent role fails before dispatch when the selected adapter
  cannot fulfil it.
- The Control Center receives normalized progress and completion events without
  parsing provider-specific prose.
- Existing command adapters remain usable during migration.

## Milestone 2 — Add an execution-environment provider

**Goal:** turn the Project Contract from a checked description into a
reproducible environment lifecycle.

### Interface

Define a provider with bounded operations:

```text
provision → prepare → health → preview → reset → destroy
```

Each operation returns structured evidence and identifies the governed
repository revision and Project Contract hash.

### Local provider

- Reuse the existing checkout, virtual environment, setup commands, ports, and
  gates.
- Report drift rather than silently repairing unreviewed configuration.
- Keep `prepare` explicit because repository setup commands are trusted code
  running with the operator's permissions.
- Provide one preview record containing startup command, local URL, process
  owner, and stop action.

### Container or hosted provider

- Add only after the local interface and tests are stable.
- Create a disposable checkout and dependency environment.
- Supply scoped credentials and network access based on declared capability.
- Return a preview URL when the application supports it.
- Destroy the environment without deleting remote GitHub evidence.

### Acceptance criteria

- A clean local environment can be recreated from the committed Project
  Contract and a named repository revision.
- `health` distinguishes missing tools, dependency failures, identity failures,
  branch drift, and gate failures.
- Reset names exactly what it changes and preserves source and remote evidence.
- The documentation continues to state that a Git worktree is not a security
  sandbox.

## Milestone 3 — Add evidence-backed production intake

**Goal:** turn raw feedback into a reproducible, governed Ticket before an
the Implementation Role receives it.

### Intake funnel

```text
Raw feedback
  → check affected and latest revisions
  → search duplicate candidates
  → attempt a focused reproduction
  → identify missing external information
  → classify
  → human review when uncertain
  → governed Ticket
```

The outcome must be exactly one of:

- `READY_TO_IMPLEMENT`;
- `READY_TO_PLAN`;
- `NEEDS_INFORMATION`; or
- `WAIT`.

### Required evidence

- affected revision and environment;
- latest revision checked;
- focused reproduction command and bounded output, or a reason reproduction is
  impossible;
- duplicate candidates and confidence;
- required external data or human decision;
- proposed acceptance criteria and file ownership; and
- source-feedback reference without executing untrusted attached code.

### Evaluation

- Preserve historical intake decisions as sanitized evaluation cases.
- Measure reproduction validity, duplicate suggestion usefulness,
  classification reversals, and human correction rate.
- Treat classifier percentages as local measurements, not universal targets.
- Route hard-to-reproduce or externally dependent issues to a person rather
  than weakening the admission criteria.

### Acceptance criteria

- Raw feedback cannot start implementation directly.
- Collection errors, environment failures, and unrelated failures do not count
  as a reproduction.
- Existing planning and Monitor issues cannot recursively re-enter intake.
- A human can correct the proposed Ticket and preserve a record of the original
  classification.

## Milestone 4 — Add reviewed compounding engineering

**Goal:** learn from repeated runs without letting the factory rewrite its own
authority.

### Aggregate bounded signals

- planning artifact corrections;
- invalid structured outputs by adapter and role;
- retry and verifier rejection rates;
- Acceptance Tests that were already green before implementation;
- recurring code-review findings;
- diff-budget exceptions;
- human wait and review-queue pressure;
- repeated Monitor findings and changed hotspots; and
- classification decisions later contradicted by delivery evidence.

### Produce an improvement report

The report may suggest:

- a prompt or skill change;
- a Project Contract correction;
- a new deterministic gate;
- a different adapter for a particular role;
- a profile or retry-budget adjustment; or
- documentation and recovery improvements.

Every suggestion must name its source evidence, expected effect, possible
regression, and verification plan. Accepted changes go through a separate,
human-reviewed pull request.

### Optional usage telemetry

- Accept model, input/output tokens, provider duration, and cost only when the
  adapter reports trustworthy values.
- Store `unavailable` rather than estimating missing values.
- Keep credentials, raw prompts, unrestricted logs, and hidden reasoning out
  of summaries.

### Acceptance criteria

- No metric or agent may edit or approve the Factory Charter.
- Every proposed improvement links to at least two bounded observations or one
  explicit high-severity failure.
- A human can reject a suggestion without changing the delivery configuration.
- Before-and-after evaluation uses the same retained cases.

## Milestone 5 — Add a non-authoritative merge steward

**Goal:** automate merge-queue mechanics without hiding or transferring the
human shipping decision.

### Behavior

- Begin only after required gates and code review approve the current
  candidate.
- Keep the branch synchronized with the default branch when policy allows.
- Rerun required gates and code review after every candidate-head change.
- Stop on semantic conflicts, changed protected paths, changed acceptance
  evidence, branch-protection failure, or an unresolved review comment.
- Present the new merge-ready exact revision to the human.
- Keep the current exact-revision human merge as the Standard and Assured
  default.

An optional future Charter policy may delegate purely mechanical completion
after a named human records merge intent, but any candidate change must revoke
that authorization unless policy defines and tests a narrower safe case.

### Acceptance criteria

- The steward cannot waive checks, resolve semantic conflicts silently, or
  merge an unreviewed head.
- A base synchronization that changes the candidate reruns all revision-bound
  evidence.
- The Control Center distinguishes `ready for human merge`, `steward updating`,
  and `human decision required`.

## Milestone 6 — Add optional triggers and workspace coordination

**Goal:** support production integrations without complicating the beginner
path.

### Trigger adapters

- Accept schedule, webhook, issue, CLI, and Control Center inputs through one
  governed intake proposal interface.
- Authenticate and deduplicate every external event.
- Make retries idempotent.
- Never let an external event bypass planning, Charter, QA, review, or merge
  policy.

### Multi-repository workspace contract

Define an optional coordination contract containing:

- related repositories and required revisions;
- read-only and writable ownership per repository;
- shared services and environment requirements;
- the repository that receives each Ticket, branch, and pull request;
- cross-repository dependency ordering; and
- combined verification requirements.

Keep single-repository operation as the workshop and default path. Do not use
Git submodules as the mandatory coordination mechanism.

### Durable remote control plane

Consider a database, worker registry, lease model, and remote dispatcher only
when the project must support multiple operators or execution workers. GitHub
claims and summaries remain authoritative shared evidence during any migration.

### Acceptance criteria

- Replayed webhooks and schedule retries do not create duplicate Tickets or
  agents.
- A multi-repository run names every affected revision and pull request.
- A missing repository or service blocks before implementation with a clear
  owner and recovery action.
- Rehearsal and the three-hour workshop remain independent of these features.

## Workshop narration

Use this concise opening:

> AI made code generation cheap. That does not make software delivery cheap:
> intent, environment setup, verification, review, and accountability remain
> scarce. A software factory connects those concerns through explicit
> contracts. The agent is one replaceable part of the harness; the factory is
> the system around it. We plan enough to create reviewable slices, run each
> slice in an isolated workspace, prove behavior with independent evidence, and
> stop when human judgment is valuable.

### Recommended progression

1. **Locate the layers.** Identify compute, development environment, inner and
   outer harness, and control plane.
2. **Prove readiness.** Prepare the repository and run preflight. Fix the first
   failed layer before retrying.
3. **Turn intent into contracts.** PRD → Product Review → System Architecture →
   Program Design → Vertical Slices.
4. **Protect review capacity.** Publish bounded Tickets with ownership,
   dependencies, and diff budgets.
5. **Produce causal evidence.** Independent QA proves RED; implementation and
   gates prove GREEN.
6. **Automate until judgment matters.** Supervisor, agents, verification, and
   review/rework loops operate within approved limits.
7. **Make the accountable decision.** A person inspects the evidence and merges
   the exact reviewed revision.
8. **Design the attendee's factory.** Choose what to own, buy, bring, and
   replace at each layer.

### Factory Canvas additions

| Layer | Own, buy, or bring existing? | Required interface | Required evidence | Failure owner |
| --- | --- | --- | --- | --- |
| Compute |  |  |  |  |
| Development environment |  |  |  |  |
| Inner harness |  |  |  |  |
| Outer harness |  |  |  |  |
| Control plane |  |  |  |  |

The closing message is not “copy this Python implementation.” It is:

> Define stable responsibility, evidence, and authority contracts so agents,
> environments, tools, and policies can change independently.

## Suggested implementation order

1. Milestone 0: workshop layer model and narration.
2. Milestone 1: Adapter Protocol v1 and compatibility tests.
3. Milestone 2: local execution-environment provider.
4. Milestones 3 and 4: reproducible intake, evaluation, and reviewed learning.
5. Milestone 5: merge steward.
6. Milestone 6 only after a real hosted, scheduled, or multi-repository use case
   exists.

Do not teach a future interface as implemented before its code, fail-closed
tests, Control Center behavior, and recovery documentation are complete.

## Success measures

- Attendees can correctly locate a setup or execution failure in one factory
  layer.
- Swapping an adapter does not change role authority, gates, or evidence
  requirements.
- Custom adapters pass a versioned compatibility suite.
- A clean environment can be recreated from a Project Contract and repository
  revision.
- Raw feedback does not enter implementation without a reviewed reproduction
  or explicit human exception.
- Cross-run reports identify repeated failures and produce reviewable
  improvement proposals.
- Standard and Assured retain accountable exact-revision human merge.
- Human wait, false gate failures, escaped defects, retries, and review burden
  improve without using agent count or pull-request count as vanity metrics.
- The core workshop remains achievable in the scheduled three-hour session,
  including its 10-minute break and human review activities.

## Explicit non-goals and guardrails

- Do not aim for a fully autonomous organization or remove named human
  accountability.
- Do not copy the video's unsandboxed MacBook assumption for arbitrary
  repositories or raw user input.
- Do not treat Git worktrees as process, network, credential, or host isolation.
- Do not build every infrastructure layer merely because it appears in the
  model.
- Do not replace GitHub Projects with the Control Center; they serve different
  audiences.
- Do not make one provider's private lifecycle behavior a mandatory universal
  abstraction.
- Do not publish raw prompts, hidden reasoning, unrestricted logs, environment
  values, or credentials.
- Do not allow an agent, Monitor, metric, or improvement report to edit the
  Factory Charter automatically.
- Do not add multi-repository, schedule, webhook, or remote-worker complexity
  to the beginner workshop path.
- Do not use throughput, agent count, or generated-code volume as primary
  success measures.
