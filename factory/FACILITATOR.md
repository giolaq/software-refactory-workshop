# Facilitator runbook

Runtime reference: workshop-v1.2.4. Freeze a tested session release and matching
guide before sending the invitation.

Use the [three-hour plan](WORKSHOP_PLAN_3_HOURS.md) for timing and the
[narrative](WORKSHOP_NARRATIVE.md) for slide notes. The attendee website explains
how to operate the factory, not the presentation's rationale.

## Prepare

1. Send the [prerequisites](WORKSHOP_OUTLINE.md) at least one day ahead.
2. Verify that everyone creates their own disposable GitHub repository.
3. Use a separate facilitator repository and a signed-in provider you have tested.
4. Rehearse the full [Pocket Cinema → TableStory transformation](../recipe-app-prd.md)
   with the Live provider. Review the complete ticket breakdown and dependencies.
5. Keep a separate five-ticket TableStory Rehearsal checkout and prepared
   evidence for slow or unavailable providers.
6. Test the guide, Control Center, and screenshots against the same code.
7. Check the projector layout and the actual room's network/authentication flow.
8. Record one real transformation's outcome and operating cost, then observe two
   or three new users with the [dry-run procedure](WORKSHOP_DRY_RUN.md). These
   records are required evidence to collect, not results supplied by the code.

Freeze feature work until that observation. Prioritize unclear instructions,
broken steps, and recovery over new roles, dashboards, or integrations. Keep the
same tested release for preparation and the session.

Run local validation with the Factory virtual environment:

```sh
.factory/venv/bin/python -m unittest discover -s factory/tests
npm --prefix workshop-guide test
npm --prefix workshop-guide run lint
npm --prefix workshop-guide run build:vercel
./factory/factory release-check --rehearsal
```

The release audit expects a clean, frozen tree. It is not a substitute for a
live-provider smoke or a novice dry run. Record both in
[Workshop validation](WORKSHOP_VALIDATION.md).

## Explain only the next decision

Use **agree on the change → build it → inspect the evidence → accept it** in
slides. Follow one cooking journey: ingredient search → cooking steps → My
Cookbook. Keep the complete transformation in the tickets; do not turn the
teaching thread into a smaller exercise.

- Setup: confirm the target and review the shell commands and authority in the
  contract. Worktrees isolate Git state, not the whole host.
- Plan: make a recipe journey testable; trace it through the four expert outputs
  and confirm that the tickets cover the whole product transformation.
- QA: read the assertion, exact command, and baseline failure before approving.
- Deliver: distinguish working, waiting for dependencies, waiting for a person,
  and blocked by a failed check.
- Review: inspect the current revision. A separate role using the same model is
  not a guarantee of independent reasoning. A Factory comment may not be a
  formal GitHub branch-protection approval.
- Finish: check the integrated recipe journeys and removal of movie-domain
  behavior. Distinguish a complete transformation from partially merged work.
  Export run evidence and complete the pilot
  worksheet. An optional detailed Canvas is not an export prerequisite.

## Keep execution moving

Ask attendees to finish Setup and open Pocket Cinema before class. Confirm that
state at the start; do not restart successful setup for the demonstration.
After valid QA approval, continue immediately to **Deliver tickets → Run factory**.
Target the first eligible implementation in minutes 65–80; this is not a timeout
or a completion guarantee. Attendees may progress at different rates.

Use the [prepared decision cases](WORKSHOP_PLAN_3_HOURS.md#worked-examples-and-answer-key)
while healthy work runs. Each person decides first, compares reasons with a
neighbor, then sees the answer. Include a weak requirement, an unnecessary
dependency, false RED, and stale review. Never manufacture defects in a healthy
Live run or ask attendees to approve evidence they have not inspected.

Keep handling later QA and merge decisions while other tickets execute. Do not
wait until the closing review block to unlock a dependency that is ready now.

## Recovery without shortcuts

| Observation | What to do |
| --- | --- |
| Wrong repository | Stop before running setup commands. Save the correct personal repository URL in Connection. |
| Wrong branch | Preserve local changes. Fetch, switch to the product's detected default branch, then pull with --ff-only. Do not assume every repository uses main. |
| Wrong agent or sign-in missing | Select the matching preset; verify that CLI's authentication; retry setup. |
| Missing pytest | Use the interpreter printed in the failing gate and the guided starter's requirements file. Retry only after the dependency check passes. |
| Port 5050 warning while the Control Center is open | Confirm it is this server. Do not kill an unrelated process. |
| Agent still working | Leave it running and use prepared evidence for the next teaching decision. No presentation timeout. |
| QA review takes time | Review the core test or a prepared example. Keep the QA gate enabled. |
| Missing dependency versus assertion failure | Repair the environment; do not accept infrastructure failure as RED evidence. |
| Ticket waits for another ticket | Inspect the dependency and finish its required decision. Re-running the waiting ticket does not remove the dependency. |
| Agent review covers an older commit | Re-verify and review the candidate revision. Do not reuse stale approval. |
| Run is unfinished at the delivery checkpoint | Record the ticket and next action. Continue the learning activity with labeled prepared evidence. |
| Someone needs to start again | Explain the reset scope in the dialog. Use a separate checkout for Rehearsal; preserve the Live repository and GitHub evidence. |

The [Control Center reference](CONTROL_CENTER.md) explains supported actions and
recovery. Do not introduce a second set of setup commands in slides.

## Closing

Protect the final 20-minute [pilot worksheet](WORKSHOP_PILOT.md). Ask partners to
challenge one unsupported assumption. Count actual Live completions separately
from successful decision exercises on prepared evidence.

A useful final answer may be that the team's current coding-agent and CI workflow
is sufficient. The workshop should teach when this coordination earns its cost,
not require everyone to adopt this implementation.
