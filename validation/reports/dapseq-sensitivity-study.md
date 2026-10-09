# Controlled DAP-seq sensitivity study

Date: 2026-10-07. **Computational fixture study completed; no production default changes.** The user explicitly selected retained fixtures and requested that biological limits be documented. These results support configurable sensitivity experiments, not a biological recommendation to discard ambiguous or duplicate reads.

Genesis SHA: `af0bbfb50806babd78b8e9f88df2a55aab0a2a13`. Dedicated local branch: `validation/dapseq-sensitivity`; repository remains clean. No source, production tests, dependency manifests, credentials, Docker configuration or original inputs were changed. No push, sudo, new reference download, biological replicate pooling or trimming was performed.

## Subset and scope

The retained deterministic fixture at `results/multiqc/runs/docker-xbuym0la` contains three treatments and two controls:

| Library | Layout | Raw reads / pairs | Control |
|---|---|---:|---|
| se_treatment | SE | 32,000 reads | se_control |
| se_second | SE | 32,000 reads | se_control |
| se_control | SE | 6,000 reads | none |
| pe_treatment | PE | 32,000 pairs / 64,000 read ends | pe_control |
| pe_control | PE | 6,000 pairs / 12,000 read ends | none |

The SE control is reused unchanged within each policy branch; it is never pooled or counted twice in branch resource totals. All libraries are kept separate. The synthetic 2 Mb chr1 reference, 75-base reads, approximately 200 enriched treatment loci and 160–200 bp PE fragments come from `repo/tests/verify_pipeline.py:301` (seed 60141), with an exact repeated genomic block to produce MAPQ 0 alignments. These are layout/enrichment/repeat test cases, **not real DAP-seq targets or a realistic spectrum of sequencing errors/PCR effects**. Real Sorghum evaluation still requires its exact reference (audit/05); no synthetic FASTA is represented as that assembly.

Input paths and SHA256 values for all 15 original BAM representations, raw FASTQs and reference files are in [preflight.json](../results/dapseq-sensitivity/preflight.json). Every original input was rehashed unchanged at completion. The existing alignments were reused, not realigned: this isolates post-alignment policy effects and excludes download/index/alignment cost from the timings.

## Experimental design

The full **3 × 3 factorial matrix** has nine branches, five libraries per branch, and 27 treatment/control peak analyses. [experiment-matrix.tsv](../results/dapseq-sensitivity/experiment-matrix.tsv) records every cell.

| Factor | Levels | Fixed interpretation |
|---|---|---|
| A: MAPQ | No cutoff (current), >=10, >=30 | Apply equally to treatment and corresponding control. For PE primary analysis, retain a fragment only when both mates pass; count and report any reads removed for pair completeness. |
| B: duplicates | Original retained; marked but retained; marked duplicates excluded | Picard MarkDuplicates labels full original BAMs before MAPQ selection. Both removal switches are false during marking. Exclusion occurs only when creating experiment-owned branch BAMs. |
| C: SPP | Current independently aligned first 50 bases of R1 | Apply the same branch cutoff/duplicate policy separately to that representation. Add a baseline-only full-75-bp R1 diagnostic, using the existing independent full-R1 alignment. |
| D: preprocessing | Full original reads | FastQC adapter evidence determines whether a trimming arm is warranted. No trimming arm was warranted here. |

SPP50 duplicate marking is **single-end R1 endpoint marking**, including for PE libraries; main PE duplication is fragment-pair marking. Thus the same policy label does not imply the same retained population in SPP and primary analysis. Both populations/counts are reported in library-metrics.tsv. No trimmed SPP read is fed to primary alignment, tracks, peaks or quantification. Full-75 SPP changes only the QC representation; all primary outcomes are the baseline by construction and are not redundantly rerun.

These are explicitly **MAPQ/duplicate/SPP sensitivity experiments**, not bug fixes. No MAPQ filter, duplicate exclusion or read-length change is proposed as a production correction.

### Important pre-existing downstream behavior

