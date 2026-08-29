# Software (re)-Factory: three-hour workshop plan

Release baseline: `workshop-v1.2.0`  
Duration: 180 minutes, including one 10-minute break  
Audience: software developers and technical leads  
Format: individual repository, paired review, facilitator-led checkpoints

Use this document to run the session. The attendee website supplies the exact
clicks and commands. This plan tells the facilitator what to explain, what the
attendees must do, what evidence to inspect, and when to move on.

## Workshop outcome

By the end of the session, every attendee should be able to:

- explain the difference between a coding agent and a software factory;
- locate compute, development environment, inner harness, outer harness, and
  control-plane responsibilities;
- connect and validate a personal GitHub repository;
- turn a PRD into Product Review, System Architecture, Program Design, and
  Vertical Slices;
- review the resulting issues and dependencies in GitHub Projects;
- explain why QA proves RED before implementation and GREEN afterward;
- follow one Ticket through claim, supervision, isolated implementation,
  verification, code review, rework, and human merge;
- recover from a failed preflight or blocked Ticket without blindly retrying;
- distinguish Agent Role, Agent Adapter, Supervisor, orchestrator, and human
  authority;
- inspect the completed application, Evidence Packet, and Monitor findings;
  and
- sketch the smallest useful factory for their own use case.

The workshop is successful when attendees can explain the evidence and human
decision that permit each transition. Completing the largest number of Tickets
is not the objective.

## Recommended operating mode

Use **Standard Live** as the primary path:

- Every attendee creates and owns a disposable GitHub repository.
- The facilitator uses a different repository on screen.
- The attendee selects an authenticated Claude, Codex, Cursor, or registered
  custom adapter.
- PRD planning creates the Tickets. Do not seed Tickets during the normal path.
- GitHub Projects is the shared work-management view.
- The Control Center is the local engine-room view.
- A person makes the final exact-revision merge decision.

Keep **Rehearsal** ready as the deterministic fallback. It demonstrates the
same decisions and evidence without model credentials or GitHub writes. It is a
TableStory teaching pack; do not claim that its mock adapters implement an
arbitrary PRD.

Live agents have no presentation timeout. If one attendee's agent is still
working when the group reaches the next teaching checkpoint, leave it running
and use the facilitator's prepared Live run or Rehearsal evidence. Do not kill a
healthy session merely to keep the room synchronized.

## Before the workshop

Send the prerequisite checklist at least one day before the session.

### Every attendee must have

- macOS, Linux, or Windows with WSL2;
- Python 3.11 or later with `venv` support;
- Node.js 20 or later;
- Git and a modern browser;
- GitHub CLI;
- access to the workshop repository;
- a personal, disposable GitHub repository for the exercise;
- permission to create Issues, branches, pull requests, and GitHub Projects;
- GitHub CLI authentication with the `project` scope;
- one installed and authenticated agent CLI;
- ports 5000 and 5050 available; and
- network access to GitHub and the selected agent provider.

Ask attendees to verify:

```bash
python3 --version
node --version
git --version
gh --version
gh auth status
gh auth refresh -s project
```

They should also verify the CLI they intend to select in the Control Center:

```bash
claude auth status --text
# or
codex login status
```

Do not ask attendees to use a work repository containing secrets or valuable
uncommitted changes. The Live exercise creates Issues, branches, pull requests,
Project items, comments, claims, and run evidence.

### Facilitator preparation

- Complete one clean Standard Rehearsal from PRD to merge-ready evidence.
- Complete one disposable Standard Live run through GitHub Project publication.
- Keep a Live Ticket ready at QA Review.
- Keep a Live or Rehearsal Ticket ready with a code-review
  `REQUEST_CHANGES` result.
