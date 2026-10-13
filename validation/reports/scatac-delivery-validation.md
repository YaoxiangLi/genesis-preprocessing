# scATAC delivery validation

Date: 2026-10-10. Baseline: `37ef72069b8205cd4ce263d4b62139c943d42e02`.
Branch: `feature/scatac-delivery`. New implementation hashes and complete command
logs are retained under `results/incremental-prs/` outside Git. This is a software
validation and public-source audit, **not a completed two-species model-ready release**.

## Implemented and tested

- Lossless workbook snapshots, idempotent registry imports, separate accessions,
  conflict detection, transparent readiness components and source-backed evidence.
- Five-/six-column 10x ATAC/ARC ingestion, exact reference/coordinate validation,
  BGZF and tabix, preserved read support, duplicate-row rejection and verified resume.
- Library-scoped barcodes, replicate-preserving pseudobulks, explicit technical
  merging, reversible membership and deterministic raw cut counts.
- Pinned MACS3 peaks, bigWigs, fragment-based FRiP, recorded unknown TSS enrichment.
- Separate pinned Cherimoya and ChromBPNet export adapters, disjoint chromosome
  folds, context/jitter boundary validation and checksum validation.
- Immutable unreviewed scATAC records in the existing registry. Registration does
  not bypass scientific review or claim model readiness.

The original independent pseudobulk contract produces the same six task identities
and counts as the streaming implementation: nine fragments and twelve supporting
read pairs, across two biological replicates and three synthetic cell types.
The large deterministic fixture checks 100,000 distinct fragments, 200,000 support,
100,000 barcodes, final-record flushing, tabix retrieval and resume.

The real-tool fixture has 900 independent fragments and 2,700 supporting pairs.
It produces exactly 1,800 cut counts, three peaks and FRiP 1.0. A separate fresh
execution produces byte-identical scientific outputs. Raw input checksums remain
unchanged. Full stdout/stderr and time-bearing MACS3 reports are retained as
diagnostics, separate from deterministic scientific-output identity.

Both actual pinned model loaders read the fixture and recover 600 cuts on the
training chromosome. Cherimoya `PeakGenerator` returns sequence `[1,4,2114]` and
signal `[1,1,1000]`; ChromBPNet `ChromBPNetBatchGenerator` returns `[1,2114,4]` and
`[1,1000]`. This tests data loading, not model initialization, training, bias-model
fitness or plant biological quality. Cherimoya's pinned IO module is loaded
directly to avoid unrelated GPU/training imports.

The final full `pixi run checks` passed in 127.50 seconds. Existing real-tool
`pixi run validate-docker --keep` passed in 296.41 seconds, including resume,
FastQC malformed/corrupt input handling, MultiQC collisions and publication tests.
All three model folds were additionally tested with positive/background windows
and recovered 600/zero counts respectively. Pinned-source checks are enforced in
the retained loader scripts.

Implementation commits:
`cff8a30` (inventory), `d23e333` (fragments/pseudobulks),
`710b1df` (CLI/model exports). Exact full SHAs remain in Git history.

## Workbook results

| Species | Candidate experiment rows | BioProjects | BioSample IDs | Unique runs |
| --- | ---: | ---: | ---: | ---: |
| Arabidopsis thaliana | 56 | 11 | 41 | 93 |
| Sorghum bicolor | 25 | 2 | 24 | 37 |

The workbook has eight tabs and 409 records in `scATAC Fable Curated`. Its 81
selected records are not 81 independent biological samples. Confirmed biological
sample, replicate and library counts remain zero in the automatic inventory;
reviewed identity reconciliation is still required. Source values and formulas
remain available for round-trip inspection. All pilot availability findings remain
UNREVIEWED. No review has been attributed to a human without their decision.

Workbook snapshot SHA256:
`2c4dd00d9c1408880a6d8889ad3ba8ebafa8ddd2df58a5528b60890c2a475fce`.
Milestone text snapshot SHA256:
`e76a91f99c5d42c88bd2d78162afaef76ab427b27d57afc2146f8115203f26f0`.
Exports and evidence receipts: `results/scatac-discovery/`.

## Real-data acceptance gates

### Arabidopsis GSE155304 / PRJNA649267

[The GEO study](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE155304)
explicitly describes two independent snATAC replicates from seven-day root nuclei.
Author archives and the integrated annotation object were downloaded with checksums.
The RDS has two gzip layers; both are retained and decoded without changing the
original download. Base R reads its metadata without installing Seurat.

| Archive | Fragment SHA256 | Fragment rows | Read-pair support |
| --- | --- | ---: | ---: |
| GSM4698760 / replicate 1 | `6ab3024000deb86f37605f1789bffd39807a0c2df68e0948fb6ce691fe513699` | 81,811,226 | 113,530,890 |
| GSM4698761 / replicate 2 | `d9ed324151b438b51037bf1afe52f5d0e50660de9e76497474c753210cc6e2c1` | 98,254,384 | 143,341,235 |

Read-only scans cover every record, validate interval/support syntax and retain
per-contig counts. No adjacent duplicate rows were observed; this is **not** a full
uniqueness proof. Only nuclear contigs 1–5 appear; absence of organellar fragments
does not establish the original libraries' organellar fractions.

The annotation object has 4,764 cells. All 2,728 `g10` cells match replicate 1 after
an explicit `B_` prefix removal; all 2,036 `n5` cells match replicate 2 without that
removal. Each match agrees on seven author QC fields. Cross-replicate matches are
zero. This is recorded evidence for an adapter, not an implicit generic barcode
rewriting rule. Labels are cluster identifiers and transferred RNA labels; a
source-backed cluster-to-biological-cell-type mapping is still needed.

