# Bulk ATAC and execution evidence

Compact observations from the 2026-10-09 validation. Large FASTQs, BAMs, indexes,
HTML reports and complete logs remain in the validation workspace under
`results/supported-atac/` and `results/incremental-prs/`.

- `public-input-checksums.json`: exact input bytes, including original manifests.
- `public-scientific-before.json`: 28 scientific outputs before cache hardening.
- `public-qc-summary.json` and `fastqc-flags.tsv`: observed QC, without plant cutoffs.
- `adapter-sensitivity.tsv` and `adapter-counts.json`: separate maize trimming experiment.
- `dap-portable-comparison.json`: DAP scientific equivalence after portable QC images.
- `scaling.json`: synthetic fragment-stage resources, input hashes and commands.
- `versions.json`: tool versions, container identities and version commands.
- `source-cache-defect.json`: reproduced stale helper cache before the fix.
- `diagram-browser-checks.json` and `status-page-checks.json`: browser checks.

Absolute paths identify retained local evidence. They are not portable input
requirements; the reproduction scripts create manifests for a new location.
