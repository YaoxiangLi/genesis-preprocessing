# Built-in plant preprocessing benchmark validation

Date: 2026-10-09. Branch: `validation/benchmark`. Starting production revision:
`e8b37e281b4cace2522179ac7208cfef15cd4dea`. This is an opt-in experiment layer;
no production Nextflow module, pipeline configuration, dependency lock or scientific
default changed. See [design](../design/benchmark-spec.md) and
[usage/contracts](../../benchmarks/README.md).

## Scope and evidence

The release supports explicit post-alignment DAP sensitivity matrices, an external
pinned synthetic Genesis PE ATAC prototype, and configured nf-core/atacseq 2.1.2.
It does not turn the prototype into a production plant ATAC workflow. Public
Arabidopsis candidates are curated but blocked pending exact reference/input and
replicate identities. No real FASTQs or substitute genome were downloaded.

Implemented CLI: `pixi run benchmark fixture|plan|fetch|run|compare|report`.
The JSON/TOML contract pins inputs, references, annotations, library/control graphs,
parameters, containers, resources and source recipes. Every supported scientific
parameter is explicit. Unsupported options fail instead of being silently ignored.
Reports retain units/denominators, undefined-value reasons, native metrics,
distributions, all-library QC, command evidence and a standalone interactive HTML.
No biological pass threshold or composite score is invented.

## Observations

The expanded deterministic DAP fixture has SE and PE, three treatments, two controls,
one shared control, intermediate MAPQ classes, organellar contigs and injected
duplicate flags. All nine arms produce 200 peaks for each treatment. Retained
fragments per treatment are 32,000 / 31,900 / 31,800 for no cutoff / MAPQ10 / MAPQ30;
duplicate-excluded counts are 29,091 / 29,001 / 28,909. Marking while retaining reads
preserves fixed-region counts and peak intervals. These are computational checks,
not evidence favoring a biological filtering policy. Stable resume reuses 127 stages.

The Genesis raw ATAC run executes eight tasks and caches all eight on stable resume.
The configured nf-core run executes 38 tasks; stable resume caches 35. Sample-sheet
validation, software-version aggregation and MultiQC rerun. The adapter rewrites its
sample sheet and metadata includes run-dependent values; these three reruns are
recorded rather than counted as fully cached. Scientific BAM/peak bytes and common
metrics stay identical; MultiQC JSON changes. Both workflows have two distinct
FastQC mates and all four required parsed QC families. Executed commands are checked
for peak format, duplicate setting, q-value, narrow/broad mode and nf-core MAPQ.

Cross-workflow scoring on identical reads/reference yields 200 peaks and peak-base
Jaccard 1.0 on this fixture. nf-core retains 31,557 fragments with fixed-peak fragment
FRiP 0.94017. Common metric definitions make this comparison interpretable, but
filtering and callers still differ; identical synthetic peaks do not establish
methodological equivalence. The capped Genesis ATAC run selects exactly 8,000 paired
templates and passes. Comparing it against the full-depth campaign is rejected.

The original production pipeline regression is separate from this sensitivity study.
Independent comparison found all 15 BAMs byte-identical to the original baseline;
91 of 99 published scientific files were byte-identical. The remaining eight match
under the previously defined gzip-payload or PDF-timestamp comparisons. Ten raw FASTQ
payloads match. No biological output regression was found.

## Defects, warnings and failure evidence

A new failing regression test reproduced a benchmark cache defect: SPP filtering
and SPP scoring shared a task marker. The remedy separates their output/cache
directories; it does not change input reads, SPP commands or numerical definitions.
The fixed five-library/three-treatment run reused all 25 stages on resume, with
zero tool reruns and unchanged outputs. All 135 peak/quantification files from the
full retained matrix matched the prior study byte-for-byte; all 45 SPP NSC/RSC/fragment
length results matched.

Raw-workflow resume also checks recorded scientific output hashes before trusting
Nextflow's existence-based cache. Successful invocation history is preserved across failed retries, preventing a second
retry from bypassing the check. Altered products fail closed and require a fresh
campaign directory. Native-default or parameter-matched labels are not accepted
for the initial explicitly configured raw adapters.

Full stdout/stderr is preserved, including MACS warnings about the synthetic SE
fragment model, SPP/R package messages, Matplotlib's fallback temporary cache warning,
and Nextflow's newer-version notice. No model parameters were changed to silence
warnings. Host-version probing outside Pixi initially missed project executables;
the corrected project-environment probe records actual resolved versions. Formatting
and typing failures during development and the intentional SPP-cache regression
failure remain in the evidence directories; assertions were not weakened.

## Scientific limits and follow-up

Plant QC thresholds remain **UNSPECIFIED**. There is no real-data policy recommendation
from these synthetic runs. Motif validation, polyploid/homoeolog assignment accuracy,
mappability/repeat stratification, library complexity estimation and biological
replicate concordance need appropriate data/annotations and separate metric adapters.
No model training or scATAC benchmark is claimed by this release.

