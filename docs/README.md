# Genesis documentation

If you are new to Genesis, start with [installation and a first analysis](../README.md#install-and-check-your-environment).
Choose the guide for the task you want to complete. For the scientific question,
measurement definitions and evidence boundaries, read the
[scientific overview](scientific-overview.md).

## Process sequencing data

- [DAP-seq](usage/dapseq-reference.md): sample sheets, controls, references, execution and scientific settings.
- [MACS3 builds and resources](usage/macs3.md): select the optimized source build and inspect caller provenance.
- [Bulk ATAC-seq](usage/bulk-atac.md): paired lanes, adapter/duplicate policies, fragments, peaks and QC.
- [Single-cell ATAC](usage/scatac.md): import existing fragments and make replicate-specific pseudobulks.
- [Model handoff](usage/scatac-model-handoff.md): load an scATAC export and check its conventions.
- [Execution](usage/execution.md): local Docker, schedulers and independent workers.

## Organize and review a study

- [Study workflow](usage/studies.md): register prepared inputs, run jobs, collect results and export a reviewed selection.
- [Curation](usage/curation.md): validate files, search the registry, review metadata/QC and back up your catalog.
- [AI providers](usage/ai-providers.md): configure optional metadata proposals and failure explanations.
- [Private model services](usage/llm-deployment.md): inspect, start, monitor and stop a model on an existing node.

## Understand the methods

- [Benchmarks](../benchmarks/README.md): datasets, method comparisons, metric definitions and measured results.
- [Validation records](../validation/README.md): dated tests and their limitations.
- [Historical DAP documentation](history/dapseq-readme-fb60096.md): commands and behavior at revision `fb60096`.

## Develop Genesis

- [Contributor guide](development.md): install a development environment, run checks and test changes.
- [Nextflow conventions](nextflow-style.md): module structure and pipeline changes.
- [Diagram maintenance](diagrams/README.md): update the maintained workflow maps.
- [Curation design](curation/IMPLEMENTATION_BRIEF.md): component ownership, contracts and compatibility.

Current guides describe the installed commands. Historical reports describe the
revision and date written in each report; their commands and temporary paths may
differ from a current installation.
