# Software (re)-Factory

Release: `workshop-v1.2.0`

Software (re)-Factory is a legible control layer for running several coding
agents against a dependency-mapped backlog. GitHub Issues are tickets, Projects
v2 is the audited board, Git worktrees isolate changes, and ordered gates decide
whether a ticket is retried, reviewed, or blocked. Two deterministic scenarios
make the factory visible: the main five-ticket exercise rebrands Pocket Cinema
as the TableStory recipe app, while an eight-ticket TV exercise demonstrates a
deliberately blocked requirement.

Those deterministic scenarios are a workshop pack, not a product constraint.
A Live Run accepts any PRD and any Git repository through a committed Project
Contract.

The implementation is organized as five replaceable layers: compute,
development environment, inner harness, outer harness, and control plane. Read
[INTERFACES.md](INTERFACES.md) before adding an Agent Adapter, environment
provider, intake source, trigger, or workspace integration.

## One-minute rehearsal quickstart

A Rehearsal Run needs Python 3.11+, Git, Node 20+, and no credentials or agent tokens.

```sh
./setup_demo.sh --scenario recipe-rebrand
./factory/factory control-center
```

Open <http://127.0.0.1:5050>. The Control Center guides the complete workflow,
shows the exact CLI command behind every action, and streams its output. Choose
**Rehearsal** to use deterministic agents without credentials or GitHub writes.

For a persistent single-repository deployment, use the
[AWS + GitHub CloudFormation edition](../deploy/aws/README.md). It runs the
authenticated Control Center on ECS Fargate, persists worktrees and state on
EFS, sends logs to CloudWatch, and adds a native Amazon Bedrock adapter without
changing the local CLI contract.

The equivalent CLI-only smoke run is:

```sh
./factory/factory run --mock --scenario recipe-rebrand --once
./factory/factory status
```

For versioned installation, drift-safe updates, and migration behavior, see
[COMPATIBILITY.md](COMPATIBILITY.md). An update is preview-only until
`factory/update_workshop.sh --apply` is supplied, and local drift fails closed.

The Rehearsal Run exercises the
same independent-QA commit and protected-test policy as a Live Run without using
credentials. The `recipe-rebrand` scenario runs five deterministic TableStory
tickets; the original `tv` scenario merges seven tickets and deliberately blocks
the vague eighth ticket.

To use the shorter `factory run` spelling during a workshop:

```sh
export PATH="$PWD/factory:$PATH"
factory run --mock --scenario recipe-rebrand --once
```

Reset between sessions with `./setup_demo.sh --scenario recipe-rebrand`. It
removes only rehearsal worktrees and `factory/*` branches, restores `demo-app/`
from the baseline tag, and clears runtime state. It refuses to overwrite
uncommitted `demo-app/` changes unless `--force` is supplied. A Blocked
worktree is otherwise preserved for review.

The `factory-baseline` tag must name the mobile workpiece — the
`chore: establish factory workshop baseline` commit. Setup repoints the tag
automatically and `factory doctor` fails if it drifts onto a finished
rehearsal, because a baseline carrying rehearsal-era tests grades fresh
tickets against a product they replaced and stalls every scenario. Push the
tag so clones inherit it:

```sh
git push origin factory-baseline
```

A checkout with no history for that commit (a downloaded archive rather than a
clone) cannot be repaired locally; clone from `origin` instead.

## Use any repository and PRD

Keep this factory checkout as the control plane. In the Control Center, select
**Live** and paste any accessible GitHub repository URL. The factory clones or
reuses it under the ignored `.factory/repositories/` workspace and operates on
that checkout without changing the factory repository's `origin`. The target
does not need to contain Pocket Cinema or the factory source.

To use an existing local checkout instead:

```sh
./factory/factory configure --repo /path/to/your-project \
  --preset codex-workshop \
  --github-repository https://github.com/YOU/YOUR-PROJECT
./factory/factory init --repo /path/to/your-project
# Review the repository model and operating policy.
./factory/factory approve-contract --repo /path/to/your-project --live
./factory/factory control-center --repo /path/to/your-project
```

In **Setup → Connection**, select **Live**, paste that project's GitHub URL,
choose the role adapters, and select **Save and connect**. Select **Create
contract**, review its repository model and operating policy, then select
**Approve contract and continue**. The final approval publishes the contract,
prepares the environment, checks health and gates, and runs full preflight. In
**Plan → Requirements**, paste or write the actual
product requirement. The four planning experts use the PRD for scope and the
Project Contract plus repository inventory for technical context. The approved
Vertical Slices become GitHub Issues and Project items; no scenario seed is
involved.

