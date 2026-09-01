# Facilitator runbook

Release: `workshop-v1.2.0`

Use [WORKSHOP_NARRATIVE.md](WORKSHOP_NARRATIVE.md) for the spoken story,
[WORKSHOP_OUTLINE.md](WORKSHOP_OUTLINE.md) for the presentation path, and
[COMPATIBILITY.md](COMPATIBILITY.md) for upgrades and migration behavior. This
runbook is the detailed preparation, release, and recovery reference; do not
read it as the attendee script.

Use this runbook to prepare and deliver the three-hour Software (re)-Factory
workshop. The attendee website contains the full instructions. Your job is to
keep time, make the control points visible, and stop the group when evidence is
weak.

For the first dry run, use a Self-paced Rehearsal Run. It exercises the complete workflow
without GitHub writes or model latency. Demonstrate a Live Run only after the
rehearsal path works from a clean checkout.

## Readiness checklist

Complete this checklist before attendees arrive:

- [ ] macOS, Linux, or WSL 2 is available.
- [ ] Python 3.11 or later includes the `venv` module.
- [ ] Node.js 20 or later and Git are on `PATH`.
- [ ] Ports 5000 and 5050 are free.
- [ ] The presentation browser can open localhost pages.
- [ ] The workshop repository is clean and synchronized with its default branch.
- [ ] A disposable local Git checkout exists for a Rehearsal Run.
- [ ] The deterministic recipe scenario completes successfully.
- [ ] A colleague has recovered one failed preflight by using the website without verbal help.
- [ ] The attendee website is open at the prerequisites section.
- [ ] The frozen source, CLI, website, and Git tag all identify
      `workshop-v1.2.0`.
- [ ] Every attendee will create and own a separate repository. Rehearsal may
      stay local; Live uses GitHub. The facilitator uses a different repository.
- [ ] Peer-review pairs are assigned without sharing repository state.

A Live Run also requires:

- [ ] `gh auth status` succeeds.
- [ ] GitHub authentication includes the `project` scope.
- [ ] The repository owner can create issues, Projects, branches, and pull requests.
- [ ] The repository URL is saved in **Setup → Connection** and the repository card says **connected**.
- [ ] A current Bedrock, Claude, Codex, or Pi planning CLI is authenticated.
- [ ] The selected supervision, implementation, QA, and code-review adapters are registered and their
      noninteractive commands have been smoke-tested. Claude is only the worked
      example; attendees may use their own agent.
- [ ] The selected supervisor adapter is registered and can return the required
      structured dispatch decision noninteractively.
- [ ] If the demo requires formal GitHub approval, `FACTORY_REVIEW_GH_TOKEN`
      belongs to a second account with repository review access.
- [ ] Network access to GitHub and the selected agent provider is stable.

## Prepare the dry run

Create a disposable rehearsal checkout:

```sh
./factory/new_workshop.sh ../software-refactory-rehearsal recipe-rebrand
cd ../software-refactory-rehearsal
```

Run the deterministic preflight and scenario once:

```sh
python3 --version
node --version
git --version
./factory/factory init
# Review factory.project.toml and factory.charter.toml.
./factory/factory approve-contract --yes
```

Prepare the live checkout only if you plan to demonstrate real agents:

```sh
./factory/new_workshop.sh ../software-refactory-live live
cd ../software-refactory-live
./setup_demo.sh --scenario recipe-rebrand
git push origin main
./factory/factory configure \
  --github-repository "$(gh repo view --json url --jq .url)" \
  --preset claude-workshop
./factory/factory approve-contract --live --yes
```

Continue only when the doctor reports zero failures. A warning is acceptable
only for an optional adapter that won't be used or for the documented
single-account review-comment fallback.

If a colleague asks whether the factory only works for Pocket Cinema, show the
Project Contract card in **Setup → Connection**. The extension path is:

```sh
./factory/factory init --repo /path/to/existing-project
# Review factory.project.toml in that project.
./factory/factory control-center --repo /path/to/existing-project
```

Explain the boundary plainly: a Live Run accepts any PRD and repository;
Rehearsal is a deterministic TableStory teaching pack. Do not switch the core
exercise to an unfamiliar repository during the three-hour session.

If the group uses another implementation or QA adapter, register it under
`[agents]` in `factory/factory.toml`, then save the attendee defaults with
`factory configure`. Keep Bedrock, Claude, Codex, or Pi as the structured planning adapter.
The exact contract and wrapper requirements are in `factory/CONFIGURATION.md`.
Run `./factory/factory adapter-check` and show its declared capabilities in
**Setup → Connection** before using a custom adapter live.

