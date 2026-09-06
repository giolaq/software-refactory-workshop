# Factory Control Center

The Control Center is the local operator interface for the Software
(re)-Factory. It turns the normal PRD-to-evidence workflow into a guided web
experience while keeping the CLI as the execution layer.

Start it from the workshop repository:

```sh
./factory/factory control-center
```

It opens <http://127.0.0.1:5050>. Keep that terminal running during the
workshop. Press `Ctrl+C` to close the server.

## What attendees do

| Screen | Attendee action | Factory result |
| --- | --- | --- |
| Setup → Connection | Connect the repository, create the contract, then review and approve | Publishes setup where needed, prepares the environment, and runs readiness checks automatically |
| Plan → Requirements | Review or edit the auto-saved requirement; start Product Review | Saves a local PRD and runs the first planning expert |
| Plan → Review plan | Read four expert artifacts; approve Product Review, final alignment, and any Charter-selected intermediate gates | Creates PRD-derived rehearsal tickets or GitHub issues |
| Deliver → Tickets | Run the scheduler or start Live repository issue listening; inspect prompts, logs, diffs, tests, gates, code review, and history | Operates isolated worktrees, admits later user-created issues, and shows live state |
| More tools → Supervisor activity | Inspect worker reports, dispatch instructions, blocks, merge recommendations, and prior decisions | Explains how the next safe Ticket wave and approved revision were coordinated |
| Review → Run app | Preview baseline or merged work; export and download run evidence | Shows which checkout is previewed and keeps incomplete tickets visible |
| More tools → Repository monitor | Preview read-only health findings; publish only by explicit Live action | Finds stale claims, waits, drift, CI, and advisories without repairing code |
| More tools → Factory interfaces | Check workspace revisions, inspect trigger proposals, and generate a reviewed improvement report | Makes optional production seams visible without changing the beginner workflow |

Every operation shows the exact equivalent CLI command and streams its output.
The interface runs one command at a time, so two buttons cannot start competing
factory processes.

Ticket decisions are companion actions while a scheduler or issue listener is
running. This allows an attendee to approve tests, merge, retry, or accept and
edit a proposed Ticket correction without stopping the long-running command.

The primary navigation follows four operator stages: **Setup**, **Plan**,
**Deliver**, and **Review**. Supervisor activity and repository monitoring are
available under **More tools**. Advanced role configuration, run options,
diagnostics, and CLI output stay collapsed until needed so the next safe action
remains visually dominant.

Setup begins with three actions. Keep architecture explanations in the
facilitator presentation. The advanced selected Agent Adapter card
shows its Adapter Protocol version and declared features. An unavailable
feature remains visibly unavailable; choosing another adapter does not change
the role's policy or authority.

Setup has three attendee decisions:

1. **Connect** — select the GitHub repository, run mode, Factory Profile, and
   agent preset, then select **Save and connect**.
2. **Create contract** — let the factory detect source folders, tests, gates,
   and a conservative operating policy.
3. **Review and approve** — inspect the repository model and operating policy,
   then select **Approve contract and continue** once.

The final approval runs the mechanical work in order: publish the contract in
Live mode, provision the checkout, run only declared setup commands, check
health and gates, and run preflight. **Activity and CLI output** names every
substep and stops at the first error. Fix that error and select **Retry automatic
setup**; completed governance work is safe to repeat.

The granular `publish-setup`, `environment`, and `doctor` commands remain
available to operators for diagnosis, but they are not separate attendee
phases. Provider reset preserves source and GitHub evidence and remains
separate from **Reset run**, which controls planning and Ticket history.

If a planning expert cannot make a product or technical decision safely, its
card shows each blocking question with an answer field. Answer every question
and select **Submit decisions**. For System Architecture, Program Design, and
Vertical Slices, the Control Center records the answers, preserves the previous
artifact, reruns only that expert, and resumes downstream planning. Product
Review returns to its human approval gate after revision. A blind retry remains
available only for operational failures that did not produce blocking questions.