`factory init` detects common repository conventions and writes the two files
behind the repository contract: a technical Project Contract and a conservative
Factory Charter. `approve-contract` records one exact human approval, commits
and pushes only `.gitignore`, `factory.project.toml`, and
`factory.charter.toml`, refuses unrelated changes, and runs only setup commands
declared in the contract. The same contract
defines source and test roots, ticket-numbered QA filenames, tools, ports,
ordered gates, protected paths, default branch, and an optional
repository-specific reset adapter. Planning records its hash and must be
repeated if the contract changes. Review and commit any setup-generated lockfile
change before Live preflight; the default-branch checkout must be clean.

Operators can still run the internal environment lifecycle explicitly for
diagnosis:

```sh
./factory/factory environment provision --repo /path/to/your-project
./factory/factory environment prepare --repo /path/to/your-project --yes
./factory/factory environment health --repo /path/to/your-project --gates
./factory/factory doctor --repo /path/to/your-project --full
```

`environment reset` clears only provider-owned state and a provider-owned
preview. It preserves source, Issues, Projects, pull requests, and evidence.

Arbitrary PRDs require Live agents. Rehearsal remains deterministic by design
and therefore supports only its bundled Pocket Cinema scenarios.

For a greenfield product, create and connect an empty GitHub repository but
leave **Seed the guided Pocket Cinema starter** unchecked. In **Setup →
Connection**, use the same three steps: connect, create the contract, then
review and approve it. The automatic initial commit contains only
`.gitignore`, `factory.project.toml`, and `factory.charter.toml`. Planning turns
the PRD into GitHub Issues and the worker roles create the product and tests;
the local factory implementation is never copied into the product repository.
State the intended language, framework, and required verification in the PRD
and review the generic contract before approval.

## Architecture tour

Start with `ARCHITECTURE.md`, which maps the runtime into a short reading path.
The orchestration flow is intentionally direct:

1. Load issues and parse `Depends-on: #…` plus `agent: …` from each body.
2. Move dependency-complete, `agent-ready` tickets to Ready.
3. In Standard and Assured profiles, give ready Tickets and recent worker
   Handoff Receipts to the Supervisor role. The orchestrator validates its
   dispatch, defer, or block decision and remains the lifecycle authority.
4. Create `../<repository>-wt-<issue>` on `factory/<issue>-<slug>` and ask the independent
   QA adapter to add ticket-numbered acceptance tests only.
5. Commit and protect the Acceptance Tests; optionally pause for explicit human approval.
6. Run the Implementation adapter with the supervisor's Ticket instruction. The factory rejects any implementation that
   modifies or deletes a protected test.
7. Measure implementation-owned changed lines separately from protected QA
   tests and stop candidates that exceed the ticket limit.
8. Execute configured gates in order; feed the last 3,000 failure characters
   back to the agent for up to two retries.
9. On green gates, push or update the PR and give its exact candidate revision
   to the read-only Code Review role. Review comments return to the same
   Implementation adapter and consume the bounded retry budget; gates and review rerun.
10. After an `APPROVE` decision with no comments, the Supervisor may recommend
   a revision-bound `MERGE`. The orchestrator rechecks the live PR head. Lean,
   Standard, and Assured then stop for the human exact-revision merge action;
   only an explicitly opted-in Autonomous Demo executes the recommendation.
11. Reconcile the merge, unlock dependants, and mirror each transition and
    artifact path to `.factory/state.json` for the Control Center.

The Control Center teaches four macro phases—**Plan, Build, Verify, Review**—before
showing detailed ticket states. Every executed role produces a Handoff Receipt
with input and output revisions, its claim, verification, unresolved risks,
artifacts, and policy hashes. Worker roles communicate results to the Agent
Supervisor through those receipts; the Supervisor screen shows its validated
commands and decision history.

## Choose a Factory Profile

Profiles are executable role topologies, not presentation labels:

```sh
./factory/factory profiles
./factory/factory configure --profile standard
```

- **Lean** runs Product Review and Vertical Slices, then implementation,
  verification, and human review.
- **Standard** includes all four planning roles, supervised dispatch, independent
  QA, protected Acceptance Tests, implementation, verification, independent
  code review, review-comment rework, a Supervisor recommendation, and a human
  exact-revision merge.
- **Assured** adds cleanup, architecture conformance, hardening, and a read-only
  final verifier before independent code review and the same human merge gate.
- **Autonomous Demo** keeps the end-to-end automated merge demonstration. It is
  workshop-only and requires a fresh, visible opt-in for every run. A Charter
  `requires_human_approval` path still requires a human merge.

Agent Role contracts are versioned in `roles.json`; ownership, exclusions,
verification responsibility, and receipt requirements remain stable when an
Agent Adapter changes. Project policy is versioned in `policy.json`, and its
section hashes are recorded in plans and receipts.

