# Public scATAC data expansion

Audit date: 2026-10-11. This inventory measures processing readiness, not biological
quality. Source metadata, retrieval dates and SHA256 snapshots are retained in
`results/scatac-discovery/inventory/` in the validation workspace.

The workbook contains 81 candidate Arabidopsis/Sorghum experiment rows. Public
archive discovery inspected 17 GEO series and 404 records mentioning either
species. These include RNA, bulk ATAC and mixed-species records. They must not be
counted as 404 single-cell ATAC libraries.

| Species | Workbook experiment rows | Reconciled candidate rows | BioProjects | BioSample accessions | Sequencing runs |
| --- | ---: | ---: | ---: | ---: | ---: |
| Arabidopsis thaliana | 56 | 81 | 14 | 66 | 125 |
| Sorghum bicolor | 25 | 25 | 2 | 24 | 37 |

The 25 additional candidate rows comprise eight INTACT bulk ATAC experiments,
16 sorted-cell-type ATAC experiments and one new single-species scATAC candidate.
The first two categories may support separate bulk ATAC benchmarks; they are not
new barcode-resolved scATAC datasets. Biological sample and replicate counts
remain unknown outside the four explicitly documented pilot libraries. Archive
accessions are not substituted for those identities.

The export contains 16 accession-defined study groups, 106 candidate experiment
rows, 90 distinct BioSample accessions and 162 matched sequencing runs. Four
biological samples, four biological replicates and four technical libraries have
explicit documented identities for the pilot; the remaining biological counts
are unresolved. None has been marked human-approved. Updated availability
evidence records the inspected author objects and exact downloaded references
without converting those observations into approval.

## Processing priorities

| Study | Available evidence | Next action | Status |
| --- | --- | --- | --- |
| [GSE155304](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE155304) | Two Arabidopsis root fragment libraries, author cell metadata and published cell-type labels | Review the completed two-replicate candidate and reference/annotation provenance | Computational pilot passed; review pending |
| [GSE248919](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE248919) | Sorghum multiome annotations; public SRA retains genomic and barcode reads | Review the completed reconstruction of one library per biological replicate and its differences from the author pipeline | Sensitivity pilot passed; review pending |
| [GSE299784](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE299784) | Two Arabidopsis root fragment libraries and an author RDS object | Resolve the numeric cluster-to-cell-type crosswalk before aggregation | NEEDS_METADATA |
| [GSE303996](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE303996) | Arabidopsis fragments and annotated R objects across four conditions | Resolve replicate identity within each condition; do not pool conditions to manufacture replication | NEEDS_METADATA |
| [GSE320172](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE320172) | Newly public Arabidopsis control-root scATAC fragments; a separate infected sample has mixed organism metadata | Verify labels and reference; resolve host/parasite handling separately | NEEDS_METADATA / NEEDS_REFERENCE_RESOLUTION |
| [GSE326975](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE326975) | Arabidopsis multiome matrices and RDS objects | Locate fragment coordinates or reconstruct from raw reads with explicit barcode semantics | NEEDS_PROCESSED_FILES |
| [GSE332675](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE332675) | A multispecies snATAC atlas with tissue-specific H5AD objects | Resolve each library's species and replicate identity; locate fragment coordinates | NEEDS_METADATA / NEEDS_PROCESSED_FILES |
| PRJNA1063172 | Sorghum sciATAC raw-data candidate already present in the workbook | Resolve protocol-specific barcode reads and the exact v5.1 reference independently | NEEDS_REFERENCE_RESOLUTION |

GSE320172 was public on 2026-10-05. Its control ATAC record is GSM9536803;
GSM9536804 is retained as a mixed-species candidate. The available records do not
establish two biological replicates in one condition. ENA returned no public runs
for PRJNA1427083 at retrieval; this is recorded as `NO_ARCHIVE_RUNS`, not as proof
that no raw data will become available.

Both fragment endpoints returned HTTP 200 on 2026-10-11. The advertised sizes are
1,934,714,767 bytes for the control and 1,086,519,823 bytes for the mixed-species
sample. These were HEAD requests only: no additional sequencing data were
downloaded, and full-file checksums remain unverified.

GSE332675 is an additional lead outside the strict single-species candidate
counts above. Broad organism fields and pooled author outputs require explicit
reconciliation. A peak-by-cell matrix alone cannot recover cut-site coordinates
for sequence-to-function models.
Its deposited objects name Arabidopsis thaliana, Arabidopsis lyrata, Brassica
oleracea and Capsella rubella tissues. The associated [Zenodo record](https://zenodo.org/records/18407668)
provides peak-accessibility tables and genome annotations. Inspection of the
[author analysis code](https://code.jgi.doe.gov/AMoralesCruz/regulatory-neighborhoods),
pinned at `2e86323116ad371408d9033b1aaec87c5625359e`, covered all 24 source files.
Neither that inspection nor the archive's file metadata identified a direct
fragment download. These resources can support further annotation work; they do
not yet establish additional fragment-ready libraries. The metadata snapshot and
source hashes are retained in `provenance/extra-atlas-source-audit.json`.

The separately useful bulk datasets are
[GSE142613](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE142613) and
[GSE190753](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE190753).
The expansion checks retrieved metadata and file headers. GSE299784's processed
fragments and RDS object were downloaded during pilot selection, but its unresolved
cell-type crosswalk kept it out of the selected pilot. No additional raw sequencing
studies were downloaded for the expansion audit.

The GSE299784 object contains 14,466 cell records across two deposited libraries
and 18 numeric ATAC clusters. It retains source TSS enrichment, nucleosome signal,
peak overlap and alignment counters. Numeric clusters are not cell-type names;
cluster numbers from the separately reanalyzed RNA atlas cannot be substituted.
The reproducible metadata audit is `provenance/extra-root-candidate-audit.json`.
This study is a practical next candidate once its author crosswalk is resolved.

## Evidence and limits

The ENA reconciliation contains 1,342 project-run records across 16 projects.
Only explicit experiment matches enter candidate run relationships. Project-wide
rows include other assays and organisms; 1,342 is not a scATAC run count.
Repeated imports preserve the original spreadsheet values and do not duplicate
GSM accessions shared by a series and its superseries.

The exported `scATAC_studies.tsv`, `scATAC_samples.tsv`, `scATAC_libraries.tsv`,
`scATAC_accessions.tsv`, `scATAC_readiness.tsv` and `scATAC_metadata_issues.tsv`
are under `results/scatac-completion/inventory-tables/`. The readiness score keeps
fragment availability, labels, reference compatibility, replicate evidence and
metadata completeness separate. None is a plant QC threshold or approval.

Workbook SHA256:
`2c4dd00d9c1408880a6d8889ad3ba8ebafa8ddd2df58a5528b60890c2a475fce`.
Discovery and ENA commands, complete logs, resource usage and source hashes are
in `results/scatac-completion/commands/`. This is a bounded search, not a claim
that every public plant dataset has been found.
