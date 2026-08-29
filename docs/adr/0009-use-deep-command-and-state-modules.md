# ADR 0009: Use deep command and state modules in the control plane

## Status

Accepted

## Context

The factory accumulated repository setup, diagnostics, planning, delivery,
review, recovery, and workshop presentation behavior. Three public functions
became central switchboards: the Control Center command builder, the CLI entry
point, and the ticket lifecycle. Their branch counts made unrelated changes
interfere and made it difficult to see which module owned a policy.

Splitting code by line count alone would create shallow helpers and preserve the
same coupling. Introducing a generic workflow framework would hide the workshop
lifecycle behind abstraction that the project does not need.

## Decision

Keep the existing public CLI and Control Center contracts, and deepen their
implementations:

- route allowlisted actions to cohesive command families;
- collect diagnostics by operational boundary behind `run_doctor()`;
- resolve journey guidance as a prioritized state machine;
- separate ticket preparation and an implementation attempt while keeping
  retry and lifecycle authority in `Factory.process()`; and
- enforce a dependency-free complexity budget in tests.

The global production-function budget is 75 using the repository's conservative
McCabe-style score. Public dispatch interfaces and primary state machines have
tighter budgets. Complexity extraction is accepted only when the new seam owns
one concept, policy boundary, or lifecycle phase.

## Consequences

- Adding a command extends one registry and one command family instead of a
  repository-wide conditional.
- Diagnostic and lifecycle phases can be characterized independently.
- Control Center and CLI behavior remain backward compatible.
- The score is a regression signal, not a substitute for design review or test
  coverage.
- Some domain-heavy exporters and recovery functions remain below the global
  budget and can be deepened when their behavior changes.

## Rejected alternatives

- **Create one class per command.** This would add dozens of shallow types with
  little leverage in a workshop-scale codebase.
- **Adopt a workflow framework.** The additional runtime and indirection would
  make authority and failure recovery harder to inspect.
- **Suppress or raise the budget.** That preserves the hotspot and provides no
  structural improvement.
