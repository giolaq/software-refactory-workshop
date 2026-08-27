# Simplified Control Center

## Design intent

The Control Center should answer three questions in this order:

1. What is happening now?
2. Does the factory need a decision from me?
3. What is the single safest action I can take next?

Everything else is supporting detail. It stays available, but it should not
compete with the current state or next action.

## Information architecture

The operator workflow is presented as four stages:

| Stage | Primary surface | Supporting surface |
| --- | --- | --- |
| Setup | Connection and repository policy | Advanced role settings |
| Plan | Requirements and plan approval | Expert artifacts and recovery |
| Deliver | Ticket flow | Supervisor activity |
| Review | Run the completed application | Repository monitor |

`Supervisor activity` and `Repository monitor` are secondary tools. They live
under **More tools** instead of appearing as peer steps in the main workflow.

## Interaction rules

- Show one primary action for the current context.
- Do not repeat the overview's next action in the masthead.
- Hide an empty attention queue; show it only when a human decision is waiting.
- Collapse diagnostics, CLI output, advanced role configuration, and run
  options until the operator asks for them.
- Automatically save the PRD draft so `Save` does not compete with
  `Start Product Review`.
- In Planning, show only the action that is currently possible: continue the
  experts or create tickets.
- Keep destructive recovery in one sidebar entry and one confirmation dialog.
- Preserve every existing capability and safety boundary; simplification is
  about hierarchy and disclosure, not removing operational evidence.

## Overview hierarchy

1. Current phase and state
2. Next safe action
3. Human decision queue, only when non-empty
4. Four-stage delivery trace and compact totals
5. Collapsed activity output
6. Collapsed system diagnostics

## Language

Use short, task-oriented labels. Prefer `Setup`, `Plan`, `Deliver`, and
`Review` over internal implementation terms. Use internal role names only in
the supporting detail where they help explain evidence or recovery.

## Responsive behavior

The same hierarchy applies on mobile. The navigation becomes a drawer, the
current action stacks below the current state, and disclosure panels remain
closed by default. No control essential to the next safe action may require
horizontal scrolling.

