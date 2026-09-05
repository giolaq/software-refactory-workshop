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

Use four verbs throughout: **agree on the change → build it → inspect the
evidence → accept it**. Introduce a tool-specific term only at the decision it
supports. The learning outcome is control over delivery, not memorizing eight
roles or adopting this implementation.

Follow one journey during explanations: **find a recipe by ingredient → read
its cooking steps → save it to My Cookbook**. This is the teaching thread, not
a reduction in scope. All recipe data, APIs, branding, mobile/TV behavior, and
domain-cleanup requirements remain in the approved transformation.

## Before the session

Send the [invitation and prerequisites](WORKSHOP_OUTLINE.md) at least a day ahead.
Supply a tested release tag and matching guide URL. Everyone creates a personal
repository, including people using the simulated fallback. Complete tool
installation and authentication before class.

Ask attendees to complete Setup and open the Pocket Cinema baseline before
class using the session guide. Keep the in-session setup block for confirmation
and repairs. Do not silently assume installation instructions were followed.

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
| 10–20 | Explain the four verbs and agent, engine, human responsibilities while confirming setup | Verify their repository, selected CLI, contract, and Pocket Cinema baseline; repair failures | Correct target and no unresolved required readiness failure |
| 20–35 | Show how ambiguity becomes unintended behavior | Paste the full recipe PRD; write a concrete cooking journey, review Product Review, request a justified correction, approve | A testable example without shrinking the transformation |
| 35–50 | Trace the cooking journey through architecture, design, and slices | Locate its contracts and acceptance criteria; challenge an unnecessary ticket; check full-scope coverage | A complete transformation plan with genuine dependencies |
| 50–65 | Show GitHub Projects versus the local Control Center | Publish the approved plan, find their issues and Project, run one QA cycle | A ticket and its proposed acceptance tests are available, or its true waiting state is recorded |
| 65–80 | Contrast valid RED with environment failures and irrelevant assertions | Decide individually, compare reasons, inspect actual tests, approve valid evidence, then select Run factory | The first eligible implementation can start; no gate is skipped |
| 80–95 | Explain verification and rework while eligible implementation runs | Follow the cooking journey's ticket and inspect a retry or prepared failure | They distinguish blocked, working, dependency wait, and human wait |
| 95–105 | Break | Leave healthy work running | No new material |
| 105–130 | Inspect review receipts and exact-revision human merge | Decide on stale-review evidence before the answer; inspect actual diffs, request rework or merge; approve later QA when ready | Accepted transformation tickets and continued dependent work, not a room-wide barrier |
| 130–145 | Verify the complete product and durable evidence | Check the cooking journey, mobile/TV behavior, recipe APIs, and domain cleanup; export evidence | A verified TableStory transformation, or a recorded partial result with remaining tickets and resume action |
| 145–155 | Show the facilitator's recorded Live run and its limitations | Compare accepted outcomes, invocations, elapsed time, review effort, retries, and available provider usage | One justified cost or review-capacity question, not an unsupported speedup claim |
| 155–175 | Apply the decisions to their own work | Complete the pilot worksheet; exchange a peer challenge | A use case, owner, evidence strategy, cost question, and stop/go criterion |
| 175–180 | Ask three new decision questions | Answer and name one next action | Answers refer to evidence, authority, and capacity |

### Run work while teaching

The 65–80 block is a target for beginning eligible implementation, not a model
latency promise. An attendee who has completed the required approvals can start
earlier. Continue with website **Deliver tickets** immediately after valid QA
approval; do not wait for every ticket or every attendee to reach that point.
Service later QA and merge decisions as they become ready. Never approve merely
to keep pace. Use labeled prepared evidence for a discussion while healthy
agents continue; keep each attendee's actual state visible.

## Worked examples and answer key

### Opening: stale review

Give everyone 30 seconds to decide silently: merge, request changes, or wait.
Ask for the evidence behind two different answers before revealing the result.
Show approval at commit A and a PR now at commit B. Inspect and verify B and
obtain the required current review before merge. Use a prepared example rather
than editing an attendee's active branch to manufacture the mismatch.

### Product Review: make the request testable

Show this deliberately weak example: “My Cookbook should work well.” Give
attendees one minute to write an observable outcome and compare it with a
neighbor. One acceptable correction: save a recipe, reload, confirm it remains
saved, remove it, reload, and confirm it is absent. Inspect the agreed PRD's
persistence rule rather than adding accounts or synchronization by assumption.
Use the same find → read → save journey throughout the session. Request a real
plan correction when needed; do not manufacture a defect in a correct Live plan.

### Four experts: one trace

Follow the same requirement through all four outputs:

1. Product Review: a home cook finds a recipe by ingredient and reads its steps.
2. Architecture: recipe data and API contracts feed the browsing and detail views.
3. Program Design: define recipe fields, routes, matching behavior, and saved-item contracts.
4. Vertical Slices: order the recipe foundation, interface, journeys, and integration checks.

Inspect which tickets can run together and which depend on merged contracts.
Check that every required PRD outcome has a ticket and acceptance evidence.
Do not split work merely to increase the number of agents.

Before showing the answer, ask: “Must a ticket to build a generic event bus block
our recipe search?” In this prepared example, no requirement needs messaging.
Reject that dependency unless someone identifies a concrete contract or risk
that justifies it. Review actual Live tickets on their merits; do not delete
necessary foundation work to match the example.

### QA: three failures

| Observation | Decision |
| --- | --- |
| No module named pytest | Repair the environment. This is not behavior evidence. |
| The accepted recipe behavior assertion fails on the unchanged baseline | Inspect its relation to the requirement; then it can be valid RED. |
| An unrelated or impossible assertion fails | Request a revision. Failure alone does not justify implementation. |

RED PROVED is a runner classification, not a semantic guarantee. Inspect the
assertion, command, baseline revision, and later the same tests passing on the
candidate. Separate roles can still use the same model and share blind spots.
Have attendees classify all three failures individually before the answer key.
Ask them to point to the assertion, not merely say “the test is red.”

### Review capacity and cost

Use hypothetical numbers: agents produce six candidates per hour, while a
reviewer can inspect three. More workers increase waiting work, not necessarily
accepted delivery. Ask whether smaller changes or clearer evidence would help.

Inspect actual attempts, execution time, human wait, and retries. Count planning,
QA, implementation, review, and supervisor invocations separately where records
are available. Unknown token usage is not zero. Keep provider charges and human
effort separate until an attendee supplies cost assumptions.

Prepare the real-run record in [Workshop dry run](WORKSHOP_DRY_RUN.md). Show its
revision, scope, provider/model, and evidence source. A single run is an example,
not a benchmark; human wait is not active review effort. If usage is unavailable,
say so. If no Live record exists, show the unfilled record as a limitation, not
mock timings as provider performance.

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
