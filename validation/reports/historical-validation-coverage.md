# Historical validation coverage

> Validation record for the revision and date below. Use the
> [current task guides](../../docs/README.md) for a new analysis. Recorded temporary
> paths identify the original test environment.

Baseline: `4468c712e4c171b573e2ec2806fdc5327b5379e9`. This table records
the scope of the original DAP audit and isolated paired-end ATAC prototype. Exact
tested revisions and artifact checksums were recorded in the original workspace
at `results/completion/final-manifest.json`. Later validation appears in the
[validation index](../README.md).

| Component | Status | Acceptance evidence / remaining boundary |
| --- | --- | --- |
| Environment, baseline and cache experiment | COMPLETE | audit/00–04; original failures/warnings retained |
| Exact Sorghum integration | BLOCKED | audit/05; exact `Sbicolor_730_v5.0.softmasked.fa.gz`/manifest absent; no substitute |
| FastQC | LOCALLY VALIDATED | Per-mate reports, unchanged reads/scientific outputs; image deployment separate |
| MultiQC | LOCALLY VALIDATED | Exact required parsed identities and publication; SPP NA handling cleanly deferred |
| Picard | COMPLETE, synthetic scope | audit/06 and ADR; no mandatory adoption or production duplicate removal |
| DAP sensitivity | COMPLETE computationally | Nine policy arms; biological/motif recommendations unresolved |
| Reference ID collision | IMPLEMENTED AND TESTED | Native and real-container rejection before downloads |
| Reference provenance | IMPLEMENTED AND TESTED LOCALLY | Fail-closed cache checks, full checks/Docker/resume, scientific output equality |
| Registry/schema prototype | COMPLETE | Exact synthetic checksums, compressed/uncompressed identity, damaged sizes and ambiguous IDs rejected |
| Bulk ATAC design | COMPLETE | Pinned actual ENCODE/nf-core comparison, explicit decisions and UNSPECIFIED plant thresholds |
| Bulk ATAC prototype | COMPLETE for bounded PE fixture | Known-answer metrics, full checks, actual tool run/resume, successful nf-core differential benchmark |
| scATAC reference audit | COMPLETE | Pinned source, protocol/10x comparison, two reproduced EOF defects; full external pipeline not certified |
| Model-facing pseudobulk contract | COMPLETE, toy formation tests | Actual model code inspected; two reps × three types; production exporter/training outside contract scope |
| Multiome contract | COMPLETE, toy tests | Five barcode cases, metadata retained, independent modality selection |
| Workbook inventory | BLOCKED | Exact input workbook absent; no invented worksheet results |
| Validation synthesis | COMPLETE | [Validation report](GENESIS_PREPROCESSING_VALIDATION.md) |
| Current/animated metro maps | COMPLETE | Native SVG, exact process inventory, browser animation/reduced motion, static fallback |
| Architecture roadmap | COMPLETE | Explicit implemented/experimental/tested-contract/planned labels |

“Complete” here means the bounded audit, specification or prototype was tested within the stated scope, not that Genesis is production-ready for all assays. Scientific defaults remain unchanged in DAP. Real plant datasets, exact references, protocol decisions and deployment are still required for broader acceptance.
