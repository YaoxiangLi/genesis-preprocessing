# ADR: run-level MultiQC aggregation

Date: 2026-10-07. Status: implemented and validated; local commit `af0bbfb50806babd78b8e9f88df2a55aab0a2a13`. Design preceded implementation.
Base commit: `430cfe31aab5fb9638d18c75a087a9bcb7a868c5`; branch `validation/multiqc`.

## Native recognition investigation

Inspect the pinned MultiQC **1.35** sources and then probe retained Genesis outputs.
Source snapshots/checksums are under `scratch/multiqc/parser-source*`.

| Genesis output | Native recognition | Decision |
| --- | --- | --- |
| `*.read[12]_fastqc.zip` | FastQC `*_fastqc.zip`; reads `fastqc_data.txt` inside ZIP, including internal Filename | Include ZIP once per mate; HTML is already published separately. |
| `*.qc.report.flagstat.txt` | samtools/flagstat matches its QC-passed/QC-failed total header | Include for every library. |
| `*.qc.report.main.stats.txt` | samtools/stats matches its producer header | Include for every library, label full name. |
| `*.qc.report.read1.stats.txt` | Same native stats parser | Include separately; never overwrite main stats. |
| `*.qc.report.idxstats.tsv` | samtools/idxstats filename contains `idxstat` | Include for every library. |
| `*.qc.report.spp.tsv` | phantompeakqualtools exists, but default pattern is `*.spp.out`; parser requires integer fragment length and numeric NSC/RSC | Defer aggregation: Genesis NA fallback is incompatible. Preserve original per-library SPP TSV/PDF; do not rename or impersonate another tool. |
| SPP PDF / insert_lengths.tsv | No matching parser among selected modules | Optional; retain existing publication. Insert sizes are already included in main samtools stats. |
| `*.metadata.tsv` | Not a native tool format | Add an explicitly Genesis-labelled metadata table via supported custom content. |

[Samtools documentation](https://docs.seqera.io/multiqc/modules/samtools),
[versioned search patterns](https://github.com/MultiQC/MultiQC/blob/v1.35/multiqc/search_patterns.yaml),
[SPP parser](https://github.com/MultiQC/MultiQC/blob/v1.35/multiqc/modules/phantompeakqualtools/phantompeakqualtools.py).
The native samtools parsers overwrite colliding cleaned sample names; FastQC may
use its internal Filename. File counts and exit code alone are insufficient.

## Decision

Add one MULTIQC task consuming a sorted, collected set of FASTQC, QC and METADATA
outputs through channels, not a scan of asynchronously published directories. It
has no edge back into alignment, peaks or quantification. The task waits for all
included producers; optional SPP/PDF/insert-size outputs do not become requirements.

Use a dedicated `DAP_SEQ_MULTIQC` YAML + generated Pixi TOML/lock and the existing
Dockerfile. Pin MultiQC 1.35 and record its resolved Python and container identity.
Do not change the R/SPP QC, FastQC or existing scientific environments.

Commit `multiqc_config.yaml` with an explicit module list, disabled broad sample
name cleaning, machine-readable export and no network version check. Keep full
report identifiers so main/read1 stats and R1/R2 remain distinct. Validate a unique
source identity per sample/report kind, expected filenames and FastQC internal
Filename, then require exact sample sets for each required parser in parsed output.
Duplicate sample IDs remain invalid under the existing sheet contract; test both
exact duplicates and distinct names that default MultiQC cleaning could collapse.
Abort rather than silently overwrite. Retain a source-to-sample mapping and hashes.

Publish `output/multiqc/multiqc_report.html` and the complete `multiqc_data/`.
Include run name, pipeline Git SHA, manifest/pipeline version, species, reference
ID and control associations through report header and Genesis custom-content table;
retain structured provenance. Mark unavailable Git metadata explicitly, never guess.
Record dirty-tree status where practical for development runs.

Determinism means one sorted aggregation per run, stable sample identities/parsed
metrics and byte-identical cached outputs on stable resume. Investigate fresh
report determinism separately: timestamps, task paths and generated UI identifiers
may prevent byte-identical HTML across independent executions. Do not strip
scientific differences or misrepresent these limitations.

## Validation

Probe real retained FastQC/samtools outputs with stock MultiQC before choosing final
configuration. Test SE and PE, all five synthetic libraries and shared control;
assert required parser sample sets and machine-readable metrics, not just HTML or
exit status. Run an aggregation-only fixture with one optional SPP file absent.
Negative cases remove a required file, hide a parser, duplicate a report identity,
and introduce collision-prone names. Verify safe failure or distinct entries.
Compare existing BAM/peak/quantification outputs with the prior baseline. Run
focused tests, full `pixi run checks`, and Docker validation, retaining failures,
resources and warnings. Commit source locally only; no image or Git push.

SPP custom-content support could preserve NA strings with an explicitly labelled
Genesis table and no inherited ChIP-seq thresholds. It is deferred here pending a
separate SPP schema decision; the report will disclose this boundary. Biological
QC acceptance thresholds remain UNSPECIFIED.

## Empirical refinements

The stock v1.35 run exited zero but retained only five of ten samtools stats
reports: default cleaning merged main/read1 and selected whichever was encountered
last. Configuring `fn_clean_sample_names: false` preserves all ten; full FastQC
internal filenames preserve seven distinct mates. Native data are in
`report_saved_raw_data` in `multiqc_data.json`, not necessarily individual
per-module JSON files. The wrapper validates exact parser sample sets and exports
four small explicit `genesis_{fastqc,stats,flagstat,idxstats}.json` files as well.

Numeric Genesis SPP rows parse with a search-pattern override using the real
filename. A synthetic NA fallback row reproducibly raises `ValueError` in the
native parser. This confirms the deferral decision without impersonating another
tool. Native idxstats parsed values contain mapped counts and reference lengths;
original per-library idxstats TSVs retain unmapped counts too. Setting its display
fraction cutoff to zero shows all positive-count contigs; no biological acceptance
threshold or upstream processing changes.

MultiQC's `--require-logs` falsely reports missing custom_content despite detecting
the Genesis table. The explicit post-parse guard checks all required native modules
and Genesis metadata instead. Output filenames and directory names are explicit:
a title/filename otherwise causes MultiQC to rename the data directory.

Independent repeated reports have identical metrics, but HTML differs only in a
gzip timestamp, report UUID and configCreationDate. For this pinned renderer,
canonicalize precisely those three fields: gzip mtime=0, a content-derived UUID,
and a message directing readers to the native JSON creation timestamp. Assert one
replacement per field and verify the decompressed plot payload is unchanged.
Native JSON/parquet/logs keep their generation metadata; HTML and explicit metric
exports are byte-reproducible for identical inputs/provenance/config. Require this
in regression tests; cached full output directories must be byte-identical too.

The configured parser probe and focused tests passed: 7 FastQC, 10 samtools stats,
5 flagstat, 5 idxstats, and 5 Genesis metadata identities. Deliberately disabling
FastQC or re-enabling destructive name cleaning lets native MultiQC exit zero,
but the wrapper rejects the incomplete parsed data. Distinct `collision`,
`collision.bam`, and `collision.report` samples remain distinct. An exact duplicate
sample ID and a missing required flagstat file fail before aggregation.
