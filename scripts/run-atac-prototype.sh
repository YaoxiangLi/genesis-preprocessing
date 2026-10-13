#!/usr/bin/env bash
set -euo pipefail
project=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    cat <<'USAGE'
Usage: pixi run pipeline-atac --read1 R1.fastq.gz --read2 R2.fastq.gz
  --fasta reference.fa.gz --tss tss.bed --outdir OUTPUT
  --mapq INTEGER --organelles chrM,chrC --genome_size INTEGER
  --adapter_policy none-synthetic-adapter-free [-resume SESSION]

Experimental single-library paired-end synthetic ATAC only.
TSS input: tab-separated chromosome, BED0 position, strand.
Use --organelles NONE only when the reference has no organellar contigs.
Duplicate-marked reads are retained in the intermediate BAM, then excluded
from analysis. Plant biological thresholds remain UNSPECIFIED.
Run pixi run validate-atac --keep for a deterministic Docker regression.
USAGE
    exit 0
fi
exec nextflow -C "$project/experimental/atac/nextflow.config" run "$project/experimental/atac/main.nf" --source_sha "$(git -C "$project" rev-parse HEAD)" "$@"