“Current retained reads” describes Genesis BAM retention, **not an end-to-end absence of duplicate handling**. Genesis invokes MACS3 without `--keep-dup`; MACS3 3.0.5 defaults to `--keep-dup=1`. We preserve that default in every branch to isolate the requested BAM-policy changes. Baseline PE logs show 32,000 treatment fragments entering MACS3 and 31,655 after its internal redundancy filter. The duplicate-excluded branch enters with those 31,655 fragments. The unchanged caller explains why duplicate removal can change quantification without changing peaks. This is directly observed in the retained logs and consistent with the [MACS3 callpeak documentation](https://macs3-project.github.io/MACS/docs/callpeak.html). It is not evidence that duplicate handling never matters.

Quantification uses the unmodified Genesis CLI with `--weighting primary`, independently counting retained primary read ends (including MAPQ 0 and duplicate flags unless the records were explicitly excluded). Coverage is regenerated with the same `bamCoverage --binSize 1 --normalizeUsing RPKM --exactScaling` recipe. No tracks are used as a substitute for counts.

## Metric definitions

- **Retained mapped reads/fragments:** read ends in each branch primary BAM; PE fragment counts require both mates, SE “fragments” are read observations because true insert lengths cannot be inferred. No orphan was introduced or additionally removed in this fixture: both mates' eligibility agreed in every PE case.
- **Mapping fraction:** raw alignment mapping fraction is original retained primary ends / known raw FASTQ ends (1.0 for these error-free fixtures). `retention_mapping_fraction` is branch retained ends / that same raw denominator. Filtering does not change where reads originally mapped; it changes retention. These are not interchangeable metrics, and original Genesis BAMs alone would not recover a general raw mapping rate.
- **MAPQ distribution:** every observed integer MAPQ and read-end count, separately for primary and SPP50, without invented bins or thresholds. Duplicate fraction is Picard-labeled retained ends / retained ends; original unset duplicate flags are also reported separately. For complete PE pairs the pair fraction equals the end fraction here. Optical duplication cannot be inferred from the synthetic `readN` identifiers.
- **SPP:** raw NSC, RSC, fragment-shift estimates, read count and tool status are retained. NSC uses fragment-peak correlation / minimum correlation; RSC uses (fragment minus minimum) / (phantom minus minimum). No human ChIP/ATAC quality classifications are adopted. See the [upstream SPP descriptions](https://github.com/kundajelab/phantompeakqualtools/blob/master/README.md) and the pinned vendored script.
- **Peak widths:** half-open BED end minus start, with min/median/max and all per-peak widths. Genome-wide peak Jaccard is merged interval intersection bp / union bp. Overlap count uses any positive overlap with a baseline peak; all coordinates in this fixture are chr1.
- **Peak ranking:** tie-aware Spearman of narrowPeak column 9, the reported -log10(q), on reciprocal maximum-overlap matches. Coordinate order breaks equal-overlap ties deterministically. Matched count is reported; all comparisons matched all 200 baseline peaks. No arbitrary overlap-percent cutoff was introduced.
- **Enrichment analogue:** read-end FRiP counts each retained alignment once if its reference span intersects the union of peaks by at least one bp. PE fragment FRiP instead counts each complete fragment once using its template span. SE fragment FRiP is explicitly the read-span analogue. Both branch-own and fixed-baseline peak unions are reported; overlap with multiple peaks cannot double-count the numerator. These measure concentration in selected intervals, not independent predictive accuracy.
- **Quantification:** rerun Genesis RPM and mean coverage RPKM on both branch-own peaks and the fixed 200 baseline intervals. Pearson and tie-aware Spearman on **fixed regions** avoid changing-region confounding. Independent BAM-span counts reproduce fixed-region RPM in all 27 cases. Also report absolute effect sizes because near-constant fixture peak counts make correlations unstable. Machine-precision Pearson values slightly above 1 are retained as arithmetic roundoff, not interpreted as super-unit correlation.
- **Runtime/disk:** elapsed command wall time includes Docker/Pixi startup. Per-branch totals sum analysis command time, counting control SPP once. Two jobs run concurrently, so summed time is not campaign elapsed time. Branch disk totals are retained logical bytes, not disk I/O or temporary high-water usage. Marking/filtering/common inputs are separate costs.

## Raw results

All 27 treatment analyses called **200 peaks**. Marked-but-retained branches reproduce their same-MAPQ unmarked counterparts byte-for-byte for narrowPeak, coverage, own/fixed RPM and RPKM, and SPP numeric output. This checks actual payloads, not just peak counts.

The baseline recreated the retained upstream-style fixture outputs exactly: narrowPeak decompressed bytes and both published quantification files match for all three treatments. SPP numeric fields also match for all five libraries. [baseline-comparison.json](../results/dapseq-sensitivity/baseline-comparison.json), [spp-baseline-comparison.json](../results/dapseq-sensitivity/spp-baseline-comparison.json), and [marked-retained-comparison.json](../results/dapseq-sensitivity/marked-retained-comparison.json) preserve these checks.

### Primary sensitivity results

The table shows the distinct unmarked/excluded outcomes. All nine branches are in [treatment-summary.tsv](../results/dapseq-sensitivity/treatment-summary.tsv). Marked-retained results equal retained; MAPQ30 equals MAPQ10 in **every primary/SPP BAM and biological output payload**.

| Treatment | Branch | Retained read ends | Peaks | Median width bp | Peak Jaccard | Peak-rank rho | Fixed RPM rho | Fixed RPKM rho | Fixed fragment/read-span FRiP |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| pe_treatment | mapq0-retained | 64000 | 200 | 299 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.940656 |
| pe_treatment | mapq0-excluded | 63310 | 200 | 299 | 1.000000 | 1.000000 | 0.357925 | 0.936244 | 0.940009 |
| pe_treatment | mapq10-retained | 63798 | 200 | 298 | 0.997402 | 0.995168 | 1.000000 | 0.999997 | 0.943635 |
| pe_treatment | mapq10-excluded | 63108 | 200 | 298 | 0.997402 | 0.995168 | 0.357925 | 0.936244 | 0.943018 |
| se_second | mapq0-retained | 32000 | 200 | 279 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.939969 |
| se_second | mapq0-excluded | 25885 | 200 | 279 | 1.000000 | 1.000000 | 0.103745 | 0.536893 | 0.926019 |
| se_second | mapq10-retained | 31900 | 200 | 279 | 0.999729 | 0.983288 | 1.000000 | 1.000000 | 0.942915 |
| se_second | mapq10-excluded | 25789 | 200 | 279 | 0.999729 | 0.983288 | 0.103745 | 0.536893 | 0.929466 |
| se_treatment | mapq0-retained | 32000 | 200 | 279 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.939906 |
| se_treatment | mapq0-excluded | 25936 | 200 | 279 | 1.000000 | 1.000000 | 0.084478 | 0.475401 | 0.925972 |
| se_treatment | mapq10-retained | 31899 | 200 | 279 | 0.999621 | 0.983608 | 1.000000 | 0.999999 | 0.942882 |
| se_treatment | mapq10-excluded | 25837 | 200 | 279 | 0.999621 | 0.983608 | 0.084478 | 0.475431 | 0.929520 |

MAPQ filtering removes 100/101 SE treatment reads, 101 PE treatment pairs, 102 SE control reads and 105 PE control pairs. The affected proportions differ between treatment and control; both are filtered symmetrically. MAPQ0 is the only observed class below 30. Other primary values are 40, 55, 57 and 60; therefore **this dataset cannot distinguish a threshold of 10 from 30**. That equivalence is a property of these inputs, not a general finding about MAPQ policy.

Without a MAPQ cutoff, duplicate exclusion removes 6,064/32,000 SE treatment records (18.95%), 6,115/32,000 SE-second records (19.109375%), and 345/32,000 PE treatment pairs (1.078125%). It removes five SE control records and zero PE control pairs. Raw input mapping remains 100%; post-policy retention decreases. BAM duplicate-flag fractions of zero in the retained branch do not mean zero measured endpoint redundancy.

### Quantification effect sizes and interpretation

| Treatment | Baseline RPM coefficient of variation | Duplicate exclusion: median absolute RPM change | Maximum absolute RPM change |
|---|---:|---:|---:|
| pe_treatment | 0.003791 | 0.418% | 4.302% |
| se_second | 0.004039 | 2.196% | 10.991% |
| se_treatment | 0.003972 | 2.136% | 9.521% |

Fixed-region baseline RPM ranges only from 4,687.5 to 4,750–4,781.25, because the generator assigns nearly equal read counts to every enriched locus. Consequently, the low RPM correlations after exclusion describe reordering of a very narrow distribution; they do **not** establish a comparable biological loss of signal. Absolute changes and [quantification-effects.tsv](../results/dapseq-sensitivity/quantification-effects.tsv) must accompany those correlations. MAPQ filtering alone leaves fixed-region RPM rank unchanged and raises RPM by approximately 0.313–0.317% through its reduced library-size denominator. A higher conditional FRiP after filtering is likewise not proof of improved biological quality.

### SPP read-length and duplicate sensitivity

The production first-50-bp behavior exists because the code's documented failure mode is a read-length phantom peak obscuring the fragment peak when full reads approach fragment length (`repo/modules/bwa_mem2_align.nf` and `qc.nf`). It applies only to the R1 alignment consumed by SPP; primary full reads remain untouched. The full-75 alternative here is scientifically interpretable as a diagnostic because it uses the same original R1 sequences/reference and a fixture with known fragment generation. It does not validate full reads for all real DAP-seq libraries or reproduce the harder read-length≈fragment-length regime.

| Library | Current 50bp NSC | Current 50bp RSC | Full75 NSC | Full75 RSC | Leading shift 50 / 75 |
|---|---:|---:|---:|---:|---|
| se_control | 1.52381 | -7.333333 | 1.52381 | 7.333333 | 128 / 128 |
| pe_treatment | 468.5556 | 6.264702 | 468.5556 | 2.944305 | 180 / 180 |
| se_second | 391.1296 | 6.621719 | 391.1296 | 2.975565 | 180 / 180 |
| se_treatment | 453.5054 | 6.503323 | 453.5054 | 2.908494 | 182 / 182 |
| pe_control | 1.512821 | 8.489226e+14 | 1.512821 | 1.111111 | 224 / 224 |

The leading treatment estimates stay 180–182 bp and NSC is unchanged, while RSC roughly halves in the full75 diagnostic. This is consistent with its dependence on the read-length-associated phantom peak; it is not evidence that the unchanged primary data became worse.

Raw control values expose a numerical/interpretive failure mode: baseline PE control RSC is `8.489226e+14`, with phantom and minimum correlations both printed as `0.004307489`, so its denominator is near zero at floating precision. SE control RSC is `-7.333333` because its phantom correlation is below the recorded minimum-shift correlation. These values are preserved, not coerced to zero or labeled biological passes. The SPP tool exited successfully and even emitted its own QualityTag in some cases; neither is adopted as a DAP-seq acceptance criterion.

Duplicate exclusion on the separately marked SPP50 single-R1 representation changes treatment NSC to 341.4615 (PE), 285.9785 (SE second), and 404.0152 (SE treatment), while leading shifts remain 180/180/182. This includes removal of single-end redundancy even when primary PE fragment duplication is much lower. It must not be interpreted as an effect of removing only the 345 PE duplicate fragments. All nine branches and both controls remain in [spp.tsv](../results/dapseq-sensitivity/spp.tsv).

### Adapter and motif evidence

All seven FastQC ZIPs contain an Adapter Content module with maximum reported adapter percentage **0.0**, PASS status and no overrepresented-sequence rows. [adapter-evidence.tsv](../results/dapseq-sensitivity/adapter-evidence.tsv) records the evidence. No trimming was tested: there is no adapter-positive case here. This does not demonstrate that real DAP-seq libraries never need adapter removal; trimming sensitivity remains conditional on actual adapter evidence. Raw FASTQs remain byte-identical.

Motif QC is **NOT APPLICABLE to these fixtures**: there are enough artificial peaks, but no known TF target, TF family or planted binding motif. The reference is random sequence and the enriched coordinates were chosen without motif biology. Running a discovery program and retrospectively assigning a TF would be misleading. No existing fast-motif proposal was found in this workspace's audit/design/reports. [motif-status.tsv](../results/dapseq-sensitivity/motif-status.tsv) records the missing TF identity for each treatment; no motif program failure or absence is used to call a dataset bad.

For a future exact-reference real-data study, a reasonable fast candidate is [STREME](https://meme-suite.org/meme/doc/streme.html): use identically defined peak windows, reproducible ranking/tie handling, a fixed seed, declared background/control sequences, a held-out enrichment evaluation and a pinned plant motif-database release for TF-family comparison. Pin the executable/version before running it and preserve all motifs/scores, not only the expected match. That prospective protocol was **not run or validated** here. Motif-family enrichment would remain supportive evidence, with alternative explanations and failures reported rather than automatic quality rejection.

## Runtime, disk and reproducibility

| Branch | Sum of analysis command wall seconds | Retained branch bytes |
|---|---:|---:|
| mapq0-retained | 39.99 | 9888277 |
| mapq0-marked | 40.51 | 10045891 |
| mapq0-excluded | 34.54 | 9582548 |
| mapq10-retained | 36.04 | 9906955 |
| mapq10-marked | 41.18 | 10060894 |
| mapq10-excluded | 44.71 | 9520690 |
| mapq30-retained | 36.29 | 9906957 |
| mapq30-marked | 34.42 | 10060891 |
| mapq30-excluded | 33.82 | 9520691 |

These are single-run observations under two-job concurrency, not a benchmark demonstrating speed differences. They include primary peak calling, RPKM coverage, own/fixed quantification, and five SPP calls per branch. They exclude common original alignment generation, shared marking preparation (33.80 summed seconds), branch construction (11.59 s), and independent summary verification (101.07 s, 117,496 KiB GNU-time max RSS). Full75 SPP costs are separately logged. All 172 tool invocations span approximately 5 min 21 s including investigator/setup gaps; summed invocation wall time is 394.45 s. No end-to-end sequencing-to-peaks runtime claim follows from these values.

Observed per-command wall ranges: MACS3 1.17–2.70 s; coverage 2.76–4.43 s; quantification 1.08–3.26 s; SPP 2.35–4.56 s; Picard marking 3.08–3.99 s. Docker cgroup peak memory maxima were respectively 51,372,032; 177,631,232; 27,009,024; and 263,503,872 bytes for MACS3, coverage, quantification and SPP. Cgroup values include page cache and subprocesses, unlike GNU-time process RSS. Picard host peak RSS and CPU/I/O counters are in each mark command's time.txt. Container io.stat is retained where exposed by the host. Peak RAM for the initial Python branch-construction helper was not measured. The complete study evidence is approximately 96 MB logical bytes before final report/checksum additions; branch logical sizes are not peak scratch space.

Environment: Pixi 0.70.1, project CPython 3.14.5, pysam 0.24.1 / HTSlib 1.24; prior locked Picard environment Picard 3.5.0, Java 17.0.18-internal, samtools 1.24. Picard uses `-Xms128m -Xmx2g -XX:ActiveProcessorCount=2`; its lock SHA256 is `0ed278ddff8f1a588fcf8d6bc9ae578ab27802f389baa7ba2214903c4b0a8fa9`. No dependency installation/change was needed. Docker 29.1.3, linux/amd64 images:

| Task | Image reference / resolved software |
|---|---|
| qc | `kundajelab/dap_seq_qc@sha256:ace177a497934a26adb305bc0dc92cc6a447fe8ca714b79f72a007c7acb53239` |
| peaks | `kundajelab/dap_seq_peaks@sha256:10467dd29e3d25ce7769f76f57402bd1a5a582006e911d06479bfcc3e3325df3` |
| tracks | `kundajelab/dap_seq_tracks@sha256:e6dd6ceb79e50fc6db83e9346a920e51fd2bf0dcffbc18c9305b1b6e8c806390` |
| tools | `kundajelab/genesis_tools@sha256:31458d4a6a83541f463ea4b0e692a0afc65c6df441f70c3f71fc4ccf1a11eb59` |

MACS3 3.0.5; deepTools 3.5.6; samtools 1.24; R SPP 1.16.0. Image IDs/platform and RepoDigests are in [images.json](../results/dapseq-sensitivity/images.json); exact version stdout/stderr is under `commands/versions-*`. The Genesis quantifier comes from the pinned project tools image and reproduced published baseline values. SPP script and original module hashes are recorded with every applicable invocation. Containers mount the workspace read-only with only this study's results directory writable, run as the current user, and are limited to two CPUs/4 GiB; no privileged mode or Docker configuration changes.

Reproduction entry points, run from the validation workspace (fresh experimental output directory required to preserve this evidence):

```bash
python scratch/dapseq-sensitivity/preflight.py
python scratch/dapseq-sensitivity/prepare.py
repo/genesis_tools/.venv/bin/python scratch/dapseq-sensitivity/filter_matrix.py
python scratch/dapseq-sensitivity/run_matrix.py
repo/genesis_tools/.venv/bin/python scratch/dapseq-sensitivity/summarize.py
python scratch/dapseq-sensitivity/add_evidence.py
python scratch/dapseq-sensitivity/quant_effects.py
python scratch/dapseq-sensitivity/verify.py
```

The locked project environment and prior isolated Picard environment must already exist; image acquisition, if needed elsewhere, must use the digest references above. No floating tool/container versions are required. Each actual invocation has exact argv, cwd, git SHA, input hashes, UTC timestamp, wall time, full stdout/stderr, exit code and GNU-time data under `results/dapseq-sensitivity/commands/<label>/`. [commands.tsv](../results/dapseq-sensitivity/commands.tsv) indexes these. `filter-provenance.json` captures Python filtering versions/inputs/order. Final [checksums.json](../results/dapseq-sensitivity/checksums.json) covers scripts, manifests, summaries and generated outputs.

## Recommendations — interpretation, not production edits

| Policy | Recommendation | Evidence and limits |
|---|---|---|
| MAPQ | **expose as configurable**, preserve current no-cutoff default | Filtering removes real ambiguous primary observations and changes denominators/control signal. It changes some peak boundaries/ranks here, but the fixture cannot discriminate 10 versus 30 or establish a biologically superior threshold. Record paired-fragment semantics explicitly. |
| Duplicates | **retain current** BAM retention; optional measurement remains useful | Flagging alone is neutral in all tested outputs. Exclusion changes quantification despite stable peaks; non-PCR endpoint collisions occur in this enriched synthetic design. No evidence justifies automatic removal. Separately document MACS3's existing keep-dup behavior; optimal real-data caller duplicate policy remains unresolved. |
| SPP first50 | **retain current** | Baseline reproduced; full75 was interpretable but altered RSC through its phantom denominator without changing primary analysis or leading treatment fragment estimates. Neither length is biologically validated by this fixture; raw ratios/curves need context. |
| Full-read preprocessing | **retain current** | No adapter evidence in any mate. A trimming arm without adapter-positive input would test an unsupported intervention. Revisit only with observed adapter evidence and explicitly labeled sensitivity results. |

No policy receives “change default.” Plant/DAP-seq QC thresholds remain **UNSPECIFIED**. Computational retention, overlap and correlation effects are measured; biological specificity, true target recovery, optimal MAPQ/deduplication and motif enrichment remain unresolved. Human ATAC thresholds were not imported.

## Acceptance, warnings and files

**Passed:** all nine branches, 45 library cases, 27 treatment peak/quantification cases, 45 SPP50 and five full75 SPP diagnostics completed. All 172 recorded invocations and all 50 underlying Rscript calls exited zero. Original inputs and workflow sources remain unchanged; recreated baseline and marked-retained equivalence passed at payload level. Independent RPM calculations, PE completeness, no remaining duplicate flags in excluded outputs, MAPQ10/30 equivalence and deterministic metric-helper checks passed. See [acceptance.json](../results/dapseq-sensitivity/acceptance.json).

**Warnings/ambiguity retained:** ten Picard optical read-name parsing warnings (one per representation) are in [warnings.tsv](../results/dapseq-sensitivity/warnings.tsv); optical-duplicate zeros are not validated. Successful SPP exits do not resolve negative/near-singular control RSC values. No command failure was patched, retried into invisibility, or converted into a biological judgment. No production test was weakened. Full pipeline checks were not rerun because no production source/dependency/test code changed; this report claims only the executed experiment and content checks.

**Files added:** this report; compact summary TSVs and raw evidence under `results/dapseq-sensitivity/`; standalone experiment scripts under `scratch/dapseq-sensitivity/`. The main summaries are treatment-summary.tsv, library-metrics.tsv, mapq-distributions.tsv, spp.tsv, peak-widths.tsv, quantification-effects.tsv and branch-resources.tsv. Controls do not receive treatment peak calls/quantification; their library/SPP metrics and one-per-branch cost are retained. No original audit or production file was modified. No commit or push was requested or performed for this experiment.
