# Factory & Workshop Review Findings

Scope: `factory/` (Python orchestrator, adapters, Control Center, tests), `workshop-guide/` (Next.js attendee site), `deploy/aws/`, `docs/`, root config. Reviewed after the Pi adapter integration on `feat/pi`.

**Overall verdict:** this is unusually disciplined code for an LLM-generated codebase. Consistent validation-at-boundary style, atomic state writes (`.tmp` + `os.replace`), list-form subprocess calls everywhere except deliberately-trusted template commands, path-traversal checks on the HTTP surface, and honest docs (`LIMITS.md` is exemplary). The findings below are real but mostly low-severity.

---

## A. Genuine bugs / defects

### A1. Test suite is not hermetic — 8 tests fail on a clean checkout (HIGH for CI trust)
`factory/tests/test_factory_runtime.py` (5 failures) and `factory/tests/test_orchestrator_qa.py` (3 failures) fail on an untouched checkout because the runtime tests execute real QA gates (`python -m pytest ...`) and the host interpreter has no `pytest` installed. The failure mode is misleading: `Causal Acceptance Test evidence failed: focused test failed for an unrelated or unclassified reason` — the classifier correctly refuses to call it RED, so the ticket ends up `Blocked` instead of `In Review`. Anyone running `unittest discover` on a fresh machine concludes the product is broken. Fix: skip (or fixture-stub) these tests when `pytest` is not importable, or declare dev dependencies and document how to run the suite.

### A2. `environment_provider.py` runs gates and setup commands with no timeout (MEDIUM)
`prepare()` (line ~203) and `health()` (line ~292) call `subprocess.run(..., shell=True)` without `timeout=`, while the orchestrator's own gate runner honors `gate_timeout` (default 300s). A hanging setup command or gate wedges the environment provider — and through the Control Center, the whole operation thread — indefinitely. Use the configured `gate_timeout` here too.

### A3. Preflight failure classification uses substring matching on adapter names (LOW–MEDIUM)
`factory/control_center.py` (~line 877): the "Inner harness" layer is chosen when the error text contains `"claude"`, `"codex"`, or `"cursor"`. Consequences:
- Any failure message that merely *mentions* one of these words (e.g. a SQL `cursor`, a log line quoting `claude`) is misclassified as an adapter sign-in problem.
- Pi is absent from the list, so Pi auth failures fall through to the generic layer and get weaker recovery guidance. Add `"pi"` and ideally match on structured error codes instead of substrings.

### A4. Invalid `.gitignore` pattern (LOW)
Root `.gitignore` ends with `../wt-*/`. Gitignore patterns cannot reference parent directories, so this line is a no-op. It happens not to matter (the `-wt-N` worktrees live outside the repo), but it signals an intent that is not actually enforced and will confuse maintainers.

### A5. `ticket_diff` rev regex permits `..` path segments (LOW)
`factory/control_center.py` `ticket_diff()`: the branch/HEAD regex `[A-Za-z0-9][A-Za-z0-9._/-]{0,255}` accepts strings like `a/../../etc`. Since the value is passed to git as a list argument there is no command injection, and the repo-root containment check limits damage, but a stricter rev pattern (reject `..` parts, as done elsewhere in the same file) would be consistent.

---

## B. Design smells / maintainability

### B1. Duplicated sources of truth for adapters
- `orchestrator.py:DEFAULT_AGENTS` duplicates the `[agents]` table of `factory/factory.toml` verbatim (both must be edited in lockstep; the Pi work had to touch both).
- `session_config.PLANNING_AGENTS` and `planning_pipeline.SUPPORTED_PLANNING_AGENTS` are two hand-maintained copies of the same set, with separate error strings ("planning_agent must be bedrock, claude, codex, or pi" vs "planning retry agent must be …"). One canonical constant (or deriving one from the other) would remove a whole class of drift bugs.
- The `{bedrock,claude,codex…}` choice lists are also re-hardcoded in the Control Center frontend (`app.js` ×2) and asserted verbatim in tests, so every adapter addition touches ~6 places. Consider exposing the planning-agent set through the snapshot API and rendering the dropdown from data.

### B2. `AgentSupervisor` carries Codex-specific plumbing for all agents
`supervisor.py` takes `codex_bin` and formats every template with a `codex=` placeholder regardless of which adapter is selected. Harmless today (unused placeholders are ignored by `str.format`), but the naming leaks one vendor into a supposedly adapter-agnostic module. Rename to something like `agent_bin` / pass a dict of resolved binaries.

### B3. Pi-specific inconsistencies introduced with the new adapter (self-review)
- The `pi` ticket template invokes bare `pi` from `PATH`, while Codex templates use a resolved `{codex}` binary (`FACTORY_CODEX_BIN`, ChatGPT-app fallback). `FACTORY_PI_BIN` therefore only affects the *planning* role, not implementation/QA/supervisor/review. Either give pi a resolved placeholder or document the limitation.
- Pi planning passes the full prompt as a single argv element; Codex/Claude pipe via stdin. With a large PRD plus prior artifacts this can approach `ARG_MAX` (~1 MB on macOS). Switch to stdin (`cat prompt | pi -p`) for parity.

### B4. `Factory.__init__` QA selection logic is convoluted
The `--no-qa` flag is handled in the first `if/elif/else` (setting `qa_agent = None`) and then *re-checked* in a second `if/elif` where `elif args.no_qa: raise ValueError(...)`. Correct, but it reads like dead code and requires careful reasoning to prove reachability. A single normalized decision would be clearer.

