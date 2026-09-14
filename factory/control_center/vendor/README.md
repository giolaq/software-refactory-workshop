# Locally bundled Markdown dependencies

The Control Center has no frontend build step. These pinned browser bundles
are served locally so ticket formatting works without a CDN or internet access.

| File | Package | Version | Source |
| --- | --- | --- | --- |
| `marked.umd.js` | Marked | 18.0.13 | https://registry.npmjs.org/marked/-/marked-18.0.13.tgz (`package/lib/marked.umd.js`) |
| `purify.min.js` | DOMPurify | 3.4.15 | https://registry.npmjs.org/dompurify/-/dompurify-3.4.15.tgz (`package/dist/purify.min.js`) |

License texts are included beside the bundles. Marked is MIT licensed;
DOMPurify is used under its Apache-2.0 license option.

Keep bundles unmodified. Review upstream security releases when updating them
and run the Control Center Markdown browser checks. `markdown.js` escapes raw
HTML, omits images, and sanitizes generated HTML with a restricted allowlist.
Never insert `marked.parse()` output directly into the interface.
