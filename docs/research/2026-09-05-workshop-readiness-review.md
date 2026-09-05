# Software (re)-Factory: three-hour workshop readiness review

Date: 5 September 2026

Audience: workshop owner, maintainers, and facilitators

Reviewed revision: `b80bf38ca55bfae461f9c738ae8c5688a592f94a` on `main`

Release reference: `workshop-v1.2.1`; the reviewed revision includes subsequent website-copy changes.

Implementation update: the original review below describes that revision. See
[the implementation disposition](#implementation-disposition) for the changes
on `codex/workshop-simplify-readiness`. The owner's later direction supersedes
two recommendations: the website explains **how**, while slides explain **why**;
website completion tracking is removed, not repaired.

Subsequent exercise decision: the owner selected the full Pocket Cinema →
TableStory product transformation as the main exercise, superseding R04's
small-change curriculum recommendation. Both Live and Rehearsal use
[`recipe-app-prd.md`](../../recipe-app-prd.md). The genre-search PRD remains an
optional example. Completion means the approved transformation scope is merged
and integrated acceptance checks pass; unfinished Live work needs an explicit
resume point. The original assessment below is retained as historical context.

## Executive assessment

The factory is a credible teaching implementation with unusually useful review and verification controls. The current workshop does not yet make those controls easy enough to understand, exercise, and reuse in three hours.

The highest-value lesson is not that several agents can build a recipe application. It is that a team can turn a request into a sequence of reviewable decisions, attach evidence to a specific change, and retain authority over what enters its codebase. This is relevant to engineers, tech leads, and CTOs even if they already use coding agents.

I would keep this project as the workshop foundation. I would not yet describe the current guide as a reliably self-guided, three-hour experience for first-time attendees. Two interface defects were reproduced, the website and facilitator plan disagree on the primary path and completion criteria, and the activity that connects the workshop to attendees' own work receives only five minutes.

The next investment should be in reliability and teaching design, not additional agents, cloud providers, or autonomous features.

### The five most important changes

1. **Make the interfaces tell the truth.** Fix fresh-start readiness and website progress persistence. Distinguish a learner's checklist from an actual factory run.
2. **Choose one classroom route and one achievable result.** Use Standard Live with each attendee's own repository, as the existing plan specifies. Provide a clearly labeled Rehearsal fallback. Make one complete, user-visible slice the core result; treat the full rebrand as an extension.
3. **Replace passive approvals with decisions.** Every attendee should reject one inadequate proposal, distinguish a behavior failure from a broken test environment, and identify the exact revision they would permit to merge.
4. **Make setup and recovery executable by a novice.** Show the checkout, action, expected output, and recovery for each instruction. Fix copyable placeholders and ambiguous dependency repairs. Use screenshots of the actual decision state.
5. **Reserve meaningful time for application and economics.** Attendees should leave with a bounded pilot proposal, a verification strategy, an accountable owner, and a way to judge cost and benefit—not just a list of architectural layers.

### What a successful attendee should leave with

| Audience | Useful result from the session | Evidence that they learned it |
| --- | --- | --- |
| Engineer | A repeatable path from a bounded requirement to a tested, reviewed change | Can trace one requirement through a ticket, acceptance test, implementation, and reviewed commit; can recover from one failure |
| Tech lead | A delivery policy that fits review capacity and repository risk | Can explain what pauses the factory, who resolves it, and why another agent is not a substitute for an independent check |
| CTO | A defensible decision about where to pilot a factory | Can name a suitable use case, compare it with the existing workflow, identify operating costs and limits, and assign an owner |

These are different outcomes within one shared exercise. The workshop should not become three separate tracks.

## 1. Scope, method, and confidence

This review covers the Python factory and its contracts, the browser Control Center, the workshop guide, the facilitator materials, the sample exercise, release checks, and configured CI. It includes source inspection, local automated checks, and browser walkthroughs.

The walkthrough used a disposable local clone for factory state and mock execution. It did not modify an attendee repository or the working repository's current run. No paid coding agent, GitHub publication, AWS deployment, or production website deployment was performed.

### Verification performed

| Check | Result | What the result establishes |
| --- | --- | --- |
| `python -m unittest discover -s factory/tests -q` using the existing factory environment | 428 tests passed | The current unit and integration-style assertions pass locally |
| Workshop guide `npm test` | Build and all 8 tests passed | The tested rendered structure, copy constraints, and local-editor assertions pass |
| Workshop guide `npm run lint` | Passed | The configured static checks pass |
| Workshop guide `npm run build:vercel` | Passed | The separate Next.js production build also compiles locally; no deployment was performed |
| `factory/orchestrator.py release-check --rehearsal` | Passed: five completed tickets, Evidence Packet, healthy Monitor | The deterministic Standard Rehearsal can complete using the release-check harness |
| Factory complexity checker | Passed its configured threshold | The repository's current complexity policy is satisfied, not that all modules are easy to change |
| Fresh Control Center browser walkthrough | Incorrect initial phase reproduced | Presentation metadata can make an unconfigured run appear ready for planning |
| Workshop guide completion and reload | Progress loss reproduced | Marking a step complete does not survive reload in the tested browser flow |
| Shell syntax check of the plan-ID example | Failed | The literal copyable `export PLAN_ID=<plan-id-from-output>` example is not valid shell syntax |

Automated success and walkthrough failures can coexist. That is an important finding: the tests cover many factory policies, but do not yet establish that a first-time attendee can navigate the complete experience.

Findings below are labeled as **reproduced**, **source-confirmed**, or **needs measurement**. Priorities indicate workshop impact, not security severity:

- **P0:** fix before presenting the guide as independently usable.
- **P1:** address before the next general beginner workshop.
- **P2:** improve maintainability, extensibility, or advanced adoption after the core journey works.

This is not a penetration test, a provider compatibility certification, or a measured learning study. Linux and WSL were not exercised on separate machines. A three-hour completion guarantee requires a timed novice dry run; no amount of source inspection can substitute for it.

## 2. What is already worth keeping

### Evidence is attached to delivery decisions

The project does more than dispatch prompts. Planning approvals, protected QA tests, verification gates, review results, and exact-revision merge decisions give attendees concrete objects to inspect. These controls are the workshop's strongest differentiator.

The materials should explain each control through a failure it prevents. For example: “This approval belongs to this commit. If the branch changes, the earlier approval is not enough.” That is more useful than introducing all receipt types at once.

### Planning is separated into useful responsibilities

Product Review, System Architecture, Program Design, and Vertical Slices create opportunities to correct the request before implementation. The first Product Review checkpoint can demonstrate that an apparently reasonable PRD still contains ambiguity.

Keep the four responsibilities. Teach them as four questions, not four impressive agent personalities:

1. What should change for the user?
2. Which components and boundaries are affected?
3. What contracts and code structure make the change implementable?
4. What independently verifiable work should be delivered first?

### The human decision is explicit

Standard and Assured retain a human exact-revision merge decision. The project also documents the limits of formal GitHub approvals when author and reviewer identities are the same. This is more credible than presenting every agent-generated approval as an independent organizational review.

### Rehearsal is a real teaching asset

The deterministic five-ticket rehearsal completed during this review, including evidence export. It provides repeatable examples when a provider, network connection, or attendee environment is unavailable.

Keep it clearly labeled. A mock change demonstrates orchestration and evidence handling; it does not demonstrate that a live model understood an arbitrary PRD. It must not be reported as an attendee's successful Live delivery.

### The project documents important trust boundaries

[Production boundaries](../../factory/LIMITS.md) correctly explains that worktrees are not security sandboxes, trusted configuration can execute shell commands, and provider behavior remains a separate boundary. It also states that unavailable usage information must not be invented.

Keep these qualifications visible in the teaching path. They make the workshop more credible to experienced engineers and CTOs.

### The writing and interface already have useful foundations

The website now has a consistent action/inspection/continuation structure, explicit Control Center launch instructions, a distinction between CONTROL and TARGET, and useful recovery examples. The [narrative](../../factory/WORKSHOP_NARRATIVE.md) already contains a strong opening based on whether a PR should merge.

The problem is not that everything needs rewriting. It is that the strongest narrative, the runnable instructions, and the operating UI have drifted apart.

## 3. Prioritized findings

| ID | Priority | Finding | Confidence |
| --- | --- | --- | --- |
| R01 | P0 | A fresh Control Center can mark setup and PRD complete without actual setup or a saved PRD | Reproduced and source-confirmed |
| R02 | P0 | Website progress resets on reload; checklist labels imply actual factory completion | Reproduced / source-confirmed |
| R03 | P0 | Live-first facilitator plan conflicts with Rehearsal-first website and conditional prerequisites | Source-confirmed |
| R04 | P1 | One-ticket completion, whole-app completion, and app availability are described inconsistently | Source-confirmed |
| R05 | P1 | Transfer and Evidence Packet activities do not fit the time or available UI | Source-confirmed |
| R06 | P1 | Several setup and recovery instructions require knowledge beginners do not have | Source-confirmed; shell example reproduced |
| R07 | P1 | QA approval is explained more confidently than the evidence warrants, and its screenshot shows the wrong phase | Source-confirmed and visually inspected |
| R08 | P1 | The guide teaches navigation better than judgment and application | Curriculum assessment |
| R09 | P1 | Control Center hierarchy and decision screens expose unnecessary interpretation work | Browser observation / source inspection |
| R10 | P1 | “Generic factory” expectations exceed current focused-test support and security boundaries | Source-confirmed |
| R11 | P1 | Operating cost and review capacity are not usable attendee exercises | Source-confirmed / curriculum assessment |
| R12 | P1 | Tests and releases do not validate the published beginner journey end to end | Source-confirmed |
| R13 | P2 | State, lifecycle, and evidence logic remain concentrated and partially duplicated | Source-confirmed |
| R14 | P2 | Snapshot streaming may repeat substantial work; resource limits need measurement | Source-confirmed architecture; impact unmeasured |

## 4. Detailed findings and recommended changes

### R01. Fresh-start readiness is derived from the wrong evidence

**Observed:** In a clean local clone with no session configuration, no saved PRD, and an environment reported as `not-provisioned`, the overview displayed Phase 3 of 6, Plan, with setup and PRD complete. The next action was Start Product Review.

**Cause:** In [control_center.py](../../factory/control_center.py), `snapshot()` adds `presentation` and compatibility fields to an initially empty planning dictionary, around lines 1454–1470. `journey()`, around lines 1175–1198, treats `bool(planning)` as evidence of connection, environment readiness, and an existing PRD. Presentation-only fields therefore satisfy workflow checks.

The setup panel can simultaneously report that connection settings are unsaved. A beginner cannot determine which view to trust.

This demonstrates an incorrect readiness display. It does **not** establish that the backend allows an unauthorized merge or bypasses every setup check.

**Change:** Derive readiness from explicit domain facts: a configured target, valid contract, approved policy, required preparation result, saved PRD, and a real planning run identifier. Do not infer persisted workflow progress from a dictionary containing display metadata. Produce one readiness result for both the overview and setup screen.

**Acceptance:** An end-to-end snapshot test and a browser test must start from an empty runtime directory. Both views must identify Connect as the next step. Adding presentation fields must not change completion. Existing runs and imported state must retain supported recovery behavior.

### R02. Website completion is neither persistent nor actual factory state

**Observed:** Marking Setup complete changed the guide from 0 of 8 to 1 of 8, or 13%. Reloading returned it to 0 of 8.

**Cause:** [page.tsx](../../workshop-guide/app/page.tsx), lines 183–209, schedules restoration from local storage with a timer. Separate effects write the initial empty completion list and default Rehearsal track before that delayed restoration reads them. The selected track uses the same problematic pattern; progress loss was directly tested.

The keys are also not scoped by release or track. The completion panel says “Factory progress” and “Factory complete,” although it only counts manually marked website steps. It is not connected to execution state.

**Change:** Restore and validate saved state before enabling persistence. Scope it appropriately and give attendees an explicit reset action. Label the result “Workshop checklist” or “Your learning progress.” The hosted guide does not need privileged access to the local factory simply to fix this distinction.

**Acceptance:** Reload preserves the chosen route and checked steps; malformed storage does not crash the page; changing routes follows an explicit policy; 100% checklist completion does not claim that a real run finished.

### R03. The workshop has competing primary routes

The [three-hour plan](../../factory/WORKSHOP_PLAN_3_HOURS.md), under Recommended operating mode, specifies Standard Live, every attendee's own disposable repository, GitHub Projects, and human merge. The website initializes to Rehearsal and marks it “Recommended first.”

On the website, route selection follows the prerequisites. Some GitHub and provider authentication commands appear only for Live. Selecting Live scrolls directly to Setup, potentially skipping the prerequisite commands that have just become relevant.

Both modes are useful. The problem is making attendees reconcile the choice while the facilitator follows a different default.

**Change:** Publish a session-specific starting route, selected before route-dependent requirements. The scheduled workshop should use Standard Live as already agreed. Every attendee should still create and own a repository, and the facilitator should use a separate one. Use Rehearsal as a labeled alternate path when needed, not as an undisclosed change to the promised outcome.

For independent study, Rehearsal can remain a reasonable recommendation on a separate entry path. Do not mix that recommendation with the scheduled session's instructions.

**Acceptance:** The invitation, guide, facilitator agenda, starting UI, and screenshots name the same route. A person arriving at the session link sees all of that route's prerequisites before executing setup.

### R04. The completion promise changes between steps

Website Step 7 requires at least one ticket to reach Done. Step 8 asks the attendee to inspect the completed TableStory app and says the Run app page becomes available when every ticket is Done. The backend journey also uses all tickets Done as its delivery-completion condition.

However, the application-entrypoint and rendering code can expose an application independently of every ticket being complete. The problem is an inconsistent teaching and completion contract, not a demonstrated hard lock on opening the app.

The sample's five tickets include dependencies across several waves. A working API ticket or design shell is not the same as the complete mobile, desktop, and TV rebrand.

**Change:** Define a core result that fits the session: one end-to-end, user-visible capability, with the evidence and merge decision inspected. Clearly distinguish baseline preview, partial implementation, and completed product. Make the remaining rebrand work an extension. Prepare a finished run for demonstrating integration without claiming that an attendee's unfinished branch is complete.

**Acceptance:** The facilitator and guide use the same definition of success. The sample's selected core slice actually produces observable behavior. The UI states which revision and level of completeness it is previewing.

### R05. The personal application activity is squeezed out—and evidence export is disconnected

The final five minutes of the plan require attendees to answer eight use-case questions, fill a five-row architecture decision table, exchange peer feedback, and answer three closing questions. That is not a credible allocation for first-time learners.

There is also an ordering mismatch. The agenda exports an Evidence Packet at 168–175 minutes and completes the Canvas at 175–180. [evidence_packet.py](../../factory/evidence_packet.py) requires a Canvas with 16 nonempty, non-placeholder sections before export.

The Control Center still implements Canvas read/write endpoints and an evidence action. Its current HTML and JavaScript do not expose a corresponding Canvas editor or Evidence Packet export workflow. These are not wholly dead backend capabilities; they are inaccessible through the normal interface promised to attendees. The website's transfer section lists the five layers without an activity or usable artifact.

**Change:** Allocate 20 minutes to a short personal pilot worksheet and peer review, plus a separate cost/evidence discussion. Make the run's evidence accessible from the UI. Separate “what this run proved” from “how I would adopt a factory.” If policy requires a complete governance Canvas, explain and complete it before export rather than surprising attendees at the end.

Keep the longer Canvas as an advanced planning artifact. A beginner should not have to invent 16 governance answers before seeing the evidence they just generated.

**Acceptance:** A Control Center-only attendee can open and export the intended learning evidence. The agenda follows the real prerequisites. Every attendee finishes a personal artifact during the session, not as an optional afterthought.

### R06. Setup is clearer, but still assumes too much

The three-step setup is a good improvement. The remaining problems are small individually but expensive when multiplied across a classroom.

| Current instruction or behavior | Why it can stop a novice | Recommended correction |
| --- | --- | --- |
| Clone the repository's default branch while the page displays release 1.2.1 | Guide, code, and screenshots can describe different revisions | Provide a pinned session release and visibly identify the guide/runtime pair |
| `export PLAN_ID=<plan-id-from-output>` | Copying it literally produces shell syntax failure | Use a safe quoted example with explicit replacement instructions, or generate the command from the actual run |
| `gh project view <project-number>` | The angle brackets are shell syntax, not a placeholder mechanism | Provide a populated command or a named variable with a valid assignment |
| `open recipe-app-prd.md` | macOS-specific despite Linux and WSL support claims | Use the Control Center editor, or provide explicitly labeled platform alternatives |
| CONTROL and TARGET variables established in one terminal | A second terminal does not inherit those shell variables | Identify which terminal to use or repeat the exact environment initialization |
| “Install the dependency with the repository's normal setup command” for missing pytest | The attendee may not know the command, checkout, or Python environment | For the guided starter, show the exact supported repair and interpreter; for custom repositories, show the resolved contract command and where to edit it |
| Recovery commands always switch to `main` | Valid only when the product's default branch is main | Use the detected default branch, or label the example as specific to the guided repository |
| “Open ticket #1” | GitHub issue numbers need not start at 1 | Select the named ready ticket from the current plan |
| “Read-only clone” followed by commits and local modifications | “Read-only” describes neither the checkout nor the exercise accurately | Say the rehearsal modifies a disposable local clone but does not publish to GitHub |

Likewise, distinguish “mock execution makes no provider calls” from “nothing leaves your machine.” Initial cloning and dependency installation still require network access.

The beginner baseline activity also needs a visible app-launch instruction in the Control Center route. Asking people to inspect a product without teaching them how to start it turns the baseline into a screenshot exercise.

For the colleague's earlier class of failure—wrong branch, wrong selected agent, missing pytest—the recovery should answer four questions directly: **where am I, what should I change, how do I verify it, and which button do I press next?** “Retry” is only helpful after those facts are clear.

Do not repair these cases by force-resetting source, disabling gates, or installing dependencies into an unrelated global interpreter.

### R07. QA evidence needs a better explanation and the right screenshot

The website says RED PROVED means the failure occurred because the requested behavior is missing. The implementation is more limited: [acceptance_evidence.py](../../factory/acceptance_evidence.py) classifies exit codes and output markers, excluding known collection, command, timeout, and skipped-test cases.

That is useful evidence, not a semantic proof that the test correctly captures the PRD. A deliberately irrelevant assertion can still fail. A reviewer must inspect what is asserted and why that failure represents missing behavior.

The screenshot used for pre-implementation QA approval, [control-center-ticket-tests.jpg](../../workshop-guide/public/screenshots/control-center-ticket-tests.jpg), shows a ticket already In Review with GREEN PROVED. The actual QA Review state inspected during this review showed RED PROVED and GREEN NOT PROVED. The image therefore teaches the wrong moment in the workflow.

The Tests drawer lists test paths and outputs, but does not present the full proposed test code as a coherent review alongside approval. The user must move between Tests and Summary to inspect and approve.

**Change:** Create a single QA decision view with the acceptance criterion, test code or diff, command, observed baseline result, classification, and approval/revision action. Before implementation, say “Green check: not run yet” where that is the actual state. Capture a screenshot at QA Review, not after implementation.

Teach the boundary explicitly: “The runner observed a failure consistent with an assertion. Confirm that this assertion tests the requested behavior.” Later, show that the accepted test set passes on the candidate revision and has not been weakened.

**Acceptance:** A novice can explain the failing assertion without leaving the guided decision view. The screenshot matches the state and button labels. A missing dependency is never presented as sufficient RED evidence.

### R08. The material needs more judgment, not more words

The current website is better at “where to click” than “how to decide.” Prompts such as “check users, problem, behavior, and success checks” are correct but do not show what an inadequate answer looks like.

The [narrative](../../factory/WORKSHOP_NARRATIVE.md) already provides a stronger basis than the website introduction. Reuse its PR-approval opening. Show a visible outcome and ask for a decision before presenting the five-layer architecture.

A usable first definition is:

> An AI software factory is a repeatable delivery workflow that combines coding agents with repository rules, tests, review, and explicit human decisions. A request enters the workflow. Changes leave it only when the required evidence and approvals are present. The factory coordinates the work; it does not remove engineering responsibility.

Explain “why now” without claiming universal productivity gains: coding CLIs can perform substantial repository work, and existing Git/CI systems supply durable coordination and verification mechanisms. The engineering question is how to connect those capabilities so another person can reproduce and trust the result. Whether this is worthwhile depends on the task and operating cost.

For beginners, introduce each technical term immediately before its first decision. The Google technical-writing guidance emphasizes the gap between audience knowledge and what they need to learn; this is a better editing criterion than simply minimizing word count. [Google: Audience](https://developers.google.com/tech-writing/one/audience)

The recipe rebrand can remain the common exercise. Anchor it to a concrete user outcome, not cosmetic transformation. Be explicit that API and design-shell work are enabling tasks; they are not individually end-to-end user-facing vertical slices. This distinction matters if the workshop promises to teach vertical slicing.

### R09. The Control Center needs a beginner decision layer

The underlying information is valuable. The interface still asks the attendee to translate among website steps, a six-phase journey, four navigation groups, expert stages, ticket states, and several policy concepts.

The setup screen also exposes capabilities that are irrelevant to the first run. Rehearsal can show a provider preset and a stopped GitHub listener even though neither is needed for mock delivery. These details invite unnecessary troubleshooting.

**Change the information hierarchy:**

1. Show the current task: “Plan · Product Review.”
2. State who is acting: agent, factory check, or attendee.
3. Explain whether this is running, waiting normally, blocked, or awaiting a decision.
4. Show the next allowed action and the evidence needed for it.
5. Put advanced configuration, raw records, and optional integrations underneath.

Retain detailed logs and recovery tools. Do not replace them with vague progress animation. A pulse says something is alive; it does not explain whether the user needs to act.

For reset and retry, show the effect before execution: what is retained, what is regenerated, what remains on GitHub, and whether a healthy agent will be stopped. Existing recovery mechanisms deserve better explanation, not a second reset implementation.

The website has a clean visual foundation, but at a 1280-by-720 laptop viewport the two side regions leave a narrow lesson column. Large screenshots become difficult to read. Use one primary navigation region and compact checklist progress during exercises. Provide cropped, numbered images for decisions, while retaining the full-resolution reference.

Source inspection also suggests an accessibility follow-up: the ticket drawer uses an aside rather than an explicit dialog pattern, and focus trapping/restoration and tab semantics need verification. This is not a completed screen-reader audit. Test the actual keyboard journey before making accessibility claims.

### R10. Separate general orchestration from supported verification

The factory can model and connect repositories beyond the sample. That does not mean every language and test framework receives the same acceptance-evidence workflow.

`focused_test_command()` in [acceptance_evidence.py](../../factory/acceptance_evidence.py) currently supports Python pytest files or Node's built-in test runner with JavaScript extensions. Mixed sets and unsupported extensions are rejected. A Go, Java, or native TypeScript test suite therefore needs an explicit integration strategy, not just a new PRD.

Likewise, a configurable adapter is not proof of an enforced sandbox. The production-boundary documentation correctly distinguishes declared execution capabilities from the implementation that enforces them.

**Change:** Publish a small capability table: repository intake, planning, implementation adapter, focused acceptance runner, review, execution isolation, and usage reporting. Mark each as supported, configurable with additional work, or not established. During setup, validate the chosen verification path before planning an unsupported Standard run.

A future test-runner interface should return structured collection, assertion, skipped, and infrastructure results. Until then, explain the supported Python/JavaScript route and its limits. Do not hide unsupported ecosystems behind generic language.

Also explain that separate QA and review roles can use the same provider and model. Role separation reduces some conflicts of responsibility; it does not guarantee independent reasoning or eliminate correlated mistakes.

### R11. Add an operating-cost and review-capacity exercise

The code already records useful operational data in [run_summary.py](../../factory/run_summary.py), including attempts, stage durations, human wait, and retry/rejection information. The adapter protocol can represent usage. The current attendee experience does not turn this into a practical cost decision.

Calling elapsed agent time “useful agent work” implies value that elapsed time alone cannot establish. A run can keep agents busy while producing no accepted outcome.

**Change:** Teach four separate measures:

- accepted user outcomes;
- agent invocations and retries by role;
- human review and recovery time;
- provider usage/cost when actually available.

Unknown token counts must remain unknown, not zero. Estimates should be labeled with their assumptions and kept separate from provider-reported values.

Use an explicit model:

> Cost per accepted change = model and execution cost + review and rework effort + allocated operating effort.

Do not add unlike units without conversion. Keep dollars, minutes, and invocation counts separate until an attendee supplies their organization's assumptions.

Let attendees compare the same bounded task under fewer roles and checks, and explain which risks increase. This is an advanced policy-design exercise, not a second build-everything exercise. A sensible answer may be that the existing coding-agent-plus-CI workflow is sufficient.

Review capacity also limits useful parallelism. Increasing workers while the reviewer cannot keep up increases queueing, not necessarily delivery. An invocation allowance or pause-before-new-dispatch policy is a useful future control; it should not impose a presentation timeout that kills healthy live agents.

### R12. Validate the journey, not just its pieces

The current [factory CI workflow](../../.github/workflows/factory-verify.yml) runs Python unit tests and deterministic first-wave TV and recipe checks on Ubuntu. These are valuable. It does not include the website browser journey or the full release-check rehearsal command that passed manually in this review.

The website tests are predominantly rendered-structure and source/copy assertions. They do not detect the local-storage defect or a contradiction between the guide and a fresh Control Center.

The guide also has two build paths: the default test build uses Vinext, while `build:vercel` uses Next.js. Passing one should not be reported as validating both deployment paths.

**Change:** Add a small, maintained end-to-end matrix:

- clean setup and correct next action;
- chosen route and checklist surviving reload;
- PRD review and revision;
- QA pause, evidence inspection, and approval;
- one implementation/review/human-merge cycle;
- preview and evidence access;
- a supported recovery and reset flow.

Use deterministic fixtures for browser tests. Keep a separate, explicitly authorized live smoke process for provider and GitHub integration. A mock result must not certify live authentication or provider behavior.

Pin the session version and capture screenshots from named fixture states. Record the runtime commit and scene used to generate each image. Existing screenshot-presence checks cannot tell whether an image shows the correct state.

Finally, document what has actually been verified on macOS, Linux, and WSL. Local macOS checks and Ubuntu CI are useful evidence, but do not establish a fresh WSL setup by themselves.

### R13. Refactor around shared decisions, not fashionable patterns

The repository already has dedicated modules for adapters, governance, acceptance evidence, GitHub integration, and human attention. Preserve these boundaries. The next refactor should make frequently changed decisions easier to find and test.

The largest areas remain substantial: approximately 7,430 lines in `orchestrator.py`, 2,739 in `control_center.py`, 1,866 in `planning_pipeline.py`, 1,572 in the Control Center JavaScript, and 816 in the main guide page at the reviewed revision.

The project's own complexity tool reports these representative scores:

| Function | Reported score | Why to inspect it |
| --- | ---: | --- |
| `export_evidence` | 72 | Validation, assembly, and export decisions are concentrated |
| `Factory.load_tickets` | 69 | Ticket ingestion combines many sources and conditions |
| `Factory.__init__` | 62 | Construction includes significant configuration policy |
| `ControlCenter.journey` | 60 | Readiness and next-action policy have user-visible consequences |
| `retry_ticket` | 52 | Recovery must preserve evidence and lifecycle invariants |
| `human_merge_ticket` | 48 | Authority and revision checks are high-consequence logic |

These are the repository tool's scores, not an independent standard complexity benchmark. High scores identify places to inspect; they do not justify splitting every branch into a class.

Prioritize four cohesive boundaries:

1. **Readiness and next-action model.** One authoritative projection of persisted workflow facts; consumed by CLI and UI. R01 is a concrete reason for this extraction.
2. **Ticket transitions and recovery.** Keep transition conditions, evidence invalidation, and retry rules together. UI code should render allowed actions rather than reconstruct their policy.
3. **Agent invocation lifecycle.** Share event normalization, cancellation, bounded output, and usage handling where planning and delivery currently repeat those concerns. Preserve role-specific permissions and prompts.
4. **Workshop session definition.** One versioned description of route, release, supported requirements, learning checkpoints, and screenshot scenes. Generate repetitive metadata, not all prose.

Use typed records or enums where they prevent ambiguous dictionary states. Do not replace the current system with microservices, introduce a new workflow platform, or add abstractions solely to improve a metric. The test is whether a policy change has one clear home and fewer opportunities for contradictory behavior.

### R14. Measure status-stream cost before optimizing it

The Control Center event stream repeatedly calls `snapshot()`. That snapshot reads multiple files and derives repository, environment, planning, and application state. Each connected stream repeats work, and operation polling adds another refresh path while actions are running.

This architecture can amplify filesystem and subprocess work across tabs. It is not evidence that the current UI is slow; no representative multi-tab performance benchmark was run.

Measure snapshot duration, subprocess count, CPU use, event payload size, and update latency with several active tickets and browser clients. If material, reuse a versioned snapshot, invalidate it when relevant state changes, and stream bounded changes rather than recomputing everything for every client.

Also inspect bounded log retention and invocation output buffering. Delivery execution accumulates output chunks as well as writing logs. Long runs need explicit limits and predictable cancellation behavior. Optimize the observed bottleneck while preserving useful recovery evidence.

## 5. A coherent three-hour learning story

### The central question

Use one question throughout the session:

> What evidence would let another engineer accept this change without trusting the agent's claim that it is done?

This connects the interests of all three audiences. The engineer needs a reliable change; the tech lead needs a workable review process; the CTO needs an accountable operating model.

The story should develop in six parts:

1. **A plausible result is not enough.** Show a finished-looking application and a PR. Ask whether it should merge. Reveal missing or stale evidence.
2. **A request needs decisions before it needs code.** Use the planning roles to expose ambiguity and agree on a bounded result.
3. **A ticket needs a testable contract.** Follow one requirement into a slice and a meaningful acceptance test.
4. **Execution produces a candidate, not permission.** Show the worktree, gates, retries, and review record.
5. **A person accepts an exact change.** Inspect the current revision and make the merge decision.
6. **The workflow has to earn its overhead.** Map the same decisions to the attendee's own use case and decide whether a pilot is worthwhile.

The five layers belong after attendees have seen the responsibilities in action. Introduce them as locations where those responsibilities are implemented, not as five terms to memorize before beginning.

### Proposed 180-minute agenda

This is a replacement proposal, not a claim that the current five-ticket Live rebrand already fits these timings. It assumes completed prework and a revised bounded core exercise. Prepare evidence for teaching checkpoints when live execution is still running; do not terminate a healthy agent to synchronize the room.

| Time | Topic and facilitator points | Attendee activity | Required observable result |
| --- | --- | --- | --- |
| 00–10 | Show a candidate PR and application; ask “Would you merge?” | Vote individually, then identify missing evidence with a neighbor | One reason a plausible result is not sufficient |
| 10–20 | Define a factory using familiar Git, tests, CI, and review; distinguish agent, orchestrator, and person | Map those three actors onto the displayed run | A simple explanation without relying on product-specific terminology |
| 20–35 | Confirm target repository, selected agent, contract, and human merge policy | Connect each attendee's own repository; complete or verify setup | Correct target and readiness; facilitator separately verifies the demonstration repository |
| 35–50 | Product intent and ambiguity | Edit one requirement, inspect Product Review, and request a specific correction | A testable behavior and an intentional approval |
| 50–65 | Architecture, program design, and delivery order | Trace one requirement through the technical plan; select the core slice | A bounded user-visible result and its dependencies |
| 65–80 | Tickets and QA preparation | Publish the approved plan to the attendee's GitHub Project; start QA for the core work | A real issue and Project item, with the relevant ticket identifiable by title rather than fixed number |
| 80–95 | Meaningful RED evidence | Classify prepared failures; inspect and approve the live or rehearsal test proposal | A justified rejection and a justified acceptance |
| 95–105 | Break | Leave healthy work running where appropriate | No new material |
| 105–125 | Implementation, checks, and recovery | Follow the selected ticket; inspect a retry or a prepared recovery case | Can distinguish working, blocked, and waiting for a person |
| 125–145 | Review and human merge | Inspect the current diff and review receipt; request rework if needed; merge the accepted revision when ready | One accepted core slice, or an explicitly recorded incomplete Live outcome with the decision exercise completed on prepared evidence |
| 145–155 | Product verification, durable evidence, and cost | Verify the user behavior; inspect evidence and invocation/review data | Can state what was proved, what remains unknown, and what consumed effort |
| 155–175 | Apply the model to a real use case | Complete the short pilot worksheet and exchange a challenge with a peer | A bounded pilot proposal with an owner and a stop/go criterion |
| 175–180 | Check understanding and close | Answer three new decision questions and name the next action | Evidence of transfer, not just completed clicks |

Attendees whose Live runs are unfinished should leave with an exact resume point. The facilitator should report that honestly. The teaching fallback protects the learning outcome; it does not convert unfinished execution into successful delivery.

### What to move out of the core session

Keep these as optional follow-up labs or reference material:

- deploying the factory to AWS;
- implementing a custom adapter or test runner;
- multi-repository workspace coordination;
- Autonomous Demo policy;
- advanced trigger, monitoring, and compounding workflows;
- completing every mobile and TV rebrand ticket;
- a detailed build/buy comparison for every infrastructure layer;
- optimization of role count and deep verification budgets.

Mention their existence where useful, but do not make attendees configure them. More features are not more learning when the core model is still unfamiliar.

## 6. Exercises that repay the time investment

The exercises should make attendees decide, predict, or repair something. Copying a command is preparation for an exercise, not the learning outcome itself.

Short, focused tasks with checks between them reduce the amount a novice must keep in memory. Use one worked example before asking for an independent decision. [The Carpentries: Memory and Cognitive Load](https://carpentries.github.io/instructor-training/instructor/05-memory.html)

### Exercise A: Would you merge this PR?

**Time:** embedded in the opening ten minutes.

**Provide:** a finished-looking app, a diff, and a review receipt for an older commit than the current PR head. Use a prepared fixture, not a surprise edit to an attendee's active branch.

**Ask:** “The tests shown here passed and the agent says the PR is approved. What do you check before merging?”

**Expected insight:** inspect whether the tests and review apply to the candidate revision, not merely whether a green badge exists. Identify the missing check or renewed review.

**Transfer:** release approval, infrastructure changes, generated migrations, and dependency updates all require evidence attached to the actual candidate.

This opening makes the factory relevant before the first installation command. It should take minutes, not a complete live run.

### Exercise B: Turn an ambiguous request into a contract

**Provide:** “Let users find recipes quickly.”

**Ask:** choose the supported search fields, behavior for no matches, and one concrete example. Compare that decision with the Product Review output and request a revision if the output leaves it ambiguous.

**A possible answer:** “Search recipe titles and ingredient names case-insensitively. Searching for spinach returns recipes that contain spinach. A query with no matches shows an empty state rather than all recipes.” This is a proposed teaching example, not a claim about the current sample's accepted contract.

**Expected insight:** a longer PRD is not automatically a clearer PRD. Human judgment should settle product meaning before agents implement their own interpretation.

**Transfer:** the same technique applies to “improve onboarding,” “harden this endpoint,” or “make reporting faster.”

### Exercise C: Follow one requirement, not four documents

**Provide:** the chosen search requirement, architecture output, program design, ticket, and proposed test.

**Ask:** identify the component boundary, the data or method contract, the first deliverable, and the test that would detect a violation. Find one mismatch or confirm a specific trace.

**Expected insight:** the four experts are useful only if their outputs agree. Reading four long documents independently does not establish alignment.

**Transfer:** tech leads can use the same trace in design review even without adopting this factory implementation.

### Exercise D: Reject false RED evidence

**Provide three small outputs and the relevant tests:**

1. `No module named pytest`.
2. An assertion expecting the new search result while the baseline returns none.
3. A failing assertion about an unrelated title or a test that cannot pass for any valid implementation.

**Ask:** Which result justifies beginning implementation? What must be repaired in the other cases?

**Expected answer:** the dependency failure is an environment problem; the second can be meaningful RED after inspecting the assertion and intended behavior; the unrelated or impossible assertion is not acceptable merely because it fails.

**Transfer:** green/red test statuses are observations. They require an argument connecting them to the requirement.

The same examples can be solved while the live QA role works. This protects teaching time without killing the process or weakening a gate.

### Exercise E: Explain a blocked ticket and the next safe action

**Provide:** one dependency wait, one failed verification gate, and one human-approval wait. Use fixture snapshots or the actual run when it naturally reaches those states.

**Ask:** Who must act? What evidence is missing? Is retrying useful? What would reset discard or preserve?

**Expected insight:** not every stationary ticket is an agent failure, and retry is not a universal repair.

Keep a dependency-cycle repair as an advanced challenge for experienced attendees. Do not deliberately corrupt the core classroom run just to create drama.

### Exercise F: Match delivery rate to review capacity

**Provide a hypothetical example:** implementation can produce six reviewable changes per hour, but one reviewer can properly inspect three per hour. Ignore other constraints for this simplified calculation.

**Ask:** Will doubling implementation workers double accepted delivery? Where will work accumulate? What would you limit or improve first?

**Expected insight:** under these assumptions, review is the limiting step. More generated candidates can increase waiting work. Smaller changes, clearer evidence, and controlled work in progress may matter more than additional agents.

**Transfer:** the CTO and tech lead can evaluate staffing, risk, and throughput using familiar delivery-system reasoning rather than agent-count enthusiasm.

The numbers are teaching assumptions, not measured factory benchmarks.

### Exercise G: Design a pilot worth running

Use this short worksheet in the 20-minute transfer block:

1. What recurring change will enter the workflow? Give one example and one exclusion.
2. What observable result would make that change useful?
3. Which checks must be executable, and what still needs a person?
4. Which repository, data, credentials, and execution boundary are in scope?
5. Who owns review, recovery, and the final acceptance decision?
6. What would you measure against today's workflow: accepted changes, lead time, review effort, defects, and execution cost?
7. What is the smallest pilot, and what result would cause you to continue, change, or stop it?

Allow “do not use a factory for this case” as a valid, well-reasoned conclusion. That is evidence of understanding, not failure to adopt the product.

Suggested peer challenge: “Which assumption in this proposal is least tested?” Each attendee should leave with one specific next action, not an instruction to automate their entire backlog.

## 7. How to simplify the materials without removing essential teaching

### Give each document one job

| Material | Primary job | Keep out of its main path |
| --- | --- | --- |
| Attendee invitation | Exact prerequisites, route, access, expected costs, and readiness proof | Architecture and implementation detail |
| Workshop website | Current task, action, expected evidence, recovery, and learning checkpoint | Long facilitator scripts and all optional features |
| Three-hour plan | Timing, facilitation, questions, transitions, and contingency use | Repeated installation reference material |
| Narrative | The story and explanations behind the decisions | A competing set of copyable setup commands |
| Factory README and configuration reference | Precise runtime behavior, supported integrations, and operational limits | Claims that every capability is a required workshop activity |
| Advanced labs | Custom adapters, cloud deployment, stronger controls, economics experiments | Anything that blocks the first successful core slice |

The plan, narrative, outline, and facilitator file together contain roughly 15,000 words at this revision. Separate documents are justified by their audiences, but duplicated route, timing, and setup facts should have one maintained source.

Do not solve this by hiding every explanation. The guide's copy-budget test helps prevent a wall of text, but it cannot determine whether an omitted explanation was necessary.

### Use a consistent task pattern

For each beginner action, show:

- **Goal:** the observable result in one sentence.
- **Location:** the page or exact checkout and terminal.
- **Action:** a short ordered procedure.
- **Expected result:** the status or artifact that should appear.
- **Decision:** what the attendee must inspect or choose.
- **If it differs:** one targeted repair, with a link to deeper diagnosis.

This follows the useful parts of Microsoft's procedure guidance: use task-oriented headings, imperative steps, and tell the reader where an action occurs. [Microsoft: Writing step-by-step instructions](https://learn.microsoft.com/en-us/style-guide/procedures-instructions/writing-step-by-step-instructions)

For example, replace “Review the test proposal” with:

> In Deliver → Tickets, open the ticket waiting for QA approval. Select Tests. Read the assertion and the baseline failure. Confirm that the failure describes the missing behavior, not a missing dependency. If it does, approve the test proposal. The ticket should become ready for implementation.

The final wording and button names must follow the actual interface after the QA decision view is settled.

### Keep screenshots small and specific

Each instructional image should answer one question: where to click, what to inspect, or what success looks like. Use a crop with numbered callouts and a matching numbered instruction. Retain a full-screen reference for orientation.

Record a screenshot's scene, mode, ticket state, and runtime revision. Never use a post-implementation green result to illustrate pre-implementation approval. Clearly label illustrated GitHub examples; do not imply they are proof of an actual publication.

Use text for commands and evidence that attendees need to copy. A screenshot of a log is not an accessible substitute for the log text.

## 8. Improvement backlog and sequencing

The following are proposed work packages. This review has not implemented them.

| Order | Work package | Scope and dependencies | Done when |
| --- | --- | --- | --- |
| 1 | Correct initial readiness | R01; backend projection and matching UI tests | An empty runtime cannot skip setup or claim an existing PRD; all readiness views agree |
| 2 | Repair guide state | R02; independent of factory execution | Route and checklist survive reload; invalid storage is safe; labels do not imply a completed run |
| 3 | Define the session contract | R03–R04; prerequisite for final copy and screenshots | One primary route, pinned release, own-repository rule, bounded core slice, completion rule, and fallback are agreed |
| 4 | Make setup and recovery copyable | R06; follows the session contract | A new user can execute each command and identify its checkout; the earlier branch/agent/pytest failure has a specific safe repair |
| 5 | Improve the QA decision | R07 and part of R09 | Criterion, code, failure, and action are inspectable together; screenshots show QA Review; false-RED exercise has an answer key |
| 6 | Restore evidence and transfer access | R05, R11 | The UI exposes the intended evidence; prerequisites and export order agree; a short pilot worksheet is part of the timed session |
| 7 | Align all teaching materials | R08; uses packages 3–6 | Website and facilitator follow the same story, actions, outcomes, vocabulary, and revised timing |
| 8 | Add journey-level checks | R12; tests packages 1–7 | Browser coverage catches the reproduced defects and completes a deterministic core delivery; deployment build paths are checked explicitly |
| 9 | Run a novice readiness study | Requires a release candidate | Observed completion, assistance, and learning results meet the agreed criteria or produce a focused revision list |
| 10 | Clarify extension boundaries | R10 | Test-runner, adapter, provider, and execution capabilities are visible before custom-project commitment |
| 11 | Extract high-consequence policy seams | R13; preserve behavior with characterization tests | Readiness, transition, and revision invariants have clear ownership; duplication is reduced without a platform rewrite |
| 12 | Measure and tune long-running behavior | R14 | Performance and cancellation changes are justified by measurements, with bounded output and maintained recovery evidence |

Packages 1–3 are the immediate release blockers for a self-guided claim. Packages 4–9 make the workshop substantially more likely to repay a beginner's three hours. Packages 10–12 improve the factory as a reusable engineering tool.

### What not to prioritize now

- More expert roles before existing roles produce understandable decisions.
- A new frontend framework or orchestration platform.
- Cloud provisioning in the mandatory attendee path.
- Automatic merge as the workshop's main attraction.
- Token dashboards populated with guessed numbers.
- A larger sample application.
- Cosmetic complexity reduction without clearer policy ownership.

These would consume development or classroom time without resolving the reproduced failures and learning gaps.

## 9. Prove that the workshop works for beginners

### Conduct a representative dry run

Recruit six to eight people unfamiliar with this implementation, including engineers, tech leads, and a technical decision-maker. Include the operating systems and agent providers you intend to advertise. They should use the invitation and session link as distributed, not receive an undocumented setup briefing.

Each participant creates their own disposable repository. The facilitator uses a separate repository. Observe individual progress even when peers discuss decisions.

Record:

- time to a correct target and readiness result;
- every request for help, with the screen and instruction involved;
- wrong-checkout or wrong-repository actions;
- where participants retry without understanding the failure;
- time waiting on a provider versus time lost to unclear instructions;
- ability to explain an approval decision;
- whether the core result was actually delivered or a fallback was used;
- completion and quality of the personal pilot proposal.

Do not coach immediately when someone hesitates. First note what they expected and what the interface said. Intervene before an unsafe action or prolonged unproductive struggle, and record the assistance.

### Proposed release criteria

These are suggested targets to validate, not results obtained in this review:

| Area | Proposed criterion |
| --- | --- |
| Prework | At least 90% of the pilot group can establish readiness from the invitation before the session |
| Repository safety | No participant is instructed to modify the facilitator's repository or an unrelated checkout |
| Core execution | At least 80% of Live-ready participants finish the bounded core slice within the scheduled delivery block; report provider failures separately |
| Recovery | Participants can select the correct next action for dependency wait, infrastructure failure, and human approval without treating them all as retry cases |
| Evidence | At least 80% correctly reject stale review evidence and explain a valid RED result in new examples |
| Transfer | Every participant completes a bounded pilot proposal; peer review identifies at least one assumption or risk |
| Honest fallback | Every use of Rehearsal or prepared evidence is recorded as such, with an unfinished Live run's resume point retained |
| Schedule | The session preserves its break and 20-minute application exercise; setup overruns do not consume the entire closing block |

With a small pilot, report actual counts as well as percentages. One successful dry run improves confidence; it does not prove that every venue, provider, or cohort will behave identically.

### A short post-workshop assessment

Use unfamiliar examples rather than asking attendees to repeat button names:

1. A test suite is green, but the PR changed after review. What must happen before merge?
2. A baseline acceptance run fails because a package is missing. Is that sufficient evidence to begin implementation? Why?
3. Your proposed factory produces work faster than your team can review it. What would you measure or change before adding more agents?

A useful answer references evidence, authority, or capacity. “Click Retry” or “use a stronger model” alone is not sufficient.

Ask separately whether the attendee can name a task that should **not** use this level of orchestration. That tests whether they learned proportional engineering judgment rather than a product pitch.

## 10. Facilitator readiness and contingency rules

Before the next workshop:

- Freeze the session release and verify that the hosted guide and screenshots describe it.
- Complete the exact attendee setup on a clean machine or clean user environment.
- Verify one chosen live provider against the supported CLI version with explicit authorization for cost and GitHub changes.
- Keep prepared evidence for Product Review, meaningful and invalid RED, a verification retry, stale review, accepted revision, and final app behavior.
- Check the projector layout, screenshot readability, keyboard navigation, Wi-Fi, and authentication redirects.
- Make the cost expectation and provider-subscription requirement explicit in the invitation.
- Verify the evidence-export route and its actual Canvas requirements before scheduling that activity.

During the workshop:

- Preserve the attendee's own repository and actual run status.
- Leave healthy live agents running; use prepared evidence for the group's next decision when needed.
- Never claim a simulated run is a completed Live change.
- Do not remove a selected human gate simply to make the room appear finished.
- Record the exact recovery or resume point for unfinished work.
- Protect the final application exercise instead of spending every remaining minute on setup.

The current facilitator recovery table suggests finishing without `--review-qa-tests` when QA review takes too long. Replace that shortcut with a prepared evidence decision or a narrower core workload. Removing the gate in response to time pressure teaches the opposite of the workshop's strongest lesson.

## 11. Evidence and source map

Paths and function names refer to the reviewed revision. Relative links open the current checkout; use [the reviewed commit](https://github.com/giolaq/software-refactory-workshop/tree/b80bf38ca55bfae461f9c738ae8c5688a592f94a) when comparing this report with later changes.

| Area | Primary source and inspection point |
| --- | --- |
| Fresh-start state | [control_center.py](../../factory/control_center.py): `journey()` around line 1152; `snapshot()` around line 1409 |
| Canvas and export UI gap | [control_center.py](../../factory/control_center.py): `canvas()`, `save_canvas()`, evidence action, `/api/canvas`; compare [index.html](../../factory/control_center/index.html) and [app.js](../../factory/control_center/app.js) |
| App availability versus completion | [control_center.py](../../factory/control_center.py): `_application_entrypoint()`, `application_instructions()`, `journey()`; [app.js](../../factory/control_center/app.js): application rendering and navigation |
| Website persistence and route | [page.tsx](../../workshop-guide/app/page.tsx): state/effects around lines 183–217; prerequisites and route selection around lines 335–398 |
| Commands and completion text | [page.tsx](../../workshop-guide/app/page.tsx): setup around line 399; plan-ID examples around line 540; QA around line 586; completion and recovery around lines 670–748 |
| QA screenshot | [control-center-ticket-tests.jpg](../../workshop-guide/public/screenshots/control-center-ticket-tests.jpg) |
| Test classification and runners | [acceptance_evidence.py](../../factory/acceptance_evidence.py): `focused_test_command()` and `classify_focused_result()`; [tests](../../factory/tests/test_acceptance_evidence.py) |
| Canvas validation | [evidence_packet.py](../../factory/evidence_packet.py): `CANVAS_SECTIONS`, `validate_canvas()`, `export_evidence()`; [Canvas template](../../factory/FACTORY_CANVAS.md) |
| Timing and primary route | [WORKSHOP_PLAN_3_HOURS.md](../../factory/WORKSHOP_PLAN_3_HOURS.md): Recommended operating mode and the final two timed blocks |
| Facilitator recovery | [FACILITATOR.md](../../factory/FACILITATOR.md): recovery table around line 300 |
| Existing narrative | [WORKSHOP_NARRATIVE.md](../../factory/WORKSHOP_NARRATIVE.md) and [WORKSHOP_OUTLINE.md](../../factory/WORKSHOP_OUTLINE.md) |
| Sample delivery order | [example-plan.json](../../factory/scenarios/recipe-rebrand/example-plan.json), [planning slices](../../factory/scenarios/recipe-rebrand/planning/04-vertical-slices.json) |
| Orchestration and complexity | [orchestrator.py](../../factory/orchestrator.py), [planning_pipeline.py](../../factory/planning_pipeline.py), [complexity.py](../../factory/complexity.py) |
| Operational metrics and boundaries | [run_summary.py](../../factory/run_summary.py), [adapter_protocol.py](../../factory/adapter_protocol.py), [LIMITS.md](../../factory/LIMITS.md) |
| CI and guide checks | [factory-verify.yml](../../.github/workflows/factory-verify.yml), [rendered-html.test.mjs](../../workshop-guide/tests/rendered-html.test.mjs), [package.json](../../workshop-guide/package.json) |

### Verification limits

The local checks passed on the available macOS environment. Both guide build paths compiled. The completed five-ticket run was deterministic Rehearsal, not a new live-provider certification. No production deployment, provider billing inspection, full accessibility audit, hostile-repository test, or measured multi-client load test was performed.

At the time of the original review, the only repository change was this report.
The implementation disposition below records the subsequent work separately.

## Conclusion

This project can deliver a compelling workshop because it exposes decisions that ordinary coding-agent demonstrations often skip: clarifying intent, rejecting inadequate tests, preserving evidence through rework, and accepting an exact revision.

The current risk is not a shortage of capability. It is that attendees spend their limited attention navigating setup, interpreting inconsistent progress, and reading artifacts without practicing the judgment those artifacts are meant to support.

Fix the misleading states, teach one complete delivery path, and reserve time to evaluate a real use case. Then validate the result with beginners. The workshop's strongest promise is not “you will run many agents.” It is “you will know when this workflow helps, what evidence to demand, and how to introduce it without surrendering engineering responsibility.”

## Implementation disposition

Branch: `codex/workshop-simplify-readiness`, based on the reviewed main revision.
No publication, version bump, tag, merge, paid provider run, or cloud change is
part of this implementation.

### Changes by finding

| Finding | Applied change | Remaining boundary |
| --- | --- | --- |
| R01 | Shared `setup_readiness` derives setup from persisted facts and a valid plan ID. The UI consumes that result. Regression and browser checks cover an empty run. | A plan cannot override a failed current setup attempt. |
| R02 | Removed mark-complete controls, progress indicators, the right rail, and guide completion storage. Static section links remain. | This follows the owner's instruction instead of repairing persistence. |
| R03 | Website defaults to Standard Live, with personal repositories and GitHub Projects. Rehearsal is explicitly simulated. Outline, timed plan, and narrative use the same route. | Rehearsal does not demonstrate provider performance or publish issues. |
| R04 | Added `workshop-search-prd.md`: one end-to-end genre-search fix. Planning now permits one ticket. The complete recipe rebrand is an extension; the app view names its checkout revision and unfinished tickets. | A justified blocker may require another slice. Completion is not guaranteed by a clock. |
| R05 | Evidence export works without a Canvas, and the Control Center can export, open, and download the packet. A short pilot worksheet receives 20 minutes. | An explicitly supplied Canvas is still validated. |
| R06 | Setup uses short direct commands, an explicit session-tag replacement, and browser repository creation. Shell variables stay in optional CLI instructions; plan and ticket inputs are requested there when needed. Recovery identifies the failing interpreter. | A new-user setup observation is still required; copying valid shell does not prove comprehension. |
| R07 | QA Review opens Tests. Criterion, committed source, baseline result, revision feedback, and approval are together. The viewer verifies protected Git blob hashes; approval stays disabled if source cannot be read. | An assertion failure is not proof of semantic correctness. A person must inspect it. |
| R08 | Rewrote the facilitator plan and speaker narrative around product correction, false RED, stale revision, review capacity, and a pilot decision. Removed conceptual lecture sections from the website. | Learning effectiveness needs the closing questions and novice dry run, not a website checklist. |
| R09 | Removed the competing setup architecture strip, folded adapter detail, hid irrelevant listener state, improved QA layout, and added drawer focus handling including live-refresh restoration. | A full screen-reader and assistive-technology audit is not claimed. |
| R10 | Documented built-in planning adapters, custom role integration, pytest/Node focused-test support, and the distinction between worktrees and a security sandbox. | No new native Go, Rust, Java, or TypeScript focused runner is claimed. |
| R11 | Added a review-throughput exercise, cost-and-capacity pilot questions, and recorded execution/wait/retry information in the Control Center. Unknown provider usage remains explicit. | No invented token count, price, or predicted completion time. |
| R12 | Added browser checks for fresh setup, QA source inspection, focus recovery, five-ticket delivery, evidence export, and guide reload. CI includes the guide tests, lint, both builds, and the deterministic browser journey. Refreshed screenshots carry source/image hashes and an explicit Rehearsal label. | CI is configured, not remotely executed in this turn. Live providers, other OS environments, the deployed guide, and timed novice validation remain release checks. |
| R13 | Extracted the shared readiness decision and reused QA decision rendering and handlers. Removed guide state and unused presentation CSS. Preserved existing governance, transition, adapter, and evidence modules. | Deliberately no new workflow framework, universal lifecycle abstraction, or whole-codebase rewrite. Further extraction should follow a concrete policy change. |
| R14 | Status streams share a one-second snapshot cache. Healthy SSE stops redundant operation polling. Delivery keeps a bounded ordinary-output response tail while retaining its complete ordinary output log. | This is not a measured multi-client speedup. Protocol buffering, disk retention, and cancellation still need representative long-run measurements before broader changes. |

### Verification and release handoff

The local checks exercise the current working files, not just the old committed
HEAD. The disposable browser fixture copies current source, commits it in a
temporary repository, runs real deterministic planning and delivery commands,
and removes that repository afterward. It uses no paid agent or GitHub remote.

- Factory unit and integration-style suite, including readiness, protected test
  source, optional Canvas, stream reuse, and bounded ordinary output.
- Guide rendered-HTML and local-editor tests, shell-syntax checks, lint, and both
  Vinext and Next.js production builds.
- Browser checks and visual inspection of updated Setup, planning, ticket board,
  QA source/decision, merge, overview, and evidence screenshots.
- Five-ticket Standard Rehearsal with protected QA approvals and exact-revision
  human merge commands; Evidence Packet readable without a Canvas.
- Local Markdown links and website assets; existing complexity limits retained.

Use [Workshop validation](../../factory/WORKSHOP_VALIDATION.md) for the commands,
the screenshot procedure, the mandatory human checks, and the release freeze.
It explicitly separates demonstrated behavior from support targets. The next
session release must publish the tested source, matching guide, and matching
screenshots together; the old `workshop-v1.2.1` tag does not contain this branch's
unpublished changes.
