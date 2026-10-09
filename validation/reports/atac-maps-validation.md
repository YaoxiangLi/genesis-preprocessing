# ATAC integration and workflow-map validation

Date: 2026-10-09. Base fork commit: `003c9457161d9588421074f37b50bea6050daf45`. Original ATAC prototype: `0b8850207e94a3d4909bf4ab99d18c03cd010cc2`.

## Scope and implementation

Integrated the existing synthetic PE prototype under `experimental/atac/`, exposed `pixi run pipeline-atac --help` and `pixi run validate-atac --keep`, and added focused ATAC and map checks to `pixi run checks`. The ATAC scientific workflow, metrics, enrichment and Nextflow settings are byte-identical to the original prototype. DAP workflow modules and both dependency lock files are unchanged.

Five SVGs now use larger labels, clear route corridors, selectable text, accessibility titles/descriptions, light/dark palettes and reduced-motion support. DAP and ATAC fingerprints identify their own workflow source. The architecture map distinguishes available experimental ATAC from planned single-cell processing.

## Commands, observations and acceptance

Full stdout/stderr, command, tested SHA, tracked-input checksums, exit status, elapsed time and GNU time measurements are retained under workspace `results/incremental-prs/<label>/`. Container process resources are separately recorded in Nextflow traces; GNU time launcher RSS is not aggregate container RAM.

| Label | Command | SHA | Exit | Wall seconds | Peak launcher RSS (KiB) |
| --- | --- | --- | ---: | ---: | ---: |
| atac-maps-checks-1 | `pixi run checks` | `cb3ea94f27c30de0632e71892b22dd89b375a1fe` | 0 | 89.81 | 704600 |
| atac-maps-checks-final | `pixi run checks` | `32c23884393d689f85997e33e81b8cae1f129f83` | 0 | 90.79 | 679424 |
| atac-maps-atac-1 | `pixi run validate-atac --keep` | `cb3ea94f27c30de0632e71892b22dd89b375a1fe` | 1 | 37.22 | 570672 |
| atac-maps-atac-2 | `pixi run validate-atac --keep` | `32c23884393d689f85997e33e81b8cae1f129f83` | 0 | 48.04 | 573836 |
| atac-maps-dap-docker | `pixi run validate-docker --keep` | `32c23884393d689f85997e33e81b8cae1f129f83` | 1 | 221.45 | 670580 |
| atac-maps-dap-docker-frozen | `pixi run validate-docker --keep` | `47aa6a16e9c3b4114cbec19efb03e4a00ca5f9e1` | 0 | 321.54 | 700852 |

The first ATAC invocation completed eight tasks but its new output checker expected organelles in noncanonical order. The explicit expectation was corrected to mitochondria, plastid; no membership assertion was removed. The second invocation passes all eight fresh tasks and all eight cached tasks. Every published file and raw input checksum remains identical across resume.

The first DAP validation failed the stable-resume MultiQC cache assertion because documentation edits changed run provenance from clean to dirty during execution. Comparing the two MultiQC command scripts isolates that difference. The failure is retained; the pipeline correctly invalidated changed provenance. A frozen-checkout full rerun follows below.

## ATAC output inspection

The deterministic fixture yields 31,557 usable fragments, 63,114 cut counts and 200 nonempty peaks. Fragment FRiP is 29,669 / 31,557 = 0.9401717527014608. NRF is 0.986248710816639; PBC1 is 0.9862154197167031; PBC2 is 72.37674418604651. These are synthetic observations, not biological acceptance thresholds.

BED and JSON fragments agree exactly, cut counts match independently computed endpoints, and FastQC contains two HTML/ZIP report pairs. MultiQC retains machine-readable data with FastQC, samtools flagstat, stats and idxstats; both mates and both raw/usable samtools groups are required. FASTQs and BAMs are not published. The fresh trace observed peak task RSS up to 234.4 MB (REPORT); short-task sampling may miss true peaks. Retained ATAC fixture/run uses approximately 45 MiB.

Against retained `results/benchmarks/atac-final`, all nine scientific published files and all five intermediate BAMs are byte-identical. Comparisons are in `results/atac-maps/atac-scientific-comparison.json`. Provenance/report timestamps and the integration SHA are not scientific-equivalence targets.

## Warnings and limits

FastQC reports FAIL for per-base and per-sequence quality, and WARN for duplication, on both synthetic mates. Adapter content passes. These diagnostic flags remain visible and do not fail the dataset. TSS enrichment is null because the fixture has zero background at its toy TSS sites; it is not replaced by zero or called biological failure. No ATAC Nextflow/task warning was found in the inspected run logs.

Real plant biological performance remains unresolved. The prototype uses one synthetic PE library, in-memory fragment grouping, a toy TSS definition, a combined post-MAPQ organellar counter and fixed duplicate exclusion. No trimming, production-scale multi-library input, replicate pooling/IDR, optical duplicate inference or sc/snATAC processing is introduced. Plant thresholds remain UNSPECIFIED. Exact FastQC/MultiQC local image IDs are required on this host and have not been published as portable registry images.

ENCODE and primary plant studies informed the documented boundaries in `experimental/atac/plant-methods.md`; they did not silently change scientific parameters.

## Visual checks

