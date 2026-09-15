# Factory agents: tasks, inputs, outputs, and prompts

The Standard workshop uses four planning roles and three delivery roles:

```text
PRD → Product Review → human approval
    → System Architecture → Program Design → Vertical Slices
    → human review and publication of tickets

For each dependency-ready ticket:
QA → test review, when required → Implementation → automated verification
   → Code Review → human merge
                     │
                     └─ changes requested → Implementation → verification → review again
```

An agent role is an assignment, not a permanent employee or a separate model.
The same configured provider can perform several roles through separate
invocations. Independent QA means a separate assignment with protected test
ownership; it does not guarantee a different model or eliminate shared blind spots.

This reference describes the implementation inspected on 7 September 2026.
It describes which agents **can run**, not which processes are running now.
The source of truth is the prompt builders, [role contracts](roles.json), and
[profile definitions](factory_contracts.py).

## Which agents run in each profile?

| Role | Lean | Standard | Assured | Autonomous Demo |
| --- | --- | --- | --- | --- |
| Product Review | Yes | Yes | Yes | Yes |
| System Architecture | — | Yes | Yes | Yes |
| Program Design | — | Yes | Yes | Yes |
| Vertical Slices | Lean prompt | Yes | Yes | Yes |
| Independent QA | — | Yes | Yes | Yes |
| Implementation | Yes | Yes | Yes | Yes |
| Code Review | — | Yes | Yes | Yes |
| Supervisor: dispatch and merge checkpoints | — | — | Yes | Yes |
| Cleanup | — | — | Yes | — |
| Architecture Conformance | — | — | Yes | — |
| Hardening | — | — | Yes | — |
| Critic | If deep verification | If deep verification | If deep verification | If deep verification |
| Final Verifier | — | — | Yes | — |

The Critic is selected by the ticket's effective `deep` verification level, not
only by the Assured profile. The Charter's consequence tier, gate level, and
affected paths determine that level. See [triage.py](triage.py).

Lean, Standard, and Assured keep human merge authority. Autonomous Demo requires
explicit opt-in and remains subject to Charter and path-policy restrictions.
A Supervisor recommendation cannot waive those restrictions.

Rehearsal uses deterministic fixtures and mock adapters. It demonstrates the
workflow without invoking these live AI providers.

## How prompts are assembled

There is no single “factory prompt.” Each invocation receives an assignment
built from the current ticket or planning stage.

The prompt blocks below are **verbatim instruction excerpts**, except that
runtime values are represented by `{placeholders}` and long lines are wrapped.
They are not complete, standalone prompts. The saved prompt contains the actual
PRD, ticket, policy, and other applicable context.

Every role receives a contract rendered by `role_input()` in
[factory_contracts.py](factory_contracts.py). It includes:

- Ownership: what this role may do.
- Exclusions: what it must not do.
- Verification responsibility: what it must check or report.
- Handoff Receipt: what the next stage needs.
- Applicable engineering, workflow, and repository rules from [policy.json](policy.json), with hashes.

The factory reads a target repository's `factory/roles.json` and
`factory/policy.json` when present; otherwise it uses the bundled files.
Project Contract and approved Factory Charter context are also included by the
prompt builders.

The factory writes handoff receipts around the invocation and its checks.
An agent's claim is not itself a successful gate, human approval, or merge receipt.
Provider tools and system instructions can add another layer; saved assignment
prompts are not a transcript of hidden reasoning or every provider instruction.

## Planning agents

All four use `stage_prompt()` and `_run_stage_agent_impl()` in
[planning_pipeline.py](planning_pipeline.py). Each returns a complete JSON object
matching its [planning schema](planning_schemas). The factory validates it,
saves it, and renders a Markdown review document. The expert does not publish
GitHub issues itself.

All planning prompts include this shared instruction:

```text
Use the repository only as implementation context; product scope comes from
the PRD and approved upstream artifacts. Preserve stable IDs exactly. Every
new object ID must start with an uppercase letter and contain only uppercase
letters, digits, underscores, or hyphens (for example USER_HOME_COOK or
COMPONENT_API). Ticket keys follow the same rule and must be at most 16 characters.
Inspect the current codebase when technical or file-level detail is required.
Do not invent scope. Put decisions that require a human in blocking_questions.
Return only JSON matching the supplied schema. This artifact is an auditable
contract for the next expert.
```

### 1. Product Review

**Task:** Turn the PRD into an explicit statement of product intent. Surface
questions before technical planning begins.

**Input:** Source PRD, repository inventory and Project Contract, approved Charter,
role contract, and applicable policy. A revision also receives the current
artifact and human feedback.

**Output:** `01-product-review.json` and its factory-rendered `.md` counterpart.
The artifact contains the problem, users, scope, journeys, requirements with
stable IDs and PRD sources, success evidence, assumptions, and blocking questions.
A person approves the product intent before technical planning continues.

**Prompt:**

```text
You are the Product Review expert. Clarify the problem, users, observable
behavior, scope, journeys, success evidence, mockup needs, assumptions, and
blocking questions. Give requirements stable IDs R1, R2, and so on. Cite the
PRD section or phrase in each requirement's source. Do not design architecture
or create implementation tickets.
```

Schema: [product_review.json](planning_schemas/product_review.json).

### 2. System Architecture

**Task:** Define how components work together to deliver the approved product.

**Input:** Source PRD, Product Review, repository context, Charter, role contract,
and policy. The agent can inspect the existing codebase through its adapter.

**Output:** `02-system-architecture.json` and rendered `.md`: components,
ownership, contracts, data models, decisions, constraints, risks, and blocking
questions. Requirements must have owning components.

**Prompt:**

```text
You are the System Architecture expert. Inspect the existing repository and,
using the approved product review, define components, ownership boundaries,
data models, explicit component contracts, architectural decisions,
constraints, and risks. Map every item to product requirement IDs. Every
requirement must have an owning component. Do not assign tickets or write
low-level implementation code.
```

Schema: [system_architecture.json](planning_schemas/system_architecture.json).

### 3. Program Design

**Task:** Translate architecture into a code-level design that implementation
agents can follow without inventing the interfaces independently.

**Input:** PRD, Product Review, System Architecture, repository context, Charter,
role contract, and policy.

**Output:** `03-program-design.json` and rendered `.md`: modules and paths,
types, function signatures, call flows, errors, test seams, and traceability IDs.

**Prompt:**

```text
You are the Program Design expert. Inspect the existing code and turn the
approved architecture into a concrete code design: modules and paths, types,
function signatures, call relationships, error behavior, call flows, and test
seams. Use stable IDs (MOD-, TYPE-, FN-, FLOW-, TEST-), reference contracts and
requirements, and prefix calls outside this design with external:.
modules[].components must contain only component IDs copied from System
Architecture. Never put function IDs, type IDs, constants, or prose in
modules[].components. Every type and function module reference must name a
MOD- ID defined in this artifact. Do not create tickets.
```

Schema: [program_design.json](planning_schemas/program_design.json).

For live generation, the factory writes a run-specific schema that restricts
references to the exact IDs from validated upstream artifacts. Module, type, and
function `notes` hold rationale and constraints and appear in the Markdown
review. Invalid structured output returns to the same read-only expert with its
validation error and rejected response, for at most two automatic repairs within
the Charter retry limit. Repair instructions require preserving scope and
unanswered human questions; repairs do not approve artifacts. See each stage's
`repair_history` in the manifest for evidence.

### 4. Vertical Slices

**Task:** Divide the aligned plan into implementable, end-to-end tickets.

**Input:** PRD and all available upstream planning artifacts, repository context,
ticket-count limits, default implementation provider, Charter diff budget, role
contract, and policy. The prompt lists exact allowed contract and program-element
IDs for full planning profiles.

