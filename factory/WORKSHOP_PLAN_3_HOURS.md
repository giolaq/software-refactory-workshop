# Three-hour workshop plan

## Session contract

Use **Standard Live**, each attendee's own disposable GitHub repository, and
GitHub Projects. The facilitator uses a separate repository. Keep human QA
approval and exact-revision human merge enabled.

The core Live exercise is [genre-aware film search](../workshop-search-prd.md):
one visible improvement to Pocket Cinema, including tests and review. The full
[TableStory rebrand](../recipe-app-prd.md) is an extension, not the three-hour
completion promise. Rehearsal uses that five-ticket teaching pack; its mock
adapters do not implement an arbitrary PRD.

The website explains **how**: commands, clicks, expected results, and recovery.
Explain **why** with slides, worked examples, and discussion. The website does
not repeat the presentation or track attendance and completion.

## Before the session

Send the [invitation and prerequisites](WORKSHOP_OUTLINE.md) at least a day ahead.
Supply a tested release tag and matching guide URL. Everyone creates a personal
repository, including people using the simulated fallback. Complete tool
installation and authentication before class.

Prepare examples of Product Review, valid and invalid RED evidence, a failed
gate, stale review, accepted revision, and the final application. Label prepared
and simulated evidence. Verify the live provider used on screen. See the
[verification record](WORKSHOP_VALIDATION.md) for what is and is not tested.

## Timed agenda

These blocks total 180 minutes, including a ten-minute break. Agent latency is
variable. Leave healthy agents running; use prepared evidence when the group
reaches the next decision. Do not impose a presentation timeout.

| Time | Explain or demonstrate | Attendee activity | Observable result |
| --- | --- | --- | --- |
| 00–10 | Show an app and a PR approved at an older commit. Ask whether to merge. | Vote and identify missing evidence with a neighbor | They inspect the candidate revision, not just a green badge |
| 10–20 | Define the factory with Git, tests, review, and three actors: agent, orchestrator, human | Identify who acts at each point | They distinguish a proposal from permission |
| 20–35 | Confirm repository, selected CLI, contract, and merge policy | Complete or verify website Setup in their own repository | Correct target and no unresolved required readiness failure |
| 35–50 | Show how ambiguity becomes unintended behavior | Paste the search PRD, review Product Review, request a correction, approve | Search behavior and one success example are testable |
| 50–65 | Explain architecture, program design, and slicing through one requirement | Trace genre search through the plan; reject unnecessary enabling tickets | One end-to-end slice, with genuine blockers explained |
| 65–80 | Show GitHub Projects versus the local Control Center | Publish the approved plan, find their issue and Project, start QA | They identify the ticket waiting for QA review |
| 80–95 | Contrast an assertion failure, missing dependency, and irrelevant assertion | Inspect test code and baseline failure; approve or request changes | One justified rejection and acceptance |
| 95–105 | Break | Leave healthy work running | No new material |
| 105–125 | Show implementation, checks, and recovery | Follow the ticket; inspect a retry or prepared failure | They distinguish blocked, working, dependency wait, and human wait |
| 125–145 | Inspect review receipts and human merge | Review the diff and current receipt; request rework or merge | An accepted core slice, or an honest unfinished Live state with the decision exercised on prepared evidence |
| 145–155 | Verify behavior, durable evidence, and operating effort | Run the app, stop it, export and download run evidence | They name what was verified and what remains unknown |
| 155–175 | Apply the decisions to their own work | Complete the pilot worksheet; exchange a peer challenge | A use case, owner, evidence strategy, cost question, and stop/go criterion |
| 175–180 | Ask three new decision questions | Answer and name one next action | Answers refer to evidence, authority, and capacity |

## Worked examples and answer key

### Opening: stale review

Show approval at commit A and a PR now at commit B. Inspect and verify B and
obtain the required current review before merge. Use a prepared example rather
than editing an attendee's active branch to manufacture the mismatch.

### Product Review: make the request testable

Start with “Find films quickly.” Ask for the searched fields, case and whitespace
behavior, the empty state, and one real genre from the catalog. Request a
specific correction. Longer prose is not the objective.

### Four experts: one trace

Follow the same requirement through all four outputs:

1. Product Review: the viewer can search by genre.
2. Architecture: catalog genre data reaches browser filtering.
3. Program Design: specify the data and matching contract without a new framework.
4. Vertical Slices: deliver template data, browser behavior, and tests together.

A genuine dependency may justify another ticket. Review that reason rather than
forcing an unsafe change to satisfy a ticket count.

### QA: three failures

| Observation | Decision |
| --- | --- |
| No module named pytest | Repair the environment. This is not behavior evidence. |
| The accepted genre assertion fails on the unchanged baseline | Inspect its relation to the requirement; then it can be valid RED. |
| An unrelated or impossible assertion fails | Request a revision. Failure alone does not justify implementation. |

RED PROVED is a runner classification, not a semantic guarantee. Inspect the
assertion, command, baseline revision, and later the same tests passing on the
candidate. Separate roles can still use the same model and share blind spots.

### Review capacity and cost

Use hypothetical numbers: agents produce six candidates per hour, while a
reviewer can inspect three. More workers increase waiting work, not necessarily
accepted delivery. Ask whether smaller changes or clearer evidence would help.

Inspect actual attempts, execution time, human wait, and retries. Count planning,
QA, implementation, review, and supervisor invocations separately where records
are available. Unknown token usage is not zero. Keep provider charges and human
effort separate until an attendee supplies cost assumptions.

Use the [pilot worksheet](WORKSHOP_PILOT.md) for the final activity. A justified
decision not to use a factory is a successful learning outcome.

## Closing questions

1. Tests are green, but the branch changed after review. What must happen?
2. A missing dependency causes RED. Is that sufficient implementation evidence?
3. Review is slower than implementation. What would you measure before adding agents?

## If the room falls behind

- Preserve the break and the 20-minute personal pilot exercise.
- Keep each person's repository and actual run status intact.
- Leave healthy agents running; use prepared evidence for the next decision.
- Use a separate Rehearsal checkout, not a reset of the Live run.
- Keep human gates enabled. Reduce scope instead of bypassing QA.
- Record the exact resume point. Do not claim a fallback completed a Live change.

Cloud deployment, custom adapters, native test-runner integration, dependency
cycle repair, and lower-cost profile design are optional follow-up labs. They
must not interrupt the first complete delivery path.