The ticket backend is isolated in `github_backend.py`; adapter commands and gates
are all in `factory.toml`. You can keep the workflow and swap the CLI, model
wrapper, execution environment, test suite, or lint policy. See
`CONFIGURATION.md` for the complete project configuration contract. Adapter
Protocol v1 normalizes assignments, progress, results, cancellation, timeouts,
and trustworthy usage while keeping provider-specific capabilities visible.
Run `./factory/factory adapter-check` before selecting a custom adapter.

## Preflight every live session

Choose the workshop agents once. The ignored `.factory/local.toml` file stores
attendee-specific defaults; repository policy remains in `factory.toml`. Claude
is the worked example, not a factory requirement.

```sh
curl -fsSL https://claude.ai/install.sh | bash  # omit when already installed
claude auth login
./factory/factory configure --preset claude-workshop
./factory/factory doctor --full
```

For a Live Run, connect the attendee's repository explicitly. This removes any
dependency on the current `gh` default repository:

```sh
./factory/factory configure \
  --github-repository https://github.com/YOUR-NAME/YOUR-REPOSITORY \
  --preset claude-workshop
./factory/factory doctor --full
```

The preset selects Claude for planning, supervision, independent QA,
implementation, and code review,
requires human QA-test approval, selects the Standard profile, and limits
execution to one ticket at a time for a legible workshop trace.
Use `codex-workshop` to make the same choices with Codex. Explicit command-line
flags still override saved defaults for one invocation. Use `cursor-workshop`
to make the same choices with Cursor after `agent status` confirms its login.
You can also combine
built-in adapters or register your own supervision, implementation, QA, and code-review command:

```sh
./factory/factory configure \
  --planning-agent claude \
  --supervisor-agent claude \
  --agent cursor \
  --qa-agent codex \
  --review-agent claude \
  --review-qa-tests \
  --max-parallel 1
```

Built-in Bedrock, Claude, Codex, and Cursor planning adapters enforce the four
structured planning schemas. Supervision, implementation, QA, and code review can use any lowercase
adapter registered in `factory.toml`. Follow `CONFIGURATION.md` to connect a
different CLI, model wrapper, container, or remote runner. Cursor users should
also read [CURSOR.md](CURSOR.md).

If the GitHub Project already exists, save its number at the same time:

```sh
./factory/factory configure \
  --preset claude-workshop \
  --project-number "$PROJECT_NUMBER"
```

It checks repository safety and synchronization, GitHub authentication and
Projects scope, Python/Node and the virtual environment, agent CLIs, ports,
baseline data, configuration, and optionally the complete test suite.
For Standard and Assured runs it also reports whether
`FACTORY_REVIEW_GH_TOKEN` provides a distinct GitHub reviewer identity. Without
one, the validated review is posted as a labelled Factory comment instead of a
formal self-approval.

## Start from an attendee PRD

Copy `factory/PRD_TEMPLATE.md`, fill it in, then start the four-expert alignment
pipeline. Each expert is a fresh, read-only invocation of the planning CLI
selected by the workshop preset. Each stage has a distinct role, prompt, strict
JSON schema, Markdown review artifact, prompt, and log.

```sh
cp factory/PRD_TEMPLATE.md workshop-prd.md
# Edit workshop-prd.md
./factory/factory plan workshop-prd.md
```

The first command runs only **Product Review**. Inspect the product behavior,
users, journeys, scope, evidence, assumptions, mockup needs, and blocking
questions. Nothing technical runs until a human approves this contract:

```sh
./factory/factory review product PLAN_ID
./factory/factory revise PLAN_ID product \
  --feedback "Describe the objective evidence this requirement must produce"
./factory/factory review product PLAN_ID
./factory/factory approve-product PLAN_ID
```

Approval launches nothing. Continue explicitly to run **System Architecture**,
**Program Design**, and **Vertical Slices**, in that order:

```sh
./factory/factory continue-plan PLAN_ID
./factory/factory review alignment PLAN_ID
```

If the approved Charter also names `system_architecture` or `program_design` in
`policy.planning_approvals`, `continue-plan` pauses after that expert. Use the
Control Center approval, or review and approve the exact artifact from the CLI:

```sh
./factory/factory review architecture PLAN_ID
./factory/factory approve-stage architecture PLAN_ID
./factory/factory continue-plan PLAN_ID
```

Vertical Slice file ownership strengthens these gates automatically when it
intersects a Charter load-bearing path.

The run lives at `.factory/plans/PLAN_ID/` and contains:

- `source-prd.md` and a hash-tracked `manifest.json`.
- `01-product-review.{json,md}`.
- `02-system-architecture.{json,md}`.
- `03-program-design.{json,md}`.
- `04-vertical-slices.{json,md}`.
- `traceability.json` and `alignment-review.md`.