- Keep another Ticket ready for exact-revision human merge.
- Verify the completed TableStory application starts.
- Verify Evidence Packet export and Monitor preview.
- Rehearse one failed preflight and its recovery.
- Rehearse one blocked-Ticket recovery and one local reset/recovery.
- Keep the attendee website open at prerequisites.
- Keep the Control Center, GitHub Project, one pull request, and completed app
  open in separate tabs.
- Use two terminals: one for the Control Center and one for the application or
  recovery commands.

Recommended room support is one helper for roughly every 8–10 attendees. Pair
attendees for evidence review, but do not make them share a repository or
credentials.

## Three-hour agenda

| Time | Segment | Attendee result |
| ---: | --- | --- |
| 0–10 | Welcome and working agreement | Understand the outcome, repository boundary, and peer-review pairing |
| 10–25 | What a software factory is and why now | Map the five factory boxes and locate human judgment |
| 25–50 | Connect the repository and prove readiness | Healthy Project Contract, approved Charter, selected adapter, and passing preflight |
| 50–65 | Inspect the baseline and frame the PRD | Identify preserved behavior, desired outcome, constraints, and observable success |
| 65–82 | Product Review and human revision | Reject one vague claim, request a focused revision, and approve a testable product outcome |
| 82–95 | Architecture, Program Design, and Vertical Slices | Trace one requirement across all four planning artifacts |
| 95–105 | Break | Keep agents and Control Centers running |
| 105–120 | Approve slices and inspect GitHub Projects | Review Ticket boundaries and dependencies before publication |
| 120–138 | Independent QA and causal acceptance evidence | Approve a focused test only after valid RED proof |
| 138–157 | Supervised factory execution | Follow claim, worktree, prompt, log, gates, receipts, and back-pressure |
| 157–168 | Code review, rework, and human merge | Inspect an exact revision and make an accountable merge decision |
| 168–175 | Integrated product, Evidence Packet, and Monitor | Verify the product and identify durable delivery evidence |
| 175–180 | Design your own factory and close | Record one bounded use case and its build/buy boundaries |

## Facilitation pattern

Use the same four questions in every hands-on segment:

1. **What is happening?** Name the current factory phase and owner.
2. **Why did it stop?** Name the missing evidence, failed check, or human
   decision.
3. **What should you inspect?** Point to the artifact, revision, test, log, or
   policy that supports the next action.
4. **What can happen next?** State the one safe transition and who is allowed
   to authorize it.

Avoid narrating every field in the interface. Follow one requirement and one
Ticket deeply enough that attendees can repeat the inspection themselves.

---

## 0–10 minutes — Welcome and working agreement

### Purpose

Set expectations: this is an engineering-control workshop, not a race to
generate code.

### Points to touch

- Every attendee works in a personal disposable repository.
- The facilitator's repository is for the screen demonstration only.
- GitHub Projects and the Control Center show different views of the same run.
- The workshop uses Standard Live; Rehearsal is the fallback.
- Agents may progress at different speeds.
- Human decisions are part of the design, not interruptions to automation.
- The room will inspect evidence before approving anything.

### Attendee activity — pair and predict

1. Pair with the person next to you.
2. Each person names one repeated engineering task they would consider giving
   to an agent.
3. The partner names one failure that would make that automation unsafe or
   difficult to review.
4. Write both answers in the first section of the Factory Canvas or personal
   notes.

### Facilitator prompt

Ask two pairs to share. Keep the failures visible. Return to them when
introducing planning, isolation, QA, review, and monitoring.

### Checkpoint

Every attendee has a peer reviewer and one candidate use case. Do not discuss
solutions yet.

---

## 10–25 minutes — What a software factory is and why now

### Purpose

Give attendees a model that makes the rest of the interface coherent.

### Opening explanation

Use this wording:

> AI made code generation cheap. Software delivery still depends on clear
> intent, a working environment, trustworthy verification, review capacity,
> and accountable decisions. A coding agent is one replaceable part of the
> harness. A software factory is the system around it.

### Points to touch

