# Validate, catalog and review published datasets

Curation is an explicit, offline step after DAP-seq or bulk ATAC processing.
It adds artifact validation, a local scientific registry, reproducible QC
assessments and manual review. Existing pipeline inputs, scientific settings,
outputs, retries and resume behavior remain unchanged. There is no LLM dependency.

Install with `pixi run install-all`. Use `pixi run genesis` in this checkout, or
the installed `genesis` command in the Python environment containing the wheel.
All new command families support `--help` and `--json`. Successful commands emit
JSON by default; search also supports `--format tsv`.

## Five independent states

| State | Owner | Meaning |
| --- | --- | --- |
| Execution | Campaign `state.sqlite` | What happened to a processing attempt |
| Structure | Versioned validation | Which declared files and evidence were checked |
| Scientific QC | Versioned assessment | Measurements interpreted under an explicit policy |
| Metadata review | Immutable decisions | A person's review of exact metadata/source versions |
| Export eligibility | Decision and export profile | Acceptance for a particular catalog purpose |

`SUCCEEDED` does not mean accepted. Zero peaks can be structurally valid.
A reviewer cannot waive structural errors. `resolve` still authorizes an
execution retry; it does not approve scientific quality or curation.

## Validate existing inputs and published runs

Input checks delegate to the existing validators and keep their requirements:

```bash
pixi run genesis validate inputs samples.tsv --assay bulk-ATAC \
  --references references.json --json
pixi run genesis validate inputs dap.tsv --assay DAP-seq \
  --references /data/references --json
```

For published runs, use a stable source namespace and the actual worker identity.
Reusing that namespace and library name identifies a new revision of the same
dataset. Different studies with overlapping sample names need different namespaces.
Internal dataset IDs are separate from accessions, library names, lanes and jobs.

```bash
# Execute on the machine that holds these artifacts.
pixi run genesis validate run /data/atac-run --assay bulk-ATAC \
  --source-id study-A --study study-A --worker local \
  --output atac-inspection-v1.json --json

# Explicit full inspection with a separately installed bigWig reader.
pixi run genesis validate run /data/atac-run --assay bulk-ATAC \
  --source-id study-A --study study-A --worker local --level full \
  --bigwig-python /path/to/track-environment/bin/python \
  --max-bytes 10737418240 --max-records 10000000 --max-seconds 1800 \
  --output atac-validation-v1.json --json

pixi run genesis validate run /data/dap-run --assay DAP-seq \
  --source-id study-B --study study-B --worker local \
  --sheet /data/dap.tsv --references /data/references \
  --output dap-inspection-v1.json --json
```

The DAP run directory is the directory containing `output/`, not the pipeline
workspace above it. ATAC uses its runner directory containing `manifest.json`,
`provenance.json` and `output/`. Adapters preserve lanes, shared-control assignments,
raw source snapshots and available QC definitions. DAP controls have no required
treatment peak outputs. ATAC provenance must match the stored run manifest digest.

Historical DAP MultiQC provenance lacks complete input/resource/container evidence.
Its import remains incomplete even when all surviving files are readable. No
success or missing scientific measurement is invented. The default reviewed
export excludes these incomplete records. An explicitly authored export profile
can allow incomplete evidence for an appropriate catalog purpose; it still cannot
allow a known structural error. Such an export is not full model-readiness evidence.

Metadata inspection checks declarations and local availability; it is not a full
validation pass. Full inspection hashes bytes and scans supported formats. Defaults
are 1 GiB of scanned bytes, one million records and 300 seconds per bundle. Scanned
bytes include rereads and decompression; they are not network bytes. Zero disables
the byte or record limit, while the time limit must remain finite and positive.
An exhausted budget or unavailable reader yields `NOT_EVALUATED`, not a pass.
Documents/snapshots are limited to 32 MiB; split larger imports into bundles.

Checks cover reference contigs/lengths and declared BED0 TSS points; BAM headers
and declared coordinate sorting/index availability; BED/narrowPeak coordinates,
ordering and finite values; bigWig readability, contigs, finite signals and declared
count/normalization semantics; source-backed metrics and required published outputs.
No TSS annotation, cell barcode or plant threshold is synthesized. BAMs are checked
when declared, not required as new published outputs. Optional pruned intermediates
remain `intentionally_pruned`, distinct from unavailable required artifacts.

bigWig parsing uses `pyBigWig` in the explicitly selected track interpreter,
via a bounded local subprocess. Keep that binary dependency outside core Python
3.14; the existing track environment is pinned separately. This command does not
install it. Selecting another worker name does not connect to that worker: run
the validator there and transfer only the resulting JSON through approved means.
`/data/a.bw` on two workers is two locations even if both have identical digests.

For authored records or repeat scans:

```bash
pixi run genesis validate manifest bundle.json --json
pixi run genesis validate manifest bundle.json --scan --level full --worker worker-A \
  --bigwig-python /path/to/track-environment/bin/python --output recheck-v2.json --json
```

