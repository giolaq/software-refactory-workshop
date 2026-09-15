# Presenting the three-hour Software (re)-Factory workshop

Use [the presentation](software-refactory-workshop-3-hours-no-footer-timings.pptx) in Presenter
View. Slides 1–40 pace exactly 180 minutes, including a ten-minute break.
Slides 41–44 are optional reference material outside that schedule.

Speaker notes retain elapsed time from the session start. Exercise slides
show how long to work, the corresponding website section, and the evidence
attendees should be able to show. These are teaching timeboxes, not agent
timeouts. The PowerPoint does not automatically advance or cancel any work.

Speaker notes contain the explanation, discussion prompts, answer keys, source
references, and instructions for handling a slow or unfinished run. Keep the
attendee [workshop guide](https://software-refactory-workshop.vercel.app/)
open alongside the slides. Use the website for exact commands and clicks.

## Before attendees arrive

Follow [the facilitator runbook](../../factory/FACILITATOR.md). Confirm that
everyone has their own disposable GitHub repository, an authenticated coding
CLI, and the tested session release. The facilitator uses a separate repository.
Attendees should finish Setup and open Pocket Cinema before class. The opening
readiness block confirms this and handles remaining failures.

Use Standard Live with human QA approval and human merge. Prepare a separate
Rehearsal checkout and examples of a plan, acceptance tests, a failed check,
review evidence, and the completed TableStory product. Label prepared examples
and simulations. Keep the complete product transformation in scope.

Record the actual session start on a clock. The deck uses elapsed time so it
works at any scheduled start time. Announce the wall-clock return time when
the break begins.

## Running order

| Elapsed time | Slides | Activity and output |
| --- | --- | --- |
| 00:00–00:10 | 1–5 | Introduce the product transformation. Let people decide whether a review of an earlier commit justifies merge. |
| 00:10–00:20 | 6–9 | Define the factory and why current coding tools make it practical. Confirm the target, readiness and baseline. |
| 00:20–00:35 | 10–12 | Make the cooking journey observable. Review Product Review and approve clear intent. |
| 00:35–00:50 | 13–15 | Trace the journey through architecture, design and slices. Challenge an unnecessary dependency and review any revision. |
| 00:50–01:05 | 16–17 | Publish the approved tickets, find them in GitHub Projects, and begin one QA cycle. |
| 01:05–01:20 | 18–20 | Classify valid and false RED evidence. Inspect real tests, approve when justified, then run the factory. |
| 01:20–01:35 | 21–24 | Explain the repair loop. Diagnose a real or prepared failure and identify the next actor. |
| 01:35–01:45 | 25 | Break. Healthy agents can keep running. |
| 01:45–02:10 | 26–28 | Review the current candidate, request rework or merge. Continue later QA and merge decisions as they become ready. |
| 02:10–02:25 | 29–31 | Check the integrated product. Export evidence and record any unfinished work with a resume action. |
| 02:25–02:35 | 32–34 | Discuss the recorded Codex run, review capacity and incomplete cost data. Identify a measurement question. |
| 02:35–02:55 | 35–38 | Write a small team pilot, exchange a challenge, and name an owner and stop/go criterion. |
| 02:55–03:00 | 39–40 | Answer the closing decision questions and state the next action. |

## Holding the room during exercises

Leave the exercise slide visible while people work. Give a halfway reminder
and a two-minute reminder where the block is long enough. Ask people to explain
their decision to a partner before inviting answers from the room.

The observations on the slides are learning targets, not permission to bypass
a gate. An attendee who has inspected and approved valid QA evidence can start
implementation early. Handle later QA and merge decisions when they are ready;
do not hold prerequisites until the scheduled review block.

If an agent is still working, preserve the run and use the labeled prepared
case for the next discussion. An unfinished Live run stays unfinished even if
the attendee correctly reviews a prepared example. Record the ticket, current
phase, next action, and owner. Preserve the break and the twenty-minute pilot.

## Answer cues

- **Opening and post-break review cases:** evidence and approval must cover the
  current candidate. Inspect the new revision and obtain the required checks
  and review. An old approval alone is insufficient.
- **Weak requirement:** describe an action and observable result. For example,
  save a recipe, reload the page, inspect My Cookbook, remove it, and reload
  again. Keep the server running. The PRD permits saved items to reset when the
  server restarts and does not require accounts or cross-device sync.
- **Unnecessary dependency:** a generic event bus is unjustified in the prepared
  case because no approved requirement needs messaging. Evaluate real plan
  dependencies against their actual contracts.
- **RED cases:** a missing runner is an environment problem. A relevant behavior
  assertion may prove missing behavior. An unrelated assertion needs revision.
  Read the assertion even when the runner reports RED PROVED.
- **Repeated unavailable-service failure:** repair the environment or correct
  its approved configuration before repeating the operation. Identify the
  cause and owner. Another production edit may not address it.
- **Capacity example:** six arriving candidates and three reviews per hour
  produce a queue growing by three per hour under the stated assumptions.
  These are hypothetical rates, not measurements of this factory.

## Evidence and source boundaries

The deck follows [the current three-hour plan](../../factory/WORKSHOP_PLAN_3_HOURS.md),
the [narrative](../../factory/WORKSHOP_NARRATIVE.md), the
[agent reference](../../factory/AGENT_REFERENCE.md), and
[the complete TableStory PRD](../../recipe-app-prd.md).

The supplied *AI Software Factories — Knowledge and Workshop Review*, dated
8 September 2026, informs the explanations and discussion cases. Its proposals
are not treated as implemented features or completed tests. Its longer published
event agenda does not replace the explicitly requested 180-minute workshop.

Slide 32 summarizes [the historical Codex walkthrough](../research/2026-09-06-codex-live-attendee-report.md):
eight merged tickets, 298 Python tests, and 105 JavaScript tests. That report
includes debugging, source repairs and operator intervention. It does not
establish total cost, active review minutes, current-release validation, or
unassisted completion within three hours. Partial planning token counts are
not a complete bill.

Primary discussions checked for this presentation include
[Software Factory Design Patterns](https://github.com/ai-that-works/ai-that-works/tree/main/2026-08-25-software-factory-design-patterns),
[Why Software Factories Fail](https://ai.engineer/talks/Ib5GBkD555M-harness-engineering-is-not-enough-why-software),
[SWE-Marathon](https://ai.engineer/talks/Rx8f05JI_WA-swe-marathon-evaluating-coding-agents-at-billion),
and [Don’t Ship Skills Without Evals](https://ai.engineer/talks/0vphxNt4wyk-dont-ship-skills-without-evals).
Relevant speaker notes preserve the sources and qualifications.

## Optional reference slides

41 explains replaceable responsibilities and honest provider comparisons.
42 summarizes profiles and merge authority. 43 suggests later experiments,
including skill comparisons, adapter portability and recovery. 44 lists sources.
Use these for questions or follow-up rather than cutting the main exercises.

For the final activity, use [the pilot worksheet](../../factory/WORKSHOP_PILOT.md).
A reasoned choice to keep an existing coding CLI and CI workflow is a valid
outcome. Every proposed factory pilot should have an acceptance standard,
an owner, and a condition for changing course.