## Arrange the presentation workspace

Use two terminals:

| Terminal | Keep visible | Purpose |
| --- | --- | --- |
| A | `./factory/factory control-center --no-open` | Local factory server and fallback command output |
| B | Demo application | Pocket Cinema or TableStory |

Prepare these browser tabs:

1. attendee workshop website;
2. `http://127.0.0.1:5050`;
3. `http://localhost:5000`;
4. the disposable GitHub Project for the Live Run; and
5. one pull request for the merge-and-unlock explanation.

Don't start the application before running the live doctor. An occupied port is
reported as a warning.

The Control Center is the attendee path. Its four stages are **Setup**, **Plan**,
**Deliver**, and **Review**. Keep terminal commands below as a
facilitator recovery reference and to explain that the UI calls the same
versioned CLI. Do not tunnel or publicly expose port 5050.

## Timing and presenter cues

| Time | Attendee action | What to say or show |
| --- | --- | --- |
| 0–10 min | Pair and frame the outcome | Confirm separate repositories, identify peer reviewers, and name one candidate use case. |
| 10–25 min | Define the factory | Teach the five replaceable layers, review bottleneck, and location of human judgment. |
| 25–50 min | Connect and prove readiness | Establish the Project Contract, Charter, environment lifecycle, adapter capabilities, and passing preflight. |
| 50–65 min | Inspect Pocket Cinema and read the PRD | Identify the user journey, system constraints, preserved behavior, and observable success. |
| 65–82 min | Revise Product Review | Reject vague evidence, record feedback, and approve the objective revision. |
| 82–95 min | Trace R3 | Follow one requirement across Architecture, Program Design, Vertical Slices, and planned QA evidence. |
| 95–105 min | Break | Keep Control Centers and healthy agent sessions running. |
| 105–120 min | Align and publish | Show PRD-derived tickets and dependencies in GitHub Projects. |
| 120–138 min | Review Acceptance Tests | Approve QA-owned assertions only after causal RED evidence. |
| 138–157 min | Observe the Factory Run | Follow claim, worktree, Supervisor coordination, logs, gates, receipts, and back-pressure. |
| 157–168 min | Review, rework, and merge | Inspect the exact candidate revision and retain the accountable human merge decision. |
| 168–175 min | Verify the app and evidence | Verify TableStory, export the Evidence Packet, and preview Monitor findings. |
| 175–180 min | Complete the Canvas and close | Choose what to own, buy, or bring existing and name one bounded experiment. |

The schedule is a teaching target, not a guarantee that live model work will
finish. Live agents have no presentation timeout. Narrate observable state
instead of terminating slow work to manufacture a result.

## Rehearsal command path

Run Product Review:

```sh
./factory/factory plan recipe-app-prd.md --mock
./factory/factory review product PLAN_ID
./factory/factory revise PLAN_ID product \
  --feedback "Require automated Escape and Backspace checks that preserve mode=tv and restore focus." \
  --mock
./factory/factory review product PLAN_ID
./factory/factory approve-product PLAN_ID
```

Run and inspect technical planning:

```sh
./factory/factory continue-plan PLAN_ID --mock
./factory/factory review alignment PLAN_ID
./factory/factory approve-rehearsal PLAN_ID --scenario recipe-rebrand
```

Pause after the first QA wave:

```sh
./factory/factory run --mock \
  --scenario recipe-rebrand \
  --review-qa-tests \
  --once
./factory/factory approve-tests 1 --yes
./factory/factory approve-tests 2 --yes
```

Finish the scenario:

```sh
./factory/factory run --mock --scenario recipe-rebrand --once
./factory/factory merge ISSUE_NUMBER --yes
./factory/factory monitor
```

## Live command path

The commands below use Claude as a coherent worked example. If an attendee uses
a different registered implementation or QA adapter, the remaining planning,
GitHub Project, worktree, QA-review, and verification steps stay the same.

```sh
./factory/factory plan recipe-app-prd.md
./factory/factory review product PLAN_ID
./factory/factory revise PLAN_ID product \
  --feedback "Require automated Escape and Backspace checks that preserve mode=tv and restore focus."
./factory/factory review product PLAN_ID
./factory/factory approve-product PLAN_ID
./factory/factory continue-plan PLAN_ID
./factory/factory review alignment PLAN_ID
./factory/factory approve PLAN_ID \
  --new-project-title "TableStory Workshop"
./factory/factory run
```