The generated traceability matrix connects each product requirement to
architecture contracts, program elements, vertical slices, and QA evidence.
Validation rejects unresolved questions, orphan requirements or program
elements, dependency cycles, missing evidence, and overlapping file ownership
between parallel tickets. Editing an approved upstream artifact invalidates its
approval and every downstream artifact; the factory never silently reuses stale
planning output.

Use `factory revise` rather than editing a generated artifact. It records human
feedback and revision history, reruns only the selected expert, clears affected
approvals, and marks downstream stages stale. The accepted stage names are
`product`, `architecture`, `program`, and `slices`. In the Control Center, a
blocked expert displays one answer field per question; submitting every decision
revises that artifact and resumes downstream planning without a JSON edit or CLI
command. If an expert instead fails deterministic validation, the rejected JSON
and validator message are preserved. Enter a specific repair instruction in the
failed expert card and select **Apply correction and continue**. The factory
uses the rejected JSON as the revision source, records the instruction, reuses
valid upstream work, and resumes only after the replacement validates.

After the alignment review, approve and publish the final slices:

```sh
./factory/factory approve PLAN_ID
```

The human types `APPROVE ALIGNMENT`; only then does the factory create or update
GitHub Issues, translate dependencies into issue numbers, add them to Projects,
and set dependency-free tickets Ready. Publication remains idempotent.

For a credential-free Rehearsal Run, record the same alignment approval and
materialize local tickets directly from the reviewed Vertical Slices:

```sh
./factory/factory approve-rehearsal PLAN_ID
./factory/factory run --mock --scenario recipe-rebrand --dry-run
```

Type `APPROVE ALIGNMENT`. This path writes only local rehearsal state and does
not contact GitHub.

The deterministic scenario supplies execution actions, but ticket titles,
specifications, criteria, dependencies, and plan provenance come from the PRD.

For a clean workshop board, create one during approval:

```sh
./factory/factory approve PLAN_ID --new-project-title "TableStory Workshop"
```

The approval command stores the selected Project number in `.factory/local.toml`.
Inspect the GitHub board, then deliberately start implementation:

```sh
./factory/factory run
```

## Listen for user-created GitHub issues

A Live Factory can remain open and admit new issues created directly in the
connected GitHub repository:

```sh
./factory/factory run --listen
```

For the complete Control Center workflow, issue template, recovery steps, and
troubleshooting, follow the
[Repository Issue Listener guide](ISSUE_LISTENER.md).

The first start records every currently open repository issue as a baseline.
It does not import that existing backlog. Later open issues are triaged and
added to the configured Factory Project. Issues created by Factory planning,
monitoring, or an earlier intake are identified by durable hidden markers and
are not ingested as new user requests.

An issue is executable when its body contains:

```markdown
## Spec
Describe the requested behavior.

## Acceptance criteria
- State an observable result.
```

An incomplete issue is still admitted, but it enters **Blocked** with the exact
triage cause and an editable proposed Ticket body. In the Control Center, open
the Ticket Summary, accept or edit the proposal, provide the retry reason, and
choose **Save ticket and retry**. The running listener treats that as a companion
action, reloads the edited GitHub issue, and re-triages it. Direct GitHub edits
are also detected on the next poll.

The listener does not bypass delivery controls. Admitted issues use the
configured implementation adapter and the selected Factory Profile's QA,
verification, code-review, and merge authority. An unknown `agent:` value falls
back to the configured implementation adapter and is recorded as an intake
warning. The listener remains running after all admitted Tickets are Done; stop
it with the Control Center stop action or `Ctrl+C`.

## Independent QA acceptance-test phase

Real factory runs use a dedicated QA adapter before the Implementation adapter for
every ticket. The committed repository default is Codex; an attendee preset
overrides it locally. The QA adapter can be different from the implementation
adapter, including a project-specific adapter registered in `factory.toml`:

```toml
[qa]
agent = "codex"
max_retries = 1
require_human_approval = false
```

Test placement stays in `factory.project.toml`:

```toml
[qa]
test_roots = ["tests"]
test_file_patterns = ["test_ticket_{ticket}*.py"]
```

You can select a different QA CLI for one run. To omit independent QA, select
the Lean profile; Standard and Assured reject `--no-qa`:

```sh
./factory/factory run --agent codex --qa-agent claude --max-parallel 4
./factory/factory run --profile lean --agent codex --max-parallel 1
./factory/factory run --agent codex --review-qa-tests
```

For each issue, QA receives the full spec and acceptance criteria. It may only
add new files that match the Project Contract's ticket-numbered patterns inside
its configured test roots. The factory
commits those files before implementation and records their Git blob hashes.
The Implementation adapter sees the protected-file list in its prompt and may add
more tests, but changing, renaming, or deleting an Acceptance Test fails verification and
is fed back into the normal retry loop.

