# Pocket Cinema: search by film or genre

Optional small-change example. This is not the main workshop exercise; use
[the TableStory product-transformation PRD](recipe-app-prd.md) for the workshop.

## User and problem

A viewer wants to find a film by title or genre. The search field says
“Search films or genres,” but the browser currently filters only film titles.
The movie API already accepts a query and searches titles and genres.

## Required behavior

1. Typing a title or genre filters the visible film cards without reloading.
2. Matching ignores case and leading or trailing query whitespace.
3. A genre query returns films in that genre even when their titles do not
   contain the query. Use an actual genre from `demo-app/catalog.json`.
4. The visible result count matches the cards. No matches shows the existing
   empty-state message. Clearing the query restores every card.
5. Film details, watchlist actions, and the existing movie API keep working.

## Scope and constraints

Deliver this as one end-to-end ticket: template data, browser filtering, and
regression tests together. Do not create separate API, design-system, or
documentation tickets for this small change. If a genuine blocker needs another
ticket, explain it during plan review.

Keep Pocket Cinema's design and data. Do not rebrand it, add authentication,
install a new framework, add a database, or implement a TV interface.
Use the repository's existing Python and Node test tools. Acceptance tests
must demonstrate a genre match that fails on the unchanged browser behavior,
as well as preserve title matching and empty-query behavior.

## Acceptance and manual check

Start the app, type a genre from the catalog, and verify the matching films and
count. Try a mixed-case query with surrounding whitespace, an unmatched query,
and an empty query. Open a film and use the watchlist to check compatibility.

A human reviews the proposed tests, their baseline assertion failure, and the
candidate diff. Merge only the revision covered by passing checks and review.
