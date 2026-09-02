# Software (re)-Factory: the 3-hour run sheet

Status: produced against `main` at `004bad8` (`workshop-v1.2.0`).
180 minutes including one 10-minute break. Audience: engineers, tech leads, CTOs.
Primary mode: Standard Live on attendee repositories. Fallback: Rehearsal.
Condensed from `factory/WORKSHOP_PLAN_3_HOURS.md` and `factory/WORKSHOP_NARRATIVE.md`.

## Thesis

One question drives all 180 minutes: what must be true between receiving a PRD
and responsibly merging an exact revision?

Every segment opens with a visible failure, introduces the smallest factory
mechanism that prevents it, inspects the evidence it produces, and asks who may
authorize the next transition. Nobody watches slides about agents. Attendees
operate a factory against their own disposable repository and make every human
decision themselves. Completing tickets is not the goal; defending each
transition is.

| Persona | What they take away |
| --- | --- |
| Engineers | The mechanics: worktrees, remote claims, gates, prompts, protected test hashes. Every UI action shows its CLI command. |
| Tech leads | The operating model: review capacity as the real bottleneck, back-pressure, recovery playbooks, ticket boundaries that survive review. |
| CTOs | The control story: where accountability lives, what an audit sees (Evidence Packet), cost of parallelism, build/buy per layer. |

## Agenda at a glance

| Time | Block | Attendee walks away with |
| ---: | --- | --- |
| 0:00–0:10 | Cold open: would you merge this PR? | The gap between generated code and a shippable decision |
| 0:10–0:25 | Agent vs. factory, the five layers | A mental model that makes the rest of the UI coherent |
| 0:25–0:50 | Connect and prove readiness (hands-on) | A passing preflight on their own repo plus first-FAIL recovery skill |
| 0:50–1:05 | Baseline and PRD framing | Named preserved behavior before any agent touches code |
| 1:05–1:35 | Planning chain: challenge, revise, trace | One rejected vague claim; one requirement traced through four artifacts |
| 1:35–1:45 | Break (agents keep running) | |
| 1:45–2:00 | Publish tickets to GitHub Projects | Why parallelism is bounded by dependencies and review, not compute |
| 2:00–2:20 | Independent QA: RED before GREEN | The difference between a green test and causal evidence |
| 2:20–2:40 | Run the factory, follow one ticket | Claims, worktree, gates, receipts, plus one real recovery decision |
| 2:40–2:55 | Review, rework, human merge | An accountable exact-revision merge they performed themselves |
| 2:55–3:00 | Payoff and the smallest useful factory | The integrated app running plus a sketch of their own factory |

## The blocks

### 0:00–0:10 Cold open: would you merge this PR?

- **Hook.** No intro slides. Screen shows a real agent-authored PR: diff, green tests, no context. Ask the room to vote merge or don't-merge, then ask the holdouts what they'd need to know. Their answers are the workshop's table of contents.
- **Land.** Code generation is solved enough. The engineering problem is a trustworthy path from demand to an exact, reviewable revision. Working agreement: personal disposable repos, evidence before approval, finishing tickets is not the objective.
- **Check.** Each pair names one task they'd delegate to an agent and one failure that would make it unsafe. These come back at the close.

### 0:10–0:25 Agent vs. factory, the five layers

- **Land.** Compute, dev environment, inner harness (Claude/Codex/Cursor, replaceable), outer harness (roles, Charter, QA, gates, review), control plane (lifecycle, claims, Projects, Control Center). One live proof: assign the same Implementation Role to two adapters and show capabilities differ but authority, gates, and merge boundary do not move.
- **Do (3 min).** Pairs place five responsibilities ("install pytest", "generate a change", "prevent duplicate claims", "decide a merge", "show a preview URL") into layers and name the final owner: agent, deterministic system, or human.
- **Check.** One attendee explains why five parallel agents is not a factory. Any two of coordination, evidence, accountability: move on.

### 0:25–0:50 Connect the repository and prove readiness

