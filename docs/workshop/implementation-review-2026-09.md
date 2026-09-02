# Implementation review against PRD v1.0, September 2026

Status: written against branch head `295ddec` (before the Control Center,
planning experts, and Live/Rehearsal modes landed on `main`). Kept for history.
Critical finding C1 (missing mobile baseline) is fixed on `main`: `setup_demo.sh`
repoints the `factory-baseline` tag automatically and `factory doctor` fails if
it drifts. Re-check the remaining items against current code before acting.

## Verdict

Solid implementation, wrong ending state. Milestones M1–M5 were all present and
the pipeline worked end to end in mock mode (CI proved it). But the repository
was left in a post-demo state rather than the pre-demo baseline the PRD
deliverable requires, and two latent bugs (rails wiring, crash-recovery
publish) undermined acceptance criteria 5 and 8.

## Critical findings (workshop-breaking at the time)

### C1. The committed demo app was the finished TV app, not the mobile baseline

`demo-app/` already contained every TV-refactor output (`focus.js`, `tv-nav.js`,
`tv-rails.css`, `tv-detail.*`, `/api/rails` and `is_tv_mode()` in `app.py`),
exactly the files `mock_agent.py` writes. The `factory-baseline` tag the reset
script restored from did not exist, so on a fresh clone the script tagged HEAD
(the finished app) as the baseline. Because the mock agent's edits are
idempotent, the run still reported success and CI stayed green while the demo
did nothing. Fixed on `main`.

### C2. Ticket #5 (TV home rails) was dead code

Commit `1112ead` added the `rails.js` and `tv-rails.css` references to
`templates/index.html`; merge `73b0ea2` resolved that file by taking main's
side and discarded both lines. No template test asserted the assets were
referenced (unlike `test_tv_detail.py`). Restoring the lines is not sufficient:
`rails.js` replaces `#movie-grid`, which `tv-nav.js` captured at import time.

### C3. Crash recovery re-created pushed branches, then failed the push

On restart an active ticket was reset to Backlog and re-dispatched;
`create_worktree` deleted and recreated its branch. `publish()` pushed before
checking `existing_pr`, so an already-pushed branch was rejected
non-fast-forward and the ticket landed in Blocked. Fix: check `existing_pr()`
before pushing and push with `--force-with-lease`; persist the attempt counter.

## Requirement coverage at that commit

| Area | Status | Notes |
| --- | --- | --- |
| FR1 board sync | PARTIAL | Projects v2 bootstrap, labels, atomic `state.json` good. `.factory/ids.json` caching not implemented; no pagination past `gh` list limits. |
| FR2 scheduler | PARTIAL | Parsing, gating, cycle and deadlock detection present. Wave-barrier dispatch; missing dependency strands a ticket in Backlog; only first `Depends-on:` line parsed. |
| FR3 isolation | MEETS | Branch/worktree naming, clean recreate, preserved on Blocked. |
| FR4 adapters | MEETS | Four templates, TOML override, per-ticket override, retry feedback, per-attempt logs. Literal `{}` in a custom command crashed the run. |
| FR5 gates | MEETS | Ordered, required/optional, 300 s timeout, retry to Blocked. No early exit after required failure; timeout killed only the shell. |
| FR6 publish | PARTIAL | Push-before-PR-check bug (C3); many `gh` calls per poll. |
| FR7 dashboard | MEETS | Fully compliant. |
| FR8 controls | PARTIAL | `--once` drained all waves; `--dry-run` ignored current status. |
| FR9 mock mode | PARTIAL | Merge-conflict path simulated, not exercised. |
| NFRs | PARTIAL | Stdlib-only held. 700 lines vs ≤ ~500. No preflight for `git`/`node` in mock mode. |
| Criterion 7 (CI) | PARTIAL | No dependency-order assertion; `Done == 7` brittle. |
| Criterion 8 (TV demo) | MISSES | Search input, watchlist buttons, header links unreachable by D-pad. |

## Other deviations noted

- Trap ticket spoiled in the attendee README (PRD confines that to facilitator notes).
- Seed ticket #5 depended on the API ticket in its criteria but not in `Depends-on:`.
- Issue template shipped a live `agent: codex` line.
- `factory/.github/` was inert (GitHub reads only the root `.github/`).
- `recipe-app-prd.md` referenced by no README.
- PRD's `node --test static/tests/` command fails on Node 22 (directory form unsupported).

## Beyond the PRD

Two subsystems the PRD never asked for: `planner.py` with `plan`/`approve`
(PRD to tickets behind a typed-APPROVE human gate) and an independent QA
acceptance-test phase (protected test files with blob-hash verification). Both
well designed, and the main reason the orchestrator exceeded the line budget.
At that commit they were the only parts with unit tests.

## Remediation order proposed at the time

1. Restore the baseline, tag and push `factory-baseline`, add a CI pre-run guard. (Done on `main`.)
2. Fix rails wiring in the ticket path; add template smoke assertions.
3. Fix crash-recovery publish ordering; persist attempts.
4. Harden CI: dependency-order assertion; `>= 2` Done instead of `== 7`.
5. Implement `.factory/ids.json` caching; make one seed ticket produce a real merge conflict.
6. Scheduler correctness: Block on missing dependencies, parse all `Depends-on:` lines, deterministic dispatch order.
7. Doc and config hygiene.
8. Optional polish: escape braces in command templates, fail-fast gates, process-group kill on timeout, D-pad coverage for search and watchlist.
