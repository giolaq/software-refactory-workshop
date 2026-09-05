# Three-hour workshop plan

## Session contract

Use **Standard Live**, each attendee's own disposable GitHub repository, and
GitHub Projects. The facilitator uses a separate repository. Keep human QA
approval and exact-revision human merge enabled.

The main exercise is the [Pocket Cinema → TableStory product transformation](../recipe-app-prd.md).
A food company wants a recipe product built from the existing cinema app. Attendees
change the data model, APIs, visual identity, recipe journeys, saved items, and
mobile/TV behavior. A logo swap or a single completed ticket is not the result.

Live and Rehearsal use the same PRD. Live experts generate and humans review the
ticket breakdown; Rehearsal uses five deterministic tickets. Do not force Live
to match that count. Product completion means the approved transformation scope
is merged and the integrated recipe journeys pass their acceptance checks.

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
| 00–10 | Show Pocket Cinema, introduce the recipe customer, and show a prepared TableStory result. Ask whether to merge a PR reviewed at an older commit. | Vote and identify missing evidence with a neighbor | They inspect the candidate revision, not just a green badge |
| 10–20 | Define the factory with Git, tests, review, and three actors: agent, orchestrator, human | Identify who acts at each point | They distinguish a proposal from permission |
| 20–35 | Confirm repository, selected CLI, contract, and merge policy | Complete or verify website Setup in their own repository | Correct target and no unresolved required readiness failure |
| 35–50 | Show how ambiguity becomes unintended behavior | Paste the recipe PRD, review Product Review, request a correction, approve | Recipe discovery, cooking steps, and My Cookbook have testable outcomes |
| 50–65 | Explain architecture, program design, and slicing through one requirement | Trace a recipe journey through the plan; inspect contracts, ticket scope, and dependencies | The tickets cover the complete transformation in a workable order |
| 65–80 | Show GitHub Projects versus the local Control Center | Publish the approved plan, find their issues and Project, start QA | They identify the ticket waiting for QA review |
| 80–95 | Contrast an assertion failure, missing dependency, and irrelevant assertion | Inspect test code and baseline failure; approve or request changes | One justified rejection and acceptance |
| 95–105 | Break | Leave healthy work running | No new material |
| 105–125 | Show implementation, checks, and recovery | Follow the dependency-ready tickets; inspect a retry or prepared failure | They distinguish blocked, working, dependency wait, and human wait |
| 125–145 | Inspect review receipts and human merge | Review candidate diffs and current receipts; request rework or merge, then allow dependent work to continue | Accepted transformation tickets; unfinished work remains explicitly recorded |
| 145–155 | Verify behavior, durable evidence, and operating effort | Check recipe search, detail, My Cookbook, mobile/TV behavior, and domain cleanup; export evidence | A verified TableStory transformation, or a recorded partial result with the remaining tickets and resume action |
| 155–175 | Apply the decisions to their own work | Complete the pilot worksheet; exchange a peer challenge | A use case, owner, evidence strategy, cost question, and stop/go criterion |
| 175–180 | Ask three new decision questions | Answer and name one next action | Answers refer to evidence, authority, and capacity |

## Worked examples and answer key

### Opening: stale review

Show approval at commit A and a PR now at commit B. Inspect and verify B and
obtain the required current review before merge. Use a prepared example rather
than editing an attendee's active branch to manufacture the mismatch.

### Product Review: make the request testable

Start with “Turn this cinema app into a recipe app.” Ask what a recipe contains,
what users can search, how My Cookbook works, and which movie-specific interfaces
must disappear. Make one cooking journey explicit and request a specific
correction. Longer prose is not the objective.

### Four experts: one trace

Follow the same requirement through all four outputs:

1. Product Review: a home cook finds a recipe by ingredient and reads its steps.
2. Architecture: recipe data and API contracts feed the browsing and detail views.
3. Program Design: define recipe fields, routes, matching behavior, and saved-item contracts.
4. Vertical Slices: order the recipe foundation, interface, journeys, and integration checks.

Inspect which tickets can run together and which depend on merged contracts.
Check that every required PRD outcome has a ticket and acceptance evidence.
Do not split work merely to increase the number of agents.

### QA: three failures

| Observation | Decision |
| --- | --- |
| No module named pytest | Repair the environment. This is not behavior evidence. |
| The accepted recipe behavior assertion fails on the unchanged baseline | Inspect its relation to the requirement; then it can be valid RED. |
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
- Keep human gates and the transformation objective intact. Walk through prepared
  evidence rather than quietly replacing the exercise with a smaller feature.
- Separate product completion from participation: record unfinished Live work
  and demonstrate the remaining recipe journey on the labeled prepared run.
- Record the exact resume point. Do not claim a fallback completed a Live change.

Cloud deployment, custom adapters, native test-runner integration, dependency
cycle repair, and lower-cost profile design are optional follow-up labs. They
must not interrupt the first complete delivery path.
