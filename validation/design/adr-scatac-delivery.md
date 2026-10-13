# Fragment-first scATAC delivery

Status: accepted for implementation; real-data release acceptance remains open.

## Decisions

Reuse the existing cell/pseudobulk contract and registry. Add version-4 records for
inventory snapshots and unreviewed scATAC outputs; leave version 1–3 schemas intact.
Keep single-cell fragments separate from the DAP-seq and bulk ATAC workflows.

Use disk-backed sorting and joins, BGZF, and tabix through the already locked
pysam dependency. Preserve support counts, source coordinates, library namespaces,
biological replicates and reversible membership. Reject duplicate fragment rows
rather than guessing whether they represent repeated sequencing or independent
molecules. Technical-library merging requires an explicit independent-library
statement; this is not an adapter for resequencing the same molecules.

Keep standalone commands as the first execution interface. Use the existing
immutable MACS3 and track containers. Prepared-study scheduling and reviewed-release
promotion need separate scATAC integration; storing an output record is not review
approval. This boundary is explicit in command outputs and user documentation.

Model export uses separately pinned adapters. Existing 10x offsets are converted
to the already tested ChromBPNet interval convention for cut tracks only. Neither
stored fragments nor reads are shifted again. No generic training-readiness claim
is made. Each model's actual loader must read its exported bundle.

Use explicit chromosome folds with full input-window and jitter boundary checks.
Deterministic background tiles provide a transparent initial input contract, not
a claim of optimal GC matching or protection against paralog/homology leakage.
ChromBPNet's plant bias-model requirements remain visible and unresolved when no
validated model is supplied.

## Evidence and source semantics

The [10x fragment specification](https://www.10xgenomics.com/support/software/cell-ranger-atac/latest/analysis/outputs/fragments-file)
defines adjusted BED-like intervals, barcode identity and read-pair support.
Support is not a count of independent molecules. A sixth strand column is retained
when present, and conflicting five-/six-column library merges are rejected.

Model source revisions:

- Cherimoya: `8ecf7f791ec07c05a701076cc58a0f845bf97609`, `cherimoya/io.py`.
- ChromBPNet: `ece97c93ccaa2d9ee5bc5687e62f4dbf8d055367`,
  `chrombpnet/training/data_generators/batchgen_generator.py` and
  `chrombpnet/training/utils/data_utils.py`.

The real Arabidopsis candidate is GSE155304. Author fragment archives and the
integrated RDS are available, but biological label mapping and exact author
reference provenance still require resolution. For Sorghum GSE248919, publicly
listed RData objects and internal fragment paths do not establish an accessible
fragment release. No FASTQ fallback or reference substitution is authorized by
this fragment-first scope.