- **Hook.** "A developer repairs a broken laptop setup from experience. A factory needs that knowledge explicit and testable." Setup is the first contract.
- **Do.** Everyone runs `./factory/factory control-center`, opens `127.0.0.1:5050`. Three human decisions: connect the disposable repo (Live, Standard, authenticated adapter), create the Project Contract, review and approve it. Then watch provision, prepare, health, preflight run mechanically.
- **Failure lab.** Prepared broken preflight on screen. Pairs find the first `[FAIL]`, name its layer, choose the recovery: wrong branch, unauthenticated adapter, missing pytest, missing `project` scope. Rule of the day: a retry without a changed condition repairs nothing.
- **CTO beat.** Reproducibility decides whether agent output can be trusted, repeated, and audited across machines.
- **Check.** Most of the room at zero preflight failures. Stragglers go to a helper lane or Rehearsal. Never hold the room for one provider login.
- **Cut line.** Drop the second failure example, never the readiness check.

### 0:50–1:05 Inspect the baseline, frame the PRD

- **Hook.** Run Pocket Cinema (`.factory/venv/bin/python demo-app/app.py`) on desktop, mobile, and TV. "The rebrand PRD describes the future. The running app contains behavior users depend on. Unnamed, an agent will delete it while completing the rebrand."
- **Do.** Pairs record: one behavior that must survive, one that must change, one accessibility or responsive constraint, one observable success condition, one question the PRD doesn't answer. Open the Recipe App PRD in Plan → Requirements.
- **Check.** One attendee states the requested change in one sentence with no file, framework, or method name.

### 1:05–1:35 Planning chain: challenge, revise, trace

