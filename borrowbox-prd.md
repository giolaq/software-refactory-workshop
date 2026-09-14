# PRD — BorrowBox equipment lending desk

**Version:** 1.0

**Status:** Ready for workshop product review

**Project type:** New application in an empty repository

**Product owner:** Fictional community workshop coordinator

## Problem and goal

A community workshop lends cameras, microphones, and tools to members. Its
coordinator records loans in a spreadsheet. During a busy session, it is hard
to tell which item is available, who borrowed it, and whether it is overdue.

Build **BorrowBox**, a small web application for the coordinator's lending
desk. The coordinator must be able to find an item, record a loan, and record
its return. Two checkout attempts must never create two active loans for the
same physical item. Records must survive a server restart.

This is a fictional workshop exercise, not a service for real borrower data.
Build the application from scratch. Do not copy or modify Pocket Cinema.

## Users

- **Desk coordinator:** uses one local computer to check equipment out and in.
- **Workshop manager:** checks availability, overdue items, and loan history on
  that same application. This is a user need, not a separate permission role.

The release is a single-operator local application. Multiple browser tabs may
be open. It has no authentication and must bind to loopback by default.

## Scope

### In scope

- A seeded inventory of individually identifiable physical items.
- Search and category/availability filters.
- Item details, checkout, return, and per-item loan history.
- Due dates and an overdue list.
- SQLite persistence, validation, and protection against duplicate checkout.
- Responsive, keyboard-accessible screens, automated checks, and a run guide.

### Out of scope

- Accounts, permission roles, public hosting, or real personal data.
- Creating, editing, deleting, or importing inventory through the UI.
- Reservations, waiting lists, renewals, multiple quantities per item, or fines.
- Email, SMS, QR codes, barcode scanning, payments, or external integrations.
- Maintenance scheduling, analytics, and a separate mobile application.

## Functional requirements

### BB-01 — Inventory

The home page shows every item in asset-tag order. Each row shows asset tag,
name, category, condition note, and availability. Each physical item has its
own row; two cameras are not represented as a quantity of two.

Seed these eight items on first startup:

| Asset tag | Name | Category | Condition note |
| --- | --- | --- | --- |
| CAM-001 | Mirrorless camera | Cameras | Battery and strap included |
| CAM-002 | Mirrorless camera | Cameras | Battery and strap included |
| AUD-001 | USB microphone | Audio | USB cable included |
| AUD-002 | Field recorder | Audio | Carry case included |
| TLS-001 | Cordless drill | Tools | Battery and charger included |
| TLS-002 | Orbital sander | Tools | Dust bag included |
| ACC-001 | Camera tripod | Accessories | Quick-release plate included |
| ACC-002 | LED light panel | Accessories | Power cable included |

All items start available, with no loans. Restarting or running initialization
again must not duplicate items, delete history, or make borrowed items available.

### BB-02 — Search and filters

Search matches a substring of asset tag or item name, ignoring case and outer
whitespace. Category is one of All, Cameras, Audio, Tools, or Accessories.
Availability is All, Available, or On loan.

Apply all selected conditions together. Show the result count. An empty result
shows “No equipment matches these filters” and a Clear filters control. Clearing
restores all items. An overdue item is still On loan, not a third availability
state. Query processing must not interpret user input as SQL.

### BB-03 — Item detail and checkout

Selecting an item opens a directly addressable detail page. It shows the
inventory fields, current availability, and loan history. An unknown asset tag
shows a useful not-found page with a link to inventory.

For an available item, show a checkout form with:

- **Borrower name:** required; trim outer whitespace; allow 1–80 characters.
- **Due date:** required; a valid `YYYY-MM-DD` calendar date, today or later.

Determine today from the server's local calendar date. Display that date on
the form so the user knows which date is being used. Revalidate it on submission.

On success, create one loan, show the borrower and due date, and replace the
checkout form with a Return item button. Preserve form entries on validation
errors and explain errors beside the affected fields. Do not create a partial
loan when validation fails.

Recheck availability in the same database transaction that records the loan.
If two tabs submit checkout for the same item, exactly one may succeed. The
other must show “This item is already on loan. Refresh to see its borrower.”
A disabled button alone is not sufficient protection.

### BB-04 — Return and history

Return item asks for confirmation. Cancel makes no change. Confirm records
the return time and makes the item available. Keep the original loan record.

Repeating a return request for the same loan is harmless: it must not add
history, change the original return time, or return a newer loan of that item.
Return operations identify a loan, not just an asset tag.

Show loan history newest checkout first, with borrower, checkout time, due
date, and return time or “Not returned”. A newly seeded item shows “No loans
yet”. A returned item can be checked out again, creating a distinct loan.

### BB-05 — Current and overdue loans

A Loans screen lists active loans, ordered by due date and then asset tag.
Show asset tag, item name, borrower, due date, and a link to item detail.

A loan is overdue only when it is unreturned and its due date is earlier
than the server's current local date. A loan due today is not overdue.
The Overdue filter shows only overdue active loans. Use a text label, not
color alone. Refreshing the page recalculates overdue status; no background
scheduler is required. Returning an item removes it from both active views.

