// Evaluate in a loaded Control Center browser, e.g. with agent-browser eval --stdin.
(() => {
  const assert = (condition, message) => { if (!condition) throw new Error(message); };
  const render = source => {
    const node = document.createElement("div");
    node.innerHTML = renderTicketMarkdown(source);
    return node;
  };
  const markdown = [
    "### Search behavior", "", "The **result count** matches the visible cards.", "",
    "1. Search for `camera`.", "2. Clear the search.", "   - Restore every item.", "",
    "- [ ] Handle an empty result", "- [x] Keep keyboard focus visible", "",
    "| Input | Expected |", "| --- | --- |", "| `camera` | Two results |", "",
    "```json", '{"count": 2}', "```", "", "[Reference](https://example.com/spec)",
  ].join("\n");
  const formatted = render(markdown);
  assert(formatted.querySelector("h3")?.textContent === "Search behavior", "heading");
  assert(formatted.querySelector("strong")?.textContent === "result count", "bold text");
  assert(formatted.querySelectorAll("ol > li").length === 2, "numbered list");
  assert(formatted.querySelector("ol ul li"), "nested list");
  assert(formatted.querySelectorAll('input[type="checkbox"][disabled]').length === 2, "read-only checkboxes");
  assert(formatted.querySelector("table td code")?.textContent === "camera", "table and inline code");
  assert(formatted.querySelector("pre code")?.textContent.includes('"count": 2'), "code block");
  assert(formatted.querySelector("a")?.getAttribute("href") === "https://example.com/spec", "safe link");

  const unsafe = render([
    '<img src=x onerror="alert(1)"><script>alert(1)</script>',
    '<form id=config-form><input autofocus onfocus="alert(1)"></form>',
    '[Click](javascript:alert%281%29)', '[Encoded](jav&#x61;script:alert%281%29)',
    '![tracking pixel](https://example.com/track.png)',
  ].join("\n\n"));
  assert(!unsafe.querySelector("script,img,form,input,[onerror],[onfocus],[id]"), "untrusted HTML escaped");
  assert([...unsafe.querySelectorAll("a")].every(a => !/javascript:/i.test(a.href)), "unsafe URLs removed");
  assert(unsafe.textContent.includes("<script>"), "raw HTML examples stay visible as text");
  assert(unsafe.textContent.includes("tracking pixel"), "image description retained without a request");
  assert(render("Not provided.").textContent === "Not provided.\n", "plain text fallback");

  const purify = window.DOMPurify;
  try {
    window.DOMPurify = null;
    const fallback = render('<img src=x onerror="alert(1)">');
    assert(!fallback.querySelector("img") && fallback.querySelector("pre"), "missing sanitizer fails closed");
  } finally { window.DOMPurify = purify; }
  return "PASS Markdown formatting and unsafe-content checks";
})();
