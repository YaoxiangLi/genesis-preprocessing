# Two-species scATAC evidence

Compact observations from the real Arabidopsis and Sorghum pilot. Full command
logs and large data remain in `results/scatac-completion/` in the validation
workspace. See [the report](../../reports/scatac-completion.md) for interpretation.

`summary.json` and `pseudobulk-qc.tsv` summarize measured counts. `stages.json`
and `models.json` retain exact input/output identities, versions and loader
evidence. `commands.json` and `resources.tsv` include successful and failed
attempts. A failed attempt remains a failure even if a later correction passes.
`replicate-qc.tsv` pairs each signal/peak comparison with cell counts, fragment
depth and group FRiP. `portable-release-acceptance.json` records the four further
loader checks against copied release bundles.
Published TSV copies use LF line endings and quoted fields. Every parsed field
matches the original export; both byte-level checksums are recorded in
`provenance/tsv-normalization.json`. Raw results and the candidate release retain
the original bytes. This resolves Git whitespace diagnostics without dropping
empty fields or changing scientific observations.
The evidence-export command itself finishes after this snapshot and is retained
in the workspace command ledger.

The candidate passed computational acceptance. Scientific review remains open,
plant thresholds are unspecified, and no model training is claimed.
