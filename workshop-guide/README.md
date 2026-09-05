# Software (re)-Factory workshop guide

Release: `workshop-v1.2.1`

The attendee procedure guide follows **Setup → Plan → Deliver → Review**.
It explains commands, clicks, expected results, and recovery. The facilitator's
slides and notes explain the rationale. Live is the session path, using the
Pocket Cinema → TableStory product-transformation PRD in `recipe-app-prd.md`.
The same transformation is the simulated Rehearsal pack, not an optional extension. The organizer supplies a tested release tag.

The guide supports deterministic rehearsal and live GitHub paths. Claude is
the worked example, but attendees can use Codex, Cursor, or a custom CLI.
For Cursor, install the `agent` executable, run `agent login`, and select
**Cursor workshop** in the Control Center. The full operator contract is in
[`factory/CURSOR.md`](../factory/CURSOR.md).
The hosted guide provides instructions; the repository's Control Center runs
locally because it operates the attendee's agents, Git worktrees, and files.

## Local development

Requires Node.js 22.13 or later. `npm install`, `npm run dev`, `npm run edit`,
and `npm run build` stop immediately with a direct version message when the
active Node.js runtime is too old.

```sh
npm install
npm run dev
```

Open `http://localhost:3000`.

## Local copy editor

Use the local editor when you want to review the guide and change a word,
phrase, heading, or paragraph without editing TSX by hand:

```sh
npm run edit
```

The command opens `http://127.0.0.1:3001/__workshop_editor` and starts the
workshop preview if it is not already running. Click visible text in the
preview, type in the editor, and choose **Save to project**. The draft appears
in the preview while you type; saving writes the change to `app/page.tsx` so it
can be reviewed with Git and included in the next commit. **Undo last save** is
available for changes made during the current editor session.

The editor listens only on the local loopback address. It is not included in
the deployed workshop website and does not need an account, database, or API
key. Use the normal code workflow for layout, links, commands, conditional
logic, and component changes.

## Illustration assets

The concept illustrations in `public/illustrations/` were generated for this
workshop using the visual language and QA guidance from
[Ian Xiaohei Illustrations](https://github.com/helloianneo/ian-xiaohei-illustrations)
by Ian. The source skill is MIT-licensed; the workshop preserves visible
attribution as requested by its notice. The installed skill was audited and
pinned from upstream commit `91b560849e8f883922cc2fa8a358a668caa94105`.

## Verification

```sh
npm run lint
npm test
```

There is no completion tracker, progress bar, or browser-storage state. The guide
opens on Live; attendees can select the simulated Rehearsal instructions. It
does not require a database, account, or application secrets.