1. **Why now:** agents can generate changes faster than teams can specify,
   coordinate, verify, and review them.
2. **Advantage:** a factory makes context, ownership, evidence, recovery, and
   decisions repeatable and inspectable.
3. **Cost:** every extra role, gate, and parallel worker consumes compute and
   human attention.
4. **Goal:** automate routine motion and present people with smaller,
   evidence-rich decisions—not remove people completely.
5. **Review bottleneck:** output volume is not success when reviewers cannot
   absorb it.
6. **Composability:** teams should choose what to own, buy, or bring at each
   layer.

### Show the layer map

```text
Control plane
  Control Center · orchestrator · GitHub Projects

Outer harness
  roles · Charter · planning · QA · retries · review · Handoff Receipts

Inner harness
  Claude · Codex · Cursor · your adapter

Development environment
  repository · tools · dependencies · services · identity · gates

Compute
  laptop · container · hosted runner
```

Explain that the Project Contract belongs mainly to the development-environment
layer. The Factory Charter and Agent Roles belong to the outer harness. The
Control Center is not the coding agent; it is the control plane.

Open **Setup → Connection → Selected harness capabilities**. Assign the same
Implementation Agent Role first to Claude and then to Codex (or the two
adapters available in the room). Point to one real declared difference such as
native read-only execution, streamed tool progress, session resume, subagents,
browser verification, execution environment, or usage telemetry. An
unavailable feature must remain unavailable; swapping adapters never changes
the role's authority, Charter, gates, or merge boundary.

### Attendee activity — locate the responsibility

Give each pair these five cards verbally or on a slide:

- “Install `pytest`.”
- “Decide whether a PR may merge.”
- “Generate a code change.”
- “Prevent two runners from claiming the same Ticket.”
- “Show a preview URL.”

Pairs assign each card to a layer and identify whether an agent, deterministic
system, or human should own the final decision.

Expected mapping:

- dependencies and previews → development environment;
- code generation → inner harness;
- claims and lifecycle enforcement → control plane;
- merge authority → human-owned policy applied by the outer harness and
  orchestrator.

### Checkpoint

Ask one attendee to explain why “five agents” is not a complete software
factory.

---

## 25–50 minutes — Connect the repository and prove readiness

### Purpose

Make setup understandable and recoverable. Readiness is the first factory
contract, not clerical work.

### Facilitator demonstration

From the factory checkout, start the Control Center:

```bash
./factory/factory control-center
```

Show `http://127.0.0.1:5050` and point out:

- **Current phase**;
- **Next safe action**;
- **Activity and CLI output**;
- **Setup → Connection**; and
- the fact that the UI calls the same versioned CLI shown in the terminal.

### Attendee activity — connect and validate

Each attendee:

1. Opens **Setup → Connection**.
2. Selects **Live** and the **Standard** Factory Profile.
3. Selects the preset matching the CLI they installed and authenticated.
4. Pastes the full URL of their personal product repository.
5. Leaves the Pocket Cinema starter selected only for the guided exercise.
6. Saves the configuration.
7. Creates the Project Contract and Factory Charter when offered.
8. Reviews the exact Charter policy.
9. Approves the exact Charter.
10. Commits and pushes setup to the Live repository.
11. In **Development environment**, selects **Provision** to record the exact
    checkout revision and Project Contract hash.
12. Selects **Prepare**, reviews the confirmation, and runs only the declared
    setup commands.
13. Selects **Check health** to prove tools, roots, ports, and gates.
14. Selects **Run preflight**.
15. Opens **Activity and CLI output** and reads the first `[FAIL]`, if any.

Explain the distinction:

- `environment provision` records the governed revision and contract.
- `environment prepare` or **Prepare** performs reviewed setup commands.
- `environment health` or **Check health** proves the repository environment.
- `doctor --full` or **Run preflight** checks the complete factory boundary.
- Repeating preflight without changing the failed condition cannot repair it.

### Points to touch

