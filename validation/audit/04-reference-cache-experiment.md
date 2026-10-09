# Synthetic reference provenance and cache correctness

Observed 2026-10-07. Upstream SHA: **`4468c712e4c171b573e2ec2806fdc5327b5379e9`**. Local branch: `validation/reference-cache-experiment`, created at that unchanged SHA before adding the experiment driver outside the repository.

**Finding: HIGH severity silent reference inconsistency, empirically reproduced.** Replacing a synthetic FASTA with different contents under the same filename did not regenerate chromosome sizes or the bwa-mem2 index. All six non-reference tasks, including sample validation, remained cached. A separate run with an empty Nextflow task cache recomputed all six tasks but still used the stale reference products. Renaming the identical replacement FASTA to a new basename caused both products to rebuild correctly.

This is a **synthetic reference-file sensitivity experiment**, not a bug fix. All references, reads, run/work/cache directories, snapshots and experiment code are under `scratch/reference-cache-experiment/`. No real reference was read, overwritten, renamed or removed. No upstream source, tests, manifests, locks or `.env` changed. No permissions, Docker configuration or preprocessing policies were changed.

## Deterministic design and scientific oracle

Reference A is 100,000 bases on `chr1`. Reference B contains the exact same `chr1` plus a new 10,000-base `chr_added` contig. Both are tiny generated sequences, not excerpts of a real assembly. Seeds are 44207 for chr1, 44208 for chr_added and 44209 for reads, using pinned CPython 3.14.5. FASTA formatting is fixed. Gzip has an empty embedded filename, compression level 6 and timestamp 0. An independent in-memory re-generation reproduced both compressed SHA256 values exactly; it did not overwrite experimental files.

The fixed single-end library has 10,000 75-base reads: 8,000 enriched reads in twenty chr1 regions, 1,900 chr1 background reads, and **100 named witness reads** (`added_000`–`added_099`) from chr_added. The same read file is used in every phase. The sample sheet uses one control-only library, `probe`, with `control_sample = -`, which the unmodified workflow supports. This invokes reference generation, metadata, alignment, QC and tracks. Peak calling and quantification are deliberately not needed for this reference-cache test.

The expected reference-dependent result is exact rather than a biological QC cutoff:

- With A: BAM header contains only chr1; 9,900 retained mapped reads; zero chr_added witnesses mapped.
- With B and correct products: header contains chr1 and chr_added; 10,000 retained mapped reads; all 100 witness reads mapped; metadata genome size 110,000.
- Reusing A's products for B yields the first result despite B's actual content. That is a provenance/correctness failure, not low biological enrichment.

A and B are archived immutably as `reference-versions/A.fa.gz` and `B.fa.gz`. The active reference initially uses `references/synthetic.fa.gz`. Phase 04 overwrites **only this synthetic active path** with B. Phase 07 renames that same B file to `references/renamed.fa.gz` and updates only the sheet's reference filename. Original A-derived files remain in the test directory as evidence; no cleanup/rebuild fix was applied.

File mtimes are explicitly controlled: A initially has epoch 1700000000; mtime-only A uses +100 seconds; B replacement uses +200 seconds; mtime-only B uses +300 seconds. Rename preserves B's +300 mtime. Compressed file sizes and contents differ between A and B, so the same-name stale result does not rely on concealing changes with an equal-size/equal-mtime edit.

## Execution and retained provenance

The complete reproducible driver is [experiment.py](../scratch/reference-cache-experiment/experiment.py). It refuses to reuse existing fixture subdirectories; a rerun should use a **new empty directory under scratch**, with a copy of the driver, rather than overwrite retained evidence. It asserts that its base is under scratch. No separate test framework was introduced.

Executed from `repo/`:

```bash
export PATH="$HOME/.pixi/bin:$PATH"
/usr/bin/time -v -o ../scratch/reference-cache-experiment/driver.time \
  pixi run --locked uv run --frozen --project genesis_tools python \
  ../scratch/reference-cache-experiment/experiment.py \
  > ../scratch/reference-cache-experiment/driver.stdout \
  2> ../scratch/reference-cache-experiment/driver.stderr
experiment_exit=$?
printf '%s\n' "$experiment_exit" > ../scratch/reference-cache-experiment/driver.exit
```

