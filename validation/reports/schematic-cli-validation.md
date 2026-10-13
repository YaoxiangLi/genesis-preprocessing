# Genesis schematic CLI validation

Date: 2026-10-09. Base: `78ea67231a1f246aee4c7d0b80c4eede1c5fb584`.
Branch: `feature/schematic-cli`.
Implementation commit: `e0b71e452493de99474bc226993ca01d546fb32f`.

## Change

`pixi run genesis schematic` generates standalone SVG figures for DAP-seq,
bulk ATAC and execution. It supports light/dark themes, optional animation,
editable JSON templates, a licensed icon catalog and overwrite protection.
Figures use original Genesis seedling/DNA artwork and illustrated stage cards.
The existing metro maps remain available.

Sixteen Tabler icons are pinned to
`a4ce1404bc6d24d3c365afe7b258d6bf6f48d62d`. Sources, authors, licenses and SHA256
values are in the packaged `schematics/assets/catalog.json`. Full MIT notices
for Tabler and the original Genesis artwork are embedded in exported SVG
metadata. Rendering uses only the standard library and bundled files.

## Verification

| Check | Result |
| --- | --- |
| Full `pixi run checks` | PASS: 113.70 seconds |
| Twelve workflow/theme/animation combinations | PASS: deterministic XML, stage and edge counts, licensed assets, no network calls |
| Custom JSON and CLI | PASS: export, round trip, escaping, overwrite protection, invalid layout rejection |
| Geometry | PASS: connections do not cross unrelated cards; independent built-in routes do not share line segments |
| Browser checks | PASS: nine cases; 37.51 seconds |
| Package build | PASS: offline source distribution and wheel; 1.63 seconds |
| Wheel inspection | PASS: assets and licenses included; rendering outside the checkout matches the repository SVG |
| Scientific workflow, container and lock-file changes | None |

Visual inspection covered all three final light figures and dark ATAC. Browser
checks used Firefox 157.0.1, including text bounds, pairwise text overlap,
animation and reduced-motion preferences. Screenshots are retained under
`results/schematics/`, not in Git.

The first package build exposed an existing missing-package-README warning.
A package README was added and the final source/wheel build is warning-free.
Visual review also caught shared DAP connector segments; separate routing lanes
and a regression assertion now prevent that ambiguity in the built-in figures.
Development lint findings were corrected without relaxing checks.

No scientific processes or filtering choices changed. Docker data workflows
were not rerun for this illustration-only feature; the full project suite
includes existing workflow stub and controller regressions.

## Reproduction and evidence

```bash
pixi run genesis schematic --workflow atac --output atac.svg
pixi run genesis schematic --workflow atac --theme dark --animate --output atac-dark.svg
pixi run genesis schematic --workflow atac --template custom.json
pixi run genesis schematic --spec custom.json --output custom.svg
pixi run checks
pixi run uv build --offline genesis_tools --out-dir /path/to/artifacts
```

Pixi 0.70.1, uv 0.11.33 and project Python 3.14.5 were used. The offline package
render check also exercised the standard-library renderer in Python 3.12.12
with site packages disabled. This does not change the package's Python >=3.14
installation requirement. Dependency lock files remain unchanged.

The command ledger records exact argv, base SHA, source-file checksums,
elapsed time, peak launcher RAM, exit status and complete stdout/stderr paths.
See `validation/evidence/schematics/`; full logs are retained in workspace
`results/incremental-prs/schematic-*/`. Artifact inputs are the committed JSON
templates and checksummed SVG assets.

Changed files: the schematic package and assets, CLI registration, package-data
configuration, package README, regression test, check runner, generated previews,
usage guide and README links. No new runtime dependency or system installation
was introduced.

## Limits

These are maintained illustrations of selected dependencies, not automatically
inferred execution DAGs. Animation is illustrative, not live status. Custom
layouts are limited to 16 stages on a 4×4 grid and 40 connections. Complex
layouts and converted publication formats still need visual inspection; preserve
the bundled license notices if conversion removes SVG metadata. No raster or PDF
export dependency is bundled.
