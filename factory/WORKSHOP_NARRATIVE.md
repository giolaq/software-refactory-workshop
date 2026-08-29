# Software (re)-Factory workshop narrative

Duration: 3 hours  
Audience: software engineers, tech leads, architects, engineering managers, and CTOs  
Companion runbook: [WORKSHOP_PLAN_3_HOURS.md](WORKSHOP_PLAN_3_HOURS.md)

Use this document as the spoken story for the workshop. The workshop website
provides the instructions. The facilitator runbook provides setup and recovery
details. This document explains what to say, why each activity appears, and how
to connect one section to the next.

## The story in one sentence

AI can produce code quickly. A software factory turns that capability into a
repeatable delivery system with explicit intent, a known environment,
independent evidence, controlled coordination, and accountable human decisions.

## What the audience should believe at the end

Most attendees will arrive with one of two mental models:

- An AI coding agent is a faster pair programmer.
- An AI software factory is several coding agents running at the same time.

Both models are incomplete. By the end of the workshop, attendees should
understand the following points:

1. A coding agent is one replaceable worker. The factory is the delivery system
   around that worker.
2. Faster generation moves the bottleneck to intent, environments,
   verification, review, and accountability.
3. Planning is not a large document produced before coding. It is a sequence of
   reviewable contracts that reduce ambiguity before it becomes code.
4. More agents do not create safety. Isolation, ownership, evidence, limits,
   and deterministic lifecycle rules create safety.
5. Human judgment remains necessary. The factory moves it to explicit,
   evidence-rich decision points.
6. Teams should build the smallest factory that addresses their actual failure
   modes. They should not copy every control from this workshop.

## The narrative arc

The workshop follows one question:

> What must be true between receiving a PRD and making a responsible merge
> decision?

Build the answer in five acts.

| Act | Question | Audience shift |
| --- | --- | --- |
| 1. The delivery gap | Why is a coding agent not enough? | From code generation to system design |
| 2. The operating boundary | Where may the factory work, and under what rules? | From prompt settings to governed execution |
| 3. Intent becomes work | How does a PRD become reviewable Tickets? | From one large prompt to linked planning contracts |
| 4. Work becomes evidence | How do agents coordinate and prove a change? | From agent output to observable delivery state |
| 5. Evidence becomes accountability | Who decides that the exact revision can ship? | From automation theatre to an operating model |

Each act introduces a visible failure first. Add the factory capability only
after the audience understands that failure.

| Visible failure | Capability introduced |
| --- | --- |
| A plausible change solves the wrong problem | Product Review and human revision |
| Agents make incompatible design assumptions | Architecture and Program Design |
| A large request cannot be owned or reviewed | Vertical Slices and dependency waves |
| Two workers collide or duplicate work | Remote claims, ownership, and worktrees |
| Tests pass but prove nothing about the requested behavior | Independent QA with RED and GREEN evidence |
| Review comments are lost between agent runs | Revision-specific review and structured rework |
| Automation produces more decisions than people can absorb | Human-attention limits and back-pressure |
| The agent session ends and the evidence disappears | Handoff Receipts, Evidence Packet, and Monitor |

## Use one facilitation pattern throughout

Do not present the Control Center as a collection of features. Use the same
four-part pattern in every segment:

1. **Problem:** Show the engineering failure that the next capability prevents.
2. **Capability:** Name the smallest factory mechanism that addresses it.
3. **Evidence:** Inspect the artifact, revision, test, log, or policy produced by
   that mechanism.
4. **Decision:** Ask who may authorize the next transition.

Use these four questions when the room becomes uncertain:

- What is happening now?
- Who owns this phase?
- What evidence is missing or available?
- What is the next safe action, and who can authorize it?

This pattern gives engineers technical detail, gives tech leads a review and
operability model, and gives CTOs a clear view of control, cost, and
accountability.

---

## Act 1: The delivery gap

### 0–10 minutes — Open with the merge decision

Start with a concrete scene. Show a pull request created by an agent. Keep the
diff, tests, and approval state visible.

Say:

> An agent produced this pull request in a few minutes. Should we merge it?

Do not answer immediately. Ask the room what they would need to know first.
Capture answers such as:

- What problem was it meant to solve?
- Which revision did the tests run against?
- Did the agent change existing tests?
- Who reviewed the design?
- Does it conflict with another change?
- What happens if it is wrong?
- Who is accountable for the merge?

