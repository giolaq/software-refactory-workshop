# PRD — TrailMix conference agenda planner

**Version:** 1.0

**Status:** Ready for workshop product review

**Project type:** New application in an empty repository

**Product owner:** Fictional developer conference organizer

## Problem and goal

A developer conference has several sessions running at the same time.
Attendees need to find relevant talks and assemble a personal agenda without
accidentally choosing two overlapping sessions.

Build **TrailMix**, a browser-based conference schedule and personal agenda.
An attendee must be able to search sessions, inspect a talk, save it, and
resolve a schedule conflict. Their selections must survive a browser reload.

This is a new product, not a Pocket Cinema or TableStory rebrand. Its schedule
is bundled fictional data. It has no backend, accounts, or live conference API.

## Users

- **Conference attendee:** discovers sessions and chooses a feasible day plan.
- **Returning attendee:** opens the same browser later to review or print their
  saved agenda.

One browser profile represents one attendee. Saved choices do not sync across
devices. The application must say this near My agenda.

## Scope

### In scope

- A deterministic one-day schedule with three tracks and rooms.
- Search, track filters, session detail, and a saved personal agenda.
- Detection and explicit resolution of overlapping saved sessions.
- Browser-local persistence with graceful handling of unavailable storage.
- A useful print layout, responsive screens, accessibility, and tests.

### Out of scope

- Sign-in, cloud storage, ticket sales, payments, and conference administration.
- Editing sessions, speaker submissions, ratings, comments, and social features.
- AI recommendations, chat, external calendars, reminders, or notifications.
- Live schedule updates, multiple days, travel time between rooms, and
  conversion to an attendee's home timezone.
- A service worker, installable PWA, native mobile app, or offline page caching.

## Event and content model

Use **Northstar Developer Day**, a fictional event on **20 October 2026**.
All displayed times are venue-local time in **Europe/London**. Show this label
on the schedule and print view. Do not infer “today” or hide past sessions:
the sample must behave identically whenever the workshop runs.

Each session has a stable ID, title, speaker, track, room, start time, end
time, and a plain-text abstract of 40–80 words. Times use `HH:MM`, on this one
event date. End must be later than start. Sessions never cross midnight.

Bundle these twelve sessions. Speaker names and abstracts are fictional;
write plausible abstracts without links or claims about real people.

| ID | Time | Track / room | Title | Speaker |
| --- | --- | --- | --- | --- |
| ns-01 | 09:00–09:45 | Engineering / Cedar | APIs that survive change | Maya Chen |
| ns-02 | 09:00–09:45 | Leadership / Birch | Technical decisions without deadlock | Jordan Ellis |
| ns-03 | 09:00–09:45 | Product / Maple | Finding the smallest useful experiment | Sam Rivera |
| ns-04 | 10:00–10:45 | Engineering / Cedar | Debugging a slow service | Priya Shah |
| ns-05 | 10:00–10:45 | Leadership / Birch | Making architecture reviews useful | Theo Brooks |
| ns-06 | 10:00–10:45 | Product / Maple | Accessibility as a product requirement | Alex Kim |
| ns-07 | 11:00–11:45 | Engineering / Cedar | Tests that explain failures | Robin Patel |
| ns-08 | 11:00–12:00 | Leadership / Birch | Coaching through a difficult delivery | Casey Morgan |
| ns-09 | 11:00–11:45 | Product / Maple | Reading product signals without vanity metrics | Taylor Reed |
| ns-10 | 11:45–12:30 | Engineering / Cedar | Shipping smaller changes | Drew Bennett |
| ns-11 | 12:00–12:45 | Leadership / Birch | Planning a sustainable on-call rotation | Quinn Foster |
| ns-12 | 11:45–12:30 | Product / Maple | Writing requirements people can verify | Riley James |

## Functional requirements

### TM-01 — Schedule discovery

The default Schedule view shows all twelve sessions ordered by start time,
then title, then ID. Each card shows title, speaker, track, room, start/end
times, and an Add to agenda or Remove from agenda action.

Search matches a substring across title, speaker, and abstract, ignoring case
and outer whitespace. Track is All, Engineering, Leadership, or Product.
Search and track filters combine. Results update without a page reload and
show a matching count. Clearing both restores twelve sessions.