The driver uses the **unchanged `repo/main.nf`**, real Docker tools, no stubs, and the existing `local,test,docker` profiles. It keeps a small HTTP server alive for the fixed synthetic read file, using the same host-gateway fixture-serving arrangement as upstream tests. It shuts the server down at completion. No genome downloads occur. The temporary config contains only executor limits (four total CPUs/8 GB), the invoking Docker UID/GID and host-gateway mapping; task caps come from the existing test profile. No aligner, MAPQ, duplicate, SPP, trimming or peak options are overridden.

Each phase records its exact argument vector, working directory, SHA and environment overrides in `phases/<phase>/command.json`. Representative command, executed in `scratch/reference-cache-experiment/launch/`:

```text
nextflow -log <phase>/nextflow.log run <workspace>/repo/main.nf
  -profile local,test,docker
  --input <experiment>/samples.tsv
  --references <experiment>/references
  --workspace <experiment>/workspace --run_name cache_probe
  -work-dir <experiment>/work -c <experiment>/limits.config
  -with-trace <phase>/trace.tsv -ansi-log false -resume
```

The initial build has no explicit `-resume`. Phase 06 instead uses fresh `fresh-launch/`, `fresh-work/` and `fresh-workspace/` directories, with the same active B reference directory and same sheet/reads; no explicit resume flag is passed. Configured default resume has no history there and is ignored with a warning. All other later phases share the original launch/history/work/reference arrangement. `NXF_OFFLINE=true` and `NXF_DISABLE_CHECK_LATEST=true` match the prior baseline setup.

Each phase retains complete stdout/stderr, Nextflow log, trace, GNU-time output, input sheet copy, before/after reference-file copies with SHA256/size/mtime manifests, a published-output snapshot, BAM readback results and warning observations. The driver exits 0; all ten workflow phases exit 0. These successful exits describe execution, **not reference correctness**.

## Observed phase sequence

`C` = COMPLETED; `K` = CACHED. Initial eight tasks are VALIDATE_SHEET, DOWNLOAD, CHROM_SIZES, BWA_MEM2_INDEX, METADATA, BWA_MEM2_ALIGN, QC and TRACKS. When reference products are reused, only the other six tasks appear.

| Phase / scenario | Task result | Size/index tasks run? | Actual FASTA bases | Metadata/BAM reference | Mapped reads / witness reads |
|---|---|---|---:|---|---:|
| 00 A build | 8 C | Both | 100,000 | chr1; 100,000 | 9,900 / 0 |
| 01 A first resume, reference paths transition to published cache | 5 C + 1 K | Neither | 100,000 | chr1; 100,000 | 9,900 / 0 |
| 02 A stable resume | 6 K | Neither | 100,000 | chr1; 100,000 | 9,900 / 0 |
| 03 A same bytes, changed mtime | 6 K | Neither | 100,000 | chr1; 100,000 | 9,900 / 0 |
| 04 B changed contents, same filename | 6 K | **Neither** | **110,000** | **chr1 only; 100,000** | **9,900 / 0** |
| 05 B same bytes, changed mtime | 6 K | **Neither** | **110,000** | **chr1 only; 100,000** | **9,900 / 0** |
| 06 B, fresh task cache, same stale reference-product directory | 6 C | **Neither** | **110,000** | **chr1 only; 100,000** | **9,900 / 0** |
| 07 Identical B bytes, changed basename to renamed.fa.gz | 8 C | **Both** | 110,000 | chr1 + chr_added; 110,000 | **10,000 / 100** |
| 08 Renamed B first resume | 5 C + 1 K | Neither | 110,000 | chr1 + chr_added; 110,000 | 10,000 / 100 |
| 09 Renamed B stable resume | 6 K | Neither | 110,000 | chr1 + chr_added; 110,000 | 10,000 / 100 |

### Did chromosome sizes regenerate?

**No** for same-name B. `synthetic.chrom.sizes` remained exactly `chr1<TAB>100000`. Its SHA256 and mtime remained identical to A in every phase, including after B's rename (when it becomes an unused old product). There were no CHROM_SIZES tasks in phases 03–06. Renamed B created a separate `renamed.chrom.sizes` with `chr1 100000` and `chr_added 10000`.

### Did the bwa-mem2 index regenerate?

**No** for same-name B. All five original `synthetic.bwa-mem2/genome*` artifacts retained their exact A hashes and mtimes across all ten phases. The `.ann` header remained `100000 1 11` (total bases 100,000, one sequence). Renamed B generated five new artifacts under `renamed.bwa-mem2`, with `.ann` header `110000 2 11`. BAM sequence dictionaries and witness counts independently confirm which reference was actually used for alignment, rather than relying only on filenames or task statuses.

