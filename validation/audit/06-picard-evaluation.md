# Picard evaluation — experiment only

Date: 2026-10-07. Decision: **do not add Picard to the default Genesis workflow**. Duplicate measurement is the strongest optional addition; the other candidates are redundant or need further scientific validation. No production code, environment manifest, lock file, BAM, FASTQ, reference, alignment, peak, or publication behavior was changed. No duplicate reads were removed.

## Scope and reproducibility

Current tested Genesis SHA: `af0bbfb50806babd78b8e9f88df2a55aab0a2a13`, branch `validation/multiqc`; working tree clean before and after. Original upstream baseline: `4468c712e4c171b573e2ec2806fdc5327b5379e9`. This evaluates the current FastQC/MultiQC-enhanced local revision, not a claim that Picard existed upstream.

Four retained libraries from `results/multiqc/runs/docker-xbuym0la` were used intact, without subsampling, pooling, MAPQ filtering or rewriting. They represent SE/PE layouts, enriched treatment and control distributions, **not real biological DAP-seq**. The exact Sorghum reference remains unavailable, as documented in audit/05; no substitute was downloaded. `repo/tests/verify_pipeline.py:301` generates the deterministic synthetic reference/reads, with seed 60141, 75-base reads, 2 Mb chr1, repeated sequence, treatment enrichment and PE fragments 160–200 bp. Both SE/PE compressed reference payloads are identical; a decompressed experimental copy and new .fai/.dict were created only in `scratch/picard/`.

| Library | Layout | BAM records | MAPQ 0 | BAM bytes |
|---|---|---:|---:|---:|
| se_control | SE | 6000 | 102 | 196458 |
| pe_treatment | PE | 64000 | 202 | 1080803 |
| se_treatment | SE | 32000 | 101 | 421294 |
| pe_control | PE | 12000 | 210 | 449372 |

Input SHA256 evidence (full paths and byte sizes in [inputs-before.json](../results/picard/inputs-before.json); rehashed after all experiments):

| Input | SHA256 |
|---|---|
| se_control.primary.bam | `e3e16d6e2c1757320902c988084295663ff47d5fba21b1a72e4859d1da12cbea` |
| pe_treatment.primary.bam | `403dc9bc42d7e280bb7336c79aeb3c7d346ae7416315aded268ba22b64917c93` |
| se_treatment.primary.bam | `a4c591b5c8933bc9ebdba937df73be3ab4e9ed8178df8189551b8c2941fd003f` |
| pe_control.primary.bam | `02f3e55069160e1375ed47328f1ea58266f96ab1e597408894a4a4a67bb16598` |
| reference.fa | `6b5ce726d6c53717e39b6bdacd4dd2585617b2a65140be57b2369ff8898f4721` |
| se.fa.gz | `2d782d542015cbbdc7b5f5cf99a5e88526ddee1abd40caae68a83897bbc4d4a2` |
| pe.fa.gz | `bd0bde17c1b70378390fec3dde4da13d967bfc9b91987ef56c310e52c7bfb2c8` |

### Environment and commands

An isolated user-owned Pixi environment follows the repository's conda-forge/Bioconda + Pixi lock mechanism; it is not added to any Genesis environment. No sudo, system installation, production container rebuild or image push. Host Linux x86_64; experiment uses host Pixi, so a new container digest is **not applicable**. Provenance of the retained alignments is the existing alignment image `kundajelab/dap_seq_alignment@sha256:4764008ba8fbb5d831bd6f9ed6a720fd494062b39f0bae63ff2e4efd316ad842`.

| Component | Exact resolved version/build |
|---|---|
| Pixi | 0.70.1 |
| Picard | 3.5.0 / hdfd78af_0 |
| OpenJDK | 17.0.18 / h1602c4f_18; runtime 17.0.18-internal+0-adhoc.rattler.src |
| samtools | 1.24 / h9dcdb79_1 |
| HTSlib | 1.24 / ha79157c_0 |
| R | 4.4.3 / h502d0c9_11 |
| Retained FastQC / SPP | 0.12.1 / 1.16.0 |

Dependency manifests: [pixi.toml](../scratch/picard/environment/pixi.toml), [pixi.lock](../scratch/picard/environment/pixi.lock). Exact package URLs, builds and SHA256: [packages.json](../results/picard/packages.json). Lock SHA256: `0ed278ddff8f1a588fcf8d6bc9ae578ab27802f389baa7ba2214903c4b0a8fa9`. Java heap explicitly `-Xms128m -Xmx2g`; no CPU affinity/processor-count limit. Approximate installed environment disk footprint 1.6 GiB; experiment evidence 12 MiB. This footprint includes R, Java and dependencies, not just Picard.