Then state the workshop thesis:

> Code generation is no longer the whole problem. The engineering problem is
> creating a trustworthy path from demand to an exact, reviewable revision.

Explain the working agreement:

- Each attendee uses a personal disposable repository.
- The facilitator uses a separate repository on screen.
- The room will inspect evidence before approving transitions.
- Finishing every Ticket is not the objective. Understanding why a Ticket may
  move is the objective.

### Attendee activity: name the unsafe shortcut

Ask each pair to choose one repeated engineering task that might benefit from
an agent. The partner names one shortcut that could make the result unsafe,
unmaintainable, or expensive to review.

Keep these examples. The final Factory Canvas activity will return to them.

### Transition

Say:

> We already know how to ask an agent for code. We now need to identify the
> system around the agent that makes its work usable.

### 10–25 minutes — Define an AI software factory

Use a direct definition:

> An AI software factory is a controlled delivery system that accepts governed
> demand, assigns bounded work to replaceable agents, verifies the result, and
> presents evidence and decisions to people.

Contrast the terms:

| Coding agent | AI software factory |
| --- | --- |
| Receives an assignment | Accepts demand through an intake and planning path |
| Produces code or analysis | Coordinates the complete delivery lifecycle |
| Uses its own session context | Supplies versioned repository and policy context |
| Reports an answer | Records artifacts, revisions, checks, and handoffs |
| May stop when the prompt is complete | Stops only at a defined lifecycle state |
| Is one provider or CLI | Can replace providers behind stable role contracts |

Explain why this matters now:

> Agents can create candidate changes faster than most teams can specify,
> verify, and review them. When generation becomes cheaper, unclear intent and
> limited review capacity become more expensive.

Avoid claims that AI removes the software lifecycle. The factory exists because
the lifecycle still matters.

### Introduce the five layers

Present the layers from the bottom up:

```text
Control plane
  lifecycle · claims · state · GitHub Projects · Control Center

Outer harness
  planning · roles · Charter · QA · gates · review · receipts

Inner harness
  Claude · Codex · Cursor · registered custom adapters

Development environment
  repository · revision · tools · dependencies · services · preview

Compute
  laptop · container · hosted runner
```

Explain only the responsibility of each layer. Do not explain every feature.

- Compute runs the workload.
- The development environment makes the codebase reproducible.
- The inner harness performs one assignment.
- The outer harness constrains the assignment and requires evidence.
- The control plane owns lifecycle state and authorized transitions.

Make the distinction explicit:

> Claude, Codex, and Cursor are not three different factories. They are
> possible inner-harness adapters. The role, evidence, and authority should not
> change just because the provider changes.

### Attendee activity: place the responsibility

Ask pairs to place these responsibilities in a layer:

- install `pytest`;
- generate a code change;
- prevent two runners from claiming the same Ticket;
- decide whether an exact revision can merge; and
- produce a preview URL.

End the act by asking one attendee why running five agents in parallel is not a
complete factory.

### Transition

Say:

> Before the factory can interpret a PRD, it must know where it is working, how
> that repository works, and what it is allowed to do.

---

## Act 2: The operating boundary

### 25–50 minutes — Connect the repository and prove readiness

Frame setup as an engineering contract, not installation overhead.

Say:

> A developer can repair an incomplete laptop setup through experience. An
> automated factory needs that knowledge to be explicit and testable.

Open the Control Center. Show **Current phase**, **Next safe action**, and
**Activity and CLI output** before opening configuration. Explain that the UI
invokes the same versioned CLI shown in the output.

Introduce four terms in this order:

1. **Project Contract:** How this repository is built, tested, started, and
   reset.
2. **Factory Charter:** Human-owned limits, protected paths, approvals, stop
   conditions, and merge authority.
3. **Factory Profile:** Which roles and controls execute for this run.
4. **Agent Adapter:** Which executable performs a role.

Use one sentence to distinguish them:

> The Project Contract describes the repository, the Charter defines authority,
> the Profile selects the operating topology, and the Adapter performs a role.

### Attendee activity: establish the boundary

Attendees connect their disposable repository, create and review the contracts,
approve the Charter, provision the development environment, prepare declared
dependencies, check health, and run preflight.

While they work, repeat this progression:

