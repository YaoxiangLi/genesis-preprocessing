# Completion ledger

Original upstream: `4468c712e4c171b573e2ec2806fdc5327b5379e9`. Combined DAP work is on `validation/completion`; the PE ATAC prototype is isolated on `validation/bulk-atac-prototype`. Exact final SHAs/status and artifact checksums are in results/completion/final-manifest.json. No automatic merges or container pushes occurred.

| Work | Status | Acceptance evidence / remaining boundary |
| --- | --- | --- |
| A–D environment, baseline, cache experiment | COMPLETE | audit/00–04; original failures/warnings retained |
| E exact Sorghum integration | BLOCKED | audit/05; exact `Sbicolor_730_v5.0.softmasked.fa.gz`/manifest absent; no substitute |
| F FastQC | LOCALLY VALIDATED | Per-mate reports, unchanged reads/scientific outputs; image deployment separate |
| G MultiQC | LOCALLY VALIDATED | Exact required parsed identities and publication; SPP NA handling cleanly deferred |
| H Picard | COMPLETE, synthetic scope | audit/06 and ADR; no mandatory adoption or production duplicate removal |
| I DAP sensitivity | COMPLETE computationally | Nine policy arms; biological/motif recommendations unresolved |
| Reference ID collision | IMPLEMENTED AND TESTED | Native and real-container rejection before downloads; issue/PR pair #9/#10 |
| Reference provenance | IMPLEMENTED AND TESTED LOCALLY | Fail-closed cache checks, full checks/Docker/resume, scientific output equality |
| O registry/schema prototype | COMPLETE | Exact synthetic checksums, compressed/uncompressed identity, damaged sizes and ambiguous IDs rejected |
| J bulk ATAC design | COMPLETE | Pinned actual ENCODE/nf-core comparison, explicit decisions and UNSPECIFIED plant thresholds |
| K isolated bulk ATAC prototype | COMPLETE for bounded PE fixture | Known-answer metrics, full checks, actual tool run/resume, successful nf-core differential benchmark |
| L scATAC reference audit | COMPLETE | Pinned source, protocol/10x comparison, two reproduced EOF defects; full external pipeline not certified |
| M model-facing pseudobulk contract | COMPLETE, toy formation tests | Actual model code inspected; two reps × three types; production exporter/training outside contract scope |
| N multiome contract | COMPLETE, toy tests | Five barcode cases, metadata retained, independent modality selection |
| P workbook inventory | BLOCKED | Exact input workbook absent; no invented worksheet results |
| Q synthesis | COMPLETE | GENESIS_PREPROCESSING_VALIDATION.md; questions-for-ted-draft.md remains unsent |
| Current/animated metro maps | COMPLETE | Native SVG, exact process inventory, browser animation/reduced motion, static fallback |
| Architecture roadmap | COMPLETE | Explicit implemented/experimental/tested-contract/planned labels |
| Incremental publication | PACED QUEUE ACTIVE | Five pairs published; sixth validated and scheduled ≥2 h later; integration/deployment remains separate |

“Complete” here means the requested bounded audit, specification or prototype was delivered, not that Genesis is production-ready for all assays. Scientific defaults remain unchanged in DAP. Real plant datasets, exact references, protocol decisions and deployment are still required for broader acceptance.