The approved Vertical Slices artifact is the ticket source. The approval command
creates the issues, adds them to the new Project, and saves its number locally.
Do not seed tickets during the normal path.

Approve a reviewed test set from another terminal:

```sh
./factory/factory approve-tests ISSUE_NUMBER
```

If the tests do not represent the approved Ticket, request a replacement from
the Ticket's **QA Review** panel and describe the correction. Do not edit the
protected file directly or on GitHub. Edit the GitHub issue only when the
Ticket requirements themselves must change.

After a green pull request is merged, wait for **PR merged and synchronized**
before showing the next ticket move to Ready.

Demonstrate from the facilitator repository first. If its live run has not
reached the evidence you need, ask a consenting attendee whether you may show
their repository. If neither is ready, teach from the visible current state;
record missing evidence and complete it after the session.

## Evidence to show for one ticket

Don't click through every field. Use one ticket to show this sequence:

1. **Specification:** the authorized outcome and acceptance criteria.
2. **QA prompt and test diff:** independent evidence written before implementation.
3. **Protected test hashes:** the Implementation adapter can't weaken the evidence.
4. **Implementation prompt and log:** the current scope and activity.
5. **Changed files:** the code-review surface.
6. **Gate output:** the reason for pass, retry, or block.
7. **Supervisor decision:** the worker reports it read, the Ticket instruction
   it proposed, and the orchestrator's validated dispatch.
8. **Code review evidence:** the candidate commit, `APPROVE` or
   `REQUEST_CHANGES` decision, changed-path comments, and GitHub publication
   mode. On Ticket #1, show the first comment and the repaired second revision.
9. **Merge evidence:** the Supervisor's `MERGE` recommendation must name the
   same PR and commit that the Code Review role approved. In the Standard
   path, show the human exact-revision merge decision that follows it.
10. **Handoff Receipts:** the revisions, claim, verification, risks, and policy
   hashes behind each role transition.
11. **History:** merge synchronization and dependency unlock.

Use GitHub Projects for shared backlog ownership and dependencies. Use the
Control Center for local prompts, logs, worktree changes, protected tests,
gate results, and receipts. Do not describe the Control Center as a hosted
Project board.

Use the Supervisor screen to make authority explicit. Ticket worker roles report
results through Handoff Receipts. The Supervisor role recommends the next
bounded wave. The orchestrator validates and applies allowed commands. Humans
still approve Product Review, alignment, and Acceptance Tests when configured.
The Code Review role approves an exact candidate or requests changes but cannot
edit or merge. After approval, the Supervisor may recommend merge. The
orchestrator rechecks the PR revision, then Lean, Standard, and Assured wait for
a human decision. Only an explicitly opted-in Autonomous Demo executes the
Supervisor recommendation automatically.

GitHub does not allow the account that authored a PR to formally approve it.
With one workshop identity, point out the labelled Factory comment and explain
that it does not satisfy branch protection. A repository requiring formal
approval needs a distinct reviewer identity supplied through the uncommitted
`FACTORY_REVIEW_GH_TOKEN` environment variable.

## Recovery during the session

| Symptom | Response |
| --- | --- |
| GitHub, Wi-Fi, or a model is slow | Switch to the deterministic recipe scenario. |
| Product Review is blocked | Resolve the blocking question; don't continue to architecture. |
| A planning retry repeats the same error | Read the failed expert's recovery card. For validation, use the prefilled **Apply correction and continue** instruction. For a session or rate limit, select **Fix with Codex** (or another configured adapter). After the same process failure occurs twice, the Control Center disables same-adapter retry and preserves completed upstream artifacts. If governance changed, use **Restart planning safely**. |
| QA Review takes too long | Review one test set, then finish without `--review-qa-tests`. |
| A ticket is blocked | Open Summary and follow its cause-specific recovery. Record what changed and why another attempt can succeed before retrying. The reason is shown in Ticket details and sent to the next Supervisor and agent. Corrected Issues reload from GitHub and discard old-spec evidence; Project Contract repairs reload gates; stale PRs rebuild on a replacement branch; claims and dependency blockers never offer blind retry. |
| Live merge shows Rehearsal evidence | Do not merge it as Live. In Ticket Summary, either **Finish Rehearsal** or select **Open Reset**, clear only local run state, and rerun the published GitHub ticket. Source files and remote artifacts are preserved. |
| An attendee reset the wrong scope | Open **Reset**, verify the checkpoint timestamp and plan, then choose **Recover latest state**. With no checkpoint, a connected Live repository reconstructs from GitHub. Do not claim that deleted local receipts were restored. |
| Preflight reports `default branch` or `branch synchronization` | In the product checkout, save local work, then run `git fetch origin`, `git switch main`, and `git pull --ff-only origin main`. Do not force-reset attendee work. |
| Preflight reports an unavailable Codex or Claude adapter | Open **Setup → Connection**, select the preset for the CLI the attendee actually installed, save, sign in to that CLI, and select **Retry automatic setup**. |
| Preflight reports `No module named pytest` | Install the dependency with the repository's declared setup command, correct the contract if that command is missing, then select **Retry automatic setup**. |
| Preflight reports missing GitHub Projects scope | Run `gh auth refresh -s project`, finish authorization, and select **Retry automatic setup**. |
| Branch, Codex, and `pytest` failures appear together | Fix them in order: preserve local work; fetch, switch to `main`, and fast-forward it; select the passing Claude preset or sign in to Codex; install the declared dependencies; then select **Retry automatic setup**. Do not ask the attendee to repeat the same failed operation between fixes. |
| Live restart says the checkout is not on `main` | Run local reset again. A clean checkout preserves divergent local `main` under `recovery/pre-reset-main-*`, then aligns `main` exactly with `origin/main`. A dirty checkout must be committed or stashed by its owner first. |
| A port is occupied | Stop the old process or use a fresh checkout. |
| The state is stale | Use **Reset current run** in the Control Center after confirming demo changes can be discarded. |
| The agenda is late | Show one Acceptance Test approval and one dependency unlock, then verify the application. |

