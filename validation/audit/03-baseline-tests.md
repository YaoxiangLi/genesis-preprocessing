# Unmodified upstream baseline verification

Date: 2026-10-07. Host: Ubuntu 24.04.2, x86_64; Docker linux/amd64. Baseline SHA: **`4468c712e4c171b573e2ec2806fdc5327b5379e9`**, branch `main`.

**Normal checks: PASS. Docker validation command: FAIL.** All 34 real workflow tasks completed and upstream output assertions passed, but the Docker test harness then failed to read a BAM because its helper container runs as UID 999 against a mode 0700 fixture directory owned by UID 1001. That failure was reproduced and preserved without changing permissions, source, tests or configuration. Independent host inspection verified all 15 BAMs and the numerical outputs. The original resume checks, which the failing harness did not reach, were invoked separately without altering their implementation and passed. Both additional stable resumes cached all 30 expected tasks.

No failures were patched, no assertions weakened, no dependency manifests/locks changed, and no MAPQ, duplicate, trimming, reference or peak-calling policy was changed. No sudo, Docker permission/group/daemon changes, privileged containers, image builds or pushes were used. This is integration validation on synthetic fixtures, not biological validation of DAP-seq choices or ATAC suitability. Plant biological QC acceptance thresholds remain **UNSPECIFIED**.

## Executed commands and results

Commands ran from `repo/` with `PATH="$HOME/.pixi/bin:$PATH"`. Each substantial command was wrapped with `/usr/bin/time -v`; complete stdout/stderr are separate files under `../results/baseline/`, and explicit exit status files use `.exit`. The timing files independently preserve actual exit status. Nextflow's child stdout/stderr are combined by the **existing** driver into per-run `output-*.log`; full task `.command.*` and Nextflow diagnostic logs are retained for the `--keep` runs.

| Command / invocation | Exit | Elapsed | Peak RSS, KiB | Evidence prefix |
|---|---:|---:|---:|---|
| `pixi run checks` | **0** | 50.82 s | 656,428 | `checks.*` |
| `pixi run validate-docker --keep` | **1** | 132.69 s | 734,956 | `docker.*` |
| `pixi run uv run --frozen --project genesis_tools python tests/verify_pipeline.py --keep` | **0** | 48.10 s | 664,468 | `stubs-keep.*` |
| Original `check_bams` called again, with its `CalledProcessError` stdout/stderr saved | **1** | 1.73 s | 34,728 | `docker-bam-reproduce.*`, `docker-bam-subprocess.*` |
| Original `check_resume(work, sheet, docker=True)` called separately | **0** | 88.10 s | 659,216 | `docker-resumes.*` |
| Additional stub `run_pipeline(..., resume=True, suffix="stable2")` | **0** | 6.77 s | 692,056 | `stubs-stable2.*` |
| Additional Docker `run_pipeline(..., docker=True, resume=True, suffix="stable2")` | **0** | 6.72 s | 698,340 | `docker-stable2.*` |
| Independent host BAM/peak/score/publication inspection | **0** | 1.98 s | 70,492 | `independent-inspection.*` |

Representative exact wrapper for the required normal command:

```bash
export PATH="$HOME/.pixi/bin:$PATH"
/usr/bin/time -v -o ../results/baseline/checks.time pixi run checks \
  > ../results/baseline/checks.stdout 2> ../results/baseline/checks.stderr
baseline_exit=$?
printf '%s\n' "$baseline_exit" > ../results/baseline/checks.exit
```

The required Docker command used the same wrapper with `pixi run validate-docker --keep` and `docker.*` paths. The normal suite deletes its fixture directory on exit; the additional **unchanged** regression command with `--keep` supplies complete retained evidence. The normal command's stdout/stderr are complete, but its deleted internal task logs cannot be reconstructed; the retained rerun is explicitly separate evidence.

Diagnostic continuations imported the unchanged test file rather than copying or patching its functions. Example executed Python body for the Docker resume checks, launched through `pixi run uv run --frozen --project genesis_tools python -c`:

```python
from pathlib import Path
import runpy
n = runpy.run_path("tests/verify_pipeline.py", run_name="baseline_probe")
w = Path("tests/.runs/docker-uwbgvcy1").resolve()
n["check_resume"](w, w / "samples.tsv", docker=True)
print("Original Docker check_resume passed")
```