```text
Provision → Prepare → Check health → Run preflight
```

- Provision binds the repository revision and Project Contract.
- Prepare runs reviewed setup commands.
- Health proves the development environment.
- Preflight checks the wider factory, including adapters and GitHub access.

### Failure lab: repair the first failed boundary

Show a preflight with several failures. Ask attendees to start with the first
failure, identify its layer, and change the failed condition before trying
again.

Use the colleague scenario if useful:

- the local branch differs from the GitHub default branch;
- Codex is selected but not available while Claude is available; and
- `pytest` is missing.

Ask why selecting **Retry** cannot solve any of these failures. The answer is
that a retry repeats an unchanged condition. Recovery must change repository
state, adapter configuration, authentication, or environment preparation.

For CTOs and tech leads, make the operational implication clear:

> Reproducibility is not only a developer-experience concern. It determines
> whether agent output can be trusted, repeated, and audited across machines.

### Decision point

Continue only when preflight has no blocking failures. A warning may be
acceptable when it belongs to an unused optional capability.

### Transition

Say:

> The factory now knows its operating boundary. It still does not know what
> product outcome we want. That is the next contract.

---

## Act 3: Intent becomes work

### 50–65 minutes — Inspect the baseline before writing the future

Run Pocket Cinema. Ask attendees to inspect mobile, desktop, and TV behavior.

Say:

> A rebrand PRD describes a new outcome. The existing product still contains
> behavior that users and systems may depend on. If we do not name that
> behavior, an agent may remove it while appearing to complete the rebrand.

Ask pairs to record:

- one behavior that must remain;
- one behavior that must change;
- one accessibility or responsive constraint;
- one observable success condition; and
- one unresolved product question.

Open the Recipe App PRD. Ask an attendee to explain the requested change without
naming a file, framework, type, or method. This keeps the conversation at the
product boundary.

### 65–82 minutes — Product Review moves judgment earlier

Introduce the first expert only after showing the ambiguity in the PRD.

Say:

> The Product Review agent does not decide what to build. It converts the PRD
> into a testable proposal that a person can challenge and approve.

Start Product Review. Ask attendees to find one vague or unsupported claim.
They request a focused revision and compare the old and new artifact.

Emphasize three rules:

- Feedback should name the missing behavior or evidence.
- Feedback should not prescribe code unless the product contract requires it.
- Approval belongs to the exact artifact revision, not to the general idea.

For example:

> Require automated Escape and Backspace checks that preserve TV mode and
> restore focus to the invoking control.

Explain why this is a better intervention than fixing the behavior during pull
request review: the correction occurs before architecture, tickets, tests, and
implementation inherit the ambiguity.

### 82–95 minutes — Build the planning chain

Introduce the remaining experts as distinct questions:

| Expert | Question answered |
| --- | --- |
| Product Review | What user outcome do we want, and why? |
| System Architecture | Which components, data, and contracts must support it? |
| Program Design | Which types, functions, layouts, and call paths shape the code? |
| Vertical Slices | Which bounded outcomes can be implemented and reviewed independently? |

Do not describe this as four agents producing four documents. Describe it as a
chain of contracts. Each artifact narrows a different kind of uncertainty.

Ask attendees to trace one requirement through all four artifacts. They should
be able to point to:

- the user outcome;
- the relevant system contract;
- the program element that implements that contract;
- the Vertical Slice that owns the change; and
- the planned evidence that will prove it.

If the trace breaks, do not publish Tickets. The missing link is the result of
the activity.

### Break: 95–105 minutes

Keep healthy agent sessions and Control Centers running. Use the break to move
attendees with provider or GitHub problems to the Rehearsal path. Do not make
silent changes in an attendee repository.

### 105–120 minutes — Turn approved slices into shared work

Before publication, ask attendees to inspect every proposed Ticket for:

- one observable outcome;
- bounded ownership;
- dependencies;
- acceptance criteria;
- expected verification; and
- a reviewable size.

Then publish the PRD-derived Tickets and open GitHub Projects.

Say:

> The planning artifacts explain the system. The Project board explains the
> work. The Control Center explains the engine that is acting on that work.

Clarify the two views:

- GitHub Projects is the shared human work-management view.
- The Control Center is the local engine-room view for prompts, logs, tests,
  gates, receipts, and recovery.

