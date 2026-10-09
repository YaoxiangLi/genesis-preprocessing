# ADR: offline Genesis workflow illustrations

Date: 2026-10-09. Status: implemented.

Use a native SVG renderer with versioned JSON templates, available through
`pixi run genesis schematic`. Keep the existing detailed metro maps. The new
illustrations use stage cards, a botanical palette and original seedling/DNA
artwork, with DAP-seq, bulk ATAC and execution templates.

Bundle a small selection of MIT-licensed Tabler outline icons at a pinned Git
revision. Record source, author, license and checksum per asset; verify checksums
when rendering and embed full notices in every SVG. License the original Genesis
art separately under MIT. This avoids paid services and network dependencies.
Future artwork needs its own source and redistribution review before inclusion.

Use the Python standard library and existing project environment. Package the
assets with genesis_tools so rendering does not depend on a repository-relative
path. Accept declarative JSON rather than arbitrary SVG imports. Reject invalid
identifiers, duplicate cells, missing endpoints and connectors crossing unrelated
cards. Escape labels and restrict imported artwork to simple vector geometry.

Figures are maintained illustrations of selected dependencies, not generated
Nextflow execution graphs or live monitoring. Animation conveys direction only.
Offer static output, explicit light/dark themes, reduced-motion support and
editable text. Custom layouts are bounded to four columns and four rows;
complex or publication-specific layouts can be edited in a vector editor.

Validation covers deterministic output, offline rendering, embedded licenses,
package contents, CLI export and overwrite protection, malformed layouts, browser
text bounds and animation. Rendering changes no scientific pipeline behavior.