With `--review-qa-tests`, a ticket pauses in **QA Review**. Inspect its test diff
from the Control Center or terminal. Approve the exact revision, or send focused
feedback so independent QA replaces the rejected tests and proves RED again:

```sh
./factory/factory approve-tests ISSUE
./factory/factory request-test-changes ISSUE \
  --feedback "Describe the required test correction"
```

Do not edit pending protected tests in GitHub or in the Factory worktree. Edit
the GitHub issue only when the requirement or acceptance criteria are wrong;
the next run reloads an edited issue and discards evidence tied to its old spec.

QA prompts and logs are separate from implementation artifacts:

```text
.factory/prompts/ISSUE-qa-attemptN.md
.factory/logs/ISSUE-qa-attemptN.log
```

The Rehearsal Run uses `mock_qa_agent.py`, so QA commits and protected-test checks
remain credential-free and deterministic. Passing `--qa-agent` explicitly with
`--mock` opts into a real QA CLI instead.

## Disposable attendee checkout

Avoid resetting an attendee's working repository by creating a disposable clone:

```sh
./factory/new_workshop.sh ../software-refactory-attendee live
```

The command refuses an existing destination and clones `origin`. Use `live` for
a synchronized Live Run checkout, or `tv`/`recipe-rebrand` to prepare a local
Rehearsal Run from the tagged baseline.

## Instructor-led Live Run

Keep the factory source checkout as the control plane, prepare the guided
TableStory workpiece there, and create an empty private attendee repository:

```sh
gh auth login
gh auth refresh -s project
git clone https://github.com/giolaq/software-refactory-workshop.git software-refactory-control
cd software-refactory-control
./setup_demo.sh --scenario recipe-rebrand
gh repo create YOUR-REPOSITORY --private
./factory/factory control-center
```

In **Setup → Connection**, choose **Live**, paste
`https://github.com/YOUR-NAME/YOUR-REPOSITORY`, select the role adapters, and
check **Seed the guided Pocket Cinema starter** before saving. The Control
Center verifies that the remote has no branches or tags and creates a fresh
product-only history containing `demo-app/`, `.gitignore`, the Project Contract,
and a draft Charter. It tags that commit as `factory-baseline` and opens an
isolated checkout under `.factory/repositories/` without changing the control
checkout's `origin`. Factory source, workshop documentation, setup scripts, and
the control repository's history are never published to the attendee repository.

For a CLI-only run, clone and bootstrap the empty attendee repository
explicitly, then configure the selected agents and start with a PRD. This
example uses Claude; select a built-in or custom setup from `CONFIGURATION.md`
if your team uses another CLI or model:

```sh
CONTROL="$PWD"
TARGET="$CONTROL/../software-refactory-live"
gh repo clone YOUR-NAME/YOUR-REPOSITORY ../software-refactory-live
./factory/factory bootstrap-workshop \
  --repo "$TARGET" \
  --source "$CONTROL"
./factory/factory configure \
  --repo "$TARGET" \
  --github-repository "https://github.com/YOUR-NAME/YOUR-REPOSITORY" \
  --preset claude-workshop
./factory/factory approve-contract --repo "$TARGET" --live --yes
./factory/factory plan "$CONTROL/recipe-app-prd.md" --repo "$TARGET"
```

Follow the two human planning gates described above. `factory approve` converts
the approved Vertical Slices artifact into GitHub Issues and adds them to the
selected Project. The tickets therefore come from the PRD; they are not a
separate prepared backlog.

Use deterministic tickets only when model access, latency, or workshop timing
prevents the planning exercise from completing:

```sh
./factory/factory seed recipe-rebrand
```

The seed command explicitly reports that it bypasses PRD planning and both human
alignment gates. It is a recovery fixture, not the normal product workflow. An
advanced operator can still target another repository explicitly:

```sh
./factory/factory seed recipe-rebrand --github-repo OWNER/REPOSITORY
```

The first run creates or reuses a **Software (re)-Factory** Projects v2 project,
normalizes its Status options, adds the issues, mirrors state labels, and opens
PRs after required gates pass. Configure `--project-number N` once to use an
existing project; approval also remembers a newly created Project automatically.
Use `--once` for one scheduler sweep; without it, the factory polls for QA
approvals and newly merged PRs every 20 seconds.

Run a no-write dependency preview before dispatch:

```sh
./factory/factory run --dry-run
```

## Recover a blocked Live Ticket

Every transition to `Blocked` records one `recovery` classification and
`next_human_action` in `.factory/state.json`. The Control Center shows that
action above the ticket metadata and does not offer Retry when the unchanged
state would fail again.

Open the blocked Ticket's **Summary** first. Its recovery panel separates
**Why it stopped**, **Proposed recovery**, and, when retry is valid, a
**Suggested retry reason**. Make the proposed correction before adapting that
reason and retrying; raw logs remain available as supporting evidence.