GEO declares TAIR10/Araport11. An existing local TAIR10 FASTA has Ensembl Plants 59
annotation provenance, which cannot silently replace the author annotation. Exact
author reference/annotation identity has not been established. Full real-study
pseudobulks and model exports therefore have not been released.

### Sorghum GSE248919 / PRJNA1046450

[The GEO study](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE248919)
lists processed RData objects. The inspected sample declares Sorghum bicolor
v3.0.1. No assembly substitution was made. Author code at
[commit 6a639cb46fb5c7bb256eb78d934d074e36802621](https://github.com/joey1463/C3-C4/tree/6a639cb46fb5c7bb256eb78d934d074e36802621)
references laboratory filesystem fragment paths. Those paths are not public file
URLs. Public fragments and an unambiguous biological/technical replicate mapping
remain unresolved. This does not prove that fragments are unavailable elsewhere.
No FASTQ fallback or multi-gigabyte RData download was used to hide this blocker.

## Versions and resources

Production dependency locks are unchanged. The isolated model-loader validation
environment adds its own frozen uv lock with CPU PyTorch 2.9.0, tangermeme 1.5.0,
pyBigWig 0.3.26 and pyfaidx 0.9.0.3. Nothing was installed system-wide.
Core Python is 3.14.5 and pysam 0.24.1.

- MACS3 3.0.5: `kundajelab/dap_seq_peaks@sha256:10467dd29e3d25ce7769f76f57402bd1a5a582006e911d06479bfcc3e3325df3`.
- pyBigWig 0.3.26: `kundajelab/dap_seq_tracks@sha256:e6dd6ceb79e50fc6db83e9346a920e51fd2bf0dcffbc18c9305b1b6e8c806390`.
- ChromBPNet runtime: `kundajelab/chrombpnet@sha256:6f41e0f59fc025285645e2cbfd1bb6347431b4e0ab6088804d11843cd6aed169`.
- R runtime: `kundajelab/dap_seq_qc@sha256:ace177a497934a26adb305bc0dc92cc6a447fe8ca714b79f72a007c7acb53239`.
- All tested containers: linux/amd64; explicit two-CPU/eight-GiB limits for new container tests.

| Recorded task | Exit | Wall seconds | Wrapper peak RSS KiB |
| --- | ---: | ---: | ---: |
| `scatac-baseline-checks` | 0 | 124.49 | 700956 |
| `scatac-delivery-checks-3` | 0 | 125.45 | 704552 |
| `scatac-real-products` | 0 | 4.03 | 35928 |
| `scatac-streaming` | 0 | 1.55 | 45336 |
| `scatac-model-exports` | 0 | 0.35 | 35496 |
| `scatac-cherimoya-loader` | 0 | 5.72 | 408992 |
| `scatac-chrombpnet-loader` | 0 | 10.85 | 28580 |
| `scatac-cherimoya-all-folds` | 0 | 2.55 | 380992 |
| `scatac-chrombpnet-all-folds` | 0 | 4.19 | 28408 |
| `scatac-author-annotations-retry` | 0 | 8.78 | 28724 |
| `scatac-author-fragments-rep1` | 0 | 109.71 | 34916 |
| `scatac-author-fragments-rep2` | 0 | 133.38 | 34392 |
| `scatac-registry-output` | 0 | 0.30 | 38424 |
| `scatac-inventory-export-evidence` | 0 | 0.36 | 40416 |
| `scatac-delivery-final-checks` | 0 | 127.50 | 698272 |
| `scatac-existing-docker-regression` | 0 | 296.41 | 702928 |
| `scatac-chrombpnet-pinned-loader-retry` | 0 | 3.92 | 27944 |
| `scatac-cherimoya-pinned-loader` | 0 | 2.54 | 380732 |

Wrapper RSS does not include Docker daemon/container memory. Container limits are
not measured peak usage. Full author scans used approximately 32 MiB process RSS.
Exact argv, SHA, elapsed time and acceptance exits are in
[the command summary](scatac-command-summary.json). Original logs, input receipts,
output manifests and resource records remain under `results/`.

## Failures and limitations

Initial checks caught formatting/type errors and a transient broken documentation
link while the report was being written. They were fixed without changing test
assertions. The first RDS read failed because of double compression; an initial
container export used the wrong UID and failed permission checks. The retry used
the current user's UID; no permissions or Docker settings were changed. A later loader invocation contained a mistyped image digest and was rejected
before execution; its corrected pinned-image invocation passed. Failed
attempts and diagnostics are retained. Earlier checks also reported an unrelated
older-than-BAM index warning in the existing curation test; it was not suppressed.

Model bundles retain `model_ready: false`. Reviewed-release promotion, scATAC
integration into prepared-study scheduling, GC-matched backgrounds, TSS enrichment,
real-study model loading and the two-species pilot release are **not completed**.
No production DAP-seq/bulk ATAC parameters, assemblies, trimming or duplicate
policies changed. Biological quality and training suitability remain unassessed.

## Final code acceptance

After the bounded unwrapped-FASTA fix (`0864808`), the complete suite passed again
in **131.66 seconds** (`scatac-release-checks`). The fresh pinned-tool fixture
passed in **5.53 seconds** (`scatac-release-real-products`), including scientific
output identity across two runs. The added reference fixture contains 2.4 million
bases on one line; a non-IUPAC sequence is rejected. Production Nextflow source,
configuration and existing Pixi/uv locks have no changes from the baseline.
