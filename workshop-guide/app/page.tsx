"use client";

import { useEffect, useMemo, useState, type CSSProperties, type ReactNode } from "react";

type Track = "rehearsal" | "live";

const steps = [
  { id: "setup", label: "Connect a repository", time: "8 min" },
  { id: "baseline", label: "Run the starter app", time: "5 min" },
  { id: "prd", label: "Save the PRD", time: "7 min" },
  { id: "plan", label: "Review the product plan", time: "15 min" },
  { id: "publish", label: "Publish tickets", time: "18 min" },
  { id: "qa", label: "Review QA tests", time: "10 min" },
  { id: "factory", label: "Run tickets", time: "22 min" },
  { id: "finish", label: "Run the completed app", time: "5 min" },
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
      <section className="instruction-card cli-card" aria-label="CLI path">
        <span className="path-label">CLI</span>
        <h3>Use the CLI</h3>
        <CodeBlock label="CLI">{children}</CodeBlock>
      </section>
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
          <span className="duration-pill">100 minutes</span>
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
              Use the Control Center or CLI to turn a PRD into tickets, code, tests, and a reviewed change. Each step shows the action, result, and next check.
            </p>
            <div className="hero-meta">
              <span><b>Duration:</b> 100 minutes</span>
              <span><b>Format:</b> individual repository</span>
              <span><b>Tools:</b> Claude, Codex, Cursor, or your own CLI</span>
            </div>
            <a className="primary-button" href="#prerequisites">Start the workshop</a>
          </div>
          <div className="factory-map" aria-label="Workshop workflow">
            <div className="map-row"><span className="map-node">Connect</span><i>→</i><span className="map-node node-blue">PRD</span><i>→</i><span className="map-node node-human">Plan</span></div>
            <div className="map-down">↓</div>
            <div className="map-row"><span className="map-node node-purple">Tickets</span><i>→</i><span className="map-node node-blue">Build</span><i>→</i><span className="map-node node-human">Review</span></div>
            <div className="map-down">↓</div>
            <div className="map-row"><span className="map-node node-green">Merge and evidence</span></div>
          </div>
        </section>

        <section id="prerequisites" className="prerequisites-section">
          <div className="section-heading">
            <span className="section-kicker">Before you begin</span>
            <h2>Check your tools</h2>
            <p>Install the required tools before the workshop.</p>
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
                <li>One personal GitHub product repository</li>
                <li>Permission to create issues, branches, and Projects</li>
                <li>A signed-in Claude, Codex, or Cursor CLI</li>
                <li>Network access to GitHub and your model provider</li>
              </ul>
            </article>
          </div>
          <CodeBlock label="Check versions">{`python3 --version
node --version
git --version
${track === "live" ? "gh --version" : ""}`}</CodeBlock>
          <Callout type="warning" title="Use your own repository">
            <p>For Live mode, use a personal GitHub repository. Do not use the facilitator&apos;s repository. Rehearsal mode stays on your computer and does not need GitHub or an agent login.</p>
          </Callout>
        </section>

        <section id="path" className="path-section">
          <div className="section-heading">
            <span className="section-kicker">Choose once</span>
            <h2>Select your path</h2>
            <p>The page changes its commands to match your choice.</p>
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

        <StepSection index={1} id="setup" title="Connect a repository" goal="Open the Control Center and pass preflight." complete={completed.includes("setup")} onToggle={() => toggleStep("setup")}>
          <p>{track === "live" ? "Keep the factory checkout separate from the product repository. The factory uses a managed copy of your product repository." : "Clone a local workshop repository. Rehearsal mode does not use GitHub or a model provider."}</p>
          <CodeBlock label="Terminal 1 — repository setup">{track === "rehearsal" ? `git clone https://github.com/giolaq/software-refactory-workshop.git software-refactory-rehearsal
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
          {track === "live" && <Callout type="tip" title="Choose what the repository contains">
            <ul>
              <li><strong>Guided exercise:</strong> select <strong>Seed the guided Pocket Cinema starter</strong>. The repository receives only the starter app and its factory settings.</li>
              <li><strong>New product:</strong> leave the option clear. The repository starts with factory settings, and agents create the product code from the tickets.</li>
              <li><strong>Existing product:</strong> leave the option clear. The factory keeps the existing code.</li>
            </ul>
          </Callout>}
          {track === "live" ? <Callout type="note" title="Using an existing project instead?">
            <p>Run these commands from the factory checkout. Replace the example path with your product repository.</p>
            <CodeBlock label="Target another Git checkout">{`./factory/factory init --repo /path/to/your-project
# Review factory.project.toml and factory.charter.toml
./factory/factory approve-charter --repo /path/to/your-project --yes
git -C /path/to/your-project add factory.project.toml factory.charter.toml .gitignore
git -C /path/to/your-project commit -m "chore: configure software factory"
git -C /path/to/your-project push origin HEAD
./factory/factory prepare --repo /path/to/your-project
./factory/factory control-center --repo /path/to/your-project`}</CodeBlock>
          </Callout> : null}

          <div className="activity-card launch-card">
            <h3>Open the Control Center</h3>
            <p>Open a second terminal in <code>{track === "live" ? "software-refactory-control" : "software-refactory-rehearsal"}</code>. Run:</p>
            <CodeBlock label="Terminal 2 — keep this running">{`./factory/factory control-center`}</CodeBlock>
            <ol>
              <li>Wait for <code>Factory Control Center: http://127.0.0.1:5050</code>.</li>
              <li>Your browser should open automatically. If it does not, open <a href="http://127.0.0.1:5050">127.0.0.1:5050</a> yourself.</li>
              {track === "live" ? <li>Open <strong>Connect</strong>, choose <strong>Live</strong>, paste your full repository URL, choose the starting content, and save.</li> : null}
              <li>Leave this terminal running for the workshop. Press <code>Ctrl+C</code> only when you want to stop the Control Center.</li>
            </ol>
          </div>

          <WorkshopPaths
            click={<>Open <strong>Connect</strong>. Choose <strong>{track === "live" ? "Live" : "Rehearsal"}</strong>{track === "live" ? <>, enter the repository URL, choose the agents and starting content, then save</> : null}. Create the Project Contract and Charter when prompted. Review them, approve the Charter, and select <strong>Run preflight</strong>.</>}
            whyStopped={<>The factory cannot plan work until it knows how to build and test the repository. A person must also approve the rules in the Charter.</>}
            inspect={<>Check the repository URL, source folders, test folders, required checks, protected paths, and who can merge.</>}
            continueWhen={<>The Charter is <strong>Approved</strong> and preflight has no failures.</>}
          >{track === "live" ? `# Run from the software-refactory-control directory.
./factory/factory checkout https://github.com/YOUR-NAME/YOUR-REPOSITORY \\
  --workspace-root "$CONTROL/.factory/repositories"

# For the guided exercise only:
./factory/factory bootstrap-workshop --repo "$TARGET" --source "$CONTROL"

# For a new or existing product, skip bootstrap-workshop and run:
# ./factory/factory init --repo "$TARGET"

./factory/factory configure --repo "$TARGET" --preset claude-workshop \\
  --github-repository https://github.com/YOUR-NAME/YOUR-REPOSITORY
./factory/factory approve-charter --repo "$TARGET" --yes
./factory/factory publish-setup --repo "$TARGET" --yes
./factory/factory doctor --repo "$TARGET" --full` : `./factory/factory approve-charter --yes
./factory/factory doctor`}</WorkshopPaths>
          <WorkshopMedia
            src="/screenshots/control-center-connect.jpg"
            alt="Control Center Connect screen with agent presets, repository details, and preflight button"
            label="Connect"
            caption="Connect the repository, approve its settings, and run preflight."
            width={1440}
            height={980}
          />
          <Callout type="tip" title="Use the Overview as your guide">
            <p><strong>Current phase</strong> shows what is running. <strong>Next checkpoint</strong> opens the next action that needs you.</p>
          </Callout>
          <Checkpoint><a href="http://127.0.0.1:5050">127.0.0.1:5050</a> is open, the repository is connected, and preflight reports no blocking errors.</Checkpoint>
        </StepSection>

        <StepSection index={2} id="baseline" title="Check the starting repository" goal="Confirm what the agents will change." complete={completed.includes("baseline")} onToggle={() => toggleStep("baseline")}>
          <p>The guided exercise starts with Pocket Cinema. A new product repository has no app yet.</p>
          <WorkshopPaths
            click={<>Open <strong>Overview</strong> and check that the factory is at <strong>Define the PRD</strong>.</>}
            whyStopped={<>No ticket starts before you save and approve a plan. For the guided exercise, the starter app runs as a separate process.</>}
            inspect={<>For the guided exercise, open Pocket Cinema. For a new product, confirm that the repository contains only <code>.gitignore</code> and the two factory settings files.</>}
            continueWhen={<>The starting repository is correct and the Control Center shows <strong>Define the PRD</strong>.</>}
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

        <StepSection index={3} id="prd" title="Save the PRD" goal="Confirm what the agents must build." complete={completed.includes("prd")} onToggle={() => toggleStep("prd")}>
          <WorkshopPaths
            click={<>Open <strong>PRD</strong>. Read the document, edit it if needed, and select <strong>Save PRD</strong>.</>}
            whyStopped={<>Planning uses the saved PRD. Unsaved edits are not sent to an agent.</>}
            inspect={<>Check the target users, required behavior, limits, and proof of success.</>}
            continueWhen={<>The PRD is saved and you can describe the requested product change.</>}
          >{track === "live"
            ? `open "$CONTROL/recipe-app-prd.md"`
            : `open recipe-app-prd.md`}</WorkshopPaths>
          <WorkshopMedia
            src="/screenshots/control-center-prd.jpg"
            alt="Control Center PRD editor with Save PRD and Start Product Review buttons"
            label="PRD"
            caption="Read the request, make any needed edits, and save it."
            width={1440}
            height={980}
          />
          <Checkpoint>The PRD is saved and describes the TableStory result.</Checkpoint>
        </StepSection>

        <StepSection index={4} id="plan" title="Review the product plan" goal="Approve the user problem and expected behavior." complete={completed.includes("plan")} onToggle={() => toggleStep("plan")}>
          <WorkshopPaths
            click={<>In <strong>PRD</strong>, choose {track === "rehearsal" ? "Rehearsal" : "Live"} and select <strong>Start Product Review</strong>. Open <strong>Planning</strong>, then open <strong>Product Review</strong>.</>}
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
            alt="Control Center Planning screen showing the expert stages and human approval gates"
            label="Planning"
            caption="Open Product Review. Yellow cards need a decision from you."
            width={1440}
            height={980}
          />
          <Checkpoint>Product Review shows <strong>Approved</strong>.</Checkpoint>
        </StepSection>

        <StepSection index={5} id="publish" title="Publish tickets" goal="Review the technical plan and create the work items." complete={completed.includes("publish")} onToggle={() => toggleStep("publish")}>
          <WorkshopPaths
            click={<>In <strong>Planning</strong>, select <strong>Run remaining experts</strong>. Open each result. Answer any questions, approve alignment, and select <strong>Create tickets</strong>.</>}
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

        <StepSection index={6} id="qa" title="Review QA tests" goal="Confirm that the proposed test detects the missing behavior." complete={completed.includes("qa")} onToggle={() => toggleStep("qa")}>
          <WorkshopPaths
            click={<>Open <strong>Tickets</strong> and select <strong>Run one cycle</strong>. Open ticket <strong>#1</strong>, select <strong>Tests</strong>, and review the proposal. Return to <strong>Summary</strong> to approve it.</>}
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

        <StepSection index={7} id="factory" title="Run tickets" goal="Run the planned work and handle each human checkpoint." complete={completed.includes("factory")} onToggle={() => toggleStep("factory")}>
          <WorkshopPaths
            click={<>Open <strong>Tickets</strong> and select <strong>Run factory</strong>. Keep the page open. When <strong>NEEDS YOU</strong> appears, open the linked ticket.</>}
            whyStopped={<>For each ticket, the factory assigns work, runs tests and required checks, and asks a separate agent to review the change. It stops when a check fails or a person must decide.</>}
            inspect={<>Open the ticket tabs to read the task, live log, changed files, tests, checks, and code review. Before merge, confirm that the approved commit matches the pull request.</>}
            continueWhen={<>Code review approves the commit and you select <strong>Merge exact revision</strong>. The ticket then moves to Done.</>}
          >{track === "live" ? `gh project view <project-number> --owner "@me" --web
./factory/factory run --repo "$TARGET"` : `./factory/factory run --mock --scenario recipe-rebrand`}</WorkshopPaths>
          <WorkshopMedia
            src="/screenshots/control-center-tickets.jpg"
            alt="Control Center Tickets board with backlog and QA Review columns"
            label="Ticket board"
            caption="Open a ticket to inspect its task, log, files, tests, checks, and review."
            width={1440}
            height={980}
          />
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
            alt="Control Center Overview showing current phase, next checkpoint, progress, and human decisions"
            label="Overview"
            caption="Current phase shows what is running. Next checkpoint opens your next action."
            width={1440}
            height={980}
          />
          <div className="activity-card">
            <h3>What happens to each ticket</h3>
            <ol>
              <li>The Supervisor selects a ticket whose dependencies are complete.</li>
              <li>QA adds a test for the requested behavior.</li>
              <li>The coding agent changes an isolated Git worktree.</li>
              <li>The factory runs tests and repository checks.</li>
              <li>A separate agent reviews the pull request.</li>
              <li>You decide whether to merge the approved commit.</li>
            </ol>
          </div>
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

        <StepSection index={8} id="finish" title="Run the completed app" goal="Start TableStory and open its supported layouts." complete={completed.includes("finish")} onToggle={() => toggleStep("finish")}>
          <WorkshopPaths
            click={<>Open <strong>Run app</strong> in the Control Center and copy the startup command.</>}
            whyStopped={<>The page becomes available when every ticket is Done.</>}
            inspect={<>Open <code>http://127.0.0.1:5000/</code> for mobile and desktop, or <code>http://127.0.0.1:5000/?mode=tv</code> for television.</>}
            continueWhen={<>TableStory loads in the browser. Keep the terminal running while you use it, then press <code>Ctrl+C</code> to stop the server.</>}
          >{track === "live" ? `cd "$TARGET"
"$CONTROL/.factory/venv/bin/python" demo-app/app.py` : `.factory/venv/bin/python demo-app/app.py`}</WorkshopPaths>
          <Checkpoint>TableStory opens from the repository produced by the factory.</Checkpoint>
        </StepSection>

        <section className="completion-panel">
          <div className="completion-ring" style={{ "--progress": `${progress}%` } as CSSProperties}><span>{progress}%</span></div>
          <div><span className="section-kicker">Workshop progress</span><h2>{progress === 100 ? "Factory complete" : "Keep going"}</h2><p>{completed.length} of {steps.length} steps marked complete.</p></div>
          {progress < 100 && <a className="primary-button" href={`#${steps.find((step) => !completed.includes(step.id))?.id ?? "setup"}`}>Next step</a>}
        </section>

        <section id="troubleshooting" className="support-section">
          <div className="section-heading">
            <span className="section-kicker">When something stops</span>
            <h2>Troubleshooting</h2>
            <p>Start with the symptom you see.</p>
          </div>
          <div className="accordion-list">
            <details><summary><code>doctor</code> reports a failure</summary><p>Fix the first <strong>FAIL</strong> result. Then run preflight again.</p></details>
            <details><summary>The repository is not connected</summary><p>Open <strong>Connect</strong>, choose <strong>Live</strong>, enter the full repository URL, and save. Push the default branch if the repository already contains code. Then run preflight again.</p></details>
            <details><summary>An agent asks for the wrong credentials</summary><p>Open <strong>Connect</strong> and choose the preset for the agent you use. Save, sign in to that agent&apos;s CLI, and run preflight again.</p></details>
            <details><summary>A planning expert failed</summary><p>Open <strong>Planning</strong> and select the failed expert. For an invalid result, select <strong>Apply correction and continue</strong>. For a login or rate-limit error, fix access or choose another agent. If the PRD or repository settings changed, select <strong>Restart planning safely</strong>.</p></details>
            <details><summary>Ticket publication failed</summary><p>Open <strong>Planning</strong> and select <strong>Retry ticket publication</strong>. The retry reuses issues that were already created for this plan. In the CLI, rerun the same <code>factory approve</code> command shown in the error.</p></details>
            <details><summary>A ticket is blocked</summary><p>Open the ticket history and read the last error. Fix that problem, then select <strong>Retry</strong> or run <code>factory retry ISSUE_NUMBER</code>.</p></details>
            <details><summary>A required check still tests removed behavior</summary><p>Compare the failed test with the ticket. If the ticket intentionally removes that behavior, do not restore it. Select <strong>Retry</strong>. The coding agent can update an existing test when the Charter marks existing tests for review.</p></details>
            <details><summary><code>NEEDS YOU</code> says dispatch is paused</summary><p>Too many decisions are waiting for a person. Open the oldest linked item and complete that decision. New ticket work starts again when the queue has space.</p></details>
            <details><summary>A remote claim belongs to an old run</summary><p>Confirm that the old run has stopped. Open the blocked ticket and select <strong>Release abandoned claim</strong>.</p></details>
            <details><summary>The Control Center reports a dependency cycle</summary><p>Two or more tickets depend on each other. Edit the issue dependencies so one ticket can start, then run the factory again.</p></details>
            <details><summary>Live planning is slow or inconsistent</summary><p>Use Rehearsal mode to learn the steps. Return to Live mode after agent access and the PRD are stable.</p></details>
            <details><summary>A port or worktree is already in use</summary><p>Stop the old process. Use <code>git worktree list</code> to inspect worktrees before removing one.</p></details>
            <details><summary>I want to repeat the workshop</summary><p>Open <strong>Reset or start again</strong>. Reset ticket work to keep the approved plan, or enter <code>START OVER</code> to clear local planning history. Use a new repository when you also need a new Live GitHub Project.</p></details>
          </div>
        </section>

        <section id="reference" className="reference-section">
          <div className="section-heading">
            <span className="section-kicker">Keep nearby</span>
            <h2>Core commands</h2>
            <p>The commands you are most likely to repeat.</p>
          </div>
          <div className="reference-table">
            <div><code>factory control-center</code><span>Open the web interface.</span></div>
            <div><code>factory doctor --full</code><span>Check tools, access, and repository settings.</span></div>
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
          <div className="next-links">
            <a href="https://github.com/giolaq/software-refactory-workshop/blob/main/factory/WORKSHOP_OUTLINE.md"><span>FACILITATOR</span><b>Workshop outline</b><i>→</i></a>
            <a href="https://github.com/giolaq/software-refactory-workshop/blob/main/factory/CONFIGURATION.md"><span>REFERENCE</span><b>Agent configuration</b><i>→</i></a>
          </div>
        </section>
      </main>

      <aside className="right-rail">
        <div className="rail-card"><span className="rail-label">PATH</span><strong>{track === "live" ? "Live" : "Rehearsal"}</strong><button type="button" onClick={() => document.getElementById("path")?.scrollIntoView({ behavior: "smooth" })}>Change path</button></div>
        <div className="rail-card"><span className="rail-label">PROGRESS</span><strong>{completed.length} of {steps.length}</strong><div className="progress-track"><span style={{ width: `${progress}%` }} /></div></div>
        <div className="rail-help"><span className="rail-help-icon">?</span><strong>Stuck?</strong><p>Read the ticket event history first. It records the reason for every state change.</p><a href="#troubleshooting">Open troubleshooting</a></div>
      </aside>

      <footer>
        <span className="footer-brand"><span className="brand-mark" aria-hidden="true"><i /><i /><i /><i /></span>Software (re)-Factory</span>
        <span>Connect. Plan. Build. Verify. · workshop-v1.1.2</span>
      </footer>
    </>
  );
}
