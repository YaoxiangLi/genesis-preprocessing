# README architecture overview validation

Date: 2026-10-10 UTC (2026-10-09 America/New_York).
Base revision: `2c25645adec6157db2e91b2beaca2446d367f07c`.
Scope: README introduction, one maintained SVG overview and this evidence.

The README now introduces scientific processing, optional curation, human review,
execution modes and optional AI before the command manual. Its six-row status
table separates available implementations, the scope of existing validation and
remaining live acceptance. The table links to existing scientific and hybrid-LLM
reports; it makes no new scientific, biological-accuracy or deployment claim.

The [overview](../../docs/images/genesis_architecture_overview.svg) reuses eleven
existing licensed Genesis/Tabler vector assets. It is an editable, self-contained
1600 × 1120 SVG with selectable labels, an accessible title/description and embedded
source, checksum and full license metadata. This is a maintained architecture
illustration, not a generated Nextflow DAG or a live status display.

## Results

| Check | Result |
| --- | --- |
| `genesis_tools/.venv/bin/python tests/verify_readme.py` | PASS: 130 documented commands parse; local documentation links resolve |
| `git diff --check` | PASS |
| SVG XML, accessibility, eleven asset hashes and embedded license notices | PASS; no scripts, foreign objects, remote images or fonts |
| Native SVG browser geometry | PASS: 57 labels; no text overlap, labels outside panels or connector/text crossings |
| Local README-style embedding, 1040 px and 390 px viewports, light/dark themes | PASS: image loads, full-size link retained, no document overflow or page errors |
| GitHub Markdown API rendering of the README introduction | PASS: expected heading, linked SVG and six capability rows with four columns |
| GitHub-parsed content in a local browser preview | PASS: desktop visual inspection; phone-width table scrolls without widening the document |

Browser: Chromium 148.0.7778.96. Native-size, desktop and narrow-screen images were
visually inspected. Initial overlong labels were shortened before the final checks.
Small-screen readers can open the linked full-size SVG for detailed labels. The
diagram has a fixed white background and remains visible on a dark README page.
The browser geometry checks used only local assets and made no remote requests;
the separate Markdown API request rendered the intended public README text.

[Machine-readable results and file hashes](../evidence/architecture-overview/checks.json)
record the final SVG/README content, geometry and preview checks. The previews use
local README-style CSS, not a claim of testing every GitHub client or browser.

No scientific source, runtime behavior, CLI, dependency, schema or existing
schematic changed. The full pipeline suite and live API/GPU/SSH acceptance were
not rerun for this documentation-only update. Existing detailed guides and
their validation qualifications remain in place.