### Did Nextflow see a changed input?

**No task-cache invalidation was observed for edits to the existing FASTA in this implemented workflow.** VALIDATE_SHEET hash stayed `7b/e4f305` and remained CACHED through stable A, A's mtime change, B content replacement and B's mtime change. All other six-task-lineage hashes/statuses also remained cached. The snapshots prove the active FASTA bytes changed from A to B even though the effective task inputs did not invalidate.

This conclusion is scoped to this DAG and these paths; it is not a claim that Nextflow universally ignores direct FASTA `path` inputs. `VALIDATE_SHEET` receives the reference **directory**, while the derived-file reuse branches choose existing products before the FASTA can reach CHROM_SIZES/BWA_MEM2_INDEX. Downstream metadata/alignment then receive the old sizes/index, not an explicit content digest of the active FASTA. The observed dependency graph provides no effective content-change guard here.

Rename changed both the basename used for derived-cache lookup and the sample sheet reference field. It therefore invalidated relevant inputs and selected missing-product branches. This test does not isolate a filesystem rename from the necessary sheet update; both are part of a valid changed-filename invocation.

### Can it produce new outputs using stale reference products?

**Yes.** Phase 06 has new task/history/work/output directories. All six tasks execute afresh, including validation, metadata and BWA alignment. Neither reference task runs because the old nonempty products exist. The new metadata says 100,000 despite B's 110,000 bases; the new BAM dictionary omits chr_added; the 100 witness reads remain unmapped and are absent from the retained primary BAM. New QC and coverage products are also produced. This rules out an explanation limited to replaying old BAM/output files.

Renamed B then maps all 100 witnesses using **the same fixed read bytes**, providing a positive control for witness alignability and showing that their absence in phase 06 was caused by stale reference identity rather than unsuitable reads.

### Was a warning generated?

There was **no warning or error identifying a stale reference, FASTA/index mismatch or missing reference provenance**. Same-name B phases 04/05 completed with all tasks cached and no such diagnostic. Fresh-task-cache B also completed without any reference-mismatch warning.

Other diagnostics are preserved, not hidden: initial-history resume warnings in phases 00/06, and the previously observed Matplotlib cache-directory permission/fallback diagnostics in real TRACKS executions (six permission messages each in phases 00/01/06/07/08; thirty total). Cached phases emit no new task diagnostics. Complete raw logs are retained; keyword indexes can include benign matches on the scenario name containing “stale,” which are not reference-validation warnings. No warning was suppressed or configuration changed to remove it.

## Scenario assessment and proposed remediation

These are interpretations and recommendations; **none was implemented**.

| Scenario | Expected scientifically correct behavior | Observed behavior | Severity | Recommended remediation |
|---|---|---|---|---|
| A initial build and stable resume | Derive from A; associate products with A's identity; reuse unchanged inputs | Correct A products and witness result; stable all 6 cached | Informational | Retain baseline regression and add verifiable reference provenance |
| Same contents, changed mtime (A) | Safe content-validated reuse; no need to rebuild biological products | Exact products reused, all 6 cached | Low for this case | Prefer content identity over incidental timestamps; record that identity |
| Changed contents, same filename (A→B) | Reject a provenance mismatch or regenerate B products and invalidate dependent results | Old size/index unchanged, validation cached, chr_added absent, all 6 tasks cached, no warning | **HIGH: silent scientific data-integrity failure** | Check FASTA identity against a derived-product manifest before either reuse branch; fail clearly on mismatch or perform an explicitly recorded rebuild |
| Same B contents, changed mtime after stale replacement | A-vs-B content mismatch must remain detectable regardless of mtime | Stale products and all cached outputs persist | **HIGH inherited stale state** | Do not treat touching the FASTA as invalidation/remediation; propagate a reference content identifier |
| Fresh task cache with same B filename and old reference products | Starting new computation must not authorize stale reference products | Six new tasks compute with A products against a B-named input | **HIGH: fresh work directory does not protect correctness** | Validate external reference caches independently of Nextflow's task cache; record index manifest/checksums and make reference identity a task input |
| Changed filename, identical B contents | Correct B products; digest-validated reuse would also be acceptable | New stem triggers both builders; metadata 110,000; all 100 witnesses mapped | Informational correctness; avoidable duplication | Use content-addressed products or digest-validated aliases rather than stem/existence alone; guard stem collisions |
| Renamed B stable resume | Correct B products reused consistently | All6 cached; correct dictionary/witness result | Informational | Preserve this as positive-control regression |