Command: `python scratch/check_integrated_maps.py`, using Firefox 157.0.1. DAP, ATAC and architecture maps were rendered at 980 px light and 1480 px dark. Browser geometry checks found no route/text intersections or clipped labels. Animated dash offsets advance; reduced-motion hides markers. All final images were visually inspected. Static and animated route geometry is tested for identity, and all imported DAP process IDs and all seven ATAC process IDs are represented.

The initial geometry check caught an upper DAP route intersecting text bounds. Moving it above the labels fixed the issue; the zero-intersection assertion was preserved. Screenshots and first/final browser observations remain in `results/atac-maps/`. Browser timing and peak RAM were not measured. Headless Firefox logs include a software-framebuffer warning and channel errors when the probe browser is intentionally terminated after returning its results; separate screenshot commands exit zero and their images were inspected.

## Versions and immutable images

Pixi 0.70.1; Nextflow 25.10.4 build 11173; Java 23.0.2-internal; micromamba 2.5.0; uv 0.11.33; Docker 29.1.3; Python 3.14.5; bwa-mem2 2.2.1; samtools/HTSlib 1.24; MACS3 3.0.5; FastQC 0.12.1; MultiQC 1.35. Containers are Linux amd64; exact inspection results are in `results/atac-maps/versions.json`.

- `kundajelab/dap_seq_alignment@sha256:4764008ba8fbb5d831bd6f9ed6a720fd494062b39f0bae63ff2e4efd316ad842`
- `kundajelab/dap_seq_peaks@sha256:10467dd29e3d25ce7769f76f57402bd1a5a582006e911d06479bfcc3e3325df3`
- `kundajelab/genesis_tools@sha256:31458d4a6a83541f463ea4b0e692a0afc65c6df441f70c3f71fc4ccf1a11eb59`
- `sha256:3f8fc8c57e57994b95408cd02a7ced44a6fb90396b9067bbe2d2dcdebb396b50`
- `sha256:97ca1e181a55a1d87653984956983fea3ff76cab5875f45ae2143168ff4fd73d`

Lock checksums (unchanged):
- `pixi.lock`: `874cbf7d41658470853868c86e5b6d4f2734b85a47b1973f9bb8e78833a7047c`
- `genesis_tools/uv.lock`: `1132c51537ac229ce768fcf0edde8475a970be017cef82c0d46601b228f998f5`

ATAC input SHA256 (the fixture manifest includes all other executable inputs):
- `pe_treatment.R1.fastq.gz`: `9b7b3bc5de8b58d9d2d28ee487646b8f8b3e518f0dd55cce965b89d1910df2d3`
- `genes.bed`: `a3520307536c485f1a5304bd81192f88e98bfdf6af8d0826845747d11cc5243d`
- `pe_treatment.R2.fastq.gz`: `52a535a59b2b228505d13a5e9e4d0bdd641acb2dd8c059e45a587197bb98741b`
- `tss.bed`: `54088833e05fead8ad3eeeffc4d80af7fb4c52bf77f409d6633ac81d04be7411`
- `reference.fa.gz`: `01ad9491498f7844310ed8cf8537aade2981c1bb665ce9eedcfa8df392e7790b`


## Frozen DAP regression and final acceptance

The frozen full Docker rerun passes, including SE/PE, shared controls, reference
provenance failures, empty/corrupt downloads, FastQC malformed-input behavior,
MultiQC missing-module/collision checks and publication boundaries. Fresh run:
42 completed tasks. First resume: 10 cached, 28 completed as generated reference
paths become available. Stable resume: 37 cached; only deliberate input validation
runs again. The initial Nextflow warning that no prior run exists and resume is
ignored remains recorded in the first-run log.

All 15 alignment BAMs match the retained upstream baseline byte-for-byte.
All 99 scientific published files are equivalent: 91 byte-identical; eight differ
only in gzip headers or PDF CreationDate/ModDate fields, whose payloads are compared
explicitly. All ten raw FASTQ payloads match. Comparisons are recorded in
`results/atac-maps/dap-scientific-comparison.json`; the earlier attempt is preserved
separately. Commands: `repo/genesis_tools/.venv/bin/python scratch/compare_integrated_dap.py repo/tests/.runs/docker-msyvhe5z`
and `python scratch/compare_integrated_atac.py`. Comparison timing/RAM were not measured.

Final functional and visual acceptance: **PASS within the documented synthetic
prototype scope**. No production biological policy changed. No failed final check
remains. Biological validity on representative real plant ATAC remains unresolved.
The executable candidate was frozen at
`47aa6a16e9c3b4114cbec19efb03e4a00ca5f9e1`;
subsequent changes only add this validation evidence. Diagram source was visually
checked after `3c7f2017da56fed7d1eb5c27c826c34e7721e376`.

## Files changed

- `experimental/atac/*`: preserved prototype, parameterized output verifier and plant-method boundary documentation.
- `scripts/run-atac-prototype.sh`, `pixi.toml`: explicit experimental entry point and validation task.
- `tests/verify_atac.py`, `tests/verify_metro.py`, `scripts/check-projects.sh`: regression coverage.
- `docs/diagrams/*`, five `docs/images/genesis*metro_map*.svg` files: deterministic map generator and assets.
- `README.md`, `benchmarks/README.md`, `validation/README.md`: usage and status.
- `validation/reports/atac-maps-validation.md`, `validation/snapshot.json`: this evidence and additive provenance.

No workflow source, lock file, image, credential or security-setting changes were
needed in the existing DAP path. No container images were published.