**Output:** `04-vertical-slices.json` and rendered `.md`: ticket titles and scope,
acceptance criteria, dependencies, file ownership, required evidence, and links
to requirements and design elements. The factory checks coverage, cycles,
references, and overlapping ownership. It builds traceability and review
documents from the artifacts. Human approval and publication happen separately;
producing this JSON does not start implementation.

**Prompt:**

```text
You are the Vertical Slices expert. Divide the aligned product, architecture,
and program design into {minimum}-{maximum} small end-to-end tickets. Each
ticket must deliver an observable vertical outcome, own explicit files, name
QA evidence, and map requirement, contract, and program-element IDs. Every
program element and requirement must have an owner. Each ticket must be
implementable within {max_diff_lines} implementation-owned changed lines;
independently authored protected QA acceptance tests are measured separately.
Split a ticket when its production implementation is likely to exceed that
measurable limit. Overlapping file ownership is allowed only when one ticket
depends on the other. Keep the dependency graph acyclic and maximize safe
parallel work. Default agent to {default_agent}.
```

Lean replaces that role instruction with:

```text
You are the Vertical Slices expert for the Lean Factory Profile. Divide the
approved product intent into {minimum}-{maximum} small end-to-end tickets.
Each ticket must deliver an observable outcome, own explicit files, name
evidence from existing tests, and map product requirement IDs. Each ticket
must be implementable within {max_diff_lines} implementation-owned changed
lines; split work that is likely to exceed that measurable limit. Set
contract_ids and program_element_ids to empty arrays because this profile
intentionally omits architecture and program-design roles. Keep dependencies
acyclic and default agent to {default_agent}.
```

Schema: [vertical_slices.json](planning_schemas/vertical_slices.json).

### Planning revisions and validation retries

Requesting a change reuses the selected expert; there is no separate revision
agent. The prompt adds the current artifact and human feedback:

```text
Revise only the {stage} artifact. Treat the human decisions as authoritative,
resolve the answered blocking questions in the artifact, and preserve stable
IDs unless the feedback explicitly makes one invalid. Keep a question blocked
only when the feedback does not provide the decision needed to resolve it.
```

For an invalid structured result, the retry instead includes the validator error
and, when available, the rejected artifact:

```text
The previous structured artifact was rejected by the deterministic validator.
Return a complete corrected replacement; do not merely explain the error.
```

The Control Center pauses for review after a revision. Confirming continuation
regenerates affected downstream work. See [PLANNING.md](PLANNING.md).

## Delivery agents

These agents operate on the selected target repository, not necessarily the
factory source repository. Their prompt builders are in
[orchestrator.py](orchestrator.py).

### 5. Independent QA

**Task:** Write executable acceptance tests before implementation. Test public
behavior and the ticket's criteria, not the implementation agent's interpretation.

**Input:** Ticket body, delivery planning context, repository and Charter context,
configured test roots and filename patterns, later verification gates, role and
policy rules, and any Supervisor instruction. Retries can include failed drafts,
runner diagnostics, or human test-review feedback.

**Output:** New acceptance-test files within allowed roots. The factory builds
the focused test command, checks that it fails for a missing-behavior assertion,
and commits and protects the accepted files. The agent must not commit them.
Already-green tests, collection errors, missing dependencies, skips, and timeouts
do not count as valid RED evidence. Human test approval is a separate gate when
configured.

**Prompt excerpts** from `make_qa_prompt()`:

```text
Act as the independent QA engineer before implementation begins. Translate
the ticket's acceptance criteria into deterministic executable acceptance
tests. Inspect production code only to understand public behavior; do not
implement or repair the feature.
```

```text
Include at least one assertion that detects behavior missing at the assigned
base revision. The factory runs the exact new files before implementation and
accepts red evidence only for a behavior assertion failure. Already-passing,
skipped, uncollectable, timed-out, or infrastructure-broken tests are rejected.
```

The full test-file contract also requires deterministic, offline tests; covers
failure and boundary cases; forbids production changes and changes to existing
files except explicitly listed unaccepted drafts; and forbids assertions that
later approved slices' capabilities must remain absent.

### 6. Implementation

