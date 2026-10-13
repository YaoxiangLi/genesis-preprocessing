# MultiQC implementation and validation

Date: 2026-10-07. Branch: `validation/multiqc`.
Parent/FastQC commit: `430cfe31aab5fb9638d18c75a087a9bcb7a868c5`.
Unmodified scientific baseline: `4468c712e4c171b573e2ec2806fdc5327b5379e9`.
Final local commit: `af0bbfb50806babd78b8e9f88df2a55aab0a2a13` (clean working tree; nothing pushed).
Design was recorded before implementation: [ADR](../design/adr-multiqc.md).

## Result

PASS for the deterministic synthetic SE/PE validation scope. Exactly one MULTIQC
process consumes collected FASTQC, QC and METADATA channels. It publishes
`output/multiqc/multiqc_report.html` and complete `multiqc_data/` under the run
folder. Publication does not start until its explicit parsed-data contract passes.
No alignment, read processing, reference, peak, quantification or existing QC module
changed. All 33 inspected pre-existing modules and dependency/environment files
remain byte-identical to the parent commit.

Reports include native FastQC, samtools flagstat, stats and idxstats; both main and
read1 stats remain separate. Genesis custom content adds species, reference ID,
layout and control associations. Header/provenance include the logical run name,
Git SHA, tracked-source dirty/clean status and pipeline version 0.1.0. Git-unavailable
runs report UNKNOWN rather than inventing a revision. Validation ran on the parent
SHA with explicitly recorded dirty source hashes; the committed source was verified
against those tested hashes after committing.

## Native-recognition investigation: observations before configuration

Pinned MultiQC 1.35 parser and search-pattern source snapshots/checksums are in
`scratch/multiqc/parser-source/` and `parser-source.json`. A stock parser probe ran
against retained real-tool Genesis outputs, without changing them.

| Existing Genesis files | Native support | Stock probe / concern | Implemented handling |
| --- | --- | --- | --- |
| `*.read[12]_fastqc.zip` | FastQC ZIP search; internal Filename determines identity | 7 reports detected | Require 7 expected mate identities; validate internal Filename before parsing. |
| `*_fastqc.html` | Not the selected FastQC data source | HTML alone is insufficient here | Preserve original HTML publication; aggregate ZIP once per mate. |
| `*.qc.report.flagstat.txt` | samtools producer text | 5 reports | Required for each library, exact parsed identity set. |
| `*.qc.report.main.stats.txt` and `.read1.stats.txt` | samtools stats producer header | **Only 5 of 10 reports retained** after default name cleaning, despite exit 0 | Disable broad name cleaning; require all 10 full identifiers and numerical read counts. |
| `*.qc.report.idxstats.tsv` | Native filename contains `idxstat` | 5 reports | Required for each library; preserve parsed mapped counts/reference lengths. Original TSV also retains unmapped counts. |
| `*.qc.report.spp.tsv` | Native phantompeakqualtools exists; default searches `*.spp.out` | No SPP detected by default. Real-name search override handles numeric rows but fails on NA fragment length | Explicitly deferred; original per-library SPP TSV/PDF retained. |
| SPP PDF, `*.insert_lengths.tsv` | Not consumed by selected native parsers | Optional companions | Not required by aggregation; PE insert-size metrics already exist in main stats. |
| `*.metadata.tsv` | No Genesis-native parser | Not detected as Genesis metadata | Supported custom-content table, clearly labelled Genesis. |