Ask which Tickets may run in parallel and why. Introduce dependencies,
ownership overlap, remote claims, execution capacity, and review capacity as
separate limits.

Use a dependency cycle to make the point:

> If A waits for B and B waits for A, another agent does not create progress.
> A person must correct the plan.

### Transition

Say:

> We now have approved intent and bounded work. Before an implementation agent
> changes code, we need evidence that can detect the missing behavior.

---

## Act 4: Work becomes evidence

### 120–138 minutes — Independent QA proves causality

Open a Ticket at **QA Review**. Show the test, focused command, base revision,
and failure output.

Say:

> A test that passes after implementation is useful. A test that fails for the
> requested missing behavior before implementation, then passes with the same
> command afterward, is stronger evidence.

Introduce the causal sequence:

```text
Acceptance criteria → QA-owned test → RED PROVED
→ implementation → identical command → GREEN PROVED
```

Explain what does not count as RED:

- a missing dependency;
- a collection or syntax error;
- a timeout;
- a skipped test;
- an unrelated failure; or
- a test that already passes.

Ask pairs to classify three outputs: an expected behavior assertion, `No module
named pytest`, and an already-passing test. They must choose the next safe
action for each.

Make the separation of duties concrete:

> QA owns the protected acceptance evidence. Implementation owns production
> code. The factory records test hashes so implementation cannot quietly weaken
> the evidence.

### 138–157 minutes — Observe supervised execution

Start the factory. Follow one Ticket rather than scanning the entire board.

Build the lifecycle one step at a time:

```text
Ready → claim → Supervisor dispatch → worktree → implementation
→ verification → code review → merge decision → Done
```

At each step, ask who owns the state and what evidence is produced.

Explain the roles:

- The worker performs a bounded assignment.
- The Supervisor reads Handoff Receipts and proposes the next dispatch.
- The orchestrator validates the proposal and owns lifecycle transitions.
- The human handles exceptions and decisions reserved by policy.

State the Supervisor boundary plainly:

> The Supervisor coordinates work. It cannot edit code, change dependencies,
> waive gates, approve its own output, or take merge authority from the human.

Show the remote claim and isolated worktree. Explain that a worktree isolates
Git state, not the host process, network, files, or credentials. Stronger use
cases require stronger execution environments.

Open the prompt, bounded progress, changed files, gates, and Handoff Receipt.
Do not promise hidden reasoning or chain-of-thought. The factory exposes
artifacts, tool activity, decisions, and verification evidence that people can
use.

### Recovery activity: change the condition

Give each pair one blocked state:

- another run owns the claim;
- a dependency is incomplete;
- a required gate is misconfigured;
- the diff exceeds the approved budget; or
- implementation did not produce an acceptable commit.

They choose an action and explain what condition it changes. A blind retry is
not a recovery strategy.

Introduce back-pressure when the human queue fills:

> Parallel agents increase output. They do not increase review capacity. When
> the decision queue is full, a responsible factory stops dispatching more
> review work and shows `NEEDS YOU`.

For engineering leaders, connect this to operating cost: parallelism consumes
model capacity, CI capacity, and human attention. Throughput must be measured at
verified, reviewable outcomes rather than generated changes.

### Transition

Say:

> The candidate now has implementation and verification evidence. That still
> does not answer the final question: may this exact revision ship?

---

## Act 5: Evidence becomes accountability

### 157–168 minutes — Review, rework, and exact-revision merge

Use a prepared pull request with `REQUEST_CHANGES`.

Show this sequence:

1. The Code Review role inspects a named candidate revision.
2. It records an actionable comment against a changed path.
3. The implementation role receives the comment on the same branch and PR.
4. Tests, gates, and review run again against the repaired head.
5. Approval names the new exact revision and has no unresolved comments.
6. The Supervisor may recommend merge for that revision.
7. A person makes the normal merge decision.

Say:

> Automated code review can make a technical approval. It does not inherit
> shipping authority. In the Standard profile, the human remains accountable
> for merging the exact reviewed revision.

Ask attendees to verify:

- the pull request head matches the reviewed head;
- RED and GREEN evidence refer to the expected revisions;
- every required gate passed;
- review comments are resolved;
- the Supervisor recommendation names the same revision; and
- the Charter still requires human merge.

Only then should they merge.

