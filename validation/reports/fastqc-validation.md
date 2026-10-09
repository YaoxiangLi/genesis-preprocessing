# FastQC implementation and validation

Date: 2026-10-07. Branch: `validation/fastqc`.
Baseline SHA: `4468c712e4c171b573e2ec2806fdc5327b5379e9`.
The baseline reports remain unchanged. This is the first intentional workflow change.
Design was written before implementation in [ADR](../design/adr-fastqc.md).
Final local commit: `430cfe31aab5fb9638d18c75a087a9bcb7a868c5`. Working tree clean after commit. Nothing pushed.

## Change and acceptance

PASS for the deterministic local SE/PE validation scope. Added FASTQC after DOWNLOAD
as an independent per-mate branch. SE gets one task; PE gets two. Reports are
`output/<species>/<sample_id>/qc/fastqc/<sample_id>.read{1,2}_fastqc.html` and `.zip`,
plus a per-mate `.fastqc.version.txt`. Reads are not trimmed or modified; existing
metadata/alignment channels and scientific modules are unchanged. Quality WARN/FAIL
labels are not interpreted as dataset failures. Biological acceptance thresholds
remain **UNSPECIFIED**.

FastQC has its own YAML/TOML/lock and container. This avoids changing R/SPP QC or its
cache identity. The only separate test-harness repair adds caller UID/GID to the
Docker BAM inspection helper, matching the production runner. Baseline audit/03
recorded the old permission failure. All original BAM assertions remain in place.

## Executed commands and resources

From repo/:

```bash
pixi run uv run --frozen --project genesis_tools python tests/verify_fastqc.py --keep
pixi run checks
pixi run validate-docker --keep
```

The experiment wrapper captured complete stdout and stderr, `/usr/bin/time -v`,
exit status, UTC start time, elapsed time, baseline SHA and source SHA256s. Exact
argv/cwd are in each `.json`; `.stdout`, `.stderr`, and `.time` are separate files.
Tests ran before commit on the recorded baseline plus the captured source changes.

| Task | Exit | Wall seconds | Maximum host RSS (KiB) | Evidence prefix |
| --- | --- | --- | --- | --- |
| environment-lock | 0 | 0.832 | 162340 | `results/fastqc/environment-lock.*` |
| image-build-buildkit | 0 | 20.141 | 56728 | `results/fastqc/image-build-buildkit.*` |
| focused-cache-fix | 0 | 27.462 | 393016 | `results/fastqc/focused-cache-fix.*` |
| checks-cache-fix | 0 | 52.445 | 664596 | `results/fastqc/checks-cache-fix.*` |
| docker-cache-fix | 0 | 259.737 | 711600 | `results/fastqc/docker-cache-fix.*` |
| scientific-comparison-final | 0 | 1.559 | 107052 | `results/fastqc/scientific-comparison-final.*` |

Host RSS is for the command/process tree measured by GNU time, **not aggregate
Docker memory**. Nextflow per-task metrics are in the retained traces. Final FastQC
tasks each took about 2.3 seconds and used 121.6–132.5 MB peak RSS on these small
fixtures. No large-dataset performance or biological conclusion follows from this.

The new environment was generated with Pixi 0.70.1:

```bash
pixi init --import repo/environments/DAP_SEQ_FASTQC.yaml \
  -p linux-64 -p osx-64 -p osx-arm64 -p linux-aarch64 scratch/fastqc/environment
pixi lock --no-install --manifest-path scratch/fastqc/environment/pixi.toml
# Copy the generated TOML/lock to environments/DAP_SEQ_FASTQC.{toml,lock}.
# From repo/environments:
docker build --provenance=false --platform linux/amd64 \
  --build-arg ENV_NAME=DAP_SEQ_FASTQC -t genesis-validation/fastqc:0.12.1 \
  -f ../dockers/pixi-yaml.Dockerfile .
```

Environment-init stdout/stderr are retained; its time/RAM were not measured. New
environment hashes and version commands are in `versions-detail.json`. All 17
pre-existing environment/dependency files inspected remained byte-identical,
including `pixi.lock`, `pixi.toml`, Python manifests/lock and all prior tool
environments. Only the new FastQC manifest/lock were resolved.

## Versions and container provenance

| Component | Observed version |
| --- | --- |
| Pixi | 0.70.1 |
| Nextflow | 25.10.4 build 11173 |
| Nextflow Java | 23.0.2-internal, build 23.0.2-internal-adhoc.conda.src |
| FastQC | 0.12.1; Bioconda noarch package `fastqc-0.12.1-hdfd78af_0` |
| FastQC Java | 25.0.2-internal, build 25.0.2-internal-adhoc.rattler.src |
| uv / micromamba | 0.11.33 / 2.5.0 |
| Docker client/server | 29.1.3 / 29.1.3 |
| Buildx | 0.37.2, commit 2d379c0c3f22da0d2759d132a0ec81ca949098f0 |
| Executed container platform | linux/amd64 |