- Project Contract: repository mechanics, source/test roots, tools, setup,
  gates, ports, and default branch.
- Factory Charter: human-owned consequence, paths, limits, approvals, and merge
  authority.
- Factory Profile: the executable role topology.
- Agent Adapter: the selected executable for a role.
- Precedence: Charter → Project Contract → Profile → Role → general policy.
- Git worktrees isolate Git state, not processes, networks, host files, or
  credentials.

### Attendee activity — failure lab

Show the prepared failed-preflight screenshot or facilitator repository. In
pairs, attendees must:

1. find the first `[FAIL]`;
2. state which layer failed;
3. choose the exact recovery action; and
4. explain why later failures should wait.

Use at least these examples:

| Failure | Layer | Recovery |
| --- | --- | --- |
| Wrong local/default branch | Development environment | Save work, fetch, switch to the default branch, and fast-forward |
| Selected Codex but only Claude is available | Inner harness configuration | Select the available preset or authenticate Codex |
| `No module named pytest` | Development environment | Prepare, check health, then preflight |
| Missing GitHub Project scope | Control plane identity | Refresh `gh` authentication with `project` scope |
| Repository URL and `origin` disagree | Development environment/target identity | Save the attendee's correct repository URL and verify `origin` |

### Checkpoint

Continue when most attendees report zero preflight failures. Move unresolved
attendees to a helper lane or Rehearsal; do not hold the entire room while one
provider login is repaired.

### If the segment runs late

Skip the second failure example, not the readiness check. Setup evidence is
required for the remaining Live activities.

---

## 50–65 minutes — Inspect the baseline and frame the PRD

### Purpose

Make attendees understand the existing product before asking agents to change
it.

### Facilitator demonstration

Start Pocket Cinema and show desktop, mobile, and TV behavior:

```bash
.factory/venv/bin/python demo-app/app.py
```

### Points to touch

- A total rebrand changes more than names and colors.
- Existing navigation, accessibility, responsive behavior, data flow, and tests
  are constraints unless the PRD deliberately changes them.
- A prototype or mockup can clarify intent, but it is not automatically
  production-ready code.
- Requirements should describe observable outcomes before implementation
  details.

### Attendee activity — baseline preservation

In pairs, inspect the running app and record:

- one behavior that must survive the Recipe App rebrand;
- one behavior that must change;
- one accessibility or responsive constraint;
- one observable success condition; and
- one question the PRD does not answer.

Then open **Plan → Requirements** and read the supplied PRD. Mark:

- user and problem;
- desired behavior;
- compatibility constraints;
- explicit non-goals; and
- measurable acceptance evidence.

### Checkpoint

Ask one attendee to explain the requested product change in one sentence
without naming a file, framework, type, or method.

---

## 65–82 minutes — Product Review and human revision

### Purpose

Demonstrate that the first human gate owns the problem and desired outcome, not
the implementation.

### Attendee activity — start and challenge Product Review

1. Open **Plan → Requirements**.
2. Select **Start Product Review**.
3. Open **Plan → Review plan**.
4. Read the Product Review artifact.
5. Find one vague, untestable, or unsupported claim.
6. Write focused revision feedback that names the missing outcome or evidence.
7. Request the revision.
8. Compare the new artifact with the previous revision.
9. Approve only when the product outcome is testable.

Use this example if the generated artifact is already strong:

> Require automated Escape and Backspace checks that preserve `mode=tv` and
> restore focus to the invoking control.

### Points to touch

- The Product Review agent proposes; it cannot approve itself.
- A useful revision request is specific but does not prescribe code.
- Approval is bound to the exact artifact hash.
- Editing an approved upstream artifact invalidates dependent approvals.
- Human judgment moved earlier, where a correction is cheaper.

### Peer review activity

Partners exchange only the revision feedback, not credentials or repository
control. Each partner answers:

- Does this feedback describe a missing user outcome?
- Could an expert revise the artifact without guessing?
- Does it avoid prescribing an implementation unnecessarily?

### Checkpoint

Every pair can identify the original weakness, the revision, and why the new
artifact is safe to approve.

---

## 82–95 minutes — Architecture, Program Design, and Vertical Slices

### Purpose

Show why planning separates product intent, system structure, program design,
and delivery boundaries.

### Attendee activity — run and trace the experts

1. Select **Run remaining experts**.
2. Review the four artifacts:
   - Product Review: users, problem, behavior, and success;
   - System Architecture: components, contracts, data, and constraints;
   - Program Design: types, signatures, layout, and call paths;
   - Vertical Slices: ordered, reviewable Tickets with acceptance criteria.
3. Choose one PRD requirement.
4. Trace it through architecture, program design, and one Vertical Slice.
5. Identify any missing or contradictory link.

### Points to touch

- Product Review answers **what and why**.
- System Architecture answers **which parts and contracts**.
- Program Design answers **how the code will be shaped**.
- Vertical Slices answer **what can be implemented and reviewed independently**.
- A prototype may be discarded after clarifying intent. Vertical Slices are
  production delivery units.
- More planning is not automatically better. Lean can omit stages for bounded,
  low-risk work; the Standard workshop uses all four so attendees can inspect
  the interfaces.

### Checkpoint

One attendee presents a complete trace in under 60 seconds. Do not publish
Tickets if a requirement disappears between artifacts.

---

## 95–105 minutes — Break

Keep the Control Center and healthy agent processes running. Helpers should use
the break to move blocked attendees to Rehearsal or repair authentication and
dependency setup. Do not silently modify an attendee's repository.

---

## 105–120 minutes — Approve slices and inspect GitHub Projects

### Purpose

Turn approved planning into work that humans can understand and agents can own
without collision.

### Attendee activity — review before publication

For every proposed Ticket, inspect:

- one observable outcome;
- acceptance criteria;
- file ownership or bounded change surface;
- dependencies;
- selected adapter;
- expected verification; and
- whether it is small enough for one review.

Then select **Approve and create tickets**. Use a new GitHub Project title or
the saved Project number.

Open the GitHub Project and identify:

- which Ticket is Ready;
- which Ticket is blocked by dependencies;
- which Tickets could run in parallel without overlapping ownership; and
- which Ticket is likely to create the most review work.

### Points to touch

- The approved Vertical Slices artifact is the Ticket source.
- Normal planning does not seed five fixture Tickets.
- GitHub Projects is the shared backlog and dependency view.
- The Control Center holds local prompts, logs, tests, diffs, gates, and
  recovery evidence.
- Parallelism is bounded by dependencies, ownership, remote claims, configured
  capacity, and human attention.

### Mini-activity — dependency challenge

Ask pairs what would happen if Ticket A depends on B while B depends on A. They
must explain why adding more agents cannot resolve a dependency cycle and which
human edit is required.

### Checkpoint

The GitHub Project contains PRD-derived Issues and every attendee can explain
why one Ticket is Ready or waiting.

---

## 120–138 minutes — Independent QA and causal acceptance evidence

### Purpose

Teach that a passing test is useful only when it detects the requested missing
behavior.

### Attendee activity — approve a test, not an intention

1. Open **Deliver → Tickets**.
2. Open **Run options**.
3. Select **Run one cycle**.
4. Open one Ticket at **QA Review**.
5. Open its **Tests** tab.
6. Inspect the test file, focused command, pre-implementation revision, and
   failure output.
7. Approve only if the failure is caused by the requested missing behavior.
8. Request changes when the test is irrelevant, too broad, or fails for setup.

### Points to touch

- QA is a separate Agent Role from implementation.
- QA writes evidence before implementation.
- `RED PROVED` requires a behavior assertion failure at the named
  pre-implementation revision.