If GitHub works but live planning cannot finish, use
`./factory/factory seed recipe-rebrand` as a last-resort fixture. Tell attendees
that it bypasses PRD planning and both human alignment gates.

Reset a disposable rehearsal only when its demo changes can be discarded. The
Control Center offers two scopes: reset execution while keeping the approved
plan, or type `START OVER` to clear all workshop work while keeping attendee
configuration. The equivalent execution reset is:

```sh
./setup_demo.sh --scenario recipe-rebrand --force
```

The attendee-safe recovery command is:

```sh
./factory/factory recover --repo /path/to/attendee-repository --yes
```

Before the workshop, rehearse one reset and recovery. Confirm the dialog names
the checkpoint source, ticket count, and plan; confirm recovery creates an undo
checkpoint; and confirm a Live reset leaves the checkout on the exact remote
default revision without deleting the preserved branch.

The TV scenario remains available as an optional failure lab. Ticket 8 is
rejected because “It feels right” isn't an objective acceptance criterion.

## Dry-run acceptance criteria

The workshop is ready when a colleague can use the website without verbal help
to:

- select a path and verify its prerequisites;
- reach every checkpoint using **Setup → Plan → Deliver → Review**, with equivalent commands available;
- recover a failed preflight by reading the first `[FAIL]`, applying its specific fix, and rerunning the check;
- find the ticket board, ticket evidence, and troubleshooting section;
- explain the required Product Review and alignment approvals, any
  Charter-selected intermediate planning approvals, and the Acceptance Test
  approval;
- explain one dependency unlock;
- complete and peer review a Factory Canvas;
- export a sanitized Evidence Packet; and
- choose which Factory Profile addresses a concrete delivery risk.

## Freeze and publish the workshop

The repository remains private until the owner runs the complete rehearsal and
release audit. The day before delivery:

```sh
./factory/factory --version
.factory/venv/bin/python -m unittest discover -s factory/tests
npm --prefix workshop-guide test
npm --prefix workshop-guide run lint
./factory/factory release-check
./factory/factory release-check --rehearsal
```

The website suite includes structural accessibility checks; the release audit
checks participant links and possible secrets. The rehearsal release check
executes the complete Standard journey in a clean clone. Verify the deployed
website separately. In a dedicated disposable GitHub repository with Claude or
Codex authenticated, also run the golden-path smoke below. It creates a fresh
Project, uses the selected adapter for planning, QA, implementation, and supervision,
deterministically sends one Code Review comment back to the same PR, and merges
the repaired Ticket:

```sh
./factory/factory release-check --live-smoke \
  --live-agent codex \
  --confirm-disposable-repo
```

Use `--live-agent claude` for the Claude path. If omitted, Claude remains the
default for compatibility with the original release rehearsal.

The command creates a unique smoke endpoint and Project on every invocation so
an explicitly disposable repository can be retested without invalidating RED
proof. It still merges a real change; do not point it at an attendee repository.

After all checks pass, tag `workshop-v1.2.0`, make the repository public, and
enable GitHub template mode. Those external owner actions are intentionally not
automated by the factory.
