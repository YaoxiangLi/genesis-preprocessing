# Historical paired-end ATAC fixture

This directory preserves the frozen prototype for reproducing earlier benchmarks.
For new analyses, use the [supported bulk ATAC guide](../../docs/usage/bulk-atac.md).
The current `genesis pipeline-atac` command runs that supported workflow.

To rerun the historical fixture, use `pixi run validate-atac-legacy --keep`.
Its runner supplies synthetic reads, the toy reference, TSS positions, explicit
MAPQ/duplicate choices and the adapter-free fixture policy.

The fixture path performs per-mate raw FastQC, bwa-mem2 alignment, samtools fixmate/markdup, both-mate MAPQ filtering, marked-duplicate exclusion, organellar exclusion/accounting, fragment generation, explicit +4/-5 cut representation, MACS3 BAMPE peaks, fragment FRiP, a defined toy TSS profile, fragment lengths/NRF/PBC, MultiQC and SHA256 provenance. Original reads/BAM are not altered. Biological thresholds are UNSPECIFIED. The TSS metric is not claimed to be numerically equivalent to ENCODE or ataqv.

`verify_metrics.py` checks exact cut coordinates, asymmetric mate filtering, organellar accounting, duplicate handling, half-open FRiP, NRF/PBC, TSS normalization/strand symmetry and undefined-background behavior. Run it with the project's Python/pysam environment. MultiQC validation requires FastQC and each samtools family, including both mate reports.

Limitations: one synthetic PE library; in-memory read grouping, no optical-duplicate inference, no adapter trimming, no biological replicate aggregation/IDR, no production annotation validator or plant QC cutoffs. FastQC and MultiQC images are local image IDs from the validation build; other images use upstream repository digests. Image publication is a separate deployment step and has not occurred. Use explicit Nextflow session IDs for resume when other workflows share the same launch directory.
