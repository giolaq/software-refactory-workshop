import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", String(Date.now()));
  const { default: worker } = await import(workerUrl.href);
  return worker.fetch(
    new Request("http://localhost/", { headers: { accept: "text/html" } }),
    { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

test("guide renders the procedural Live path without a completion tracker", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  const html = await response.text();
  for (const phrase of [
    "Follow these steps in your own repository",
    "Live · workshop path", "Rehearsal · simulated fallback",
    "Finish Setup", "Check the starting app", "Write requirements",
    "Approve Product Review", "Create tickets", "Approve Acceptance Tests",
    "Deliver tickets", "Run the app and save evidence",
    "Save and connect", "Create contract", "Approve contract and continue",
    "Start the Control Center", "Start the Control Center — keep this running",
    "QA Review", "Tests", "Merge exact revision", "Export run evidence",
    "Troubleshooting", "Retry automatic setup",
  ]) assert.ok(html.includes(phrase), "missing instruction: " + phrase);
  assert.ok(html.indexOf('id="path"') < html.indexOf('id="prerequisites"'));
  assert.match(html, /aria-pressed="true"[^>]*>.*?Live · workshop path/s);
  assert.doesNotMatch(html, /Mark step complete|Factory complete|completion-ring|nav-progress|right-rail/);
  assert.doesNotMatch(html, /The code is the easy part|Take the layers with you|Factory layers/);
});

test("prerequisites and recovery identify the supported environment", async () => {
  const html = await (await render()).text();
  for (const phrase of [
    "Python 3.11", "Node.js 22.13", "WSL2", "GitHub CLI",
    "personal GitHub product repository", "pull requests",
    "gh auth status", "gh auth refresh -s project",
    "Use Cursor CLI", "agent login", "No module named pytest",
    "same Python", "requirements.txt", "factory.project.toml",
    "CONTROL", "TARGET", "session release tag",
  ]) assert.ok(html.includes(phrase), "missing prerequisite/recovery: " + phrase);
});

test("both command paths use valid shell syntax and explicit inputs", async () => {
  const html = await (await render()).text();
  const source = await readFile(new URL("../app/page.tsx", import.meta.url), "utf8");
  const decode = value => value.replace(/&quot;/g, '"').replace(/&#x27;|&#39;/g, "'")
    .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");
  const commands = [...html.matchAll(/<pre><code>([\s\S]*?)<\/code><\/pre>/g)].map(m => decode(m[1]));
  assert.ok(commands.length >= 8);
  for (const command of commands) {
    const parsed = spawnSync("sh", ["-n"], { input: command, encoding: "utf8" });
    assert.equal(parsed.status, 0, parsed.stderr + "\n" + command);
  }
  assert.doesNotMatch(source, /<plan-id-from-output>|<project-number>|open "\$CONTROL|YOUR-REPOSITORY|YOUR-NAME/);
  assert.match(source, /read -r PLAN_ID/);
  assert.match(source, /--branch SESSION_TAG/);
  assert.match(html, /Replace <code>SESSION_TAG<\/code>/);
  assert.match(source, /workshop-search-prd\.md/);
  assert.match(source, /factory approve-rehearsal/);
  assert.match(source, /factory run --mock --scenario recipe-rebrand --review-qa-tests --once/);
  assert.match(source, /factory run --repo "\$TARGET"/);
});

test("Control Center setup is direct and does not require a shell wizard", async () => {
  const source = await readFile(new URL("../app/page.tsx", import.meta.url), "utf8");
  const setup = source.slice(source.indexOf('<StepSection index={1}'), source.indexOf('<StepSection index={2}'));
  const primary = setup.slice(0, setup.indexOf('<WorkshopPaths'));
  assert.doesNotMatch(primary, /echo |read -r |export |WORKSHOP_OWNER|WORKSHOP_REPO|gh repo create/);
  assert.match(primary, /gh auth login --web --git-protocol https --scopes project/);
  assert.match(primary, /https:\/\/github.com\/new/);
  assert.match(primary, /Do not clone this repository yourself/);
  assert.match(primary, /In the same terminal/);
  assert.match(setup, /export TARGET="\$CONTROL\/\.factory\/repositories\/\$REPOSITORY"/);
});

test("guide has no local completion state and retains concise instructions", async () => {
  const source = await readFile(new URL("../app/page.tsx", import.meta.url), "utf8");
  assert.doesNotMatch(source, /localStorage|setCompleted|toggleStep|useEffect|CSSProperties/);
  const html = await (await render()).text();
  const visible = html.replace(/<script[\s\S]*?<\/script>/gi, "")
    .replace(/<style[\s\S]*?<\/style>/gi, "")
    .replace(/<details\b[^>]*>[\s\S]*?<\/details>/gi, "")
    .replace(/<[^>]+>/g, " ");
  assert.ok(visible.trim().split(/\s+/).length < 2700, "visible instructions exceed the guardrail");
  assert.doesNotMatch(html, /lights[- ]off|control experiment|two delivery systems/i);
});

test("guide has accessible structure and local instructional images", async () => {
  const html = await (await render()).text();
  assert.match(html, /<html[^>]+lang="en"/);
  assert.equal((html.match(/<h1\b/g) || []).length, 1);
  assert.match(html, /<nav[^>]+aria-label=/);
  const images = html.match(/<img\b[^>]*>/g) || [];
  assert.ok(images.length > 0);
  for (const tag of images) assert.match(tag, /\balt="[^"]+"/);
  assert.match(html, /screenshots\/control-center-ticket-tests\.jpg/);
  assert.match(html, /screenshots\/control-center-evidence\.jpg/);
});
