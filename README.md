# Plant DAP-seq processing

Each dataset has one `samples.tsv`, with one row per downloaded library, including
controls. The shared `dap_seq_pipeline.sh` replaces the repeated command lists.

| Dataset | Layout | Samples | Samples with peak calls |
| --- | --- | ---: | ---: |
| 01-Arabidopsis_thaliana-GSE60141 | Single-end | 936 | 934 |
| 15-Arabidopsis_lyrata-PRJNA1177479 | Paired-end | 405 | 378 |
| 16-Arabidopsis_thaliana-PRJNA1177481 | Paired-end | 800 | 748 |
| 24-Sorghum_bicolor-PRJNA1177471 | Paired-end | 142 | 134 |

## Order of operations

1. **download**: Download FASTQs (`wget.sh`), verify gzip integrity, and count
   first-read FASTQ lines (`countlines.sh`). Divide the line count by four for
   the read count. Paired files share one sample row.
2. **metadata**: Infer layout from the presence of a second FASTQ URL, sum the
   second column of `chrom_sizes` for genome size, and inspect the first 100 reads
   of each FASTQ to determine read length. Write `<sample_id>.metadata.tsv`.
3. **map**: Trim and align reads (`map-*.sh`), sort BAMs, and index each BAM
   (`samtools-index-*.sh`). Every sample gets a unique 36-base first-read
   alignment for cross-correlation QC. The main alignment uses all best-stratum
   alignments at the inferred read length. The historical `2x36mers` filenames
   are retained for insert-length statistics; they do not specify the main
   alignment's read length.
4. **qc**: Run cross-correlation (`run_spp.sh`), alignment statistics
   (`SAMstats-*.sh`), and paired insert-length distributions
   (`PEInsertDistFromBAM-2x36mers.sh`).
5. **tracks**: Generate total and strand-specific RPM coverage, plus strand-specific
   5-prime counts (`makewiggle*.sh`, `make5pwiggle*.sh`), then convert each WIG
   to bigWig (`wigtobigwig*.sh`).
6. **peaks**: Run MACS2 with the control listed in each sample row (`macs2.sh`),
   then gzip the narrowPeak output.
7. **quantify**: Calculate RPM over each sample's called peaks
   (`bedRPKMfromBAM.sh`). Rows with `control_sample = -` skip peaks and quantification.

Stages run across all selected samples before advancing. This ensures control
BAMs exist before peak calling. QC, tracks, and peaks can each run after mapping;
only quantification depends on peak calling.

## Running

Preview a dataset without accessing tools, reference files, or the network, and
without creating output files:

```bash
bash dap_seq_pipeline.sh --dry-run 01-Arabidopsis_thaliana-GSE60141/samples.tsv
```

Run one dataset, or omit the sheet argument to run all four:

```bash
bash dap_seq_pipeline.sh --threads 2 01-Arabidopsis_thaliana-GSE60141/samples.tsv
bash dap_seq_pipeline.sh --threads 2
```

Use `--sample ID` with one sheet to process that sample and its assigned control.
Use `--stage download|metadata|map|qc|tracks|peaks|quantify` to run a single stage with
existing upstream outputs. Results go to `results/<dataset>/`, or
`<root>/<dataset>/` when `--output-dir <root>` is supplied.

The pipeline stops on command failures, validates sheets before running, and
checks required tools and helper scripts before writing outputs. Downloads and
BAM sorting use temporary destinations, removed on failure. Existing nonempty
FASTQs are gzip-checked and reused; other selected stages rerun and may replace
their outputs. There are no completion markers or automatic downstream skips.
Use separate output roots for different reference or analysis configurations.

## Dependencies and locations

The pipeline retains the original alignment options and tools, with read length
and MACS2 genome size now inferred from inputs. It needs Python 3 for metadata,
wget, gzip, the **NH-patched Bowtie 1** (`--sam-nh`), samtools, MACS2, wigToBigWig, R/SPP,
and the original Python helpers, which are **not included in this repository**.
The Python interpreter must support those helpers; their original interpreter
was simply `python`. Ordinary Bowtie or Bowtie 2 is not a replacement for the
patched executable. No tools are installed or reference indexes built automatically.

Defaults reproduce the original Sherlock locations. Configure local installations
or other cluster locations with these environment variables:

| Variable | Default / purpose |
| --- | --- |
| `GENOME_DIR` | `/oak/stanford/groups/akundaje/marinovg/genomes`; root for relative sheet reference paths |
| `CODE_DIR` | `/oak/stanford/groups/akundaje/marinovg/code`; original Python helpers |
| `PROGRAM_DIR` | `/oak/stanford/groups/akundaje/marinovg/programs`; original tool installations |
| `LEGACY_PYTHON` | `python`; interpreter for helper scripts |
| `METADATA_PYTHON` | `python3`; interpreter for the included metadata inference script |
| `BOWTIE`, `SAMTOOLS`, `MACS2`, `WIG_TO_BIGWIG`, `RSCRIPT` | Override individual executables with absolute paths or names on PATH |
| `SAMTOOLS_SORT_STYLE` | `legacy`; set `modern` when overriding samtools with a version supporting `sort -o` |
| `SPP_SCRIPT` | `$HOME/code/spp/spp_package/run_spp.R` |
| `RPM_SCRIPT` | `$HOME/code/bedRPKMfromBAM.py` |
| `THREADS` | `2`; Bowtie and SPP thread count |
| `OUTPUT_DIR` | `results/` beside the pipeline |

Use absolute paths for script overrides and `PROGRAM_DIR`; executable overrides
can also be names on PATH. Reference columns may be absolute or relative to
`GENOME_DIR`. On Sherlock, run analysis on an
allocated compute node; the pipeline does not submit jobs or impose scheduler
resource limits. It writes to the output directory, so use an authorized destination.

## Sample sheet fields

The header and column order are fixed. Use `-` for an absent mate or control.
`sample_id` preserves the original output filename prefix;
`read1_url` and `read2_url` preserve the original ENA download paths using
HTTPS; `control_sample` preserves the exact control from the old MACS2 command.
`bowtie_index`, `reference_fasta`, and `chrom_sizes` identify the reference inputs.
Sample IDs must be unique and controls must appear in the same sheet, with the
same layout and reference. Control rows must have `control_sample = -`. The unique
first-read QC alignment always uses 36 bases.

## Inferred metadata

`<sample_id>.metadata.tsv` has one row and the columns `sample_id`, `layout`,
`genome_size`, `analysis_read_length`, `read1_reads_checked`, and
`read2_reads_checked`. Layout is `SE` when `read2_url = -`, otherwise `PE`.
Genome size is the sum of all chromosome lengths, used directly as MACS2 `-g`.
Read length is the sequence length observed in the first 100 reads of each
FASTQ. All inspected reads, including both mates, must have the same length.
Files with fewer than 100 reads use all available reads; empty or malformed
FASTQs and inconsistent lengths fail. Chromosome sizes must be positive integers
with unique chromosome names. Metadata is written atomically after validation.

Full runs infer metadata after downloading and before alignment. Standalone
`map` and `peaks` stages load the saved metadata, or generate it from the FASTQs
and chromosome sizes when missing. Run `--stage metadata` again after changing
input files. Saved metadata lets peak calling run without retaining FASTQs.
Dry runs do not inspect data files; command previews use `INFERRED_READ_LENGTH`
and `INFERRED_GENOME_SIZE` placeholders.

## Outputs and resolved gaps

Each sample produces downloaded FASTQs, `.fastq.lines`, `.metadata.tsv`, coordinate-sorted
`.1x36mers.unique.bam` plus `.SE.a.bam` or `.PE.a.bam`, BAM indexes, SPP QC,
SAMstats, WIG/bigWig tracks, and (for paired samples) insert-length statistics.
Treatments also produce the MACS2 output family, compressed narrowPeak files,
and `.MACS-2.1.0_peaks.RPM` quantification.

The old paired-end datasets referenced `.SE.a.bam` for their single-end tracks
and indexing, but supplied no command creating it. Those tracks now use the
existing unique 36-base first-read BAM and carry `.1x36mers.unique` names.
Paired-end tracks and GSE60141 tracks retain their original names and options.
The missing narrowPeak compression step is now explicit. Original SAMstats
`-paired` arguments, including those on single-end BAMs, are preserved pending
inspection of that external helper. No deduplication or other new analysis step
has been added. The replaced command lists remain available in Git history.

## Verification

```bash
bash -n dap_seq_pipeline.sh
shellcheck dap_seq_pipeline.sh
python3 tests/verify_pipeline.py
```

The dependency-free verification script checks the four sheets and exercises
single-end and paired-end workflows using temporary fake tools, including control
ordering, failure propagation, and both samtools sort interfaces. Metadata checks
cover chromosome sums, bounded read sampling, short files, empty or malformed
inputs, mixed read lengths, and mismatched mates. It does not
validate biological results or external helper compatibility.
