# Bulk ATAC prototype and differential benchmark

Status: **PASS for the synthetic computational scope**. Branch `validation/bulk-atac-prototype`, worktree `scratch/bulk-atac-prototype`, commit `0b8850207e94a3d4909bf4ab99d18c03cd010cc2`. This separate `pixi run pipeline-atac` entry does not change the DAP workflow or defaults. Design preceded implementation: design/bulk-atac-spec.md and comparison TSV.

The retained baseline PE treatment fixture supplies 32,000 pairs, 75-bp mates, a seeded 2-Mb synthetic chr1 and enriched loci. The annotation/TSS file is explicitly artificial. It is not Sorghum and not a biological ATAC dataset. Raw FASTQs are reused unchanged; nf-core staging copies have distinct R1/R2 basenames and identical SHA256s. No adapter trimming is performed; the command requires an explicit synthetic adapter-free policy.

Implemented stages: raw mate FastQC, bwa-mem2, samtools fixmate/markdup without removing from the original BAM, explicit both-mate MAPQ30 and marked-duplicate exclusion into an experiment-owned BAM, organellar accounting/filter contract, fragments, +4/-5 interval cuts, MACS3 BAMPE with keep-dup all after exclusion, fragment FRiP, declared toy TSS enrichment, fragment histogram and NRF/PBC, required-module MultiQC and provenance. Empty organellar lists are explicit because the synthetic genome has no organelles; a separate fixture tests actual plastid exclusion.

## Validation and measured outputs

| Check | Result |
| --- | --- |
| Known-answer metrics fixture | PASS: mate-asymmetric MAPQ, duplicate/organellar counts, +4/-5 endpoints, FRiP=0.5, NRF/PBC, TSS=40/21, strand symmetry, zero background null |
| Focused lint | PASS after formatting/type annotations |
| Complete project `pixi run checks` | PASS, 85.88 s |
| Normal `pixi run pipeline-atac ...` and final corrected provenance | Eight real-container tasks; initial run 22.09 s, explicit-policy correction 16.84 s, final publication/provenance update 6.86 s with scientific tasks cached |
| Exact explicit-session resume | PASS, 5.19 s, 8/8 cached; 39 published files byte-identical |
| Required MultiQC content | PASS: two FastQC entries, two each of flagstat/stats/idxstats (marked and usable BAMs) |
| Raw mapped proper pairs | 32,000 |
| Pairs failing either mate MAPQ30 | 101 |
| Eligible before duplicate exclusion | 31,899 |
| Marked duplicate pairs in that population | 345 (0.0108153861) |
| Usable unique fragments | 31,554 |
| Peaks | 200 |
| Fragment FRiP | 0.9430817012 |

Full commands, source SHAs, input checksums, stdout/stderr, exit statuses, elapsed time and GNU time maximum RSS are retained under results/incremental-prs/atac-*. Task-level peak RSS and read/write character counters are in trace.tsv; they are not physical disk-I/O or whole-server peak-memory measurements. Final outputs and source/input SHA256 provenance are under results/bulk-atac/final/. Source hashes in provenance distinguish the exact recipe from the Git label. Disk footprint and image identities are recorded in results/completion manifests. All plant acceptance thresholds remain UNSPECIFIED.

## Reference benchmark

The unmodified nf-core/atacseq 2.1.2 checkout at `1a1dbe52ffbd82256c941a032b0e22abbd925b8a` completed with the same FASTQ bytes and exact synthetic genome. External override configuration is scratch/completion/nfcore-benchmark.config; institution configs are pinned at `cd307e66da1fa765329b12615292e90846e1d2ec`, nf-validation at 1.1.4, Nextflow at 25.10.4. Separate launch directories prevent accidentally loading Genesis configuration/schema. Trimming, replicate merging and unrelated differential/annotation plots were explicitly disabled for this bounded fixture. ataqv, Picard, samtools and MultiQC ran.