The GSE60141 panel selects FUS3, ABI5 and a shared bead control. ENA identifies the
control's source run SRR2926068 as paired-end, while the existing repository manifest
uses R1 only. That projection is recorded explicitly and must be resolved before a
real campaign. GSE85203 has two reported replicate candidates; accession and label
alone do not establish biological replicate identity. Exact TAIR10 FASTA/annotation
bytes and SHA256s remain unresolved. Sorghum's exact reference remains a separate
blocker. Public catalog plans and fetches reject these unresolved conditions.

Initial workflow support is BWA only for nf-core, configured without trimming;
Genesis raw ATAC is synthetic only. Image locks include immutable local QC image IDs,
which require those exact images or verified exports on another machine. No registry
publication was performed. Public acquisition is implemented only for fully pinned
READY manifests; the blocked catalog was not downloaded.

## Reproducibility and resource interpretation

Each campaign contains resolved `experiment.json`, input and recipe SHA256s,
`invocations/`, complete `commands/*/attempt-*` logs, resource records, tool versions,
artifacts and metric definitions. Top-level validation command receipts include
argv, cwd, UTC, source SHA, tracked-source hashes, GNU time and exit status under
`results/incremental-prs/benchmark-*`. Early runs record dirty source hashes rather
than falsely claiming a clean committed revision; later commits preserve those
bytes except for the separately tested cache hardening.

Validation jobs partly overlap on this shared host. Their durations are resource
observations, **not controlled performance rankings**. Container memory includes
page cache; host wrapper RSS is separate. No cold-cache claim or OS cache flushing
is made. For performance studies use serial repetitions with declared CPU/memory
budgets and record host load; randomized order is supported for post-alignment
campaigns and explicitly rejected by current raw-workflow adapters.

Exact environment: Pixi 0.70.1, Nextflow 25.10.4 build 11173, OpenJDK 23.0.2,
uv 0.11.33, micromamba 2.5.0, Docker 29.1.3, x86_64/amd64, project Python 3.14.5,
pysam 0.24.1 / HTSlib 1.24. Full digest mappings are in committed
`benchmarks/locks/` and each campaign's `results.json`; post-alignment image digests
are in the resolved manifest. Both dependency lock files remain unchanged. MACS3 is 3.0.5, bamCoverage/deepTools
is 3.5.6, R is 4.4.3 and spp is 1.16.0. External workflow native software-version
files and per-task execution scripts are retained with the Nextflow traces.


## Files and local contributions

Production workflow code and scientific defaults are unchanged. Added modules are
under `repo/genesis_tools/src/genesis_tools/benchmark/`; offline tests are
`tests/verify_benchmark.py` and `tests/verify_benchmark_spec.py`. `pixi.toml` adds
the opt-in task, `scripts/check-projects.sh` includes the tests and shell lint, and
`genesis_tools/pyproject.toml` packages the HTML template without adding dependencies.
`benchmarks/` contains the SPP driver, immutable workflow container locks, blocked
public manifests, official metadata snapshots and user documentation. README links
to those contracts. Workspace evidence is under `results/benchmarks/` and
`results/incremental-prs/benchmark-*`. No generated BAMs or FASTQs were committed.

Local commits use the configured Yaoxiang Li identity. Nothing was pushed and no
issue/PR publishing queue was changed by this implementation.

Evidence links: [content inspection](../results/benchmarks/inspection.json),
[retained-study comparisons](../results/benchmarks/retained-comparisons.json),
[SPP comparisons](../results/benchmarks/retained-spp-comparison.json),
[cache acceptance](../results/benchmarks/final-cache-acceptance.json),
[production-output comparison](../results/benchmarks/production-scientific-comparison.json),
[browser checks](../results/benchmarks/browser.json),
[interactive DAP report](../results/benchmarks/dap-final/report.html),
[interactive ATAC report](../results/benchmarks/atac-hardened/report.html).

## Recorded validation commands

Durations include wrappers; peak RSS is host maximum RSS, not aggregate container
memory. Every linked directory contains the exact command, source hashes, complete
stdout/stderr, exit status and GNU time output.