- Collection errors, missing dependencies, timeouts, skips, and unrelated
  failures are not valid RED evidence.
- The implementation role cannot modify approved test hashes.
- After implementation, the identical command must produce `GREEN PROVED`.
- Existing required tests and repository gates still matter.

### Attendee activity — classify the evidence

Show three bounded outputs:

1. assertion failed because the Recipe behavior is absent;
2. `No module named pytest`;
3. test passed before implementation.

Pairs classify them as valid RED, environment failure, or invalid acceptance
test and state the safe next action.

### Checkpoint

At least one Ticket records approved `RED PROVED` evidence. Ask an attendee to
explain why “the test is green now” is insufficient without the earlier RED.

---

## 138–157 minutes — Supervised factory execution

### Purpose

Make agent coordination and execution observable instead of magical.

### Attendee activity — follow one Ticket deeply

1. Select **Run factory**.
2. Open **More tools → Supervisor activity**.
3. Follow one dispatch checkpoint from Handoff Receipts to the Supervisor's
   proposal and the orchestrator's validated action.
4. Return to **Deliver → Tickets**.
5. Open the selected Ticket and inspect:
   - remote claim;
   - dependency state;
   - Supervisor instruction;
   - exact Agent Role contract and prompt;
   - live tool progress and bounded log;
   - isolated worktree and branch;
   - changed files;
   - QA hashes;
   - required gate output;
   - Handoff Receipts; and
   - Ticket history.

### Points to touch

- The Supervisor coordinates; it does not edit code, change dependencies,
  waive gates, approve code, or merge.
- Workers communicate results through Handoff Receipts.
- The orchestrator validates proposals and remains lifecycle authority.
- A remote claim prevents a second runner from starting duplicate work.
- A worktree isolates Git changes, not the host or credentials.
- `NEEDS YOU` is deliberate back-pressure when the human-decision queue is
  full.
- Hidden chain-of-thought is neither requested nor exposed. The UI shows
  bounded progress, tool activity, artifacts, decisions, and verification
  evidence.
- A blocked run should name cause, owner, evidence, and recovery.

### Attendee activity — recovery decision

Give pairs one blocked state:

- another run owns the remote claim;
- a required gate is misconfigured;
- the agent exceeded the Ticket diff budget;
- a dependency is incomplete; or
- the implementation attempt failed.

They must decide whether to resume, release an abandoned claim, repair the
Project Contract, approve a documented budget exception, wait, or retry with a
reason. “Press Retry again” is not an acceptable answer without a changed
condition.

### Checkpoint

Every pair can trace:

```text
Ready → remote claim → Supervisor dispatch → worktree → QA evidence
→ implementation → gates → Handoff Receipt
```

### If Live agents are still working

Leave them running. Move the teaching view to the prepared facilitator Ticket
or deterministic Rehearsal Ticket. Return to attendee results during the final
inspection when available.

---

## 157–168 minutes — Code review, rework, and human merge

### Purpose

Separate technical review, coordination recommendation, deterministic
validation, and accountable shipping authority.

### Facilitator demonstration

Use the prepared Ticket that receives `REQUEST_CHANGES`:

1. Show the exact candidate commit reviewed.
2. Read one actionable changed-path comment.
3. Show the comment returning to implementation on the same branch and PR.
4. Show required gates and code review running again on the repaired head.
5. Show `APPROVE` only when no blocking comments remain.
6. Show the Supervisor's revision-bound `MERGE` recommendation.
7. Show the human **Merge exact revision** action.

### Attendee activity — merge decision

Each attendee or pair checks:

- Does the PR head match the approved code-review head?
- Did the identical focused acceptance command prove GREEN?
- Did every required gate pass?
- Are review comments resolved?
- Does the Supervisor recommendation name the same PR and revision?
- Is the person looking at a formal GitHub approval or a labelled Factory
  comment from the PR-author identity?
- Does the Charter retain human merge authority?

