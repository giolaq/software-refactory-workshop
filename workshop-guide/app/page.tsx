"use client";

import { useEffect, useMemo, useState, type CSSProperties, type ReactNode } from "react";

type Track = "rehearsal" | "live";

const steps = [
  { id: "setup", label: "Finish Setup", time: "25 min" },
  { id: "baseline", label: "Check the starting app", time: "8 min" },
  { id: "prd", label: "Write requirements", time: "7 min" },
  { id: "plan", label: "Approve Product Review", time: "17 min" },
  { id: "publish", label: "Create tickets", time: "28 min + break" },
  { id: "qa", label: "Approve Acceptance Tests", time: "18 min" },
  { id: "factory", label: "Deliver tickets", time: "30 min" },
  { id: "finish", label: "Review the app", time: "12 min" },
] as const;

function CodeBlock({ children, label = "Terminal" }: { children: string; label?: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    await navigator.clipboard.writeText(children);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  return (
    <div className="code-block">
      <div className="code-toolbar">
        <span>{label}</span>
        <button type="button" onClick={copy} aria-label={`Copy ${label} command`}>
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre><code>{children}</code></pre>
    </div>
  );
}

function Callout({
  type = "note",
  title,
  children,
}: {
  type?: "note" | "tip" | "warning";
  title: string;
  children: ReactNode;
}) {
  return (
    <aside className={`callout callout-${type}`}>
      <span className="callout-icon" aria-hidden="true">
        {type === "tip" ? "✓" : type === "warning" ? "!" : "i"}
      </span>
      <div>
        <strong>{title}</strong>
        <div>{children}</div>
      </div>
    </aside>
  );
}

function Checkpoint({ children }: { children: ReactNode }) {
  return (
    <div className="checkpoint">
      <div className="checkpoint-title"><span aria-hidden="true">✓</span> Check</div>
      <div>{children}</div>
    </div>
  );
}

function WorkshopPaths({
  click,
  whyStopped,
  inspect,
  continueWhen,
  children,
}: {
  click: ReactNode;
  whyStopped?: ReactNode;
  inspect: ReactNode;
  continueWhen: ReactNode;
  children: string;
}) {
  return (
    <div className="instruction-paths">
      <section className="instruction-card control-center-card" aria-label="Control Center path">
        <span className="path-label">Control Center</span>
        <h3>Use the Control Center</h3>
        <dl className="instruction-list">
          <div><dt>Do this</dt><dd>{click}</dd></div>
          <div><dt>What happens</dt><dd>{whyStopped ?? <>The factory stops when it needs your decision or when a check fails. <strong>Current phase</strong> tells you what to do next.</>}</dd></div>
          <div><dt>Check</dt><dd>{inspect}</dd></div>
          <div><dt>Continue when</dt><dd>{continueWhen}</dd></div>
        </dl>
      </section>
      <details className="instruction-card cli-card" aria-label="CLI path">
        <summary><span className="path-label">CLI</span><strong>Use the CLI</strong></summary>
        <CodeBlock label="CLI">{children}</CodeBlock>
      </details>
    </div>
  );
}

function WorkshopMedia({
  src,
  alt,
  label,
  caption,
  width,
  height,
  portrait = false,
}: {
  src: string;
  alt: string;
  label: string;
  caption: string;
  width: number;
  height: number;
  portrait?: boolean;
}) {
  return (
    <figure className={`workshop-figure${portrait ? " workshop-figure-portrait" : ""}`}>
      <a className="workshop-screenshot" href={src} target="_blank" rel="noreferrer">
        {/* These local screenshots keep their intrinsic size and open as source evidence. */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={src} alt={alt} width={width} height={height} loading="lazy" />
        <span>Open image</span>
      </a>
      <figcaption><strong>{label}</strong><span>{caption}</span></figcaption>
    </figure>
  );
}

function StepSection({
  index,
  id,
  title,
  goal,
  complete,
  onToggle,
  children,
}: {
  index: number;
  id: string;
  title: string;
  goal: string;
  complete: boolean;
  onToggle: () => void;
  children: ReactNode;
}) {
  return (
    <section id={id} className={`lesson${complete ? " lesson-complete" : ""}`}>
      <div className="lesson-heading">
        <span className="step-number">{complete ? "✓" : index}</span>
        <div>
          <span className="lesson-kicker">Step {index} · {steps[index - 1].time}</span>
          <h2>{title}</h2>
        </div>
      </div>
      <div className="lesson-body">
        <p className="goal"><strong>Goal:</strong> {goal}</p>
        {children}
      </div>
      <div className="lesson-footer">
        <button className={`complete-button${complete ? " completed" : ""}`} type="button" onClick={onToggle}>
          {complete ? "Completed" : "Mark step complete"}
        </button>
      </div>
    </section>
  );
}

export default function Home() {
  const [track, setTrack] = useState<Track>("rehearsal");
  const [completed, setCompleted] = useState<string[]>([]);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const restore = window.setTimeout(() => {
      const storedTrack = window.localStorage.getItem("workshop-track");
      const storedCompleted = window.localStorage.getItem("workshop-completed");
      if (storedTrack === "rehearsal" || storedTrack === "live") setTrack(storedTrack);
      if (storedCompleted) {
        try {
          setCompleted(JSON.parse(storedCompleted));
        } catch {
          window.localStorage.removeItem("workshop-completed");
        }
      }
    }, 0);
    return () => window.clearTimeout(restore);
  }, []);

  useEffect(() => {
    window.localStorage.setItem("workshop-track", track);
  }, [track]);

  useEffect(() => {
    window.localStorage.setItem("workshop-completed", JSON.stringify(completed));
  }, [completed]);

  const progress = useMemo(() => Math.round((completed.length / steps.length) * 100), [completed]);

  function toggleStep(id: string) {
    setCompleted((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  }

  function chooseTrack(next: Track) {
    setTrack(next);
    document.getElementById("setup")?.scrollIntoView({ behavior: "smooth" });
  }

  return (
    <>
      <a className="skip-link" href="#main-content">Skip to workshop</a>
      <header className="topbar">
        <button className="menu-button" type="button" aria-label="Open navigation" aria-expanded={menuOpen} onClick={() => setMenuOpen(true)}>
          <span /><span /><span />
        </button>
        <a className="brand" href="#overview">
          <span className="brand-mark" aria-hidden="true"><i /><i /><i /><i /></span>
          <b>Software (re)-Factory</b>
        </a>
        <span className="header-divider" aria-hidden="true" />
        <span className="header-section">Workshop guide</span>
        <div className="topbar-actions">
          <span className="duration-pill">3 hours</span>
          <a className="github-link" href="https://github.com/giolaq/software-refactory-workshop">GitHub</a>
        </div>
      </header>

      {menuOpen && <button className="nav-scrim" type="button" aria-label="Close navigation" onClick={() => setMenuOpen(false)} />}
      <aside className={`left-nav ${menuOpen ? "left-nav-open" : ""}`} aria-label="Workshop steps">
        <div className="nav-progress">
          <div className="nav-progress-row"><span>Progress</span><strong>{completed.length}/{steps.length}</strong></div>
          <div className="progress-track"><span style={{ width: `${progress}%` }} /></div>
        </div>
        <nav aria-label="Workshop sections">
          <p className="nav-label">Start</p>
          <a href="#overview" onClick={() => setMenuOpen(false)}>Overview</a>
          <a href="#layers" onClick={() => setMenuOpen(false)}>Factory layers</a>
          <a href="#prerequisites" onClick={() => setMenuOpen(false)}>Prerequisites</a>
          <a href="#path" onClick={() => setMenuOpen(false)}>Choose a path</a>
          <p className="nav-label">Workshop</p>
          {steps.map((step, index) => (
            <a key={step.id} href={`#${step.id}`} className={completed.includes(step.id) ? "nav-step-complete" : ""} onClick={() => setMenuOpen(false)}>
              <span>{completed.includes(step.id) ? "✓" : index + 1}</span>
              <span>{step.label}<small>{step.time}</small></span>
            </a>
          ))}
          <p className="nav-label">Afterward</p>
          <a href="#troubleshooting" onClick={() => setMenuOpen(false)}>Troubleshooting</a>
          <a href="#reference" onClick={() => setMenuOpen(false)}>Command reference</a>
        </nav>
      </aside>
      <main id="main-content">
        <section id="overview" className="hero">
          <div>
            <span className="eyebrow">Hands-on developer workshop</span>
            <h1>Software (re)-Factory workshop</h1>
            <p className="hero-lede">
              Follow Setup, Plan, Deliver, and Review to turn a PRD into tickets, code, tests, and a reviewed change. The Control Center tells you when to act and why it stopped.
            </p>
            <div className="hero-meta">
              <span><b>Duration:</b> 3 hours</span>
              <span><b>Format:</b> individual repository</span>
              <span><b>Tools:</b> Claude, Codex, Cursor, or your own CLI</span>
            </div>
            <a className="primary-button" href="#prerequisites">Start the workshop</a>
          </div>
          <div className="factory-map" aria-label="Workshop workflow">
            <div className="map-row"><span className="map-node">1 · Setup</span><i>→</i><span className="map-node node-blue">2 · Plan</span></div>
            <div className="map-down">↓</div>
            <div className="map-row"><span className="map-node node-purple">3 · Deliver</span><i>→</i><span className="map-node node-human">4 · Review</span></div>
            <div className="map-down">↓</div>
            <div className="map-row"><span className="map-node node-green">Running app and evidence</span></div>
          </div>
        </section>

        <section id="layers" className="layers-section" aria-labelledby="layers-title">
          <div className="section-heading">
            <span className="section-kicker">The system around the agent</span>
            <h2 id="layers-title">A coding agent makes a change. A software factory makes delivery repeatable.</h2>
            <p>Generation is fast; intent, environments, review, and accountability remain scarce.</p>
          </div>
          <div className="layer-chain" aria-label="Five replaceable factory layers">
            <article><span>01</span><b>Compute</b><small>Laptop, container, or runner</small></article><i>→</i>
            <article><span>02</span><b>Development environment</b><small>Checkout, tools, services, gates</small></article><i>→</i>
            <article><span>03</span><b>Inner harness</b><small>Claude, Codex, Cursor, or yours</small></article><i>→</i>
            <article><span>04</span><b>Outer harness</b><small>Roles, Charter, QA, retries, review</small></article><i>→</i>
            <article><span>05</span><b>Control plane</b><small>Orchestrator, Control Center, GitHub</small></article>
          </div>
          <div className="factory-principles">
            <article><strong>Review capacity is the limit</strong><p>More agents are a cost. Parallelize only reviewable evidence.</p></article>
            <article><strong>Prototype or Vertical Slice?</strong><p>A prototype may be discarded. A Vertical Slice is bounded, tested, reviewed, and intended to merge.</p></article>
          </div>
          <details className="capability-compare">
            <summary>Selected adapter capabilities</summary>
            <div className="capability-table">
              <div><b>Adapter</b><b>Protocol v1 declaration</b></div>
              <div><span>Codex</span><span>Structured planning, native read-only, subagents</span></div>
              <div><span>Cursor</span><span>Structured planning, native read-only</span></div>
            </div>
            <p><strong>Unavailable stays unavailable.</strong> The same Agent Role keeps its policy, gates, and authority when you swap adapters.</p>
          </details>
        </section>

        <section id="prerequisites" className="prerequisites-section">
          <div className="section-heading">
            <span className="section-kicker">Before you begin</span>
            <h2>Install and sign in</h2>
            <p>Complete this before opening the Control Center.</p>
          </div>
          <div className="prerequisites-grid">
            <article>
              <span className="requirement-label">Everyone</span>
              <h3>Local tools</h3>
              <ul>
                <li>macOS, Linux, or Windows with WSL2</li>
                <li>Python 3.11+ with virtual environments</li>
                <li>Node.js 20+, Git, and a modern browser</li>
                <li>Ports 5000 and 5050 available</li>
              </ul>
            </article>
            <article>
              <span className="requirement-label">Live path</span>
              <h3>Accounts and access</h3>
              <ul>
                <li>GitHub CLI with the <code>project</code> scope</li>
                <li>One personal GitHub product repository and its full URL</li>
                <li>Permission to create issues, branches, and Projects</li>
                <li>One signed-in agent CLI: Claude, Codex, Cursor, or your adapter</li>
                <li>Network access to GitHub and your model provider</li>
              </ul>
            </article>
          </div>
          <CodeBlock label="Verify before continuing">{`python3 --version
node --version
git --version
${track === "live" ? `gh --version
gh auth status
gh auth refresh -s project

# Run the check for the agent you will select later:
claude auth status --text
# or: codex login status
# or: agent status` : ""}`}</CodeBlock>
          <details>
            <summary>Use Cursor CLI</summary>
            <p>Install Cursor&apos;s current <code>agent</code> command, sign in, then select <strong>Cursor workshop</strong> during Setup. The Factory uses read-only Ask mode for planning and review, and Agent mode for implementation and QA.</p>
            <CodeBlock label="Install and verify Cursor">{`curl https://cursor.com/install -fsS | bash
agent --version
agent login
agent status`}</CodeBlock>
            <p><a href="https://cursor.com/docs/cli/installation">Cursor installation</a> · <a href="https://cursor.com/docs/cli/reference/permissions">Cursor permissions</a></p>
          </details>
          <Callout type="warning" title="Use your own repository">
            <p>For Live mode, use a personal GitHub repository. Do not use the facilitator&apos;s repository. Rehearsal mode stays on your computer and does not need GitHub or an agent login.</p>
          </Callout>
          {track === "live" && <Callout type="note" title="Live mode uses two repositories">
            <p>The <strong>factory checkout</strong> contains this workshop and starts the Control Center. Your separate <strong>product repository</strong> receives the issues, branches, pull requests, and application changes. Keep the two URLs separate.</p>
          </Callout>}
        </section>

        <section id="path" className="path-section">
          <div className="section-heading">
            <span className="section-kicker">Choose once</span>
            <h2>Select your path</h2>
            <p>Commands match your choice.</p>
          </div>
          <div className="path-grid">
            <button type="button" className={`path-card${track === "rehearsal" ? " path-selected" : ""}`} onClick={() => chooseTrack("rehearsal")}>
              <span className="recommended">Recommended first</span>
              <span className="path-icon rehearsal-icon">R</span>
              <strong>Rehearsal</strong>
              <span>Runs locally with built-in workshop agents. It does not change GitHub.</span>
              <small>Use this to learn the steps.</small>
            </button>
            <button type="button" className={`path-card${track === "live" ? " path-selected" : ""}`} onClick={() => chooseTrack("live")}>
              <span className="path-icon live-icon">L</span>
              <strong>Live</strong>
              <span>Uses your GitHub repository and signed-in coding agents.</span>
              <small>Use this for a real run.</small>
            </button>
          </div>
        </section>

        <StepSection index={1} id="setup" title="Finish Setup" goal="Open the Control Center, connect the correct repository, and pass preflight." complete={completed.includes("setup")} onToggle={() => toggleStep("setup")}>
          <p>{track === "live" ? "The workshop checkout controls a separate managed checkout of your product repository." : "Rehearsal is local, disposable, and credential-free."}</p>
          <CodeBlock label="Terminal 1 — do this once">{track === "rehearsal" ? `git clone https://github.com/giolaq/software-refactory-workshop.git software-refactory-rehearsal
cd software-refactory-rehearsal
./setup_demo.sh --scenario recipe-rebrand
git remote remove origin
git add .
git commit -m "chore: start workshop rehearsal"` : `gh auth login
gh auth refresh -s project
git clone https://github.com/giolaq/software-refactory-workshop.git software-refactory-control
cd software-refactory-control
./setup_demo.sh --scenario recipe-rebrand
gh repo create YOUR-REPOSITORY --private
export CONTROL="$PWD"
export TARGET="$CONTROL/.factory/repositories/YOUR-NAME/YOUR-REPOSITORY"`}</CodeBlock>
          <div className="activity-card launch-card">
            <span className="activity-label">Keep this process running</span>
            <h3>Start the Control Center</h3>
            <p>In a second terminal at <code>{track === "live" ? "software-refactory-control" : "software-refactory-rehearsal"}</code>, run:</p>
            <CodeBlock label="Terminal 2 — keep this running">{`./factory/factory control-center`}</CodeBlock>
            <ol>
              <li>Wait for <code>Factory Control Center: http://127.0.0.1:5050</code>.</li>
              <li>The browser should open automatically. Otherwise open <a href="http://127.0.0.1:5050">127.0.0.1:5050</a>.</li>
              <li>Leave this terminal running. <code>Ctrl+C</code> stops the Control Center.</li>
            </ol>
          </div>

          <h3>Complete Setup in three steps</h3>
          <ol className="setup-sequence">
            <li><span>1</span><div><strong>Connect</strong><p>Open <strong>Setup → Connection</strong>. Select <strong>{track === "live" ? "Live" : "Rehearsal"}</strong>, <strong>Standard</strong>, and your agent preset. {track === "live" ? <>Paste <em>your product repository</em> URL. Select <strong>Seed the guided Pocket Cinema starter</strong> for this exercise; leave it clear for your own existing product.</> : <>No GitHub settings are needed.</>} Select <strong>Save and connect</strong>.</p></div></li>
            <li><span>2</span><div><strong>Create contract</strong><p>Select <strong>Create contract</strong>. The factory detects source folders, tests, verification gates, and conservative operating rules. No coding agent runs.</p></div></li>
            <li><span>3</span><div><strong>Review and approve</strong><p>Open <strong>Review repository model</strong> and <strong>Review operating policy</strong>. If they match the repository, select <strong>Approve contract and continue</strong>.</p></div></li>
          </ol>

          <Callout type="note" title="One approval, visible automation">
            <p>After Step 3, the factory publishes the contract in Live mode, provisions and prepares the environment, checks health and gates, and runs preflight. <strong>Activity and CLI output</strong> shows each substep and stops at the first error.</p>
          </Callout>

          <Callout type="warning" title="If automatic setup stops, fix the first error">
            <p>Open <strong>Activity and CLI output</strong>, fix the first <code>[FAIL]</code>, then return to Step 3 and select <strong>Retry automatic setup</strong>. The <a href="#preflight-recovery">recovery table</a> gives exact fixes. An optional-adapter, port 5050, or reviewer <code>[WARN]</code> does not block the workshop.</p>
          </Callout>

          <WorkshopPaths
            click={<>Use <strong>Setup → Connection</strong> and complete the three numbered steps above.</>}
            whyStopped={<>The factory will not plan until the repository contract is approved and its automatic environment and preflight checks pass.</>}
            inspect={<>Confirm the product repository, source and test folders, required checks, selected agent preset, and merge authority.</>}
            continueWhen={<>Step 3 says <strong>Approved and ready</strong> and Activity output contains no <code>[FAIL]</code>.</>}
          >{track === "live" ? `# Run from the software-refactory-control directory.
./factory/factory checkout https://github.com/YOUR-NAME/YOUR-REPOSITORY \\
  --workspace-root "$CONTROL/.factory/repositories"

# For the guided exercise only:
./factory/factory bootstrap-workshop --repo "$TARGET" --source "$CONTROL"

# For a new or existing product, skip bootstrap-workshop and run:
# ./factory/factory init --repo "$TARGET"

AGENT_PRESET=claude-workshop # or codex-workshop or cursor-workshop
./factory/factory configure --repo "$TARGET" --preset "$AGENT_PRESET" \\
  --github-repository https://github.com/YOUR-NAME/YOUR-REPOSITORY
./factory/factory approve-contract --repo "$TARGET" --live --yes` : `# setup_demo.sh already created the local contract.
./factory/factory approve-contract --yes`}</WorkshopPaths>
          {track === "live" && <Callout type="note" title="Choose one agent preset">
            <p>The command defaults to Claude. Set <code>AGENT_PRESET</code> to <code>codex-workshop</code> or <code>cursor-workshop</code> when you use one of those CLIs. In the Control Center, select the matching name from <strong>Agent preset</strong>.</p>
          </Callout>}
          <WorkshopMedia
            src="/screenshots/control-center-connect.jpg"
            alt="Control Center Setup screen with Connect, Create contract, and Review and approve steps"
            label="Setup → Connection"
            caption="Three decisions: connect, create the contract, then review and approve."
            width={1440}
            height={980}
          />
          <Callout type="tip" title="Use Current run as your guide">
            <p><strong>Current phase</strong> explains the state. <strong>Next safe action</strong> opens the one action the factory needs from you.</p>
          </Callout>
          <Checkpoint><a href="http://127.0.0.1:5050">127.0.0.1:5050</a> is open, the correct repository is shown, Step 3 says <strong>Approved and ready</strong>, and Activity reports no failures.</Checkpoint>
        </StepSection>

        <StepSection index={2} id="baseline" title="Check the starting app" goal="Confirm what the factory will change." complete={completed.includes("baseline")} onToggle={() => toggleStep("baseline")}>
          <p>The guided exercise starts with Pocket Cinema. A new product repository has no app yet.</p>
          <WorkshopPaths
            click={<>Open <strong>Current run</strong> and check that <strong>Next safe action</strong> says <strong>Open the PRD</strong>.</>}
            whyStopped={<>No ticket starts before you save and approve a plan. For the guided exercise, the starter app runs as a separate process.</>}
            inspect={<>For the guided exercise, open Pocket Cinema. For a new product, confirm that the repository contains only <code>.gitignore</code> and the two factory settings files.</>}
            continueWhen={<>The starting repository is correct and the Control Center points to <strong>Plan → Requirements</strong>.</>}
          >{track === "live"
            ? `# Guided exercise:
"$CONTROL/.factory/venv/bin/python" "$TARGET/demo-app/app.py"

# New product:
git -C "$TARGET" ls-tree -r --name-only HEAD`
            : `.factory/venv/bin/python demo-app/app.py`}</WorkshopPaths>
          <WorkshopMedia
            src="/screenshots/pocket-cinema-before.webp"
            alt="Pocket Cinema application before the workshop change"
            label="Expected baseline"
            caption="A working media application that will become TableStory."
            width={1440}
            height={980}
          />
          <Checkpoint>Pocket Cinema opens, or the new product repository contains only factory settings.</Checkpoint>
        </StepSection>

        <StepSection index={3} id="prd" title="Write requirements" goal="Confirm the outcome the planning roles must design." complete={completed.includes("prd")} onToggle={() => toggleStep("prd")}>
          <WorkshopPaths
            click={<>Open <strong>Plan → Requirements</strong>. Read the PRD and edit it if needed. The draft saves automatically.</>}
            whyStopped={<>No planning role runs until you select <strong>Start Product Review</strong>.</>}
            inspect={<>Check the target users, required behavior, limits, and proof of success.</>}
            continueWhen={<>The save indicator is current and you can describe the requested product change.</>}
          >{track === "live"
            ? `open "$CONTROL/recipe-app-prd.md"`
            : `open recipe-app-prd.md`}</WorkshopPaths>
          <WorkshopMedia
            src="/screenshots/control-center-prd.jpg"
            alt="Control Center Plan and Requirements screen with an auto-saving PRD editor and Start Product Review button"
            label="Plan → Requirements"
            caption="Read the request and make any needed edits. The draft saves automatically."
            width={1440}
            height={980}
          />
          <Checkpoint>The PRD is saved and describes the TableStory result.</Checkpoint>
        </StepSection>

        <StepSection index={4} id="plan" title="Approve Product Review" goal="Approve the user problem and expected behavior before technical design." complete={completed.includes("plan")} onToggle={() => toggleStep("plan")}>
          <WorkshopPaths
            click={<>In <strong>Plan → Requirements</strong>, select <strong>Start Product Review</strong>. Then open <strong>Plan → Review plan</strong> and select <strong>Product Review</strong>.</>}
            whyStopped={<>A person must approve the product plan before technical planning starts.</>}
            inspect={<>Check the users, problem, required behavior, success checks, and any questions. Request a revision when the plan is unclear.</>}
            continueWhen={<>The product plan is clear, testable, and approved.</>}
          >{track === "live" ? `./factory/factory plan "$CONTROL/recipe-app-prd.md" --repo "$TARGET"
export PLAN_ID=<plan-id-from-output>
./factory/factory review product "$PLAN_ID" --repo "$TARGET"
./factory/factory revise "$PLAN_ID" product --repo "$TARGET" \\
  --feedback "Clarify the user journey and success checks."
./factory/factory approve-product "$PLAN_ID" --repo "$TARGET"` : `./factory/factory plan recipe-app-prd.md --mock
export PLAN_ID=<plan-id-from-output>
./factory/factory review product "$PLAN_ID"
./factory/factory revise "$PLAN_ID" product --mock \\
  --feedback "Clarify the user journey and success checks."
./factory/factory approve-product "$PLAN_ID"`}</WorkshopPaths>
          <WorkshopMedia
            src="/screenshots/control-center-planning.jpg"
            alt="Control Center Plan and Review plan screen showing expert stages and human approval gates"
            label="Plan → Review plan"
            caption="Open Product Review. Yellow cards need a decision from you."
            width={1440}
            height={980}
          />
          <Checkpoint>Product Review shows <strong>Approved</strong>.</Checkpoint>
        </StepSection>

        <StepSection index={5} id="publish" title="Create tickets" goal="Review the technical plan and approve the Vertical Slices." complete={completed.includes("publish")} onToggle={() => toggleStep("publish")}>
          <Callout type="tip" title="Break">
            <p>After experts finish, pause 10 minutes; keep agents running.</p>
          </Callout>
          <WorkshopPaths
            click={<>In <strong>Plan → Review plan</strong>, select <strong>Run remaining experts</strong>. Open each result, resolve blockers, and complete approvals. Then select <strong>Create tickets</strong>.</>}
            whyStopped={<>The factory waits for answers when an expert cannot make a safe assumption. It also waits for your final approval before it creates tickets.</>}
            inspect={<>Check the planned components, code changes, ticket acceptance criteria, order, and dependencies.</>}
            continueWhen={track === "live" ? <>The GitHub Project contains the planned issues.</> : <>The Tickets page contains the planned work.</>}
          >{track === "rehearsal" ? `./factory/factory continue-plan "$PLAN_ID" --mock
./factory/factory review alignment "$PLAN_ID"
./factory/factory approve-rehearsal "$PLAN_ID" --scenario recipe-rebrand
./factory/factory run --mock --scenario recipe-rebrand --dry-run` : `./factory/factory continue-plan "$PLAN_ID" --repo "$TARGET"
./factory/factory review alignment "$PLAN_ID" --repo "$TARGET"
./factory/factory approve "$PLAN_ID" --repo "$TARGET" \\
  --new-project-title "TableStory Workshop"`}</WorkshopPaths>
          <Callout type="note" title="What planning creates">
            <p>Product Review defines the user result. Architecture defines the main components. Program Design lists the code changes. Vertical Slices become ordered tickets.</p>
          </Callout>
          <Checkpoint>{track === "live" ? "The GitHub Project shows the new issues." : "The Tickets page shows the planned work."}</Checkpoint>
        </StepSection>

        <StepSection index={6} id="qa" title="Approve Acceptance Tests" goal="Confirm that the proposed test detects the missing behavior." complete={completed.includes("qa")} onToggle={() => toggleStep("qa")}>
          <WorkshopPaths
            click={<>Open <strong>Deliver → Tickets</strong>. Open <strong>Run options</strong> and select <strong>Run one cycle</strong>. Open ticket <strong>#1</strong>, select <strong>Tests</strong>, and review the proposal. Return to <strong>Summary</strong> to approve it.</>}
            whyStopped={<>The factory runs the new test before implementation. <strong>RED PROVED</strong> means the test failed because the requested behavior is still missing.</>}
            inspect={<>Check the test file, command, and failure. Do not approve a test that fails because of setup, syntax, or an unrelated error.</>}
            continueWhen={<>The failure proves the behavior is missing and you approve the test.</>}
          >{track === "live" ? `./factory/factory run --repo "$TARGET" --review-qa-tests --once
./factory/factory approve-tests ISSUE_NUMBER --repo "$TARGET"` : `./factory/factory run --mock --scenario recipe-rebrand --review-qa-tests --once
./factory/factory approve-tests ISSUE_NUMBER`}</WorkshopPaths>
          <WorkshopMedia
            src="/screenshots/control-center-ticket-tests.jpg"
            alt="Control Center ticket drawer open on the Tests tab"
            label="Ticket tests"
            caption="Approve only when RED PROVED shows that the requested behavior is missing."
            width={1440}
            height={980}
          />
          <Checkpoint>The ticket shows <strong>RED PROVED</strong> and records your approval.</Checkpoint>
        </StepSection>

        <StepSection index={7} id="factory" title="Deliver tickets" goal="Run the planned work and handle each human checkpoint." complete={completed.includes("factory")} onToggle={() => toggleStep("factory")}>
          <WorkshopPaths
            click={<>Open <strong>Deliver → Tickets</strong> and select <strong>Run factory</strong>. Keep <strong>Active lanes</strong> selected. When <strong>NEEDS YOU</strong> appears, open the linked ticket.</>}
            whyStopped={<>For each ticket, the factory assigns work, runs tests and required checks, and asks a separate agent to review the change. It stops when a check fails or a person must decide.</>}
            inspect={<>Open the ticket tabs to read the task, live log, changed files, tests, checks, and code review. Before merge, confirm that the approved commit matches the pull request.</>}
            continueWhen={<>Code review approves the commit and you select <strong>Merge exact revision</strong>. The ticket then moves to Done.</>}
          >{track === "live" ? `gh project view <project-number> --owner "@me" --web
./factory/factory run --repo "$TARGET"` : `./factory/factory run --mock --scenario recipe-rebrand`}</WorkshopPaths>
          <WorkshopMedia
            src="/screenshots/control-center-tickets.jpg"
            alt="Control Center Tickets board with backlog and QA Review columns"
            label="Deliver → Tickets"
            caption="Active lanes keep the current work readable. Choose All lanes only when you need the full lifecycle."
            width={1440}
            height={980}
          />
          {track === "live" && <details className="optional-detail">
            <summary>Optional: admit a new GitHub issue after planning</summary>
            <p>Open <strong>Run options → Listen for new issues</strong>. The first start records the current backlog without changing it. Create a new issue afterward, then review the proposed acceptance criteria and dependencies in the Control Center before accepting it. The listener never treats old issues as new work.</p>
          </details>}
          {track === "live" && <WorkshopMedia
            src="/screenshots/github-project-board.jpg"
            alt="Illustrated GitHub Project board showing factory Tickets in lifecycle columns"
            label="GitHub Project"
            caption="Use the project board to see shared ticket status."
            width={1280}
            height={942}
          />}
          <WorkshopMedia
            src="/screenshots/control-center-overview.jpg"
            alt="Control Center Current run page showing current phase, next safe action, delivery trace, and human decisions"
            label="Current run"
            caption="Current phase shows what is happening. Next safe action opens the decision the factory needs."
            width={1440}
            height={980}
          />
          <details className="optional-detail">
            <summary>What happens to each ticket</summary>
            <ol>
              <li>The Supervisor selects a ticket whose dependencies are complete.</li>
              <li>QA adds a test for the requested behavior.</li>
              <li>The coding agent changes an isolated Git worktree.</li>
              <li>The factory runs tests and repository checks.</li>
              <li>A separate agent reviews the pull request.</li>
              <li>You decide whether to merge the approved commit.</li>
            </ol>
          </details>
          <WorkshopMedia
            src="/screenshots/control-center-human-merge.jpg"
            alt="Control Center Ticket summary showing an exact-revision human merge action"
            label="Merge checkpoint"
            caption="Confirm that review approved the current pull request commit. Then select Merge exact revision."
            width={1440}
            height={980}
          />
          <Callout type="tip" title="A failed check is normal">
            <p>The factory sends the error back to the agent and reruns the check after the fix. Open the ticket history to follow the retry.</p>
          </Callout>
          {track === "live" && <Callout type="tip" title="Two views, one run">
            <p>GitHub Projects shows shared ticket status. The Control Center shows local agent logs, changed files, tests, and checks.</p>
          </Callout>}
          <Checkpoint>At least one ticket reaches Done after tests, checks, review, and your merge decision.</Checkpoint>
        </StepSection>

        <StepSection index={8} id="finish" title="Review the completed app" goal="Start TableStory and check the integrated result." complete={completed.includes("finish")} onToggle={() => toggleStep("finish")}>
          <WorkshopPaths
            click={<>Open <strong>Review → Run app</strong> and select <strong>Start app</strong>, or copy the displayed startup command.</>}
            whyStopped={<>The page becomes available when every ticket is Done.</>}
            inspect={<>Open <code>http://127.0.0.1:5000/</code> for mobile and desktop, or <code>http://127.0.0.1:5000/?mode=tv</code> for television.</>}
            continueWhen={<>TableStory loads in the browser. Keep the terminal running while you use it, then press <code>Ctrl+C</code> to stop the server.</>}
          >{track === "live" ? `cd "$TARGET"
"$CONTROL/.factory/venv/bin/python" demo-app/app.py` : `.factory/venv/bin/python demo-app/app.py`}</WorkshopPaths>
          <WorkshopMedia
            src="/screenshots/control-center-evidence.jpg"
            alt="Control Center Review and Run app screen with the start command and application URLs"
            label="Review → Run app"
            caption="Start the integrated application from the repository used by this run."
            width={1440}
            height={980}
          />
          <Checkpoint>TableStory opens from the repository produced by the factory.</Checkpoint>
        </StepSection>

        <section className="transfer-section" aria-labelledby="transfer-title">
          <div><span className="section-kicker">Use it for your work</span><h2 id="transfer-title">Own, buy, or bring existing</h2><p>Name each layer&apos;s interface, evidence, and failure owner.</p></div>
          <ol><li>Compute</li><li>Development environment</li><li>Inner harness</li><li>Outer harness</li><li>Control plane</li></ol>
        </section>

        <section className="completion-panel">
          <div className="completion-ring" style={{ "--progress": `${progress}%` } as CSSProperties}><span>{progress}%</span></div>
          <div><span className="section-kicker">Factory progress</span><h2>{progress === 100 ? "Factory complete" : "Keep going"}</h2><p>{completed.length} of {steps.length} steps marked complete.</p></div>
          {progress < 100 && <a className="primary-button" href={`#${steps.find((step) => !completed.includes(step.id))?.id ?? "setup"}`}>Next step</a>}
        </section>

        <section id="troubleshooting" className="support-section">
          <div className="section-heading">
            <span className="section-kicker">When something stops</span>
            <h2>Troubleshooting</h2>
            <p>Read the exact status before repeating an action.</p>
          </div>
          <section className="preflight-recovery" id="preflight-recovery" aria-labelledby="preflight-recovery-title">
            <span className="section-kicker">Setup recovery</span>
            <h3 id="preflight-recovery-title">Automatic setup stopped: fix the first FAIL</h3>
            <ol>
              <li>Open <strong>Current run → Activity and CLI output</strong>.</li>
              <li>Scroll to the first <code>[FAIL]</code>. Ignore later failures until this one is fixed.</li>
              <li>Apply the matching fix below. Do not delete work or force-reset a branch.</li>
              <li>Return to <strong>Setup → Connection</strong> and select <strong>Retry automatic setup</strong>.</li>
            </ol>
            <div className="status-key" aria-label="Preflight status meanings"><span className="status-pass">PASS · ready</span><span className="status-warn">WARN · check whether optional</span><span className="status-fail">FAIL · fix before continuing</span></div>
            <div className="fix-table" role="table" aria-label="Common preflight failures and fixes">
              <div className="fix-table-head" role="row"><span role="columnheader">The FAIL says</span><span role="columnheader">Fix it</span></div>
              <div role="row"><code role="cell">default branch<br />branch synchronization</code><span role="cell">Save any local work first. Then run <code>git fetch origin</code>, <code>git switch main</code>, and <code>git pull --ff-only origin main</code> in the product checkout.</span></div>
              <div role="row"><code role="cell">codex/claude adapter not found or not signed in</code><span role="cell">In <strong>Setup → Connection</strong>, choose the preset for the CLI you actually installed and save. Sign in with <code>codex login</code> or <code>claude auth login</code>.</span></div>
              <div role="row"><code role="cell">No module named pytest<br />gate: api-tests</code><span role="cell">Install the dependency with the repository&apos;s normal setup command, then select <strong>Retry automatic setup</strong>. If the contract omitted that command, correct its setup commands before retrying.</span></div>
              <div role="row"><code role="cell">GitHub Projects scope</code><span role="cell">Run <code>gh auth refresh -s project</code>, finish the browser authorization, and select <strong>Retry automatic setup</strong>.</span></div>
              <div role="row"><code role="cell">repository target<br />origin remote</code><span role="cell">Paste the full URL of your product repository in <strong>Setup → Connection</strong> and save. Do not paste the workshop repository URL.</span></div>
              <div role="row"><code role="cell">Project Contract<br />Factory Charter</code><span role="cell">Select <strong>Create contract</strong>, review both contract sections, then select <strong>Approve contract and continue</strong>.</span></div>
            </div>
            <p className="warning-note"><strong>Usually safe to ignore:</strong> a warning for port 5050 while the Control Center is open, an unused adapter, or the optional second reviewer identity.</p>
          </section>
          <WorkshopMedia
            src="/screenshots/control-center-preflight-failure.jpg"
            alt="Control Center Current run page with a failed preflight, recovery explanation, exact command, and CLI output"
            label="Failed preflight"
            caption="Open the activity panel, find the first FAIL, fix it, and retry automatic setup."
            width={1440}
            height={980}
          />
          <details className="optional-detail">
            <summary>Example: wrong branch, wrong agent, and missing pytest</summary>
            <p>If those three failures appear together, fix them in this order:</p>
            <ol>
              <li>Run <code>git status</code>. Commit or stash work you need to keep.</li>
              <li>Run <code>git fetch origin</code>, <code>git switch main</code>, and <code>git pull --ff-only origin main</code>.</li>
              <li>If Claude passes but Codex fails, choose <strong>Claude workshop</strong> in <strong>Setup → Connection</strong> and save. Otherwise sign in with <code>codex login</code>.</li>
              <li>Install <code>pytest</code> with the repository&apos;s normal setup command.</li>
              <li>Select <strong>Retry automatic setup</strong>. Continue only when no <code>[FAIL]</code> remains.</li>
            </ol>
          </details>
          <div className="accordion-list">
            <details><summary>The repository is not connected</summary><p>Open <strong>Setup → Connection</strong>, choose <strong>Live</strong>, enter the full product repository URL, and select <strong>Save and connect</strong>. Push its default branch first if it already contains code.</p></details>
            <details><summary>An agent asks for the wrong credentials</summary><p>Open <strong>Setup → Connection</strong> and choose the preset for the CLI you use. Save, sign in to that CLI, then select <strong>Retry automatic setup</strong>.</p></details>
            <details><summary>A planning expert failed</summary><p>Open <strong>Plan → Review plan</strong> and select the failed expert. For an invalid result, select <strong>Apply correction and continue</strong>. For a login or rate-limit error, fix access or choose another agent. If the PRD or repository settings changed, select <strong>Restart planning safely</strong>.</p></details>
            <details><summary>Ticket publication failed</summary><p>Open <strong>Plan → Review plan</strong> and select <strong>Retry ticket publication</strong>. The retry reuses issues already created for this plan. In the CLI, rerun the same <code>factory approve</code> command shown in the error.</p></details>
            <details><summary>A ticket is blocked</summary><p>Open the ticket history and read the last error. Fix that problem, then select <strong>Retry</strong> or run <code>factory retry ISSUE_NUMBER</code>.</p></details>
            <details><summary>A required check still tests removed behavior</summary><p>Compare the failed test with the ticket. If the ticket intentionally removes that behavior, do not restore it. Select <strong>Retry</strong>. The coding agent can update an existing test when the Charter marks existing tests for review.</p></details>
            <details><summary><code>NEEDS YOU</code> says dispatch is paused</summary><p>Too many decisions are waiting for a person. Open the oldest linked item and complete that decision. New ticket work starts again when the queue has space.</p></details>
            <details><summary>A remote claim belongs to an old run</summary><p>Confirm that the old run has stopped. Open the blocked ticket and select <strong>Release abandoned claim</strong>.</p></details>
            <details><summary>The Control Center reports a dependency cycle</summary><p>Two or more tickets depend on each other. Edit the issue dependencies so one ticket can start, then run the factory again.</p></details>
            <details><summary>The issue listener does not import an existing issue</summary><p>This is expected. Its first start records the existing backlog and watches only for issues created afterward. Create a new issue, or stop the listener and follow the normal PRD planning path.</p></details>
            <details><summary>Live planning is slow or inconsistent</summary><p>Use Rehearsal mode to learn the steps. Return to Live mode after agent access and the PRD are stable.</p></details>
            <details><summary>A port or worktree is already in use</summary><p>Stop the old process. Use <code>git worktree list</code> to inspect worktrees before removing one.</p></details>
            <details><summary>I want to repeat the workshop</summary><p>Select <strong>Reset run</strong> in the lower-left navigation. Reset ticket work to keep the approved plan, or enter <code>START OVER</code> to clear local planning history. Use a new repository when you also need a new Live GitHub Project.</p></details>
          </div>
        </section>

        <section id="reference" className="reference-section">
          <div className="section-heading">
            <span className="section-kicker">Keep nearby</span>
            <h2>Core commands</h2>
            <p>The commands you are most likely to repeat.</p>
          </div>
          <details className="optional-detail">
            <summary>Show the CLI command reference</summary>
            <div className="reference-table">
              <div><code>factory control-center</code><span>Open the web interface.</span></div>
              <div><code>factory init</code><span>Create the repository contract.</span></div>
              <div><code>factory approve-contract --live</code><span>Approve and complete automatic Live setup.</span></div>
              <div><code>factory plan PRD</code><span>Start planning from a PRD.</span></div>
              <div><code>factory review product PLAN_ID</code><span>Read the product plan.</span></div>
              <div><code>factory approve-product PLAN_ID</code><span>Approve the product plan.</span></div>
              <div><code>factory approve PLAN_ID</code><span>Create GitHub issues from the approved plan.</span></div>
              <div><code>factory run</code><span>Run available tickets.</span></div>
              <div><code>factory approve-tests ISSUE</code><span>Approve a ticket&apos;s QA test.</span></div>
              <div><code>factory merge ISSUE</code><span>Merge the reviewed commit.</span></div>
              <div><code>factory status</code><span>Show ticket status.</span></div>
              <div><code>factory retry ISSUE</code><span>Retry a blocked ticket.</span></div>
              <div><code>.factory/venv/bin/python demo-app/app.py</code><span>Start the completed workshop app.</span></div>
            </div>
          </details>
          <details className="optional-detail">
            <summary>Factory interfaces for production</summary>
            <p>Open <strong>More tools → Factory interfaces</strong>. Workspace checks name related revisions. Authenticated triggers create deduplicated intake proposals. Reviewed compounding suggests improvements from repeated evidence. The merge steward may synchronize and re-verify a candidate, but it never merges.</p>
          </details>
          <div className="next-links">
            <a href="https://github.com/giolaq/software-refactory-workshop/blob/main/factory/WORKSHOP_OUTLINE.md"><span>FACILITATOR</span><b>Workshop outline</b><i>→</i></a>
            <a href="https://github.com/giolaq/software-refactory-workshop/blob/main/factory/CONFIGURATION.md"><span>REFERENCE</span><b>Agent configuration</b><i>→</i></a>
          </div>
        </section>
      </main>

      <aside className="right-rail">
        <div className="rail-card"><span className="rail-label">PATH</span><strong>{track === "live" ? "Live" : "Rehearsal"}</strong><button type="button" onClick={() => document.getElementById("path")?.scrollIntoView({ behavior: "smooth" })}>Change path</button></div>
        <div className="rail-card"><span className="rail-label">PROGRESS</span><strong>{completed.length} of {steps.length}</strong><div className="progress-track"><span style={{ width: `${progress}%` }} /></div></div>
        <div className="rail-help"><span className="rail-help-icon">?</span><strong>Stuck?</strong><p>Open Current run. Follow Next safe action, or expand Activity and fix the first FAIL.</p><a href="#troubleshooting">Open troubleshooting</a></div>
      </aside>

      <footer>
        <span className="footer-brand"><span className="brand-mark" aria-hidden="true"><i /><i /><i /><i /></span>Software (re)-Factory</span>
        <span>Setup. Plan. Deliver. Review. · workshop-v1.2.0</span>
      </footer>
    </>
  );
}