If an expert returns schema-valid JSON that fails deterministic cross-artifact
validation, the failed expert card shows the exact validator message and the
preserved rejected artifact. Enter a concrete correction, then select **Apply
correction and continue**. The rejected artifact becomes the revision source;
the factory records the human instruction, reuses every approved upstream
artifact, validates the replacement, and resumes only after it passes. The
correction field starts with the exact validator failure, so the attendee can
apply or refine a concrete repair without reconstructing the error. Each failed
replacement remains available as evidence.

Agent-process failures are classified separately. A session or rate limit does
not expose a same-adapter retry because that would repeat the same failure;
choose another configured Bedrock, Claude, Codex, or Cursor adapter, or wait for the provider to
become available. Authentication and missing-tool failures point to preflight.
Only an unclassified, potentially transient process failure offers **Retry same
adapter**. Adapter changes are recorded in the manifest, valid upstream
artifacts remain unchanged, and only the failed and downstream stages rerun.

When `factory.charter.toml` selects `system_architecture` or `program_design` in
`policy.planning_approvals`, the pipeline shows another human gate immediately
after that expert. Review the artifact and choose **Approve System Architecture**
or **Approve Program Design**. The next expert cannot start until the exact
artifact hash is approved; an edit clears that approval and every downstream
approval.

Use the three recovery actions deliberately:

- **Retry same adapter** is available only for an otherwise-unclassified,
  potentially transient process failure.
- **Switch adapter and continue** recovers from provider capacity or
  availability without discarding approved upstream artifacts.
- **Apply correction and continue** revises a rejected artifact with a recorded
  human instruction when deterministic validation would otherwise repeat.
- **Restart planning safely** creates a governed run from the saved PRD when
  the PRD, Project Contract, or Factory Charter changed. The old run remains
  evidence and no GitHub Ticket is rewritten silently.

After verification, open the Ticket's **Code review** tab. It shows the
reviewer adapter, candidate commit, `APPROVE` or `REQUEST_CHANGES` decision,
file-and-line comments, publication mode, and structured review artifact.
`REQUEST_CHANGES` returns the comments to implementation; the same PR is updated,
gates rerun, and the new revision is reviewed. `APPROVE` enables a revision-bound
Supervisor recommendation. In Lean, Standard, and Assured, a person must inspect
that exact revision and choose whether to merge it. The Code Review role does
not edit or merge.

The Ticket Summary also shows the **Non-authoritative merge steward**. It
distinguishes **ready for human merge**, **steward updating**, and **human
decision required**. When the default branch moved, select **Synchronize and
re-verify** only after reading the confirmation. A changed candidate revokes
gates and Code Review, then returns through verification. Semantic conflicts,
protected-path changes, changed Acceptance Tests, branch-protection failures,
and unresolved comments always stop for a person. The steward never selects
the merge action.

## Inspect optional factory interfaces

Open **More tools → Factory interfaces** after a run when you need production
integration evidence:

- **Workspace contract** checks every configured repository and revision,
  names the Ticket and pull-request target, and blocks missing services or
  drift before implementation with a named recovery owner. Without
  `factory.workspace.toml`, it reports the normal single-repository default.
- **Authenticated triggers** lists deduplicated schedule, webhook, issue, CLI,
  and Control Center proposals. Authentication happens at the integration
  boundary; every accepted event still enters governed intake and cannot
  dispatch directly.
- **Reviewed compounding** generates suggestions from repeated bounded
  observations already retained by planning, Tickets, code review, and the
  Monitor. Each suggestion names evidence, effect, regression risk, and a
  verification plan; regenerating the report deduplicates evidence references.
  It cannot modify the Factory Charter or delivery configuration.

These tools are optional in the workshop. Their purpose is to make a future
integration replaceable, not to require hosted infrastructure for a local run.

## Inspect the Supervisor role

Standard and Assured Factory Profiles use a supervisor before each dispatch
wave. Ticket roles do not message one another or change the board directly.
They finish their assignment, and the orchestrator records the result as a
Handoff Receipt. At the next checkpoint the supervisor receives:

- every dependency-ready Ticket and the configured parallel limit;
- the current Ticket and dependency state; and
- recent QA, implementation, verification, and review Handoff Receipts.

At a dispatch checkpoint, the supervisor can propose only two commands: dispatch
a ready Ticket with a short coordination instruction, or block it with an
explicit reason. After code-review approval, it has a separate `MERGE` or `BLOCK`
contract tied to the PR and candidate head. The
orchestrator rejects unavailable Tickets, duplicate or conflicting commands,
excess parallelism, malformed output, and silent stalls. It then applies valid
commands and remains the lifecycle authority. Before merge, it also confirms
that gates pass, the decision was published, and the live PR head still matches.

With human merge authority, `MERGE` means ready for your exact-revision review.
It does not approve or execute the merge on your behalf. Pending human approval
is a waiting state, not a supervisor blocker.

Open **Supervisor** while a run is active. Read the latest summary from top to
bottom: worker reports, dispatch/block/defer decisions, Ticket instructions,
and the prompt and log used for that checkpoint. Open a Ticket's **Supervisor**
tab to connect its instruction with its later worker receipts. The deterministic
Rehearsal Supervisor makes the same contract visible without credentials.

## Read the overview

The first panel is the operating summary:

- **Current phase** names the active workshop phase and, during execution, the
  ticket and role doing the work—for example independent QA, implementation,
  verification gates, code review, or merge synchronization.
- **Next checkpoint** names the next action or inspection point and opens the relevant screen.
- **Factory progress** separates completed, current, and pending phases.
- **Waiting for you** lists approvals and blockers that pause automation.
- **Operation** shows the exact command and its live output. It explains a
  failure until the next command runs.

When the scheduler remains open while waiting for QA approval, that required
human decision takes priority over the generic “running” state. During an
Autonomous Demo merge, the exact review and Supervisor evidence remains
inspectable. Other profiles stop at a visible human merge decision.

## Rehearsal and live modes

Choose **Rehearsal** to use deterministic local planning, supervision, QA,
implementation, verification, and code review.
It requires no model credentials and makes no GitHub Project writes.
Its preflight checks the local repository and workshop tools without calling an
agent CLI.

Choose **Live** to use the configured agent CLIs and GitHub. In this mode,
GitHub Issues and Projects remain the shared source of truth. The Control Center
is the detailed operator view for the local prompts, worktrees, tests, and logs
that GitHub does not contain. Live preflight also verifies agent authentication
and runs the configured gates.

When you reopen the page, an existing run restores its recorded mode. Check the
mode in the sidebar before running an action; it matches the mode used by the
buttons. Changing it does not convert existing Live or Rehearsal evidence.

In **Setup → Connection**, paste the attendee's GitHub repository URL before saving Live
configuration. Saving verifies access, clones or reuses that repository under
the Control Center's ignored `.factory/repositories/` workspace, and switches
the interface to that checkout. The repository card must show **connected**
before preflight. The factory never rewrites the factory source checkout's
`origin`, and it uses the saved target explicitly even if `gh` has a different
default repository.

For the guided TableStory exercise, create an empty GitHub repository and check
**Seed the guided Pocket Cinema starter** when saving. The Control Center fails
closed unless the remote has no branches or tags, then publishes a fresh
product-only commit containing `demo-app/`, `.gitignore`, the Project Contract,
and a draft Charter. Factory source, workshop documentation, setup scripts, and
the control repository's history stay in the control checkout. Leave this
unchecked for an existing project; the factory never replaces repository
contents.

For a greenfield product, also leave the option unchecked. After the empty
repository activates, select **Create contract**, review its repository model
and operating policy, then select **Approve contract and continue**. The
automatic setup creates a minimal default branch containing only governance and
`.gitignore`, prepares the environment, and runs preflight. The PRD, planning
artifacts, GitHub tickets, and worker changes then create the product; the
factory implementation remains in the separate control checkout.

### Listen for new repository issues