The extra stable command called the same module's `run_pipeline(w, w/"samples.tsv", docker=True, resume=True, suffix="stable2")` and returned its actual exit code; the stub counterpart used `regression-ocblnax2` and omitted `docker=True`. No fixture server was restarted for these extra invocations; all three DOWNLOAD tasks were cached and required no reads to be served again.

GNU time measures the driver/JVM process tree, **not** aggregate Docker-daemon or container memory. Per-task Nextflow metrics are retained in every trace. Maximum reported initial real-task peak RSS was 194.4 MB for `TRACKS (se_control)`. Short tasks can have zero/sampled-low measurements. Runs overlapped in wall time; this is not a controlled performance benchmark. Small read-only inspection/version probes have measured timings where captured in JSON; otherwise elapsed/RAM are UNAVAILABLE.

## What the normal suite actually ran

`check-projects.sh` completed every stage: ShellCheck, Ruff lint, Ruff format check (eight files), ty for the project, ty for tests, `verify_nextflow_style.py`, and `verify_pipeline.py`. Successful progression under `set -euo pipefail` establishes that the silent ShellCheck stage also passed.

Focused tests exercised numerical primary/NH counting and interval cases, process style, mocked Docker build selection/platforms/no-push/failure behavior, wrapper argument handling, four sample sheets' stored identity/control digests, invalid sheets, metadata errors, and Nextflow stub runs. Mock Docker pushes never publish images. Real Docker `main()` skips wrapper/sheet/metadata unit cases by design; those were covered by the normal suite. The Docker command reached `check_outputs` successfully, then failed in `check_bams` before `check_resume`. Separately invoking the unchanged resume function closes that execution gap without reclassifying the original command as passing.

Retained invalid-input workflow evidence:

| Case | Observed behavior |
|---|---|
| Missing assigned control | `trace-invalid-sheet.tsv`: exactly one FAILED VALIDATE_SHEET task; no DOWNLOAD tasks |
| BWA seed length 0 | Parameter validation rejected it; `trace-invalid-bwa.tsv` contains no tasks; expected positive-integer diagnostic present |
| Multiple input sheets | Parameter validation rejected it; `trace-multiple-sheets.tsv` contains no tasks; expected “Supply exactly one” diagnostic present |

The normal and retained stub drivers exited 0 after checking these expected failures. They are successful negative tests, distinct from the unexpected Docker helper failure. Unit cases also reject duplicate/self/cross-species/layout controls, unsafe IDs/URLs, missing references, malformed/empty reads and invalid size records. They are not exhaustive validation of real-world biological inputs.

## Unexpected Docker harness failure

`tests/verify_pipeline.py:check_bams` invokes:

```text
docker run --rm --network none -v <fixture-root>:<fixture-root>:ro \
  kundajelab/dap_seq_alignment@sha256:4764008ba8fbb5d831bd6f9ed6a720fd494062b39f0bae63ff2e4efd316ad842 \
  samtools view <fixture-root>/work/c2/d08c2cbd1b066054f44aeda7ef5391/se_control.spp.bam
```

Unlike workflow containers, this helper command has no invoking-user override. Observed image default user: `nonroot`; `docker run ... id` reports UID 999/GID999. Python `tempfile.mkdtemp` created `<fixture-root>` with mode 0700, owner 1001:1001. The BAM itself is mode 0644, owner 1001:1001. The root directory denies the helper traversal before BAM readability matters. Workflow containers ran with the configured invoking UID/GID and therefore completed their tasks.

Captured underlying stderr:

```text
[E::hts_open_format] Failed to open file ".../se_control.spp.bam" : Permission denied
samtools view: failed to open ".../se_control.spp.bam" for reading: Permission denied
```

The original traceback retains the complete actual command/path in `docker.stderr`; reproduction saved complete subprocess stderr in `docker-bam-subprocess.stderr` and its command/exit1 in JSON. No ownership, mode, container user, test command or workflow setting was modified to make this pass. The independent readback below is additional evidence, **not a repaired or passing upstream BAM test**.

## Retained fixture and output inspection

Runs are retained under:

- `results/baseline/runs/regression-ocblnax2/` — about 35 MiB, stub tests and invalid-input cases.
- `results/baseline/runs/docker-uwbgvcy1/` — about 103 MiB, real-tool initial/resume/stable/stable2 work and outputs.

