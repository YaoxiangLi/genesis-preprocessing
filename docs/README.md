# Genesis documentation

If you are new to Genesis, start with [installation and a first analysis](../README.md#install-and-check-your-environment).
Choose the guide for the task you want to complete. For the scientific question,
measurement definitions and evidence boundaries, read the
[scientific overview](scientific-overview.md).

## Process sequencing data

- [DAP-seq](usage/dapseq-reference.md): sample sheets, controls, references, execution and scientific settings.
- [MACS3 builds and resources](usage/macs3.md): select the optimized source build and inspect caller provenance.
- [Bulk ATAC-seq](usage/bulk-atac.md): sample sheets, trimming, filtering, fragments, peaks and QC.
- [scATAC pseudobulks](usage/scatac-seq.md): fragment files, cell lists, pseudobulk peaks, tracks and QC.
- [RNA-seq](usage/rna-seq.md): plant annotations, STAR intron limits, gene counts, tracks and QC.
- [TSS mapping](usage/tss-seq.md): CAGE, TSS-seq and csRNA-seq trimming, cap-G correction, TSS tags, paraclu clusters and QC.
- [Running on Perlmutter and Sherlock](usage/clusters.md): default profiles, images, accounts and QOS, references and purged scratch.

## Related repository

[genesis-curation](https://github.com/kundajelab/genesis-curation) has metadata
discovery, curation and review.

## Earlier work

These links are pinned to the revision they describe; their commands may differ from the current
ones.

- [Method benchmarks](https://github.com/kundajelab/genesis-curation/blob/12bb02cb9ec98fe8c4c0ec660adcfdeb7384f20e/benchmarks/README.md): datasets, method comparisons, metric definitions and measured results.
- [DAP-only README](https://github.com/kundajelab/genesis-preprocessing/blob/fb600968b3abf5d79756aaf7e6d1e4ff43a1b41d/README.md) at revision `fb60096`.
- [Validation reports and evidence](https://github.com/kundajelab/genesis-preprocessing/tree/e2e2aa92252a3ff8c53f5a4787816d2c80b27401/validation) at revision `e2e2aa9`, including the MACS3 build comparison and the 2026-10-14 method comparison.

## Develop Genesis

- [Contributor guide](development.md): install a development environment, run checks and test changes.
- [Nextflow conventions](nextflow-style.md): module structure and pipeline changes.
- [Diagram maintenance](diagrams/README.md): update the maintained workflow maps.
