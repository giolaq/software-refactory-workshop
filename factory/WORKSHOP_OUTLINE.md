# Software (re)-Factory workshop

Runtime reference: workshop-v1.2.1. The organizer supplies the tested session
release tag and matching guide URL; branch previews are not published releases.

## Attendee invitation

In three hours, you will work through an AI software factory's transformation of
Pocket Cinema, a film-browsing app, into TableStory, a recipe product. You will review the plan,
follow GitHub tickets, inspect acceptance tests and code reviews, and decide what
to merge in your own repository. You will also create a pilot proposal for your
team. You do not need prior AI software-factory experience.

The goal is the complete product transformation, not a small film-search change.
Follow one journey through the work: find a recipe by ingredient, read its cooking
steps, and save it to My Cookbook. This example does not replace the full PRD.
Live execution time varies. If work is unfinished, keep its actual state and
resume point; use labeled prepared evidence to practice the remaining decisions.

The website contains the step-by-step instructions. The facilitator explains the
concepts with slides and worked examples. Use Standard Live for the session.
Rehearsal is a clearly labeled simulated fallback, not a second required run.

### Install before attending

Bring a laptop with:

- macOS, Linux, or Windows with WSL2. On Windows, use the WSL terminal and keep
  the checkout in its Linux filesystem.
- Python 3.11 or later with venv.
- Node.js 22.13 or later.
- Git, with your commit name and email configured.
- GitHub CLI, a modern browser, and ports 5000 and 5050 available.
- One installed, signed-in coding CLI: Claude, Codex, Cursor, or a compatible
  adapter configured before the session.
- Network access to GitHub, package registries, and your selected provider.

You do not need AWS, Docker, or an OpenAI API key for the authenticated CLI path.
Check your provider subscription, usage allowance, and data policy. Live agent
work can consume paid usage; the workshop cannot guarantee a fixed token cost.

### GitHub access

Sign in with GitHub CLI. Confirm you can create a private disposable repository,
issues, branches, pull requests, and a GitHub Project. Authorize the project
scope. Every attendee owns a repository; do not use the facilitator's repository.

### Check readiness

Run these before the session:

```sh
python3 --version
python3 -m venv --help
node --version
git --version
git config --get user.name
git config --get user.email
gh --version
gh auth status
gh auth refresh -s project
```

Then run only the check for your selected agent:

- Claude: `claude auth status --text`.
- Codex: `codex login status`.
- Cursor: `agent status`.
- Custom adapter: follow its registered readiness command.

Follow the session guide's Setup steps using the release tag supplied by the
organizer. Confirm the selected repository, resolve required failures, and open
the Pocket Cinema baseline before class. Ask for help with the first failed
command, its output, operating system, and selected CLI. Never send a password
or access token.

Support targets and actually completed checks are listed in
[Workshop validation](WORKSHOP_VALIDATION.md). WSL and individual live providers
need an explicit fresh-environment check; do not confuse support intent with
completed verification.

## Session at a glance

1. Inspect whether a candidate change is safe to merge.
2. Connect your repository and approve its contract.
3. Turn [the recipe-product PRD](../recipe-app-prd.md) into a reviewed transformation plan.
4. Publish the tickets to your GitHub Project and inspect their dependencies.
5. Review QA's test code and its baseline failure.
6. Run implementation and checks; inspect review and merge the accepted revision.
7. Verify the changed behavior and export run evidence.
8. Complete a [personal pilot worksheet](WORKSHOP_PILOT.md).

See the [timed plan](WORKSHOP_PLAN_3_HOURS.md) for the full 180-minute agenda and
answer keys. The [recipe transformation](../recipe-app-prd.md) is the main exercise.
Cloud deployment and custom adapters are optional follow-up labs.

## Completion

Complete means the full approved transformation is merged and integrated
acceptance checks pass. One completed slice is progress, not a finished TableStory.
A healthy Live run can continue past a teaching checkpoint. If it is unfinished,
retain its resume point and use prepared evidence for the decision exercise.
Do not disable QA, mark unmerged
tickets Done, or claim a mock run completed a Live change.

Learning success is separate: explain why you accepted or rejected a requirement,
test, or candidate revision, and leave with a pilot owner, evidence strategy,
and a measurable stop/go criterion. The workshop does not require adoption of
this factory or claim that more agents always improve delivery.
