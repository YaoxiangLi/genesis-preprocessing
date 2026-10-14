# Genesis: plant DAP-seq and ATAC-seq processing

Genesis turns plant DAP-seq and paired-end bulk ATAC-seq reads into peaks, signal
tracks and quality-control reports. It runs on a single server or through
Nextflow on a cluster. You can also organize results in a local catalog, review
metadata and QC, and export a selected dataset collection.

Start with the standalone pipeline for your assay. Study management, the catalog
and AI assistance are optional.

<a id="install-and-run"></a>
<a id="environments-and-docker-builds"></a>

## Install and check your environment

Install [Pixi](https://pixi.sh/). For the default execution mode, Docker must
already be available to your user. Run:

```bash
git clone https://github.com/kundajelab/genesis-preprocessing.git
cd genesis-preprocessing
pixi run install-all --install-cli
export PATH="$HOME/.local/bin:$PATH"
genesis doctor
genesis --help
```

Keep `~/.local/bin` on your PATH in new shells. The installer links `genesis` to
this checkout; keep the checkout in place. To use another command directory,
add `--bin-dir /your/bin` to the install command.

After installation, use `genesis` directly. Scientific commands use Pixi
internally for Nextflow and the project runtime. You can also run commands through
`pixi run`. See [installation and upgrades](docs/development.md#command-installation-and-maintenance)
for moving a checkout, using a Python wheel or removing the command.

## Run your first analysis

Run the examples below from the checkout, substituting your input paths. Both
pipelines need an explicitly selected reference genome; Genesis does not choose
or download an assembly for you.

<a id="sample-sheet"></a>

### DAP-seq

Prepare a tab-separated sample sheet with this exact header:

```tsv
sample_id	species	read1_url	read2_url	control_sample	reference_fasta
treatment	Arabidopsis_thaliana	https://example.org/treatment.fastq.gz	-	control	TAIR10.fa.gz
control	Arabidopsis_thaliana	https://example.org/control.fastq.gz	-	-	TAIR10.fa.gz
```

Replace the example URLs. Use `-` for an absent mate or control. Put the named
gzipped FASTA in your reference directory. Each treatment's control must occur
in the same sheet and match its species, reference and read layout.

```bash
genesis validate inputs dap.tsv --assay DAP-seq --references /data/references
genesis pipeline -w /scratch/genesis -n study-A dap.tsv --references /data/references
# Continue the same analysis after an interruption.
genesis pipeline -w /scratch/genesis -n study-A dap.tsv --references /data/references -resume
```

Results appear in `/scratch/genesis/study-A/output/`, grouped by species and
sample. Treatments receive peaks and peak scores; controls receive QC and tracks.
Keep the run's `work/` directory to allow resume.

Read the [DAP-seq guide](docs/usage/dapseq-reference.md) for complete sample-sheet
rules, reference setup, analysis choices and output definitions.

### Bulk ATAC-seq

Prepare one row per paired-end technical lane and a reference registry containing
the FASTA, annotation-derived TSS positions, organellar contigs and checksums.
The [ATAC guide](docs/usage/bulk-atac.md) explains the columns and reference fields.

```bash
genesis validate inputs atac.tsv --assay bulk-ATAC --references references.json
genesis pipeline-atac atac.tsv --references references.json --outdir /scratch/atac-run
genesis pipeline-atac atac.tsv --references references.json --outdir /scratch/atac-run --resume
```

Results appear under `/scratch/atac-run/output/`. Each library has QC reports,
fragments, Tn5 cut-count tracks and peaks. Technical lanes are combined within a
library; biological replicates remain separate. Choose MAPQ, duplicate and adapter
policies in the sample sheet before running.

<a id="analysis-choices"></a>
<a id="outputs-and-resources"></a>

## Find and interpret your results

Start with the MultiQC report, then inspect the library-level QC and signal
tracks. A successful run means the computation finished; it does not establish
that the data are suitable for every biological analysis. In particular, FastQC
flags need interpretation, and zero peaks can be a valid result.

| Output | What it tells you |
| --- | --- |
| MultiQC and library QC | Read quality, alignment summaries and assay-specific measurements |
| Peaks | Regions enriched under the recorded peak-calling and control settings |
| bigWig tracks | Signal across the reference; check whether the track contains normalized coverage or raw cuts |
| DAP peak scores | Read-end RPM and mean coverage RPKM; these are different statistics |
| ATAC fragments and enrichment metrics | Usable paired fragments, fragment FRiP and TSS enrichment |
| Provenance and Nextflow reports | Inputs, analysis settings, software identity and execution records |

See the [DAP output definitions](docs/usage/dapseq-reference.md#outputs-and-resources)
and [ATAC outputs](docs/usage/bulk-atac.md#outputs) before comparing measurements
between tools or studies.

<a id="reference-compatibility-and-development"></a>

## Choose your next task

| I want to… | Start here |
| --- | --- |
| Run DAP-seq or understand its scientific settings | [DAP-seq guide](docs/usage/dapseq-reference.md) |
| Run paired-end bulk ATAC | [Bulk ATAC guide](docs/usage/bulk-atac.md) |
| Run on a cluster or independent servers | [Execution guide](docs/usage/execution.md) |
| Manage a study from inputs through reviewed export | [Study workflow](docs/usage/studies.md) |
| Validate results, search a catalog or review QC | [Curation guide](docs/usage/curation.md) |
| Import single-cell fragments and build pseudobulks | [Single-cell ATAC guide](docs/usage/scatac.md) |
| Prepare scATAC outputs for model loaders | [Model handoff](docs/usage/scatac-model-handoff.md) |
| Propose metadata or explain a failure with an LLM | [AI providers](docs/usage/ai-providers.md) |
| Host a private model on an existing node | [Model services](docs/usage/llm-deployment.md) |
| Compare processing methods and inspect benchmark evidence | [Benchmarks](benchmarks/README.md) |
| Set up a development environment or contribute | [Contributor guide](docs/development.md) |

The [documentation index](docs/README.md) also links to reference material and
validation records. Core processing, catalog queries and manual review work
without AI, a GPU or an API account.

<a id="verification"></a>

## Architecture and current capabilities

Nextflow runs the scientific analysis. The `genesis` CLI supplies input checks,
study management, result validation and review. Independent workers use local or
SSH execution; they do not need a shared filesystem. Optional AI services propose
metadata and explanations for review.

| Capability | Supported use | Validation scope |
| --- | --- | --- |
| DAP and bulk ATAC processing | Standalone and managed-study commands | [Real tools on synthetic inputs](validation/reports/real-study-validation.md); [small public ATAC subsets](validation/reports/supported-atac-execution-validation.md) |
| Single-cell ATAC | Existing fragment ingestion, pseudobulks and model exports | [Fixture and loader tests](validation/reports/scatac-delivery-validation.md); exports require independent scientific review before training |
| Catalog, validation and review | Local registry, metadata/QC decisions, reviewed export | [Offline and installed-package tests](validation/reports/hybrid-llm-validation.md) |
| Independent workers and clusters | Local/SSH transport and scheduler profiles | Local workers tested; test scheduler and SSH access at your site before use |
| AI assistance and private model services | Optional providers and service lifecycle commands | Mock/HTTP/lifecycle tests; live GPU deployment and biological metadata accuracy are unvalidated |

The [validation records](validation/README.md) list tested revisions, environments
and limitations.

## Benchmarks and tool choices

Use [the benchmark guide](benchmarks/README.md) for the experiment matrix, metric
definitions, results and reproduction commands. It distinguishes package comparisons
from parameter sensitivity and software tests. A higher mapping rate or more peaks
alone is not evidence that one method is better.

The [plant comparison report](validation/reports/expanded-plant-comparison.md)
contains 64 completed Arabidopsis method/depth cases, independent TF motif evidence,
biological ATAC replicate measurements, and comparisons of reference assemblies
and annotation releases. Tables distinguish completed results from the ongoing
A. lyrata, sorghum and maize runs. The current evidence does not establish a better
replacement for the BWA-MEM2/MACS3 defaults across assays.
The [complete-workflow comparison](validation/reports/pipeline-method-comparison.md)
scores Genesis and nf-core ATAC using common metric definitions.

## Troubleshooting

| Problem | First step |
| --- | --- |
| `genesis: command not found` | Complete installation with `--install-cli` and check your PATH. |
| Docker or Nextflow is unavailable | Run `genesis doctor`; check the selected runtime and installation. |
| Reference or input checksum differs | Check which file changed. Preserve the old run and use a new input/run version. |
| A resumed run repeats some tasks | Check changed inputs, code and reference-cache paths in the Nextflow trace. |
| No peaks or unexpected QC values | Inspect depth, reference, assay settings and control assignment before changing parameters. |
| A reviewed export is empty | Read its exclusions; validation or current review decisions may be missing. |
| A worker is unreachable | Inspect worker status and reconnect before authorizing another attempt. |