No matches shows “No sessions found. Try another search or track.” Include
a Clear filters control. Search and filters affect discovery only; they must
not remove saved sessions or hide agenda conflicts.

### TM-02 — Session detail

Opening a session shows all its fields and full abstract, plus its save state.
Detail can be an inline panel or a separate view; the planning roles must
choose one simple interaction and apply it consistently.

Returning to the schedule preserves search and track selection. If detail
opens as a dialog, move focus inside it, allow Escape to close it, and restore
focus to its opener. Do not require the attendee to interact with hover-only
content.

### TM-03 — Save and remove

Saving a session with no conflict adds its ID once and updates its control
to Remove from agenda in both schedule and detail. Repeated save attempts
must not create duplicate agenda entries.

Removing a session removes only that ID. Removing an already absent ID is a
no-op. The visible agenda count always equals the number of saved sessions,
regardless of the active discovery filters.

### TM-04 — Conflict detection and replacement

Treat intervals as half-open: `[start, end)`. Two sessions conflict when
`A.start < B.end` and `B.start < A.end`, comparing minutes after midnight.
Adjacent sessions do not conflict. A session ending at 11:45 may be followed
by one starting at 11:45. Being in different rooms does not prevent a conflict.

When a proposed session overlaps any saved session, do not change the agenda
yet. Show all conflicting titles and times, with two actions:

- **Keep my agenda:** dismiss the choice without saving the proposed session.
- **Replace conflicting sessions:** remove every overlapping saved session
  and add the proposed session in a single state update. Preserve all others.

Closing the conflict prompt with Escape or its close control is equivalent
to Keep my agenda. Never silently replace sessions or permit an overlapping
agenda. Comparison includes saved sessions hidden by the current search.

Example: saving ns-08 while ns-07 and ns-10 are saved must identify both as
conflicts. Replacement removes both and adds only ns-08. By contrast, ns-07
and ns-10 can be saved together because one starts exactly when the other ends.

### TM-05 — My agenda

My agenda shows saved sessions in the same chronological ordering as Schedule.
Show session details, removal controls, session count, and total duration in
minutes. Total duration is the sum of session lengths, excluding breaks.

An empty agenda shows “Your agenda is empty. Explore the schedule to add a
session.” Include a link or button to Schedule. A filtered schedule with zero
results must not cause this empty state if the agenda contains saved sessions.

### TM-06 — Persistence and recovery

Save only a versioned collection of session IDs in localStorage under a key
specific to this event, such as `trailmix:northstar-2026:agenda:v1`. Do not store
personal information, raw HTML, or duplicate copies of the bundled session data.

On startup, validate stored data before using it:

- Missing data starts an empty agenda without a warning.
- A malformed object, malformed JSON, or unsupported version starts an empty
  agenda and displays a short explanation. Do not crash the schedule.
- Remove unknown IDs and duplicates from an otherwise valid saved list.
- If valid IDs form an overlapping agenda, process them in schedule order,
  retain each nonconflicting session, and explain that conflicting choices
  were removed. Save the repaired list when storage is available.
- If reading or writing storage fails, the app remains usable in memory.
  Show “Your agenda works in this tab but cannot be saved in this browser.”
  Do not claim it will survive a reload.

Each action saves the current tab's complete agenda. Live cross-tab merging
is not required; the last successful write wins and a reload reads that value.

### TM-07 — Print agenda

Provide Print agenda on the agenda view, enabled only when it contains sessions.
Use the browser's print dialog; a custom PDF generator is out of scope.

Print includes the event name, date, venue timezone, and only saved sessions
with their titles, speakers, times, tracks, and rooms. Exclude navigation,
search, action buttons, conflict prompts, and unsaved sessions. Text must be
readable on a white background without requiring background-color printing.

## Screens and design

```text
TrailMix — Northstar Developer Day       Schedule | My agenda (2)
20 October 2026 · All times Europe/London
[Search talks or speakers…] [Track: All]
12 sessions
09:00–09:45  Engineering · Cedar
APIs that survive change — Maya Chen
[View details] [Add to agenda]
```

Use white or light gray surfaces, dark text, and a clear purple accent. Use
track labels in text; color is supplementary. Prefer a chronological list
over a dense calendar grid so the same workflow works on mobile.