Only then may the attendee select **Merge exact revision**.

### Points to touch

- Code Review is read-only and revision-specific.
- The code-review agent can approve technically but cannot merge.
- The Supervisor can recommend merge but cannot execute it in Standard.
- The orchestrator rechecks exact revision and policy.
- The human owns the normal shipping decision.
- GitHub does not permit a PR author to formally approve their own PR. A
  labelled Factory comment is evidence but does not satisfy branch protection.
- Autonomous Demo is an explicit accountability contrast, not the normal path.

### Checkpoint

At least one Ticket reaches Done or the room can identify the exact missing
decision preventing Done.

---

## 168–175 minutes — Integrated product, Evidence Packet, and Monitor

### Purpose

Verify the integrated system and show that delivery evidence continues beyond
an individual agent session.

### Attendee activity

1. Open **Review → Run app**.
2. Start the integrated application.
3. Check one desktop/mobile behavior and one TV behavior.
4. Confirm that the behavior preserved from the baseline still works.
5. Generate or open the Evidence Packet.
6. Open **More tools → Repository monitor**.
7. Inspect one Monitor finding or the empty healthy result.

### Points to touch

- Ticket-level green checks do not replace integrated product review.
- The Evidence Packet binds requirements, policy, revisions, QA, gates,
  review, human decisions, and unresolved risks.
- Raw prompts, unrestricted logs, credentials, and hidden reasoning are not
  remote delivery evidence.
- Monitor is read-only. It may propose follow-up work but does not repair and
  merge its own finding.

### Checkpoint

An attendee can name the governed revision, the human shipping decision, and
one post-delivery owner.

---

## 175–180 minutes — Design your own factory and close

### Purpose

Transfer the model from TableStory to a real attendee use case.

### Attendee activity — complete the Factory Canvas

Attendees return to the repeated task chosen at the beginning and record:

| Question | Attendee answer |
| --- | --- |
| What demand enters the factory? |  |
| What consequence occurs if it is wrong? |  |
| Which repository or workspace is involved? |  |
| What evidence proves success? |  |
| Which decisions remain human? |  |
| What limits parallelism or review capacity? |  |
| What happens when the factory cannot reproduce or verify the request? |  |
| Who owns post-delivery monitoring? |  |

Then choose the boundary for each layer:

| Layer | Own, buy, or bring existing? | Required interface | Required evidence | Failure owner |
| --- | --- | --- | --- | --- |
| Compute |  |  |  |  |
| Development environment |  |  |  |  |
| Inner harness |  |  |  |  |
| Outer harness |  |  |  |  |
| Control plane |  |  |  |  |

Partners exchange one observation and challenge one unsupported assumption.

### Close with three questions

1. Which repeated task is slow or inconsistent enough to justify a factory?
2. What evidence would make its output safe to review?
3. Where must human accountability remain explicit?

End with:

> Do not copy this implementation blindly. Define stable responsibility,
> evidence, environment, and authority contracts so agents, tools, and
> execution providers can change independently.

## Topic checklist for the facilitator

Use this as a final audit. Every checked topic should appear in the spoken
session, an attendee activity, or inspected evidence.

### Concept and architecture

- [ ] Agent versus software factory
- [ ] Why now: generation speed moves the bottleneck
- [ ] Advantages: repeatability, ownership, evidence, recovery, observability
- [ ] Costs: compute, review load, complexity, and provider dependence
- [ ] Compute, development environment, inner harness, outer harness, control plane
- [ ] Build versus buy by layer
- [ ] Stable interfaces without pretending adapters are identical

### Setup and governance

- [ ] Personal disposable repository for every attendee
- [ ] Factory checkout versus product repository
- [ ] Control Center startup
- [ ] Live versus Rehearsal boundary
- [ ] Project Contract
- [ ] Factory Charter
- [ ] Factory Profile
- [ ] Agent Role versus Agent Adapter
- [ ] Configuration precedence
- [ ] Provision versus Prepare versus Check health versus preflight
- [ ] First-`FAIL` recovery
- [ ] Worktree limitations and production isolation