Initial command: `pixi install --manifest-path scratch/picard/environment/pixi.toml` (installation logs retained; initial solve elapsed/RAM not captured). Subsequent locked reinstallation succeeded; its command, wall time and GNU time resources are in `results/picard/reinstall.{json,time,stdout,stderr}`. All analyses used `pixi run --locked --manifest-path ...`. This locks full transitive resolution, including the Java/R versions allowed by the experimental manifest.

For each input BAM, three sequential repetitions of:

```text
picard -Xms128m -Xmx2g CollectAlignmentSummaryMetrics I=BAM O=metrics.txt R=scratch/picard/reference.fa TMP_DIR=EXPERIMENT_TMP
picard -Xms128m -Xmx2g CollectInsertSizeMetrics I=BAM O=metrics.txt H=histogram.pdf TMP_DIR=EXPERIMENT_TMP
picard -Xms128m -Xmx2g MarkDuplicates I=BAM O=EXPERIMENT_ONLY.marked.bam M=metrics.txt REMOVE_DUPLICATES=false REMOVE_SEQUENCING_DUPLICATES=false TMP_DIR=EXPERIMENT_TMP
picard -Xms128m -Xmx2g EstimateLibraryComplexity I=BAM O=metrics.txt TMP_DIR=EXPERIMENT_TMP
samtools flagstat BAM
samtools stats BAM
samtools idxstats BAM
```

Every invocation has an exact expanded command, input SHA256, Genesis SHA, environment-lock SHA256, timestamps, elapsed time, output hashes, stdout, stderr, exit status and GNU time peak RSS/block-I/O in `results/picard/<label>/`. Scripts: [run_experiment.py](../scratch/picard/run_experiment.py), [native_benchmark.py](../scratch/picard/native_benchmark.py), [known_fixture.py](../scratch/picard/known_fixture.py). All duplicate-tool experiments are explicitly **duplicate-measurement sensitivity experiments**, not bug fixes or a proposed change to production duplicate handling. Picard's default insert-size exclusion of duplicate-flagged reads changes no membership here: all original duplicate flags are unset.

## Raw observations: costs

One additional native measurement per library/tool places `/usr/bin/time -v` **inside** Pixi, excluding the launcher. Values below are native wall seconds / maximum RSS MiB. Native timing resolution is 0.01 s; these small, warm-cache cases are not throughput or full-dataset capacity estimates. The three initial repeats include Pixi startup; their medians and raw observations are retained in [resources.json](../results/picard/resources.json). RSS is GNU time's maximum process/descendant RSS, not simultaneous summed Java+R memory. No production resource request is inferred from these measurements.

| Tool | SE control | SE treatment | PE control | PE treatment |
|---|---:|---:|---:|---:|
| CollectAlignmentSummaryMetrics | 1.27 / 181.7 | 1.20 / 287.6 | 2.25 / 265.0 | 1.49 / 310.8 |
| CollectInsertSizeMetrics | 1.20 / 152.1 | 1.39 / 299.0 | 2.29 / 305.4 | 2.07 / 316.4 |
| MarkDuplicates | 1.70 / 826.3 | 2.14 / 932.8 | 1.83 / 870.5 | 2.54 / 1027.9 |
| EstimateLibraryComplexity | 1.01 / 159.2 | 2.15 / 223.9 | 1.14 / 221.8 | 1.45 / 325.8 |
| samtools-flagstat | <0.01 / 3.6 | <0.01 / 3.6 | <0.01 / 3.6 | 0.01 / 3.8 |
| samtools-stats | 0.01 / 4.0 | 0.05 / 4.2 | 0.03 / 4.1 | 0.09 / 4.2 |
| samtools-idxstats | <0.01 / 3.5 | <0.01 / 3.5 | <0.01 / 3.5 | <0.01 / 3.5 |

Additional measured disk work, all four native runs:

| Tool | Kernel block reads | Kernel block writes, min–max | Retained tool output bytes, min–max | Logical work / scaling concern |
|---|---:|---:|---:|---|
| CollectAlignmentSummaryMetrics | 0 B (warm cache) | 745472–745472 B | 2332–2596 | One BAM traversal plus reference access; reference memory scales with contig length. |
| CollectInsertSizeMetrics | 0 B (warm cache) | 745472–770048 B | 0–7525 | One BAM traversal, histogram and R PDF; SE has no useful output. |
| MarkDuplicates | 0 B (warm cache) | 962560–1871872 B | 212940–1123220 | Two BAM traversals plus a complete marked BAM write; sorting/mate state can spill to temporary disk. |
| EstimateLibraryComplexity | 0 B (warm cache) | 745472–745472 B | 1054–1449 | One BAM traversal plus internal sequence sorting/group comparison; pending mates and spill/similar groups can be costly. |

GNU time filesystem block counts are multiplied by 512 on this Linux host. They measure kernel-accounted I/O, **not logical bytes read**, and include JVM/native-library temporary writes, stderr and other process writes; retained file sizes alone understate that cost. No cache drop was attempted. Zero physical reads does not mean no BAM/reference read. No sorting spill remained in these small runs; a large-data spill benchmark remains outstanding. samtools native peak RSS was 3.5–4.2 MiB, with 4,096–40,960 B block writes including captured stdout. Compared with these existing passes, Picard adds JVM startup, hundreds of MiB RSS, and (for MarkDuplicates) a new BAM write.

## Raw observations: overlap and new information

### CollectAlignmentSummaryMetrics

In all four libraries, total reads, mapped reads, mean length (75), and mismatch rate (0) agree exactly with samtools stats. PE `PAIR` counts sum FIRST_OF_PAIR and SECOND_OF_PAIR; these are not three independent totals. `PF_HQ_ALIGNED_READS` independently equals the count with MAPQ >=20: SE control 5,898; SE treatment 31,899; PE control 11,790; PE treatment 63,798. This is **Picard's hard-coded metric subset**, not a Genesis filter. MAPQ 0 records remain present and count in total/mapped metrics.

Picard's mapping rate is 1 for every input. Genesis removes unmapped, secondary and supplementary alignments before this BAM (`samtools view -F 2308`); therefore this is a conditional retained-BAM statistic, **not the fraction of raw reads mapped**. Vendor PF flags likewise do not measure plant biological quality. Additional fields include clipping fractions, high-quality mismatch summaries, adapter/noise categories and chimeras; their semantics are not all identical to samtools NM/CIGAR counters or FastQC raw-read adapter checks. These error-free one-contig fixtures cannot validate real mismatch/chimera usefulness.

### CollectInsertSizeMetrics

| Library | Pairs | Picard mean / SD | samtools displayed mean / SD | Picard median / MAD | Distribution agreement |
|---|---:|---|---|---|---|
| PE treatment | 32,000 | 180.009031 / 11.846541 | 180.0 / 11.8 | 180 / 10 | All 41 nonzero bins, 160–200, identical |
| PE control | 6,000 | 180.239667 / 11.697052 | 180.2 / 11.7 | 180 / 10 | All 41 nonzero bins, 160–200, identical |

Independent BAM TLEN counting, Picard histogram and samtools IS bins agree exactly. Genesis already publishes that samtools histogram as insert_lengths.tsv, so Picard mainly supplies summary presentation and a PDF. Both SE cases exit 0 but emit warnings and **no metrics/PDF**. Eight PE PDFs across repeats/native runs have valid PDF signatures/EOF; their numeric histograms were parsed, not judged only by exit code.

### Duplicate measurement

| Library | samtools original duplicate flags | MarkDuplicates duplicate reads/pairs | Picard duplication fraction | FastQC R1/R2 sequence-duplicate fraction, % |
|---|---:|---|---:|---|
| SE control | 0 | 5 reads / 6,000 | 0.000833 | 0.100 / N/A |
| SE treatment | 0 | 6,064 reads / 32,000 | 0.189500 | 18.953125 / N/A |
| PE control | 0 | 0 pairs / 6,000 | 0 | 0.216667 / 0.083333 |
| PE treatment | 0 | 345 pairs / 32,000 (690 records) | 0.010781 | 18.775000 / 18.909375 |

FastQC fractions are `100 - Total Deduplicated Percentage` extracted from retained ZIPs. They are per-mate sequence comparisons, not paired fragment coordinate duplicates. samtools flagstat/stats count existing 0x400 flags and do not infer duplicates. MarkDuplicates therefore adds information beyond these existing reports, especially for PE.