After all runs finished, these generated directories were moved out of `repo/tests/.runs/`. Ignored symlinks at the original paths preserve the absolute staging/cache paths embedded in task scripts and logs. Source files were not moved or changed; modes/ownership were not altered. `artifact-locations.json` records the mapping and `artifact-manifest.json` records 2,277 regular-file/symlink entries with checksums or link targets. No workflow computation occurred after relocation.

The seeded fixture has a 2,000,000-base genome, duplicated sequence, 75-base FASTQ records, SE treatments `se_treatment` and `se_second`, shared `se_control`, and PE treatment/control. There are 32,000 generated records per treatment mate and 6,000 per control mate. The generator writes second-mate files even for SE fixture libraries, but the sheet uses `-` for those mates and the workflow does not ingest them. Compressed and decompressed FASTQ/FASTA checksums, record counts and lengths were independently collected in `independent-inspection.json`. Both FASTAs contain the expected two million bases; no public assembly substitution occurred.

The real run generated two chromosome-size files and two complete BWA index directories. All 14 reference files (two FASTAs, two sizes, ten index components) retained identical checksums and mtimes across the separately executed first resume and both stable resumes. Stub reference generation uses fake sizes/index files and cannot alone establish indexing correctness.

### BAMs, MAPQ and read policy

All 15 **real** BAMs were read with installed host pysam 0.24.1; no project counting code was used. Every BAM is nonempty, retains MAPQ0, and excludes all flag 2308 records. Main/QC query lengths are 75; SPP query lengths are 50. All QC/SPP BAMs are unpaired; PE main records carry paired flags.

| Sample | Primary records | Primary MAPQ0 | QC records / MAPQ0 | SPP records / MAPQ0 |
|---|---:|---:|---:|---:|
| se_control | 6,000 | 102 | 6,000 / 102 | 6,000 / 102 |
| pe_control | 12,000 | 210 | 6,000 / 105 | 6,000 / 105 |
| se_second | 32,000 | 100 | 32,000 / 100 | 32,000 / 100 |
| pe_treatment | 64,000 | 202 | 32,000 / 102 | 32,000 / 102 |
| se_treatment | 32,000 | 101 | 32,000 / 101 | 32,000 / 101 |

The independent reader checked all records, lengths, flag distributions and read groups and saved BAM hashes. This verifies behavior on these fixtures, not sensitivity to different MAPQ/duplicate policies or complex alignment edge cases.

### Controls, peaks and quantification

Executed CALL_PEAKS scripts and staged control BAM symlink targets were inspected. `se_treatment` and `se_second` both point to the **same actual** `se_control` primary BAM (matching resolved path and SHA256), while `pe_treatment` points to `pe_control`. Controls have no published peaks or score outputs. This checks the data association, beyond matching control-name substrings in command text.

All three treatment narrowPeak files contain **200 rows**. Each RPM and mean_RPKM TSV contains 200 finite positive values and preserves the exact peak rows/order. Independent numerical checks used:

1. An independent primary-read-end denominator from a full BAM scan, then indexed BAM overlap counting per peak, divided by that denominator and multiplied by one million.
2. Direct length-weighted integration of the RPKM bedGraph over each peak, including uncovered bases in the denominator; input coverage intervals were checked for disjointness first.

The inspection ran from workspace root as `/usr/bin/time -v -o results/baseline/independent-inspection.time repo/genesis_tools/.venv/bin/python -`, with the read-only audit program supplied on stdin and complete stdout/stderr captured to `independent-inspection.stdout`/`.stderr`. Its inputs and detailed observations are in the JSON evidence. Neither calculation called `genesis_tools.quantification`. All **1,200 score values** matched within floating serialization tolerance (`rel_tol=1e-10`, `abs_tol=1e-10`, a numerical comparison tolerance, not biological QC). RPM values matched exactly. Maximum absolute mean_RPKM difference was ~4.984e-6 for values around 1e6, consistent with 12-significant-digit output.

| Treatment | Read-end denominator | Peaks | RPM range | mean_RPKM range |
|---|---:|---:|---|---|
| se_second | 32,000 | 200 | 4,687.5–4,781.25 | 1,154,152.68456–1,386,853.44828 |
| pe_treatment | 64,000 | 200 | 4,687.5–4,781.25 | 1,115,184.43910–1,327,112.85425 |
| se_treatment | 32,000 | 200 | 4,687.5–4,750 | 1,141,408.86288–1,343,106.99588 |

