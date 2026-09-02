# Software (re)-Factory: facilitator script, block by block

Status: produced against `main` at `004bad8` (`workshop-v1.2.0`). UI labels
verified against `factory/control_center.py` and `factory/orchestrator.py`.
Quotes attributed to AI Engineer World's Fair 2026 speakers come from published
recaps; verify wording before printing on a slide.

Legend used below:

- **SHOW** — a slide or a live screen.
- **SAY** — spoken script. Rewrite in your own words before the session.
- **DO** — attendee action, with the exact Control Center label.
- **NOTE** — facilitator only.

## The deck (20 slides, 7 reused from the AgentConf draft)

| # | Slide | Content |
| --- | --- | --- |
| S1 | Title | Reuse draft 1. Subtitle: "Three hours. One PRD. One accountable merge." |
| S2 | Would you merge this? | Full-bleed screenshot of a real agent-authored PR from the facilitator repo: diff stats, green checks, "Closes #N". Nothing else. |
| S3 | What would you need to know? | Blank slide with that one question. Room's answers go on a whiteboard and stay visible all day. |
| S4 | An agent executes. A factory governs the change. | Reuse draft 2 (The Idea). |
| S5 | Agent vs. factory | Two columns: receives an assignment / accepts governed demand · produces code / coordinates the lifecycle · own session context / versioned repo and policy context · reports an answer / records artifacts, revisions, checks · stops when the prompt ends / stops at a lifecycle state · one CLI / replaceable providers behind role contracts. |
| S6 | Five layers | Bottom-up: Compute · Development environment · Inner harness (Claude/Codex/Cursor/custom) · Outer harness (roles, Charter, planning, QA, gates, review, receipts) · Control plane (lifecycle, claims, Projects, Control Center). |
| S7 | Four kinds of "loop" | Ralph loop (fresh context, one task, same spec, repeat) · inner/outer loop (agent executes, human directs) · learning loop (people and agents improve shared knowledge) · factory loop (plan, build, verify, review, merge). Footer: "AIEWF 2026: everyone said 'loop', nobody meant the same thing." |
| S8 | The bottleneck moved | Big number: 27.6% of merged PR code is AI-generated (28× in 14 months); verification capacity flat at ~48%. Below: "A sandbox is not a software factory." — Ryan Cooke, WorkOS. |
| S9 | Every control answers a visible failure | Reuse draft 4 (The Controls). |
| S10 | Four words | Project Contract = how the repo builds/tests/starts · Factory Charter = human-owned authority, limits, protected paths · Factory Profile = which roles run · Agent Adapter = which executable performs a role. Precedence: Charter, Contract, Profile, Role, policy. |
| S11 | Failure lab | Table: failure, layer, recovery (five rows from block 3). Reveal the recovery column only after pairs answer. |
| S12 | Pocket Cinema to TableStory | Reuse draft 6 and 7 side by side. |
| S13 | The planning chain | Four experts, four questions: Product Review (what and why) · System Architecture (which parts and contracts) · Program Design (how the code is shaped) · Vertical Slices (what can be built and reviewed independently). "Each artifact narrows a different uncertainty; approval binds to the hash." |
| S14 | Completion is a claim until evidence makes it reviewable | Reuse draft 8 (The Proof). Add: `Acceptance criteria → QA test → RED PROVED → implementation → same command → GREEN PROVED`. |
| S15 | What is NOT red | Three terminal snippets, unlabelled: (1) assertion fails on missing behavior (2) `No module named pytest` (3) test passes before implementation. |
| S16 | One ticket's life | `Ready → remote claim → Supervisor dispatch → worktree → QA evidence → implementation → gates → Handoff Receipt → code review → merge decision → Done`. Owner under each step. |
| S17 | Recovery drill | Five cards: foreign claim · incomplete dependency · misconfigured gate · diff budget exceeded · failed attempt. Footer: "'Retry' without a changed condition is not an answer." |
| S18 | Separated powers | Code Review: can approve, cannot merge · Supervisor: can recommend, cannot execute · Orchestrator: rechecks revision and policy · Human: owns shipping. Plus the 7-line merge checklist. |
| S19 | Factories or orchestras? | "I want to be in front of an orchestra, waving my baton." — Charlie Holtz, Conductor. "Encode how your org plans, scopes and verifies." — Ryan Cooke. "Start with the smallest useful factory." |
| S20 | Factory Canvas | The 8 questions plus the 5-layer own/buy/bring grid (from `factory/FACTORY_CANVAS.md`). Handout too. |