When the Factory can express an exact File ownership correction, Summary also
shows an editable **Proposed ticket body**. Accept it or revise it, review the
prefilled retry reason, then choose **Save ticket and retry**. The Control
Center preserves and validates the Ticket's Factory identity and governance
markers, saves the reviewed body to the configured GitHub repository, and
queues retry only after that save succeeds.

| Recorded cause | Recovery |
| --- | --- |
| Missing or ambiguous Ticket specification | Edit the GitHub Issue, preserve its Factory Plan and governance comments, then choose **Reload issue and retry**. An unchanged issue is refused. |
| Owned files cannot produce a functional change | Expand the GitHub Issue's Spec and File ownership to include the required integration path reported in **Last failure**, preserve its hidden Factory comments, then choose **Reload issue and retry**. The Factory stops after the first deterministic scope conflict and refuses an unchanged retry. |
| Project Contract does not describe the repository | Update, review, and commit `factory.project.toml`, then choose **Reload contract and retry**. The running Factory reloads its gates and test roots. |
| Protected QA tests are defective | Choose **Regenerate QA tests and retry**. The Factory discards only that ticket's candidate and protected QA evidence, restarts from the repository base, and gives the recorded defect to the next independent QA attempt. |
| Implementation diff exceeds the ticket limit | Split and replan the work, or enter an exact ticket-only limit and written reason. Protected QA lines are reported separately. |
| Dependency cycle or missing merged prerequisite | Correct the `Depends-on` graph or restore the prerequisite. Blind retry remains disabled. |
| Another Factory Run owns the remote claim | Resume the named run, or explicitly release only a confirmed abandoned claim. |
| GitHub rejected formal approval because the PR author and reviewer are the same account | Treat the labelled Factory comment as the structured Code Review evidence. Inspect and merge the exact reviewed PR; the running Factory verifies its merged head and marks the Ticket Done. When branch protection requires formal approval, restart with `FACTORY_REVIEW_GH_TOKEN` from a distinct reviewer instead. |
| A saved candidate passed its focused test but the result was misclassified | Choose **Re-verify saved candidate**. The Factory preserves the exact candidate and human-approved QA tests, skips another implementation dispatch, and reruns focused and repository verification with the corrected classifier. An interrupted re-verification is rediscovered from the exact worktree on restart. |
| PR was closed or its head changed after review | Choose **Rebuild and retry**. The Factory starts from the default branch on a versioned replacement branch, reruns QA and all gates, and closes a stale open PR as superseded. |
| A different revision was already merged | Preserve the merge history and create a new governed Ticket for corrective work. The original Ticket cannot be retried. |
| Retryable adapter or gate failure | Enter what was repaired or why another attempt can succeed, then choose **Retry ticket**. The reason is recorded and sent to the Supervisor and next agent. Eligible protected QA and candidate work are preserved; otherwise the Factory restarts from the repository base. |

For a corrected GitHub Ticket:

1. Open its Summary in the Control Center.
2. When an editable proposal is present, accept or revise it and choose
   **Save ticket and retry**. Otherwise, choose **Edit issue** and correct the
   title, Spec, Acceptance criteria, dependencies, or registered `agent:` line.
   Do not remove the hidden Factory Plan or governance comments.
3. For an externally edited issue, choose **Reload issue and retry**. The
   Factory reloads GitHub rather than trusting the local copy.
4. If the specification fingerprint changed, the old branch, QA evidence,
   gates, review, PR metadata, receipts, and ticket-only budget exception are
   cleared. The Ticket restarts from the current default branch.

The same change is detected after a Factory process restart: the edited Ticket
returns to `Backlog`, stale evidence is cleared, and normal triage decides when
it becomes `Ready`. A still-running process consumes the retry event without a
restart.

The basic CLI recovery is:

```sh
./factory/factory retry 8 \
  --reason "The missing generated-output ignores were added to the corrected Ticket"
```

Every manual retry requires a reason of at least 12 characters. The Factory
records it in Ticket history, displays it in the Control Center, includes it in
Supervisor coordination, and sends it to the next implementation prompt.

When the blocked-ticket recovery says the protected QA harness is defective,
use the dedicated recovery instead of generic Retry:

```sh
./factory/factory retry 8 \
  --reset-qa \
  --reason "The protected test used an internal API instead of public behavior" \
  --yes
```

`--reset-qa` is refused for every other blocker. It clears the ticket's old QA
commit, test hashes, RED/GREEN evidence, candidate, gates, review, and QA
approval, then regenerates independent tests from the current repository base.
The defect report is included in the first replacement QA prompt.