This is an oracle against the produced BAM and bedGraph, not an independent proof that MACS3 or deepTools implements a biologically suitable model.

### Publication boundaries and SPP

The real published sample tree contains **99 files**, versus 67 in the stub run. Real SE samples each have five bigWigs; PE samples each have ten. BigWig signatures are valid; SPP PDFs have PDF signatures and nonzero sizes. Metadata and alignment provenance match layout/read-length policies. No FASTQ, BAM, BAI, SAM or bedGraph appeared in the published sample tree. References are published separately; FASTQs/BAMs and bedGraphs remain in work, as expected. The independent enumeration and checksums are in `trace-output-review.json`.

SPP tables and plots exist for all five samples, but upstream tests mostly check existence/nonemptiness rather than scientific quality. Raw control results include:

- `se_control`: NSC 1.52381, RSC **-7.333333**, quality tag **NA**.
- `pe_control`: NSC 1.512821, RSC **8.489226e+14**, quality tag 2; reported phantom and baseline correlations both round to 0.004307489.

These observations suggest sensitivity to a very small RSC denominator in the weakly enriched control; they are not invented biological failure thresholds. No NA-fragment fallback was exercised by this fixture. Treatment RSC values are about 6.26–6.62. Plant-specific acceptance cutoffs remain **UNSPECIFIED**. The suite passing its output checks does not validate interpretation of these QC scores.

## Resume, reference reuse and reproducibility

Both retained runs show the same task-count pattern:

| Phase | Stub trace | Docker trace | Interpretation |
|---|---|---|---|
| Initial | 34 COMPLETED | 34 COMPLETED | Includes two sizes and two index tasks |
| First resume | 27 COMPLETED + 3 CACHED | 27 COMPLETED + 3 CACHED | DOWNLOAD cached; reference tasks skipped; changed reference paths cause downstream recomputation |
| Stable resume | 30 CACHED | 30 CACHED | Every scheduled task cached |
| Additional second stable resume (`stable2`) | 30 CACHED | 30 CACHED | Independently requested extra resume; every scheduled task cached |

The original `check_resume` only explicitly asserts stable caching for DOWNLOAD, BWA_MEM2_ALIGN and QUANTIFY. This audit inspected **all trace rows**, so the all-30 statement is independently supported. No reference tasks ran after the initial phase. The Docker driver's original command never reached resume because of `check_bams`; the separate unchanged resume invocation is clearly distinguished above.

Final published products were compared byte-for-byte to the original completed task products. **91/99 match exactly.** The remaining eight are three gzipped narrowPeaks with **identical decompressed contents**, and five SPP PDFs that become byte-identical after removing only CreationDate/ModDate fields in memory. No files were rewritten to normalize them. `recomputed-byte-differences.json` preserves raw hashes and comparison results. Numerical score files and SPP TSVs match exactly across recomputation. Thus semantic repeatability is supported for these fixtures, but raw-byte identity of all outputs is **not** established and is false for these observed files. Fixture gzip headers also carry timestamps; seeded sequence generation does not guarantee byte-identical compressed fixtures.

## Warnings and errors retained

- First-run Nextflow warning: configured `-resume` ignored because there is no prior run history.
- TRACKS logs: **80** `mkdir -p failed ... /.config/matplotlib ... Permission denied` events across ten executed TRACKS tasks (five initial, five first-resume), each followed by a temporary Matplotlib cache-directory warning. These did not cause task failure. Counting `.command.err` only avoids double counting the same lines in `.command.log`.
- Docker BAM-inspection helper: unexpected permission failure described above, original and reproduced.
- Invalid-input tests: expected schema/sample-validation errors and trace failures, retained rather than suppressed.

The complete logs remain available. `warnings-errors.json` is an index of matched lines, not a replacement for full logs; its raw count includes duplicate command-log/stderr occurrences and stack traces. The more precise task-only counts are in `trace-output-review.json`. No environment variable was set to silence Matplotlib or other warnings.

## README claim classification

