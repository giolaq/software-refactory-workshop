import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", { headers: { accept: "text/html" } }),
    { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

test("server-renders the concise self-guided workshop", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<title>Software \(re\)-Factory Workshop<\/title>/i);
  assert.match(html, /Software \(re\)-Factory workshop/);
  assert.match(html, /Use the Control Center or CLI/);
  assert.match(html, /Each step shows the action, result, and next check/);

  assert.match(html, /Check your tools/);
  assert.match(html, /Python 3\.11/);
  assert.match(html, /Node\.js 20/);
  assert.match(html, /One personal GitHub product repository/);
  assert.match(html, /Do not use the facilitator/);
  assert.match(html, /Rehearsal/);
  assert.match(html, /Live/);
  assert.match(html, /factory control-center/);
  assert.match(html, /Open the Control Center/);
  assert.match(html, /Project Contract/);
  assert.match(html, /Terminal 2 — keep this running/);
  assert.match(html, /Factory Control Center: http:\/\/127\.0\.0\.1:5050/);
  assert.match(html, /browser should open automatically/i);
  assert.match(html, /Ctrl\+C/);
  assert.match(html, /Control Center/);
  assert.match(html, /Control Center path/);
  assert.match(html, /CLI path/);
  assert.match(html, /Do this/);
  assert.match(html, /What happens/);
  assert.match(html, /Check/);
  assert.match(html, /Continue when/);

  for (const heading of [
    "Connect a repository",
    "Check the starting repository",
    "Save the PRD",
    "Review the product plan",
    "Publish tickets",
    "Review QA tests",
    "Run tickets",
    "Run the completed app",
  ]) {
    assert.match(html, new RegExp(heading));
  }

  assert.match(html, /factory doctor --full/);
  assert.match(html, /factory plan recipe-app-prd\.md/);
  assert.match(html, /factory approve-product/);
  assert.match(html, /factory approve-rehearsal/);
  assert.match(html, /factory run --mock --scenario recipe-rebrand --review-qa-tests --once/);
  assert.match(html, /factory approve-tests ISSUE_NUMBER/);
  assert.match(html, /\.factory\/venv\/bin\/python demo-app\/app\.py/);
  assert.match(html, /RED PROVED/);
  assert.match(html, /NEEDS YOU/);
  assert.match(html, /remote claim/);
  assert.match(html, /Merge exact revision/);
  assert.match(html, /http:\/\/127\.0\.0\.1:5000\/\?mode=tv/);
  assert.match(html, /What planning creates/);
  assert.match(html, /What happens to each ticket/);
  assert.match(html, /The coding agent changes an isolated Git worktree/);
  assert.match(html, /A required check still tests removed behavior/);
  assert.match(html, /Troubleshooting/);

  assert.match(html, /screenshots\/pocket-cinema-before\.webp/);
  assert.match(html, /screenshots\/control-center-connect\.jpg/);
  assert.match(html, /screenshots\/control-center-prd\.jpg/);
  assert.match(html, /screenshots\/control-center-planning\.jpg/);
  assert.match(html, /screenshots\/control-center-tickets\.jpg/);
  assert.match(html, /screenshots\/control-center-ticket-tests\.jpg/);
  assert.match(html, /screenshots\/control-center-overview\.jpg/);
  assert.match(html, /screenshots\/control-center-human-merge\.jpg/);

  assert.doesNotMatch(html, /Start with one responsible delivery loop/);
  assert.doesNotMatch(html, /More agents are a cost/);
  assert.doesNotMatch(html, /The supervisor coordinates work\. It does not own delivery/);
  assert.doesNotMatch(html, /The Code Review role closes the feedback loop/);
  assert.doesNotMatch(html, /Turn product intent into contracts and small vertical slices/);
  assert.doesNotMatch(html, /illustrations\/0[123]-/);
  assert.doesNotMatch(html, /lights[- ]off|control experiment|run_lights_off|two delivery systems/i);
  assert.doesNotMatch(html, /localhost:8000|python3 -m http\.server 8000/i);
  assert.doesNotMatch(html, /codex-preview|react-loading-skeleton|Your site is taking shape/i);
});

test("attendee page stays within its copy budget", async () => {
  const source = await readFile(new URL("../app/page.tsx", import.meta.url), "utf8");
  const response = await render();
  const html = await response.text();
  const initiallyVisibleHtml = html.replace(
    /<details\b(?![^>]*\bopen\b)[^>]*>([\s\S]*?)<\/details>/gi,
    (_, content) => content.match(/<summary\b[^>]*>[\s\S]*?<\/summary>/i)?.[0] ?? "",
  );
  const visible = initiallyVisibleHtml
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&(?:[a-z]+|#\d+);/gi, " ");
  const words = visible.trim().split(/\s+/).filter(Boolean).length;
  assert.ok(words < 2400, `attendee page renders ${words} visible words; expected fewer than 2400`);
  assert.match(source, /factory doctor --repo "\$TARGET" --full/);
  assert.match(source, /factory run --repo "\$TARGET"/);
  assert.match(source, /approve-tests ISSUE_NUMBER --repo "\$TARGET"/);
  assert.match(source, /gh project view <project-number>/);
  assert.match(source, /screenshots\/github-project-board\.jpg/);
  assert.match(source, /gh repo create YOUR-REPOSITORY --private/);
  assert.match(source, /Seed the guided Pocket Cinema starter/);
  assert.match(source, /New product:/);
  assert.match(source, /agents create the product code from the tickets/);
  assert.match(source, /repository contains only factory settings/);
  assert.match(source, /Retry ticket publication/);
  assert.match(source, /retry reuses issues that were already created for this plan/);
  assert.match(source, /factory bootstrap-workshop --repo/);
  assert.doesNotMatch(source, /git push workshop main factory-baseline/);
  assert.doesNotMatch(source, /--template giolaq\/software-refactory-workshop/);
  assert.doesNotMatch(source, /agent_capabilities\.my-agent/);
  assert.doesNotMatch(source, /Start with one responsible delivery loop/);
});

test("server-rendered workshop has accessible document and image structure", async () => {
  const response = await render();
  const html = await response.text();
  assert.match(html, /<html[^>]+lang="en"/i);
  assert.match(html, /<main\b/i);
  assert.match(html, /<nav\b[^>]*aria-label=/i);
  const headings = html.match(/<h1\b/g) ?? [];
  assert.equal(headings.length, 1, "the attendee page should expose one primary heading");
  const images = html.match(/<img\b[^>]*>/gi) ?? [];
  assert.ok(images.length > 0, "the attendee page should render its instructional images");
  for (const tag of images) {
    assert.match(tag, /\balt="[^"]+"/i, `instructional image is missing useful alt text: ${tag}`);
  }
});