Without `--scan`, this validates only the JSON contract and content digests.
Record schemas ship in `genesis_tools/contracts/schemas/records-v1.json`.
`contracts.records` provides typed manifest, finding, measurement, proposal,
assessment and decision records. Unknown versions, extra contract fields, malformed
types, duplicate JSON keys, NaN and stale nested hashes are rejected. Flexible
descriptive metadata and legacy lane dictionaries retain their source fields.
Use `record()`/typed `.export()` to seal authored records; never hand-edit a hash.

Run adapters declare `metadata.output_contract = genesis-published-v1`, which checks
the existing assay's required output roles. Authored generic manifests describe
their own artifact set; full validation of that set is not a claim that a complete
assay or every possible model input has been provided. Export profiles can require
specific roles in addition to review and full structural validation.

Exit codes: **0** for valid requests without found errors (including metadata-only
inspection), **1** for structural findings with errors, **2** for invalid requests,
and **3** for an incomplete requested full scan. Inspect findings and `complete`;
never interpret metadata-level exit 0 as scientific acceptance. Output bundles are
immutable: use a new output filename for a new observation.

## Import, search and inspect provenance

Keep the scientific registry on the controller's local disk. Do not place SQLite
on a shared worker/NFS filesystem. Workers export bundles, not database writes.
Every write uses a local writer lock and transaction; readers use SQLite snapshots.
Sources, findings, decisions and prior manifests are immutable. Current dataset
projections change only through explicit import, assessment or review operations.

```bash
pixi run genesis registry init /local/catalog --json
pixi run genesis registry import /local/catalog --bundle atac-validation-v1.json --json
pixi run genesis registry import /local/catalog --campaign /local/campaign --json
pixi run genesis registry search /local/catalog --filter assay=bulk-ATAC \
  --filter availability=available --limit 100 --json
pixi run genesis registry search /local/catalog --text 'leaf' --format tsv
pixi run genesis registry show /local/catalog DATASET_ID --json
pixi run genesis registry history /local/catalog DATASET_ID --limit 100 --after 0 --json
```

Structured filters are `species`, `assay`, `study`, `reference_id`, `worker`,
`availability` and `biological_context`. QC/review filters use `--qc-status` or
`--review-status` with `--category metadata|qc|eligibility`. Text search is literal
FTS5 when available, with escaped substring fallback. No SQL supplied by a user
or model is executed. Search and review queues return `next_after`; status filters
apply within each scanned page, so an empty result page can still have a cursor.
Registry history uses an offset; review history returns decision sequence cursors.

Repeat imports of an identical bundle are idempotent and preserve approvals.
A new manifest revision supersedes the current projection and invalidates affected
review. Importing known historical content cannot silently roll the catalog back.
Campaign imports preserve observed jobs/events and worker configuration without
polling or changing execution. They do not reconstruct unavailable past attempts.
The returned `campaign_id` is the full SHA256 of canonical campaign JSON, distinct
from the controller's shortened worker-attempt directory prefix. Supply
`--campaign-id ID --job-id JOB --attempt N` together to `validate run` to link records.

The registry models entities/relations, worker-qualified locations, exact reference
versions in manifests, immutable scientific records and attempt observations.
Invocation/deployment provenance contracts can be imported with `--record`; there
is no provider or deployment operation in this milestone. Sequencing files stay
outside SQLite. Catalog facts describe observations, not continuous filesystem
monitoring: revalidate before consuming artifacts that might have changed.

## Assess QC and review one dataset at a time

```bash
pixi run genesis qc evaluate /local/catalog DATASET_ID --json
pixi run genesis review queue /local/catalog --category metadata --json
pixi run genesis review show /local/catalog DATASET_ID --json
```

The packaged `plant-diagnostic-v1` policy leaves thresholds **UNSPECIFIED**. It
reports `NOT_EVALUATED` or `NOT_APPLICABLE`, rather than converting absent or
incompatible metrics into zero or a pass. A policy records applicability,
metric definition/version, units, denominator, depth, threshold, missing behavior,
severity, rationale, author and evidence. Custom policies use `--policy FILE`;
only fixed declarative comparison operators are supported. Reassessment stores a
new version when evidence or policy changes and never reruns sequencing.

Approve only after inspecting evidence. Put selected references in an evidence
file using their exact recorded location, worker and digest:

```json
{"evidence":[{"location":"/data/atac-run/output/lib/qc/enrichment.json",
  "worker":"local","sha256":"REPLACE_WITH_RECORDED_SHA256","locator":"/FRiP"}]}
```

Locators are JSON pointers into stored sources, `line:N` with one-based line
numbers, or `$` for a whole source/artifact. Fabricated locations, hashes and
unresolvable source locators are rejected. Copy the current `status.token` from
`review show`; obtain a fresh token after each decision or reassessment.