Classification applies to this SHA and these observed Ubuntu/linux-amd64 runs. A historical linux/arm64 run is not directly reproduced by this host. “VERIFIED” below means observed for these fixtures, not universal software or scientific correctness.

| Claim | Classification | Evidence and limits |
|---|---|---|
| Full normal suite covers shell/Python checks, focused quantification and mocked builds | **VERIFIED** | Required `pixi run checks` exit0; every stage completed |
| SE workflow | **VERIFIED** | Three SE libraries executed in stub and real runs; real BAMs/outputs inspected |
| PE workflow | **VERIFIED** | Two PE libraries executed; paired main BAMs, unpaired QC/SPP, ten PE tracks inspected |
| Treatment/control association | **VERIFIED** | Actual staged control targets/digests and MACS3 scripts match sheet assignments |
| One control reused by multiple treatments | **VERIFIED** | Both SE treatments reuse the same se_control BAM, not independent renamed copies |
| Invalid input rejection | **VERIFIED** | Unit cases passed; retained workflow negative traces stop before downloads; not exhaustive |
| Reference generation | **VERIFIED** | Two real sizes and complete five-file indexes per reference; generated once initially |
| Reference reuse | **VERIFIED** | Later reference tasks absent; 14 reference-file hashes/mtimes unchanged; stale-content invalidation is not tested |
| Resume/cache behavior | **VERIFIED** | First path-transition recomputation; both stable phases all 30 cached, stub and real |
| MAPQ0 retention | **VERIFIED** independently | All15 real BAMs contain MAPQ0; upstream helper assertions were blocked by permissions |
| SPP uses shortened read1 while main/QC use full reads | **VERIFIED** independently | Real SPP reads 50, main/QC 75; all SPP/QC records unpaired |
| Nonempty peak output / 200 peaks per treatment | **VERIFIED** | Three real narrowPeaks, 200 rows each |
| Quantification outputs preserve peaks and contain finite positive scores | **VERIFIED** | Six files, 1,200 values, exact rows and independent numeric checks |
| Output publication boundaries | **VERIFIED** | Enumerated all 99 real/67 stub sample files; references separately published |
| FASTQs not published | **VERIFIED** | No FASTQ extensions in either sample publication tree; fixtures/work do contain reads |
| BAMs not published | **VERIFIED** | No BAM/BAI in either sample publication tree; work BAMs retained |
| Docker test command validates BAMs and resume end-to-end successfully on this server | **CONTRADICTED** | Required command exits1 in helper; independent inspection/separate resumes are not a passing original command |
| Existing tests cover real MAPQ/read-length checks and all stable tasks | **PARTIALLY VERIFIED** | Assertion code exists, helper blocked; stable test names only three process types; independent audit covers remaining evidence |
| README current task-count expectation of 45 initial / 41 cached | **CONTRADICTED** for current SHA | Current tests explicitly expect 34; observed 34 initial and 30 stable; historical run cannot be adjudicated here |
| Tool logs contain no warnings | **CONTRADICTED** on this host | Matplotlib fallback warnings and permission diagnostics retained |
| Historical 2026-10-06 linux/arm64 validation result | **NOT VERIFIED** | This execution is linux/amd64, a later SHA/context |
| Synthetic fixtures are deterministic | **PARTIALLY VERIFIED** | Seeded biological content; gzip headers, ports and paths vary; outputs include timestamp-dependent bytes |
| SPP no-fragment-peak NA fallback is validated | **NOT VERIFIED** | No such failure path in this fixture; control quality-tag NA is not that fallback |
| Biological outputs / plant QC interpretation are validated | **NOT VERIFIED** | README itself says full public-data comparisons remain separate; observed extreme control RSC is not quality validation |

## Software and immutable image provenance

Runner: Pixi 0.70.1, Nextflow 25.10.4 build 11173, Groovy 4.0.28, project OpenJDK 23.0.2-internal, micromamba 2.5.0, uv 0.11.33, CPython 3.14.5, pysam 0.24.1, defopt 7.0.0, ShellCheck 0.11.0, Ruff 0.16.10, ty 0.0.84; plugins nf-schema 2.4.2 and nf-dotenv 1.0.0. Docker client/server 29.1.3. See audit02 and `tool-versions.json` for raw observations.

