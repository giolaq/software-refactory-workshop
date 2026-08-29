# ADR 0008: Use explicit interfaces for replaceable factory layers

- Status: Accepted
- Date: 2026-08-29
- Decision owners: Workshop lead

## Context

The factory already separated Agent Roles from Agent Adapters, but command
templates, environment setup, raw issue intake, cross-run learning, merge queue
mechanics, triggers, and multi-repository coordination did not share explicit
contracts. Provider prose sometimes carried lifecycle state, and setup was
treated as a prerequisite rather than a governed product boundary.

We want teams to replace compute, development environments, and inner harnesses
without weakening the outer harness or human authority. We also want the
beginner workshop to stay local and single-repository.

## Decision

Adopt a five-layer model: compute, development environment, inner harness,
outer harness, and control plane.

Introduce narrow, fail-closed interfaces:

1. Adapter Protocol v1 for structured assignments, bounded events, results,
   capability negotiation, and conformance.
2. A local execution-environment lifecycle of `provision`, `prepare`, `health`,
   `preview`, `reset`, and `destroy`.
3. Evidence-backed raw-feedback intake whose output is a non-dispatching
   proposal until human review.
4. Reviewed compounding reports that may propose changes but cannot edit the
   Charter or delivery configuration.
5. A non-authoritative merge steward that may synchronize a candidate and
   revoke stale evidence but never merge.
6. Optional idempotent trigger proposals and a multi-repository workspace
   contract. Single-repository local operation remains the default.

Compatibility command adapters remain supported. GitHub Projects remains the
shared work-management view, the Control Center remains the local engine room,
and the orchestrator remains lifecycle authority.

## Consequences

- Provider-native capabilities stay visible instead of being flattened behind
  a lowest-common-denominator abstraction.
- A role fails before dispatch when its declared capability is unavailable.
- Setup commands remain an explicit human-approved action because they run
  repository code with local permissions.
- Every external input is a proposal; it cannot bypass planning, Charter, QA,
  review, or merge policy.
- Exact-revision human merge remains the Standard and Assured default.
- Protocol and provider records add local evidence files below `.factory/`.
- Hosted isolation, durable remote workers, and multi-user dispatch remain
  future implementations behind these interfaces rather than workshop
  dependencies.

## Rejected alternatives

- **Treat every provider as an interchangeable command.** This hides important
  differences such as native read-only execution, session resume, browser
  verification, and trustworthy usage telemetry.
- **Let agents or triggers dispatch and merge directly.** This transfers
  lifecycle authority away from deterministic policy and accountable people.
- **Require containers, remote workers, or multi-repository setup in the core
  workshop.** This adds operational complexity before substitution is needed.
- **Let metrics rewrite prompts or policy automatically.** Learning without a
  reviewed change can silently weaken the factory's authority model.
