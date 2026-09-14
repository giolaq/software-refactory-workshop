"use client";

import { useState, type ReactNode } from "react";

type Track = "rehearsal" | "live";

const steps = [
  { id: "setup", label: "Finish Setup" },
  { id: "baseline", label: "Check the starting app" },
  { id: "prd", label: "Write requirements" },
  { id: "plan", label: "Approve Product Review" },
  { id: "publish", label: "Create tickets" },
  { id: "qa", label: "Approve Acceptance Tests" },
  { id: "factory", label: "Deliver tickets" },
  { id: "finish", label: "Review the app" },
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
  cliPurpose,
  cliDirectory,
  cliAfter,
  children,
}: {
  click: ReactNode;
  whyStopped?: ReactNode;
  inspect: ReactNode;
  continueWhen: ReactNode;
  cliPurpose: ReactNode;
  cliDirectory: ReactNode;
  cliAfter?: ReactNode;
  children: string;
}) {
  return (
    <div className="instruction-paths">
      <section className="instruction-card control-center-card" aria-label="Control Center path">
        <span className="path-label">Control Center</span>
        <h3>Use the Control Center</h3>
        <dl className="instruction-list">
          <div><dt>Do this</dt><dd>{click}</dd></div>
          <div><dt>What happens</dt><dd>{whyStopped ?? <>It stops when it needs your decision or a check fails. <strong>Current phase</strong> says what to do next.</>}</dd></div>
          <div><dt>Check</dt><dd>{inspect}</dd></div>
          <div><dt>Continue when</dt><dd>{continueWhen}</dd></div>
        </dl>
      </section>
      <details className="instruction-card cli-card" aria-label="CLI path">
        <summary><span className="path-label">CLI</span><strong>Use the CLI</strong></summary>
        <dl className="cli-context">
          <div><dt>Purpose</dt><dd>{cliPurpose}</dd></div>
          <div><dt>Run from</dt><dd>{cliDirectory}</dd></div>
          <div><dt>Success looks like</dt><dd>{continueWhen}</dd></div>
        </dl>
        <CodeBlock label="CLI">{children}</CodeBlock>
        {cliAfter}
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
      {src.startsWith("/screenshots/control-center-") && <p className="field-help">Local Rehearsal example. Ticket names and agents may differ.</p>}
    </figure>
  );
}

function StepSection({
  index,
  id,
  title,
  goal,
  children,
}: {
  index: number;
  id: string;
  title: string;
  goal: string;
  children: ReactNode;
}) {
  return (
    <section id={id} className="lesson">
      <div className="lesson-heading">
        <span className="step-number">{index}</span>
        <div>
          <span className="lesson-kicker">Step {index}</span>
          <h2>{title}</h2>
        </div>
      </div>
      <div className="lesson-body">
        <p className="goal"><strong>Goal:</strong> {goal}</p>
        {children}
      </div>
    </section>
  );
}

