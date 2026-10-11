# Single-cell ATAC fragments and pseudobulks

Genesis imports single-cell ATAC fragments and produces cell-type signals while
keeping biological replicates separate. It supports 10x ATAC, ARC and explicitly
documented Chromap fragments. Run these commands on a standalone Linux server;
track and peak generation uses pinned Docker images. Raw-read reconstruction
requires a separate, protocol-specific workflow.

## Discover studies

```bash
pixi run genesis scatac inventory import inventory --source 'Plant Data Sets.xlsx' --source-id plant-data-sets --registry catalog
pixi run genesis scatac inventory discover inventory
pixi run genesis scatac inventory runs inventory
pixi run genesis scatac inventory audit inventory
pixi run genesis scatac inventory evidence inventory --source evidence.json
pixi run genesis scatac inventory resolve inventory --source identities.json
pixi run genesis scatac inventory export inventory --output inventory-tables
```

The importer retains the workbook and original cell values, including formulas
and cached values. It focuses on Arabidopsis and Sorghum in `scATAC Fable Curated`.
Accessions remain separate from biological identities. Repeated imports do not
create duplicate registry records. Six TSVs describe studies, candidate libraries,
BioSamples, accessions, readiness and metadata issues.

Discovery retains dated GEO and ENA snapshots with checksums. It can find studies
beyond the workbook. RNA samples, mixed-species records and reused accessions stay
visible in the evidence; they do not become additional scATAC libraries automatically.
Archive failures are reported as incomplete discovery. Rerunning uses verified
snapshots; `--refresh` retrieves a new revision. Biological identities require
source-backed assertions and remain subject to release review.

Availability evidence records a source URL, retrieval date, snapshot checksum and
review status. It never overwrites spreadsheet values. Readiness gives equal
weight to fragments, cell annotations, reference compatibility, biological
replicate evidence and metadata completeness. The first four components earn
points only with approved evidence. This is a processing-priority score, not a
biological quality score. A named reviewer is required for approved evidence.

## Process known libraries

```bash
pixi run genesis scatac ingest --manifest library.json --output fragments/library-1
pixi run genesis scatac ingest --manifest library.json --output fragments/library-1 --resume
pixi run genesis scatac pseudobulk --input fragments/library-1 --input fragments/library-2 --annotations cells.jsonl --policy policy.json --output pseudobulk
pixi run genesis scatac products --input pseudobulk/TASK_ID --output products/TASK_ID
pixi run genesis scatac qc --input products/TASK_ID
pixi run genesis scatac register --input products/TASK_ID --registry catalog --level full --bigwig-python validation/environments/scatac-loaders/.venv/bin/python
```

Each library manifest declares its biological identity, producer/version, exact
FASTA SHA256, chromosome lengths, organellar contigs and source-fragment checksum.
Source offsets must be explicit. The supported 10x adapters require BED0 half-open
intervals and already-applied +4/−5 offsets. Ingestion never shifts coordinates.
Five-column support counts and optional sixth-column strand are preserved.
Duplicate library/barcode/interval rows are rejected for review, not silently removed.
The Chromap adapter also requires the MAPQ, duplicate, trimming, barcode translation
and command provenance used to create the fragments.

Cells are keyed by **library + barcode**. The existing
[cell contract](../../validation/design/scatac-metadata-schema.yaml) governs
annotation provenance and explicit ATAC inclusion. Unknown QC values remain null;
plant thresholds remain unspecified. Biological replicates are never pooled.
Independent technical libraries require a named, explicit merge declaration.
Different cells with identical coordinates remain independent molecules.

Pseudobulks count each selected fragment once, regardless of read support. They
retain source-cell membership, library composition, exclusions and support totals.
For the recorded `chrombpnet-atac-v1` signal convention, a 10x interval `[s,e)`
contributes cuts at `s` and `e`. This converts source offsets to the audited model
convention; it does not shift the stored fragments. Out-of-reference cuts require
an explicit error or exclusion-and-report policy.

The policy must specify organellar handling, boundary handling, a peak q-value and
an effective genome size per reference. MACS3 runs in BEDPE mode with all selected
molecules retained. Signals are unstranded raw cut counts. FRiP counts unique
selected fragments overlapping the union of the group's peaks by at least one
base. An optional checksum-bound `tss` file adds a strand-oriented TSS profile.
Its three columns are chromosome, zero-based TSS position and strand. Enrichment
is the central-base count divided by the mean outer 100-base flanks of a ±2,000-base
window. This declared metric is not interchangeable with every other tool's TSS score.
Zero-background profiles return null. No plant pass/fail threshold is applied.

Compare matching cell types across two biological replicates with:

```bash
pixi run genesis scatac compare --input products/REP1_TASK --against products/REP2_TASK --bin-size 1000 --output concordance.json
```

The comparison reports peak overlap and signal correlations on shared genomic
bins, with and without bins that are zero in both replicates. It never pools reads.

SQLite keeps fragment sorting and cell joins on disk. Plan free space for the
input, temporary database, indexed fragments and each selected group's outputs.
`--resume` verifies input identity and output checksums. Changed inputs, annotations,
policy or implementation require a new output directory. Failed staging directories
retain diagnostics; complete outputs are published atomically.

## Export model inputs

```bash
pixi run genesis scatac model export --input products/TASK_ID --config model.json --output models/TASK_ID
pixi run genesis scatac model validate --input models/TASK_ID
pixi run genesis scatac model validate --input models/TASK_ID --model-root ../benchmarks/cherimoya --output loader-tests/TASK_ID
```

Adapters target Cherimoya `8ecf7f791ec07c05a701076cc58a0f845bf97609` and ChromBPNet
`ece97c93ccaa2d9ee5bc5687e62f4dbf8d055367`. The config names one target, its audited
SHA, even input/output window sizes, jitter, and explicit train/validation/test
chromosomes. No human chromosome defaults are supplied. The export includes a
FASTA, sizes, raw-count bigWig, summit-centered peak regions, deterministic
genomic background tiles, cell membership, QC and parent provenance.
Choose `nonoverlapping-genome-tiles-v1` or `gc-matched-genome-tiles-v1` explicitly.
GC matching requires `background_seed` and records the matching differences;
insufficient background space is an error. Chromosome folds prevent coordinate-window
leakage; sequence-homology leakage remains a separate modeling concern.

Both adapters expose one unstranded channel without a control track. ChromBPNet
requires a recorded bias-model plan; exporting files does not supply or validate
a plant bias model. Do not apply another Tn5 shift to exported tracks.

Actual loader validation tests both a peak and a background window in each fold
against the pinned model code. It checks tensor dimensions and base-level signal.
Add `--resume` to reuse a verified export or loader result.

## Assemble a reviewed release

```bash
pixi run genesis scatac release --manifest release.json --registry catalog --output pilot-release
```

The release manifest lists each group's `products` directory and, under `models`,
each target's `bundle` and loader `validation` directories. `required_species`
names the species that must each have two biological replicates within one study.
Paths are relative to the release manifest or absolute.

The release includes fragments, membership, signals, peaks, model bundles, QC,
review decisions and checksums. Registration connects each pseudobulk to the
existing metadata, QC and eligibility review system. A candidate remains
`model_ready: false` until structural validation, both loader tests and all
required reviews pass. Loader acceptance does not establish biological quality
or demonstrate successful training.

See the [model handoff](scatac-model-handoff.md) for loader setup and the [validation report](../../validation/reports/scatac-delivery-validation.md)
for the actual tests, public-data findings and remaining release gates.