## Data and persistence

Use an item record with a stable asset tag, name, category, and condition note.
A loan has a unique ID, item reference, borrower name, checkout timestamp, due
date, and nullable return timestamp. Derive availability from active loans;
do not maintain a second independent availability flag that can drift.

Persist items and loans in a local SQLite file under `data/`, excluded from
Git. Store event timestamps in UTC and display them in the server's local time
with a timezone label. Due dates are calendar dates, not midnight UTC instants.

Enforce at most one unreturned loan per item at the database level. Tests must
use separate temporary databases and never reset the user's database.

## Screens and interaction examples

The main navigation has **Inventory** and **Loans**. Use a simple lending-desk
layout: readable tables on desktop and stacked records on narrow screens.

```text
BorrowBox                              Inventory | Loans
Equipment
[Search equipment…] [Category: All] [Availability: All]
8 items
CAM-001  Mirrorless camera  Cameras  Available  [View]
CAM-002  Mirrorless camera  Cameras  Available  [View]
```

On item detail, put current availability and the checkout/return action above
history. Use white surfaces, dark text, and a restrained blue accent. Do not
spend a ticket on a logo, animation, or design-system package.

All controls need visible labels and focus states. Every workflow must work
using Tab, Shift+Tab, Enter, and Space where appropriate. At 375 CSS pixels,
there must be no horizontal page scrolling or inaccessible actions. Render
borrower names and search terms as text, never executable markup.

## Technical and delivery constraints

- Use Python 3.11+, Flask, the standard-library SQLite driver, server-rendered
  HTML, and CSS. Small vanilla JavaScript enhancements are allowed; checkout
  and return must not depend on a frontend framework.
- No paid APIs, cloud account, Docker, external database, or hosted assets.
  After dependencies are installed, application use must work offline.
- Document installation in a virtual environment, starting on
  `http://127.0.0.1:5000`, and selecting another port.
- Use parameterized SQL and transactional writes. Never log borrower names
  or submitted form bodies. Browser error pages must not expose tracebacks.
- Document exact test commands. Use pytest with Flask's test client and
  temporary databases. Include a browser test for the complete checkout/return
  journey; document any browser-test installation separately from app startup.
- The app is a local demo, not a production-ready lending system. State that
  limitation in its README.

## User journeys and success evidence

| Check | Action | Required evidence |
| --- | --- | --- |
| BB-A01 | Start on a fresh database, then restart | Exactly eight items and no duplicate initialization |
| BB-A02 | Search ` camera ` with category Cameras and availability Available | CAM-001 and CAM-002 appear; count is two |
| BB-A03 | Check out CAM-001 to fictional borrower Alex Morgan, due today | One active loan; Available + Cameras results now contain only CAM-002 |
| BB-A04 | Submit a blank borrower, impossible date, or yesterday's due date | Specific validation errors; no inserted loan |
| BB-A05 | Starting with CAM-001 available, submit two independent checkout requests | One succeeds; the other reports conflict; one active loan exists |
| BB-A06 | Cancel return, then confirm return | Cancel preserves the loan; confirm makes the item available and retains history |
| BB-A07 | Return an old loan again after a new checkout | The new loan stays active; original return timestamp is unchanged |
| BB-A08 | With a fixed test clock, inspect loans due yesterday and today | Only yesterday's unreturned loan is overdue |
| BB-A09 | Restart with one active and one returned loan | Availability and complete history are preserved |
| BB-A10 | Enter a borrower name containing HTML-like text | Text is displayed without executing markup |

Tests for overdue behavior must control the clock rather than depend on the
day the workshop runs. Concurrency evidence must exercise separate requests
or connections, not just a single UI's disabled button.
Use isolated fixtures for independent checks. State any pre-existing loan
explicitly; do not rely on earlier tests having run.

## Definition of done

From a clean checkout, a reviewer can install, initialize, and start BorrowBox
using its README. They can search, check out, inspect the active loan, return
the item, and verify history after a restart. BB-A01 through BB-A10 pass with
recorded test results. The UI is usable on desktop and at 375 CSS pixels.

No Pocket Cinema routes, film data, or recipe functionality are present.
Generated databases, secrets, virtual environments, and browser artifacts are
not committed. Human approval covers the tested candidate revision.

## Planning guidance and open questions

Plan small end-to-end slices, such as inventory discovery, safe checkout,
return/history, and overdue visibility. Each slice includes its UI, data
behavior, and acceptance evidence; do not split frontend and backend into
independent products. Establish a runnable foundation before dependent slices.
The planning roles choose and justify the ticket count during human review.

The repository starts without application code or tests. Define bootstrap
dependencies and meaningful verification before implementation. A missing
dependency, absent test runner, or missing module is not proof that a behavior
test is correctly RED. Do not weaken the approved Project Contract to proceed.

No product decisions are intentionally left open. The planning roles propose
file layout, routes, and internal interfaces within these constraints. An
incompatible generated contract is a human-review decision, not permission to
silently change scope. A three-hour workshop does not guarantee completion of
every Live ticket; record unfinished work honestly.