---

## 0:00–0:10 Cold open: would you merge this?

Goal: the room writes the agenda themselves by listing what they'd need to know before merging agent output.

**SHOW** S2, the agent PR. No title slide first.

**SAY**
> An agent produced this pull request in about four minutes. Tests are green. It closes the issue it was asked to close. Hands up: who merges it?
>
> (Wait. Count hands out loud. Then to the people who didn't raise a hand:) What would you need to know first?

**SHOW** S3. Capture answers on the whiteboard, one line each. Steer until you have at least: what problem was it solving · which revision were the tests run against · did the agent touch the tests · did anyone review the design · does it conflict with other work · what happens if it's wrong · who is accountable for the merge.

**SAY**
> Look at that list. Not one item is "can the model write code." Code generation is not the problem anymore. The engineering problem is a trustworthy path from a request to an exact revision someone is willing to put their name on. That list is today's agenda. We're going to build the system that answers every line on it, and you're going to operate it yourselves.
>
> Ground rules. Everyone works in a personal disposable repository; I use a different one on screen. We inspect evidence before we approve anything. And finishing every ticket is not the objective; being able to defend why a ticket was allowed to move is.

**DO (pairs, 3 min)**
1. Pair with your neighbour.
2. Each of you names one repeated engineering task you'd hand to an agent tomorrow.
3. Your partner names one failure that would make that automation unsafe or impossible to review.
4. Write both on the top of the Factory Canvas handout.

**NOTE** Ask two pairs to share. Don't discuss solutions. Keep the whiteboard visible all session; you point back at it in blocks 5, 7, and 9.

---

## 0:10–0:25 Agent vs. factory, the five layers

Goal: one mental model that makes every screen they'll see today coherent.

**SHOW** S4, then S5.

**SAY**
> Most of you arrived with one of two models. Either an AI coding agent is a faster pair programmer, or a software factory is several coding agents running at once. Both are incomplete.
>
> An agent is one replaceable worker. It receives an assignment, uses its own session context, produces an answer, and stops when the prompt is done. A factory is the delivery system around the worker: it accepts governed demand, supplies versioned context, records every artifact and check, stops only at a defined lifecycle state, and can swap the provider behind a stable role contract.
>
> Why now? Agents can produce candidate changes faster than your team can specify, verify, and review them. When generation gets cheap, unclear intent and limited review capacity become the expensive things.

**SHOW** S6. Talk bottom-up.

**SAY**
> Compute runs the workload. The development environment makes the codebase reproducible. The inner harness performs one assignment: Claude, Codex, Cursor, or your own adapter. The outer harness constrains the assignment and demands evidence: roles, the Charter, planning, QA, gates, review, receipts. The control plane owns lifecycle state and authorized transitions.
>
> Claude, Codex and Cursor are not three different factories. They're inner-harness adapters. The role, the evidence, and the authority must not change because the provider changed. I'll prove that in a second.

**SHOW (live, facilitator repo)** Control Center → Setup → Connection → Selected harness capabilities. Assign the Implementation Role to Claude, then to Codex. Point at one declared difference and at what did not change: gates, Charter, merge boundary.

**SHOW** S7, 90 seconds.

**SAY**
> If you followed AI Engineer World's Fair this summer you heard the word "loop" a hundred times, and it meant four things. The ralph loop: restart a fresh-context agent against the same spec, one task at a time, until it's done. That's the minimum factory: one spec, one worker, one loop. The inner/outer loop: the agent runs execution, the human sets direction. The learning loop: people and agents improving shared knowledge. And the factory loop we're building today: plan, build, verify, review, merge. Today's system is all four stacked.

**DO (pairs, 3 min)** Place each in a layer and name who owns the final decision (agent, deterministic system, or human): install pytest · generate a code change · prevent two runners claiming the same ticket · decide whether a PR merges · show a preview URL.

**SAY (debrief)**
> Dependencies and previews: development environment. Code generation: inner harness. Claims and lifecycle: control plane. Merge authority: a human-owned policy that the outer harness and orchestrator enforce. Now, someone tell me why five agents running in parallel is not a factory.

**NOTE** You want: no coordination, no evidence, no accountability. Move on the moment you hear any two.

---

## 0:25–0:50 Connect the repository and prove readiness

Goal: every attendee has a passing preflight on their own repo and has repaired one failure by changing its cause.

**SAY**
> A developer with a half-broken laptop repairs it from experience. A factory can't. That knowledge has to be explicit and testable. Setup isn't clerical work; it's the first contract.

**SHOW (live, facilitator repo)**

```sh
./factory/factory control-center
```

Open `http://127.0.0.1:5050`. Before touching configuration, point at Current phase, Next safe action, Activity and CLI output.

**SAY**
> Three things to notice before we do anything. The Control Center always tells you the current phase and the one next safe action. And every button you press shows the exact versioned CLI command it ran, with its output streamed underneath. There is no hidden magic in this UI.

**SHOW** S10.

**SAY**
> Four words for the rest of the day. The Project Contract describes the repository: how it builds, tests, starts, resets. The Factory Charter defines authority: limits, protected paths, approvals, stop conditions, who may merge. The Factory Profile selects the operating topology: which roles run. The Agent Adapter is the executable that performs a role. Contract describes, Charter authorizes, Profile selects, Adapter performs. Precedence when they disagree: Charter, then Contract, Profile, Role, general policy.

**DO (everyone, 12 min)**
1. Run `./factory/factory control-center` in your factory checkout; open `127.0.0.1:5050`.
2. Setup → Connection: select Live, Standard, your authenticated adapter preset, paste your disposable repo URL → Save and connect.
3. Create contract. Check the detected source folders, tests, and gates.
4. Open the repository model and operating policy, read them, then Approve contract and continue.
5. Watch Activity and CLI output: publish, provision, prepare, health, gates, preflight run by themselves.

**SAY (while they work)**
> You made three human decisions: connect, create, approve. Everything scrolling past now is mechanical, and it stops at the first failure and keeps its output. The most important rule of the day: repeating an automatic step without changing the failed condition cannot repair it.
>
> One honesty point for the leaders in the room: a Git worktree isolates Git state. It does not isolate processes, network, host files, or credentials. If your use case needs that, you need a stronger execution boundary. That's the compute layer, and it's a deliberate choice.

**SHOW (live, then S11)** Switch to the prepared broken facilitator repo: preflight with several `[FAIL]` lines. Then S11 with the recovery column hidden.

**DO (pairs, 5 min, failure lab)** Find the first `[FAIL]`. Name its layer. Name the exact recovery. Explain why the later failures should wait.

| Failure | Layer | Recovery |
| --- | --- | --- |
| Local branch ≠ default branch | Dev environment | Save work, fetch, switch to default, fast-forward |
| Codex selected, only Claude available | Inner harness config | Select the available preset or authenticate Codex |
| `No module named pytest` | Dev environment | Prepare, health, preflight |
| Missing GitHub `project` scope | Control-plane identity | `gh auth refresh -s project` |
| Repo URL and `origin` disagree | Target identity | Save the correct URL, verify `origin` |

**SAY (debrief)**
> Why can't "Retry" fix any of these? Because retry repeats an unchanged condition. Recovery changes repository state, adapter configuration, authentication, or environment preparation. For the CTOs: reproducibility is not a developer-experience nicety. It decides whether agent output can be trusted, repeated, and audited across machines.

**NOTE** Move on when most of the room reports zero preflight failures. Stragglers go to a helper or to Rehearsal mode. Never hold the room for one provider login. If late: cut the second failure example, never the readiness check.

---

## 0:50–1:05 Inspect the baseline, frame the PRD

Goal: attendees name what must survive before any agent is allowed to change anything.

**SHOW (live, facilitator)**

```sh
.factory/venv/bin/python demo-app/app.py
```

Open `http://127.0.0.1:5000` on desktop width, narrow to mobile, then `/?mode=tv` and drive it with arrow keys plus Enter only.

**SAY**
> This is Pocket Cinema. It works. It has search, detail pages, a watchlist, an API, and a TV mode you can drive with a remote. The PRD we're about to feed the factory describes a future product: a recipe app. The running app contains behavior real users depend on. If we don't name that behavior, an agent will happily delete it while "completing" the rebrand, and every test will still be green.

**SHOW** S12.

**DO (pairs, 6 min)**
1. Open the running app (Review → Run app, or the same command).
2. Write down: one behavior that must survive · one that must change · one accessibility or responsive constraint · one observable success condition · one question the PRD does not answer.
3. Open Plan → Requirements and read the supplied Recipe App PRD. Mark: user and problem · desired behavior · compatibility constraints · explicit non-goals · measurable acceptance evidence.

**SAY (checkpoint)**
> Someone give me the requested change in one sentence. No file names, no framework, no method.

**NOTE** If they name a file, stop them and ask again. This is the product boundary.

---

## 1:05–1:35 Planning chain: challenge, revise, trace

Goal: every attendee rejects one vague claim, approves a revision bound to a hash, and traces one requirement through four artifacts.

**SHOW** S9. Point at row 01, ambiguous intent.

**SAY**
> The first failure on your whiteboard was "what problem was it solving." Here's the failure in practice: a plausible change that solves the wrong problem, discovered at PR review, after architecture, tickets, tests and code have all inherited the ambiguity. The fix is not a better reviewer. It's moving judgment earlier, where correction is cheap.
>
> The Product Review agent does not decide what to build. It converts the PRD into a testable proposal that a person can challenge and approve. It proposes; it cannot approve itself.

**DO (everyone, 12 min, Product Review)**
1. Plan → Requirements → Start Product Review.
2. Plan → Review plan. Read the artifact.
3. Find one vague, untestable, or unsupported claim.
4. Write revision feedback that names the missing outcome or evidence. Do not prescribe code.
5. Request the revision. Compare the new artifact with the previous one.
6. Approve only when the product outcome is testable.
7. Swap feedback with your partner. Score it: does it name a user outcome? Could an expert act on it without guessing? Does it avoid prescribing implementation?

**SAY (if an artifact is already strong)**
> Use this one: require automated Escape and Backspace checks that preserve TV mode and restore focus to the invoking control. That's a missing behavior with evidence, not a code instruction.

**SAY**
> Three rules. Feedback names the missing behavior or evidence. Feedback does not prescribe code unless the product contract needs it. And approval belongs to the exact artifact revision, not the general idea. If you later edit an approved upstream artifact, every approval downstream is invalidated. That's how the factory stops stale decisions from silently surviving.

**SHOW** S13.

**SAY**
> Now the rest of the chain. Don't think of this as four agents writing four documents. It's four contracts, each narrowing a different kind of uncertainty. Product Review: what and why. System Architecture: which parts and contracts. Program Design: how the code is shaped. Vertical Slices: what can be implemented and reviewed independently. More planning is not automatically better; the Lean profile skips stages for bounded low-risk work. We run all four today so you can see the seams.

**DO (everyone, 10 min, trace)**
1. Run remaining experts.
2. Pick one PRD requirement.
3. Trace it: user outcome, system contract, program element, the Vertical Slice that owns it, the evidence planned to prove it.
4. If the trace breaks, that's your result. Do not publish tickets over a broken trace.

**SAY (checkpoint)**
> One volunteer: your full trace, under sixty seconds.

**NOTE** If late: trace one requirement as a room. Never skip the revision request.

---

## 1:35–1:45 Break

**NOTE** Control Centers and healthy agents keep running. Helpers repair auth and move blocked attendees to Rehearsal. Nobody touches an attendee's repository without them watching.

---

## 1:45–2:00 Publish tickets, read the board

Goal: attendees explain why a specific ticket is Ready or waiting, and why parallelism is bounded.

**SAY**
> Before anything becomes a ticket, inspect it. Thirty seconds each: one observable outcome, acceptance criteria, a bounded change surface, dependencies, the adapter, and: is it small enough for one review? The last one is the one teams skip.

**DO (everyone, 8 min)**
1. Inspect every proposed ticket against that list.
2. Approve and create tickets (new GitHub Project title, or your saved Project number).
3. Open the GitHub Project. Answer: which ticket is Ready · which is blocked by a dependency · which two could run in parallel without overlapping ownership · which will create the most review work.

**SHOW (live, facilitator)** Your GitHub Project board next to Deliver → Tickets.

**SAY**
> Two views of one run. GitHub Projects is the shared, human work-management view. The Control Center is the engine room: prompts, logs, tests, diffs, gates, receipts, recovery. Neither replaces the other.
>
> Parallelism question. If ticket A waits on B and B waits on A, what does adding five more agents do? (Nothing. A person must edit the plan.) Parallelism is limited by dependencies, by ownership overlap, by remote claims, by configured capacity, and by human review attention. In that order of how hard they are to buy your way out of.

---

## 2:00–2:20 Independent QA: RED before GREEN

Goal: attendees can tell causal evidence from a green checkmark, and one ticket in the room holds approved RED PROVED evidence.

**SAY**
> Back to the whiteboard: "did the agent touch the tests?" and "which revision did the tests run against?" Here's the failure: tests pass, and prove nothing about the requested behavior, because the same agent wrote the code and the test, or the test was already green before any code changed.
>
> The factory's answer is separation of duties. A separate QA role writes the acceptance test first, against the pre-implementation revision, and must prove it fails for the right reason. Then implementation runs. Then the identical command must pass.

**SHOW** S14.

**DO (everyone, 8 min)**
1. Deliver → Tickets → Run options → Run one cycle.
2. Open a ticket at QA Review → Tests tab.
3. Inspect: the test file, the focused command, the pre-implementation revision, the failure output.
4. Approve only if the failure is caused by the requested missing behavior. Request changes if the test is irrelevant, too broad, or fails for setup reasons.

**SHOW** S15.

**DO (pairs, 4 min)** Classify each output (valid RED · environment failure · invalid acceptance test) and name the safe next action.

**SAY (debrief)**
> One: assertion fails because the recipe behavior is absent. Valid RED, approve. Two: `No module named pytest`. Environment failure; repair, re-prove, do not approve. Three: passes before implementation. Invalid test; it cannot detect the missing behavior; request changes.
>
> What doesn't count as RED: a missing dependency, a collection or syntax error, a timeout, a skipped test, an unrelated failure, or a test that already passes. Once approved, the factory records the test hashes; implementation cannot quietly weaken the evidence. "The test is green now" means nothing without the earlier RED at a named revision.

---

## 2:20–2:40 Run the factory, follow one ticket

Goal: attendees trace one ticket end to end with an owner at every step, and make one recovery decision that isn't "retry."

**SHOW** S16.

**SAY**
> Now we run it. The temptation is to watch the whole board light up. Don't. Follow one ticket, deeply. At every step ask: who owns this state, and what evidence did it produce?

**DO (everyone, 10 min)**
1. Run factory.
2. More tools → Supervisor activity: follow one dispatch checkpoint from the Handoff Receipts to the Supervisor's proposal to the orchestrator's validated action.
3. Back to Deliver → Tickets, open your ticket and find: the remote claim · dependency state · the Supervisor instruction · the exact role contract and prompt · live tool progress and the bounded log · the worktree and branch · changed files · QA hashes · required-gate output · the Handoff Receipt · ticket history.

**SAY (while it runs)**
> The roles. The worker performs a bounded assignment. The Supervisor reads Handoff Receipts and proposes the next dispatch; it cannot edit code, change dependencies, waive gates, approve its own output, or take merge authority. The orchestrator validates the proposal and owns every lifecycle transition. The human handles exceptions and the decisions the Charter reserves.
>
> The remote claim is what stops a second runner from starting duplicate work. And no, you're not seeing hidden reasoning; the factory exposes artifacts, tool activity, decisions, and verification evidence.
>
> One more mechanism you'll see if the queue fills: `NEEDS YOU`. When the human-decision queue is full, a responsible factory stops dispatching more review work. Parallel agents increase output. They do not increase review capacity. For the leaders: throughput is measured at verified, reviewable outcomes, not at generated changes.

**SHOW** S17.

**DO (pairs, 5 min)** Each pair takes one blocked state: another run owns the claim · a dependency is incomplete · a required gate is misconfigured · the diff exceeded the approved budget · the implementation attempt failed. Decide: resume, release an abandoned claim, repair the Project Contract, approve a documented budget exception, wait, or retry with a reason. Name the condition your action changes.

**NOTE** Live agents have no presentation timeout. If attendee runs are still going at the checkpoint, leave them and teach from your prepared facilitator ticket or a Rehearsal ticket.

**NOTE (verified Rehearsal beat)** In the `recipe-rebrand` scenario, ticket #3 ("Build the mobile TableStory experience") fails verification on attempt 1, retries with the gate output fed back, and passes on attempt 2. Deterministic, under 10 seconds. Tickets #1/#2 dispatch in parallel; #3, #4, #5 unlock one merge at a time.

**NOTE (do not drive Rehearsal from the CLI on screen)** `factory run --mock --once` prints `Deadlock: #3 waits for [1, 2]` when tickets are simply parked at In Review awaiting your merge. Use the Control Center, which shows "NEEDS YOU — new dispatch is paused".

---

## 2:40–2:55 Code review, rework, and the human merge

Goal: each attendee performs an accountable exact-revision merge after running the checklist.

**SAY**
> Last lines on the whiteboard: "did anyone review it" and "who is accountable." Here's the failure: review comments lost between agent runs, and a green approval that nobody owns.

**SHOW (live, facilitator's prepared REQUEST_CHANGES ticket)**
1. The exact candidate revision the review ran against.
2. One actionable comment on a changed path.
3. The comment landing back in implementation on the same branch and PR.
4. Gates and review running again on the repaired head.
5. `APPROVE` only with no blocking comments.
6. The Supervisor's revision-bound `MERGE` recommendation.
7. The human Merge exact revision action. Don't click it yet.

**SHOW** S18.

**SAY**
> Four separated powers. The code-review role is read-only and revision-specific; it can approve technically but cannot merge. The Supervisor can recommend but cannot execute. The orchestrator rechecks the exact revision and policy. The human owns the shipping decision. That's the Standard profile. Autonomous Demo exists as an explicit accountability contrast; it requires opt-in and is never the default.
>
> One honest limitation: GitHub will not let a PR author formally approve their own PR. A labelled Factory comment is evidence; it does not satisfy branch protection. Plan for that in your own setup.

**DO (everyone, 6 min)** Run the checklist on your merge-ready ticket, out loud with your partner: PR head equals the reviewed head · the identical focused command proved GREEN · every required gate passed · review comments resolved · the Supervisor recommendation names this PR and revision · you know whether you're looking at a real approval or a labelled Factory comment · the Charter still keeps merge human. Only then: Merge exact revision.

**SAY (checkpoint)**
> Who has a ticket at Done? Who doesn't, and can name the exact missing decision preventing it? Both are the right answer.

---

## 2:55–3:00 Payoff and the smallest useful factory

Goal: they see the integrated result, see what an audit sees, and leave with their own factory sketched.

**SHOW (live)** Review → Run app. One changed behavior (recipe browsing), one preserved baseline behavior (TV arrow-key navigation). Open the Evidence Packet; scroll once through requirements, artifact revisions, Charter hash, QA proof, gates, decisions, unresolved risks. Then More tools → Repository monitor.

**SAY**
> Ticket-level checks prove bounded changes. They don't replace looking at the product. And this packet is what an audit sees instead of a chat transcript: why this delivery was allowed, bound to exact revisions. The Monitor looks for drift afterwards; it may propose work; it never repairs and merges its own findings.

**SHOW** S19.

**SAY**
> The industry hasn't settled the name. Some of you want a factory; some of you want to stand in front of an orchestra with a baton. What you ran today is both: a human at every decision, with factory-grade evidence underneath. The disagreement is about who conducts, not about whether evidence matters.
>
> Don't copy this topology. Start with one bounded demand, one implementation role, one independent success check, one pull request, one human merge. Add planning stages, supervision, stronger isolation, or deeper gates only when they address a failure mode you can name.

**SHOW** S20.

**DO (3 min, individually)** Go back to the task and the failure you wrote at 0:05. Fill in: what demand enters · what happens if it's wrong · what evidence proves success · which decisions stay human · what limits review capacity · who owns monitoring. Then one row of the own/buy/bring grid.

**SAY (close)**
> Three questions to take home. Which repeated task is slow or inconsistent enough to justify a factory? What evidence would make its output safe to review? Where must human accountability stay explicit?
>
> Homework, one week: one low-consequence task in a disposable repo, a small Project Contract, a conservative Charter, one focused success test, one adapter, one human merge. Record review time, retries, false failures, escaped defects. The follow-up question is not "how many agents did you run." It's "which decision became smaller, safer, or easier to inspect."
>
> Build around stable contracts: responsibility, environment, evidence, authority. Not around one model. Thank you.

---

## Where the sample factory is used

| Block | Who drives | Mode | Control Center / command |
| --- | --- | --- | --- |
| 0:00 | Facilitator | Live (prepared) | Screenshot of a factory-authored PR from the facilitator repo |
| 0:10 | Facilitator | Live | Setup → Connection → Selected harness capabilities (swap Claude/Codex) |
| 0:25 | Everyone | Live, Standard | `./factory/factory control-center` · Save and connect · Create contract · Approve contract and continue; facilitator shows broken preflight |
| 0:50 | Facilitator and all | — | `.factory/venv/bin/python demo-app/app.py` · `/?mode=tv` · Plan → Requirements |
| 1:05 | Everyone | Live | Start Product Review · Plan → Review plan · Run remaining experts |
| 1:45 | Everyone | Live | Approve and create tickets · GitHub Project · Deliver → Tickets |
| 2:00 | Everyone | Live | Run options → Run one cycle · QA Review → Tests tab |
| 2:20 | Everyone | Live | Run factory · More tools → Supervisor activity · ticket detail |
| 2:40 | Facilitator, then all | Live (prepared) | REQUEST_CHANGES ticket · Merge exact revision |
| 2:55 | Facilitator | Live | Review → Run app · Evidence Packet · More tools → Repository monitor |
| Fallback | Anyone blocked | Rehearsal | `./setup_demo.sh --scenario recipe-rebrand` then Control Center → Rehearsal; CLI: `./factory/factory run --mock --scenario recipe-rebrand --once` |

## Facilitator checklist (day before)

- Attendees pre-verified: `python3 --version` (3.11+), `node --version` (20+), `git`, `gh auth status`, `gh auth refresh -s project`, one of `claude auth status --text` / `codex login status`; a disposable repo; ports 5000 and 5050 free.
- Factory checkout: `./setup_demo.sh --scenario recipe-rebrand` → `./factory/factory doctor` passes. Rehearse on a disposable clone or branch: every Rehearsal merge is a real commit on the current branch (about 16 per full run) and the reset script restores files but does not rewind history.
- Run the factory's own tests with the venv interpreter: `cd factory && ../.factory/venv/bin/python -m unittest discover -s tests` (414 tests, about 40 s). With system `python3` lacking pytest, 8 QA tests fail spuriously.
- One clean Rehearsal PRD-to-merge run and one disposable Live run through Project publication done.
- Staged: broken-preflight repo (S11 rows) · Live ticket parked at QA Review · ticket with `REQUEST_CHANGES` · merge-ready ticket · finished app · Evidence Packet export.
- Screenshot S2 from a real PR in the facilitator repo.
- Tabs: Control Center · GitHub Project · one PR · running app. Two terminals: Control Center · recovery.
- Handouts: Factory Canvas (`factory/FACTORY_CANVAS.md`). One helper per 8–10 attendees.
