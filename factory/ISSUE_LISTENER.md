# Repository Issue Listener

This guide shows how to keep a Live Factory running, admit new user-created
GitHub issues, triage them, and deliver valid requests through the normal
Factory controls.

## Before you start

Use a repository that is already connected to the Control Center. Complete the
normal **Setup** checks first:

1. Start the Control Center from the factory checkout:

   ```sh
   ./factory/factory control-center
   ```

2. Open <http://127.0.0.1:5050/>.
3. Open **Setup → Connection** and select **Live**.
4. Enter the GitHub repository URL and save the configuration.
5. Select the required Factory Profile and role adapters.
6. Create or review the Project Contract and Factory Charter.
7. Approve the exact Charter.
8. Commit and push the repository setup.
9. Run the full preflight and confirm that it has no failures.

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
- **Admitted**: later user-created issues accepted into Factory intake; and
- **Ignored**: later Factory-managed issues excluded from intake.

Do not create the demonstration issue until the status is **Listening**. An
issue opened before the baseline is recorded is intentionally treated as old
backlog.

## Step 2: Open a valid GitHub issue

In the connected GitHub repository, create an issue after the listener starts.
Use a specific title and this body:

```markdown
## Spec
Describe the behavior to implement, where it belongs, and any important
constraints.

## Acceptance criteria
- State an observable result that proves the behavior works.
- State an important boundary or failure case.

## File ownership
- src/path-owned-by-this-issue
- tests/path-owned-by-this-issue
```

`## Spec` and at least one bulleted item under `## Acceptance criteria` are
required. `## File ownership` is recommended because it gives the worker a
clear change boundary.

Optional dependencies use issue numbers:

```markdown
## Dependencies
Depends-on: #12, #13
```

Avoid adding an `agent:` line unless the named adapter is configured. If an
issue requests an unknown adapter, Factory records an intake warning and uses
the configured default implementation adapter.

## Step 3: Watch admission and triage

Return to **Deliver → Tickets**. After the next poll:

1. The **Admitted** count increases.
2. Factory adds the issue to its GitHub Project.
3. Factory adds its hidden intake and governance markers.
4. The ticket enters the delivery board.

A complete dependency-free issue moves to **Ready** and follows the selected
profile. An issue with unfinished dependencies remains in **Backlog**. Factory
planning, monitoring, and previously governed intake issues are ignored rather
than admitted again.

## Step 4: Follow the normal delivery controls

Admission does not bypass the Factory Profile:

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

## Step 5: Recover an incomplete issue

An issue without the required headings or a bulleted acceptance criterion is
admitted but moves to **Blocked**.

1. Open the blocked ticket in the Control Center.
2. On **Summary**, read **Why it stopped**.
3. Review **Proposed recovery**.
4. Inspect the proposed Ticket body.
5. Accept the proposal or edit it to accurately describe the intended result.
6. Enter a retry reason explaining why the correction is now implementable.
7. Select **Save ticket and retry**.

The correction runs as a companion action, so the long-running listener does
not need to stop. Factory updates the GitHub issue, reloads it, restores its
governance markers, and re-runs deterministic triage.

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

### The ticket is blocked

Open its Summary. The Control Center shows the cause and proposed recovery.
Missing `## Spec` or `## Acceptance criteria` content must be corrected before
implementation can start.

### All tickets are Done but the operation still runs

This is expected. Listener mode waits for future issues. Use **Stop operation**
when you no longer want repository intake.

### A Factory-created issue was ignored

This is expected. Durable markers prevent planning tickets, monitor findings,
and prior intake issues from recursively creating more Factory work.