A proposed reference manifest should bind declared assembly/source identity to actual FASTA bytes (and optionally a canonical sequence/contig digest), ordered contig lengths, index-tool version/build, indexing parameters and each artifact's checksum. A cache entry with no trustworthy manifest should not be silently accepted as matching a new FASTA. The reference identifier should participate in downstream task inputs/cache keys, not merely live in an audit sidecar. Exact policy for explicit rebuild versus fail-fast should be designed separately.

Keeping the old derived directory while changing only the work directory is demonstrably insufficient. Changing the filename happened to obtain correct products in this fixture; that is an observation, **not a general recommended repair**, since another basename can also collide with pre-existing stale products. No commands to remove or rebuild real references were issued.

## Checksums: exact test references and all derived artifacts

FASTA payload hashes include the exact headers and line breaks used in this experiment, not only nucleotide letters. Full before/after manifests additionally record every file's size and nanosecond mtime in each phase.

| Input | Compressed SHA256 | Decompressed SHA256 |
|---|---|---|
| A (chr1=100,000) | `d02363a2ac2351674a1defd84706d4abef1a64cc344e8b32bda205aba77b55b6` | `922ab2bfa1ba235cc97aa3d668ecec282458caced75c2abdc52880dff77b3b17` |
| B (chr1=100,000; chr_added=10,000) | `94323997aac65f361b7f9a85124f44f6a9350ea4785b3dc1c972a93327bd2bc2` | `929a21fc826fda0ea91a4639362a23c00f38866f47b938f221272411a3c191f1` |
| Fixed probe FASTQ, 10,000 reads | `1d49730e76e0ebf5d02adcc91a54240b2bbd3faa067a659d6d0f0d166e769704` | `be516d1521755bc04e9dcaaae193f8bd4294a40be8d0adb6bc955469a991cbad` |

| Derived artifact | SHA256 |
|---|---|
| `synthetic.bwa-mem2/genome.0123` | `897280a1624327f60e03118dbd32ed3ae413dabb77c301056d4b1c9fb18beab0` |
| `synthetic.bwa-mem2/genome.amb` | `4a041147801b23f396335bab2bcd1fe70a7fa4bd31a922192faf0c3850200fef` |
| `synthetic.bwa-mem2/genome.ann` | `e4295a5513006c56310eebf15990713c7255d92061ae126bd596a32c8b03b0a8` |
| `synthetic.bwa-mem2/genome.bwt.2bit.64` | `b7ce3c31ed4ab77ea3e8e6973ba7d52ebbd528852e683a5465bac6bb94e2a88a` |
| `synthetic.bwa-mem2/genome.pac` | `240edd662f7b260429bd96340df0806140657394aa2e53650fb2df34cf7c1e7c` |
| `synthetic.chrom.sizes` | `be2bafddea8604ce4b184d5eafce7387da6f3423d19113f348ffda9e8b1ab15f` |
| `renamed.bwa-mem2/genome.0123` | `96c7e8797c53c366addebcc99b514a38f4362d927cd9b133d395184540941ee6` |
| `renamed.bwa-mem2/genome.amb` | `1e2e69bab623b88798c248b3680fe79d630c354877b01309cffe334b52783c93` |
| `renamed.bwa-mem2/genome.ann` | `83d375c1754e0712bcbd55f0d19b025958eed754ffac8c855833cf911d417164` |
| `renamed.bwa-mem2/genome.bwt.2bit.64` | `de67b985eb040f3c45f6acd6dcc068bade3c440908264f5ca9f2b6ca78dccc7c` |
| `renamed.bwa-mem2/genome.pac` | `f2fb2c9092847a43be817649685525a0cc18f9477a10e7f25e3a7f5e2cda5bc9` |
| `renamed.chrom.sizes` | `0beaaccac0eae4df33d0d75a66d17d887e508603953017c770b4d2dee16e307c` |

## Resource and software provenance

| Phase | Wall time (GNU time) | Peak driver/JVM RSS, KiB | Exit |
|---|---:|---:|---:|
| `00_A_build` | 0:23.29 | 616808 | 0 |
| `01_A_path_transition` | 0:21.31 | 634144 | 0 |
| `02_A_stable` | 0:06.33 | 618936 | 0 |
| `03_A_same_bytes_new_mtime` | 0:06.30 | 696164 | 0 |
| `04_B_changed_bytes_same_name` | 0:06.45 | 620368 | 0 |
| `05_B_same_bytes_new_mtime` | 0:06.25 | 623784 | 0 |
| `06_B_fresh_task_cache_stale_reference_cache` | 0:21.33 | 617004 | 0 |
| `07_B_same_bytes_new_filename` | 0:21.60 | 671592 | 0 |
| `08_B_renamed_path_transition` | 0:21.53 | 599428 | 0 |
| `09_B_renamed_stable` | 0:06.14 | 622292 | 0 |

