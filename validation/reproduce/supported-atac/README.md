# Reproduce the public bulk ATAC checks

Run from the validation workspace, with the checkout in `repo/`. Keep generated
files outside Git. Docker must already work for the current user.

```bash
python repo/validation/reproduce/supported-atac/public_inputs.py results/public-atac-inputs
cd repo
pixi run pipeline-atac ../results/public-atac-inputs/samples.tsv \
  --references ../results/public-atac-inputs/references.json --outdir ../results/public-atac-run
pixi run pipeline-atac ../results/public-atac-inputs/samples.tsv \
  --references ../results/public-atac-inputs/references.json --outdir ../results/public-atac-run --resume
```

The acquisition script verifies every retained checksum, derives TSS positions
from the exact GTF release, and checks the resulting TSS checksum. `downloads.json`
records authoritative URLs and checksums. The other two manifests preserve the
original run inputs; the script changes only local path prefixes when recreating
them. FASTQ subsets contain the first 200,000 records of each mate, not a random
sample. Full source FASTQ checksums were not verified. Gzip build differences
can cause a subset checksum mismatch; the script fails rather than replacing a
validated identity. The original acquisition used Python 3.12.12.

This is a computational integration check, not a reproduction of the papers'
full-depth biological results. MAPQ 30 and duplicate exclusion are declared
benchmark choices. Organellar identities and genome assemblies are explicit.

For the separate maize adapter sensitivity experiment, copy the sample sheet
to a new file, retain only SRR27443453 and SRR27443454, and set both adapter columns
to `CTGTCTCTTATACACATCT`. Use a new output directory. Keep every other field and
the exact reference registry unchanged. The recorded experiment reused the
checksum-verified existing index through an external experiment DAG; a normal
fresh run produces its own index and includes that cost in its timing.

```bash
pixi run validate-atac --keep
pixi run checks
pixi run validate-docker --keep
```

The ATAC regression creates deterministic technical lanes and two biological
replicates, tests two stable resumes, mutates a helper only in an isolated copy,
and verifies invalidation followed by another stable resume. It also checks
paired adapter removal against a known 40-base insert, raw byte preservation,
and publication of the adapter report and MACS3 version.

To reproduce the fragment-stage resource test, take `marked.bam` from the
`ATAC_ALIGN (first)` work directory listed in a retained regression's
`fresh-trace.tsv`, and use that regression's `run/inputs/first.json`:

```bash
pixi run uv run --frozen --project genesis_tools python \
  validation/reproduce/supported-atac/scale_fragments.py \
  /path/marked.bam /path/run/inputs/first.json /new/scaling-output
```

This creates 1, 10 and 40 coordinate-disjoint copies (32,000 to 1,280,000
templates), records input checksums and GNU time statistics, and requires known
fragment counts. Disk use includes the synthetic BAMs and temporary sorting
files. It measures only fragment processing, not whole-pipeline peak RAM.