At 375 and 1440 CSS pixels, users must be able to search, inspect detail,
resolve a conflict, and remove a session without horizontal page scrolling.
Use semantic controls, visible focus, associated form labels, and a polite
status announcement for result counts and save/remove actions. Support
keyboard-only operation. Render all session and search text safely as text.

## Technical and delivery constraints

- Use semantic HTML, CSS, and vanilla JavaScript ES modules. Keep conflict,
  filtering, ordering, duration, and storage-validation logic independently
  testable. Do not install a frontend framework or application server.
- Store the event schedule as local JSON. Validate unique IDs, required
  content, the three track/room pairs, and time ranges in automated tests.
- Serve the static app locally using Python 3.11+'s built-in HTTP server,
  bound to `127.0.0.1`. Document the exact command, the default port 5000,
  and how to select a different port. Opening an HTML file directly is not
  the supported run method.
- Use Node.js's built-in test runner for pure JavaScript tests. Use a small
  browser acceptance suite for integrated workflows and document its setup.
- No API keys, cloud services, hosted fonts, external images, or runtime
  requests outside the local server. Once dependencies are installed, the
  locally served application must work without internet access. This does
  not promise that the page works after the local server stops.
- Provide a README with install, run, test, print, and reset-agenda instructions.
  Reset removes only TrailMix's event key, never all browser storage.

## User journeys and success evidence

| Check | Action | Required evidence |
| --- | --- | --- |
| TM-A01 | Open a fresh browser state | Twelve valid sessions, zero saved, visible event date/timezone |
| TM-A02 | Search ` API ` | Only ns-01 matches; count is one; clearing restores twelve |
| TM-A03 | Select Leadership, then search `reviews` | Only ns-05 matches; unrelated saved sessions remain saved |
| TM-A04 | Save ns-07 and ns-10 | Both are saved without conflict; agenda total is 90 minutes |
| TM-A05 | Propose ns-08 after TM-A04, then cancel | Both overlapping sessions are named; the original agenda is unchanged |
| TM-A06 | Propose ns-08 again and replace | ns-07 and ns-10 are removed, ns-08 is saved, total is 60 minutes |
| TM-A07 | With ns-08 saved, add ns-11 | No conflict at the 12:00 boundary; total is 105 minutes |
| TM-A08 | Reload, then remove ns-08 and reload again | Only ns-11 remains, once, with total 45 minutes |
| TM-A09 | Load malformed, duplicate, unknown, or conflicting saved data | Recovery follows TM-06; the schedule stays usable and the agenda has no overlaps |
| TM-A10 | Simulate storage read and write failures | In-memory actions work; a visible warning explains non-persistence |
| TM-A11 | Print ns-08 and ns-11 | Print view contains those sessions and event details, without discovery controls or other sessions |
| TM-A12 | Complete save, conflict cancellation, replacement, and removal using the keyboard | Focus stays usable and visible; state changes are announced |

Write abstracts so the search examples are deterministic: only ns-01's
searchable fields contain `api`, and only ns-05 among Leadership sessions
contains `reviews`. Cover partial overlaps, identical times, containment,
multiple conflicts, and touching boundaries in the conflict-function tests.

## Definition of done

A reviewer can start the app from a clean checkout, search the schedule, build
an agenda, resolve a multi-session conflict, reload, and print their selections.
TM-A01 through TM-A12 have passing evidence. Every fixture record is validated,
and the main journey works at mobile and desktop widths.

The delivered app has no cinema or recipe functionality, no backend, and no
external runtime dependencies. Human review covers the revision that passed
the tests. A screenshot alone does not prove conflict handling or persistence.

## Planning guidance and open questions

Choose a small number of end-to-end slices: schedule discovery, saved agenda,
conflict resolution, and recovery/printing are natural boundaries. Include
tests within each slice. Establish a runnable static page and test harness
before dependent behaviors. Do not turn every field or screen into a ticket;
the planning roles must explain the proposed breakdown for human review.

No product decisions are intentionally left open. The planning roles choose
module layout and the detail interaction. They must preserve the no-backend
constraint and the exact conflict rules. Missing tooling or module imports
are bootstrap problems, not valid RED evidence for a behavior test. Resolve
Project Contract incompatibilities during human review rather than bypassing
its gates. A three-hour session is not a promise that all Live tickets finish.
