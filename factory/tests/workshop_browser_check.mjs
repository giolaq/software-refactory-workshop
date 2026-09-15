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
  if (process.env.FACTORY_BROWSER_STAGE && process.env.FACTORY_BROWSER_STAGE !== stage) return;
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
  } catch (error) {
    console.error(`FAIL Control Center ${stage}: ${output.slice(-3000)}`);
    console.error(browser("errors"));
    console.error(browser("snapshot", "-i"));
    throw error;
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
    check("!document.querySelector('#attention-surface')");
    // Display Live setup without contacting GitHub; the fixture remains local.
    browser("select", "#connect-mode", "live");
    browser("fill", '[name="github_repository"]', "https://github.com/your-account/factory-tablestory-workshop");
    browser("fill", '[name="project_number"]', "https://github.com/users/your-account/projects/1/views/1");
    check("document.querySelector('[name=project_number]').checkValidity()");
    check("!document.querySelector('[name=project_number]').closest('details')");
    browser("set", "viewport", "1440", "1200");
    browser("check", '[name="bootstrap_workshop"]');
    shot("connect");
    browser("uncheck", '[name="bootstrap_workshop"]');
    browser("set", "viewport", "1440", "980");
    // Submit through the real form in Rehearsal: exercise parsing and persistence
    // without cloning a repository or creating a GitHub Project.
    browser("select", "#connect-mode", "rehearsal");
    browser("click", '#config-form button[type="submit"]');
    browser("wait", "--fn", "app.snapshot?.config?.project_number === 1 && app.snapshot?.operation?.status === 'succeeded'");
    browser("reload");
    browser("wait", "--fn", "app.snapshot?.config?.project_number === 1");
    check("document.querySelector('[name=project_number]').value === '1'");
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
    // A valid completed stage remains editable before tickets are published.
    for (const stage of ["product_review", "system_architecture", "program_design", "vertical_slices"]) {
      browser("click", `[data-planning-stage="${stage}"]`);
      browser("wait", "#request-stage-revision:not([disabled])");
    }
    browser("click", '[data-planning-stage="system_architecture"]');
    browser("wait", "#stage-revision-feedback");
    browser("fill", "#stage-revision-feedback", "Keep the service in this repository and preserve the recipe API contracts.");
    browser("click", "#request-stage-revision");
    browser("wait", "--fn", "app.snapshot?.planning?.revision_review?.stage === 'system_architecture' && app.snapshot?.operation?.status === 'succeeded'");
    navigate("planning");
    browser("click", '[data-planning-stage="system_architecture"]');
    browser("wait", "#request-stage-revision:not([disabled])");
    check("app.snapshot.planning.stages.find(s => s.id === 'program_design').status === 'stale'");
    check("app.snapshot.planning.stages.find(s => s.id === 'vertical_slices').status === 'stale'");
    check("!app.snapshot.planning.approvals.alignment && !(app.snapshot.factory.tickets || []).length");
    check("document.querySelector('#continue-plan').textContent === 'Confirm revision and continue'");
    check("!app.snapshot.operation.command.includes('continue-plan')");
    shot("plan-revision");
    browser("reload");
    browser("wait", "--fn", "app.snapshot?.planning?.revision_review?.stage === 'system_architecture'");
    navigate("planning");
    browser("wait", "#continue-plan:not([hidden]):not([disabled])");
    check("app.snapshot.planning.revision_review.stage === 'system_architecture'");
    browser("click", "#continue-plan");
    browser("wait", "--fn", "app.snapshot?.planning?.status === 'awaiting_alignment_approval' && app.snapshot?.operation?.status === 'succeeded'");
    check("!app.snapshot.planning.revision_review && !(app.snapshot.factory.tickets || []).length");
  });
  await fixture("running", () => {
    navigate("planning");
    check("app.snapshot.planning.stages.find(stage => stage.id === 'product_review').status === 'running'");
    check("document.querySelector('#artifact-content').textContent.includes(app.snapshot.planning.stages.find(stage => stage.id === 'product_review').activity || 'The expert is working')");
    check("document.querySelector('#open-artifact').hidden");
    check("!performance.getEntriesByType('resource').some(entry => entry.name.endsWith('/api/artifact?path='))");
    navigate("evidence");
    check("document.querySelector('#start-app').disabled");
    check("document.querySelector('#run-app-status').textContent.includes('separate terminal')");
  });
  await fixture("qa", () => {
    assert.equal(browser("eval", readFileSync(resolve(root, "factory/tests/markdown_browser_checks.js"), "utf8")), '"PASS Markdown formatting and unsafe-content checks"');
    shot("overview");
    check("!document.querySelector('#attention-surface') && document.querySelector('#journey-next').textContent.length > 0");
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
    browser("wait", "--fn", "!document.querySelector('#toast-region').children.length");
    navigate("tickets");
    check("document.querySelector('#issue-listener-state').hidden");
    shot("tickets");
    browser("click", '[data-ticket="1"]');
    browser("wait", "[data-ticket-action=approve-tests]:not([disabled])");
    check("document.querySelector('#drawer-content').textContent.includes('RED PROVED')");
    check("document.querySelector('#drawer-content').textContent.includes('def test_')");
    check("document.querySelector('#drawer-content .ticket-markdown')?.textContent.trim().length > 0");
    check("document.querySelector('#ticket-drawer').getAttribute('role') === 'dialog'");
    shot("ticket-tests");
    assert.equal(browser("eval", readFileSync(resolve(root, "factory/tests/drawer_scroll_browser_checks.js"), "utf8")),
      '"PASS Tests tab keeps reading position and feedback across refreshes"');
    browser("eval", "document.querySelector('[data-ticket-action=approve-tests]').scrollIntoView({block:'center'})");
    shot("qa-decision");
    assert.equal(browser("eval", readFileSync(resolve(root, "factory/tests/approval_queue_browser_checks.js"), "utf8")),
      '"PASS approval queues while executor busy, closes on success, and stays open on failure"');
    // A polling update must refresh the header as well as the decision content.
    // Assert in the same browser task so a real SSE update cannot replace this
    // synthetic state between separate command round trips.
    assert.equal(browser("eval", "app.selectedTicket = {...app.selectedTicket, status: 'Ready'}; renderDrawer({preservePosition:true}); document.querySelector('#drawer-issue').textContent === '#1 · Ready'"), "true");
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
      scenario: "Disposable Standard Rehearsal; mock providers. Connection screenshot displays unsaved example Live URLs; no GitHub calls or Live evidence.",
      viewport: { width: 1440, height: 980 },
      viewportOverrides: { "control-center-connect.jpg": { width: 1440, height: 1200 } },
      sources: Object.fromEntries(sources.map(path => [path, hash(path)])),
      images: Object.fromEntries(images.map(path => [path, hash(path)])),
    }, null, 2) + "\n");
  }
} finally {
  browser("close");
}
