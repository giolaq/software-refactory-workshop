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
  if (capture) await fixture("product", () => {
    navigate("prd"); shot("prd");
    navigate("planning"); shot("planning");
  });
  await fixture("qa", () => {
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
    browser("press", "Escape");
    check("document.querySelector('#ticket-drawer').hidden");
    check("document.activeElement.matches('[data-ticket]')");
  });
  if (capture) await fixture("review", () => {
    navigate("tickets");
    browser("click", '[data-ticket="1"]');
    browser("wait", "[data-ticket-action=merge]");
    shot("human-merge");
  });
  // This fixture completes all five tickets through human QA and merge commands.
  await fixture("done", () => {
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
