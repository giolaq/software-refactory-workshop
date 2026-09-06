# Codex Live workshop: attendee walkthrough

Status: **Live delivery complete. Final validation and attendee assessment recorded below.**

## Result at a glance

The full Pocket Cinema → TableStory transformation completed with Codex in all
agent roles. Eight PRD-derived tickets are merged, and all eight GitHub Project
items show Done. No release scope was cut to a search-only example. Final product
main is `5e84b3877eb99652b11fea2d13be996ff4f108cb`.

- Final merged checkout: 298 Python and 105 JavaScript tests pass, zero skips.
- Factory fixes: 469 Python regression tests pass. Five Control Center browser
  scenarios pass; website build and 14 website tests pass.
- Real browser checks cover mobile ingredient search/save, refreshed TV cookbook,
  keyboard navigation, error recovery, contrast, overflow and all-recipe detail scrolling.
- Exported evidence contains eight Done tickets, 126 verified artifact hashes,
  and no missing evidence reported by the exporter's structural checks.
- Factory source fixes are uncommitted on `codex/live-attendee-validation`.
  Product PR merges are in the disposable private repository, not Factory main.

**Attendee verdict:** worthwhile for learning delivery control, but the starting
revision was not ready for an unassisted novice. This debugging run is not proof
that a new participant can finish the exercise smoothly in three hours. Run one
clean human pilot on the repaired version before making that promise.

## Attendee perspective

The valuable lesson is how to demand evidence and recover a delivery process,
not how to start several agents. This Live run has already demonstrated three
important distinctions:

- A test process failing is not necessarily valid RED evidence. An assertion
  about missing behavior is useful; a missing runner or import error is not.
- An agent approving a change does not prove that the resulting screen works.
  Actual mobile and TV checks found evidence that static tests could not supply.
- A merge recommendation is not merge authority. I inspected the exact candidate
  and retained the human merge gate throughout this run.

The starting revision was not ready for an unassisted novice Live workshop.
Recovery, handoffs, and status reporting needed source repairs. The fixes below
have regression coverage and were exercised as the run continued, but a second
clean human pilot is still needed before promising a smooth three-hour session.

The main exercise remains the complete Pocket Cinema to TableStory product
transformation. All eight tickets are merged, including remote navigation and
final release evidence. The chronological checkpoints below explain what failed
and how it was repaired; their intermediate counts are not the final outcome.

For the facilitator, prepare the repository and authenticated CLI before the
session, make approval checkpoints explicit, and reserve time for one deliberate
recovery exercise. Keep a known-complete reference available for the closing
comparison. This preserves the transformation story without implying that every
live provider invocation will finish on a fixed classroom schedule.

## Run record