Repository issue listening is explicitly Live-only. On **Deliver → Tickets**,
open **Run options** and choose **Listen for new issues**. The status band reports whether
the listener is starting, listening, degraded, or stopped, plus its baseline,
admitted, and ignored counts.

For a start-to-finish walkthrough, use the
[Repository Issue Listener guide](ISSUE_LISTENER.md).

On its first start, the listener records all current open issues as a baseline,
so it never surprises an attendee by implementing an old backlog. Open a new
GitHub issue after the status becomes **Listening** and use this body:

Raw feedback becomes an evidence-backed proposal. A feature is
`READY_TO_PLAN`; a bug is `READY_TO_IMPLEMENT` only when the affected and latest
revisions, environment, focused causal reproduction, acceptance criteria, and
file ownership are present. Collection, setup, and unrelated failures do not
count as reproduction. Open the Ticket Summary to review the classification and
missing evidence. A proposal cannot dispatch work. A person must record why a
reproducible bug is sufficient before **Approve intake for triage** becomes the
normal delivery path. Factory planning, monitor, and prior intake Issues are
ignored to prevent recursion. See [ISSUE_LISTENER.md](ISSUE_LISTENER.md).

### Open an existing local checkout

The URL workflow above is the normal path. To use an existing local checkout
instead, pass it when starting the Control Center:

```sh
./factory/factory control-center --repo /path/to/your-project
```

Use the same three steps: **Save and connect**, **Create contract**, then
**Approve contract and continue**. “Repository contract” is the single review
concept in the UI. Its technical model is stored in `factory.project.toml`; its
human-owned operating policy is stored in `factory.charter.toml`. The approval
publishes only those governance files and `.gitignore`, provisions and prepares
the declared environment, and runs full preflight. Unrelated working-tree
changes still make publication stop safely.

The PRD editor accepts any product requirement. Live planning combines its
scope with this contract and a bounded repository inventory. Rehearsal planning
uses the bundled TableStory fixture and is not a generic implementation mode.

## Safety boundary

The Control Center is intentionally local and unauthenticated:

- It binds only to `127.0.0.1` or `localhost`.
- It accepts only same-machine browser requests.
- It exposes a fixed list of factory actions, never arbitrary shell commands.
- It passes arguments directly to the existing CLI without a shell.
- It opens only allowlisted files under `.factory`; configuration and
  credentials are not readable through the browser.
- Agent credentials stay in the selected CLI's normal credential store.

Do not expose port 5050 through a tunnel, reverse proxy, container port, or
public deployment. The hosted workshop guide explains the exercise; the
Control Center operates a local repository and therefore stays on the attendee's
machine.

## Recovery

For a ticket at **QA Review**, open **Tests**. Read the acceptance criterion,
the protected test code from its recorded Git revision, and the baseline
assertion failure before selecting **Approve tests**. The viewer checks the
recorded Git blob hashes; it does not show an uncommitted working copy.
Request corrections in the same tab. RED PROVED classifies an assertion
failure; it does not establish that the assertion tests the right requirement.

At **Review → Run app**, the branch, revision, local-change warning, and completed
ticket count identify what is being previewed. Unmerged ticket worktrees are not
part of this checkout. Stop the app, select **Export run evidence**, open the
packet, then select **Download**. No Canvas is required. The optional **Run effort**
section shows recorded ticket execution, waiting time, and retries; provider
usage and price are separate from these duration measurements.

While the Factory runner is open, **Start app** is disabled. To inspect merged
work without stopping agents, use **Copy command** and run it in a separate
terminal. This previews the managed checkout, not unmerged ticket worktrees.

If an action fails, read the operation output first. The same command is shown
above it, so you can copy it into a terminal when deeper diagnosis is useful.

If GitHub fails while approved tickets are being published, the alignment
decision remains recorded and Planning shows **Retry ticket publication**.
Retrying is idempotent: issues carrying the same plan-and-slice marker are
reused instead of recreated. The equivalent CLI recovery is the same
`factory approve PLAN_ID --yes --project-number N` command shown in the failed
operation.

