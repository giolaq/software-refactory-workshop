# Rehearsal walkthrough results

The local Pocket Cinema → TableStory Rehearsal reached **5 of 5 tickets Done**.
This was an agent-operated browser walkthrough with repairs, not an unassisted
human pilot or a Live provider benchmark.

## Environment and scope

- Source branch during validation: `codex/workshop-audience-payoff` (working changes).
- Disposable checkout: `/tmp/factory-novice.ZdoRYt/software-refactory-rehearsal`.
- Planning run: `eea40ab19dfe`; Standard profile; human QA and merge decisions.
- macOS, local Python and Node.js, automated Chromium browser interaction.
- No paid coding agents, GitHub writes, or AWS resources were used for this run.

## Repairs and observed results

| Problem | Repair and retest |
| --- | --- |
| Missing files and generic failure text could count as RED evidence | Tightened classification; missing-file and mixed assertion/environment failures are rejected. Regenerated affected QA rather than approving old receipts. |
| Rehearsal QA could ignore revision feedback | Added an explicit supported reference revision and a clear refusal for unsupported changes. Rehearsal is not an open-ended QA adapter. |
| Brand ticket delivered an unused stylesheet | Added the visible TableStory shell; tested the served stylesheet and checked the mobile rendering. |
| My Cookbook displayed unsaved recipes | Filtered the collection and refreshed it after removal. Browser check: save one recipe, see exactly one, remove it, see zero. |
| TV return navigation lost the originating focus; empty rails crashed | Saved and restored rail position, skipped empty rails, added navigation unit coverage, and exercised Enter, Escape, and Backspace. |
| Rounded cards clipped the visible focus outline | Moved the visible ring to the card and added scroll margin. Inspected the rendered ring at 1920 × 1080. |
| Rehearsal candidate synchronization required a GitHub remote | Added a local synchronization path. Changed candidates lose approval and go through verification and review again. |
| Preview linked to the Control Center or launched on the wrong port | Resolve the application port separately and bind Flask explicitly. Start app selected and served port 5001 while 5000 was occupied. |
| Final documentation QA crashed before making an assertion | Assert that the required product guide exists before inspecting its contents. Observed genuine RED followed by GREEN. |
| A dependency waiting for human merge was labelled a deadlock | Changed the scheduler message to “Waiting for dependencies”; this condition alone does not prove a cycle. |

## Verification

- Factory suite: 442 tests passed.
- Workshop website: production build and 14 tests passed.
- Integrated recipe app: 15 Python tests and 4 JavaScript tests passed.
- Mobile at 375 × 812: ingredient search, empty results, ingredients and method,
  saving, saved-only collection, removal, and no horizontal overflow.
- TV at 1920 × 1080: rail navigation, recipe opening, cookbook action, returning
  to the originating card, and a visible focus ring within the viewport.
- Control Center: QA review, retry, exact-revision merge, five completed tickets,
  Start app, Stop app, and evidence export.
- A stale candidate approval was rejected after its commit changed. The changed
  candidate was synchronized and re-verified before merge.

The five-ticket merge completed at `486a744b7eff`. A subsequent human visual
correction for focus-ring clipping and singular recipe counts was committed only
in the disposable checkout at `fcab9da`; its 19 app tests were rerun successfully.
Do not describe that follow-up as another agent-reviewed ticket.

Local screenshots and the exported packet are under
`/tmp/factory-novice.ZdoRYt/`; temporary files are not durable release artifacts.
The packet is at
`software-refactory-rehearsal/.factory/control-center/evidence-eea40ab19dfe/evidence-packet.md`.

## What this does not establish

Rehearsal reference tests do not replace browser inspection or demonstrate Live
agent reliability. No provider cost or speed comparison was measured. Linux,
WSL, other browsers, and an unassisted first-time attendee remain unverified.
Run the human pilot in `factory/WORKSHOP_DRY_RUN.md` before claiming that a novice
can finish without help. Validation was performed before committing the source changes.
