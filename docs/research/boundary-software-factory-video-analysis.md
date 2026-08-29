# Video analysis: Boundary's software-factory design patterns

**Research date:** 2026-08-29  
**Primary source:** [How to Build a Software Factory for AI Coding Agents](https://www.youtube.com/watch?v=tGbjIvvYuHE), Boundary / *AI That Works*, 70:45, published 2026-08-28  
**Requested moment:** [1:04:08 — interface layer first](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=3848s)  
**Our snapshot:** `main` at `8df3ad4` (`workshop-v1.1.3`)

## Executive reading

The talk's durable idea is not a particular model, agent, or vendor. It is that a software factory should be treated as a **composable stack with explicit interfaces**. The speakers divide that stack into compute, development environment, coding harness, and control plane/orchestration. A team should be able to build, buy, or replace each layer independently instead of inheriting one vertically integrated system ([00:00](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=0s), [22:08](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=1328s), [55:56](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=3356s)).

The linked moment at 1:04:08 is the conclusion of that argument. The speakers use MCP as an ecosystem precedent: a sufficiently useful interface allowed agent clients and integrations to mix and match. Their recommendation is therefore to design **open seams before a universal product**, so a company can retain the pieces where control matters and buy the rest ([1:04:08](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=3848s)). They immediately acknowledge that this is difficult because Claude, Codex, Pi, and OpenCode expose different hooks and vendors have incentives to preserve differentiation ([51:23](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=3083s), [1:04:54](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=3894s)).

Software (re)-Factory already implements much of the control-plane side of this thesis: replaceable Agent Adapters, a repository Project Contract, a human-owned Factory Charter, PRD planning, bounded Ticket execution in worktrees, a Supervisor, independent QA, causal RED/GREEN proof, revision-specific code review, human merge, durable run summaries, monitoring, and a visual Control Center. In this comparison, our project is ahead as a **governed delivery and teaching workflow**.

The video exposes three remaining architectural gaps:

1. Our adapter seam is useful but not yet a complete interface between control plane, harness, and execution environment.
2. Our development-environment layer is checked and described, but not provisioned as a reproducible disposable resource.
3. Our system records corrections and metrics, but does not yet turn repeated corrections into reviewed improvements to the outer harness.

The strongest workshop change is narrative rather than another agent role: teach the factory as a layered system whose purpose is to move scarce human judgment to high-leverage gates.

## What the video means by a software factory

### Four layers

| Layer | Video's definition | Example from the talk | Equivalent in our project | Current gap |
| --- | --- | --- | --- | --- |
| Compute | The machine or sandbox on which an agent session runs | Mac minis, EC2, Kubernetes, or managed sandboxes ([23:08](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=1388s), [31:44](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=1904s)) | The attendee's machine or an adapter-supplied `local`, `container`, or `hosted` execution boundary | Built-in workflows remain local; the execution type is declared, not provisioned |
| Development environment | Runtimes, repository checkout, dependent services, identity, credentials, network access, and preview URLs | Preinstalled Rust toolchain, internal service access, authenticated identity, shareable previews ([33:47](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=2027s), [41:30](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=2490s)) | `factory.project.toml`, `factory prepare`, `factory doctor`, required tools, setup commands, ports, gates, target checkout | No first-class provision/start/preview/teardown lifecycle; setup can drift between machines |
| Inner and outer harness | Inner: the coding CLI/model loop. Outer: team-specific prompts, skills, tests, retry rules, and completion loops | Headless Claude Code or Codex plus JSONL traces, CodeRabbit loops, skills, and max iterations ([24:00](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=1440s), [36:23](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=2183s)) | Agent Adapters are the inner harness; roles, policy, Charter, prompts, QA/review loops, and Handoff Receipts are the outer harness | Planning is limited to Claude/Codex; adapter-specific lifecycle features are normalized only partially |
| Control plane | Dispatch, traces, planning artifacts, triggers, review, permissions, audit, budgets, and organizational learning | A service receiving Slack/Linear/GitHub events and dispatching work to machines ([27:16](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=1636s), [39:55](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=2395s)) | Orchestrator, Supervisor, Control Center, GitHub Issues/Projects, issue listener, evidence summaries, Monitor | No cost/token accounting, scheduling/cron, or reviewed compounding-memory loop |

This framing is more precise than “a group of AI agents.” Agents occupy the harness layer. The factory is the complete system that turns intent into a governed, observable, reviewable change.

### Build versus buy is a decision per layer

The talk rejects the false choice between building the whole stack and buying one managed system. Its preferred rule is effectively composition over inheritance: use a vendor's compute, harness, or orchestration only where its interface and control trade-off suit the team ([29:41](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=1781s), [55:56](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=3356s)).

Our project already embodies this at the harness layer. `factory/factory.toml` registers commands, `.factory/local.toml` assigns adapters by role, and the Factory Profile preserves the workflow when Claude, Codex, Cursor, or a custom noninteractive command fills a role. The Project Contract similarly separates repository mechanics from the factory engine.

However, our website can make this stronger by showing the build/buy decision explicitly:

- **Use ours:** the orchestration lifecycle, evidence model, Control Center, and workshop Rehearsal.
- **Bring yours:** agent CLI/model, target repository, setup commands, verification gates, and optionally a container or hosted runner.
- **Replace later:** any adapter or execution boundary without rewriting the Product → Ticket → evidence lifecycle.

### Interfaces first does not mean pretending every adapter is identical

At [1:04:08](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=3848s), the speakers argue that an interface layer can unlock an ecosystem. Earlier, they warn that current agent protocols do not cover the lifecycle hooks they need, and that every harness makes different trade-offs ([51:23](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=3083s)). Their own advice is also to avoid wrappers that merely hide a good vendor API and create a second lagging interface ([54:16](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=3256s)).

That distinction matters for Software (re)-Factory. A good adapter contract should standardize only the factory invariants:

- accepted assignment and repository context;
- declared filesystem, network, credential, and environment boundaries;
- bounded progress events and final structured decision/evidence;
- cancellation, timeout, and retry semantics; and
- capabilities that the Control Center can expose honestly.

It should not erase useful provider-specific behavior. The UI and documentation should say when an adapter supports structured planning, read-only mode, tool progress, resumable sessions, subagents, browser testing, or hosted execution. `factory/adapter_capabilities.py` is the right foundation; the next improvement is capability negotiation and versioned event schemas, not one lowest-common-denominator prompt wrapper.

## Workflow lessons from the talk

### 1. Prototype to settle intent, then deliver reviewable slices

For large work, the described workflow iterates on a PRD and rough HTML interaction mockups, lets agents build an end-to-end prototype, uses that prototype to clarify the desired product, and then re-plans the production change as smaller PRs. The speaker explicitly avoids asking a reviewer to absorb a 20,000-line prototype and aims for digestible increments, often around 1,000–3,000 lines ([11:08](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=668s), [13:49](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=829s), [14:56](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=896s)).

Our four planning experts and Vertical Slices are a stronger production mechanism than their informal prompt queue. The Project Contract, Charter, dependency graph, file ownership, diff budget, and traceability validators make the slices executable and governed. What we do not currently teach clearly enough is the difference between:

- a **cheap prototype used to discover intent**, which may be discarded; and
- a **reviewable vertical slice**, which must preserve quality and evidence.

The Pocket Cinema → Recipe App exercise can demonstrate this distinction directly: show a rough visual target during Product Review, then explain that the generated Tickets rebuild it as bounded, independently reviewable increments rather than promoting a giant prototype diff.

### 2. Treat incoming feedback as untrusted until it becomes a reproduction

The Boundary workflow does not create an issue directly from raw user feedback. It first checks whether the problem is already fixed, attempts deduplication, and produces a reliable reproduction. If an agent cannot reproduce it or external information is required, a human takes over ([15:32](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=932s), [18:03](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=1083s), [32:02](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=1922s)).

Our PRD path has a strong trust funnel: Product Review, architecture, program design, Vertical Slices, deterministic validation, human approvals, then publication. Our Live issue listener also classifies incomplete Tickets and offers a human-reviewed correction. It does not yet provide the same **feedback → dedupe → reproducible failure → governed Ticket** pipeline for production bug reports.

An incremental improvement would add an optional intake role that produces:

- the affected revision and environment;
- a focused reproduction command or a reason one is impossible;
- duplicate candidates and confidence;
- required external data or human decision; and
- exactly one of `READY_TO_PLAN`, `READY_TO_IMPLEMENT`, `NEEDS_INFORMATION`, or `WAIT`.

Crucially, raw issue text and attached code must remain untrusted input. The talk's own decision to avoid containers is tied to its narrow workload and the fact that raw user code is not executed ([30:59](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=1859s)). A generic factory accepting arbitrary repositories should keep or strengthen isolation, not copy that local trust assumption.

### 3. Measure imperfect agent stages instead of assuming correctness

The speakers build evals from historical issues and measure reproduction, deduplication, and classification rates. They are willing to use an imperfect classifier when its accuracy is visible and the downstream outcome can correct the dataset ([19:34](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=1174s), [20:14](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=1214s)). Their cited target of roughly 60% for one classifier is a practitioner starting point, not a general benchmark.

Our factory already records useful operational evidence: stage time, agent time, gate time, human wait, retries, verifier rejection, review-queue pressure, diff size, RED/GREEN verdicts, review decisions, and exact revisions. The Monitor detects repeated review findings and hotspots. This is better than the workflow shown in the talk because it connects metrics to governed delivery evidence rather than a standalone eval.

The missing loop is evaluation across runs. We should aggregate only bounded, sanitized outcomes and answer:

- Which planning stages are most often corrected?
- Which adapters cause retries or invalid structured output by role?
- Which acceptance tests are already green before implementation?
- Which review findings recur?
- Where does human wait dominate cycle time?
- Which Ticket classifications are reversed by later evidence?

These metrics should propose changes to prompts, skills, contracts, or profiles. They must never edit the Factory Charter automatically.

### 4. Optimize for high automation, not zero humans

The speakers call full automation a common mistake and prefer a system that automates roughly 95% while escalating cases that require judgment or external knowledge ([32:29](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=1949s)). Their review loop lets CodeRabbit and an implementation agent iterate up to three times, then escalates. A human still approves and clicks merge; an agent only babysits synchronization and CI after that approval ([25:00](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=1500s), [25:23](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=1523s)).

This strongly validates our current Standard path:

- QA owns the acceptance evidence.
- Implementation and verification loop within bounded retries.
- Code Review returns comments to the same PR for rework.
- The Supervisor coordinates but cannot grant itself lifecycle authority.
- Standard and Assured stop at a human exact-revision merge decision.
- Autonomous merge remains an explicit workshop-only profile.

Our project is better here because the stopping conditions, exact-head checks, causal RED/GREEN evidence, human-attention capacity, and merge authority are executable policy rather than an informal while loop. The workshop narration should make that advantage legible: **the human did not disappear; the factory prepared a smaller, evidence-rich decision for them**.

### 5. Review, not generation, is the scarce resource

The talk's zoomed-in factory is agent builds → agent tests/receives feedback → review. Its thesis is that generation became fast while review remained the bottleneck ([22:08](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=1328s)). The large-project example makes the social consequence concrete: huge AI diffs reduce reviewer quality and create resentment ([13:49](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=829s)).

Software (re)-Factory already has the right mechanics: vertical slices, diff budgets, `max_awaiting_human_review`, a visible `NEEDS YOU` queue, and human-wait metrics. This should become the workshop's main tension. Parallel agents are not the success metric. The success metric is whether the factory produces **small decisions with trustworthy evidence at a rate humans can absorb**.

### 6. Development environment is product functionality

The speakers argue that development environments become the difficult layer once an agent needs precise runtimes, dozens of services, identity, credentials, network access, and a preview another person can open. For complex enterprise systems, teams may need to own this layer even if they buy the harness ([33:47](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=2027s), [35:10](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=2110s)). They use “pets versus cattle” to distinguish manually maintained workers from reproducibly provisioned disposable ones ([42:19](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=2539s)).

This is the clearest lesson for our recent colleague setup failure. `factory prepare` and `factory doctor --full` are not clerical prerequisites. They are our current implementation of the development-environment contract. A failed Codex login, missing `pytest`, wrong default branch, or unsynchronized repository means the environment cannot satisfy the contract yet; rerunning the factory cannot fix that fact.

Our documentation now explains recovery, but the narration should state the architectural reason:

> Setup proves that the repository, tools, identity, branch, gates, and agent harness form one runnable development environment. The factory does not dispatch work until that environment passes.

Longer term, the Project Contract should drive an environment adapter with a lifecycle such as `provision`, `prepare`, `health`, `preview`, `reset`, and `destroy`. A local implementation may reuse the checkout; a container or hosted implementation may create disposable infrastructure. Both should return the same bounded evidence to the control plane.

### 7. Multi-repository work needs a coordination workspace

The talk recommends one canonical coordination workspace that tells the agent where related repositories live, without requiring a monorepo or Git submodules. Every session begins from that shared context; disposable environments then face the cost of provisioning the necessary repositories ([45:30](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=2730s), [46:39](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=2799s), [47:27](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=2847s)).

Our Project Contract currently describes one target repository. That is appropriate for the workshop and most first deployments. For enterprise adoption, a future `workspace` contract could declare related repositories, read/write ownership, required revisions, shared services, and which repository receives each Ticket and PR. This should follow demonstrated demand; it should not complicate the beginner workshop.

### 8. Code-defined extensions can beat a universal no-code workflow

Near the end, the speakers argue that every company's definition of an issue, trust, approval, and external dependency is different. They prefer stable building blocks plus code-defined workflows over a universal visual integration builder ([50:00](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=3000s), [1:00:12](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=3612s), [1:06:18](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=3978s)). They also separate an extensible “vibe” zone from a protected functional core through deliberate interfaces ([1:08:49](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=4129s)).

Our architecture already has the beginnings of this split:

- protected core: orchestrator lifecycle, schema validation, Charter, gates, hashes, claims, and exact-head merge checks;
- extension zone: Agent Adapter commands, role assignments, Project Contract setup/gates, Ticket-specific adapter choice, and external execution wrappers.

We should make this an explicit extension model. Custom code may propose intake, planning, dispatch, verification, or presentation behavior through a small versioned interface, but only the orchestrator may apply lifecycle mutations. This preserves our strongest design principle: agent and extension output is a proposal; executable policy decides what can happen.

## Where our project is better

1. **Planning rigor.** The talk shows an effective practitioner workflow; ours turns Product Review, Architecture, Program Design, and Vertical Slices into schema-validated, hash-bound, traceable artifacts with selected human gates.
2. **Independent and causal QA.** Our QA role authors protected acceptance evidence and proves the same focused command RED before implementation and GREEN afterward.
3. **Governance.** The Factory Charter makes consequence, paths, budgets, stop conditions, review capacity, and merge authority explicit and human-owned.
4. **Closed review loop.** Code Review is revision-specific, comments return to implementation, gates rerun, and Standard/Assured stop at a human exact-head merge.
5. **Distributed coordination.** Dependency-aware scheduling, atomic remote claims, isolated worktrees, Handoff Receipts, and Supervisor proposals are more complete than the single dispatcher example in the video.
6. **Observability and recovery.** The Control Center makes prompts, logs, artifacts, tests, gates, review, human waits, failures, and recovery actions inspectable in one place.
7. **Durable evidence.** Bounded remote summaries and a read-only Monitor preserve cross-run outcomes without publishing raw prompts, credentials, or hidden reasoning.
8. **Workshop reproducibility.** Rehearsal mode demonstrates the complete topology without model credentials or GitHub mutations.

## Where our project is worse or less mature

1. **Environment provisioning.** The Project Contract describes and checks a development environment, but the factory does not create disposable compute, services, identity, or previews itself.
2. **Adapter interface depth.** We can swap command adapters, but do not expose a stable, versioned event/capability protocol across harnesses; planning remains Claude/Codex-specific.
3. **Provider-specific transparency.** The workflow abstraction can make adapters look more equivalent than they are. The UI should expose meaningful capability differences.
4. **Compounding engineering.** Corrections and repeated findings are recorded, but no reviewed process turns them into proposed outer-harness improvements.
5. **Cost visibility.** We measure time, retries, evidence, and queue pressure but intentionally do not invent provider cost. Adapters that expose token/cost data could report it through an optional sanitized interface.
6. **Production feedback intake.** The issue listener validates Ticket structure; it does not yet deduplicate raw reports and prove a reproduction before issue admission.
7. **Multi-repository workspaces.** One Project Contract maps one repository. There is no shared coordination contract for changes spanning services.
8. **Scheduled control-plane triggers.** Live issue listening and Monitor publication exist, but cron/webhook-triggered runs are not a first-class supported interface.

## Recommended applications

### Apply now to the workshop and website

1. **Introduce the four-layer stack before setup.** Show compute → development environment → inner/outer harness → control plane, then point to the attendee's laptop, Project Contract/doctor, selected CLI adapters, and Control Center.
2. **Rename the meaning of setup.** Explain that `prepare` provisions declared dependencies and `doctor --full` proves the development-environment contract. Every failure should be located in one layer.
3. **Use the review bottleneck as the story's conflict.** Fast generation creates more review demand. Vertical Slices, causal tests, diff budgets, and review capacity protect human attention.
4. **Show one adapter swap.** Run the same role contract with Claude and Codex, then point out one genuine capability difference. This demonstrates composability without claiming interchangeability is free.
5. **Make the human decision visible.** At Product Review, alignment, Acceptance Test review, and merge, ask: “What judgment is the factory waiting for, and what evidence made this decision small enough?”
6. **End with a build/buy Factory Canvas.** For each layer, attendees mark `own`, `buy`, or `bring existing`, plus the interface and evidence they require.
7. **Separate prototype from delivery.** Treat mockups or a throwaway app as intent discovery; use the factory to rebuild the result as reviewable slices.
8. **Conclude with the interface-first principle.** The take-home message is not to copy our Python implementation. It is to define stable contracts so agents, environments, tools, and policies can change independently.

### Apply next to the factory

1. **Version the adapter event and capability contract.** Preserve current command adapters, but add declared structured planning, read-only enforcement, progress events, cancellation, session resume, browser, subagent, and execution-environment capabilities.
2. **Add an execution-environment lifecycle adapter.** Implement `provision`, `prepare`, `health`, `preview`, `reset`, and `destroy`, first for local checkouts and later for a real container or hosted runner.
3. **Add optional reproducible-intake evidence.** Before a raw bug report becomes a Ticket, attempt duplicate detection and a focused reproduction; escalate when external information is required.
4. **Create a reviewed compounding report.** Aggregate repeated corrections, invalid outputs, review findings, and human wait. Suggest a prompt/skill/contract change; require a person to accept it in a separate PR.
5. **Accept optional adapter usage telemetry.** Store tokens, model, and cost only when a provider exposes trustworthy values. Mark unavailable data as unavailable rather than estimating it.
6. **Design, but do not yet force, a multi-repository workspace contract.** Keep the beginner path single-repository.
7. **Add trigger adapters after the event contract is stable.** Webhook and schedule inputs should propose work through the same governed intake interface as the UI and CLI.

## Recommended narration

A concise story for the workshop is:

> AI made code generation cheap. That does not make software delivery cheap: intent, environment setup, verification, review, and accountability remain scarce. A software factory connects those concerns through explicit contracts. The agent is one replaceable part of the harness; the factory is the system around it. We plan enough to create reviewable slices, run each slice in an isolated workspace, prove behavior with independent evidence, and stop when human judgment is valuable. The goal is not a lights-off organization. It is a composable workflow that automates routine motion and presents people with smaller, better-supported decisions.

The workshop progression then becomes:

1. **Locate the layers.** Identify compute, development environment, harness, and control plane.
2. **Prove readiness.** Prepare and run preflight; fix the first failed layer.
3. **Turn intent into contracts.** PRD → Product Review → Architecture → Program Design → Vertical Slices.
4. **Protect review capacity.** Publish bounded Tickets with ownership, dependencies, and diff budgets.
5. **Produce causal evidence.** Independent QA proves RED; implementation and gates prove GREEN.
6. **Use automation until judgment matters.** Review/rework loops run within limits; blocked work explains what a person must decide.
7. **Make the accountable decision.** A person merges the exact reviewed revision.
8. **Design your own factory.** Choose what to own, buy, and replace at each layer.

## Source quality and caveats

This analysis uses the video's first-party YouTube metadata, creator description/chapters, and English auto-generated captions. The captions were checked around every cited timestamp, but names and product terms may contain transcription errors. Timestamp links are therefore more authoritative than the prose rendering.

The video is an informal practitioner discussion and product-founder conversation, not a controlled benchmark. Statements about model quality, the value of 60% classification accuracy, or the 95% automation target are experiences and heuristics. They should guide experiments, not become universal requirements.

The speakers' no-container approach is explicitly conditioned on a narrow trusted workload and a pipeline that does not execute raw user-submitted code. It is not evidence that local unsandboxed execution is safe for a generic factory.

Finally, the code-extension demo near the end fails after a local dependency upgrade ([1:07:00](https://www.youtube.com/watch?v=tGbjIvvYuHE&t=4020s)). That accidental failure reinforces one of our strongest teaching points: a reproducible development environment and an explanatory readiness check are part of the factory product, not setup trivia.