| Image key | Immutable reference |
| --- | --- |
| DAP_SEQ_ALIGNMENT_IMAGE | `kundajelab/dap_seq_alignment@sha256:4764008ba8fbb5d831bd6f9ed6a720fd494062b39f0bae63ff2e4efd316ad842` |
| DAP_SEQ_TRACKS_IMAGE | `kundajelab/dap_seq_tracks@sha256:e6dd6ceb79e50fc6db83e9346a920e51fd2bf0dcffbc18c9305b1b6e8c806390` |
| DAP_SEQ_QC_IMAGE | `kundajelab/dap_seq_qc@sha256:ace177a497934a26adb305bc0dc92cc6a447fe8ca714b79f72a007c7acb53239` |
| DAP_SEQ_PEAKS_IMAGE | `kundajelab/dap_seq_peaks@sha256:10467dd29e3d25ce7769f76f57402bd1a5a582006e911d06479bfcc3e3325df3` |
| GENESIS_TOOLS_IMAGE | `kundajelab/genesis_tools@sha256:31458d4a6a83541f463ea4b0e692a0afc65c6df441f70c3f71fc4ccf1a11eb59` |
| DAP_SEQ_FASTQC_IMAGE | `sha256:97ca1e181a55a1d87653984956983fea3ff76cab5875f45ae2143168ff4fd73d` |

FastQC's reference above is an immutable **local image/config ID**, not a registry
manifest digest. `RepoDigests` is empty because the image has never been pushed.
Remote pull/Apptainer use of that ID is not supported. The committed locks and
existing Dockerfile provide a rebuild path; rebuilds may have a different image
ID, which must be recorded and explicitly configured. Other image references are
unchanged registry digests; image IDs and architectures are in `versions-detail.json`.

The unchanged Dockerfile pins build base
`ghcr.io/prefix-dev/pixi@sha256:2537738f8b7e2c7a7f070f56928ab959c4559a8d7e04f71eb16b0f779f0588f6`
and runtime base
`ubuntu@sha256:f3d28607ddd78734bb7f71f117f3c6706c666b8b76cbff7c9ff6e5718d46ff64`.
Only linux/amd64 was built/executed. Other lock platforms were resolved but not tested.

