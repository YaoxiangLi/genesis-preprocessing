# Expanded plant comparison evidence

Read the [results report](../../reports/expanded-plant-comparison.md) for the
scientific interpretation and the
[experiment recipe](../../../benchmarks/experiments/reference-comparison-20261014/README.md)
for reproduction commands.

| Files | Contents |
| --- | --- |
| [Report PDF](expanded-comparison.pdf) | Report text, tables and measured figures; source hashes in the adjacent manifest |
| [figures](figures/) | Method quality, timing/memory, depth and cross-reference plots; PDF/PNG/SVG, TSV tables and renderer hashes |
| [reference-runs](reference-runs/) | Completed reference-run archives, exact method commands, peaks and measurements; sequencing files and indexes excluded |
| [reference-concordance-1m.json](reference-concordance-1m.json) | Every reciprocal mapping outcome and paired fixed-region fragment count |
| [annotation-sensitivity-1m.json](annotation-sensitivity-1m.json) | Full TSS profiles, common gene set and annotation-specific denominators |
| [caller-diagnostics-tair10-1m.json](caller-diagnostics-tair10-1m.json) | TAIR10 Genrich operating-point comparison and exploratory biological-pair IDR |
| [caller-diagnostics-colcen-1m.json](caller-diagnostics-colcen-1m.json) | The corresponding Col-CEN assessment |
| [caller-diagnostics-colcen-5m.json](caller-diagnostics-colcen-5m.json) | Deeper Col-CEN Genrich operating points and biological-pair IDR |
| [dap-se-5m-motifs](dap-se-5m-motifs/) | Independent PBM motif hits, GC-matched controls, individual windows and exclusions |
| [sources](sources/) | Complete FASTA scans, publisher acquisition receipts and explicit reference derivations |
| [Maize coordinate mappings](sources/maize-mapping/) | Both publisher-checked chains, explicit contig aliases and block/length validation |
| [A. lyrata identity mapping](sources/lyrata-identity-mapping/) | All 695 uniquely matched complete contigs and exact sequence identities |
| [checks.json](checks.json) | Exact regression commands, scope, log hashes and limitations |
| [installed-wheel-check.json](installed-wheel-check.json) | Direct reference CLI from an isolated wheel installation without a workflow checkout or Pixi |
| [run-status.json](run-status.json) | Timestamped completion/pending/failure ledger; a snapshot, not a live status service |
| [snapshot-manifest.json](snapshot-manifest.json) | Original and public hashes for loose assessment/source records |
| [recipe-sources](recipe-sources/) | Exact historical preparation source used by the continuing runs, named by SHA256 |

The six original Arabidopsis method matrices comprise 64 completed
method/repetition cases. Their
[raw measurements and compact archives](../method-comparison-20261013/README.md)
remain the inputs to the expanded figures. The native/production ATAC comparison
is recorded separately from those component timings.

New public archives are path-redacted derivatives. Their manifests record the
original archive hash, each original member hash and each published member hash.
The published archive was then read back and verified. `<CHECKOUT>` and
`<LOCAL_HOME>` mark path substitutions; they are not literal runnable paths.
Input checksums, measurements and biological identifiers are unchanged.

These files do not contain sequencing reads, BAMs, indexes, environments or
credentials. Use new local paths and the pinned acquisition/experiment recipes
to reproduce a comparison. An archived report is not an execution-resume cache.

Pending and failed attempts never enter successful timing or biological
summaries. Exploratory caller and IDR assessments retain their separate input
policies and do not authorize a change to the production pipeline.
