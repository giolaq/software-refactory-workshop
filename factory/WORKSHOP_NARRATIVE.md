# Workshop narrative and slide notes

Keep procedural instructions on the website. Use these notes to explain the
decisions around those instructions. Follow the timing in the
[three-hour plan](WORKSHOP_PLAN_3_HOURS.md).

## 1. Begin with a decision, not an installation

Show a working application and a plausible pull request.

Ask: “Would you merge this?”

Let people answer before revealing that the review applies to an earlier commit.
The application may look right, but the evidence does not cover the candidate.

Say: “Today you will produce a change another engineer can inspect without
trusting the agent's statement that it is done.”

Do not open with a complete live factory run. Use prepared evidence for this
short example, clearly labeled.

## 2. Define the factory through familiar engineering work

An AI software factory is a repeatable delivery workflow combining coding agents
with repository rules, tests, review, and explicit human decisions. A request
enters the workflow. A candidate leaves only with the required evidence and
approval.

Three actors matter:

- An agent proposes plans, tests, code, or review findings.
- The orchestrator enforces workflow rules and records state.
- A person settles ambiguity and accepts the exact change.

This is not a replacement for engineering responsibility or a security sandbox.
Git worktrees separate changes; they do not isolate the host filesystem,
credentials, or network.

### Why now

Coding CLIs can perform substantial repository work, while Git and CI already
provide durable coordination and verification. The opportunity is to connect
those capabilities into something repeatable. The unresolved question is whether
the extra coordination improves a particular team's outcomes enough to justify
its operating cost.

Avoid claims that agents always make development faster. This session teaches
how to evaluate and control the workflow.

## 3. Intent still needs human judgment

Use the bounded genre-search request. “Find films quickly” leaves decisions
unanswered. Search which fields? What happens with no matches? How does a viewer
know the result is correct?

Ask attendees to make one example explicit and request a Product Review revision.
The important event is their correction, not the length of the generated plan.

## 4. Four experts must agree about one change

Teach four questions:

1. Product Review: what changes for the user?
2. System Architecture: which responsibilities and data paths are affected?
3. Program Design: what contracts and code structure implement that behavior?
4. Vertical Slices: what user-visible result can be delivered and verified first?

Trace one requirement across the artifacts. Do not read every document aloud.
For the search exercise, template data, filtering behavior, and regression tests
belong together. A ticket called “build the backend” is not automatically a
complete user-facing slice.

## 5. A failing test is evidence to inspect

Show three failures: a missing dependency, a relevant assertion, and an irrelevant
assertion. Ask which one justifies implementation.

RED PROVED records the runner's classification. A person must still inspect
whether the assertion represents the agreed requirement. Later, show those same
protected tests passing on the candidate.

The QA and Implementation roles can use the same model. Different roles
help separate responsibilities but do not eliminate correlated mistakes.

## 6. Execution creates a candidate, not permission

Show the ticket, isolated worktree, checks, and review record. Explain the next
action when work stops:

- Working: leave the agent running.
- Dependency wait: inspect the prerequisite.
- Human wait: complete the requested decision.
- Failed check: inspect the cause before retrying.

A retry without a changed cause is not recovery. A reset should say what it
preserves and discards. Do not remove a gate merely because the presentation is
running late.

## 7. Accept the exact revision

Return to the opening question. Inspect the actual diff, test results, and review
for the current candidate. A later code change invalidates earlier evidence where
the policy requires re-verification.

Explain the identity limitation: a Factory PR comment from the author identity
may not satisfy an organization's independent-review policy. Keep the final
human merge decision visible.

Then run the merged application. Verify the behavior, not just the server's
ability to start. Export the evidence packet; incomplete work remains incomplete.

## 8. Decide whether this helps your team

Now introduce the five layers as an implementation map, not a prerequisite
vocabulary test:

- Compute: where work runs.
- Development environment: checkout, dependencies, services, and checks.
- Inner harness: the coding CLI and its tools.
- Outer harness: planning, orchestration, verification, and retry rules.
- Control plane: operator actions and durable work records.

Use the [pilot worksheet](WORKSHOP_PILOT.md). Engineers identify a verifiable
change. Tech leads specify review and recovery ownership. CTOs evaluate costs,
risks, and adoption criteria.

Count accepted outcomes, attempts, review effort, and provider cost when known.
Agent activity is not itself value. If candidates arrive faster than people can
review them, adding agents can increase the queue.

A lower-cost profile is a tradeoff to justify, not a way to evade failed checks.
Existing tools may already meet the need. Allow “do not build a factory for this”
as a reasoned conclusion.

## Close

Ask attendees to explain stale review, invalid RED, and limited review capacity
using new examples. Then ask for one bounded next action with an owner.

End with: “Keep the decisions and evidence you need. Start with one useful change,
measure the overhead, and expand only when the workflow earns it.”