If an agent is still running, select **Stop operation**. A later Factory Run
recovers interrupted ticket work through the normal orchestrator logic. Use the
ticket History and Live log tabs to find the recorded blocker, then follow the
cause-specific recovery panel at the top of Summary. It reloads an edited
GitHub Issue, reloads a repaired Project Contract, records a bounded diff
exception, rebuilds a stale PR revision, or routes an ownership/dependency
decision without presenting a retry that will deterministically fail. The open
drawer preserves its tab and scroll position while snapshots and Live logs
refresh.

Prefer stopping at a review checkpoint. If implementation has not changed the
clean, approved QA revision, restart keeps that QA approval. Changed scope or
uncertain work requires the normal recovery checks. A retry may retain an
already-approved candidate without creating another commit; it still reruns
verification and review before returning to the human merge decision.

If review asks for browser evidence, record the candidate revision, checks, and
results in a Markdown file under the target repository's `.factory/reviews/`.
Reference that relative path in the retry reason. The Factory includes the
report text and hash in the isolated implementation, code-review, and supervisor
handoffs. Reports are limited to 20 KB each and are evidence, not merge approval.
If only evidence changed, include the full candidate revision in the report.
The same code can then return through verification and independent review
without a cosmetic commit. Stopping a repair at a clean, already-reviewed head
preserves the candidate but requires an operator retry; it does not approve it.
If the agent committed a clean repair just before stopping, restart can preserve
that descendant revision when protected tests still match. The repair must pass
fresh verification and review; its predecessor's approval does not apply.

Coding agents can also supply a report in their worktree at
`.factory/review-handoff.md`. The report must name the full candidate revision
and stay within 20 KB. The Factory redacts credentials, saves a content-hashed
copy, and passes it to review and supervision as an implementation-authored
claim. This is not independent verification or human approval. Runtime reports
remain outside the committed application tree.

For an exact File ownership blocker, Summary proposes the corrected GitHub
Ticket body and a retry reason. The attendee can accept or edit both, then
choose **Save ticket and retry**. The Control Center validates the required
paths, exact Factory identity and governance markers, and configured repository
before saving GitHub. Retry runs only after the save command succeeds.

If an In Review ticket has `rehearsal://` review evidence while the Control
Center is set to Live, the drawer suppresses the merge action. Finish it in
Rehearsal, or open **Reset**, clear local run state, and load the published
Live ticket from GitHub. A Rehearsal candidate never becomes a Live candidate:
the Live run must create and approve an exact GitHub pull request.

Use **Reset run** in the lower-left sidebar:

- **Recover latest state** restores the newest local pre-reset checkpoint.
  The dialog shows its timestamp, ticket count, and plan. If no checkpoint
  exists for a connected Live repository, it reconstructs the latest governed
  plan from read-only GitHub evidence. Recovery creates an undo checkpoint
  first and never invents missing receipts or review history.
- **Reset current run** restores Pocket Cinema and clears ticket execution,
  worktrees, branches, test approvals, implementation evidence, and run state.
  It keeps the PRD, approved expert plan, Factory Canvas, agents, and Project
  choice, so you can demonstrate the same tickets again.
- **Start workshop over** also clears the saved PRD, expert artifacts, human
  approvals, rehearsal tickets, Canvas, and Evidence Packets. It keeps only the
  attendee's agent and GitHub Project configuration.

The workshop Project Contract delegates Rehearsal reset to its reviewed Pocket
Cinema adapter, which refuses to overwrite uncommitted `demo-app` changes. For
a Live Run, reset bypasses every repository adapter and clears only `.factory`
runtime state and factory-owned worktrees. A clean managed checkout returns to
the exact `origin` default revision; a divergent local default branch is
preserved under `recovery/pre-reset-*` first. Uncommitted source stops the reset.
Reset never deletes GitHub issues, Projects, branches, or pull requests.

The equivalent recovery command is:

```sh
./factory/factory recover --repo /path/to/repository --yes
```

The Control Center is the supported workshop dashboard. Compatibility and
migration behavior are documented in `COMPATIBILITY.md`.