All four experimental marked BAMs have the original record counts. Canonical SAM comparison clears only the new duplicate flag, removes Picard PG tags, and sorts optional tag order; every other record field, sequence, quality, CIGAR, mapping quality and order matches. Original BAM SHA256 values are unchanged. The marked BAMs live only under `results/picard/`; none enters alignment, peak calling, quantification, tracks, production QC or publication. **Measuring endpoint redundancy does not authorize removing reads.**

### EstimateLibraryComplexity

SE runs exit 0 with a header-only metrics file and no metric rows: unpaired reads are ignored. PE control reports 6,000 pairs and zero duplicates, with no library-size estimate. PE treatment reports 31,997 pairs, 151 duplicates, fraction 0.004719, estimated library size 3,379,418. MarkDuplicates reports 32,000 pairs, 345 duplicates, estimated size 1,473,372. These are not interchangeable estimates.

Independent original-orientation paired-sequence counting finds 153 duplicate ordered pairs, versus 345 when mate order is canonicalized. ELC groups ordered R1/R2 sequences; its histogram has one group of size three, which is excluded from metric calculation by default MIN_GROUP_COUNT=2. This removes three pairs and two duplicate observations, explaining 31,997 and 151 exactly. It retains the size-three group in the printed histogram, another reason not to interpret histogram totals as the final metric denominator. Blank library-size fields are unavailable estimates, not zero-size libraries.

A separate tiny known-answer fixture has two duplicate classes of size two and four unique classes, with valid read groups/library and optical-coordinate names. MarkDuplicates returns exactly 2/8 duplicate SE records and 2/8 duplicate PE pairs, retaining all 8/16 records. ELC returns 2/8 for PE and no rows for SE. Both PE estimators return library size 13, although the constructed input has six distinct observed sequence classes: this output is a model-based extrapolation, not a ground-truth molecule census.

## Requirements, assumptions and decision

| Candidate | Read groups / sorting / reference | SE versus PE | DAP-seq assumptions and incremental value | Classification |
|---|---|---|---|---|
| CollectAlignmentSummaryMetrics | ALL_READS does not intrinsically need RG; RG/SM/LB needed for appropriate stratification. Coordinate-sorted BAM with matching reference used; reference-walking collector expects coordinate order. Exact FASTA required for reference-derived metrics. | Useful alignment summaries for both; PE has per-mate/combined categories. | Diagnostic clipping/chimera/reference mismatch detail may help targeted investigations, but much overlaps samtools/FastQC. Current filtered input cannot supply raw mapping rate. HQ MAPQ20 and default chimera assumptions must be exposed. | **OPTIONAL** for investigations; no default adoption |
| CollectInsertSizeMetrics | ALL_READS does not need RG; labels need metadata. Sequential collection does not require name sorting; existing coordinate order is accepted. No reference needed; R for PDF. | PE only; no fragment sizes from SE. | Existing samtools histogram contains the useful distribution. Picard default truncates summary/histogram tail at median+10 MAD and drops orientation categories below 5%; these are tool defaults, not plant acceptance thresholds. Not a replacement for SE SPP cross-correlation or an unbiased view of all tails. | **REJECT** for routine Genesis addition |
| MarkDuplicates metrics | Coordinate or query-grouped input supported, with different treatment of unmapped mates/secondary/supplementary records. Coordinate input tested. RG/LB important for correct library grouping and optical identification; missing LB here yields Unknown Library. No reference. Do not invent LB or pool libraries. | SE endpoint redundancy less specific; PE endpoint-pair redundancy more informative. Only PE supports reported library-size extrapolation. | Useful orthogonal duplication distribution, but same endpoints can reflect biological enrichment or repeated genome sequence, not PCR. No UMI-based causal identification here. Optical detection needs suitable original read names and instrument settings. | **OPTIONAL**, measurement-only |
| EstimateLibraryComplexity | No alignment/reference required; paired sequences required, any input order can be read, internal sequence sort and pending mate storage. RG/LB required for meaningful library attribution; these inputs report Unknown. | SE **REJECT** as inapplicable; PE computationally runs. | Default quality/prefix/mismatch/group filters alter denominator; mate ordering changes duplicate definition. Uniform-sampling library-size extrapolation is unvalidated for these enriched DAP-seq libraries. | **DEFER** PE scientific adoption |

Genesis supplies RG ID/SM/PL but no LB. These runs process one library per invocation, so they do not merge independent libraries under Unknown. That would become unsafe if multiple libraries were supplied together. Optical parsing fails for fixture names `readN`; warnings are retained. Optical zeros and optical-adjusted library estimates are **not validated** by these fixtures. The extra known fixture tests readable names with deliberately separated coordinates, not optical-duplicate sensitivity.

