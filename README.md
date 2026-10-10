# Genesis plant sequencing and curation

Genesis processes plant **DAP-seq** and **paired-end bulk ATAC-seq** into QC reports,
peaks and signal tracks. It also validates artifacts, catalogs scientific provenance,
supports human review, and optionally uses external APIs or private LLM services for
metadata proposals and failure explanations. Use one server or a controller with
independent authenticated workers. Nextflow remains responsible for scientific computation.

## Architecture and Current Capabilities

Follow plant reads through scientific processing to reusable results, then opt into
validation, cataloging and review. Run on one server or distribute independent
datasets across authenticated workers.

[![Genesis architecture: plant reads and explicit references enter DAP-seq or bulk ATAC-seq pipelines; results feed validation, registry, human review and reviewed export. Optional AI exchanges evidence and proposals; a controller supports local or SSH workers.](docs/images/genesis_architecture_overview.svg)](docs/images/genesis_architecture_overview.svg)

**AI is optional.** Models suggest metadata and explanations; deterministic checks
and accountable human review govern changes. Core processing and manual curation
work without AI. [Open the full-size, editable diagram](docs/images/genesis_architecture_overview.svg).

**Implemented** means code is available. **Validated** names the evidence and its
limits. **Planned** identifies remaining validation, not completed work. Evidence
snapshot: **2026-10-09**.

| Capability | Implemented | Validated | Planned / next validation |
| --- | --- | --- | --- |
| [DAP-seq](docs/usage/dapseq-reference.md) / [bulk ATAC-seq](docs/usage/bulk-atac.md) | Yes | Historical Docker runs and public ATAC subsets; current regressions ([scientific evidence](validation/reports/supported-atac-execution-validation.md), [current checks](validation/reports/hybrid-llm-validation.md)) | — |
| [Controller / workers](docs/usage/execution.md) | Yes | Local isolation, retries, recovery and deployment-profile parsing ([evidence](validation/reports/supported-atac-execution-validation.md)) | Live SSH / scheduler site acceptance |
| [Validation / registry](docs/usage/curation.md) | Yes | Binary formats, provenance, migrations, backup/restore and installed-package checks ([evidence](validation/reports/hybrid-llm-validation.md)) | — |
| [QC / human review / export](docs/usage/curation.md) | Yes | Offline workflow, stale-decision rejection, export eligibility and immutable history ([evidence](validation/reports/hybrid-llm-validation.md)) | — |
| [Metadata / AI assistant / diagnosis](docs/usage/ai-providers.md) | Yes | Synthetic cases, mock providers and fake HTTP; real biological accuracy **not evaluated** ([evidence](validation/reports/hybrid-llm-validation.md)) | Live provider acceptance and expert-reviewed metadata evaluation |
| [Private LLM deployment](docs/usage/llm-deployment.md) | Yes | Offline lifecycle, resource conflicts, ownership and failure simulations; live GPU/SSH **not run** ([evidence](validation/reports/hybrid-llm-validation.md)) | Real GPU / SSH deployment acceptance |

## Contents

