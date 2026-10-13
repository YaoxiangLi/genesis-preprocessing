# Genesis built-in benchmark specification

Approved scope: DAP-seq and experimental PE bulk ATAC; preprocessing evidence; synthetic defaults and curated opt-in public manifests. Implementation branch validation/benchmark, starting e8b37e281b4cace2522179ac7208cfef15cd4dea. Production policy remains unchanged.

The public interface is `pixi run benchmark plan|fetch|run|compare|report`. Versioned TOML experiments reference JSON dataset manifests. Dataset identities, reference sequence hashes, annotations, library/control graphs, input artifact hashes, software/container identities, experiment parameters, metric definitions, budgets and source hashes are explicit. Unknown keys or unsupported combinations fail validation. Missing public references are BLOCKED, not silently replaced.

Evidence levels are synthetic known answers, real-data sensitivity and independent pipeline comparisons. All reports separate those levels. Workflow-native defaults and matched-stage comparisons must remain distinct. Biological replicates never pool implicitly. Templates, read ends, fragments and cut sites have distinct units. Undefined metrics carry null plus a reason. Tool-native metrics retain their original definition; common metrics are independently computed. No universal plant thresholds or composite quality score.

The maintained post-alignment DAP adapter reproduces the prior MAPQ none/10/30 by retained/marked/excluded matrix, preserving caller duplicate policy. Existing raw pipeline commands remain separate whole-workflow adapters with pinned checkouts and isolated Nextflow launch directories. The experimental Genesis ATAC adapter rejects real raw data until that prototype's limitations are addressed. External ATAC and artifact imports can support real data without overstating Genesis readiness.

Metrics: counts/retention/MAPQ, duplicate and organellar accounting, fragment lengths, own/fixed FRiP, peak widths/bases/Jaccard/matched ranks, fixed-region count/normalized-signal correlations and absolute changes, SPP and ATAC TSS definitions, resources and resume evidence. Regions selected from the baseline measure changes, not independent biological accuracy. Real annotations and independent truth are optional separately labelled evidence.

Each task records argv, cwd, source SHA/content, input hashes, versions, stdout/stderr, status, elapsed time and available resource measurements. Fresh runs and stable resumes are distinguished. Cache reuse verifies output content; any scientific input/configuration change receives a new identity. Performance profiles run serially with fixed resource limits and randomized reproducible order, retaining all repetitions and failures. No filesystem-cache flushing or host security changes.

Public pilot: native Arabidopsis GSE60141 FUS3/ABI5 and shared declared control; GSE85203 reported ATAC replicates GSM2260231/GSM2260232. References/metadata must resolve before executable status. Sorghum remains blocked on the exact requested v5.0 reference. Public fetches are explicit, size bounded and checksum verified. Initial per-library pilot cap is one million templates, a compute budget only.

Delivery: (1) manifest/planner/provenance, (2) independent metrics/fixtures, (3) DAP runner, (4) ATAC/reference adapters/report, (5) public manifests/docs. Existing tests/framework/environment are reused. Known-answer tests cover pairing/MAPQ boundaries/duplicates/organelles/half-open intervals/Tn5/undefined values/control fan-out/cache invalidation/missing outputs. Full checks and Docker regression are required. No automatic publication or production-default changes.

## Delivered contract and boundaries

The implementation lives on `validation/benchmark`, with executable examples generated
by `pixi run benchmark fixture`. See `repo/benchmarks/README.md` for the exact supported
fields, metric populations, adapter pins and public-catalog blockers, and
`reports/benchmark-validation.md` for measured acceptance evidence. Raw adapters use
`workflow-configured`: neither untouched native defaults nor policy-matched biology
is implied. Matched-stage post-alignment experiments remain separately labelled.

Randomized repetition order is implemented for post-alignment experiments only; raw
adapters reject it explicitly. The initial real-data catalogs are discoverable blocked
plans rather than runnable downloads: no fabricated SHA256/reference identities are
allowed. Model training, motif accuracy, homoeolog/repeat stratification, biological
replicate agreement and universal plant thresholds are outside the executable v1
metric set. Adding these requires annotated/independent data and explicit adapters.

SPP filtering and scoring have independent cache markers. Nextflow workflow resume
verifies recorded scientific output hashes, in addition to input identity and pinned
source/container checks. Known-answer regression coverage includes command-parameter
inspection, output corruption/missing files, nonzero command log preservation,
TSS strand/edge handling, deterministic paired subsets and comparison-depth guards.
