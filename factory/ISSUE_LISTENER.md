# Repository Issue Listener

This guide shows how to keep a Live Factory running and turn new user-created
GitHub issues into evidence-backed proposals. Raw feedback never starts an
Implementation adapter directly.

## Before you start

Use a repository that is already connected to the Control Center. Complete the
normal **Setup** checks first:

1. Start the Control Center from the factory checkout:

   ```sh
   ./factory/factory control-center
   ```

2. Open <http://127.0.0.1:5050/>.
3. Open **Setup → Connection**, select **Live**, enter the GitHub repository
   URL, choose the Factory Profile and role adapters, then select **Save and
   connect**.
4. Select **Create contract** and review the detected repository model and
   operating policy.
5. Select **Approve contract and continue**. Confirm that the automatic publish,
   environment preparation, health, gates, and preflight operation has no
   failures.

The GitHub repository must have Issues enabled. The selected GitHub identity
must be able to edit issues, create labels, add Project items, and create pull
requests.

## Step 1: Start listening

1. Open **Deliver → Tickets** in the Control Center.
2. Open **Run options**.
3. Confirm that **Mode** is **Live**.
4. Select **Listen for new issues**.
5. Watch the operation output until the repository issue listener reports
   **Listening**.

The first start records every currently open issue as the baseline. Those
issues are not imported or implemented. This prevents an old repository backlog
from being executed unexpectedly.

The listener status band shows:

- **Baseline**: open issues recorded at first start;
- **Admitted**: later user-created issues evaluated by Factory intake; and
- **Ignored**: later Factory-managed issues excluded from intake.

Do not create the demonstration issue until the status is **Listening**. An
issue opened before the baseline is recorded is intentionally treated as old
backlog.

## Step 2: Open raw feedback

For a feature, create an Issue with a specific title and this short body. It
will become `READY_TO_PLAN`, not a delivery Ticket:

```markdown
## Spec
Describe the behavior to implement, where it belongs, and any important
constraints.

## Acceptance criteria
- State an observable result that proves the behavior works.
- State an important boundary or failure case.

```

For a bug, add the `bug` label and provide reproducible evidence:

```markdown
## Spec
Submitting an empty ingredient crashes recipe search.

## Affected revision
`0123456789abcdef0123456789abcdef01234567`

## Environment
Python 3.12, macOS 15, clean checkout

## Reproduction command
`python -m pytest tests/test_search.py -q`

## Reproduction result
AssertionError: expected validation message, process exited 1

## Acceptance criteria
- Empty input shows a validation message.
- Search does not start for empty input.

## File ownership
- src/search.py
- tests/test_search.py
```

The listener records the current default-branch revision as the latest revision
checked. It treats the reproduction text as reviewed evidence and never runs an
attached script or code from feedback. Use only a command and bounded output a
person has already inspected. Collection errors, missing dependencies, login
failures, and unrelated test failures are not causal product reproductions.

Optional dependencies use issue numbers:

```markdown
## Dependencies
Depends-on: #12, #13
```

Avoid adding an `agent:` line unless the named adapter is configured. If an
issue requests an unknown adapter, Factory records an intake warning and uses
the configured default implementation adapter.

## Step 3: Review the proposal

Return to **Deliver → Tickets**. After the next poll:

1. The **Admitted** count increases.
2. Factory records a sanitized intake case and proposed classification.
3. The Ticket Summary shows the rationale and missing evidence.
4. The proposal remains unable to dispatch work.

Use the classification deliberately:

- `READY_TO_PLAN`: open **Plan → Requirements** and use the request as a PRD.
- `READY_TO_IMPLEMENT`: review the revisions, environment, causal reproduction,
  acceptance criteria, and ownership. Enter the human approval reason, then
  select **Approve intake for triage**.
- `NEEDS_INFORMATION`: ask for the named missing evidence. Do not dispatch.
- `WAIT`: fix the collection or environment boundary, or wait for the external
  dependency. Do not pretend it is a product reproduction.

Factory planning, monitoring, and previously governed intake Issues are ignored
rather than admitted again.

