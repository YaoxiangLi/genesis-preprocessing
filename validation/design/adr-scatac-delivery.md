# Fragment-first scATAC delivery

Status: implemented; two-species computational acceptance passed on 2026-10-11.
Scientific review and training remain open. See the
[completed pilot evidence](../reports/scatac-completion.md).

## Decisions

Reuse the existing cell/pseudobulk contract and registry. Version-4 records retain
inventory snapshots and unreviewed scATAC outputs. Version 5 adds explicit
single-cell assay identities and actual model-loader receipts; earlier schemas
remain intact.
Keep single-cell fragments separate from the DAP-seq and bulk ATAC workflows.

Use disk-backed sorting and joins, BGZF, and tabix through the already locked
pysam dependency. Preserve support counts, source coordinates, library namespaces,
biological replicates and reversible membership. Reject duplicate fragment rows
rather than guessing whether they represent repeated sequencing or independent
molecules. Technical-library merging requires an explicit independent-library
statement; this is not an adapter for resequencing the same molecules.

Keep standalone commands as the first execution interface. Use the existing
immutable MACS3 and track containers. Pseudobulk products enter the existing
artifact validator and metadata/QC/eligibility review gates. Release assembly binds
each model bundle and loader receipt to the current pseudobulk revision. Missing
reviews produce a candidate with `model_ready: false`. Prepared-study scheduling
remains a separate integration; storing an output record is not review approval.

Model export uses separately pinned adapters. Existing 10x offsets are converted
to the already tested ChromBPNet interval convention for cut tracks only. Neither
stored fragments nor reads are shifted again. No generic training-readiness claim
is made. Each model's actual loader must read its exported bundle.

Use explicit chromosome folds with full input-window and jitter boundary checks.
Deterministic background tiles exclude peak bodies and full context windows.
Optional GC matching draws without replacement within each chromosome fold using
declared one-percent bins, nearest-bin fallback and a fixed seed. Matching quality
is reported; it does not protect against paralog/homology leakage.
ChromBPNet's plant bias-model requirements remain visible and unresolved when no
validated model is supplied.

### Background windows for compact plant genomes

The disjoint 2,114 bp tile experiment supplied one background per peak for only
8 of 12 Arabidopsis groups. A 1,000 bp stride supplies enough candidates for all
12, while retaining full positive-context exclusion. The pinned ChromBPNet
[genome-wide GC helper](https://github.com/kundajelab/chrombpnet/blob/ece97c93ccaa2d9ee5bc5687e62f4dbf8d055367/chrombpnet/helpers/make_gc_matched_negatives/get_genomewide_gc_buckets/get_genomewide_gc_bins.py)
explicitly separates window length from stride and defaults to these dimensions.

Expose this as `gc-matched-genome-windows-v1` with an explicit
`background_stride`. Keep the original tile method available with unchanged
semantics. The two-species pilot uses stride 1,000 as a recorded model-preparation
sensitivity choice. It changes background regions only. Selection remains
one-to-one, without replacement, with reported GC deviations. Background contexts
may overlap within a fold; they must never overlap positive contexts or cross
chromosome folds. Such overlapping training windows are correlated examples,
not independent biological observations. This does not resolve homology leakage.

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

The Arabidopsis pilot uses both GSE155304 fragment libraries. Author barcode QC
identifies library membership; published Figure 3C resolves the six cell classes.
TAIR10 is explicit, but byte identity with the authors' original FASTA and their
exact Araport11 release remains unverified. Posthoc TSS annotation is therefore
recorded as a sensitivity choice.

For Sorghum GSE248919, author RData supplies labels and barcode membership but
points to inaccessible local fragment files. The separately recorded raw-read
sensitivity reconstruction uses five public SRA runs, exact v3.0.1 reference files,
paired ATAC/GEX whitelists and pinned Chromap 0.3.2. The ingestion adapter requires
explicit MAPQ, duplicate, trimming, barcode-translation and command provenance.
It performs no second Tn5 shift or duplicate collapse. This is not an assertion of
Cell Ranger equivalence or a change to production raw-read defaults.