The synthetic generator does not model PCR amplification, yet endpoint duplicates occur. Interpretation: enrichment and finite endpoint sampling alone can produce duplicate observations. DAP-seq repeated loci and SE ambiguity strengthen the need to keep duplication a descriptive distribution rather than automatic exclusion. No biological threshold, MAPQ policy or deduplication decision is adopted; all plant/assay acceptance thresholds remain **UNSPECIFIED**. SPP estimates strand cross-correlation/enrichment and fragment shift; none of these Picard tools replaces that information.

## Failures, warnings and acceptance

- All 124 recorded analysis/setup/header/benchmark commands exited 0; 48 main Picard runs, 36 main samtools runs, 28 native measurements, six known-fixture commands, four headers and two reference preparations. Locked reinstall also passed.
- Parsed metric rows were identical over three repeats. The four-library overlap checks and known-answer checks passed; all original inputs rehashed unchanged. See [independent-checks.json](../results/picard/independent-checks.json) and [acceptance.json](../results/picard/acceptance.json).
- Expected applicability failure: SE insert-size collection produced no result, and SE ELC no metric rows despite success exit codes. These are not accepted as useful SE QC.
- Warnings: SE insert-size empty-category warnings; optical read-name parsing warnings in duplicate tools. Their raw stderr is retained. No warning was hidden or converted into a biological fail threshold.
- One experimental inspection-script run failed because a local variable shadowed the samtools executable path. Original stderr is preserved in `independent-checks-first.stderr`; only the standalone inspection helper was corrected, then rerun without changing assertions. No Picard, Genesis, or production-test failure was patched.
- Missing evidence: real DAP-seq performance, large-genome memory/I/O scaling, optical-duplicate validity, multiple true libraries/read groups, nonzero error/indel/chimera cases, and biological meaning of estimated library size. These limit adoption, not the recorded small-fixture results.
- Full Genesis regression suite was not rerun: this is a read-only standalone-tool experiment with no production edits; no claim of newly validating the pipeline suite is made. No local commit or branch change was needed for production code because none was changed.

Files added: this audit, [ADR](../design/adr-picard.md), experiment scripts/environment/reference/source snapshots under `scratch/picard/`, and raw logs/metrics/marked copies/checksums under `results/picard/`. Genesis git diff/status remain empty. Complete artifact manifest: [checksums.json](../results/picard/checksums.json).

## Primary sources

The versioned source snapshots in `scratch/picard/source/` back the tool-specific observations above; source hashes are recorded. Documentation/source review is separate from empirical acceptance.

- [Picard 3.5.0 release](https://github.com/broadinstitute/picard/releases/tag/3.5.0): release and Java requirements.
- [AlignmentSummaryMetrics collector, 3.5.0](https://github.com/broadinstitute/picard/blob/3.5.0/src/main/java/picard/analysis/AlignmentSummaryMetricsCollector.java): hard-coded HQ subset and category semantics.
- [CollectInsertSizeMetrics, 3.5.0](https://github.com/broadinstitute/picard/blob/3.5.0/src/main/java/picard/analysis/CollectInsertSizeMetrics.java) and [collector](https://github.com/broadinstitute/picard/blob/3.5.0/src/main/java/picard/analysis/directed/InsertSizeMetricsCollector.java): orientation, exclusions and histogram defaults.
- [MarkDuplicates, 3.5.0](https://github.com/broadinstitute/picard/blob/3.5.0/src/main/java/picard/sam/markduplicates/MarkDuplicates.java): coordinate/query sorting, duplicate detection and separate removal controls.
- [EstimateLibraryComplexity, 3.5.0](https://github.com/broadinstitute/picard/blob/3.5.0/src/main/java/picard/sam/markduplicates/EstimateLibraryComplexity.java): paired sequence matching and denominator filters.
- [DuplicationMetrics model, 3.5.0](https://github.com/broadinstitute/picard/blob/3.5.0/src/main/java/picard/sam/DuplicationMetrics.java): Lander–Waterman model and unavailable-estimate behavior.
- [samtools stats 1.24](https://www.htslib.org/doc/1.24/samtools-stats.html), [flagstat 1.24](https://www.htslib.org/doc/1.24/samtools-flagstat.html), [FastQC duplication](https://www.bioinformatics.babraham.ac.uk/projects/fastqc/Help/3%20Analysis%20Modules/8%20Duplicate%20Sequences.html): meanings of the existing reports.