GNU time does not measure aggregate Docker-daemon/container memory. Per-task trace metrics are retained. These tiny sequential runs test semantics; timings are not throughput benchmarks. Runner versions are Pixi 0.70.1, uv 0.11.33, CPython 3.14.5, Nextflow 25.10.4 build 11173 on project OpenJDK 23.0.2-internal, plugins nf-schema 2.4.2/nf-dotenv 1.0.0, Docker 29.1.3 linux/amd64. Host audit parsing used existing Python 3.12.12; BAM readback used project pysam 0.24.1.

The same immutable images as audit03 were inspected locally again. BWA package metadata reports 2.3 (`he70b90d_0`) while its executable prints 2.2.1; samtools/htslib are 1.24, deepTools 3.5.6, R 4.4.3 with spp 1.16.0. Preserve the package/executable version distinction documented in audit03. No image was rebuilt or substituted.

| Image | Exact immutable reference | Platform |
|---|---|---|
| `kundajelab/dap_seq_alignment` | `kundajelab/dap_seq_alignment@sha256:4764008ba8fbb5d831bd6f9ed6a720fd494062b39f0bae63ff2e4efd316ad842` | linux/amd64 |
| `kundajelab/dap_seq_tracks` | `kundajelab/dap_seq_tracks@sha256:e6dd6ceb79e50fc6db83e9346a920e51fd2bf0dcffbc18c9305b1b6e8c806390` | linux/amd64 |
| `kundajelab/dap_seq_qc` | `kundajelab/dap_seq_qc@sha256:ace177a497934a26adb305bc0dc92cc6a447fe8ca714b79f72a007c7acb53239` | linux/amd64 |
| `kundajelab/dap_seq_peaks` | `kundajelab/dap_seq_peaks@sha256:10467dd29e3d25ce7769f76f57402bd1a5a582006e911d06479bfcc3e3325df3` | linux/amd64; configured but unused |
| `kundajelab/genesis_tools` | `kundajelab/genesis_tools@sha256:31458d4a6a83541f463ea4b0e692a0afc65c6df441f70c3f71fc4ccf1a11eb59` | linux/amd64 |

## Acceptance and scope

- **Deterministic fixture: PASS.** Both FASTAs re-generated in memory to the same compressed hashes; fixed gzip metadata, seeds, interpreter and read hashes are recorded.
- **Empirical cache reproduction: PASS.** Ten unmodified workflow runs; direct before/after hashes/mtimes, actual task traces, index annotations, BAM dictionaries and named-read counts agree. All original A-derived hashes/mtimes remained unchanged in every phase. Run success did not imply reference correctness.
- **Safety/scope: PASS.** Every `--references` argument and every run/work/output directory resolves under this experiment's scratch root. Only generated synthetic references were replaced, touched or renamed. Source SHA and all 73 tracked files remain unchanged; Git working tree is clean. The local branch name changed deliberately; no source commit was made.
- **Scientific correctness: FAIL for same-name content replacement**, including fresh task-cache execution; no stale-reference warning was issued.
- **Limits:** one small SE fixture, one added-contig content change and a previously unused new basename. Same-length substitutions, all possible file-metadata adversarial edits, basename collisions, concurrent writers, corrupt indexes, real assemblies and official reference-pipeline comparisons were not tested. No biological thresholds or general-purpose repair were inferred.

Evidence root: [scratch/reference-cache-experiment](../scratch/reference-cache-experiment/). `fixture-provenance.json`, `empirical-review.json`, `scope-and-invariants.json`, `deterministic-reference-check.json` and each phase's snapshots/logs contain raw observations. Interpretation and proposed remediation are separated above. `evidence-manifest.json` supplies artifact SHA256 values; `final-acceptance.json` records final Git/source verification.

Files created: this audit, the scratch-only experiment driver/config/fixtures, and retained reference, task, output and log snapshots. The upstream branch was created at the unchanged baseline SHA; no production files, tests, dependencies or real references changed. No fixes were made. Stop after reporting.