The successful initial reference run took 152.92 s after staged-mate correction, including container startup/pulls; this is not a fair steady-state performance ranking against the already-cached Genesis images. A command-line narrow-peak/q=0.01 rerun took 40.24 s. Software versions are in nfcore-narrow/pipeline_info/software_versions.yml; image IDs/repository digests/architecture are in results/completion/container-inventory.json. Reference tools include BWA 0.7.17-r1188, MACS2 2.2.7.1, Picard 3.0.0, ataqv 1.3.1 and versioned samtools modules. Genesis uses bwa-mem2, MACS3 3.0.5, samtools 1.24 and pysam 0.24.1; toolchains are intentionally not identical.

| Independent comparison | Genesis prototype | nf-core matched narrow run |
| --- | ---: | ---: |
| Usable fragments | 31,554 | 31,554 |
| Peaks | 200 | 200 |
| Fragment-coordinate multisets | identical | identical |
| Fragment-length histogram | identical | identical |
| Peak base-pair Jaccard | 1.0 | 1.0 |
| Independently defined fragment FRiP | 0.9430817012 | 0.9430817012 |
| Tool-reported FRiP | fragment definition above | 0.94221 (20% read-overlap definition) |
| TSS enrichment | 0.3628117914 (toy window) | 2.8571428571 (ataqv) |

The TSS values have different windows/normalization and are not interchangeable. Artificial TSS coordinates carry no biological quality conclusion. The fixture lacks a useful intermediate MAPQ spectrum, realistic error/adapter contamination and nucleosomal populations, so equal outputs do not establish policy equivalence on plants. Comparison JSON/TSV and the independent script are retained.

Reference resume: 36/38 tasks cached; software-version aggregation and MultiQC reran. All alignment/filter/peak/ataqv tasks were cached. This reporting-layer rerun is recorded, not hidden or described as all-cache success.

## Preserved failures and warnings

The first prototype report failed because MultiQC chose its default data-directory name; the next attempt exposed the actual parsed-data key prefixes. A committed explicit config and exact key checks fixed both without weakening required-content assertions. Formatting/type-annotation failures were repaired; original logs remain. A failed run also produced a Nextflow report-render interruption warning; successful final runs retain reports/timeline/DAG.

The first nf-core help invocation inherited Genesis launch-directory configuration. The explicit-config attempt still resolved the wrong launch-directory schema; isolating its launch directory fixed that without disabling validation. Next, identically named mate files collided during staging; distinct byte-identical copies fixed the input adapter. Finally, an override loaded after module configuration produced a broad MACS2 command under a narrow-named publication path. The command was inspected, the run preserved, and explicit CLI narrow mode/q fixed the comparison. This demonstrates why output-folder labels are insufficient evidence. Deprecated docker.userEmulation and unmatched optional process-selector warnings remain in reference logs; they were not suppressed.

Limits: no real plant ATAC validation, SE ATAC, replicate/IDR benchmark, trimming implementation or production-scale streaming guarantee. The prototype groups reads in memory and supports the documented synthetic scope only. Local FastQC/MultiQC image IDs require a separately authorized image deployment for portability. Full scATAC and model training are not claimed by this prototype.

Final content inspection found and repaired two prototype contract defects. An empty Nextflow `--organelles` argument became boolean true; the code now requires a string `NONE` or contig list, records an actual list, and rejects the empty flag before any task. A known-answer CLI regression passed. The chr1-only fixture's biological selection was unchanged, but the old incorrect metadata is preserved under pre-organellar-fix/. Secondly, BED/cut-count files existed in work directories without declared publication outputs. The publication regression first failed on missing files, then passed after adding explicit output declarations. Published BED has 31,554 rows and cut-count sum is 63,108; no FASTQs or BAMs are published. The final full suite, focused metrics/lint, differential comparison and eight-task stable resume pass. See atac-release-* and atac-publication-{red,green} evidence directories.

The nf-core broad-to-narrow/q change is explicitly a **peak-calling sensitivity experiment** used to align comparison parameters, not a production default fix. No DAP peak policy changed.