The stock probe exits zero after losing half the samtools stats entries. Its raw
parsed data and source mapping are in `results/multiqc/native-probe/multiqc_data/`.
This is direct evidence that file counts and tool exit status alone are inadequate.
[Native samtools support](https://docs.seqera.io/multiqc/modules/samtools),
[versioned parser/search source](https://github.com/MultiQC/MultiQC/tree/v1.35/multiqc).

The SPP numeric probe exits 0; a separate synthetic NA-injected row causes native
SPP aggregation to exit 1 with `ValueError: invalid literal for int() ... 'NA'`.
Logs are `spp-numeric.*` and `spp-na.*`. Only copied synthetic QC reports under
scratch/ were altered. No filename was changed to impersonate another tool.
[SPP parser](https://github.com/MultiQC/MultiQC/blob/v1.35/multiqc/modules/phantompeakqualtools/phantompeakqualtools.py).

Custom-content support could preserve SPP NA values explicitly, but defining a
Genesis SPP schema is deferred cleanly. Native SPP also brings ChIP-oriented
presentation defaults that are not established plant DAP-seq acceptance criteria.
The report comment and provenance state the deferral; original SPP remains visible
outside the aggregate. [Supported custom-content format](https://docs.seqera.io/multiqc/custom_content).

## Implementation and collision contract

`multiqc_config.yaml` commits module selection, preserved full names, JSON/raw-data
export, reproducible display options and an explicit SPP notice. MultiQC uses a
new isolated YAML/Pixi lock/container, leaving both R/SPP and FastQC environments
unchanged. The Python aggregation driver uses the standard library and the pinned
MultiQC executable; no new test framework or host pip installation was introduced.

Preflight rejects duplicate input basenames, duplicate sample IDs, missing required
reports, inconsistent metadata identities and mismatched FastQC internal filenames.
Only expected reports are copied into a deterministic scan directory, with original
filenames and bytes. After parsing, exact expected sample sets are required in all
four `report_saved_raw_data` keys. Genesis metadata sample coverage is checked too.
A missing parser, dropped mate, or merged stats entry fails the task even if native
MultiQC exited zero. Dataset quality flags never determine task acceptance.

Full filenames intentionally distinguish raw mates, main BAM statistics and read1
statistics; they are not implicitly merged into a single statistical population.
The original sample-sheet contract already rejects duplicate sample IDs globally.
Report input checks enforce that invariant again rather than trusting a dict merge.

Machine-readable native JSON, parquet, plot exports, sources, citations, logs and
software versions are retained. Additional `genesis_fastqc.json`,
`genesis_stats.json`, `genesis_flagstat.json`, `genesis_idxstats.json`, custom metadata,
config copy and `genesis_provenance.json` make identities/metrics explicit. Provenance
records required QC input SHA256s, expected identities, run/source metadata, config
and driver hashes and HTML canonicalization hashes.

## Tests and commands

From repo/:

```bash
pixi run checks
pixi run validate-docker --keep
# Focused real-tool cases, using retained synthetic QC inputs:
pixi run uv run --frozen --project genesis_tools python tests/verify_multiqc.py \
  --source ../scratch/multiqc/configured-probe/inputs \
  --manifest ../scratch/multiqc/configured-probe/manifest.json \
  --work ../results/multiqc/focused-deterministic
```

The complete default suite includes ShellCheck, Ruff, ty, quantification/build
regressions, the new dependency-free MultiQC guard/determinism tests and Nextflow
SE/PE stub workflows with invalid-input and resume tests. Docker validation retains
the prior FastQC, BAM, peak, quantification and publication assertions, adds actual
MultiQC section/sample/count checks, and runs eight focused aggregation cases.

| Task | Exit | Wall seconds | Maximum host RSS (KiB) | Evidence prefix |
| --- | --- | --- | --- | --- |
| environment-lock | 0 | 2.110 | 441240 | `results/multiqc/environment-lock.*` |
| image-build | 0 | 48.734 | 56604 | `results/multiqc/image-build.*` |
| native-probe | 0 | 5.831 | 28180 | `results/multiqc/native-probe.*` |
| focused-deterministic | 0 | 34.641 | 34140 | `results/multiqc/focused-deterministic.*` |
| checks-deterministic | 0 | 53.616 | 669284 | `results/multiqc/checks-deterministic.*` |
| docker-final | 0 | 294.918 | 663172 | `results/multiqc/docker-final.*` |
| scientific-comparison-final | 0 | 1.506 | 106876 | `results/multiqc/scientific-comparison-final.*` |

Each evidence prefix has exact argv/cwd, UTC time, Git SHA and tested source hashes
in `.json`, complete stdout/stderr separately, and `/usr/bin/time -v` in `.time`.
Host RSS does not measure aggregate container memory. Nextflow traces show MULTIQC
at about 8.0 seconds / 265.9 MB peak RSS initially and 7.8 seconds / 283.1 MB on the
first resume. These are small-fixture measurements, not large-study resource limits.

| Scenario | Observed result | Acceptance |
| --- | --- | --- |
| Initial mixed SE/PE workflow | 42 tasks COMPLETED, exactly one MULTIQC | PASS |
| First resume | 38 tasks: 10 CACHED, 28 COMPLETED, including MULTIQC | Expected reference-path transition; same baseline behavior plus aggregation. |
| Stable resume | All 38 CACHED; complete report/data hashes unchanged | PASS |
| Native module/sample coverage | 7 FastQC, 10 stats, 5 flagstat, 5 idxstats, 5 metadata | PASS; HTML section anchors also present. |
| Known read counts | SE/control/treatment and PE main/read1 counts checked numerically | PASS |
| Shared control | se_treatment and se_second both point to se_control; control appears once as a library | PASS |
| One optional SPP file absent | Aggregation succeeds; required metric exports identical | PASS |
| collision / collision.bam / collision.report | Three distinct samples, six distinct stats entries | PASS |
| Exact duplicate sample ID | Rejected before native aggregation | Expected failure |
| Missing required flagstat | Rejected before native aggregation | Expected failure |
| Required FastQC module disabled | Native MultiQC exits 0; wrapper rejects missing parsed identities | Expected failure; omission cannot pass silently. |
| Destructive name cleaning re-enabled | Native MultiQC exits 0; wrapper rejects collapsed identities | Expected failure |
| Independent repeat | Byte-identical canonical HTML and four metric exports | PASS |
| Input integrity | Focused QC input bytes unchanged; existing raw-read hash checks still pass | PASS |

Focused case stdout/stderr, input SHA256s, exact commands and exits are in each case
folder and `observations.json`. Complete regression artifacts are under
`results/multiqc/runs/docker-xbuym0la/`; the earlier pre-canonicalization integration
is retained separately. Ignored original `repo/tests/.runs/` paths are symlinks to
these retained directories to preserve absolute task/cache paths.

## Determinism boundary

Unmodified fresh MultiQC HTML differed only in the compressed plot's gzip timestamp,
a random report UUID and the embedded creation-date variable. The decompressed plot
payload was already identical. Evidence is retained in `fresh-html.diff` and
`determinism-proof.json`. The driver canonicalizes precisely those three fields,
requires one match per field and derives the report UUID from content/provenance.
A unit test proves the numerical plot payload is preserved; fresh real-report tests
require byte-identical HTML. Native JSON/parquet/logs retain their genuine generation
time and task paths, so the entire data directory is **not claimed byte-identical
across fresh independent executions**. Its explicit metric exports are deterministic;
the complete directory is byte-identical when reused from Nextflow cache.

## Scientific regression comparison

All 15 BAMs are byte-identical to the unmodified upstream baseline, including
headers and every alignment record. All 10 decompressed fixture FASTQ payloads
match baseline. Compressed fixture headers vary between independent fixture
creation times; each run independently verifies raw-byte preservation.

The 99 pre-existing published scientific files have identical path sets. Of these,
91 are byte-identical; three gzipped peak files have identical decompressed bytes,
and five SPP PDFs differ only in CreationDate/ModDate. Peak/quantification content
is unchanged, with 200 peaks for each of three treatments. No broad text/record
normalization was used. All old processing modules and old dependency locks remain
unchanged. Detailed hashes and comparison rules are in
`scientific-comparison-detail.json`, with raw stdout and commands retained.

## Versions, image identity and reproducible build

| Component | Version |
| --- | --- |
| MultiQC | 1.35 (exact YAML pin and generated package lock) |
| MultiQC container Python | 3.14.8 |
| Pixi | 0.70.1 |
| Nextflow | 25.10.4 build 11173 |
| Nextflow Java | 23.0.2-internal, build 23.0.2-internal-adhoc.conda.src |
| uv / micromamba | 0.11.33 / 2.5.0 |
| Docker client/server | 29.1.3 / 29.1.3 |
| Buildx | 0.37.2 |
| Executed platform | linux/amd64 |

| Environment | Image reference |
| --- | --- |
| DAP_SEQ_ALIGNMENT_IMAGE | `kundajelab/dap_seq_alignment@sha256:4764008ba8fbb5d831bd6f9ed6a720fd494062b39f0bae63ff2e4efd316ad842` |
| DAP_SEQ_TRACKS_IMAGE | `kundajelab/dap_seq_tracks@sha256:e6dd6ceb79e50fc6db83e9346a920e51fd2bf0dcffbc18c9305b1b6e8c806390` |
| DAP_SEQ_QC_IMAGE | `kundajelab/dap_seq_qc@sha256:ace177a497934a26adb305bc0dc92cc6a447fe8ca714b79f72a007c7acb53239` |
| DAP_SEQ_PEAKS_IMAGE | `kundajelab/dap_seq_peaks@sha256:10467dd29e3d25ce7769f76f57402bd1a5a582006e911d06479bfcc3e3325df3` |
| GENESIS_TOOLS_IMAGE | `kundajelab/genesis_tools@sha256:31458d4a6a83541f463ea4b0e692a0afc65c6df441f70c3f71fc4ccf1a11eb59` |
| DAP_SEQ_FASTQC_IMAGE | `sha256:97ca1e181a55a1d87653984956983fea3ff76cab5875f45ae2143168ff4fd73d` |
| DAP_SEQ_MULTIQC_IMAGE | `sha256:3f8fc8c57e57994b95408cd02a7ced44a6fb90396b9067bbe2d2dcdebb396b50` |

The new MultiQC reference is an immutable local image/config ID. RepoDigests is
empty because it was not pushed; it is not a remotely pullable registry digest.
The existing FastQC image has the same local-only limitation. Other references
remain their prior registry digests. Full version output, image IDs/architectures
and new environment SHA256s are in `versions-detail.json` and `image-detail.json`.

```bash
pixi init --import repo/environments/DAP_SEQ_MULTIQC.yaml \
  -p linux-64 -p osx-64 -p osx-arm64 -p linux-aarch64 scratch/multiqc/environment
pixi lock --no-install --manifest-path scratch/multiqc/environment/pixi.toml
# Generated manifest/lock copied to environments/DAP_SEQ_MULTIQC.{toml,lock}.
# From repo/environments:
docker build --provenance=false --platform linux/amd64 \
  --build-arg ENV_NAME=DAP_SEQ_MULTIQC -t genesis-validation/multiqc:1.35 \
  -f ../dockers/pixi-yaml.Dockerfile .
```

The existing Dockerfile and pinned bases were reused unchanged:
`ghcr.io/prefix-dev/pixi@sha256:2537738f8b7e2c7a7f070f56928ab959c4559a8d7e04f71eb16b0f779f0588f6`
and
`ubuntu@sha256:f3d28607ddd78734bb7f71f117f3c6706c666b8b76cbff7c9ff6e5718d46ff64`.
The direct build avoids the previously documented tagless-wrapper failure. Other
lock platforms resolve but were not executed. No image push, sudo, system software
installation, Docker permission/group/daemon change or credential change occurred.

## Failures, warnings and unresolved scope

Development probes preserved the following failures: native `--require-logs`
incorrectly reported missing custom_content despite parsing the metadata table;
title/filename-derived output-directory names initially violated the required
`multiqc_data/` path. The implementation now explicitly pins both names and enforces
parsed coverage itself. Initial lint findings were corrected without suppression.
The original non-deterministic HTML observations remain preserved separately.

Final focused/full/Docker suites all passed. Controlled negative cases are expected
failures, not omitted tests. Successful workflow task logs retain the ten existing
track-generation Matplotlib cache-warning logs from baseline; no new MultiQC warning
was observed in successful aggregation. These warnings were not hidden or fixed as
part of this change.

SPP aggregation remains explicitly deferred. Biological QC thresholds remain
UNSPECIFIED; MultiQC success and its displayed default tool labels do not establish
biological quality. Full Sorghum integration remains blocked on its exact reference
(audit/05). Large cohorts, conda execution, non-amd64 execution and remote image
distribution remain unvalidated. MultiQC metadata/readable identifiers do not solve
the previously demonstrated reference-content cache issue (audit/04).

## Changed files

Source: `.env`, `main.nf`, `nextflow.config` (manifest version),
`modules/multiqc.nf`, `multiqc_config.yaml`,
`genesis_tools/src/genesis_tools/multiqc_reporting.py`,
`environments/DAP_SEQ_MULTIQC.yaml`, `.toml`, `.lock`,
`tests/verify_multiqc.py`, `tests/verify_pipeline.py`, `scripts/check-projects.sh`,
and `README.md`.

Workspace documents: `design/adr-multiqc.md`, `reports/multiqc-validation.md`.
Evidence/scripts: `results/multiqc/` and `scratch/multiqc/`. Large outputs are outside
Git; these workspace documents are outside the upstream repository. No earlier
baseline report was altered. Nothing was pushed.