The command refuses a retry that cannot fit the measured diff budget. Either
split the ticket, or approve a ticket-only exception with an exact limit and
reason:

```sh
./factory/factory retry 8 \
  --budget-lines 1200 \
  --reason "The approved UI outcome requires the existing accessible workflow" \
  --yes
```

The Charter does not change. The exception is recorded on Ticket `#8`. The
Control Center recovery panel invokes this exact CLI contract.

## Recover after an accidental reset

Every `factory reset` first snapshots recoverable runtime state under
`.factory/recovery/checkpoints/`. Open **Reset or start again** and choose
**Recover latest state**, or run:

```sh
./factory/factory recover --repo /path/to/attendee-repository --yes
```

Recovery restores the newest pre-reset checkpoint and creates an undo
checkpoint first. It restores Factory-owned state, plans, prompts, approvals,
reviews, receipts, and saved Control Center documents that existed in that
checkpoint. It does not change tracked source or GitHub.

For a Live Run made before checkpoint support, `factory recover` reads the
configured GitHub Project, governed issue markers, Project statuses, pull
requests, sanitized run summaries, and active claims. It selects the latest
published plan and reconstructs local ticket and planning dashboards without a
GitHub write. Surviving planner logs can restore structured artifacts. Deleted
local Handoff Receipts and review history are reported as unavailable and are
never fabricated.

A Live local-state reset also returns a clean managed checkout to the exact
`origin` default revision. If local `main` diverged, its previous revision is
preserved under `recovery/pre-reset-main-*` before `main` is aligned. A dirty
checkout stops the reset before runtime state is deleted.

Per-ticket `agent: adapter-name` overrides the default when that lowercase name
is registered under `[agents]` in `factory.toml`. Before a live session,
smoke-test each installed CLI or wrapper because provider flags can change;
update only its adapter template when needed.

Claude planning uses Claude Code structured output with the stage JSON schema.
It runs in plan mode with read-only repository tools. Authenticate it with:

```sh
claude auth login
claude auth status --text
```

For Codex, the factory selects a current CLI with either a valid saved ChatGPT
login or an explicit managed-credentials environment. It skips legacy `codex`
executables that only support `OPENAI_API_KEY`. On macOS it also checks the CLI
bundled with the ChatGPT app. Override discovery when needed:

```sh
export FACTORY_CODEX_BIN=/path/to/current/codex
"$FACTORY_CODEX_BIN" login status
```

Managed Amazon Bedrock wrappers also require an AWS region. The factory checks
`AWS_REGION`, then `AWS_DEFAULT_REGION`, then the selected profile in
`~/.aws/config`; it passes the resolved region to Codex without forwarding AWS
credential variables. `factory doctor --full` reports the selected region or
fails with the configuration needed before an agent starts.

## Product payoff

The default recipe rehearsal finishes with a responsive, offline TableStory
app. Start it with:

```sh
.factory/venv/bin/python demo-app/app.py
```

Open <http://localhost:5000/> for the recipe browser and
<http://localhost:5000/?mode=tv> for its keyboard-driven TV presentation.

To rehearse the original Pocket Cinema TV story instead, reset and run:

```sh
./setup_demo.sh --scenario tv --force
./factory/factory run --mock --scenario tv --once
```

Before that run, the mobile baseline starts with:

```sh
.factory/venv/bin/python demo-app/app.py
```

After the seven successful Rehearsal Run merges, open <http://localhost:5000/?mode=tv>.
Use arrow keys and Enter on the home rails, then Escape or Backspace in film
details. The data and gradient poster artwork are bundled and fictional, so the
demo works offline.

## Export review evidence

Generate the 16-section Factory Canvas, complete it, and ask a peer to review
it before export:

```sh
./factory/factory canvas --output factory-canvas.md
./factory/factory evidence PLAN_ID --canvas factory-canvas.md
```

The packet includes reviewed planning, approvals, traceability, selected ticket
and pull-request links, protected-test metadata, gate results, Handoff Receipts,
the Canvas, missing-evidence warnings, and a hash manifest. Raw prompts, raw
logs, command output, environment values, tokens, and credentials are excluded.

Before a public/template release, freeze a clean tree and run:

```sh
./factory/factory --version
.factory/venv/bin/python -m unittest discover -s factory/tests
npm --prefix workshop-guide test
npm --prefix workshop-guide run lint
./factory/factory release-check
./factory/factory release-check --rehearsal
```

The local audit checks release identity, tracked generated state, possible
credentials, obsolete participant-facing language, and a clean worktree. The
`--rehearsal` check clones committed HEAD and executes the complete Standard
planning, approval, execution-role, and retry path. Maintainers can additionally
validate GitHub Issue, Project, PR, merge, and dashboard synchronization from a
disposable repository. This opt-in check runs the selected authenticated Agent
Adapter for planning and delivery with a deterministic review adapter, creates
a fresh Project and run-specific smoke
endpoint, approves independent
Acceptance Tests, returns one review comment to the same implementation branch,
merges the repaired Ticket, and verifies its Evidence Packet links:

```sh
./factory/factory release-check --live-smoke \
  --live-agent codex \
  --confirm-disposable-repo
```

`--live-agent` accepts `bedrock`, `claude`, `codex`, or `cursor` and defaults
to `claude`.

The unique endpoint preserves causal RED proof when the same explicitly
disposable repository is reused. Every invocation still creates and merges a
real change, so never run this command against an attendee or product repository.

## Operator reference

```text
factory configure [--preset claude-workshop|codex-workshop|cursor-workshop|bedrock-aws]
                  [--profile lean|standard|assured|autonomous-demo]
                  [--agent NAME] [--qa-agent NAME]
                  [--planning-agent bedrock|claude|codex|cursor]
                  [--review-qa-tests|--no-review-qa-tests]
                  [--max-parallel N] [--project-number N]
factory control-center [--port N] [--no-open]
factory bootstrap-workshop --repo PATH --source WORKSHOP_CHECKOUT
factory init [--repo PATH] [--name NAME] [--force]
factory approve-contract [--repo PATH] [--live] [--yes]
factory environment provision [--repo PATH]
factory environment prepare [--repo PATH] [--yes]
factory environment health [--repo PATH] [--gates]
factory environment preview [--repo PATH]
factory environment reset [--repo PATH] [--yes]
factory environment destroy [--repo PATH] [--yes]
factory seed [recipe-rebrand|tv] [--github-repo OWNER/REPOSITORY] [--agent NAME]
factory run [--repo PATH] [--profile lean|standard|assured|autonomous-demo]
            [--agent NAME] [--qa-agent NAME] [--supervisor-agent NAME]
            [--review-agent NAME] [--allow-autonomous-merge]
            [--review-qa-tests|--no-review-qa-tests] [--scenario tv|recipe-rebrand]
            [--max-parallel N]
            [--project-number N] [--once] [--dry-run] [--listen] [--mock]
factory plan PRD.md [--output RUN_DIRECTORY] [--default-agent NAME]
                    [--profile lean|standard|assured|autonomous-demo]
                    [--planning-agent bedrock|claude|codex|cursor]
                    [--min-tickets N] [--max-tickets N] [--mock]
factory review product|architecture|program|alignment PLAN_ID
factory approve-product PLAN_ID [--yes]
factory approve-stage architecture|program PLAN_ID [--yes]
factory continue-plan PLAN_ID [--mock]
factory revise PLAN_ID product|architecture|program|slices
               (--feedback TEXT|--feedback-file PATH) [--mock]
factory approve PLAN_ID [--project-number N] [--new-project-title TITLE] [--yes]
factory approve-rehearsal PLAN_ID [--scenario recipe-rebrand|tv] [--yes]
factory approve-tests ISSUE [--yes]
factory request-test-changes ISSUE
                            (--feedback TEXT|--feedback-file PATH) [--yes]
factory status [--repo PATH]
factory retry ISSUE --reason TEXT
                    [--repo PATH] [--project-number N] [--mock]
                    [--reset-qa --yes]
                    [--budget-lines N --yes]
factory release-claim ISSUE --owner-run-id RUN_ID --reason TEXT --yes
factory reset [--repo PATH] [--start-over] [--local-state-only]
factory recover [--repo PATH] [--project-number N] [--yes]
factory profiles [--json]
factory canvas [--output PATH] [--force]
factory evidence PLAN_ID --canvas PATH [--ticket ISSUE] [--output DIRECTORY]
factory release-check [--repo PATH] [--rehearsal]
                      [--live-smoke --confirm-disposable-repo]
factory doctor [--repo PATH] [--full] [--agent NAME] [--qa-agent NAME]
               [--planning-agent bedrock|claude|codex|cursor]
```

Runtime artifacts are under `.factory/`: `planning-state.json`, planning runs,
`state.json`, QA, implementation, and code-review prompts, structured review
artifacts, and one log per phase attempt.
Required gate failure blocks progress;
optional gate failure is recorded in the ticket's `warnings`. Killing and
restarting the loop replays an interrupted active ticket from a clean worktree
and reuses any already-open PR.

The Control Center shows the four planning contracts, human gates, ticket board,
live operations, and evidence. See `CONTROL_CENTER.md` for its workflow and
local security boundary. The original static dashboard remains a read-only
compatibility view.

See `WORKSHOP_OUTLINE.md` for the colleague-facing teaching structure and
`FACILITATOR.md` for the live-demo sequence and recovery notes. See
`CONFIGURATION.md` before adapting the workshop to another repository or agent.
