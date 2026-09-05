# Workshop validation

Use this checklist before publishing a session release. A passing test suite is
not a guarantee that beginners finish Live work in three hours.

## Instruction update — 6 September 2026

On `codex/workshop-audience-payoff`, 14 guide/editor tests, seven repository-contract
tests, guide lint, both production builds, and local link/asset checks passed.
Regression checks cover the continuous 180-minute agenda, earlier eligible
implementation, the break and pilot time, full transformation scope, and the
absence of a completion tracker. No factory runtime or screenshot assets changed.
The real-run cost record and novice observation remain to be performed.

## Baseline validation — 5 September 2026

On `codex/workshop-simplify-readiness`: 432 factory tests and 11 guide/editor
tests passed, as did lint, both production builds, the complexity gate, and local
document/asset checks. The browser check passed empty setup, QA source and focus
recovery, a five-ticket Standard Rehearsal, UI evidence export and packet opening,
and guide reload. Updated screenshots were inspected; their recorded source and
asset hashes match. A 390-pixel guide viewport had no horizontal overflow.

Those were local macOS checks. Subsequent PR #59 checks passed the factory tests,
guide/browser journey, and both rehearsal scenarios on GitHub
([run record](https://github.com/giolaq/software-refactory-workshop/actions/runs/33964842824)).
CI is not a novice observation. Live provider accounts, fresh Linux/WSL
installations, the public deployment, and a timed novice session remain unverified.

## Automated local checks

From the control checkout, with the development dependencies installed:

```sh
.factory/venv/bin/python -m unittest discover -s factory/tests -q
cd workshop-guide
npm test
npm run lint
npm run build:vercel
```

The CI workflow also checks the guide and Control Center in a browser. It creates
disposable repositories, uses mock providers, approves protected QA tests, and
merges all five Rehearsal tickets before opening the Evidence Packet. It does not
call GitHub, bill a model provider, or change your current run.

To run that check locally, return to the control checkout:

```sh
FACTORY_PYTHON="$PWD/.factory/venv/bin/python" node factory/tests/workshop_browser_check.mjs
```

Start the guide separately with `npm run dev -- --port 3030` in `workshop-guide`.
Add `GUIDE_URL=http://localhost:3030` before the browser-check command to include
guide navigation and reload checks. The first browser run downloads the pinned
`agent-browser` package and may require
`npx --yes agent-browser@0.36.0 install --with-deps` on Linux.

## Refresh screenshots

```sh
FACTORY_PYTHON="$PWD/.factory/venv/bin/python" node factory/tests/workshop_browser_check.mjs --screenshots
```

The command captures real local states: empty setup, Product Review, QA Review,
human merge, and completed Rehearsal evidence. Images are examples of Rehearsal,
not proof of a Live provider run. Review each image visually. The generated
`workshop-guide/public/screenshots/capture-manifest.json` records source and image
hashes, the base commit, and whether the working tree contained changes. Retake
screenshots after changes to the affected interface; publish them with the same
tested source revision as the guide.

## Required human dry run — not yet established by these checks

Follow [Workshop dry run](WORKSHOP_DRY_RUN.md): record one real transformation's
scope and operating effort, then observe two or three people who have not used
the Factory. Record observations rather than coaching them past unclear
instructions. Freeze feature additions until these observations identify the
actual blockers; fix and retest required paths before claiming beginner readiness.

| Check | Record before release |
| --- | --- |
| Fresh setup on macOS, Linux, and WSL2 | OS, Python and Node versions, selected provider, exact failure and successful repair |
| Live provider smoke | CLI version, authentication method, planning, QA, implementation, review, final human merge; test each advertised provider when an account is available |
| Personal GitHub repository and Project | Correct target, published issues, visible Project status, permission and branch recovery |
| Novice navigation | Can open the Control Center, find the current phase, inspect tests, recover, and export without facilitator rescue |
| Three-hour pacing | Setup duration, first eligible implementation start, time at each decision, agent time versus active human effort and wait, completed transformation scope, remaining tickets and resume point |
| Learning | Can reject false RED, reject stale approval, and propose a bounded pilot with an owner and stop/go criterion |
| Accessibility | Keyboard-only decisions, zoom, narrow viewport, and screen-reader labels in the browsers attendees use |

Mock success does not certify Claude, Codex, Cursor, another model, another
operating system, or an arbitrary product repository. Unknown token usage is not
zero cost. Collect provider usage and human review effort separately.

## Release handoff

1. Resolve failures and record the novice dry-run results.
2. Commit the tested code, guide, and matching screenshots together.
3. Create the session release tag and give that exact tag to attendees.
4. Deploy the guide from that revision. Check the public guide against the tag;
   a successful local build does not prove the production deployment updated.
5. Freeze the session version. Keep a prepared, clearly labeled Rehearsal example
   available while healthy Live agents continue working.

The readiness implementation itself does not publish, tag, run paid providers,
or claim cross-platform certification.