## Step 4: Follow the normal delivery controls

Human intake approval does not bypass the Factory Profile:

1. Independent QA writes acceptance tests when the profile requires QA.
2. If **Test approval** is required, open the ticket at **QA Review**, inspect
   the test evidence, and approve or request changes.
3. Implementation runs in an isolated ticket worktree.
4. Verification gates and code review inspect the exact candidate revision.
5. In profiles with human merge authority, open **In Review**, inspect the
   evidence and pull request, then merge the approved revision.
6. Keep the listener running. After admitted tickets are **Done**, it waits for
   the next new issue instead of exiting.

Use the **Autonomous Demo** profile only when the workshop explicitly intends to
delegate merge authority. Other profiles retain their normal human decisions.

## Step 5: Correct an intake proposal

An incomplete bug proposal remains `NEEDS_INFORMATION` or `WAIT`.

1. Open the blocked ticket in the Control Center.
2. On **Summary**, read **Raw feedback intake** and its missing evidence.
3. Add the evidence to the GitHub Issue, or use the CLI correction command to
   record a human classification and reason.
4. Wait for the next listener poll to create a new evidence proposal.
5. Approve intake only when a causal bug is truly ready for triage.

Corrections preserve the original classification in
`.factory/intake/cases.jsonl`. The long-running listener does not need to stop.

You can instead edit the issue directly on GitHub. Preserve the hidden Factory
comments when possible. The listener detects the edit on its next poll and
restores required intake metadata before re-triaging.

## Step 6: Stop and resume

To stop listening, select **Stop operation** in the Control Center.

To resume:

1. Return to **Deliver → Tickets**.
2. Confirm **Live** mode.
3. Open **Run options**.
4. Select **Listen for new issues**.

The listener resumes from `.factory/issue-listener.json`. It does not create a
new baseline, so issues opened after the previous poll can still be admitted.
The listener state is included in Factory recovery checkpoints.

If local listener state is deliberately deleted, the next start creates a new
baseline from all currently open issues. Use **Recover latest state** before
starting again when the listener state was removed accidentally.

## CLI equivalent

The Control Center action runs:

```sh
./factory/factory run --listen
```

The same constraints apply from the CLI:

- listening is Live-only;
- `--listen` cannot be combined with `--dry-run`;
- the first start creates the no-backlog baseline; and
- `Ctrl+C` stops the listener.

To evaluate or correct a bounded request without the listener:

```sh
./factory/factory intake evaluate request.json --repo /path/to/product
./factory/factory intake correct CASE_ID correction.json --repo /path/to/product
./factory/factory approve-intake ISSUE --case CASE_ID \
  --reason "Reproduction, criteria, and ownership reviewed" \
  --repo /path/to/product --yes
```

The approval command applies only to a `READY_TO_IMPLEMENT` proposal and records
the named human reason. It does not waive QA, gates, Code Review, or merge
policy.

## Troubleshooting

### Listen for new issues is disabled

Set the **Deliver → Tickets** run mode to **Live**. Repository intake is unavailable in
Rehearsal.

### A new issue did not appear

Confirm that:

1. the issue was opened after the listener reached **Listening**;
2. the issue is open in the connected repository;
3. the listener operation is still running; and
4. the status is not **Listening with an error**.

An issue included in the first baseline remains excluded. Create a new issue
after listening starts instead of editing the listener state.

### The listener is degraded

Open the operation output and read the first GitHub error. Run **Full
preflight** again and correct authentication, repository access, Project scope,
or connectivity. The listener keeps running and retries on the next poll.

### The intake proposal needs information

Open its Summary. The Control Center names the missing revision, environment,
reproduction, acceptance, or ownership evidence. Update the Issue; do not keep
retrying the coding agent because it has not been dispatched.

### All tickets are Done but the operation still runs

This is expected. Listener mode waits for future issues. Use **Stop operation**
when you no longer want repository intake.

### A Factory-created issue was ignored

This is expected. Durable markers prevent planning tickets, monitor findings,
and prior intake issues from recursively creating more Factory work.
