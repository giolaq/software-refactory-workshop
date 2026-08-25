# Live Greenfield Rehearsal

This guide records the Live run used to create a new product from an empty
GitHub repository. It follows the Control Center path and does not seed the
Pocket Cinema workshop application.

Last updated: 25 August 2026

## Current status

- [x] Create an empty GitHub repository.
- [x] Connect the repository in Live mode.
- [x] Create and approve the Project Contract and Factory Charter.
- [x] Publish the initial repository setup.
- [x] Pass preflight.
- [x] Save a new FocusFlow PRD.
- [x] Run Product Review.
- [x] Answer the Product Review questions.
- [x] Approve the Product Review.
- [x] Run System Architecture.
- [x] Run Program Design.
- [x] Resolve the Vertical Slices test-file approval question.
- [x] Complete Vertical Slices.
- [x] Review alignment and create GitHub tickets.
- [x] Load published tickets into the local delivery board.
- [ ] Run ticket implementation and QA.
- [ ] Review and merge the generated pull requests.
- [ ] Run the completed FocusFlow application.

Current checkpoint: tickets `#1` and `#3` are merged. Ticket `#2` is in its
third verification attempt after two independent Code Review findings were
fixed. Tickets `#4` through `#6` remain in Backlog until their dependencies
are complete.

## Repositories

Factory checkout:

```text
/Users/laquigi/Projects/agentconf/software-refactory-workshop
```

Product repository:

```text
https://github.com/giolaq/focusflow-live-20260825
```

Managed product checkout:

```text
/Users/laquigi/Projects/agentconf/software-refactory-workshop/.factory/repositories/giolaq/focusflow-live-20260825
```

The factory checkout and product checkout remain separate. Factory source,
workshop documentation, and Pocket Cinema are not copied into the product
repository.

## 1. Prepare GitHub

Authenticate the GitHub CLI and add GitHub Projects permission:

```sh
gh auth login
gh auth refresh -s project
```

Create an empty private repository:

```sh
gh repo create focusflow-live-20260825 --private
```

An empty repository has no default branch yet. This is expected. The factory
creates `main` when it publishes the initial setup commit.

## 2. Start the Control Center

From the factory checkout, start the local Control Center:

```sh
cd /Users/laquigi/Projects/agentconf/software-refactory-workshop
./factory/factory control-center
```

Open:

```text
http://127.0.0.1:5050
```

Keep the terminal running while using the Control Center.

## 3. Connect the empty repository

In **Connect**:

1. Select **Live**.
2. Enter the full repository URL:

   ```text
   https://github.com/giolaq/focusflow-live-20260825
   ```

3. Select the **Standard** Factory Profile.
4. Select the `codex-workshop` agent preset.
5. Set parallel tickets to `1`.
6. Leave **Seed the guided Pocket Cinema starter** clear.
7. Save the configuration.

Leaving the seed option clear is important. It tells the factory that this is a
new product. The repository receives governance settings first; product code is
created later from approved tickets.

After connection, the Control Center created this managed checkout:

```text
.factory/repositories/giolaq/focusflow-live-20260825
```

## 4. Create the Project Contract and Charter

In **Connect**, select **Create contract and Charter**.

Because the repository was empty, the generated Project Contract was
conservative:

- Source root: `.`
- Test root: `tests`
- Required tool: `git`
- Verification gate: `git diff --check`
- Setup commands: none
- Application ports: none

The gate checks that a candidate change has no malformed whitespace errors. QA
still creates and runs ticket-specific tests during delivery.

The generated Factory Charter used these main rules:

- Consequence tier: `shared`
- Merge authority: `human`
- Verification level: `full`
- Product Review and Alignment require human approval
- Tests require human approval
- Agents cannot modify `factory.charter.toml`

Expand **Review exact policy**, inspect the policy, and select
**Approve exact Charter**.

The approved policy hash for this run starts with:

```text
e06f6b8905f0
```

## 5. Publish the initial setup

Select **Commit and push setup** and confirm.

The factory created commit:

```text
e3074ac chore: configure software factory
```

Only these files were committed:

```text
.gitignore
factory.project.toml
factory.charter.toml
```

No factory implementation, workshop documentation, starter application, or
product code was added.

The **Run setup** button remained disabled because the empty repository had no
setup commands. This is expected.

## 6. Run preflight

In **Connect**, select **Run preflight**.

Result:

```text
Doctor: 25 passed, 2 warnings, 0 failures
```

The two warnings did not block the run:

1. `FACTORY_REVIEW_GH_TOKEN` was not set. Self-review therefore uses a labelled
   Factory comment instead of a separate GitHub approval identity.
