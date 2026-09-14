/* Ticket content is untrusted. Keep rendering local and sanitize before insertion. */
function renderTicketMarkdown(value) {
  const source = String(value ?? "");
  const escape = text => String(text).replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
  if (!window.marked || !window.DOMPurify) {
    return `<div class="ticket-markdown"><pre>${escape(source)}</pre></div>`;
  }
  const parser = new marked.Marked({
    gfm: true,
    async: false,
    renderer: {
      // Show HTML examples literally. Do not execute markup from an issue.
      html: ({ text }) => escape(text),
      // Do not fetch images or tracking pixels from ticket content.
      image: ({ text }) => escape(text),
    },
  });
  const html = parser.parse(source);
  const clean = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ["p", "br", "hr", "strong", "em", "del", "code", "pre",
      "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "blockquote",
      "table", "thead", "tbody", "tr", "th", "td", "a", "input"],
    ALLOWED_ATTR: ["href", "title", "start", "type", "checked", "disabled"],
    ALLOW_DATA_ATTR: false,
  });
  return `<div class="ticket-markdown">${clean}</div>`;
}
