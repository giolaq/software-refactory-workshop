# Workshop narrative and slide notes

Keep procedural instructions on the website. Use these notes to explain the
decisions around those instructions. Follow the timing in the
[three-hour plan](WORKSHOP_PLAN_3_HOURS.md).

## 1. Begin with a decision, not an installation

Show Pocket Cinema and introduce Hearth & Harvest Foods, a customer that wants
a recipe app called TableStory. Show a prepared before-and-after example, labeled
as prepared, then a plausible pull request for the transformation.

Say: “You have a working product. A new customer needs a different product.
Today you will use the factory to transform it, while deciding what to reuse,
what must change, and what evidence makes the result acceptable.”

This is product transformation, not only refactoring: behavior and contracts
intentionally change. Recipes need ingredients and cooking steps; movie fields
with new labels are not enough.

Ask: “Would you merge this?”

Give people 30 seconds to decide alone. Ask two people for their evidence before
revealing that the review applies to an earlier commit.
The application may look right, but the evidence does not cover the candidate.

Say: “Today you will produce a change another engineer can inspect without
trusting the agent's statement that it is done.”

Do not open with a complete live factory run. Use prepared evidence for this
short example, clearly labeled.

## 2. Define the factory through familiar engineering work

Start with four verbs: **agree on the change → build it → inspect the evidence
→ accept it**. Use them as the section titles in slides. Keep the factory's exact
button labels in the website; attendees need not learn the whole architecture
before making their first decision.

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

Call this a working reference implementation, not a proven efficiency gain or
a production-readiness guarantee. Its usefulness must survive measurement and
the attendee's access, review, and operating constraints.

Introduce “Charter” when approving operating limits, “acceptance tests” when
reviewing behavior evidence, and “receipt” when inspecting a recorded result.
Do not lead with a glossary, all eight roles, or deployment architecture.

## 3. Intent still needs human judgment

Use the recipe-app PRD. “Make it a recipe app” leaves decisions unanswered.
What does a recipe contain? Can cooks search by ingredient? What belongs in My
Cookbook? Which existing behavior should survive, and which movie APIs must go?

Use one thread from now to the final preview: **find a recipe by ingredient →
read its cooking steps → save it to My Cookbook**. It connects decisions across
artifacts; it does not remove the full rebrand, API, mobile/TV, or cleanup scope.

Give attendees a weak requirement such as “My Cookbook should work well.” Ask
them to write an observable outcome before discussing it. Then inspect their
actual Product Review and request a justified revision if needed.
The important event is their correction, not the length of the generated plan.

## 4. Four experts must agree about one change

Teach four questions:

1. Product Review: what changes for the user?
2. System Architecture: which responsibilities and data paths are affected?
3. Program Design: what contracts and code structure implement that behavior?
4. Vertical Slices: what user-visible result can be delivered and verified first?

Trace one requirement across the artifacts. Do not read every document aloud.
Follow recipe discovery from data and API contracts through cards, details, and
tests. Then inspect how My Cookbook and the TV journey depend on that foundation.
A ticket called “build the backend” is not automatically a complete user-facing
slice. The plan must cover the entire transformation, not just its first ticket.

Challenge the proposed work: does a generic event-bus ticket really need to block
recipe search? Ask for a concrete requirement before accepting that dependency.
Use the prepared example if the Live plan has no such issue; do not sabotage a
correct plan to create a teaching moment.

## 5. A failing test is evidence to inspect

Show three failures: a missing dependency, a relevant assertion, and an irrelevant
assertion. Ask which one justifies implementation.
Collect individual answers before explaining them. Ask each person to identify
the assertion and expected behavior, not just a failure label.

RED PROVED records the runner's classification. A person must still inspect
whether the assertion represents the agreed requirement. Later, show those same
protected tests passing on the candidate.

The QA and Implementation roles can use the same model. Different roles
help separate responsibilities but do not eliminate correlated mistakes.

## 6. Execution creates a candidate, not permission

Start eligible implementation as soon as the required plan and QA approvals are
complete, targeting the 65–80 minute block. Do not wait for the whole room. Teach
verification and recovery while work runs, and handle later QA and merge decisions
as they become ready. A slow agent changes the evidence used for the discussion,
not the policy or the full transformation objective.

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

Then run TableStory. Search by ingredient, open a recipe, read its cooking steps,
save it to My Cookbook, and exercise mobile and TV navigation. Inspect API and
UI terminology for leftover movie concepts. Verify behavior, not just startup.

The product is complete only when the approved transformation scope is merged
and its integrated acceptance checks pass. Export the evidence packet. If Live
work is unfinished, name the remaining tickets and resume action, then demonstrate
the finished journey on labeled prepared evidence. Do not call one merged ticket
a completed recipe product.

## 8. Decide whether this helps your team

Show one completed, recorded Live transformation using the
[run record](WORKSHOP_DRY_RUN.md#record-one-real-transformation). State its scope,
revision, provider/model, elapsed time, active human effort, retries, and available
usage. A single observation is not a speedup benchmark. Disclose missing data and
remaining defects. Do not substitute Rehearsal timings for a provider result.

Keep the [architecture map](ARCHITECTURE.md) as a follow-up reference, not another
required lecture. Explain a component only when it answers an attendee's pilot
question.

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