```bash
pixi run genesis review approve /local/catalog DATASET_ID --category metadata \
  --token CURRENT_TOKEN --reason 'Reviewed the named source evidence' --evidence evidence.json
pixi run genesis review approve /local/catalog DATASET_ID --category qc \
  --token NEW_TOKEN --reason 'Document the actual QC judgment or exception' --evidence evidence.json
pixi run genesis review approve /local/catalog DATASET_ID --category eligibility \
  --token NEWEST_TOKEN --reason 'Reviewed for this catalog purpose' --evidence evidence.json
pixi run genesis review history /local/catalog DATASET_ID --json
```

`reject` and `request-info` use the same category/token/reason interface. QC approval
requires a current assessment; a scientific concern can have a documented human
exception. Structural errors always exclude the dataset. Review records the OS
UID, login name, hostname, timestamp, reason, evidence and exact version bindings.
Shared OS accounts cannot distinguish individual humans; use distinct project
accounts when that accountability is required. Hashes detect stale content, not
malicious database administrators. Protect registry files using existing permissions.

Manual descriptive edits use a proposal, never an executed sample-sheet rewrite:

```python
from pathlib import Path
from genesis_tools.contracts.records import MetadataProposal, dump, load

proposal = MetadataProposal(
    dataset_id="DATASET_ID", manifest_version="CURRENT_MANIFEST_SHA256",
    changes={"tissue": "leaf"}, evidence=load(Path("evidence.json"))["evidence"],
    reason="State what the cited source establishes",
).export()
dump(Path("proposal.json"), proposal, immutable=True)
```

```bash
pixi run genesis review propose /local/catalog --file proposal.json
pixi run genesis review diff /local/catalog DATASET_ID --target PROPOSAL_VERSION
pixi run genesis review approve /local/catalog DATASET_ID --category metadata \
  --target PROPOSAL_VERSION --token CURRENT_TOKEN --reason 'Reviewed this diff' \
  --evidence evidence.json
```

Approval creates the canonical metadata revision and makes affected QC/eligibility
stale. Reference, control, MAPQ and other scientific-input edits are not accepted
as descriptive proposals. Use an explicit new scientific run for such changes.

## Export an explicit selection

```bash
pixi run genesis registry search /local/catalog --filter study=study-A \
  --limit 100 --selection-output selection.json --json
pixi run genesis registry export /local/catalog --selection selection.json \
  --reviewed --output reviewed-catalog-v1.json --json
```

Inspect the selection before exporting. It contains exact dataset/manifest
versions and registry identity; it is one search page, not an implicit all-record
selection. For larger selections, collect every intended page and use the
`selection` contract to seal the explicit combined candidates. There is no
approve-all command. Omitting `--reviewed` produces an ordinary, ungated bundle.

The default reviewed profile requires full validation, metadata/QC/eligibility
approval and at least one available artifact with a digest. A custom profile
can add required roles and is supplied with `--profile` both at eligibility
approval and export. A different profile invalidates that eligibility approval.

Reviewed exports are **manifest catalogs**. They include candidates, exclusions,
missing-evidence reasons, QC exceptions, exact candidate/included/excluded counts,
canonical metadata, relevant proposals/assessments/policies, decisions and the
original scientific manifest bundle. They do not copy sequencing files or produce
training arrays. A catalog with zero eligible candidates still succeeds and
reports those exclusions. Importing it imports its scientific bundle; it does
not replay another registry's approvals. Use backup/restore for complete history.

## Read-only status, backup and rollback

```bash
pixi run genesis serve /local/campaign --registry /local/catalog --port 8765
pixi run genesis registry backup /local/catalog --output catalog-backup.sqlite --json
pixi run genesis registry restore /local/restored-catalog --backup catalog-backup.sqlite --json
```

The existing page remains loopback-only with no write endpoints. It escapes
untrusted names and shows campaign-linked curation summaries from a bounded
catalog page (first 1,000 records). Use CLI pagination for complete catalogs.
Approved report links download digest-verified HTML as attachments, not active
HTML on the status origin. Only registered `local` reports under the run's
`output/` root are served, with a 32 MiB limit. Remote reports are never fetched.

`registry init` migrates the local database transactionally and creates a
pre-migration backup for an existing older schema. Backups use SQLite's consistent
backup API, including committed WAL content. Restore requires a new destination
and verifies database/FK integrity and supported schema. To roll back, stop catalog
writes, restore the pre-migration backup into a new directory using the appropriate
software revision, verify it, then point commands at that directory. Do not copy a
live `.sqlite` file alone or delete campaign state. Disabling curation simply means
omitting these commands and `serve --registry`; scientific execution is unaffected.

See the [implementation brief](../curation/IMPLEMENTATION_BRIEF.md) and
[validation report](../../validation/reports/curation-foundations-validation.md)
for scope, exact checks and unrun live scenarios.