Measured container tools: samtools/htslib 1.24, aria2c 1.37.0, deepTools 3.5.6, MACS3 3.0.5, R 4.4.3, spp 1.16.0, caTools 1.18.4, snow 0.4.4, gawk 5.4.1; genesis-tools 0.1.0 with CPython 3.14.5/pysam 0.24.1/defopt 7.0.0.

**Version-report discrepancy:** the installed conda BWA package is `bwa-mem2 2.3 he70b90d_0` with artifact SHA256 `7ccf117aa586d663e12181e60f0cf60215fb162515e0b6e98517f5e108613d41`, matching the package identity in the lock, but the executable's `bwa-mem2 version` prints **2.2.1**. Alignment provenance records the executable-reported value. Both observations are preserved in `bwa-package-identity.json`, `tool-versions.json` and sample provenance; no unsupported conclusion about a wrong image is drawn from this alone.

The previously missing configured images were pulled automatically by Nextflow during the authorized Docker test. Local inspection now confirms all five are linux/amd64. Exact declared digest and local image configuration ID follow; these identify this execution without asserting a build-to-git attestation.

| Image setting | Immutable image reference | Local image ID |
|---|---|---|
| `DAP_SEQ_ALIGNMENT_IMAGE` | `kundajelab/dap_seq_alignment@sha256:4764008ba8fbb5d831bd6f9ed6a720fd494062b39f0bae63ff2e4efd316ad842` | `sha256:2e2c492c5935b2187212d09a3b1009e5f25c9bede8c41217dfac1beea22ad8f3` |
| `DAP_SEQ_TRACKS_IMAGE` | `kundajelab/dap_seq_tracks@sha256:e6dd6ceb79e50fc6db83e9346a920e51fd2bf0dcffbc18c9305b1b6e8c806390` | `sha256:61a1abe901bd424a719619a8e0c1a81275ee5635d96d12e16f8d5b25c3f66149` |
| `DAP_SEQ_QC_IMAGE` | `kundajelab/dap_seq_qc@sha256:ace177a497934a26adb305bc0dc92cc6a447fe8ca714b79f72a007c7acb53239` | `sha256:2c5e0239910883b3540b152e24c651c13c1fae1ea454572e4ca7243a72066cfd` |
| `DAP_SEQ_PEAKS_IMAGE` | `kundajelab/dap_seq_peaks@sha256:10467dd29e3d25ce7769f76f57402bd1a5a582006e911d06479bfcc3e3325df3` | `sha256:49c00c5a20397109816a2e1c5ea4a62d126ff1455db953c72dce0b8747c620ce` |
| `GENESIS_TOOLS_IMAGE` | `kundajelab/genesis_tools@sha256:31458d4a6a83541f463ea4b0e692a0afc65c6df441f70c3f71fc4ccf1a11eb59` | `sha256:966cf11967c6d0bdff49a6fdb31a8579de832288ff38f7281285b15ded689d7f` |

## Acceptance and files changed

Every available baseline test entry point was attempted: normal full checks and Docker validation. The complete original Docker failure is preserved; the blocked BAM assertions have independent readback evidence, and the skipped resume function was explicitly executed unchanged. Expected negative-test failures are distinguished from the unexpected helper failure. Output contents, control association, all stable trace rows and reference immutability were inspected. No full-suite success is claimed for Docker.

All original tracked-file SHA256 values are recorded in `results/baseline/before.json`; final comparison is in `final-acceptance.json`. The upstream SHA and all 73 tracked file hashes, including tests, source, `.env`, manifests and locks, remain unchanged, with empty Git porcelain status. Ignored test output/cache paths are expected. No code branch or commit was created because no production/test code was changed.

Created: `audit/03-baseline-tests.md`, `results/baseline/` logs/status/timing/JSON evidence, and retained fixture/work/output trees with compatibility symlinks in ignored `repo/tests/.runs/`. Five immutable workflow images are now cached in Docker. Large generated artifacts are under results, not Git. Audit02's images-absent observation remains an accurate earlier observation; this task's automatic pulls are recorded separately.

Remaining uncertainty: biological validity, official/reference-pipeline comparisons, plant-specific QC limits, error-path coverage beyond these fixtures, cross-platform behavior, clean-room reproducibility and image/source attestation. No fixes or sensitivity experiments were undertaken. Baseline verification is complete with the Docker helper failure and warnings explicitly unresolved.