- [Architecture and Current Capabilities](#architecture-and-current-capabilities)
- [Install and check your environment](#install-and-check-your-environment)
- [Try the complete offline tutorial](#try-the-complete-offline-tutorial)
- [Process DAP-seq](#process-dap-seq)
- [Process bulk ATAC-seq](#process-bulk-atac-seq)
- [Run on a cluster or independent workers](#run-on-a-cluster-or-independent-workers)
- [Validate inputs and artifacts](#validate-inputs-and-artifacts)
- [Import, search and back up the registry](#import-search-and-back-up-the-registry)
- [Assess QC, review and export](#assess-qc-review-and-export)
- [Configure mock, API or private providers](#configure-mock-api-or-private-providers)
- [Harmonize metadata with evidence](#harmonize-metadata-with-evidence)
- [Ask read-only catalog questions](#ask-read-only-catalog-questions)
- [Inspect and deploy a private model](#inspect-and-deploy-a-private-model)
- [Diagnose a failed job](#diagnose-a-failed-job)
- [Create figures and benchmark methods](#create-figures-and-benchmark-methods)
- [Validation, troubleshooting and rollback](#validation-troubleshooting-and-rollback)

## Install and check your environment

Install [Pixi](https://pixi.sh/) and make your chosen container runtime available to
your existing user. Standalone scientific execution defaults to local Docker.
Do not run installation or analysis as root.

```bash
git clone https://github.com/YaoxiangLi/genesis-preprocessing.git
cd genesis-preprocessing
pixi run install-all
pixi run genesis doctor
pixi run genesis --help
```

Pixi supplies Nextflow and uv; the Python project uses Python **3.14 or newer**.
`pixi run genesis` invokes the existing controller CLI. An installed Python wheel
also exposes `genesis` and the existing `genesis-tools` task helpers. Curation and
HTTP inference have no torch/vLLM dependency. Private model serving uses a separate
pinned runtime and an already available Docker image.

Commands below run from this checkout. Replace uppercase IDs/hashes and example
paths with recorded values. Curation/AI commands print JSON by default and accept
`--json`; use `--help` on each subcommand. First-time environment installation can
need network access; the subsequent offline tutorial does not.

## Try the complete offline tutorial

This creates two tiny, explicitly synthetic DAP/ATAC artifact catalogs, verifies
their files, imports them, proposes metadata with a mock provider, demonstrates
individual review/apply, assesses QC, exports the selected catalog, diagnoses a
synthetic log, and checks backup/restore. It runs no sequencing pipeline or model.
It approves only the two newly created synthetic fixtures, with that limitation
recorded in every decision.

```bash
pixi run uv run --frozen --project genesis_tools python \
  examples/curation/offline_workflow.py /tmp/genesis-curation-demo
pixi run genesis registry search /tmp/genesis-curation-demo/catalog
```

Choose a **new** directory each time. Expect `status: PASS`, two selected/included
datasets, six demonstration decisions and files `reviewed.json`, `diagnosis.json`,
`backup.sqlite`, and `acceptance.json`. The reported pipeline/live-inference status
is `NOT RUN`. To create fixtures for a step-by-step manual exercise instead:

```bash
pixi run uv run --frozen --project genesis_tools python \
  examples/curation/create_demo.py /tmp/genesis-manual-demo
pixi run genesis registry init /tmp/genesis-manual-demo/catalog
pixi run genesis registry import /tmp/genesis-manual-demo/catalog \
  --bundle /tmp/genesis-manual-demo/bundle.json
```

The workflow script is a runnable example of the commands described below.
Synthetic structural correctness is not evidence of real biological quality.

## Process DAP-seq

Supply a tab-separated sheet with exactly these columns:

```tsv
sample_id	species	read1_url	read2_url	control_sample	reference_fasta
treatment	Arabidopsis_thaliana	https://example.org/treatment.fastq.gz	-	control	TAIR10.fa.gz
control	Arabidopsis_thaliana	https://example.org/control.fastq.gz	-	-	TAIR10.fa.gz
```

Replace the example URLs with actual public FASTQs. Use `-` for an absent mate or
control. Controls must occur in the same sheet and match species, layout and
reference. Place the exact named gzipped FASTA in your reference directory; Genesis
does not choose/download a replacement assembly. Derived references carry checksum
provenance; stale/unproven cached products stop the run.

```bash
pixi run genesis validate inputs dap.tsv --assay DAP-seq --references /data/references
pixi run pipeline -w /scratch/genesis -n study-A dap.tsv --references /data/references
pixi run pipeline -w /scratch/genesis -n study-A dap.tsv --references /data/references -resume
```

Results are in `/scratch/genesis/study-A/output/`, intermediates in `work/`, and
Nextflow reports in `trace/`. Retain the work directory for resume. Treatment
libraries receive control-based peaks/quantification; controls receive QC/tracks.
The existing read, MAPQ, duplicate, SPP and peak-calling policies remain explicit
and unchanged by curation or AI.

![DAP-seq workflow](docs/images/genesis_metro_map_animated.svg)

[Complete DAP input, output and scientific-policy guide](docs/usage/dapseq-reference.md).

## Process bulk ATAC-seq

Use one row per paired-end technical lane with these exact TSV columns:

```text
library_id sample_id biological_replicate lane_id reference_id read1 read2 read1_sha256 read2_sha256 mapq duplicates adapter_r1 adapter_r2
```

The displayed names are space-separated for readability; the actual sheet must
use tabs. `read1/read2` are local gzipped FASTQs or public HTTPS URLs; SHA256 hashes
refer to compressed files. `mapq` is the approved threshold (0–254), `duplicates`
is `retain` or `exclude`, and both adapter fields are `-` when no trimming is chosen.
Repeated library IDs combine technical lanes only; biological replicates stay separate.

Supply `references.json` with `schema_version: 1` and a `references` list. Each
entry declares `reference_id`, species, assembly, annotation release, exact gzipped
FASTA/TSS paths and SHA256 values, positive effective `genome_size` with its method,
and separate mitochondrial/plastid contig lists. TSS rows are contig, **zero-based**
position and strand. Derive them from the recorded annotation; do not invent TSS or
organellar assignments. Stage authenticated inputs locally before constructing sheets.

```bash
pixi run genesis validate inputs atac.tsv --assay bulk-ATAC --references references.json
pixi run pipeline-atac atac.tsv --references references.json --outdir /scratch/atac-run
pixi run pipeline-atac atac.tsv --references references.json --outdir /scratch/atac-run --resume
```

Each library publishes raw-read/alignment QC, fragments, raw Tn5 cut-count bigWig,
MACS3 peaks, enrichment/complexity metrics and MultiQC. Run-level files record inputs,
checksums, comparisons and provenance. Changed sheets/references require a new run
folder. A zero-peak result can be structurally valid. No universal plant QC threshold
or single-cell barcode processing is implied.

![Bulk ATAC workflow](docs/images/genesis_atac_metro_map_animated.svg)

[Exact column/reference definitions and output paths](docs/usage/bulk-atac.md).

## Run on a cluster or independent workers

For scheduler execution, copy a site template from `conf/sites/` outside the checkout,
set authorized account/partition/resources/paths, and select the profile explicitly:

```bash
pixi run pipeline-atac atac.tsv --references references.json \
  --profile slurm,apptainer --config /local/site.config --outdir /scratch/atac-run
pixi run pipeline -p slurm,apptainer dap.tsv -c /local/site.config
```

Profiles also cover Sherlock, NERSC, PBS Pro, LSF and SGE; see the
[execution guide](docs/usage/execution.md) for site/runtime requirements. Inputs,
checkout and work paths must be visible to scheduler tasks. Site access/authorization
is not established by local tests.

For independent servers, stage inputs with your approved transfer tools and install
the same pinned clean checkout on each worker. A minimal campaign configuration is:

```json
{
  "schema_version": 1,
  "workers": {
    "worker-A": {
      "transport": "ssh", "host": "existing-ssh-alias", "slots": 1,
      "repo": "/project/genesis",
      "python": "/project/genesis/genesis_tools/.venv/bin/python",
      "root": "/scratch/genesis-jobs"
    }
  },
  "jobs": [{
    "id": "library-1", "worker": "worker-A",
    "payload": {
      "git_sha": "REPLACE_WITH_FULL_40_CHARACTER_COMMIT",
      "inputs": [{"path": "/data/atac.tsv", "sha256": "REPLACE_WITH_SHA256"},
                 {"path": "/data/references.json", "sha256": "REPLACE_WITH_SHA256"}],
      "argv": ["/absolute/path/to/pixi", "run", "pipeline-atac", "/data/atac.tsv",
               "--references", "/data/references.json", "--outdir", "/scratch/library-1", "--resume"]
    }
  }]
}
```

Use `transport: local` without `host` for the same protocol on one server. Include
all input/config hashes. One ATAC job includes a library's lanes; shared-control
DAP treatments should share one job. Paths are worker-local; no shared filesystem
or implicit data transfer is assumed. `slots` limits job count, not RAM/GPU use.

```bash
pixi run genesis run /local/campaign --manifest campaign.json
pixi run genesis status /local/campaign
pixi run genesis issues /local/campaign
pixi run genesis resume /local/campaign
pixi run genesis serve /local/campaign --port 8765
```

The read-only page binds to `127.0.0.1`. Confirmed exit-75 failures have at most two
automatic retries. Other failures need review; `UNKNOWN` retains capacity and
prevents duplicate submission. After correcting a confirmed failure:

```bash
pixi run genesis resolve /local/campaign library-1 --note 'Cause corrected; retry approved'
pixi run genesis resume /local/campaign
```

If a supervisor was lost, independently verify its processes/scheduler jobs have
stopped before `genesis reconcile ... --confirmed-stopped --note ...`. A fresh
heartbeat blocks reconciliation. Changed inputs/resources require a new campaign;
never edit an existing campaign to smuggle in new configuration.

## Validate inputs and artifacts

Validation, execution success, scientific QC, metadata approval and export eligibility
are separate statuses. Run artifact validation on the machine holding the files:

```bash
pixi run genesis validate run /scratch/atac-run --assay bulk-ATAC \
  --source-id study-A --study study-A --worker worker-A --output inspection.json
pixi run genesis validate run /scratch/atac-run --assay bulk-ATAC \
  --source-id study-A --study study-A --worker worker-A --level full \
  --bigwig-python /absolute/track-environment/bin/python \
  --max-bytes 10737418240 --max-records 10000000 --max-seconds 1800 \
  --output validated.json
# DAP adapters additionally need the executed sheet and reference directory:
pixi run genesis validate run /scratch/genesis/study-A --assay DAP-seq \
  --source-id study-B --worker worker-A --sheet /data/dap.tsv \
  --references /data/references --output dap-inspection.json
pixi run genesis validate manifest validated.json --json
```

Metadata-level inspection is the default. Full scans explicitly check hashes,
references, interval bounds/order, declared BAMs, bigWigs and metric semantics within
budgets. Install pyBigWig only in the separately selected track interpreter; Genesis
does not install a reader automatically. Partial scans report `NOT_EVALUATED` and
cannot claim completeness. Optional/pruned outputs differ from corrupt files;
missing measurements differ from zero. Historical DAP evidence can remain incomplete.

Exit 0 means the requested check found no errors; it is not scientific approval.
Exit 1 indicates structural errors, 2 invalid input, and 3 an incomplete full scan.
Use new output filenames for new observations. Repeated scans with changed bytes
invalidate old evidence/review. See [validation contracts and budgets](docs/usage/curation.md).

## Import, search and back up the registry

Keep the registry on **controller-local disk**, separate from campaign `state.sqlite`.
Transfer validated JSON bundles explicitly; workers never write a shared SQLite file.

```bash
pixi run genesis registry init /local/catalog
pixi run genesis registry import /local/catalog --bundle validated.json
pixi run genesis registry import /local/catalog --campaign /local/campaign
pixi run genesis registry search /local/catalog --filter assay=bulk-ATAC \
  --filter availability=available --text leaf --limit 100
pixi run genesis registry show /local/catalog DATASET_ID
pixi run genesis registry history /local/catalog DATASET_ID --limit 100 --after 0
pixi run genesis registry search /local/catalog --filter study=study-A --format tsv
pixi run genesis registry backup /local/catalog --output catalog-backup.sqlite
pixi run genesis registry restore /local/restored-catalog --backup catalog-backup.sqlite
```

Filters include species, assay, study, reference_id, worker, availability and
biological_context; add `--qc-status` or `--review-status --category metadata|qc|eligibility`.
Follow `next_after` with `--after` for pagination. Search is literal text, never model
SQL. Dataset/library IDs, accessions, lanes and job attempts remain distinct.
`/data/file.bw` on two workers is two locations, even if the bytes match.

Imports are transactional/idempotent and preserve decisions. Schema upgrades run
through `registry init`, which takes a pre-migration backup. Restore uses a new
folder. Large sequencing files remain outside the database. To inspect any immutable
record by its version: `genesis registry show /local/catalog VERSION --kind invocation`
(or `proposal`, `diagnosis`, `deployment`, `source`, etc.).

## Assess QC, review and export

```bash
pixi run genesis qc evaluate /local/catalog DATASET_ID
pixi run genesis review queue /local/catalog --category metadata
pixi run genesis review show /local/catalog DATASET_ID
```

The shipped plant policy leaves biological thresholds **UNSPECIFIED**. It preserves
units, metric definitions, denominators and depth; missing/incompatible values do
not become passes. Use `qc evaluate ... --policy reviewed-policy.json` for an
explicitly authored/versioned policy. Reassessment does not rerun sequencing.

Review selected evidence and save `evidence.json` with exact stored references:

```json
{"evidence":[{"location":"/data/source.json","worker":"local",
  "sha256":"REPLACE_WITH_RECORDED_SHA256","locator":"/tissue"}]}
```

A locator is a JSON pointer, `line:N`, or `$` for a whole recorded source/artifact.
Use the fresh `status.token` from `review show` **after each change/decision**:

```bash
pixi run genesis review approve /local/catalog DATASET_ID --category metadata \
  --token CURRENT_TOKEN --reason 'State what the reviewed evidence establishes' --evidence evidence.json
pixi run genesis review approve /local/catalog DATASET_ID --category qc \
  --token NEW_TOKEN --reason 'Record the QC judgment and any exception' --evidence evidence.json
pixi run genesis review approve /local/catalog DATASET_ID --category eligibility \
  --token NEWEST_TOKEN --reason 'Accepted for this catalog purpose' --evidence evidence.json
pixi run genesis review history /local/catalog DATASET_ID
pixi run genesis registry search /local/catalog --filter study=study-A \
  --selection-output selected.json
pixi run genesis registry export /local/catalog --selection selected.json \
  --reviewed --output reviewed-catalog.json
pixi run genesis serve /local/campaign --registry /local/catalog --port 8765
```

`reject`/`request-info` use the same category/token/reason interface. Reviewer identity
comes from the OS, never an LLM field. Shared accounts cannot distinguish humans.
Source/manifest/policy changes invalidate affected approvals; corruption cannot be
waived. `resolve` authorizes an execution retry, not QC approval.

Inspect the explicit selection before export; it is one search page, not an implicit
whole catalog. Reviewed exports include candidates, exclusions, missing evidence,
exceptions, exact denominators, metadata/source revisions and decisions. They are
manifest catalogs, not copied sequencing files or training arrays. Omitting
`--reviewed` produces an ungated bundle. [Detailed review/export instructions](docs/usage/curation.md).

## Configure mock, API or private providers

```bash
pixi run genesis ai providers list --config examples/curation/providers.mock.json
pixi run genesis ai providers check /local/catalog \
  --config examples/curation/providers.mock.json --provider mock
```

For live inference, copy [providers.live.example.json](examples/curation/providers.live.example.json)
outside the checkout, then set the approved endpoint/model, credential reference,
tasks, source classifications, limits and capabilities. The adapter uses
OpenAI-compatible **Chat Completions**. External services require HTTPS; private
HTTP endpoints must use loopback, normally through an SSH tunnel. Credentials are
existing environment-variable names or owned `0600` file references, never literal
keys in configuration or command arguments.

```bash
pixi run genesis ai providers check /local/catalog --config /local/providers.json --provider api
pixi run genesis ai providers check /local/catalog --config /local/providers.json --provider private
```

`mode` is `disabled`, `mock` or `live`. Choose a provider explicitly per operation.
Local-only data cannot fall back to an external API. Context/output budgets,
timeouts, concurrency limits, bounded retries, redaction and local schema validation
apply to requests. JSON Schema/tool/streaming capabilities are probed independently
when declared. Unknown capabilities/usage/cost stay unknown; mock success is labeled
`MOCK_PASS`. Failed responses remain available through their invocation version.
[All configuration fields, failure handling and provenance](docs/usage/ai-providers.md).

## Harmonize metadata with evidence

```bash
pixi run genesis metadata ingest /local/catalog DATASET_ID \
  --source metadata.json --source paper-excerpt.txt --classification local-only
pixi run genesis metadata propose /local/catalog DATASET_ID --output proposal.json
# Optional: replace deterministic-only proposal generation with an explicit provider.
pixi run genesis metadata propose /local/catalog DATASET_ID \
  --config /local/providers.json --provider private --output ai-proposal.json
pixi run genesis metadata diff /local/catalog DATASET_ID --target PROPOSAL_VERSION
```

Local JSON/CSV/TSV/text and explicit public ENA/GEO accessions are supported; use
`metadata ingest ... --accession SRR123456 --classification public` for bounded
network retrieval. Never represent an inaccessible paper as read.

Proposals retain raw/current values, candidate status, vocabulary versions, exact
source hashes/locators/quotes and rationale. Unknown treatment stays unknown;
technical lanes and biological replicates remain separate. DAP TF-source organism
and assayed DNA organism are distinct. Ambiguous ATAC/GRO/5-prime protocols enter
review. Unknown author terms are preserved without invented ontology IDs.

Review the diff and `proposal.data.evidence`, then save that evidence array as
`{"evidence":[...]}`. Approval targets the exact proposal; version 2 application is separate:

```bash
pixi run genesis review show /local/catalog DATASET_ID
pixi run genesis review approve /local/catalog DATASET_ID --category metadata \
  --target PROPOSAL_VERSION --token CURRENT_TOKEN --reason 'Explain the reviewed mapping' \
  --evidence evidence.json
pixi run genesis metadata apply /local/catalog DATASET_ID --target PROPOSAL_VERSION \
  --output canonical-metadata.json
```

Until apply, status is `PENDING_APPLY`. Apply creates an immutable metadata revision
and a compiled input description referencing the original scientific inputs.
It never changes executed sheets, reference/control assignments or campaigns.
Reassess QC/eligibility afterward. For entirely manual corrections, supply
`metadata propose --fields curated-fields.json` with evidence-backed field entries;
[the guide explains the exact field format and legacy manual proposal behavior](docs/usage/curation.md#evidence-backed-metadata-harmonization).

## Ask read-only catalog questions

```bash
pixi run genesis registry search /local/catalog --text leaf --limit 10
pixi run genesis ai ask /local/catalog 'What tissue and treatment evidence is recorded?' \
  --dataset DATASET_ID --config /local/providers.json --provider private \
  --classification local-only
```

Select 1–10 datasets explicitly. Answers cite selected record hashes and use bounded
read-only catalog tools. They cannot query arbitrary SQL, launch jobs, approve data,
edit policies or run shell commands. Source instructions are treated as untrusted
data. Read the evidence before relying on an interpretation.

## Inspect and deploy a private model

Use existing authorized Linux nodes and separately pinned serving environments.
Docker/NVIDIA access, a digest-pinned local vLLM image, an external `hf` CLI, existing
node-local secret files, reviewed license/access and adequate resources are prerequisites.
Genesis does not provision them. Multiple serving nodes are independent endpoints;
cross-host model sharding and public listeners are not supported.

```bash
# Read metadata, resolve an immutable revision; no weight download.
pixi run genesis ai model inspect NAMESPACE/MODEL --revision REVISION --output model.json
# Copy/edit the template with your actual node, image digest, budgets and reviewed model.
pixi run genesis ai deployment plan --config /local/deployment.json \
  --model model.json --output plan.json
# Only after reviewing the complete plan: authorize this exact plan hash.
pixi run genesis ai deployment apply /local/catalog --plan plan.json --authorize EXACT_PLAN_HASH
pixi run genesis ai deployment status /local/catalog --plan plan.json
pixi run genesis ai deployment logs /local/catalog --plan plan.json
pixi run genesis ai deployment stop /local/catalog --plan plan.json
pixi run genesis ai deployment status /local/catalog --plan plan.json
```

Start from [deployment.example.json](examples/curation/deployment.example.json), which
contains synthetic placeholders and is not a production recommendation. Set existing
worker paths/SSH alias, physical GPU UUIDs, CPU/RAM/disk/VRAM reservations, context and
concurrency, KV/runtime overhead, compatible architectures, license confirmation,
secret-file references and allocation expiry when applicable. Prefer dedicated GPUs;
shared nodes need explicit separate pipeline reservations. Reusing campaign `slots`
alone does not allocate RAM/GPUs.

Apply stages only revision-pinned selected model files, verifies their hashes and
starts a separately supervised owned container. Host binding is loopback-only;
remote status opens/checks an authenticated owned SSH tunnel. Readiness needs real
structured inference from the expected model. `UNKNOWN` retains reservations;
controller restart/repeated apply cannot duplicate the server. Stop verifies
ownership and preserves caches/logs. A changed model/context/config needs a new plan.
No automatic OOM fallback or scientific parameter change is permitted.

A vLLM API key does not protect all routes. This backend uses container isolation
and loopback/SSH networking; broader exposure requires a separately secured site
gateway. [Deployment configuration, state machine, recovery and rollback](docs/usage/llm-deployment.md)
explain every prerequisite and limit. Real GPU/SSH/API acceptance remains opt-in.

## Diagnose a failed job

```bash
pixi run genesis ai diagnose /local/catalog --root /scratch/atac-run \
  --log .nextflow.log --log work/ab/task/.command.err \
  --dataset DATASET_ID --output diagnosis.json
# Optional model explanation; deterministic classification still runs first.
pixi run genesis ai diagnose /local/catalog --root /scratch/atac-run \
  --log .nextflow.log --config /local/providers.json --provider private
```

Use `--facts diagnostic-facts.json` for measured exit/worker/resource facts and
campaign/job/attempt identity. Exit 137 alone is not confirmed OOM. Remote collection
uses `--worker-config worker.json --worker-id worker-A` and approved diagnostic roots.
Only 16 explicitly selected logs and their last 64 KiB each are collected/redacted;
there is no recursive filesystem upload.

The result separates deterministic evidence from optional model hypotheses and
proposes a typed action with preconditions. It **never executes a retry or repair**.
Recheck evidence/target versions, reconcile uncertain workers, and use the existing
review/retry mechanism. Resources or input changes require a new campaign.
[Diagnostic categories, evidence and limitations](docs/usage/curation.md#failure-diagnosis).

## Create figures and benchmark methods

```bash
pixi run genesis schematic --workflow atac --output atac.svg
pixi run genesis schematic --workflow execution --theme dark --animate --output execution.svg
pixi run genesis schematic --workflow dap --template dap-template.json
pixi run genesis schematic --spec dap-template.json --output edited-dap.svg
pixi run benchmark --help
pixi run benchmark plan --help
pixi run benchmark run --help
pixi run benchmark compare --help
pixi run benchmark report --help
```

With the benchmark's required pinned images already present, a synthetic
post-alignment comparison can be prepared and run explicitly:

```bash
pixi run benchmark fixture --out /scratch/benchmark-fixture
pixi run benchmark plan /scratch/benchmark-fixture/experiment.toml
pixi run benchmark run /scratch/benchmark-fixture/experiment.toml --out /scratch/benchmark-run
pixi run benchmark run /scratch/benchmark-fixture/experiment.toml --out /scratch/benchmark-run --resume
pixi run benchmark report /scratch/benchmark-run
pixi run benchmark compare /scratch/candidate-run --against /scratch/reference-run
```

The last command needs two completed runs with matching source bytes/reference.
Public input acquisition is a separate `benchmark fetch` step for a fully resolved,
READY dataset manifest with exact sizes and hashes; unresolved catalog candidates
are refused. Inspect `benchmark fetch --help` and the catalog blockers first.

Schematics are self-contained SVGs with bundled licensed artwork; animations show
workflow connections, not live state. [Figure templates and options](docs/usage/schematics.md).
Benchmark `fixture|plan|fetch|run|compare|report` commands compare explicit methods
using retained inputs and common metrics. Planning does not fetch or run workflows;
follow the [benchmark recipes](benchmarks/README.md) to prepare a spec, execute the
selected experiments and inspect reports. Benchmark evidence does not silently
change production scientific policies.

## Validation, troubleshooting and rollback

```bash
pixi run checks
pixi run uv run --frozen --project genesis_tools python tests/evaluate_metadata.py
# Separate opt-in real scientific-container acceptance:
pixi run validate-docker --keep
pixi run validate-atac --keep
```

The fast suite includes scientific regressions, contracts, registry migration,
review, fake HTTP, metadata evidence and model lifecycle simulations. Installed-wheel
acceptance checks packaged schemas/prompts/vocabularies outside the repository.
Synthetic gold fixtures report field/evidence/conflict/abstention results; real
biological accuracy, human corrections, API charges and GPU performance stay unmeasured.
[Foundations evidence](validation/reports/curation-foundations-validation.md) and
[hybrid extension evidence](validation/reports/hybrid-llm-validation.md) distinguish
PASS, FAIL, BLOCKED and NOT RUN and record commands/revisions/limitations.

| Symptom | Next step |
| --- | --- |
| Docker unavailable | Run `genesis doctor`; use an existing authorized runtime/profile. |
| Input/reference checksum changed | Investigate and create a new explicit input/run revision. |
| Full validation incomplete | Inspect findings, reader availability and scan budgets; do not call it a pass. |
| Approval is stale | Inspect the current diff/evidence and obtain a fresh review token. |
| Export contains no datasets | Read exclusions and candidate denominators; approvals/validation may be missing. |
| Provider unavailable or schema rejected | Inspect the saved invocation; adjust the explicit approved config or use manual curation. |
| Service UNKNOWN or tunnel lost | Restore access, inspect status/ownership and keep reservations until termination is known. |
| Model OOM/startup failure | Inspect logs and plan a reviewed resource/model configuration; no automatic fallback occurs. |
| Nextflow plugin registry unavailable | Restore access or use verified pinned cached plugins; never skip scientific checks. |

To roll back the registry, stop writes and restore a consistent pre-migration backup
into a new directory with the corresponding code revision. Preserve external
artifacts, source bundles, plans and node caches. Stop and confirm owned model
services before reverting their code/resources; disabling providers alone does
not stop them. Existing preprocessing remains usable with all optional curation/AI
commands omitted. No production policy changes are required by this extension.

Optional live acceptance has separate runners, deliberately excluded from `checks`:

```bash
pixi run uv run --frozen --project genesis_tools python tests/accept_provider_live.py \
  --registry /local/catalog --config /local/providers.json --provider api \
  --authorize-egress public --output live-provider-acceptance.json
pixi run uv run --frozen --project genesis_tools python tests/accept_llm_live.py \
  --registry /local/catalog --plan acceptance-plan.json --authorize EXACT_PLAN_HASH \
  --config /local/providers.json --provider private --timeout 300 \
  --output live-deployment-acceptance.json
```

The first sends a bounded public probe; the second downloads/launches the exact
reviewed plan, checks real inference and safely stops its owned service. Run them
only with approved credentials, budgets and hardware. Neither has been represented
as passed by the offline tests.