- Exercise: complete Pocket Cinema → TableStory transformation from `recipe-app-prd.md`.
- Starting Factory revision: `8a58df58b414ffe3aefb50e921fe18885732313e` from main, not a new release tag.
- Fix branch: `codex/live-attendee-validation`.
- Private product repository: <https://github.com/giolaq/factory-tablestory-live-20260906>.
- Control checkout: `/tmp/factory-live-20260906.ZiWX9P/software-refactory-control`.
- Product checkout: `.factory/repositories/giolaq/factory-tablestory-live-20260906` inside that control checkout.
- Baseline product revision: `486bb08bc05f0d15ced56ddb532409caba693359`.
- Approved setup revision: `f2e91dcc8e0f4201dfcd71d9075c9cb3e2e50e17`.
- Plan ID: `eea40ab19dfe` (derived from the PRD; not globally unique across repositories).
- GitHub Project: [TableStory, #17](https://github.com/users/giolaq/projects/17).
- Profile: Standard; initially one concurrent ticket, then two after cookbook merge; QA approval and human merge required.
- All selected roles use Codex. Current CLI: 0.153.4, authenticated with ChatGPT.
- Product Review reported model `gpt-6-astra`; no model override was requested.
- Platform: macOS; Python 3.14.7; Node.js 23.11.0; Chromium browser automation.

This is an agent-operated attendee simulation. I follow the guide and Control
Center, inspect the artifacts, and make the review decisions for this disposable
run. Repairs and diagnostic work are recorded separately from ordinary attendee
steps. This is not evidence that a new human can finish unassisted.

## Setup observations

The documented `codex login status` command reached a legacy CLI (0.1.2504172351)
and asked for `OPENAI_API_KEY`. A current authenticated CLI already existed in
the ChatGPT application bundle. The Factory already supports discovery and
`FACTORY_CODEX_BIN`; the attendee website did not explain that recovery.

I used the documented executable override in the Control Center process only.
No global CLI installation, credentials, or shell configuration was changed.
Official references: [Codex CLI](https://learn.chatgpt.com/docs/codex/cli) and
[authentication](https://learn.chatgpt.com/docs/auth).

The setup script also told a Live attendee to choose Rehearsal. That message is
now explicit about both paths. Live connection created the managed checkout and
published only the guided starter product and its governance, not the Factory
or workshop website. Automatic setup passed 30 checks with zero failures.
Warnings concerned an optional review identity, an unused Cursor installation,
and occupied port 5000. Start app selected port 5001 successfully.

## Planning observations

Product Review translated the full PRD into 28 traceable requirements and five
journeys. I checked them against the original requirements and exclusions before
approving. Architecture added explicit contracts for authoritative search,
confirmed saved state, recipe APIs, empty rails, remote controls, and integrated
verification. It correctly distinguished pure navigation tests from browser
proof of visibility, scrolling, and contrast.

The screen initially labelled an active expert Pending and displayed an artifact
access error before any artifact existed. Codex planning also buffered all output
until completion. Repairs now save the running stage before invocation, avoid
requesting an empty artifact path, and stream Codex session, command, completion,
and usage events. These changes were exercised during the real Architecture run.

Switching sections retained the old scroll position: after reading a long
artifact, the next section opened underneath the sticky header. A browser check
observed scroll position 313 before and after navigation. Switching sections now
returns to the top; the retest returned 0.

The completed package contains eight tickets in six dependency waves. Recipe
discovery precedes cookbook behavior. Styling, live search, and TV rails can then
proceed independently, followed by remote browse, remote detail, and integrated
release evidence. All 28 requirements are assigned; the product transformation
has not been reduced to a search feature. I reviewed the proposed signatures,
contracts, file ownership, and acceptance criteria before approving publication.
GitHub issues #1–#8 were created from this approved plan, not seeded examples.

Planning started at 17:48:27 UTC and reached alignment review at 18:19:03 UTC:
30 minutes 36 seconds, including the product approval pause. Program Design alone
took approximately 16 minutes and logged two model-catalog refresh timeouts.
It nevertheless returned a valid artifact and the next expert ran. These warnings
are not evidence of a failed stage. The attendee must see observable progress
without being encouraged to restart healthy work.

The design is thorough but demanding: 14 proposed modules, 32 functions, and a
first slice estimated at 900–1,150 changed lines. Those are proposals and estimates,
not measured implementation. For a three-hour session, the facilitator should
budget review time explicitly and avoid promising that every participant will
finish all six waves.

## Delivery blockers and repairs so far

The first independent QA invocation could not find the approved contract
definitions. Its prompt contained IDs and phrases such as “exact approved fields,”
but the planning files live in ignored runtime storage outside the isolated
worktree. Codex asked where those definitions were instead of inventing tests.
This is a Factory handoff defect, not an attendee PRD error.

Delivery prompts now embed the approved Product Review, System Architecture, and
Program Design definitions and their revision hashes. QA, implementation,
verification roles, and code review use the same handoff. Missing or changed
definition artifacts block dispatch with recovery instructions. The first version
of this repair also checked the slice file; Live validation caught that publication
legitimately adds metadata to it. The corrected implementation verifies the
definition artifacts only; existing Ticket revision checks remain in place.

I stopped the stalled command using Stop operation, kept the plan and issues,
and submitted a reasoned Ticket retry after repairing the handoff. One restart
also encountered a GitHub connection reset; a read-only authentication check
succeeded. Recovery guidance now explains retrying the existing operation rather
than resetting the repository or recreating tickets. A stopped operation no longer
labels the previously recorded QA phase as actively running.

A subsequent `gh auth status` failure was reduced to “not authenticated” even
though the next direct check confirmed the existing session. The exact failed
probe diagnostic was lost, so its cause cannot be established retrospectively.
Both GitHub connection paths now preserve a credential-redacted diagnostic. The
Control Center routes GitHub authentication problems to GitHub checks, not the
coding-agent login. No credentials were replaced during this repair.

The ticket drawer also retained its old “Blocked” heading after retry had moved
the ticket to Ready. Its heading now refreshes with the ticket state. Text entered
in the retry field was checked separately and survived polling; no additional
form-persistence change was needed.

The source regression suite passed 452 tests after these repairs. This is Factory
regression evidence, not proof that the TableStory product is complete.

### The first acceptance-test review

The regenerated QA prompt contained all three approved definition artifacts and
their hashes. Codex then produced tests for the actual recipe collection, public
APIs, validation, rendering, and mode handling. It explicitly excluded later
cookbook and TV behavior in its handoff.

However, the draft asserted that cookbook routes and browser scripts were absent.
Those are temporary intermediate states, not lasting contracts: subsequent
approved tickets add those capabilities. Protecting these assertions would make
the later work fail even when implemented correctly. I rejected that direction
and requested regeneration with recorded feedback; I did not edit protected tests
to make a candidate pass. The QA prompt now explicitly distinguishes lasting
contracts from temporary states.

Automatic RED validation also exposed an evidence-processing defect. The
orchestrator classified only the final 3,000 output characters. A 95-failure run
lost its assertion diagnostics in the summary. Regression tests reproduced both
directions of the defect: a valid assertion could be missed, and an earlier
infrastructure failure could be hidden by a later assertion. Focused RED/GREEN
and negative-proof classification now inspect the complete output before keeping
a bounded beginning-and-end excerpt for display. Mixed execution and assertion
failures still do not count as RED.

The original QA set also intentionally triggered a server exception while testing
a safe 500 response. Its captured application log made the text classifier
conservatively reject the run. The revision request calls for clear behavior
evidence without mixing expected application logs into runner errors. This is
not permission to suppress actual test-runner failures.

On automatic retry, QA added another file instead of repairing its rejected
draft because the prompt forbade all existing-file edits. It now lists its own
unaccepted drafts as repairable; accepted QA and repository tests remain
protected. The Control Center now routes rejected RED evidence to its existing
QA-regeneration recovery action. That action records the reason and rebuilds
from the base; it does not bypass RED validation or human approval.

QA revision 2 passed the factory's RED check at commit
`10f2fc37d659b4aa1a4d5a2e13d051ce24b9ff6d`. I independently ran the identical
focused command and observed 79 assertion failures in 0.57 seconds, classified
as `behavior_assertion`. For example, `/api/recipes` returned 404 where the
approved contract requires 200. The final 419-line test file allows future local
scripts and cookbook routes. Its safe-500 test captures only Flask's expected
exception logging and still checks status, JSON/HTML representation, and absence
of private diagnostics. I reviewed this revision and approved it through the
Control Center. Implementation has not been counted as complete.

### First candidate review and restart

The first implementation candidate was `720dec44d00b94dcdc6c5447bb03737cb9326dc4`
in [PR #9](https://github.com/giolaq/factory-tablestory-live-20260906/pull/9).
All three configured gates passed (two required and one optional). The implementation changed 825 lines; the
separately protected acceptance test accounted for another 419. I inspected the
migration of the original movie assertions to recipe assertions and independently
ran all 119 Python tests successfully. This is first-slice evidence, not complete
product acceptance.

The Code Review role approved the exact candidate. GitHub recorded the decision
as a labelled Factory comment because the authenticated account also authored
the PR. The reviewer attempted a Python rerun using the wrong interpreter and
reported that pytest was unavailable. Gate receipts now record their resolved
commands, and the review prompt includes them so an independent rerun uses the
configured environment rather than an arbitrary Python on PATH.

The supervisor then blocked the candidate solely because human merge approval
had not yet been supplied. Its prompt conflated readiness with execution
authority. A regression check reproduced the missing distinction. The revised
prompt makes `MERGE` a readiness recommendation: the orchestrator still enforces
the human gate. No supervisor decision was overwritten.

Manual content review found a separate issue: Berry Overnight Oats claimed ten
minutes but required six hours of refrigeration. I requested a genuinely quick
recipe through the normal reasoned retry, preserving the approved schema and
protected QA. This demonstrates why passing structural tests does not replace
editorial review.

A new browser session exposed a mode mismatch. The sidebar read Live from the
plan, while buttons used the browser's default Rehearsal selection. The engine
rejected the command without mixing evidence. A browser reproduction showed
`label=live`, `mode=rehearsal`, `recorded=github`. Initial rendering now restores
the recorded run mode, and the sidebar uses the same selection as action
payloads. The Live retest showed all three agreeing. No reset was needed.

The corrected candidate is `25863d98d393a2696866ac657c88b144b491c8c9`. The Factory
recorded GREEN against that revision. I independently reran 119 Python tests and
two Node tests, all passing, and confirmed the protected test's SHA-256 remained
`61213ac6f3351d9098234555a8cbcf143ec1656fb95c3bbb27cb97105470f9c6`.
The Node tests still exercise the old domain at this intermediate slice; their
PASS is not evidence of completed TableStory browser behavior. Independent code
review approved the corrected candidate. Supervisor receipt `supervisor-merge-8`
recommended readiness while retaining human authority. After inspecting the
evidence, I used **Merge exact revision** in the Control Center. GitHub confirms
PR #9 merged at `2026-09-06T02:31:36Z`, with candidate head unchanged and merge
commit `66e45514d8c90364fafaefb91e95a3afb7dbf859`. Ticket #1 is Done; seven
transformation tickets remain. The review role's independent pytest rerun hit
read-only sandbox temporary-file restrictions; my separate configured-environment
rerun supplied additional evidence without changing its sandbox policy.

Factory regression verification after these fixes: 454 Python tests passed in
68.943 seconds. Browser checks passed fresh setup, product planning, running
expert, QA review, and completion fixtures, including the new mode-restoration
check. These deterministic fixtures are not substitutes for the Live run.

### Evidence retention and delivery reliability

Manual retry resets the attempt counter and reuses live prompt, log, and review
filenames. An older receipt could therefore open evidence from a newer attempt.
A regression test reproduced the first receipt reading the second candidate's
log. Receipt writing now preserves content-addressed copies of referenced runtime
artifacts. Source files, missing references, and paths outside the repository's
runtime evidence roots are not copied. This cannot reconstruct already-overwritten
logs from this run; recorded Git revisions and separately embedded gate evidence
remain available. The updated source suite passed 456 tests. After restart,
supervisor receipts 10 and 11 contain content-addressed prompt and log copies,
confirming the repair is active in the Live scheduler.

Ticket #2 QA also encountered repeated Codex connection retries. At observation,
the CLI process and its TLS connection remained live. I did not restart it merely
because output paused. Provider waiting time and recovery must be measured
separately from attendee work and Factory repair time.

QA produced separate Python and Node acceptance files, which the configured
file policy permits and the cookbook slice needs. The focused runner rejected
the mixed set. Its automatic retry began moving the Node checks into Python to
work around that restriction. I stopped that retry to repair the Factory.
Mixed sets now run both language groups and classify each result separately.
An assertion in one runner cannot hide a collection, execution, or non-assertion
failure in another. Regression tests cover RED, GREEN, and an independently
broken second runner. The QA prompt explicitly permits mixed sets without wrappers.

Restart also misclassified this recorded command-construction failure as an
old-format run because it had a QA commit but no focused command. The guard now
allows a recorded RED NOT PROVED failure to recover. It still rejects a claim of
RED PROVED without the corresponding command. No tests were approved as a result
of either repair; valid RED and a separate review remain required.

I independently checked QA commit `7cef35f4e79321a2f77b41389001aaab46fda6b7`
in a temporary detached worktree. The repaired runner executed both original
suites: 24 Python assertion failures and seven Node assertion failures. It
returned exit 1 with both groups classified `behavior_assertion`. The temporary
worktree was removed after verification; the source QA commit and diagnostic log
remain. I recorded the repair and this commit in the Control Center retry reason
so QA can reuse and revalidate its drafts rather than discard browser coverage.
The latest full regression run passed 458 tests. A subsequent targeted regression
also verifies that Node's compact `ℹ skipped 1` output is rejected, like TAP's
`# skipped 1`, rather than treated as a passing runner.

The Live retry restored the same two test blobs and produced QA commit
`0b72800190d68c0ff7b77786e928b43592f68b21`. The Factory executed the mixed command,
recorded RED PROVED, and moved the ticket to QA Review. I compared both file hashes
with the independently reviewed draft, reviewed the complete 247-line Python and
282-line Node files, and selected **Approve tests**. The API and controller tests
cover the six ticket criteria without freezing future search or TV capabilities.
Their lightweight DOM adapters do not prove real browser focus or layout; the
ticket and final product walkthrough still require that evidence.
The scheduler consumed the approval and supervisor receipt 12 dispatched
implementation at `2026-09-06T03:02:31Z`, with both test suites protected. The
latest full source regression run, including the compact Node skip check, passed
458 tests in 76.440 seconds.

### Cookbook candidate validation

Candidate `d47037fc1ea79e3ec1fd07dd36975f18591b1c44` in
[PR #10](https://github.com/giolaq/factory-tablestory-live-20260906/pull/10)
passed focused GREEN and all three configured gates. Implementation-owned churn
was 371 lines, with 529 protected QA lines counted separately. I inspected the
replacement of the obsolete JavaScript tests with cookbook regression tests and
independently ran 144 Python and 12 Node tests, all passing.

For pre-merge browser evidence, I launched the candidate worktree with Flask on
an unused local port, 5077. The Control Center's Run app view previews the managed
checkout, not an arbitrary PR candidate, so this required an extra terminal step.
At 375×812, the browser loaded all 12 recipes without application errors. Saving
Quick Berry Porridge changed its label and announcement; opening detail reflected
saved membership; removal returned an empty cookbook; the back link preserved
mobile mode. With browser networking deliberately offline, a save retained false
`aria-pressed`, released pending state, kept button focus, and announced failure.
After networking was restored, retry succeeded. I closed the test browser and
stopped only the owned preview server. The old visual theme and disabled search
remain expected intermediate behavior, assigned to later tickets.

Code review approved the same candidate and the supervisor recommended human
merge. GitHub's PR head matched the approved revision. I selected **Merge exact
revision** after the independent browser and test review.
GitHub confirms merge commit `6701dfc29ae1e5c10a255e852184ffbb07395e4a` at
`2026-09-06T03:11:12Z`, with the candidate head unchanged. Tickets #3, #4, and #5
became Ready. I changed parallelism from one to two using Connection's advanced
settings, leaving every selected role on Codex and retaining human QA and merge
gates, then restarted for the independent styling/search/rails wave.

The review prompt previously omitted the already-recorded QA approval and test
revision, leading the reviewer to report that evidence as unavailable. It now
supplies the approval flag, QA commit, protected hashes, and revision-bound RED
and GREEN claims. The prompt explicitly separates QA approval from human review
of implementation changes and permission to merge. This repair does not change
the read-only review sandbox or pretend the reviewer independently reran pytest.

The next supervisor checkpoint dispatched only TV rails, reserving a slot for an
earlier styling dispatch. That worker had stopped and current state marked its
ticket Ready. The prompt now explains that dispatch checkpoints occur between
worker waves, the parallel limit is available capacity for the next wave, and
historical receipts do not prove a worker is running. A prompt regression
reproduced the missing guidance. The repair will load at the next safe review
checkpoint; the active QA worker is not interrupted for this change.
After the safe restart, `supervisor-17` dispatched #3 and #5 together, explicitly
treating current Ready states as authoritative and deferring #4 only for the
two-worker limit. I confirmed two live Codex processes: styling QA and TV-rails
implementation. This verifies the repaired decision on the actual Live run,
not only the prompt regression. The latest full source suite passed 458 tests
in 78.918 seconds.

### TV-rails QA review

QA produced `4b908cd2c16ffe8fcf8071185207b7610d488be6`, containing a 342-line
Python acceptance file. I reviewed the complete file and independently reran its
focused command: 31 assertion failures and 34 passes. It covers exact rail
identities, source ordering, 30-minute boundary, explicit dietary tags, mode
precedence, one cookbook snapshot per response, startup validation, and safe
public routes. It explicitly defers visual acceptance until styling is integrated.
I selected **Approve tests**, then restarted the stopped scheduler to consume the
approval and load the dispatch-state repair. No protected test was manually edited.

### Styling QA and scoped merge evidence

Styling QA produced `a63101c0ff074035501f4bb631a6fcac6d0cf9e4`. I read the
complete acceptance file and independently reproduced 13 assertion failures and
5 passes. These are scoped CSS/markup checks, not a rendering engine: the file
explicitly leaves computed contrast, viewport overflow, and remote scrolling for
browser validation. I approved this checkpoint through the Control Center.

TV rails implementation `594ffd6eca7e6a39017162c801e8378d2f8443e0` passed
215 Python tests on an independent rerun. Its protected acceptance file remained
unchanged. I inspected the complete 164-line implementation diff, including
additive existing-test changes. Code review approved PR #11, but the supervisor
blocked it for outstanding styling integration owned by another ticket.

The merge checkpoint supplied the title and reports but omitted the ticket's
specification and dependencies. I added that context and guidance to evaluate
this scoped handoff without inventing future dependencies. Missing acceptance
within the current ticket still blocks; downstream visual evidence remains a
release obligation. A failing prompt regression reproduced the omission, and
all 10 supervisor tests passed after the repair. Live recovery remains to be
verified at the next safe scheduler restart.

Search QA produced `483541a223e872f192401dab300b8704345e8e74`. I read both
protected files and independently reran their recorded mixed-runner command:
9 existing API checks passed and 18 JavaScript behavior assertions failed.
Coverage includes out-of-order responses, stale failures, clearing, safe failure
recovery, authoritative API IDs, duplicated rail cards, and input focus. This
also exercised the mixed-runner repair on a second real ticket. I approved the
tests through the UI. The website build and all 14 website tests passed again.

Stopping at a review checkpoint raced the next styling dispatch. Recovery then
cleared already-approved QA despite a clean worktree still at its exact QA
commit. The new recovery guard preserves that narrow case only when scope is
unchanged; dirty worktrees, changed revisions, unapproved QA, and interrupted QA
generation retain the existing conservative path. Its regression covers all
five cases. The already-triggered Live regeneration reproduced the identical
protected test file at `f6f578ef91d39de665b4c28a05fca51b884d3a75`; the extra
invocation is recovery overhead, not new product work.

The rails retry also revealed a no-change loop. The implementation role retained
the approved exact candidate as instructed, but the Factory rejected it for not
creating another commit. An unchanged head with recorded QA approval and an
APPROVE review can now return through verification and fresh review without a
cosmetic commit. New unimplemented work and requested-change reviews do not
qualify. This does not skip gates or authorize merge. Live recovery verification
is still pending.

Search candidate `26c9197bd5c44ebfacb4eea0e1e68110871a3dc9` passed an independent
153 Python and 35 Node tests. At 375×812, entering OAT MILK displayed only
BERRY_OATS, matching the API, announced one recipe, and retained input focus.
Its detail link opened the correct recipe. Offline search retained the old
card/count and announced unchanged results. Restoring networking allowed a
zero-result query; clearing then restored all 12 cards. No uncaught JavaScript
errors were reported. I stopped the owned candidate preview after this check.

The supervisor correctly requested this browser evidence, which had not yet
been supplied during automated review. It also requested diff-budget evidence
that already existed in state (195 implementation lines, 292 protected QA
lines, within the 1,200-line limit) but was absent from its input. The merge
handoff now includes the recorded candidate-bound measurement and operator
retry feedback, explicitly distinguishing that feedback from approval. The
prompt regression fails before this change and all 10 supervisor tests pass
after it. Operator browser evidence is recorded in the disposable run's
`.factory/reviews/attendee-ticket-4.md` for candidate-specific re-review.

The latest complete source suite passed 460 tests in 77.915 seconds before the
final diff-budget prompt addition; its focused supervisor suite passed afterward.

On the next Live restart, search retained exact head
`26c9197bd5c44ebfacb4eea0e1e68110871a3dc9`, passed verification again, and
entered fresh code review without an implementation commit. This verifies the
unchanged-approved-candidate repair in the actual workflow, not just a unit test.

The supervisor then resolved search's evidence blockers. I verified GitHub's
exact head and selected **Merge exact revision**. PR #12 merged at
`2026-09-06T05:08:47Z` as `13f2e4dd92f3c8ad9e8e2628eed6811a7a34a0f2`.
This is the third completed ticket, after recipe core and cookbook.

Styling candidate `863d2751d003674296f715a561dd194daeda643c` passed 162 Python
tests independently. Browser checks measured 375px document width at a 375px
viewport on browse and detail, including synthetic long text. Saving retained
focus and supplied both changed text and a checkmark. At 1920×1080, detail
content scrolled independently to its final step while actions stayed visible.
Computed contrast was 14.8232:1 charcoal/cream, 5.8068:1 herb/cream, and 8.2657:1
charcoal/gold. Tomato/cream was 4.499942:1, not a normal-text 4.5:1 pass; the
implementation uses 19px bold mobile and 24px bold TV actions, meeting the
large-text threshold. No external resource origins or uncaught JS errors were
observed. These scoped checks and screenshots are recorded in
`.factory/reviews/attendee-ticket-3.md`; integrated TV remote behavior is still
assigned to later tickets. I submitted the evidence through a reasoned retry
after the supervisor correctly requested rendered proof.

Rails PR #11 also recovered without changing candidate
`594ffd6eca7e6a39017162c801e8378d2f8443e0`, received fresh approval and a scoped
MERGE recommendation, and passed exact-head human review. GitHub records merge
`8f59d9cd03f2d128f7e82f658bf5f992c32adf1b` at `2026-09-06T05:14:52Z`.

Two additional recovery issues appeared while supplying browser evidence:

- A retry CLI wrote its old full state snapshot after another ticket reached
  review. The board briefly regressed that unrelated ticket to Verifying until
  the scheduler rewrote current state. Retry persistence now reloads current
  state and updates only its ticket under a shared file lock. State writes use
  distinct atomic temporary files. Tests cover a stale snapshot and two real
  concurrent writer processes, including preservation of both updates.
- A supervisor could not find the referenced styling report in its isolated
  worktree. Explicitly referenced reports under `.factory/reviews/` or
  `.factory/evidence/` are now embedded with content hashes in implementation,
  code-review, and supervisor handoffs. Reads are bounded, credential-redacted,
  and confined to the target repository; missing reports remain explicit errors.
  This supplies inspectable evidence without turning an operator claim into
  automatic approval. Targeted handoff and safety tests pass. Live validation
  follows the next stopped-checkpoint restart.

After those changes, all 463 source tests and all five Control Center browser
scenarios passed. The same ticket-only persistence is used by human merge,
claim release, merge stewardship, and per-ticket evidence-summary publication;
these commands must not restore unrelated stale worker states either. Styling's
next Live implementation prompt contains the actual browser report and hash,
not only a path that its isolated worktree cannot open.

The next reviewer inspected the supplied styling screenshots and approved the
same candidate. The supervisor recommended MERGE, and I confirmed the exact
GitHub head before selecting **Merge exact revision**. PR #13 merged at
`2026-09-06T05:31:21Z`, producing `7e70f61ce751a8c8d28fa6250042d07c9da37beb`.
Tickets #1–#5 are now Done; TV navigation QA has started.

The combined five-ticket checkout passed 242 Python and 35 Node tests. A mobile
tomato query displayed four matching recipes at 375px with no page overflow.
Saving Roasted Tomato Soup on mobile, then opening TV browse, put it in
My Cookbook. This matches the PRD's explicit refresh requirement; immediate
client-side rail rebuilding is not required. All four named rails rendered,
the first three had horizontal overflow inside their own containers, and the
page remained 1920px wide at a 1920px viewport. No uncaught JS errors appeared.

Run app intentionally disables **Start app** while another Control Center
operation is open. Its previous instruction to wait was insufficient because
the scheduler can remain open at approval checkpoints. Guidance now explains
using **Copy command** in a separate terminal, or stopping at a safe checkpoint.
I followed the displayed command on port 5001 for the integrated preview, then
stopped only that owned server and browser. User services on other ports were
untouched. The new browser regression initially exposed an incomplete test
fixture (its manifest was Running but operation state was idle); the fixture
now includes a frozen in-flight operation without launching a real agent.

## TV browse checkpoint

Ticket #6's independently reviewed QA commit was
`29f0917eef15f5a9014271f199d84bcd9fb9e527`. The implementation candidate
`24d953ff7728f3351600c05dfca1179bb58dcc55` passed 243 Python and 68 Node
tests. At 1920×1080, five Right presses reached the last Popular card with
actual visible focus. Two Down presses moved through Quick to Vegetarian;
Enter opened the selected Tomato Soup TV detail URL. Native Tab/Enter operated
only the cookbook button. Search retained its caret, handled zero matches,
and recovered after clearing. Mobile initialization did not steal focus.
Recordings and candidate-bound measurements are in
`.factory/reviews/attendee-ticket-6.md` in the disposable target checkout.

The reviewer correctly requested this browser evidence before approval. Stopping
the automatic repair loop then exposed a recovery gap: a clean already-reviewed
candidate could be discarded on restart. Recovery now preserves that exact head
and requires an operator retry. An unchanged candidate with a changes-requested
review can return through verification only when explicit, readable operator
evidence names that exact revision. It is not marked approved; fresh independent
review and the human merge gate remain mandatory. The targeted runtime suite
passes 93 tests, including missing/unbound evidence and dirty-worktree rejection.
The first Live evidence-only retry exposed a second no-change classifier that
still rejected the candidate. That guard now honors the same explicit exception;
a regression exercises the classifier, not only the evidence helper. The full
suite also caught a complexity-budget regression in ticket loading. Recovery
selection was extracted into a small helper; the budget was not increased.

The repaired Live path retained the same candidate, reran verification, and
obtained a fresh APPROVE from Code Review plus the supervisor's MERGE readiness
recommendation. I confirmed GitHub's exact head and selected **Merge exact
revision**. PR #14 merged at `2026-09-06T06:13:05Z`, producing
`de3d97959f68fef41cad1ff8934cbdb0c72238b8`. Tickets #1–#6 are Done.
The source suite then passed all 465 tests; the complexity limit is unchanged.

## TV detail checkpoint

Ticket #7 QA commit `6721f90566a05df81b10954615fd0df3ee51d47a`
passed independent review: two existing content checks passed, and 26 missing
behavior assertions supplied valid RED evidence. Candidate
`3e4fc5ed202101f56ce455052576d64de8b1fd78` then passed 245 Python and 99 Node
tests with protected hashes unchanged. I read all production and developer-test
changes; the latter are additive and explicitly approved for this candidate.

At 1920×1080, Down scrolled the detail pane to its end while keeping back and
cookbook actions visible. The final Lentil Stew step was wholly visible at
y889.27–972.45. Enter saved and removed without moving focus. Up returned the
pane to zero before moving to back. Back/Enter, Escape, and Backspace all
returned to TV browse. A network-disabled save retained the unsaved state and
focus, displayed an actionable failure message, and succeeded after reconnecting.
Two recordings, a screenshot, measurements, and the distinct developer-test
approval are recorded in `.factory/reviews/attendee-ticket-7.md`.

An additional native-keyboard browser sweep passed for all 12 recipes: final
steps and both actions remained visible, page width stayed 1920, and bounded
maximum scroll ranged from 301 to 573 pixels. No external resources or uncaught
JS errors appeared. PR #15 then merged at `2026-09-06T06:35:20Z`, producing
`f2f2669ea01e70064b76edfb4f3acb0f9ef8c02b`. Seven tickets are Done.

The following supervisor invocation failed with Codex's explicit usage-limit
message before ticket #8 began. This is not a dependency deadlock or a product
defect. No reset, extra credits, or provider switch was authorized. A later
account-usage read disagreed with that recorded CLI failure, so I started one
normal resume attempt rather than assuming the old limit remained current.
Supervisor failures now expose bounded, redacted terminal provider errors in
Activity. Capacity failures explain waiting/resolving the allowance and resuming
with Run factory, preserving tickets and approvals. All 467 source tests pass.

## Additional presentation fixes

Two additional UI inconsistencies surfaced during Live operation. Companion
actions such as retry can wait on GitHub for about a minute without returning
the main scheduler's Activity view. They now show a persistent submitting message
and suppress duplicate submissions until the request completes or fails.
Completed cards also now say Completed instead of displaying a historical
human-review phase or stale merge-steward badge. Underlying audit history is
preserved. All five browser scenarios pass, including these regressions.

## Final release handoff findings

The normal Codex resume succeeded after the quota interruption. Ticket #8's QA
produced 22 Python behavior-assertion failures for the missing README, with 20
Python and six Node checks already passing. I read and approved both protected
test files. Implementation added the README and 128 lines of public-seam tests.
Independent verification passed 298 Python and 105 Node tests with zero skips.

Code review correctly refused a README schema without the populated release
receipt. The worker had written that receipt externally, but the Factory did
not carry its content into the isolated review. That is a Factory handoff bug,
not evidence that the implementation had supplied no report at all. A designated
`.factory/review-handoff.md` now lets a worker return a bounded, revision-bound
report. The Factory redacts credentials, snapshots content by hash, and includes
it in review/supervisor inputs explicitly as an implementation-authored claim,
never as independent verification or approval. Tests reject stale, oversized,
and escaping-symlink reports and preserve earlier snapshots across updates.

A repair committed 21 explanatory README lines just before Stop reached the
worker. The scheduler still knew only its predecessor. Recovery now preserves
a clean descendant with unchanged protected QA blobs, clears inherited approval,
and requires operator retry plus fresh gates/review. Dirty, unrelated, changed-QA,
or changed-specification candidates do not take this recovery path.

I independently read the full README, the additive developer tests, and the
21-line repair, and reran the exact candidate's 298/105 checks. Operator receipt
`.factory/reviews/attendee-ticket-8.md` separates current automated tests from
inherited browser observations, binds acceptance to the exact candidate, and
records the four policy hashes, R1–R28 evidence, per-ticket line counts, test-change
approval, and remaining merge gate. No physical-device, kitchen, screen-reader,
cross-platform, or unassisted-human validation is claimed.

The fresh code review approved `2acee4bf2ca5b782673e77d6fa419067c497e228`,
and supervisor-merge-46 recommended MERGE while retaining human authority. I
checked the GitHub head and used Merge exact revision. PR #16 merged at
`2026-09-06T12:05:30Z`, producing `5e84b3877eb99652b11fea2d13be996ff4f108cb`.
All eight tickets reached Done.

The final merge revealed a shared-Git-ref race: the scheduler and companion
merge command fetched origin/main concurrently. GitHub had already merged, but
the companion failed with a ref-lock compare-and-swap error. The scheduler
independently synchronized and verified the merge, so code was not lost. Shared
repository synchronization now uses a cross-process lock for scheduler, merge,
and steward fetches. A subprocess regression proves exclusion and release.

Merge-event reconciliation also discarded late audit metadata when polling had
already marked a ticket Done. It now validates and attaches those events even
for Done tickets, rejecting mismatched revisions. I reconstructed ticket #6's
event from its preserved original human-merge receipt, and ticket #8's event
from the observed merge action, GitHub head/merge commit, and synchronized
receipt. This was explicit operator bookkeeping recovery, not another merge,
new approval, or an unassisted attendee action. Historical command failures
remain in the audit trail rather than being rewritten as successes.

## Usage evidence so far

Product Review's original text log reported `tokens used: 30,275`, without a
per-field breakdown. Do not relabel that number as input or output tokens.
Architecture's JSON event reported 102,293 input tokens, 62,592 cached input
tokens, and 7,956 output tokens. Cached input is a reported subset, not extra
tokens to add to input. These are invocation records, not a currency charge or
an account-wide bill. Program Design reported 126,169 input, 85,248 cached input,
and 11,449 output tokens. Vertical Slices reported 157,944 input, 102,016 cached
input, and 6,846 output tokens. Delivery roles and retries are not included in
these figures.

## Final integrated verification and export

The independent GitHub checkout at `/tmp/factory-release-check.gjSN9J/product`
was fast-forwarded to final main `5e84b3877eb99652b11fea2d13be996ff4f108cb`.
Its tracked tree is clean. Its separately installed virtual environment passed
298 Python tests in 1.58 seconds; Node passed 105 with no failures or skips.
`git diff --check` passed. Logs are `final-python.log` and `final-node.log` in
`/tmp/factory-release-check.gjSN9J/`.

I stopped only the owned preview process and restarted that final checkout using
the README's alternate-port command on 5077. Mobile ingredient search again found
only Quick Berry Porridge; detail Add confirmed saved state. TV browse then showed
the same saved recipe, native Down traversed to Cookbook, Enter opened its detail,
and Down/Enter removed it before Escape returned to browse. Final screenshots
are `final-mobile-detail.png` and `final-tv-browse.png` in the same evidence directory.
The full 12-recipe native-key TV sweep was then repeated against this final merged
server. All recipes passed final-step visibility, visible back/save actions,
bounded scrolling, 1920px document width and no external resources or uncaught JS
errors. Results: `final-all-recipes-tv.log`. The final Control Center screenshot
`final-control-center.png` shows the single Done lane and count eight.

The Control Center's Export run evidence action succeeded. GitHub run summaries
for all eight issues were updated, and a direct Project #17 read confirmed all
eight items are Done. The packet and manifest are under the target repository's
`.factory/control-center/evidence-eea40ab19dfe/`. Packet SHA-256:
`cc340a5d7a2f056178bac8766fee48629070131bf787745cc4cbc80a87acad6b`.
I verified its hash and all 126 referenced artifact hashes. Its structural
missing-evidence list is empty; this does not certify every product property,
erase historical failures, or replace the explicit validation limitations.
A credential-pattern scan found no matches. Raw provider logs/prompts are not
included in the portable packet. Review the private business content before sharing.

## What I would tell a colleague considering this workshop

“I learned why a failed test is not automatically good evidence, why a green
suite is not the same as a usable screen, and why approval must name the exact
revision. I also saw how to recover work without discarding the QA checkpoint.
Those are useful skills for my team. I would not yet describe this version as
a frictionless self-service exercise.”

The strongest moments were the false-RED rejection, browser evidence resolving
review findings, and the explicit merge decision. The least useful attendee time
was spent on CLI discovery, ambiguous waiting, and repairs to orchestration
bookkeeping. Those should be fixed by the product, not taught as routine setup.

For CTOs, the transferable decision is where authority and evidence live. For
tech leads, it is how contracts, ownership and dependencies bound parallel work.
For engineers, it is how to inspect a candidate, challenge a test, supply a useful
failure report and resume from a valid checkpoint. The number of agents is not
the learning outcome.

Before the next workshop:

1. Run a clean human pilot using the repaired branch and only the attendee guide.
   Observe where the person asks what to click, what is running, and what proves Done.
2. Complete CLI authentication, repository creation and preflight before class.
   Check the actual CLI allowance; a successful login is not a capacity guarantee.
3. Keep the whole transformation as the main exercise. Use explicit plan, QA,
   review and final-app checkpoints, with a known-complete reference for the close.
4. Teach one deliberate recovery using genuine evidence, not a collection of
   accidental infrastructure failures. Preserve time for reviewing the final app.
5. End with each attendee naming one team use case, its required evidence, merge
   owner and recovery policy. That makes the experience applicable beyond this app.

Do not extrapolate these debugging timings or partial token records into a
three-hour guarantee or a per-attendee price. This run included source repairs,
retries, provider limits, operator pauses and diagnostic work. No AWS resources,
paid quota reset or extra credit purchase was used. Physical TV/remote hardware,
Safari, screen readers, Linux/WSL and an unassisted human pilot remain untested.

Local inspection endpoints are [Control Center](http://127.0.0.1:5069/),
[TableStory](http://127.0.0.1:5077/) and [TV mode](http://127.0.0.1:5077/?mode=tv).
These are local development servers, not public deployments. Temporary evidence
and disposable GitHub artifacts were preserved. No source commit, push or release
was performed as part of this request.