### B5. SSE endpoint re-serializes the full snapshot per client per second
`control_center.py` `_events()` string-compares a full `json.dumps(snapshot())` every second per connected browser. Fine for a single-attendee workshop; would not survive a classroom on one host. Worth a comment or an incremental event log if scale ever matters.

### B6. Leftover scaffolding in `workshop-guide/`
- Empty `workshop-guide/db/` directory and `drizzle/meta/` — remains of an abandoned DB layer, confusing for contributors.
- Four deployment stacks coexist: Vercel (`.vercel/`, `vercel.json`), Cloudflare (`.wrangler/`, `worker/index.ts`), OpenAI hosting (`.openai/hosting.json`, **tracked**), and `vinext` (`.vinext/`, `vite.config.ts`). Only Vercel/OpenAI bits are tracked; a short README note saying which one is canonical would help.

---

## C. Text / content issues

### C1. Node.js version contradiction (attendee-facing)
- `workshop-guide/app/page.tsx` prerequisites: "**Node.js 20+**"
- `workshop-guide/README.md`: "Requires Node.js **22.13** or later" and `package.json` `engines: { node: ">=22.13.0" }`

An attendee on Node 20 follows the page instructions and gets an install that the package rejects. Pick one (probably 22.13) and fix the page.

### C2. Pi is missing from attendee-facing copy (staleness after the integration)
The workshop hero says "Tools: **Claude, Codex, Cursor**, or your own CLI", the capability-compare table lists only Codex and Cursor, and the troubleshooting table covers only `codex login`/`claude auth login`. Now that Pi is a first-class preset (`pi-workshop`) selectable in the Control Center connection screen, the guide should mention it (or the guide should state it lists only the worked examples).

### C3. Minor wording oddities
- `factory/README.md` quickstart and `CONFIGURATION.md` both still enumerate "Claude, Codex, Cursor" in several spots where Pi/Bedrock now also apply — mostly fixed, but a few remain in `INTERFACES.md`, `LIMITS.md`, `WORKSHOP_OUTLINE.md` ("An authenticated Claude, Codex, Cursor, or custom agent CLI").
- The capability table's "Unavailable stays unavailable" sentence is grammatical but cryptic on first read; one extra clause explaining that swapping adapters cannot grant capabilities the adapter lacks would land better.
- `WORKSHOP_NARRATIVE.md`/`FACILITATOR.md` schedule blocks sum correctly to ~3h — no issues found there.

---

## D. Security / hygiene observations (no exploitable findings)

1. **Control Center HTTP surface is well done**: loopback bind, registered-action allowlist, CSP + nosniff on assets, `MAX_BODY`/`MAX_ARTIFACT` caps, path containment on `/api/artifact` and static assets, and an access policy validated per request. No traversal found.
2. **`shell=True` usage is deliberate and documented**: adapter templates, Project Contract setup/gates, and gate commands run through `/bin/sh`, but all of these are trusted repo configuration, placeholder-validated, and the trust boundary is explicitly documented in `LIMITS.md` ("Trusted boundary"). Consistent with the stated threat model.
3. **Secrets**: `deploy/aws/config.env` (real AWS account ID + Secrets Manager ARN) is **not** tracked and is gitignored — good. `workshop-guide/.env.local` contains a short-lived Vercel OIDC dev token, also untracked; fine, but worth deleting so it never rides along in a zip/backup of the working tree.
4. **Charter integrity**: `factory.charter.toml`'s `approved_policy_sha256` verified to match the policy content (hash check passes) — no drift.
5. Credential redaction is applied before logs/errors are surfaced (`redact_credentials`), and monitor aborts if it accidentally modifies the repo — nice touches.

---

## E. Things that are notably good (for the record)

- `supervisor.py` / `code_review.py` / planning validators all enforce exact-field JSON schemas with bounded lengths — the "small interface, validated hard" pattern is applied consistently.
- Causal RED-before-GREEN acceptance-test evidence with an honest failure classifier (`acceptance_evidence.py`) that refuses to count infrastructure failures as "red".
- Atomic JSON state writes everywhere; supervisor decisions journaled with input hashes and bounded repair loops.
- `monitor.py` self-check ("Monitor modified the repository; its result was discarded").
- The workshop guide itself is genuinely well-written: dual Control Center/CLI paths per step, real troubleshooting table keyed to exact `[FAIL]` strings, honest scope notes.

---

## Priority summary

| # | Finding | Severity | Effort |
|---|---------|----------|--------|
| A1 | Non-hermetic tests fail on clean checkout | High (trust) | Small |
| A2 | No timeout on environment-provider gates/setup | Medium | Small |
| A3 | Substring-based failure classification; no `pi` | Low–Med | Small |
| C1 | Node 20 vs 22.13 contradiction | Medium (attendee-blocking) | Trivial |
| C2 | Pi missing from attendee copy | Low | Small |
| B1 | Duplicated adapter registries (~6 places per addition) | Medium (drift) | Medium |
| B3 | FACTORY_PI_BIN scope + argv-size caveat for Pi | Low | Small |
| A4 | Invalid `../wt-*/` gitignore line | Low | Trivial |
| A5 | Permissive rev regex in `ticket_diff` | Low | Trivial |
| B6 | Leftover db/drizzle + 4 deploy stacks in guide | Low | Trivial |