Buildx was absent. The first build failed on unsupported `--provenance` and recorded
the legacy-builder deprecation warning. The official v0.37.2 Linux AMD64 binary and
release checksums were downloaded; SHA256
`982ca20490b45ed1ec8d99795974d3d874a358f75938c9c237305010e6b7e548` matched.
It was installed solely at `~/.docker/cli-plugins/docker-buildx`. The first checksum
parser attempt failed because checksum filenames use a `*` marker; parsing was
corrected and the full hash verified before installation. Commands and logs are
retained in `scratch/fastqc/install-buildx.sh` and `results/fastqc/buildx-install*`.
[Official manual installation](https://github.com/docker/buildx#manual-download),
[pinned release](https://github.com/docker/buildx/releases/tag/v0.37.2).
No sudo, daemon/group/socket/security changes, credential changes, or pushes occurred.

## Raw observations

| Verification | Observed result |
| --- | --- |
| Initial real workflow | 41 tasks COMPLETED: baseline 34 plus 7 FASTQC tasks. |
| SE/PE coverage | Three SE libraries plus two PE libraries: exactly 7 uniquely tagged mate tasks. |
| Published reports | 7 nonempty HTML + 7 valid ZIP + 7 version files; expected filename, version, read counts and 75-base length checked. |
| First resume | 37 tasks: 10 CACHED (3 DOWNLOAD + 7 FASTQC), 27 COMPLETED. Reference-build tasks are bypassed. |
| Stable resume | All 37 tasks CACHED, including all 7 FASTQC tasks. |
| Report stability | All 21 FastQC files byte-identical across resumes. |
| Raw reads | All 10 fixture gzip files unchanged from pre-run hashes; 7 consumed mates match served/downloaded/FastQC-staged bytes. Unused SE mate fixtures are distinguished from consumed input. |
| Alignment | All 15 BAM files byte-identical to unmodified baseline, including headers and every SAM record; all previous MAPQ/length/flag assertions passed. |
| Existing published files | Same 99 relative paths. 91 byte-identical. 3 gzip peak files have identical decompressed bytes; 5 SPP PDFs differ only in CreationDate/ModDate. |
| Peaks/quantification | Each of three treatments has 200 peaks. All quantification files byte-identical, finite, positive where expected, with matching peak coordinates. |
| Publication boundaries | No FASTQ, BAM, BAI, SAM, bedGraph, cache directory or alignment intermediate published. |
| Empty/corrupt download | Both rejected by unchanged DOWNLOAD before FASTQC or BWA_MEM2_ALIGN. |
| Focused low-complexity input | Valid 100-read library completes with FastQC FAIL labels retained. |
| Focused empty input | FastQC produces a valid zero-read report; actual workflow rejects this upstream. |
| Focused malformed separator/corrupt gzip | Both fail the module and publish no report pairs; diagnostics retained. |
| Short quality string | FastQC 0.12.1 accepts it. Recorded limitation, not evidence of valid input. |

The seven integration ZIP summaries contain {'PASS': 56, 'FAIL': 14}. No label caused rejection.


The 27 first-resume recomputations are the existing change from work-directory
reference products to published reference paths, documented at baseline. FastQC
only depends on the original download branch and remains cached. No unexpected
FastQC reruns occurred.

Evidence: `results/fastqc/scientific-comparison-detail.json` contains SHA256 pairs
for inputs, every published file and all BAMs, plus SAM record hashes. Independent
comparison requires exact bytes first; only gzip payload and PDF date-field
normalization were accepted, with no broad text/record normalization.
`output-review-detail.json` contains traces, ZIP summaries, negative-input stderr,
peak counts and old-manifest checksums. Fixture SHA256 snapshots are retained in
`raw-input-sha256.json`; each focused negative case has its own SHA256 in
`fastqc-cases/observations.json`. FASTQ gzip headers differ between baseline fixture
generations, but all 10 decompressed fixture payloads match exactly.

## Failures and warnings preserved

- Initial full checks failed to resolve an imported sibling test module. The
  harness now invokes the focused test script as a subprocess, with no type-check
  suppression or weaker assertion.
- Initial focused execution failed because dotenv interpreted an absolute filename
  relative to the harness. The harness now writes only the selected image key to a
  local dotenv file; no secret entries are copied.
- The initial short-quality test incorrectly assumed that FastQC enforces equal
  sequence/quality length. That assertion failed. Its logs remain retained and the
  limitation is explicitly tested/reported. Rejection tests for malformed separators
  and corrupt gzip are still required. The [versioned FastQC parser](https://raw.githubusercontent.com/s-andrews/FastQC/v0.12.1/uk/ac/babraham/FastQC/Sequence/FastQFile.java)
  supports this distinction. Existing metadata malformed-input tests remain intact;
  those metadata checks sample a bounded number of records, not all reads.
- The first passing Docker integration still emitted `Fontconfig error: No writable
  cache directories` in all seven FastQC tasks. FASTQC now creates a writable
  task-local XDG cache. Focused tests, full checks and Docker validation were rerun
  after that source fix. Original logs are retained; final FastQC task stderr has
  no Fontconfig error. No warnings were hidden or redirected away.
- Existing track-generation Matplotlib cache warnings remain: permission denied for
  `/.config/matplotlib`, followed by fallback to a temporary cache. These predate
  FastQC (audit/03) and are preserved. They were not repaired in this change.
- A reporting-helper filename collision initially replaced detail JSON with command
  metadata. Distinct detail filenames were introduced and read-only inspection was
  repeated from retained artifacts; final reports link the complete detail files.

## Interpretation and limits

The fixture establishes that this implementation observes raw mates independently,
publishes expected artifacts, caches on resume and leaves tested scientific outputs
unchanged. It does not establish plant/assay biological QC cutoffs or validate real
Sorghum data. The exact Sorghum reference remains unavailable (audit/05). FastQC's
own default summary labels are observations, not dataset acceptance criteria.
Conda execution, non-amd64 containers, remote Apptainer and large-library resource
behavior remain untested. Local image distribution is an explicit prerequisite for
using the Docker profile on another host.

## Files changed and retained

Committed source: `.env` (one image key), `main.nf`, `modules/fastqc.nf`,
`environments/DAP_SEQ_FASTQC.yaml`, `.toml`, `.lock`, `tests/verify_fastqc.py`,
`tests/verify_pipeline.py`, and `README.md`. Existing alignment, peak, track, QC,
metadata, download and reference modules are unchanged. Existing dependency locks
are unchanged.

Workspace documents: `design/adr-fastqc.md`, `reports/fastqc-validation.md`.
Reproduction/inspection scripts are under `scratch/fastqc/`. Full successful and
unsuccessful test evidence and large outputs are under `results/fastqc/`; original
ignored test-run paths are symlinks to retained runs so absolute cache paths remain
usable. `artifact-locations.json` records the mapping. No generated outputs are
committed and nothing is pushed. These workspace audit documents are outside the
upstream Git repository and are not part of the source commit.
