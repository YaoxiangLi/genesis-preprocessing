#!/usr/bin/env bash
# Run the DAP-seq workflow described by one or more samples.tsv files.
set -euo pipefail

die() { printf 'Error: %s\n' "$*" >&2; exit 1; }
usage() {
    cat <<'EOF'
Usage: bash dap_seq_pipeline.sh [options] [samples.tsv ...]
With no sheets, process all four project datasets.
  --dry-run          Print commands without downloading or writing files
  --stage STAGE      all (default), download, metadata, map, qc, tracks, peaks, quantify
  --sample ID        Process one sample and its control (requires one sheet)
  --threads N        Bowtie/SPP threads (default: THREADS or 2)
  --output-dir DIR   Output root (default: OUTPUT_DIR or ./results beside script)
  -h, --help         Show usage
Tool and reference locations can be overridden with environment variables.
See README.md for dependencies, outputs, and the legacy script discrepancies.
EOF
}

cleanup() {
    local file
    if ! "$dry_run" && ((${#temporary_files[@]})); then
        for file in "${temporary_files[@]}"; do rm -f -- "$file"; done
    fi
}

print_command() { printf '%q ' "$@"; }
run() {
    if "$dry_run"; then print_command "$@"; printf '\n'; else "$@"; fi
}
need_command() { command -v "$1" >/dev/null 2>&1 || die "Executable unavailable: $1"; }
need_file() { [[ -r $1 ]] || die "Input unavailable: $1"; }
wants() { [[ $stage == all || $stage == "$1" ]]; }
reference_path() {
    if [[ $1 = /* ]]; then printf '%s' "$1"; else printf '%s/%s' "$genome_root" "$1"; fi
}

validate_sheet() {
    awk -F '\t' '
        NR == 1 {
            expected = "sample_id\tread1_url\tread2_url\tcontrol_sample\tbowtie_index\treference_fasta\tchrom_sizes"
            if ($0 != expected) { print "Invalid TSV header" > "/dev/stderr"; exit 1 }
            next
        }
        {
            if (NF != 7) { print "Expected 7 fields at line " NR > "/dev/stderr"; bad=1 }
            for (i=1; i<=NF; i++) if ($i == "" || $i ~ /\r/) bad=1
            if ($1 !~ /^[A-Za-z0-9_][A-Za-z0-9_.-]*$/ || seen[$1]++) bad=1
            if ($2 !~ /^https?:\/\/[^[:space:]]+$/) bad=1
            if ($3 != "-" && $3 !~ /^https?:\/\/[^[:space:]]+$/) bad=1
            controls[$1]=$4; layouts[$1]=($3 == "-" ? "SE" : "PE")
            refs[$1]=$5 FS $6 FS $7
        }
        END {
            if (NR < 2) bad=1
            for (s in controls) {
                c=controls[s]
                if (c != "-" && (!(c in seen) || c == s || controls[c] != "-" || layouts[c] != layouts[s] || refs[c] != refs[s])) {
                    print "Invalid control for " s ": " c > "/dev/stderr"; bad=1
                }
            }
            if (bad) { print "Invalid sample sheet: " FILENAME > "/dev/stderr"; exit 1 }
        }
    ' "$1" || die "Sample sheet validation failed: $1"
}

load_row() {
    bowtie_index=$(reference_path "$bowtie_index")
    reference_fasta=$(reference_path "$reference_fasta")
    chrom_sizes=$(reference_path "$chrom_sizes")
    unique_stem="$sample_id.1x36mers.unique"
    if [[ $read2_url == - ]]; then layout=SE; else layout=PE; fi
    if [[ $layout == PE ]]; then
        read1="$sample_id.end1.fastq.gz"
        read2="$sample_id.end2.fastq.gz"
        main_stem="$sample_id.PE.a"
    else
        read1="$sample_id.fastq.gz"
        main_stem="$sample_id.SE.a"
    fi
}

infer_metadata() {
    local partial="$sample_id.metadata.tsv.partial.$$"
    local command=("$metadata_python" "$project_dir/infer_sample_metadata.py"
        --sample-id "$sample_id" --chrom-sizes "$chrom_sizes" --read1 "$read1")
    if [[ $layout == PE ]]; then command+=(--read2 "$read2"); fi
    temporary_files+=("$PWD/$partial")
    if "$dry_run"; then
        print_command "${command[@]}"; printf '> %q\n' "$partial"
    else
        "${command[@]}" > "$partial"
    fi
    run mv -- "$partial" "$sample_id.metadata.tsv"
}

load_metadata() {
    if "$dry_run"; then
        # These values cannot be known without inspecting actual reference/FASTQ files.
        genome_size=INFERRED_GENOME_SIZE
        analysis_read_length=INFERRED_READ_LENGTH
        return
    fi
    local metadata="$sample_id.metadata.tsv" _metadata_sample _metadata_layout
    local _metadata_header _read1_checked _read2_checked
    if [[ ! -f $metadata ]]; then
        need_command "$metadata_python"
        infer_metadata
    fi
    awk -F '\t' -v sample="$sample_id" -v layout="$layout" '
        NR == 1 {
            if ($0 != "sample_id\tlayout\tgenome_size\tanalysis_read_length\tread1_reads_checked\tread2_reads_checked") bad=1
        }
        NR == 2 {
            if (NF != 6 || $1 != sample || $2 != layout) bad=1
            for (i=3; i<=5; i++) if ($i !~ /^[1-9][0-9]*$/) bad=1
            if ($5 > 100 || $6 !~ /^[0-9]+$/ || $6 > 100) bad=1
            if ((layout == "SE" && $6 != 0) || (layout == "PE" && $6 < 1)) bad=1
        }
        END {exit (bad || NR != 2)}
    ' "$metadata" || die "Invalid metadata: $metadata; rerun --stage metadata"
    {
        read -r _metadata_header
        IFS=$'\t' read -r _metadata_sample _metadata_layout genome_size analysis_read_length _read1_checked _read2_checked
    } < "$metadata"
}

download_read() {
    local url=$1 destination=$2 partial="$2.partial.$$"
    if ! "$dry_run" && [[ -s $destination ]]; then
        gzip -t -- "$destination"
        return
    fi
    temporary_files+=("$PWD/$partial")
    run wget "$url" -O "$partial"
    run gzip -t -- "$partial"
    run mv -- "$partial" "$destination"
}

count_lines() {
    if "$dry_run"; then
        print_command gzip -dc -- "$read1"; printf '| wc -l > %q\n' "$sample_id.fastq.lines"
    else
        gzip -dc -- "$read1" | wc -l > "$sample_id.fastq.lines"
    fi
}

map_bam() {
    local mode=$1 stem=$2 partial="$2.partial.$$"
    local reads=() alignment=() sorting=()
    case $mode in
        unique)
            reads=("$legacy_python" "$code_root/trimfastq.py" "$read1" 36 -stdout)
            alignment=("$bowtie" "$bowtie_index" -p "$threads" -v 2 -k 2 -m 1 -t --best --strata -q --sam-nh --sam -) ;;
        SE)
            reads=("$legacy_python" "$code_root/trimfastq.py" "$read1" "$analysis_read_length" -stdout)
            alignment=("$bowtie" "$bowtie_index" -p "$threads" -v 1 -a -t --best --strata -q --sam-nh --sam -) ;;
        PE)
            reads=("$legacy_python" "$code_root/PEFastqToTabDelimited.py" "$read1" "$read2" -trim "$analysis_read_length" "$analysis_read_length")
            alignment=("$bowtie" "$bowtie_index" -p "$threads" -v 1 -a -t --best --strata -q --sam-nh -X 1000 --sam --12 -) ;;
    esac
    if [[ $sort_style == legacy ]]; then
        sorting=("$samtools" sort - "$partial")
    else
        sorting=("$samtools" sort -o "$partial.bam" -)
    fi
    temporary_files+=("$PWD/$partial.bam")
    if "$dry_run"; then
        print_command "${reads[@]}"; printf '| '
        print_command "${alignment[@]}"; printf '| '
        print_command "$samtools" view -F4 -bT "$reference_fasta" -; printf '| '
        print_command "${sorting[@]}"; printf '\n'
    else
        "${reads[@]}" | "${alignment[@]}" | "$samtools" view -F4 -bT "$reference_fasta" - | "${sorting[@]}"
    fi
    run mv -- "$partial.bam" "$stem.bam"
    run "$samtools" index "$stem.bam"
}

make_tracks() {
    local stem=$1 mode=$2 strand label wig
    local coverage_flags=(-notitle -RPM) five_prime_flags=(-notitle -uniqueBAM)
    [[ $mode == PE ]] || coverage_flags+=(-uniqueBAM)
    wig="$stem.wig"
    run "$legacy_python" "$code_root/makewigglefromBAM-NH.py" --- "$stem.bam" "$chrom_sizes" "$wig" "${coverage_flags[@]}"
    run "$wig_to_bigwig" "$wig" "$chrom_sizes" "$stem.bigWig"
    for strand in + -; do
        if [[ $strand == + ]]; then label=plus; else label=minus; fi
        wig="$stem.$label.wig"
        run "$legacy_python" "$code_root/makewigglefromBAM-NH.py" --- "$stem.bam" "$chrom_sizes" "$wig" "${coverage_flags[@]}" -stranded "$strand"
        run "$wig_to_bigwig" "$wig" "$chrom_sizes" "$stem.$label.bigWig"
        wig="$stem.5p.counts.$label.wig"
        local flags=("${five_prime_flags[@]}" -stranded "$strand")
        if [[ $mode == PE && $strand == - ]]; then flags+=(-absValue); fi
        run "$legacy_python" "$code_root/make5primeWigglefromBAM-NH.py" --- "$stem.bam" "$chrom_sizes" "$wig" "${flags[@]}"
        run "$wig_to_bigwig" "$wig" "$chrom_sizes" "$stem.5p.counts.$label.bigWig"
    done
}

process_row() {
    local current_stage=$1 peak_prefix format control_stem stats_stem
    case $current_stage in
        download)
            download_read "$read1_url" "$read1"
            if [[ $layout == PE ]]; then download_read "$read2_url" "$read2"; fi
            count_lines ;;
        metadata)
            infer_metadata ;;
        map)
            load_metadata
            map_bam unique "$unique_stem"
            map_bam "$layout" "$main_stem" ;;
        qc)
            run "$rscript" "$spp_script" "-c=$unique_stem.bam" "-p=$threads" -savp -rf -s=-0:2:400 "-out=$sample_id.1x36mers.QC"
            # Preserve the original SAMstats arguments, including -paired.
            if [[ $layout == SE ]]; then stats_stem=$main_stem; else stats_stem=$unique_stem; fi
            run "$legacy_python" "$code_root/SAMstats.py" "$stats_stem.bam" "SAMstats-$stats_stem" -bam "$chrom_sizes" "$samtools" -paired
            if [[ $layout == PE ]]; then
                run "$legacy_python" "$code_root/SAMstats.py" "$main_stem.bam" "SAMstats-$main_stem" -bam "$chrom_sizes" "$samtools" -paired
                run "$legacy_python" "$code_root/PEInsertDistFromBAM.py" "$main_stem.bam" "$chrom_sizes" "$sample_id.2x36mers.InsertLength" -uniqueBAM -normalize
            fi ;;
        tracks)
            if [[ $layout == PE ]]; then make_tracks "$unique_stem" SE; fi
            make_tracks "$main_stem" "$layout" ;;
        peaks|quantify)
            [[ $control_sample != - ]] || return 0
            peak_prefix="$main_stem.MACS-2.1.0"
            if [[ $current_stage == peaks ]]; then
                load_metadata
                if [[ $layout == PE ]]; then format=BAMPE; control_stem="$control_sample.PE.a";
                else format=BAM; control_stem="$control_sample.SE.a"; fi
                run "$macs2" callpeak -t "$main_stem.bam" -c "$control_stem.bam" -n "$peak_prefix" -g "$genome_size" -f "$format"
                # MACS2 writes an uncompressed narrowPeak; quantification expects gzip.
                run gzip -f -- "${peak_prefix}_peaks.narrowPeak"
            else
                run "$legacy_python" "$rpm_script" "${peak_prefix}_peaks.narrowPeak.gz" 0 "$main_stem.bam" "$chrom_sizes" "${peak_prefix}_peaks.RPM" -RPM
            fi ;;
    esac
}

preflight() {
    "$dry_run" && return 0
    if wants download; then need_command wget; need_command gzip; fi
    if wants metadata || wants map || wants peaks; then need_command "$metadata_python"; fi
    if wants map || wants qc || wants tracks || wants quantify; then need_command "$legacy_python"; fi
    if wants map; then
        need_command "$bowtie"; need_command "$samtools"
        need_file "$code_root/trimfastq.py"
        if "$has_pe"; then need_file "$code_root/PEFastqToTabDelimited.py"; fi
    fi
    if wants qc; then
        need_command "$rscript"; need_command "$samtools"; need_file "$spp_script"
        need_file "$code_root/SAMstats.py"
        if "$has_pe"; then need_file "$code_root/PEInsertDistFromBAM.py"; fi
    fi
    if wants tracks; then
        need_command "$wig_to_bigwig"
        need_file "$code_root/makewigglefromBAM-NH.py"
        need_file "$code_root/make5primeWigglefromBAM-NH.py"
    fi
    if wants peaks; then need_command "$macs2"; need_command gzip; fi
    if wants quantify; then need_file "$rpm_script"; fi
}

project_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
dry_run=false
stage=all
sample_filter=
threads=${THREADS:-2}
output_root=${OUTPUT_DIR:-"$project_dir/results"}
genome_root=${GENOME_DIR:-/oak/stanford/groups/akundaje/marinovg/genomes}
code_root=${CODE_DIR:-/oak/stanford/groups/akundaje/marinovg/code}
program_root=${PROGRAM_DIR:-/oak/stanford/groups/akundaje/marinovg/programs}
legacy_python=${LEGACY_PYTHON:-python}
metadata_python=${METADATA_PYTHON:-python3}
bowtie=${BOWTIE:-"$program_root/bowtie-1.0.1+hamrhein_nh_patch/bowtie"}
samtools=${SAMTOOLS:-"$program_root/samtools-0.1.18/samtools"}
sort_style=${SAMTOOLS_SORT_STYLE:-legacy}
macs2=${MACS2:-"$program_root/MACS-2.1.0/bin/macs2"}
wig_to_bigwig=${WIG_TO_BIGWIG:-"$program_root/UCSC-utils-2017-07-13/wigToBigWig"}
rscript=${RSCRIPT:-Rscript}
spp_script=${SPP_SCRIPT:-"$HOME/code/spp/spp_package/run_spp.R"}
rpm_script=${RPM_SCRIPT:-"$HOME/code/bedRPKMfromBAM.py"}
sheets=()
temporary_files=()

while (($#)); do
    case $1 in
        --dry-run) dry_run=true; shift ;;
        --stage|--sample|--threads|--output-dir)
            (($# >= 2)) || die "Missing value for $1"
            case $1 in
                --stage) stage=$2 ;;
                --sample) sample_filter=$2 ;;
                --threads) threads=$2 ;;
                --output-dir) output_root=$2 ;;
            esac
            shift 2 ;;
        -h|--help) usage; exit 0 ;;
        --) shift; sheets+=("$@"); break ;;
        -*) die "Unknown option: $1" ;;
        *) sheets+=("$1"); shift ;;
    esac
done
case $stage in all|download|metadata|map|qc|tracks|peaks|quantify) ;; *) die "Unknown stage: $stage" ;; esac
[[ $threads =~ ^[1-9][0-9]*$ ]] || die 'Threads must be a positive integer'
case $sort_style in legacy|modern) ;; *) die 'SAMTOOLS_SORT_STYLE must be legacy or modern' ;; esac
if ((${#sheets[@]} == 0)); then sheets=("$project_dir"/[0-9]*/samples.tsv); fi
[[ -z $sample_filter || ${#sheets[@]} == 1 ]] || die '--sample requires exactly one sheet'
# Resolve roots before changing into a dataset output directory.
[[ $output_root = /* ]] || output_root="$PWD/$output_root"
[[ $genome_root = /* ]] || genome_root="$PWD/$genome_root"
[[ $code_root = /* ]] || code_root="$PWD/$code_root"

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Validate all sheets and dependencies before any downloads or output writes.
has_pe=false
for i in "${!sheets[@]}"; do
    need_file "${sheets[i]}"
    sheets[i]="$(cd -- "$(dirname -- "${sheets[i]}")" && pwd)/$(basename -- "${sheets[i]}")"
    validate_sheet "${sheets[i]}"
    if awk -F '\t' 'NR > 1 && $3 != "-" {found=1} END {exit !found}' "${sheets[i]}"; then has_pe=true; fi
done
preflight

for sheet in "${sheets[@]}"; do
    dataset=$(basename -- "$(dirname -- "$sheet")")
    destination="$output_root/$dataset"
    selected_control=
    if [[ -n $sample_filter ]]; then
        selected_control=$(awk -F '\t' -v s="$sample_filter" 'NR > 1 && $1 == s {print $4}' "$sheet")
        [[ -n $selected_control ]] || die "Sample absent from sheet: $sample_filter"
    fi
    if "$dry_run"; then
        printf '# Dataset: %s\n' "$dataset"
        print_command mkdir -p -- "$destination"; printf '\n'
        print_command cd -- "$destination"; printf '\n'
    else
        mkdir -p -- "$destination"
        cd -- "$destination"
    fi
    if [[ $stage == all ]]; then stages=(download metadata map qc tracks peaks quantify); else stages=("$stage"); fi
    for current_stage in "${stages[@]}"; do
        printf '# %s: %s\n' "$dataset" "$current_stage"
        {
            read -r _header
            while IFS=$'\t' read -r sample_id read1_url read2_url control_sample bowtie_index reference_fasta chrom_sizes || [[ -n $sample_id ]]; do
                if [[ -n $sample_filter && $sample_id != "$sample_filter" && $sample_id != "$selected_control" ]]; then continue; fi
                load_row
                if ! "$dry_run"; then
                    printf '  %s\n' "$sample_id"
                    if [[ $current_stage != download && $current_stage != peaks ]]; then need_file "$chrom_sizes"; fi
                    case $current_stage in
                        map)
                            need_file "$read1"; need_file "$reference_fasta"
                            [[ -r $bowtie_index.1.ebwt || -r $bowtie_index.1.ebwtl ]] || die "Bowtie index unavailable: $bowtie_index"
                            if [[ $layout == PE ]]; then need_file "$read2"; need_file "$code_root/PEFastqToTabDelimited.py"; fi ;;
                        qc|tracks)
                            need_file "$main_stem.bam"; need_file "$main_stem.bam.bai"
                            if [[ $layout == PE || $current_stage == qc ]]; then need_file "$unique_stem.bam"; need_file "$unique_stem.bam.bai"; fi
                            if [[ $layout == PE && $current_stage == qc ]]; then need_file "$code_root/PEInsertDistFromBAM.py"; fi ;;
                        peaks|quantify)
                            if [[ $control_sample != - ]]; then
                                need_file "$main_stem.bam"; need_file "$main_stem.bam.bai"
                                if [[ $current_stage == quantify ]]; then need_file "$main_stem.MACS-2.1.0_peaks.narrowPeak.gz";
                                elif [[ $layout == PE ]]; then need_file "$control_sample.PE.a.bam";
                                else need_file "$control_sample.SE.a.bam"; fi
                            fi ;;
                    esac
                fi
                process_row "$current_stage" < /dev/null
            done
        } < "$sheet"
    done
done