export default function Home() {
  const [track, setTrack] = useState<Track>("live");
  const [menuOpen, setMenuOpen] = useState(false);

  function chooseTrack(next: Track) {
    setTrack(next);
    document.getElementById("prerequisites")?.scrollIntoView({ behavior: "smooth" });
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
        <nav aria-label="Workshop sections">
          <p className="nav-label">Start</p>
          <a href="#overview" onClick={() => setMenuOpen(false)}>Overview</a>
          <a href="#path" onClick={() => setMenuOpen(false)}>Choose a path</a>
          <a href="#prerequisites" onClick={() => setMenuOpen(false)}>Prerequisites</a>
          <p className="nav-label">Workshop</p>
          {steps.map((step, index) => (
            <a key={step.id} href={`#${step.id}`} onClick={() => setMenuOpen(false)}>
              <span>{index + 1}</span>
              <span>{step.label}</span>
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
              Transform Pocket Cinema into TableStory, a recipe app. Follow these steps in your own repository, using the Control Center or CLI.
            </p>
            <div className="hero-meta">
              <span><b>Duration:</b> 3 hours</span>
              <span><b>Format:</b> individual repository</span>
              <span><b>Tools:</b> Claude, Codex, Cursor, or your own CLI</span>
            </div>
            <a className="primary-button" href="#path">Start the workshop</a>
          </div>
          <div className="factory-map" aria-label="Workshop workflow">
            <div className="map-row"><span className="map-node">1 · Agree</span><i>→</i><span className="map-node node-blue">2 · Build</span></div>
            <div className="map-down">↓</div>
            <div className="map-row"><span className="map-node node-purple">3 · Inspect evidence</span><i>→</i><span className="map-node node-human">4 · Accept</span></div>
            <div className="map-down">↓</div>
            <div className="map-row"><span className="map-node node-green">Running app and evidence</span></div>
          </div>
        </section>

        <section id="path" className="path-section">
          <div className="section-heading"><h2>Select your path</h2><p>Use Live for the workshop. Use Rehearsal if your facilitator asks you to follow the simulated run.</p></div>
          <div className="path-grid">
            <button type="button" aria-pressed={track === "live"} className={`path-card${track === "live" ? " path-selected" : ""}`} onClick={() => chooseTrack("live")}>
              <strong>Live · workshop path</strong><span>Your own GitHub repository and a signed-in agent CLI.</span>
            </button>
            <button type="button" aria-pressed={track === "rehearsal"} className={`path-card${track === "rehearsal" ? " path-selected" : ""}`} onClick={() => chooseTrack("rehearsal")}>
              <strong>Rehearsal · simulated fallback</strong><span>Local sample changes. No agent-provider calls or GitHub writes.</span>
            </button>
          </div>
        </section>

        <section id="prerequisites" className="prerequisites-section">
          <div className="section-heading">
            <span className="section-kicker">Before the session: finish Setup and check the starting app</span>
            <h2>Install and sign in</h2>
          </div>
          <div className="prerequisites-grid">
            <article>
              <span className="requirement-label">Everyone</span>
              <h3>Local tools</h3>
              <ul>
                <li>macOS, Linux, or Windows with WSL2</li>
                <li>Python 3.11+ with virtual environments</li>
                <li>Node.js 22.13+, Git, and a modern browser</li>
                <li>Ports 5000 and 5050 available</li>
              </ul>
            </article>
            <article>
              <span className="requirement-label">Live path</span>
              <h3>Accounts and access</h3>
              <ul>
                <li>GitHub CLI (<code>gh</code>), signed in, with Projects access</li>
                <li>One personal GitHub product repository and its full URL</li>
                <li>Permission to create issues, branches, pull requests, and GitHub Projects</li>
                <li>One signed-in agent CLI: Claude, Codex, Cursor, or your adapter</li>
                <li>Network access to GitHub and your model provider</li>
              </ul>
            </article>
          </div>
          <p>On Windows, run these commands inside WSL2. You do not need AWS, Docker, or an OpenAI API key for the authenticated CLI path. Live agent use follows your provider subscription and limits.</p>
          <CodeBlock label="Verify before continuing">{`python3 --version
node --version
git --version
git config user.name
git config user.email
${track === "live" ? `gh --version
gh auth status
gh auth refresh -s project` : ""}`}</CodeBlock>
          <p>If the Git name or email is blank, set your commit identity with <code>git config --global user.name &quot;Your name&quot;</code> and <code>git config --global user.email &quot;your-email&quot;</code>. For Live, open only the instructions for your selected provider below.</p>
          <details>
            <summary>Use Claude Code</summary>
            <p>Install Claude Code using its official instructions, then authenticate and check the session.</p>
            <CodeBlock label="Sign in to Claude">{`claude auth login
claude auth status --text`}</CodeBlock>
            <p><a href="https://code.claude.com/docs/en/setup">Claude Code installation</a></p>
          </details>
          <details>
            <summary>Use Codex CLI</summary>
            <p>Install Codex CLI, then use your authenticated CLI session. You do not need to enter an API key in the Factory.</p>
            <CodeBlock label="Sign in to Codex">{`codex login
codex login status`}</CodeBlock>
            <p>If this asks for <code>OPENAI_API_KEY</code>, an older Codex installation may be first on your PATH. Check <code>codex exec --help</code>. Update Codex using its official installation instructions, then sign in again. If you have a current CLI elsewhere, set <code>FACTORY_CODEX_BIN</code> to its full executable path, check its <code>login status</code>, and start the Control Center from that same terminal.</p>
            <p><a href="https://developers.openai.com/codex/cli/">Codex CLI installation</a></p>
          </details>
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
            <p>Live uses your personal repository. Do not use the facilitator&apos;s. Rehearsal changes a disposable local clone and pushes nothing to GitHub. Cloning and installing dependencies still require network access.</p>
            {track === "rehearsal" && <p>Create your personal repository on <a href="https://github.com/new">GitHub</a> before class too; Rehearsal leaves it unused. No coding-agent login is required for the simulated run.</p>}
          </Callout>
          <details className="checkout-orientation">
            <summary>Optional CLI: understand the two checkouts</summary>
            <div className="checkout-map">
              <article><span>CONTROL</span><strong>Factory checkout</strong><code>software-refactory-control</code></article>
              <div className="checkout-arrow" aria-hidden="true">controls →</div>
              <article><span>TARGET</span><strong>Product checkout</strong><code>.factory/repositories/you/product</code></article>
            </div>
            <p>{track === "live" ? "Run Factory commands in CONTROL; agents change TARGET." : "Rehearsal uses only the Factory checkout."}</p>
          </details>
        </section>

        <StepSection index={1} id="setup" title="Finish Setup" goal="Open the Control Center, connect the correct repository, and pass its first-time checks.">
          {track === "live" && <>
            <h3>Sign in to GitHub</h3>
            <CodeBlock label="GitHub sign-in">{`gh auth login --web --git-protocol https --scopes project`}</CodeBlock>
            <p>Follow the browser sign-in instructions and authorize access. If you already completed the GitHub checks above, skip this command.</p>
          </>}
          <h3>Download the factory</h3>
          <p>Replace <code>SESSION_TAG</code> with the session release tag your facilitator gives you. Open a terminal in the folder where you keep your projects, then run:</p>
          <CodeBlock label="Download and prepare — run once">{track === "rehearsal" ? `git clone --branch SESSION_TAG https://github.com/giolaq/software-refactory-workshop.git software-refactory-rehearsal
cd software-refactory-rehearsal
./setup_demo.sh --scenario recipe-rebrand
git remote remove origin` : `git clone --branch SESSION_TAG https://github.com/giolaq/software-refactory-workshop.git software-refactory-control
cd software-refactory-control
./setup_demo.sh --scenario recipe-rebrand`}</CodeBlock>
          <p>The setup command installs the workshop dependencies and prepares the local starter. It does not create GitHub tickets. Do not rerun it to restart an existing workshop run; use the Control Center&apos;s Reset run action.</p>
          {track === "live" && <>
            <h3>Create your workshop repository</h3>
            <ol>
              <li>Open <a href="https://github.com/new" target="_blank" rel="noreferrer">GitHub → New repository</a>. Use your personal account as the owner.</li>
              <li>Name it <code>factory-tablestory-workshop</code> and select <strong>Private</strong>. If that name already exists, choose another.</li>
              <li>Leave README, .gitignore, and license unselected. Select <strong>Create repository</strong>.</li>
              <li>Copy its page URL. You will paste it into the Control Center in the next step. Do not clone this repository yourself.</li>
            </ol>
            <p>If you already created an empty personal repository for this session, use it instead.</p>
          </>}
          <div className="activity-card launch-card">
            <span className="activity-label">Keep this terminal running</span>
            <h3>Start the Control Center</h3>
            <p>In the same terminal, still inside <code>{track === "live" ? "software-refactory-control" : "software-refactory-rehearsal"}</code>, run:</p>
            <CodeBlock label="Start the Control Center — keep this running">{`./factory/factory control-center`}</CodeBlock>
            <ol>
              <li>Wait for <code>Factory Control Center: http://127.0.0.1:5050</code>.</li>
              <li>The browser should open automatically. Otherwise open <a href="http://127.0.0.1:5050">127.0.0.1:5050</a>.</li>
              <li>Leave this terminal running. <code>Ctrl+C</code> stops the Control Center.</li>
            </ol>
            <p>Continue in the browser. You need another terminal only if you choose the optional CLI instructions or need to repair an error.</p>
          </div>

          <h3>Complete Setup in three steps</h3>
          <ol className="setup-sequence">
            <li><span>1</span><div><strong>Connect</strong><p>Open <strong>Setup → Connection</strong>. Select <strong>{track === "live" ? "Live" : "Rehearsal"}</strong>, <strong>Standard</strong>, and your agent preset — which AI CLI the factory will use. {track === "live" ? <>Paste <em>your product repository</em> URL. Select <strong>Seed the guided Pocket Cinema starter</strong> for this exercise; leave it clear for your own existing product.</> : <>No GitHub settings are needed.</>} Select <strong>Save and connect</strong>.</p></div></li>
            <li><span>2</span><div><strong>Create contract</strong><p>Select <strong>Create contract</strong>. The factory scans the repository and writes its settings: which folders it may change, and the checks every change must pass. No coding agent runs.</p></div></li>
            <li><span>3</span><div><strong>Review and approve</strong><p>Open <strong>Review repository model</strong> and <strong>Review operating policy</strong>. If they match the repository, select <strong>Approve contract and continue</strong>.</p></div></li>
          </ol>
          <details className="optional-detail setup-terms">
            <summary>What Tier, Merge, and Gates mean</summary>
            <p><strong>Tier</strong> is how much damage a wrong change could do. <strong>Merge</strong> says who makes the final merge decision — here, a human: you. <strong>Gates</strong> are the checks a change must pass before it can merge.</p>
          </details>

          <Callout type="note" title="What happens after you approve">
            <p>After Step 3, the factory publishes the contract (Live mode), prepares the environment, checks gates, and runs preflight. <strong>Activity and CLI output</strong> shows each substep and stops at the first error.</p>
          </Callout>

          <Callout type="warning" title="If automatic setup stops, fix the first error">
            <p>Open <strong>Activity and CLI output</strong>, fix the first <code>[FAIL]</code> with the <a href="#preflight-recovery">recovery table</a>, then retry. A <code>[WARN]</code> does not block the workshop.</p>
          </Callout>

          <WorkshopPaths
            click={<>Use <strong>Setup → Connection</strong> and complete the three numbered steps above.</>}
            whyStopped={<>The factory will not plan until the repository contract is approved and its automatic environment and preflight checks pass.</>}
            inspect={<>Confirm the product repository, source and test folders, required checks, selected agent preset, and merge authority.</>}
            continueWhen={<>Step 3 says <strong>Approved and ready</strong> and Activity output contains no <code>[FAIL]</code>.</>}
            cliPurpose={<>Connect the product repository and approve its contract. {track === "live" && <>Open another terminal in the Factory checkout. Set the three variables below and keep that terminal for later CLI commands. If you already connected in the browser, skip the remaining setup commands. Use <code>claude-workshop</code>, <code>codex-workshop</code>, or <code>cursor-workshop</code> for your selected CLI.</>}</>}
            cliDirectory={track === "live" ? <><code>software-refactory-control</code> (the Factory checkout)</> : <><code>software-refactory-rehearsal</code></>}
          >{track === "live" ? `# Open another terminal in software-refactory-control.
# Replace your-account/factory-tablestory-workshop with your repository.
REPOSITORY=your-account/factory-tablestory-workshop
export CONTROL="$PWD"
export TARGET="$CONTROL/.factory/repositories/$REPOSITORY"

./factory/factory checkout "https://github.com/$REPOSITORY" \\
  --workspace-root "$CONTROL/.factory/repositories"

# For the guided exercise only:
./factory/factory bootstrap-workshop --repo "$TARGET" --source "$CONTROL"

# For a new or existing product, skip bootstrap-workshop and run:
# ./factory/factory init --repo "$TARGET"

AGENT_PRESET=claude-workshop # or codex-workshop or cursor-workshop
./factory/factory configure --repo "$TARGET" --preset "$AGENT_PRESET" \\
  --github-repository "https://github.com/$REPOSITORY"
./factory/factory approve-contract --repo "$TARGET" --live --yes` : `# setup_demo.sh already created the local contract.
./factory/factory approve-contract --yes`}</WorkshopPaths>
          <WorkshopMedia
            src="/screenshots/control-center-connect.jpg"
            alt="Control Center Setup screen with Connect, Create contract, and Review and approve steps"
            label="Setup → Connection"
            caption="Three decisions: connect, create the contract, then review and approve."
            width={1440}
            height={980}
          />
          <Callout type="tip" title="Use Current run as your guide">
            <p><strong>Current phase</strong> explains the state. <strong>Next safe action</strong> is the one thing to do.</p>
          </Callout>
          <Checkpoint><a href="http://127.0.0.1:5050">127.0.0.1:5050</a> is open, the correct repository is shown, Step 3 says <strong>Approved and ready</strong>, and Activity reports no failures.</Checkpoint>
        </StepSection>

        <StepSection index={2} id="baseline" title="Check the starting app" goal="Confirm what the factory will change.">
          <p>Try Pocket Cinema’s search, film details, and watchlist. You will transform these into recipe discovery, cooking steps, and My Cookbook.</p>
          <WorkshopPaths
            click={<>Open <strong>Review → Run app</strong> and select <strong>Start app</strong>. Open the displayed browser link, inspect the baseline, then select <strong>Stop app</strong> before planning.</>}
            whyStopped={<>No ticket starts before you save and approve a plan; the starter app runs separately.</>}
            inspect={<>Confirm that Pocket Cinema shows films, film details, and a watchlist. This is the baseline, not the recipe product.</>}
            continueWhen={<>The starting repository is correct and the Control Center points to <strong>Plan → Requirements</strong>.</>}
            cliPurpose={<>Open the Pocket Cinema starter application.</>}
            cliDirectory={track === "live" ? <><code>software-refactory-control</code> with <code>CONTROL</code> and <code>TARGET</code> set</> : <><code>software-refactory-rehearsal</code></>}
          >{track === "live"
            ? `"$CONTROL/.factory/venv/bin/python" "$TARGET/demo-app/app.py"`
            : `.factory/venv/bin/python demo-app/app.py`}</WorkshopPaths>
          <WorkshopMedia
            src="/screenshots/pocket-cinema-before.webp"
            alt="Pocket Cinema application before the workshop change"
            label="Expected baseline"
            caption="A working media application that will become TableStory."
            width={1440}
            height={980}
          />
          <Checkpoint>Pocket Cinema opens and you have checked its film-browsing journey.</Checkpoint>
        </StepSection>

        <StepSection index={3} id="prd" title="Write requirements" goal="Describe the result you want, in your own words.">
          <WorkshopPaths
            click={<>Open <strong>Plan → Requirements</strong>. Replace the draft with <code>recipe-app-prd.md</code> from the Factory checkout. Edit it as directed by your facilitator. The draft saves automatically.</>}
            whyStopped={<>No planning role runs until you select <strong>Start Product Review</strong>.</>}
            inspect={<>Keep the full transformation. Trace this journey: find a recipe by ingredient → read its cooking steps → save it to My Cookbook.</>}
            continueWhen={<>The save indicator is current and you can describe the requested product change.</>}
            cliPurpose={<>Open the workshop PRD in your local editor.</>}
            cliDirectory={track === "live" ? <><code>software-refactory-control</code></> : <><code>software-refactory-rehearsal</code></>}
          >{track === "live"
            ? `\${EDITOR:-vi} "$CONTROL/recipe-app-prd.md"`
            : `\${EDITOR:-vi} recipe-app-prd.md`}</WorkshopPaths>
          <WorkshopMedia
            src="/screenshots/control-center-prd.jpg"
            alt="Control Center Plan and Requirements screen with an auto-saving PRD editor and Start Product Review button"
            label="Plan → Requirements"
            caption="The draft saves automatically."
            width={1440}
            height={980}
          />
          <Checkpoint>The saved PRD requests the full Pocket Cinema → TableStory product transformation in both modes.</Checkpoint>
        </StepSection>

        <StepSection index={4} id="plan" title="Approve Product Review" goal="Approve the user problem and expected behavior before technical design.">
          <WorkshopPaths
            click={<>In <strong>Plan → Requirements</strong>, select <strong>Start Product Review</strong>. Open <strong>Plan → Review plan</strong> and read <strong>Product Review</strong>. Then select the <strong>Approve product</strong> card and its <strong>Approve product</strong> button.</>}
            whyStopped={<>A person must approve the product plan before technical planning starts.</>}
            inspect={<>Write one observable outcome for the cooking journey. Compare it with the plan. If you request a correction, read the updated Product Review before approving.</>}
            continueWhen={<>The product plan is clear, testable, and approved.</>}
            cliPurpose={<>Generate, inspect, revise if needed, and approve Product Review.</>}
            cliDirectory={track === "live" ? <><code>software-refactory-control</code>; commands target <code>$TARGET</code></> : <><code>software-refactory-rehearsal</code></>}
            cliAfter={<>
              <div>
                <h4>Optional: request changes before approval</h4>
                <p>Skip this if the plan is clear and testable. Otherwise, replace the example feedback with your correction. Read the revised Product Review; repeat if needed.</p>
                <CodeBlock label="Revise and read again">{track === "live" ? `./factory/factory revise "$PLAN_ID" product --repo "$TARGET" \\
  --feedback "Specify what happens when an ingredient search returns no recipes."
./factory/factory review product "$PLAN_ID" --repo "$TARGET"` : `./factory/factory revise "$PLAN_ID" product --mock \\
  --feedback "Specify what happens when an ingredient search returns no recipes."
./factory/factory review product "$PLAN_ID"`}</CodeBlock>
              </div>
              <p>Approve only after reading the latest Product Review and accepting its scope and behavior.</p>
              <CodeBlock label="Approve the reviewed plan">{track === "live"
                ? `./factory/factory approve-product "$PLAN_ID" --repo "$TARGET"`
                : `./factory/factory approve-product "$PLAN_ID"`}</CodeBlock>
            </>}
          >{track === "live" ? `./factory/factory plan "$CONTROL/recipe-app-prd.md" --repo "$TARGET"
echo "Paste the plan ID from the output, then press Enter:"
read -r PLAN_ID
./factory/factory review product "$PLAN_ID" --repo "$TARGET"` : `./factory/factory plan recipe-app-prd.md --mock
echo "Paste the plan ID from the output, then press Enter:"
read -r PLAN_ID
./factory/factory review product "$PLAN_ID"`}</WorkshopPaths>
          <WorkshopMedia
            src="/screenshots/control-center-planning.jpg"
            alt="Control Center Plan and Review plan screen showing expert stages and human approval gates"
            label="Plan → Review plan"
            caption="Read Product Review, then open the Approve product card. Yellow cards need your decision."
            width={1440}
            height={980}
          />
          <Checkpoint>Product Review shows <strong>Approved</strong>. This approves intent; it does not start technical planning or coding.</Checkpoint>
        </StepSection>

        <StepSection index={5} id="publish" title="Create tickets" goal="Check the proposed work before publishing it.">
          <WorkshopPaths
            click={<>Select <strong>Run remaining experts</strong> in <strong>Plan → Review plan</strong>. Review each result. For changes: select the stage → describe your change → <strong>Request revision</strong>. Read it, then <strong>Confirm revision and continue</strong>. Resolve required approvals. Finish with <strong>Approve alignment → Approve and create tickets</strong>.</>}
            whyStopped={<>Resolve blockers and approve the plan before creating tickets.</>}
            inspect={<>Trace the cooking journey through the tickets. Challenge unnecessary dependencies. Confirm full coverage: recipe data, APIs, branding, mobile/TV, and cleanup. Live ticket counts vary; Rehearsal has five.</>}
            continueWhen={track === "live" ? <>The GitHub Project contains the planned issues.</> : <>The Tickets page contains the planned work.</>}
            cliPurpose={<>Review technical planning and publish approved tickets.</>}
            cliDirectory={track === "live" ? <><code>software-refactory-control</code>; commands target <code>$TARGET</code></> : <><code>software-refactory-rehearsal</code></>}
          >{track === "rehearsal" ? `./factory/factory continue-plan "$PLAN_ID" --mock
./factory/factory review alignment "$PLAN_ID"
./factory/factory approve-rehearsal "$PLAN_ID" --scenario recipe-rebrand
./factory/factory run --mock --scenario recipe-rebrand --dry-run` : `./factory/factory continue-plan "$PLAN_ID" --repo "$TARGET"
./factory/factory review alignment "$PLAN_ID" --repo "$TARGET"
./factory/factory approve "$PLAN_ID" --repo "$TARGET" \\
  --new-project-title "Factory Workshop"`}</WorkshopPaths>
          <Callout type="note" title="What planning creates">
            <p>Architecture → Program Design → Vertical Slices run sequentially. Publishing tickets does not start delivery.</p>
          </Callout>
          <WorkshopMedia
            src="/screenshots/control-center-product-approved.jpg"
            alt="Approved Product Review with Run remaining experts available and technical stages still pending"
            label="After product approval"
            caption="Select Run remaining experts. Wait for their results before approving alignment."
            width={1440}
            height={980}
          />
          <WorkshopMedia
            src="/screenshots/control-center-create-tickets.jpg"
            alt="Alignment approval panel with the Approve and create tickets button"
            label="After technical planning"
            caption="Inspect the proposed tickets, then approve alignment. Live creates GitHub issues; Rehearsal creates local tickets."
            width={1440}
            height={980}
          />
          <details>
            <summary>Example: revise the architecture before creating tickets</summary>
            <WorkshopMedia
              src="/screenshots/control-center-plan-revision.jpg"
              alt="Revised architecture with Request revision and Confirm revision and continue controls"
              label="Review a planning revision"
              caption="Read the revised artifact. Confirm to regenerate the outdated downstream stages, or request another change. Rehearsal uses sample artifacts; Live applies your custom feedback."
              width={1440}
              height={980}
            />
          </details>
          <Checkpoint>{track === "live" ? "The GitHub Project shows the new issues." : "The Tickets page shows the planned work."}</Checkpoint>
        </StepSection>

        <StepSection index={6} id="qa" title="Approve Acceptance Tests" goal="Confirm that the proposed test detects the missing behavior.">
          <WorkshopPaths
            click={<>Open <strong>Deliver → Tickets</strong>. Open <strong>Run options</strong> and select <strong>Run one cycle</strong>. Open the ticket labeled <strong>QA Review</strong>, select <strong>Tests</strong>, and read the proposed test and baseline failure. Approve it there, or request a revision.</>}
            whyStopped={<>The factory runs the new test before implementation. <strong>RED PROVED</strong> records an assertion failure on the baseline. Read the assertion to confirm it tests the requested behavior.</>}
            inspect={<>Decide approve or revise, and explain which assertion proves the requirement. Setup, syntax, and unrelated failures are not valid behavior evidence.</>}
            continueWhen={<>Tests approved? Go to <a href="#factory">Deliver tickets</a> and select <strong>Run factory</strong> to resume; do not wait for the whole room.</>}
            cliPurpose={<>Run one ticket through QA RED evidence, then approve its acceptance tests.</>}
            cliDirectory={track === "live" ? <><code>software-refactory-control</code>; commands target <code>$TARGET</code></> : <><code>software-refactory-rehearsal</code></>}
          >{track === "live" ? `./factory/factory run --repo "$TARGET" --review-qa-tests --once
echo "Enter the ticket number labeled QA Review:"
read -r ISSUE_NUMBER
./factory/factory approve-tests "$ISSUE_NUMBER" --repo "$TARGET"` : `./factory/factory run --mock --scenario recipe-rebrand --review-qa-tests --once
echo "Enter the ticket number labeled QA Review:"
read -r ISSUE_NUMBER
./factory/factory approve-tests "$ISSUE_NUMBER"`}</WorkshopPaths>
          <WorkshopMedia
            src="/screenshots/control-center-ticket-tests.jpg"
            alt="Control Center ticket drawer open on the Tests tab"
            label="Ticket tests"
            caption="Read the proposed test at its recorded QA revision. Check the assertion against the acceptance criterion."
            width={1440}
            height={980}
          />
          <WorkshopMedia
            src="/screenshots/control-center-qa-decision.jpg"
            alt="QA Review drawer showing the baseline assertion failure and Approve tests or Request test changes controls"
            label="Test decision — scroll down in Tests"
            caption="Read the baseline failure. Approve only if it demonstrates the missing behavior; otherwise describe the required correction."
            width={1440}
            height={980}
          />
          <Checkpoint>The ticket shows <strong>RED PROVED</strong> and records your approval.</Checkpoint>
        </StepSection>

        <StepSection index={7} id="factory" title="Deliver tickets" goal="Run the planned work and handle each human checkpoint.">
          <WorkshopPaths
            click={<>Open <strong>Deliver → Tickets</strong> and select <strong>Run factory</strong>. Keep <strong>Active lanes</strong> selected. When <strong>NEEDS YOU</strong> appears, open the linked ticket.</>}
            whyStopped={<>Each ticket needs implementation, passing checks, and separate code review. A failed check or required human decision stops progress.</>}
            inspect={<>Start with <strong>Summary → Candidate evidence</strong>. Inspect <strong>Diff</strong>, <strong>Tests</strong>, and <strong>Code review</strong>. Confirm the review covers the current commit. Open <strong>Execution details</strong> for adapters and timing.</>}
            continueWhen={<>Code review approves the commit and you select <strong>Merge exact revision</strong>. The ticket then moves to Done.</>}
            cliPurpose={<>Run eligible tickets and follow their GitHub Project state.</>}
            cliDirectory={track === "live" ? <><code>software-refactory-control</code>; commands target <code>$TARGET</code></> : <><code>software-refactory-rehearsal</code></>}
          >{track === "live" ? `echo "Enter your GitHub Project number:"
read -r PROJECT_NUMBER
gh project view "$PROJECT_NUMBER" --owner "@me" --web
./factory/factory run --repo "$TARGET"` : `./factory/factory run --mock --scenario recipe-rebrand`}</WorkshopPaths>
          <WorkshopMedia
            src="/screenshots/control-center-tickets.jpg"
            alt="Control Center Tickets board with backlog and QA Review columns"
            label="Deliver → Tickets"
            caption="Active lanes show only the current work."
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
            caption="Illustrative board layout. Open your own Project to inspect your actual issues and status."
            width={1280}
            height={942}
          />}
          <WorkshopMedia
            src="/screenshots/control-center-overview.jpg"
            alt="Control Center Current run page showing current phase, next safe action, delivery trace, and human decisions"
            label="Current run"
            caption="The overview follows your run from PRD to merge."
            width={1440}
            height={980}
          />
          <details className="optional-detail">
            <summary>What happens to each ticket</summary>
            <ol>
              <li>The scheduler selects a ticket whose dependencies are complete.</li>
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
            caption="Compare the reviewed revision with the approved head. Inspect tests and review, then select Merge exact revision. Execution details are collapsed below."
            width={1440}
            height={980}
          />
          <Callout type="tip" title="A failed check is normal">
            <p>The factory sends the error back to the agent and reruns the check after the fix. Open the ticket history to follow the retry.</p>
          </Callout>
          {track === "live" && <Callout type="tip" title="Two views, one run">
            <p>GitHub Projects shows shared ticket status. The Control Center shows local agent logs, changed files, tests, and checks.</p>
          </Callout>}
          <Checkpoint>All approved transformation tickets are checked, reviewed, and merged. One Done ticket is progress, not completion. Record any pending tickets and next action.</Checkpoint>
        </StepSection>

        <StepSection index={8} id="finish" title="Run the app and save evidence" goal="Check the merged behavior and save the run records.">
          <WorkshopPaths
            click={<>Open <strong>Review → Run app</strong> and select <strong>Start app</strong>, or copy the displayed startup command.</>}
            whyStopped={<>You can preview the baseline or merged work at any time. Remaining tickets do not prevent a preview.</>}
            inspect={<>Use the displayed application URL. Search for a recipe by ingredient, open its cooking steps, save and remove it in My Cookbook, and test mobile and TV navigation. Check for remaining film labels and movie API contracts.</>}
            continueWhen={<>The approved scope is merged and integrated acceptance checks pass. Rehearsal requires five tickets; Live follows your approved plan. Select <strong>Stop app</strong>, or press <code>Ctrl+C</code> for a terminal launch.</>}
            cliPurpose={<>Start the application from the merged product checkout.</>}
            cliDirectory={track === "live" ? <><code>$TARGET</code> (the Product checkout)</> : <><code>software-refactory-rehearsal</code></>}
          >{track === "live" ? `cd "$TARGET"
"$CONTROL/.factory/venv/bin/python" demo-app/app.py` : `.factory/venv/bin/python demo-app/app.py`}</WorkshopPaths>
          <WorkshopMedia
            src="/screenshots/control-center-evidence.jpg"
            alt="Control Center Review and Run app screen with the start command and application URLs"
            label="Review → Run app"
            caption="Start the app and check the revision shown above the preview command."
            width={1440}
            height={980}
          />
          <p>Stop the app, then select <strong>Export run evidence</strong> on this page. Open the packet and select <strong>Download</strong>. A Canvas is optional; no form is required to export.</p>
          <details className="optional-detail">
            <summary>Record the effort behind this result</summary>
            <p>Note completed tickets, retries, elapsed time, and minutes you actively spent reviewing or recovering. Use ticket records for attempts and evidence; provider records for available model usage and charges. Human wait is not active review time. Mark missing usage unknown, not zero. Do not share credentials or raw sensitive logs.</p>
          </details>
          <Checkpoint>TableStory satisfies the PRD; evidence is saved. Unfinished Live run? Record the resume point and inspect the facilitator’s labeled prepared result.</Checkpoint>
        </StepSection>


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
              <div role="row"><code role="cell">tool: node<br />requires &gt;= 22.13.0</code><span role="cell">Install Node.js 22.13+, verify with <code>node --version</code>, then retry.</span></div>
              <div role="row"><code role="cell">default branch<br />branch synchronization</code><span role="cell">Save any local work first. Use the branch shown in <strong>Review repository model</strong>. In that product checkout, fetch, switch to that branch, and pull with <code>--ff-only</code>. The guided starter uses <code>main</code>.</span></div>
              <div role="row"><code role="cell">codex/claude/cursor adapter not found or not signed in</code><span role="cell">Choose the matching preset in <strong>Setup → Connection</strong>. Then run <code>codex login</code>, <code>claude auth login</code>, or <code>agent login</code> followed by <code>agent status</code>. Retry automatic setup.</span></div>
              <div role="row"><code role="cell">No module named pytest<br />gate: api-tests</code><span role="cell">For the guided starter, open the repair commands below. Install with the same Python shown in the failing gate, then retry. For another repository, edit its <code>factory.project.toml</code> setup command and review the contract again.</span></div>
              <div role="row"><code role="cell">GitHub Projects scope</code><span role="cell">Run <code>gh auth refresh -s project</code>, finish the browser authorization, and select <strong>Retry automatic setup</strong>.</span></div>
              <div role="row"><code role="cell">repository target<br />origin remote</code><span role="cell">Paste the full URL of your product repository in <strong>Setup → Connection</strong> and save. Do not paste the workshop repository URL.</span></div>
              <div role="row"><code role="cell">Project Contract<br />Factory Charter</code><span role="cell">Select <strong>Create contract</strong>, review both contract sections, then select <strong>Approve contract and continue</strong>.</span></div>
            </div>
            <p className="warning-note"><strong>Usually safe to ignore:</strong> a warning for port 5050 while the Control Center is open, an unused adapter, or the optional second reviewer identity.</p>
          </section>
          <p>Open <strong>Activity and CLI output</strong>, find the first <strong>FAIL</strong>, apply its repair above, and select <strong>Retry automatic setup</strong>. Repeating the same command before fixing its cause will repeat the failure.</p>
          <details className="optional-detail">
            <summary>Example: wrong branch, wrong agent, and missing pytest</summary>
            <p>If those three failures appear together, fix them in this order:</p>
            <ol>
              <li>Run <code>git status</code>. Commit or stash work you need to keep.</li>
              <li>In the product checkout, fetch and switch to its default branch, then pull with <code>--ff-only</code>. Use the branch shown in the repository model; it is <code>main</code> for the guided starter.</li>
              <li>If Claude passes but Codex fails, choose <strong>Claude workshop</strong> in <strong>Setup → Connection</strong> and save. Otherwise sign in with <code>codex login</code>.</li>
              <li>In another terminal, open the Factory checkout and use the repair commands below. The guided starter uses the Factory virtual environment. If the failing command names another Python, use that exact interpreter instead.</li>
              <li>Select <strong>Retry automatic setup</strong>. Continue only when no <code>[FAIL]</code> remains.</li>
            </ol>
          </details>
          <details>
            <summary>Repair dependencies for the guided starter</summary>
            <p>Open another terminal in the Factory checkout. Confirm the Python path matches the failed gate in Activity.</p>
            <CodeBlock label="Repair guided Python dependencies">{`.factory/venv/bin/python -m pip install -r demo-app/requirements.txt
.factory/venv/bin/python -m pytest --version`}</CodeBlock>
          </details>
          <div className="accordion-list">
            <details><summary>An agent reports a full context window</summary><p>If the phase says <strong>Recovering from the context limit</strong>, leave it running. The factory can restart once with a smaller prompt and the full assignment in local files. Nothing is removed from your requirements. If it still stops, choose another configured agent or a larger-context model, or split the PRD into smaller runs. Cursor users with MCP servers may need a separate environment without MCP or another agent; the factory reports this during setup without changing personal settings.</p></details>
            <details><summary>The repository is not connected</summary><p>Open <strong>Setup → Connection</strong>, choose <strong>Live</strong>, enter the full product repository URL, and select <strong>Save and connect</strong>. Push its default branch first if it already contains code.</p></details>
            <details><summary>An agent asks for the wrong credentials</summary><p>Open <strong>Setup → Connection</strong> and choose the preset for the CLI you use. Save, sign in to that CLI, then select <strong>Retry automatic setup</strong>.</p></details>
            <details><summary>A planning expert failed</summary><p>If the current phase says <strong>Correcting invalid planning output</strong>, leave it running. The factory can make up to two automatic repairs within the Charter retry limit. If it still stops, open <strong>Plan → Review plan</strong> and select the failed expert. For an invalid result, select <strong>Apply correction for review</strong>. Read the revision before confirming to continue. For a login or rate-limit error, fix access or choose another agent. Product questions still need your decision. If the PRD or repository settings changed, select <strong>Restart planning safely</strong>.</p></details>
            <details><summary>Ticket publication failed</summary><p>Open <strong>Plan → Review plan</strong> and select <strong>Retry ticket publication</strong>. The retry reuses issues already created for this plan. In the CLI, rerun the same <code>factory approve</code> command shown in the error.</p></details>
            <details><summary>A ticket is blocked</summary><p>Open the ticket and follow its recovery panel. Explain what changed before selecting <strong>Retry</strong>. If review needs a report, paste the full commit ID you tested, your checks, and their results into <strong>Evidence for review</strong>. An action may wait for the current worker wave to finish; wait for confirmation before repeating it.</p></details>
            <details><summary>A required check still tests removed behavior</summary><p>Compare the failed test with the ticket. If the ticket intentionally removes that behavior, do not restore it. Select <strong>Retry</strong>. The coding agent can update an existing test when the Charter marks existing tests for review.</p></details>
            <details><summary><code>NEEDS YOU</code> says dispatch is paused</summary><p>Too many decisions are waiting for a person. Open the oldest linked item and complete that decision. New ticket work starts again when the queue has space.</p></details>
            <details><summary>A remote claim belongs to an old run</summary><p>A claim is the marker that says this run owns a ticket. Confirm the old run has stopped, open the blocked ticket, and select <strong>Release abandoned claim</strong>.</p></details>
            <details><summary>The Control Center reports a dependency cycle</summary><p>Two or more tickets depend on each other. Edit the issue dependencies so one ticket can start, then run the factory again.</p></details>
            <details><summary>The issue listener does not import an existing issue</summary><p>This is expected. Its first start records the existing backlog and watches only for issues created afterward. Create a new issue, or stop the listener and follow the normal PRD planning path.</p></details>
            <details><summary>Live planning is slow or inconsistent</summary><p>Leave a healthy agent running. Follow the facilitator’s prepared evidence for the next activity. Use a separate Rehearsal checkout if you need a simulated fallback; do not reset the Live run.</p></details>
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
            <p>Open <strong>More tools → Factory interfaces</strong> for workspace checks, trigger proposals, and improvement reports. These are optional. In this workshop&apos;s Standard profile, you make the final merge decision.</p>
          </details>
          <details className="optional-detail">
            <summary>Configure your own agent or product after the workshop</summary>
            <p>Register a noninteractive adapter in <code>factory/factory.toml</code> using the <a href="https://github.com/giolaq/software-refactory-workshop/blob/main/factory/CONFIGURATION.md">configuration guide</a>. Then open <strong>Setup → Connection → Advanced role settings</strong> and assign it to a supported role. Planning currently uses Claude, Codex, Cursor, or Bedrock. Review the Project Contract before approving setup in another repository.</p>
            <p>Focused acceptance tests support pytest and Node&apos;s built-in JavaScript runner. Other stacks need a compatible wrapper. A Git worktree separates changes; it does not sandbox commands on your computer.</p>
          </details>
          <div className="next-links">
            <a href="https://github.com/giolaq/software-refactory-workshop/blob/main/factory/WORKSHOP_OUTLINE.md"><span>FACILITATOR</span><b>Workshop outline</b><i>→</i></a>
            <a href="https://github.com/giolaq/software-refactory-workshop/blob/main/factory/CONFIGURATION.md"><span>REFERENCE</span><b>Agent configuration</b><i>→</i></a>
          </div>
        </section>
      </main>


      <footer>
        <span className="footer-brand"><span className="brand-mark" aria-hidden="true"><i /><i /><i /><i /></span>Software (re)-Factory</span>
        <span>Setup. Plan. Deliver. Review. · workshop-v1.2.2</span>
      </footer>
    </>
  );
}