| Validation | Exit | Wall s | Host peak RSS KiB | Evidence |
| --- | ---: | ---: | ---: | --- |
| full-checks-2 | 0 | 83.78 | 696920 | [logs](../results/incremental-prs/benchmark-full-checks-2/run.json) |
| docker-regression | 0 | 329.68 | 687736 | [logs](../results/incremental-prs/benchmark-docker-regression/run.json) |
| dap-final | 0 | 239.82 | 55152 | [logs](../results/incremental-prs/benchmark-dap-final/run.json) |
| dap-resume | 0 | 5.01 | 52560 | [logs](../results/incremental-prs/benchmark-dap-resume/run.json) |
| retained-study | 0 | 388.33 | 55468 | [logs](../results/incremental-prs/benchmark-retained-study/run.json) |
| retained-comparison | 0 | 0.15 | 29476 | [logs](../results/incremental-prs/benchmark-retained-comparison/run.json) |
| atac-final | 0 | 30.35 | 576564 | [logs](../results/incremental-prs/benchmark-atac-final/run.json) |
| atac-resume | 0 | 7.37 | 524804 | [logs](../results/incremental-prs/benchmark-atac-resume/run.json) |
| nfcore-final | 0 | 113.20 | 1358404 | [logs](../results/incremental-prs/benchmark-nfcore-final/run.json) |
| nfcore-resume | 0 | 45.73 | 1612608 | [logs](../results/incremental-prs/benchmark-nfcore-resume/run.json) |
| workflow-compare | 0 | 1.71 | 53388 | [logs](../results/incremental-prs/benchmark-workflow-compare/run.json) |
| atac-cap | 0 | 28.05 | 570660 | [logs](../results/incremental-prs/benchmark-atac-cap/run.json) |
| atac-cap-resume | 0 | 6.23 | 470920 | [logs](../results/incremental-prs/benchmark-atac-cap-resume/run.json) |
| html-browser | 0 | 3.52 | 343460 | [logs](../results/incremental-prs/benchmark-html-browser/run.json) |
| spp-cache-reproduction | 1 | 0.52 | 36112 | [logs](../results/incremental-prs/benchmark-spp-cache-reproduction/run.json) |
| spp-cache-fixed-run | 0 | 50.97 | 54520 | [logs](../results/incremental-prs/benchmark-spp-cache-fixed-run/run.json) |
| spp-cache-fixed-resume | 0 | 7.19 | 54628 | [logs](../results/incremental-prs/benchmark-spp-cache-fixed-resume/run.json) |
| workflow-hardened-run | 0 | 30.58 | 507428 | [logs](../results/incremental-prs/benchmark-workflow-hardened-run/run.json) |
| workflow-hardened-resume | 0 | 7.50 | 487636 | [logs](../results/incremental-prs/benchmark-workflow-hardened-resume/run.json) |
| workflow-history-check | 0 | 0.21 | 35240 | [logs](../results/incremental-prs/benchmark-workflow-history-check/run.json) |
| cache-acceptance | 0 | 0.04 | 13148 | [logs](../results/incremental-prs/benchmark-cache-acceptance/run.json) |
| public-blocker | 2 | 0.18 | 35240 | [logs](../results/incremental-prs/benchmark-public-blocker/run.json) |
| reject-different-depth | 2 | 0.20 | 34984 | [logs](../results/incremental-prs/benchmark-reject-different-depth/run.json) |

Exit 1 for the SPP cache reproduction is the intentionally failing pre-fix assertion.
Exit 2 for the public plan and unequal-depth comparison is required rejection behavior.
These are not successful dataset analyses. A scratch acceptance probe initially
guessed 49 cached stages for the one-arm SPP run; enumeration of the implemented DAG
shows 25 (one version stage, three stages × five libraries, three stages × three
treatments). The saved acceptance script checks that derivation and zero tool reruns.

## Final acceptance

Final local SHA: `a93c59cd4ed7daeb99dcbca8fe783704e06746f3`. Git working tree is clean. Full final
`pixi run checks` passed in 84.09 seconds; [final command receipt](../results/incremental-prs/benchmark-final-checks-3/run.json).
Docker real-tool regression passed in 329.68 seconds. Final cache-only changes
were subsequently verified with the full checks, real SPP and ATAC fresh/resume
runs, and successful/corrupt invocation-history tests. Production modules and both
dependency lock files remain byte-identical to the starting revision.

PASS: nine-arm sensitivity execution, known-answer metrics, prior-study reproduction,
raw ATAC/reference adapters, per-mate and parsed QC contracts, fixed-region comparison,
resource/log recording, bounded paired subsampling, cache integrity, standalone HTML
browser behavior, complete regression suite, and production-output preservation.

BLOCKED: executable public plant panel, pending exact reference/input checksums and
metadata decisions. UNRESOLVED: biological superiority of policies; no conclusion
is inferred from synthetic success. Deferred metric domains are explicitly listed
above. No production scientific setting changed and nothing was pushed.

[Final repository state and complete changed-file inventory](../results/benchmarks/final-repository-state.json).

Local commits:

- `a93c59cd4ed7daeb99dcbca8fe783704e06746f3 Yaoxiang Li <liyaoxiang@outlook.com> Separate SPP caches and verify workflow output history on resume`
- `5db3cadeeca47e1b1e196b3b76294dcb88ede9fa Yaoxiang Li <liyaoxiang@outlook.com> Document benchmark contracts and curate blocked Arabidopsis pilot manifests`
- `089775f7a8b363722ab02cc50d635046992a2dec Yaoxiang Li <liyaoxiang@outlook.com> Run isolated sensitivity and pinned workflow benchmarks with common metrics`
- `09d1456603d1048aef358c6d46c731c678d944ba Yaoxiang Li <liyaoxiang@outlook.com> Add independently tested fragment metrics and deterministic paired subsampling`
- `80bee414feb42bc6a44a509f87db94a0333e1d6d Yaoxiang Li <liyaoxiang@outlook.com> Validate benchmark manifests and record content-addressed execution evidence`
