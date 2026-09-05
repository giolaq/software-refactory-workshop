# Validate the workshop with people and a real run

Status: **Not performed by this document.** Replace unknowns only with observed
results. Keep the full [Pocket Cinema → TableStory PRD](../recipe-app-prd.md),
including recipe APIs, branding, mobile/TV behavior, and domain cleanup.

Freeze new features until these checks identify the actual delivery problems.
Use the [three-hour agenda](WORKSHOP_PLAN_3_HOURS.md); the website remains the
attendee procedure. This is a facilitator record, not another attendee form.

## Record one real transformation

Use your separate disposable facilitator repository and an authenticated provider
you are authorized to use. A Live run can incur charges. Keep Standard's human
QA and merge gates enabled. Do not deploy to AWS for this check.

1. Record the release, starting product revision, full PRD, provider/model, and
   selected profile before starting. Avoid other provider work during the measured
   interval if its usage cannot be separated.
2. Follow the guide from planning through all approved tickets. Record start/end
   times and time spent actively reading, deciding, fixing setup, and recovering.
   Waiting time is not active review effort; overlapping agent durations are not
   elapsed wall-clock time.
3. Check the integrated recipe journey and all remaining PRD requirements. Record
   defects, incomplete tickets, and any manual intervention. Do not mark partial
   scope complete to obtain a successful record.
4. In **Review → Run app**, stop the preview, then **Export run evidence → Download**.
   Inspect ticket attempts, gate evidence, and review revisions. The exported
   packet excludes raw logs and does not promise complete billing information.
5. Count actual invocations from available local role records, including planning,
   supervision, QA, implementation, code review, and retries. Do not equate a
   ticket's implementation attempt count with total provider calls.
6. Obtain provider-reported usage or billing for the same interval when available.
   Record the source, units, and coverage. If it includes other work, say so;
   do not attribute the whole account bill to this run. Never share tokens,
   credentials, raw sensitive prompts, or unredacted logs in slides.

Copy and complete this record for the presentation:

| Field | Observed value | Evidence / limitation |
| --- | --- | --- |
| Release, baseline and final revisions; plan ID | Not recorded | |
| Full approved scope and ticket count | Not recorded | |
| Provider, model, CLI version and profile | Not recorded | |
| Start/end; elapsed wall-clock time | Not recorded | |
| Active human review and decision minutes | Not recorded | |
| Active setup and recovery minutes | Not recorded | |
| Invocations by role, including retries | Unknown | State which roles are covered |
| Input/output tokens, cache units when reported | Unknown | Provider source and coverage |
| Provider-reported charge and currency | Unknown | Subscription usage is not a per-run price |
| Accepted tickets; remaining work and defects | Not recorded | Candidate/merge revisions and checks |
| Sanitized evidence packet | Not recorded | Reviewed location or reference |

Present this as **one observed run**, not a performance benchmark. Without a
comparable measurement of today's workflow, claim neither savings nor speedup.
If the run is unfinished or no Live record is available, state that limitation.
Rehearsal is useful for decisions, not provider-performance evidence.

## Observe two or three new users

Invite people who have not operated this factory. Include an engineer and a
lead/CTO perspective where possible. Each creates their own repository; the
facilitator keeps a separate one. Use their intended OS and selected CLI, and
record the versions. One platform or provider does not validate the others.

Send the normal prerequisite message and frozen guide. Ask them to follow it
without a walkthrough. Observe setup before class and the complete timed session.
Do not coach them past every pause: ask “What do you expect to happen next?”
If they request help, record the intervention, then help. Intervene immediately
for unsafe access, secrets, or destructive actions. Do not reset healthy work or
impose a timeout on an agent.

Record each hesitation or failure in this small log:

| Participant / environment | Time and step | Expected / observed | Help or repair needed | Effect on learning or delivery |
| --- | --- | --- | --- | --- |
| Not observed | | | | |

At the decision exercises, ask them to explain:

- Which requirement or ticket would you challenge, and why?
- Does this failure prove missing behavior or a broken environment?
- Does this review cover the code you are about to merge?
- Where does an unfinished run resume, and who acts next?
- For your team, what would you measure before adding agents?

## Decide what to change before release

Record product completion separately from learning outcomes. Note when the first
eligible implementation started; minutes 65–80 are a teaching target, not a
gate to bypass. Record time lost to setup, confusing instructions, agent latency,
human review, and dependency waits separately.

Do not claim beginner readiness while a required path needs undocumented rescue.
Fix the observed blocker and rerun that path with a new user. Keep a record of
unverified environments and providers instead of claiming general certification.
Protect the break and personal pilot exercise even when Live work remains.

Before inviting a wider audience, record:

- The unclear steps corrected and the retest outcome.
- Actual complete transformations, partial runs, and resume points.
- Whether participants justified the requirement, RED, and revision decisions.
- Whether each pilot has an owner, evidence strategy, cost question, and stop/go
  criterion; choosing an existing coding CLI plus CI is a valid result.
- The release/guide used, remaining limitations, and facilitator decision to
  proceed or repeat the dry run.