Briefly mention the single-account limitation: GitHub does not allow a pull
request author to formally approve their own pull request. A labelled Factory
comment records the review result but does not replace protected-branch policy.

Describe Autonomous Demo as an explicit contrast, not the default:

> Autonomous Demo delegates the final action for demonstration. It changes the
> accountability model, so it requires explicit opt-in. It is not the normal
> workshop path.

### 168–175 minutes — Verify the integrated product and durable evidence

Open the completed application. Check one changed behavior and one preserved
behavior.

Say:

> Ticket-level checks prove bounded changes. They do not replace integrated
> product review.

Open the Evidence Packet and identify:

- the original requirement;
- planning artifact revisions;
- the Factory Charter hash;
- QA evidence;
- required gates;
- review and merge decisions; and
- unresolved risks.

Then open the Monitor.

Explain the boundary:

> The Evidence Packet records why this delivery was allowed. The Monitor looks
> for later drift. It may propose work, but it does not repair and merge its own
> findings.

This closes the lifecycle beyond the agent session. Durable evidence belongs
to the delivery system, not to a transient chat transcript.

### 175–180 minutes — Transfer the model to a real use case

Return to the repeated task and unsafe shortcut named at the beginning.

Ask attendees to complete the Factory Canvas with eight answers:

1. What demand enters the factory?
2. What happens if the result is wrong?
3. Which repository or workspace is involved?
4. What evidence proves success?
5. Which decisions remain human?
6. What limits parallelism and review capacity?
7. What happens when the request cannot be reproduced or verified?
8. Who owns post-delivery monitoring?

Then ask them to choose what to own, buy, or bring existing at each layer.

Do not end by recommending the complete workshop topology. End with
proportionality:

> Start with one bounded demand, one implementation agent, one independent
> success check, one pull request, and one human merge. Add planning stages,
> supervision, stronger isolation, or deeper gates only when they address a
> failure mode you can name.

Close with three questions:

- Which repeated task is slow or inconsistent enough to justify a factory?
- What evidence would make its output safe to review?
- Where must human accountability remain explicit?

Finish with:

> Do not build your factory around one model. Build it around stable contracts
> for responsibility, environment, evidence, and authority. Agents and tools
> can then change without changing what your organization means by safe
> software delivery.

---

## Messages to repeat

Use these statements throughout the workshop:

- The agent proposes. The factory controls the lifecycle.
- A retry is useful only after the failed condition changes.
- Approval belongs to an exact artifact or code revision.
- GitHub Projects shows shared work. The Control Center shows engine-room
  evidence.
- The Supervisor coordinates. The orchestrator authorizes transitions.
- More parallel agents create more review work.
- Human judgment has not disappeared. It has moved to explicit decision points.
- The smallest useful factory is better than the largest possible factory.

## Statements to avoid

Do not say:

- “The factory replaces the development team.”
- “The agents understand the whole codebase.”
- “More agents make delivery faster.”
- “A green CI run proves the feature is correct.”
- “The Supervisor is the manager of the agents.”
- “The factory is autonomous by default.”
- “All agent providers are interchangeable.”
- “The Rehearsal can implement any PRD.”

Use these alternatives:

- The factory automates bounded work and makes decisions easier to inspect.
- Agents receive selected context through explicit contracts.
- Parallelism helps only when dependencies, ownership, CI, and review capacity
  allow it.
- Verification supplies evidence for a decision; it does not remove judgment.
- Adapters are replaceable behind a role contract, but their capabilities and
  limits remain visible.
- Live planning accepts a real PRD and repository. Rehearsal is a deterministic
  teaching path.

## Keep the story intact when time runs short

Protect these narrative moments in order:

1. Ask whether the opening agent-created pull request is safe to merge.
2. Show the difference between an agent and a factory.
3. Recover one readiness failure by changing its cause.
4. Request and approve one Product Review revision.
5. Trace one requirement through the four planning artifacts.
6. Approve one valid RED proof and show the identical-command GREEN proof.
7. Follow one Ticket through Supervisor dispatch and Handoff Receipts.
8. Show one review comment returning to implementation.
9. Make one exact-revision human merge decision.
10. Return to the attendee's own use case with the Factory Canvas.

If live agents are still working, leave them running. Use the prepared Live or
Rehearsal evidence for the next teaching point. Do not terminate healthy work to
create a scripted result.
