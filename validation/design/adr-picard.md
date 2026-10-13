# ADR: Picard remains outside the default Genesis workflow

Date: 2026-10-07. Status: evaluation complete; **no implementation approved or performed**. Evaluated Genesis `af0bbfb50806babd78b8e9f88df2a55aab0a2a13`, Picard 3.5.0. Evidence: [audit/06-picard-evaluation.md](../audit/06-picard-evaluation.md).

## Decision

| Candidate | Decision | Reason |
|---|---|---|
| CollectAlignmentSummaryMetrics | **OPTIONAL** | Useful for targeted reference/error/clipping/chimera diagnosis; routine counts duplicate samtools and input filtering hides raw mapping denominator. |
| CollectInsertSizeMetrics | **REJECT** for routine integration | Both PE distributions exactly reproduce existing samtools bins; added median/MAD/PDF does not justify another Java/R pass. Inapplicable to SE. |
| MarkDuplicates-derived metrics | **OPTIONAL**, measurement-only | Adds coordinate/pair redundancy absent from samtools's unpopulated duplicate flags and distinct from per-mate FastQC duplication. No automatic removal. |
| EstimateLibraryComplexity | **DEFER** for PE; **REJECT** for SE | PE estimates depend on sequence ordering/filtering and an unvalidated complexity model for enriched DAP-seq. SE is ignored. |

No candidate is ADOPT for mandatory processing. Biological thresholds are **UNSPECIFIED**. Computational success is not evidence of assay quality.

## Evidence and tradeoffs

Four synthetic libraries cover SE/PE treatment/control; they are not real Sorghum data. All original BAMs and references remained byte-identical. The known-answer SE/PE duplicate fixtures passed. Picard and samtools totals/length/error agree in all four libraries; both PE insert histograms agree at every nonzero bin.

PE treatment had 345 coordinate-duplicate pairs (1.0781%), while per-mate FastQC indicated approximately 18.8–18.9% sequence duplication and samtools reported zero pre-existing duplicate flags. ELC reported 151/31,997 after its ordering/group rules. The difference is informative about definitions, not proof that one number measures PCR duplication correctly. Details and independent reconciliation are in the audit.

Native costs across these small inputs: alignment summary 1.20–2.25 s / 182–311 MiB; insert metrics 1.20–2.29 s / 152–316 MiB (SE yields no result); MarkDuplicates 1.70–2.54 s / 826–1,028 MiB; ELC 1.01–2.15 s / 159–326 MiB. Existing samtools passes took <0.01–0.09 s and 3.5–4.2 MiB. These are warm-cache observations with native timing separate from Pixi startup, not resource prescriptions. MarkDuplicates rereads the BAM and writes a complete marked copy; sorting costs on large samples remain unmeasured.

## Boundary for a future proposal

A future, separately authorized implementation may offer an isolated optional duplicate-metrics task. It must consume the original BAM read-only and keep the production BAM/analysis path unchanged. Any scratch marked copy must explicitly set both `REMOVE_DUPLICATES=false` and `REMOVE_SEQUENCING_DUPLICATES=false`; only metrics would be eligible for publication. Measuring duplication, flagging an experimental copy, and removing duplicates are three separate operations. An adoption of removal requires a separately labeled sensitivity study and decision.

Do not combine independent libraries or infer LB from a convenient sample name. Require declared library provenance for grouping; label unresolvable optical detection unavailable instead of calling its zero a result. Keep MAPQ 0 and other production policies intact. Expose Picard's internal HQ and histogram/sequence filters as metric definitions, not dataset acceptance rules. Preserve raw distributions and warnings; detect empty/inapplicable output independently of exit status.

Before reconsidering mandatory adoption: obtain an authorized exact-reference real DAP-seq subset with SE/PE treatments/controls and declared libraries; test optical naming and nonzero mismatch/chimera cases; measure full-size contig, RAM and spill behavior; compare coordinate redundancy with sequence/UMI evidence where available; establish whether results change an actual scientific decision. No automatic biological cutoff follows from this study.

## Validation and unchanged state

124 recorded commands completed, repeat metric rows were stable, and checksums/record comparisons show no read removal or mutation of source BAMs. SE empty results and optical-name warnings are preserved. One standalone inspection helper error was corrected with its failed log retained. No production code or dependency manifest was changed; no pipeline regression rerun, commit, push, new production process, or MultiQC parser was introduced.