- **Hook.** The failure first: a plausible change that solves the wrong problem. The mechanism: judgment moved earlier, where correction is cheap.
- **Product Review (1:05–1:20).** Start it, read the artifact, find one vague or untestable claim, write a focused revision request (names the missing outcome, doesn't prescribe code), request revision, diff old vs. new, approve only when testable. Partners swap feedback and score it.
- **Remaining experts (1:20–1:35).** Run Architecture, Program Design, Vertical Slices. Each attendee picks one requirement and traces it: user outcome, system contract, program element, owning slice, planned evidence. A broken trace is a successful exercise. Do not publish tickets over it.
- **Land.** Approval binds to the exact artifact hash; editing an approved upstream artifact invalidates dependent approvals. The agent proposes, it never approves itself.
- **Check.** One attendee presents a full trace in under 60 seconds.
- **Cut line.** Trace one requirement as a room instead of per pair. Never skip the revision request.

### 1:35–1:45 Break

Control Centers and healthy agents keep running. Helpers move blocked attendees to Rehearsal and repair auth. Never silently touch an attendee's repository.

### 1:45–2:00 Publish tickets, read the board

- **Do.** Before Approve and create tickets, each proposed ticket gets a 30-second inspection: one observable outcome, acceptance criteria, bounded file ownership, dependencies, adapter, small enough for one review. Publish, open GitHub Projects, answer as a room: which ticket is Ready, which is blocked, which pair could run in parallel without overlapping ownership, which will create the most review work.
- **Land.** Projects is the shared work view; the Control Center is the engine room. Parallelism is bounded by dependencies, ownership, claims, capacity, and human attention. Dependency-cycle question: if A waits on B and B on A, why does adding agents change nothing?
- **Check.** Every attendee can say why one specific ticket is Ready or waiting.

### 2:00–2:20 Independent QA: RED before GREEN

- **Hook.** The failure: tests pass and prove nothing about the requested behavior. The mechanism: a separate QA role writes the acceptance test first and must prove it fails for the right reason at the pre-implementation revision.
- **Do.** Run one cycle, open a ticket at QA Review, inspect the test file, focused command, base revision, failure output. Approve only if the failure is caused by the requested missing behavior. Then the classification drill: three outputs on screen (assertion fails on missing behavior; `No module named pytest`; test already passes). Pairs sort them into valid RED, environment failure, invalid acceptance test, and name the safe next action.
- **Land.** Implementation cannot modify approved test hashes. After implementation the identical command must prove GREEN. "The test is green now" is not evidence without the earlier RED.
- **Check.** At least one ticket in the room holds approved `RED PROVED` evidence.

### 2:20–2:40 Run the factory, follow one ticket deeply

- **Do.** Run factory, then follow one ticket: remote claim, Supervisor dispatch (Supervisor activity), isolated worktree and branch, role prompt, live tool progress, changed files, gates, Handoff Receipt, history. Every step: who owns this state, what evidence did it produce?
- **Land.** The Supervisor coordinates but cannot edit code, waive gates, or merge; the orchestrator validates and owns transitions. A worktree isolates Git state, not processes, network, or credentials. `NEEDS YOU` is deliberate back-pressure: parallel agents increase output, not review capacity.
- **Recovery drill.** Each pair gets one blocked state (foreign claim, incomplete dependency, misconfigured gate, blown diff budget, failed attempt) and must name the action and the condition it changes. "Press retry again" is an automatic fail.
- **Ops.** Live agents have no presentation timeout. If an attendee's agent is still working at the checkpoint, leave it running and teach from the facilitator's prepared ticket or Rehearsal evidence.
- **Verified Rehearsal beat.** In the `recipe-rebrand` scenario, ticket #3 fails verification on attempt 1, retries with gate output fed back, and passes on attempt 2. Deterministic, under 10 seconds.
- **Do not drive Rehearsal from the CLI on screen.** `factory run --mock --once` prints `Deadlock: #3 waits for [1, 2]` when tickets are merely parked at In Review awaiting your merge. Use the Control Center, which shows "NEEDS YOU — new dispatch is paused".

### 2:40–2:55 Code review, rework, and the human merge

- **Do.** Use the prepared `REQUEST_CHANGES` ticket: show the exact reviewed revision, one actionable comment, the comment landing back in implementation on the same branch and PR, gates and review re-running on the repaired head, `APPROVE` with no open comments, the Supervisor's revision-bound merge recommendation. Then each attendee runs the merge checklist themselves (PR head equals reviewed head; same focused command proved GREEN; all gates passed; comments resolved; recommendation names this revision; Charter keeps merge human) and clicks Merge exact revision.
- **Land.** Four separated powers: the review agent can approve technically but cannot merge; the Supervisor can recommend but cannot execute; the orchestrator rechecks revision and policy; the human owns shipping. GitHub will not let a PR author formally approve their own PR; a labelled Factory comment is evidence, not branch protection. Autonomous Demo is an explicit accountability contrast, never the default.
- **Check.** At least one ticket reaches Done, or the room can name the exact missing decision preventing it. Both are wins.

### 2:55–3:00 Payoff and the smallest useful factory

- **Do.** Run the integrated app (Review → Run app): one changed behavior, one preserved baseline behavior. Flash the Evidence Packet as "what an audit sees instead of a chat transcript." Then three minutes on the attendee's own case from the cold open.
- **Close.** "Start with one bounded demand, one implementation role, one independent success check, one PR, one human merge. Add planning stages, supervision, or deeper gates only when they address a failure mode you can name. Build around stable contracts, not around one model." Homework: one bounded experiment in a disposable repo within a week. The follow-up question is which decision got smaller, safer, or easier to inspect.

## Facilitator prep (day before)

- Attendees pre-verified: Python 3.11+, Node 20+, git, `gh` plus `gh auth refresh -s project`, one authenticated agent CLI, a disposable GitHub repo, ports 5000/5050 free. No work repos with secrets.
- One clean Rehearsal PRD-to-merge run and one disposable Live run completed; `./setup_demo.sh --scenario recipe-rebrand` then `./factory/factory doctor` pass. Rehearse on a disposable clone: every Rehearsal merge is a real commit on the current branch and the reset script does not rewind history.
- Run the factory's own tests with the venv interpreter: `cd factory && ../.factory/venv/bin/python -m unittest discover -s tests`. With system `python3` lacking pytest, 8 QA tests fail spuriously.
- Staged and ready to switch to: a broken-preflight repo, a Live ticket parked at QA Review, a ticket with `REQUEST_CHANGES`, a merge-ready ticket, the completed app, an Evidence Packet.
- Tabs open: Control Center, GitHub Project, one PR, running app. Two terminals: Control Center plus recovery.
- One helper per 8–10 attendees; pair everyone for evidence review, never for repo or credential sharing.
- Rehearsal is the same decisions and evidence with zero credentials or GitHub writes. It is a deterministic TableStory pack; don't claim its mock adapters implement arbitrary PRDs.

## If time runs short, protect in this order

1. Readiness plus first-FAIL recovery
2. One Product Review revision
3. One four-artifact trace
4. One valid RED/GREEN proof
5. One supervised ticket trace
6. One rework plus human merge
7. The attendee's own factory sketch

Recover time by narrowing scope (one ticket, one test set, one integrated behavior; use the prepared review ticket; mention issue intake and Autonomous Demo verbally). Never by skipping readiness, accepting weak RED evidence, or merging an unverified revision.