2. Port `5050` was already in use because the Control Center was running on it.

Important checks that passed:

- The checkout was clean and on `main`.
- Local `main` matched GitHub.
- The GitHub repository and Project API were accessible.
- The Charter was approved.
- Codex, Claude, and Cursor adapters were available.
- The repository-integrity gate passed.

## 7. Save the FocusFlow PRD

Open **PRD** and replace the sample document with:

```markdown
# FocusFlow

Build a simple personal task board for people who want to organize daily work.

## User experience

- Create a task with a required title and optional description.
- Edit and delete tasks.
- Move tasks between To do, Doing, and Done.
- Filter tasks by status.
- Show the task count for each status.
- Show clear empty, validation, and error states.
- Keep task data after a page refresh while the local server is running.

## Accessibility and layout

- Support keyboard-only use.
- Give every control a clear accessible name.
- Show visible keyboard focus.
- Work without horizontal scrolling at 375 CSS pixels.
- Provide a clear desktop layout.

## Constraints

- Run locally without external services or APIs.
- Do not add authentication or multi-user support.
- Use local assets only.
- Keep the implementation small and easy to run from a clean clone.

## Required evidence

- Automated tests cover task creation, editing, deletion, status changes, and filtering.
- The README contains exact setup, start, and test commands.
- Record successful mobile and desktop checks.
```

Select **Save PRD**, then choose **Live adapters**.

## 8. Run Product Review

Select **Start Product Review**.

The Product Review expert converted the PRD into requirements, user journeys,
scope, and success evidence. It stopped because eight product decisions were
not explicit. This was a normal human checkpoint, not an adapter failure.

## 9. Answer blocked Product Review questions

Open **Answer blocked questions** and enter one answer in each field:

1. `New tasks start in To do.`
2. `Provide an All filter in addition to To do, Doing, and Done.`
3. `Status counts always represent all stored tasks and do not change with the active filter.`
4. `Handle failed load, create, update, move, and delete requests. Show an accessible error message, preserve recoverable input and existing data, and allow retry.`
5. `Require confirmation before deletion using a keyboard-accessible confirmation dialog.`
6. `Data only needs to survive browser refreshes while the same server process is running. It may reset after the server restarts.`
7. `Use 1440 x 900 CSS pixels for the desktop check.`
8. `Record mobile and desktop results in a Verification section in README, including viewport size and result. Screenshots are not required.`

Select **Submit decisions**.

The factory preserved the first artifact, recorded the decisions, and reran
only Product Review. The revised artifact included every decision and reported
no remaining blocked questions.

## 10. Approve the product contract

Review the revised Product Review artifact. Confirm that it describes:

- The user and problem
- Required task behavior
- Accessibility and responsive behavior
- Local-only constraints
- Test and documentation evidence
- Explicit in-scope and out-of-scope behavior

Select **Approve product**.

The approval records the exact artifact hash. For this run, the approved
artifact hash starts with:

```text
a0cea16718e1
```

The plan ID is:

```text
53d001e2d1b2
```

## 11. Continue technical planning

Open **Plan** and select **Run remaining experts**.

System Architecture completed successfully. It selected:

- One dependency-free Node.js server
- A framework-free browser application
- A same-origin JSON task API
- Process-memory task storage
- Server-confirmed state changes
- Local assets and deterministic offline tests

Program Design also completed successfully. It defined the server, task store,
API, client state, browser UI, styles, tests, package scripts, and README.

Vertical Slices proposed six tickets in five dependency waves:

1. `CORE_SERVER` and `BOARD_STATE`
2. `TASK_API`
3. `BOARD_UI`
4. `RESPONSIVE`
5. `DOCS_VERIFY`

The Vertical Slices expert then stopped at a Charter-required human decision.

## 12. Approve planned test-file changes

This is the current step.

The open question is:

```text
Human approval is required before TASK_API or BOARD_STATE may modify files
under tests/, per the Factory Charter.
```

Open **Answer blocked questions** and enter:

```text
I approve TASK_API creating or updating tests/task-api.test.mjs and BOARD_STATE
creating or updating tests/board-state.test.mjs for the acceptance criteria in
this plan. No other tests/ changes are approved. QA-authored acceptance tests
remain protected from implementation edits.
```

Select **Submit decisions and continue**. The factory will rerun only Vertical
Slices. If it completes, review the final Alignment artifact before creating
GitHub issues.

The decision was accepted. Vertical Slices completed with the approval limited
to:

```text
tests/task-api.test.mjs
tests/board-state.test.mjs
```

The revised plan contains no open questions.

## 13. Review alignment and create tickets