### Planning

- [ ] Baseline inspection
- [ ] PRD quality and observable outcomes
- [ ] Prototype versus production slice
- [ ] Product Review and human revision
- [ ] System Architecture
- [ ] Program Design
- [ ] Vertical Slices
- [ ] Traceability and approval invalidation
- [ ] PRD-derived Tickets, not fixture seeding

### Delivery and evidence

- [ ] GitHub Projects as shared work-management view
- [ ] Dependency-aware scheduling
- [ ] Remote claims
- [ ] Supervisor boundaries
- [ ] Orchestrator authority
- [ ] Handoff Receipts
- [ ] Independent QA
- [ ] RED before implementation and identical-command GREEN afterward
- [ ] Protected Acceptance Tests
- [ ] Diff budgets and human-attention back-pressure
- [ ] Logs, tool progress, diffs, gates, and history
- [ ] Cause-specific recovery and retry reasons

### Review and accountability

- [ ] Revision-specific automated Code Review
- [ ] `REQUEST_CHANGES` returning to the same PR
- [ ] Gates and review rerunning on the repaired head
- [ ] Supervisor merge recommendation
- [ ] Human exact-revision merge
- [ ] Single-account GitHub review limitation
- [ ] Autonomous Demo as an optional contrast only

### Completion and transfer

- [ ] Integrated product review
- [ ] Evidence Packet
- [ ] Read-only Monitor
- [ ] Factory Profiles as proportional topologies
- [ ] Custom adapter and generic-repository transfer path
- [ ] Adapter Protocol capabilities are visible, honest, and non-authoritative
- [ ] Optional intake, trigger, compounding, merge-steward, and workspace seams
- [ ] Factory Canvas for the attendee's use case

## Time recovery rules

Protect the learning objectives in this order:

1. readiness and first-`FAIL` recovery;
2. Product Review revision;
3. traceability through four planning artifacts;
4. one valid RED/GREEN proof;
5. one supervised Ticket trace;
6. one code-review rework and human merge decision;
7. Factory Canvas transfer.

If the room is more than 10 minutes late:

- inspect one Ticket instead of every Ticket;
- approve one Acceptance Test set instead of all sets;
- use the prepared review/rework Ticket;
- show GitHub issue intake and Autonomous Demo verbally, not hands-on;
- show one integrated behavior instead of every responsive mode; and
- ask attendees to complete Evidence Packet exploration after the session.

Do not save time by skipping environment readiness, accepting weak QA evidence,
or merging an unverified revision.

## Optional extensions after the core workshop

Use these only if the core session finishes early or as separate advanced labs:

- register and compare a custom Agent Adapter;
- listen for a new GitHub issue and review the non-dispatching intake proposal;
- synchronize a merge candidate with the non-authoritative steward and observe
  gates and Code Review being revoked;
- generate a reviewed cross-run improvement report;
- inspect an idempotent trigger proposal and optional workspace contract;
- compare Lean, Standard, Assured, and Autonomous Demo topologies;
- run a dependency-cycle or abandoned-claim recovery exercise;
- inspect adapter capability declarations and production limits;
- discuss container or hosted execution providers;
- design feedback → deduplication → reproduction → Ticket intake; and
- design a multi-repository coordination workspace.

## Post-workshop follow-up

Ask attendees to complete one bounded experiment within a week:

1. choose a low-consequence repeated task in a disposable repository;
2. write a small Project Contract and conservative Charter;
3. define one focused success test and one stop condition;
4. use one implementation adapter and human merge;
5. record review time, retries, false failures, and escaped defects; and
6. decide whether another role or control would solve an observed failure.

The follow-up question is not “How many agents did you run?” It is “Which
decision became smaller, safer, or easier to inspect?”
