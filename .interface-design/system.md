# Software (re)-Factory Interface System

## Direction

Use the visual language of `developer.amazon.com` without presenting this
project as an Amazon product. The interface should feel like a developer
operations console: direct, dependable, dense where state matters, and calm
where attendees need to read.

The two surfaces have distinct roles:

- **Control Center:** operational, compact, and optimized for status,
  decisions, ticket flow, and live output.
- **Workshop guide:** instructional, more spacious, and optimized for
  completing one step at a time.

The shared signature is a dark navy masthead plus an orange current-action
rail. Blue is reserved for navigation and links. Semantic colors communicate
state, not decoration.

## Reference

- Visual reference: `https://developer.amazon.com/`
- Core reference colors: navy `#232f3e`, deep navy `#162939`, orange
  `#ff6200`, link blue `#0066b3`, pale blue-gray `#e2edf4`
- Reference typefaces: Ember Modern Display and Ember Modern Text

## Palette

Use semantic tokens. Do not introduce one-off colors when an existing token
fits.

| Role | Value | Use |
| --- | --- | --- |
| Action | `#ff6200` | Primary actions, current phase, active workflow rail |
| Action hover | `#e54f00` | Primary action hover and active text |
| Action soft | `#fff5ef` | Current-action and selected backgrounds |
| Link | `#0066b3` | Links and navigation affordances |
| Link dark | `#004f8a` | Link hover and strong navigation text |
| Navy | `#232f3e` | Primary text, dark surfaces |
| Deep navy | `#162939` | Masthead and terminal base |
| Secondary text | `#495159` | Supporting values |
| Muted text | `#62686f` | Explanations and metadata |
| Quiet text | `#767676` | Disabled and low-priority labels |
| Border | `#d6e2e9` | Standard boundaries |
| Soft border | `#e2edf4` | Internal separation |
| Inset surface | `#f0f2f4` | Inputs and nested operational regions |
| Page surface | `#f7f8f9` | Application canvas |
| Success | `#237a57` | Passed and completed states |
| Warning | `#985f0d` | Human attention and waiting states |
| Error | `#d13212` | Failed, blocked, and destructive states |

## Typography

- Body: `"Ember Modern Text", "Amazon Ember", "Helvetica Neue", Arial,
  sans-serif`
- Display: `"Ember Modern Display", "Amazon Ember", "Helvetica Neue", Arial,
  sans-serif`
- Code: `"SFMono-Regular", "Cascadia Code", Consolas, monospace`
- Load Ember using the public font files used by the Amazon Developer site.
  Keep the local fallback stack so both products remain usable offline.
- Letter spacing is `0`.
- Use weight and color before adding more type sizes.

### Control Center Scale

- Metadata: `9-11px`
- Body: `12-14px`
- Surface title: `18px / 700`
- Page title: `28px / 700`
- Current operation: `32px / 700`

### Workshop Scale

- Metadata: `10-13px`
- Body: `16px`
- Supporting lead: `19px`
- Section title: `32px / 700`
- Workshop title: `48px / 700`, `42px` on mobile

## Depth And Surfaces

- Depth strategy: borders and tonal surface shifts.
- Do not add shadows to ordinary cards or page sections.
- Use shadows only for overlays, drawers, toasts, and screenshots that must
  read as captured artifacts.
- Controls use a `4px` radius.
- Work surfaces use a `6px` radius.
- Inputs are slightly darker than their parent surface.
- The masthead is deep navy. Terminals use deep navy with pale blue-gray text.
- Avoid gradients, decorative blobs, oversized radii, and nested cards.

## Spacing

- Base unit: `4px`.
- Compact Control Center padding: `12-20px`.
- Primary operational panel padding: `20-24px`.
- Workshop component padding: `20-28px`.
- Workshop section spacing: `48px` mobile, `64-76px` desktop.
- Minimum interactive target: `40px`; prefer `44px` in the workshop guide.

## Hierarchy

### Control Center

1. Current operation or required human decision.
2. Next safe action.
3. System health and run totals.
4. Delivery trace.
5. Activity output and historical evidence.

### Workshop Guide

1. Current workshop step and its goal.
2. Exact action in the Control Center.
3. What happens and what to inspect.
4. CLI equivalent.
5. Completion check.

## Component Patterns

### Masthead

- Height: `60px` desktop, `58px` mobile.
- Background: deep navy.
- Factory mark: orange square with navy internal cells.
- Keep repository and connection state compact.
- Place the current global action at the far right in orange.

### Primary Action

- Height: `40px` in the Control Center, `44px` in the guide.
- Padding: `8px 16px`.
- Radius: `4px`.
- Background: action orange.
- Text: deep navy; change to white on the darker hover state.
- Focus: `3px #ffb14a` ring with visible offset.

### Navigation

- White surface with a soft right border.
- Active item uses an orange left rail and pale blue-gray background.
- Navigation text stays navy; blue is for navigable text and links.
- Mobile navigation uses a 44px menu target and an explicit scrim.

### Current Operation

- White surface with a `4px` orange left rail.
- Headline is the focal element.
- The next action uses an inset pale surface.
- Run totals form a compact strip under the operation.
- Blocked, warning, and complete states replace orange with their semantic
  state color.

### Workshop Step

- Circular numbered marker.
- Goal appears before explanatory detail.
- Control Center and CLI paths are peers, not nested cards.
- Completion control sits after the evidence and check.

### Workflow Trace

- Use connected nodes to show lifecycle progression.
- Orange indicates the current phase.
- Green indicates completed phases.
- Gray indicates future phases.
- At narrow widths, use `minmax(0, 1fr)`, `min-width: 0`, and fluid nodes.

### Terminal

- Deep navy body, lighter navy toolbar, pale blue-gray text.
- Radius: `6px`.
- Code remains horizontally scrollable.
- Copy action has a visible hover and focus state.

### Status And Attention

- Never rely on color alone; pair color with labels and text.
- Use tabular numbers for counts and timestamps.
- Human decisions use a warning border and explicit action label.
- Empty, loading, running, failed, and complete states must all be visible.

## Responsive Rules

- Verification baseline: `390px` mobile and `1440px` desktop.
- `document.documentElement.scrollWidth` must equal `clientWidth` at `390px`.
- Fixed desktop grid children must use `minmax(0, 1fr)`.
- Any grid or flex child containing long text must use `min-width: 0`.
- Workflow map nodes may wrap on mobile; do not hide overflow.
- Control Center system signals stack to one column below `480px`.
- Ticket lanes may scroll horizontally by design, but the page itself must not.
- Text must wrap without clipping, including repository names, issue titles,
  commands, and long unbroken values.

## Accessibility And Motion

- All controls need default, hover, active, focus, and disabled states.
- Focus indicators must remain visible against light and dark surfaces.
- Use semantic HTML and native controls.
- Preserve reduced-motion behavior.
- Repeated operational actions should not animate.
- Running indicators may pulse subtly; disable the pulse for reduced motion.

## Avoid

- Generic blue SaaS dashboards.
- Purple decorative accents.
- Marketing-style card grids inside the Control Center.
- Gradients or color used only as decoration.
- Large rounded pills for commands.
- Hiding mobile overflow instead of fixing the responsible layout.
- Mixing the Control Center's dense rhythm with the guide's reading rhythm.

## Source Files

- `factory/control_center/styles.css`
- `factory/control_center/index.html`
- `factory/control_center/app.js`
- `workshop-guide/app/globals.css`
- `workshop-guide/app/layout.tsx`
- `workshop-guide/app/page.tsx`
