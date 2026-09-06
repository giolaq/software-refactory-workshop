// Local, deterministic UI checks. No GitHub or paid provider calls.
// Requires the guide at GUIDE_URL when supplied. --screenshots refreshes images.
import assert from "node:assert/strict";
import { spawn, execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../../", import.meta.url));
const capture = process.argv.includes("--screenshots");
const python = process.env.FACTORY_PYTHON || "python3";
const port = process.env.FACTORY_BROWSER_PORT || "5056";
const session = `workshop-check-${process.pid}`;
const images = [];
function browser(...args) {
  return execFileSync("npx", ["--yes", "agent-browser@0.36.0", "--session", session, ...args], {
    cwd: root, encoding: "utf8", timeout: 60000,
  }).trim();
}
function check(expression) {
  const result = browser("eval", `Boolean(${expression})`);
  assert.equal(result, "true", expression + " returned " + result);
}
function shot(name) {
  if (!capture) return;
  const relative = `workshop-guide/public/screenshots/control-center-${name}.jpg`;
  browser("--screenshot-format", "jpeg", "--screenshot-quality", "85", "screenshot", resolve(root, relative));
  images.push(relative);
}
function navigate(view) {
  browser("click", `[data-view-link="${view}"]`);
  browser("wait", `[data-view="${view}"]:not([hidden])`);
}
async function fixture(stage, work) {
  const server = spawn(python, ["factory/tests/serve_workshop_fixture.py", "--stage", stage, "--port", port], {
    cwd: root, stdio: ["ignore", "pipe", "pipe"],
  });
  let output = "";
  try {
    await new Promise((done, reject) => {
      const timer = setTimeout(() => reject(new Error(`Fixture ${stage} startup failed: ${output}`)), 180000);
      server.stdout.on("data", data => {
        output += data;
        if (output.includes("FIXTURE_URL=")) { clearTimeout(timer); done(); }
      });
      server.stderr.on("data", data => { output += data; });
      server.once("error", error => { clearTimeout(timer); reject(error); });
      server.once("exit", code => { clearTimeout(timer); reject(new Error(`Fixture exited ${code}: ${output}`)); });
    });
    browser("open", `http://127.0.0.1:${port}/`);
    browser("set", "viewport", "1440", "980");
    browser("set", "media", "reduced-motion");
    browser("wait", "#system-updated:not(:empty)");
    // Wait on rendered repository state, not an arbitrary delay.
    browser("wait", "--fn", "document.body.innerText.includes('rehearsal')");
    await work();
    assert.equal(browser("errors"), "", "Unexpected browser errors");
    console.log(`PASS Control Center ${stage}`);
  } finally {
    server.kill("SIGINT");
    if (server.exitCode === null) await new Promise(done => server.once("exit", done));
  }
}

try {
  await fixture("fresh", () => {
    check("document.querySelector('#journey-next').textContent.includes('Connect')");
    navigate("connect");
    check("document.querySelectorAll('.setup-flow > li').length === 3");
    shot("connect");
  });
  await fixture("product", () => {
    // A new browser restores the server's run mode, not a stale local default.
    browser("eval", 'const saved = app.snapshot; app.snapshot = null; setMode("rehearsal"); renderSnapshot({...saved, factory: {...saved.factory, mode:"github", execution_mode:"live"}})');
    check('mode() === "live" && basePayload().mode === "live"');
    check('document.querySelector("#sidebar-mode").textContent === mode()');
    browser("eval", 'setMode("rehearsal")');
    check('document.querySelector("#sidebar-mode").textContent === mode()');
    browser("reload");
    browser("wait", "#system-updated:not(:empty)");
    navigate("prd"); shot("prd");
    navigate("planning"); shot("planning");
    browser("click", '[data-planning-stage="product_review"]');
    browser("wait", "--fn", "document.querySelector('#artifact-content').textContent.includes('Product review')");
    navigate("connect");
    browser("set", "viewport", "1440", "600");
    browser("scroll", "down", "1000");
    check("window.scrollY > 0");
    navigate("planning");
    check("window.scrollY === 0");
    browser("set", "viewport", "1440", "980");
    browser("click", '[data-planning-stage="product_review_gate"]');
    browser("wait", "#approve-product");
    shot("planning");
    browser("eval", "window.confirm = () => true");
    browser("click", "#approve-product");
    browser("wait", "--fn", "app.snapshot?.planning?.status === 'product_approved' && app.snapshot?.operation?.status === 'succeeded'");
    navigate("planning");
    browser("wait", "#continue-plan:not([hidden]):not([disabled])");
    check("!(app.snapshot.factory.tickets || []).length");
    shot("product-approved");
    browser("click", "#continue-plan");
    browser("wait", "--fn", "app.snapshot?.planning?.status === 'awaiting_alignment_approval' && app.snapshot?.operation?.status === 'succeeded'");
    navigate("planning");
    browser("click", '[data-planning-stage="alignment_gate"]');
    browser("wait", "#approve-alignment");
    check("document.querySelector('#approve-alignment').textContent === 'Approve and create tickets'");
    check("!(app.snapshot.factory.tickets || []).length");
    shot("create-tickets");
  });
  await fixture("running", () => {
    navigate("planning");
    check("document.querySelector('#artifact-content').textContent.includes('The expert is working')");
    check("document.querySelector('#open-artifact').hidden");
    check("!performance.getEntriesByType('resource').some(entry => entry.name.endsWith('/api/artifact?path='))");
    navigate("evidence");
    check("document.querySelector('#start-app').disabled");
    check("document.querySelector('#run-app-status').textContent.includes('separate terminal')");
  });
  await fixture("qa", () => {
    // A slow companion action gives feedback and cannot be submitted twice.
    assert.equal(browser("eval", `(async () => {
      const originalRequest = request, originalConfirm = window.confirm;
      let complete, calls = 0;
      request = () => { calls++; return new Promise(resolve => { complete = resolve; }); };
      window.confirm = () => true;
      try {
        const first = action('retry', {issue: 1, reason: 'Browser fixture only'});
        await action('retry', {issue: 1, reason: 'Duplicate fixture only'});
        const pending = calls === 1 && app.pendingActions.has('retry:1')
          && document.querySelector('#toast-region').textContent.includes('Submitting retry for ticket #1');
        complete({companion: {title: 'Fixture retry'}});
        await first;
        request = async () => { throw new Error('Fixture request failed'); };
        const failed = await action('retry', {issue: 1});
        return pending && failed === null && !app.pendingActions.has('retry:1')
          && !document.querySelector('#toast-region').textContent.includes('Submitting retry');
      } finally { request = originalRequest; window.confirm = originalConfirm; }
    })()`), "true");
    shot("overview");
    navigate("tickets");
    check("document.querySelector('#issue-listener-state').hidden");
    shot("tickets");
    browser("click", '[data-ticket="1"]');
    browser("wait", "[data-ticket-action=approve-tests]:not([disabled])");
    check("document.querySelector('#drawer-content').textContent.includes('RED PROVED')");
    check("document.querySelector('#drawer-content').textContent.includes('def test_')");
    check("document.querySelector('#ticket-drawer').getAttribute('role') === 'dialog'");
    shot("ticket-tests");
    browser("eval", "document.querySelector('[data-ticket-action=approve-tests]').scrollIntoView({block:'center'})");
    shot("qa-decision");
    // A polling update must refresh the header as well as the decision content.
    browser("eval", "app.selectedTicket = {...app.selectedTicket, status: 'Ready'}; renderDrawer({preservePosition:true})");
    check("document.querySelector('#drawer-issue').textContent === '#1 · Ready'");
    browser("press", "Escape");
    check("document.querySelector('#ticket-drawer').hidden");
    check("document.activeElement.matches('[data-ticket]')");
    // A rejected review uses an explicit attachment; reports cannot inject HTML.
    browser("eval", `app.selectedTicket = {number: 1, title: 'Evidence fixture', status: 'Blocked',
      failure: 'Review requested browser checks', body: '', code_review: {status: 'changes_requested', head: 'a'.repeat(40)},
      review_evidence: [{author_role: 'operator', candidate_head: 'a'.repeat(40), sha256: 'report-hash', content: '<img src=x onerror=alert(1)>'}]};
      app.drawerTab = 'summary'; renderDrawer()`);
    check("document.querySelector('#retry-evidence').maxLength === 20000");
    check("document.querySelector('#drawer-content').textContent.includes('Candidate evidence')");
    check("document.querySelector('#drawer-content').textContent.includes('not independent verification or approval')");
    check("!document.querySelector('#drawer-content img')");
  });
  await fixture("review", () => {
    navigate("tickets");
    browser("click", '[data-ticket="1"]');
    browser("wait", "[data-ticket-action=merge]");
    check("document.querySelector('#drawer-content').textContent.includes('Candidate evidence')");
    check("app.snapshot.factory.supervisor_agent === 'disabled'");
    check("document.querySelector('[data-drawer-tab=supervisor]').hidden");
    check("document.querySelector('[data-ticket-action=merge]').getBoundingClientRect().bottom < window.innerHeight");
    browser("eval", "document.querySelector('#drawer-content details').open = true; renderDrawer({preservePosition:true})");
    check("document.querySelector('#drawer-content details').open");
    browser("eval", "document.querySelector('#drawer-content details').open = false");
    shot("human-merge");
  });
  // This fixture completes all five tickets through human QA and merge commands.
  await fixture("done", () => {
    navigate("tickets");
    check("[...document.querySelectorAll('.ticket-meta b')].every(element => element.textContent === 'Completed')");
    navigate("evidence");
    check("document.querySelector('#preview-revision').textContent.includes('5 of 5 tickets Done')");
    browser("click", "#export-evidence");
    browser("wait", "--fn", "document.querySelector('#operation-title').textContent === 'Create evidence packet' && document.querySelector('#operation-status').textContent.toLowerCase() === 'succeeded'");
    browser("wait", "[data-evidence-path]");
    shot("evidence");
    browser("click", "[data-evidence-path]");
    browser("wait", "#download-artifact");
    check("document.querySelector('#drawer-content').textContent.includes('Evidence Packet')");
  });
  if (process.env.GUIDE_URL) {
    browser("open", process.env.GUIDE_URL);
    browser("wait", "#prerequisites");
    check("!document.querySelector('.nav-progress, .complete-button, .right-rail')");
    check("!document.body.innerText.includes('Mark step complete')");
    check("document.body.innerText.includes('Start the Control Center')");
    check("!document.querySelector('vite-error-overlay, nextjs-portal')");
    browser("reload");
    browser("wait", "#prerequisites");
    check("!document.body.innerText.includes('Mark step complete')");
    assert.equal(browser("errors"), "");
    console.log("PASS procedural guide and reload");
  }
  if (capture) {
    const sources = ["factory/control_center.py", "factory/control_center/app.js", "factory/control_center/index.html", "factory/control_center/styles.css", "factory/tests/serve_workshop_fixture.py"];
    const hash = path => createHash("sha256").update(readFileSync(resolve(root, path))).digest("hex");
    writeFileSync(resolve(root, "workshop-guide/public/screenshots/capture-manifest.json"), JSON.stringify({
      capturedAt: new Date().toISOString(),
      baseRevision: execFileSync("git", ["rev-parse", "HEAD"], { cwd: root, encoding: "utf8" }).trim(),
      workingTreeChanges: Boolean(execFileSync("git", ["status", "--porcelain"], { cwd: root, encoding: "utf8" }).trim()),
      scenario: "Disposable Standard Rehearsal; mock providers; not Live GitHub evidence",
      viewport: { width: 1440, height: 980 },
      sources: Object.fromEntries(sources.map(path => [path, hash(path)])),
      images: Object.fromEntries(images.map(path => [path, hash(path)])),
    }, null, 2) + "\n");
  }
} finally {
  browser("close");
}