This is the current step.

The Alignment review reports:

- 20 approved product requirements
- 6 architecture components
- 12 architecture contracts
- 12 program modules
- 37 planned functions
- 6 tickets in 5 dependency waves
- Traceability from every requirement to planned QA evidence

Review the six tickets:

1. `CORE_SERVER`
2. `BOARD_STATE`
3. `TASK_API`
4. `BOARD_UI`
5. `RESPONSIVE`
6. `DOCS_VERIFY`

In **Approve alignment**, change the **New GitHub Project title** from the
workshop default to:

```text
FocusFlow
```

Select **Approve and create tickets**.

This action records the exact Alignment approval, creates the six GitHub
Issues, and adds them to the new GitHub Project. It does not start work through
the Implementation role or merge product code.

Publication completed successfully:

```text
GitHub Project: #15 FocusFlow
CORE_SERVER: issue #1
TASK_API: issue #2
BOARD_STATE: issue #3
BOARD_UI: issue #4
RESPONSIVE: issue #5
DOCS_VERIFY: issue #6
```

Project URL:

```text
https://github.com/users/giolaq/projects/15
```

The publication operation exited with status `0`, but the browser continued to
show the busy state. The planning state and issue publication were already
complete.

The stale browser showed:

```text
Publish approved tickets
Alignment is recorded, but ticket publication has not completed.
```

Do not publish the tickets again. The authoritative local state reports
`published`, the operation reports `succeeded`, and the ticket plan records
Project `#15` plus issues `#1` through `#6`.

The Control Center was updated to poll the authoritative snapshot while a
command is active and to refresh when the browser tab becomes visible. This
prevents a dropped event-stream update from leaving the screen at the previous
state.

Hard-refresh `http://127.0.0.1:5050`. If the page cannot reconnect, restart the
Control Center from the factory checkout and reopen the page:

```sh
./factory/factory control-center
```

The published plan and tickets are loaded from the managed product checkout,
so refreshing or restarting does not repeat publication.

## 14. Load published tickets into the delivery board

After publication, the six issues were visible in GitHub Project `#15`, but the
Control Center Tickets board was empty. This was expected lifecycle state but
was not explained clearly:

- GitHub issue publication had completed.
- `.factory/state.json` did not exist yet.
- The local delivery board is created by the first factory cycle.

The Tickets page now shows the six published issues as read-only cards. Each
card links to its GitHub issue and is marked:

```text
Published
Awaiting local load
```

Before the first local load, cards use the approved dependency graph for their
status. Dependency-free issues `#1` and `#3` appear as **Ready**; dependent
issues remain **Backlog**, matching the initial GitHub Project state.

The page also shows:

```text
6 approved tickets are ready to load
```

It also provides a **Run one cycle** button. Restart the Control Center once to
load this update, open **Tickets**, and select **Run one cycle**. The factory
will load the published issues into the local board and begin the first
independent QA step.

## 15. Start the factory

Select **Run factory** in the Tickets view.

The factory loaded all six published issues into `.factory/state.json` and
started the first dependency wave. Initial state:

```text
#1 CORE_SERVER  In Progress - Independent QA attempt 1
#3 BOARD_STATE  Ready
#2, #4, #5, #6 Backlog - waiting for dependencies
```

The configured parallel-ticket limit is `1`, so ticket `#3` remains Ready while
ticket `#1` is active. The factory first asks the independent QA role to define
acceptance evidence. Implementation starts only after the QA boundary is
satisfied.

Ticket `#1` then completed this lifecycle:

```text
Independent QA -> implementation attempt 1 -> retry -> implementation attempt 2
-> verification -> code review -> human merge
```

Results:

- One protected acceptance test was created by QA.
- The required repository-integrity gate passed.
- Code Review approved candidate `bd12d1714345`.
- Human merge completed through pull request `#7`.
- Merge commit: `d74479f5b684`.
- Ticket `#1` is Done.

The running factory then dispatched ticket `#3`. Current state:

```text
#1 Done
#3 In Progress - Independent QA attempt 1
#2, #4, #5, #6 Backlog
```

No human decision is currently waiting.

## What exists on GitHub now

At the current checkpoint:

- The product repository contains only the approved factory setup files.
- GitHub Project `#15` contains the six approved issues.
- Product implementation has not started.
- No product pull request has been merged.

Product code is created only after the factory starts the approved tickets.

## Updating this guide

After each checkpoint:

1. Mark the completed item in **Current status**.
2. Change **Current checkpoint**.
3. Add the action, result, and any human decision.
4. Record errors and their resolution.
5. Do not include credentials, tokens, or private prompt contents.