**Task:** Implement one ticket and repair its rejected candidates within the
approved scope and diff budget.

**Input:** Ticket body, delivery planning context, current worktree, Project
Contract, Charter, required gates, existing-test policy, protected QA paths and
focused command, role contract, attached review evidence, and optional Supervisor
coordination. Retries add previous failure details and any human retry direction.

**Output:** Committed production changes and implementation-owned tests. When
the ticket requires a report, an uncommitted `.factory/review-handoff.md` contains
the candidate SHA (full, or abbreviated to at least 7 characters of the same
value), actual checks, artifact paths, and unresolved work. The
factory snapshots that report as implementation-authored evidence, not approval.

**Prompt excerpts** from `make_prompt()`:

```text
Make the implementation pass them. You may add other tests, but do not edit,
rename, delete, skip, or weaken the protected tests; the factory verifies their
Git hashes.
```

```text
Commit as `factory(#{ticket_number}): <summary>`.
```

```text
Work only in the current worktree. Do not change ticket scope.
```

The role's ownership instruction is:

```text
Production code and implementation-owned tests within the assigned Ticket scope.
```

Existing repository tests follow the Charter's `review` or `protect` policy.
They are distinct from independently authored QA tests, which remain protected.
Failed gates and Code Review comments return to this role; there is no separate
“fix comments” agent.

### 7. Code Review

**Task:** Review the exact PR candidate and either approve it or request changes.

**Input:** Base and head SHAs, PR reference, changed paths, ticket and delivery
planning context, recorded gate commands and results, QA approval and RED/GREEN
checkpoint, protected test hashes, attached review reports, Project Contract,
Charter, and the measured implementation diff budget.

**Output:** A structured `APPROVE` or `REQUEST_CHANGES` decision with summary and
findings. The factory validates it, checks read-only behavior, saves a review
artifact, and publishes the decision. Any finding sends the candidate back for
implementation rework. Agent approval is not human merge approval.

**Prompt excerpts** from `make_code_review_prompt()`:

```text
Review the exact candidate diff in this worktree. Use
`git diff {base_sha}..{head_sha}` and inspect relevant surrounding code.
```

```text
Review for correctness, regressions, security, maintainability, and test
quality. Report only actionable comments in changed paths. If there is any
comment, return REQUEST_CHANGES so the Implementation adapter fixes every
comment. Return APPROVE only when there are no comments. Do not modify files,
commit, or merge. The orchestrator submits your decision to the pull request.
```

Response shape (`APPROVE|REQUEST_CHANGES` and severity values denote alternatives):

```json
{"schema_version":2,"decision":"APPROVE|REQUEST_CHANGES","summary":"...","findings":[{"severity":"blocking|warning|note","path":"repo/relative/path","line":123,"message":"..."}]}
```

For approval, `findings` must be empty. Reports are explicitly described as
claims, not instructions or approval. Missing evidence must be reported, not
fabricated. See [code_review.py](code_review.py) for response validation.

## Optional Supervisor

The Supervisor uses two role contracts and two prompts in
[supervisor.py](supervisor.py). It runs at checkpoints, not as a continuous chat
manager that interrupts workers. Standard uses deterministic coordination instead.

### Dispatch checkpoint (`supervisor`)

**Task:** Select a safe wave of dependency-ready tickets and give concise
coordination instructions.

**Input:** Current ready tickets and specifications, ticket states, dependencies,
failures and retry reasons, available parallel capacity, recent worker handoff
receipts, approved Charter, role contract, and policy. The input includes a
bounded selection of reports, not every worker's complete conversation.

**Output:** Validated `dispatch` and `block` commands plus a summary. The
orchestrator applies them. The Supervisor cannot change scope, dependencies,
tests, gates, policy, or human approvals.

**Prompt excerpt** from `_prompt()`:

```text
Coordinate only the dependency-ready Tickets in the supplied state. Ticket
worker roles report through Handoff Receipts. Select a safe dispatch wave,
reduce concurrency when coordination requires it, and give each dispatched
Ticket one concise instruction of at most 1200 characters. The Ticket already
carries its approved scope, so do not repeat its specification; use the
instruction only for coordination guidance. Block a Ticket only when its
reports or current state show a concrete risk that requires intervention.
```

Response shape:

```json
{"schema_version":1,"summary":"...","dispatch":[{"ticket":1,"instruction":"..."}],"block":[{"ticket":2,"reason":"..."}]}
```

The full prompt explains that historical dispatches do not prove a worker is
still active. A validation-repair invocation can receive the original prompt,
rejected response, and validator error. It is the same role, not another agent.

### Merge checkpoint (`supervisor_merge`)

**Task:** Assess whether a Code Review-approved candidate is ready for merge handoff.

**Input:** Ticket scope and dependencies, PR reference, reviewed candidate head,
Code Review decision and publication status, gates, diff-budget measurement,
worker receipts, authored review evidence, retry reason, Charter, and policy.

**Output:** A revision-bound `MERGE` or `BLOCK` recommendation. Assured still
requires human merge. Autonomous Demo can let the orchestrator execute an
authorized merge when all configured restrictions permit it. The agent never
runs the GitHub merge command itself.

**Prompt excerpt** from `_merge_prompt()`:

```text
Return MERGE only when all evidence refers to the same candidate and no
blocking risk remains. Return BLOCK otherwise. MERGE is a readiness
recommendation, not permission to execute a merge. When the Charter or path
policy requires human merge authority, MERGE sends the exact revision to human
review; it does not supply that approval. Do not BLOCK solely because human
approval is still pending. Block missing or inconsistent evidence and
substantive unresolved risks. You do not run GitHub commands; the orchestrator
validates the recommendation and retains the configured human approval gate.
```

Response shape:

```json
{"schema_version":1,"summary":"...","action":"MERGE|BLOCK","ticket":1,"pull_request":"https://github.com/.../pull/1","candidate_head":"full-git-sha"}
```

## Additional review and improvement agents

These roles share `make_role_prompt()` and `run_profile_role()` in
[orchestrator.py](orchestrator.py). They use the ticket's implementation adapter,
not the separately configured Code Review adapter.

**Common input:** Ticket body, delivery planning context, current candidate
worktree, Project Contract, approved Charter, role-specific contract and policy,
optional Supervisor instruction, and any previous role failure.

Unlike the dedicated Code Review prompt, this shared builder does not append
the structured gate-results and QA-checkpoint payload. Do not assume every
review role receives the same evidence bundle.

Each role's ownership text below is copied from [roles.json](roles.json).
Its exclusions, verification responsibilities, and handoff requirements are
also rendered into the full prompt.

| Role | Task / ownership prompt | Additional boundary | Output |
| --- | --- | --- | --- |
| Cleanup (`cleanup`) | “Readability and maintainability improvements within the implemented Ticket diff.” | No behavior changes, protected-test changes, or unrelated cleanup. | Scoped cleanup changes and a PASS/BLOCK verdict. |
| Architecture Conformance (`architecture_conformance`) | “Read-only comparison of the implementation with approved architecture contracts.” | No file modifications. | Conformance assessment or precise deviations, with a PASS/BLOCK verdict. |
| Hardening (`hardening`) | “Ticket-scoped reliability, error handling, and security improvements justified by identified risk.” | No protected-test changes or scope expansion. | Scoped hardening changes, residual risks, and a PASS/BLOCK verdict. |
| Critic (`critic`) | “Read-only adversarial review of propagated assumptions, untested behavior, scope drift, dead code, and maintainability risk for deep-verification changes.” | No file modifications or lifecycle decisions; distinguish concrete findings from speculation. | Candidate assessment, evidence references, risks, and a PASS/BLOCK verdict. |
| Final Verifier (`final_verifier`) | “Read-only final assessment of requirements, policy, protected evidence, and gate results.” | No file modifications or acceptance of unresolved blocking risk. | Final assessment, evidence references, risks, and a PASS/BLOCK verdict. |

Their shared prompt ends with:

```text
Work only within this Ticket handoff. The orchestrator owns lifecycle state.

End the response with exactly one structured verdict line:
`FACTORY_ROLE_VERDICT: PASS` or `FACTORY_ROLE_VERDICT: BLOCK: <reason>`.
```

Assured runs Cleanup → Architecture Conformance → Hardening after implementation.
The factory then runs verification, the Critic when deep verification is selected,
Assured's deterministic negative proof, and the Final Verifier before Code Review.
If Final Verifier blocks, the code permits a Hardening correction, reruns checks,
and invokes Final Verifier again.

## Components that are not AI agents

Some names in `roles.json` describe evidence ownership, not model invocations.

| Component | Input | Work and output | Prompt |
| --- | --- | --- | --- |
| Verification (`verification`) | Candidate revision, protected tests, accepted focused command, configured gates | Runs commands and records RED/GREEN evidence, exit status, output, and timings. | None. Deterministic code. |
| Negative Proof (`negative_proof`) | Candidate, QA revision, accepted focused command | Reverses candidate production changes in a disposable worktree and checks that the behavior assertion fails again. Records the result. Assured only. | None. Deterministic code. |
| Human Review (`human_review`) | Exact candidate, diff, receipts, tests, review and gate evidence | A person merges, requests changes, or stops. | None. Human decision. |
| Orchestrator and triage | Tickets, dependencies, policy, current state | Select readiness and controls, run adapters, validate outputs, retry or block, and record state. | None for coordination itself. Invokes role prompts where configured. |
| Repository monitoring, issue listening, and merge stewardship | Repository events, issue/PR state, candidate revisions | Observe, reconcile, synchronize, and reverify through configured workflows. | Not separate AI roles. |

The Control Center and workshop website are interfaces, not agents. GitHub
Projects synchronization is also code, not another planning or management model.

## Find the full prompt and result for a run

Look in the **target repository** used by the run. In managed Live mode this can
be a checkout under `.factory/repositories/`, not the control-plane checkout.

| Assignment | Saved prompt under `.factory/prompts/` | Main result |
| --- | --- | --- |
| Planning | `planner-{plan_id}-{stage}.md` | `.factory/plans/{plan_id}/01-product-review.json` through `04-vertical-slices.json`, plus rendered documents and manifest. |
| Planning revision | `planner-{plan_id}-{stage}-revision-{revision}.md` | Revised artifact and revision history. |
| QA | `{ticket}-qa-attempt{attempt}.md` | Test files, QA commit, and evidence in factory state and receipts. Later test revisions include `-qa-revision{revision}-attempt{attempt}`. |
| Implementation | `{ticket}-attempt{attempt}.md` | Ticket-branch commits and optional snapshotted review handoff. |
| Code Review | `{ticket}-code-review-attempt{attempt}.md` | `.factory/reviews/ticket-{ticket}-attempt-{attempt}.json`. |
| Additional role | `{ticket}-{role}-attempt{attempt}.md` | Worktree changes where allowed, role log, and handoff receipt. |
| Supervisor dispatch | `supervisor-{sequence}.md` | Recorded dispatch decision. Validation repair adds `-repair-1.md`. |
| Supervisor merge | `supervisor-merge-{sequence}.md` | Recorded merge recommendation. |

Prompts and logs can contain private PRD or repository content. Inspect them
locally; do not publish them without reviewing their contents. Some prompt
filenames are reused on retries or resumed runs, so this directory is not a
guaranteed append-only transcript. Use manifests, revision records, and receipts
to identify the relevant candidate and attempt.

From the target repository, list the available artifacts:

```sh
ls .factory/prompts
ls .factory/logs
ls .factory/receipts
```

Then open the exact prompt file for the role and attempt you want. To change how
an agent is instructed, start with its prompt builder and role contract, not the
generated runtime file. Provider selection is separate: see
[Factory configuration](README.md) and [adapter interfaces](INTERFACES.md).
