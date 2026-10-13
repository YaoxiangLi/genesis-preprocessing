# Curation and hybrid-LLM implementation specification

Baseline: `bb16baca5d9bb09bfff8825fc537fcb125809c07`, clean `main` at audit.
The foundations milestone implemented Prompts 0–3. The subsequent authorized
extension implements Prompts 4–8 in this same checkout and publishes reviewed
commits directly to main. Acceptance is offline first; production services, real
API calls and GPU/SSH launches are not part of implementation acceptance.

## Boundaries and ownership

Nextflow remains responsible for scientific computation. Existing DAP and paired-end
bulk ATAC parameters, inputs, published outputs, reference policies, caches and resume
behavior remain unchanged. Curation is explicitly invoked after processing; it never
turns a worker success into an execution failure or authorizes a retry.

Execution state belongs to campaign `state.sqlite`. A separate controller-local
scientific registry owns source snapshots, entities, artifact locations, findings,
measurements, assessments and review history. Links use campaign identity, job and
attempt. Workers never write a controller database. Paths are qualified by worker;
no shared filesystem or implicit data transfer is assumed.

Execution, structural validation, scientific QC, metadata review and eligibility for
a versioned export profile are independent. A reviewer cannot waive corruption.
Missing evidence is unknown, never zero. Plant biological thresholds remain
UNSPECIFIED. Policies assess immutable measurements without rerunning sequencing.

All core curation works offline, without models, credentials or GPUs. Optional LLMs
may propose evidence-backed changes; deterministic validation and accountable human
review remain authoritative. No hidden chain-of-thought is collected. Logs, metadata
and proposed changes are untrusted data. No production runs, model downloads, public
services, credentials, sudo or firewall changes are authorized by implementation.
The user separately authorized reviewable commits and direct publication to main.

## Implementation decisions

- Extend `genesis_tools` with contracts, registry, qc_policy and curation modules.
  Register delegated commands with the current controller dispatcher and an installed
  `genesis` alias. Preserve `genesis-tools` and all current commands.
- Package version 1 JSON Schemas and typed records. Use dataclasses and jsonschema;
  reject unknown versions/types, nonfinite values and remote schema resolution.
- Adapt existing validators in one direction: curation imports existing code;
  staged scientific helpers do not import curation dependencies.
- Explicit validation emits immutable bundles. Metadata-level inspection is the
  default; full scans are explicit and report budgets/completeness. Artifact retention
  and assay role determine requirements. Zero peaks and unpublished/pruned BAMs are
  not corruption. bigWig checks use an explicitly selected Python in the pinned track
  environment, outside the core interpreter.
- Registry imports are atomic and idempotent, preserve incomplete history and raw
  names, and use stable source namespaces. SQLite migrations, foreign keys, bounded
  writer locks, literal search, pagination, backup and restore are required.
- Review decisions bind to exact evidence/manifest/policy/profile versions and an
  optimistic concurrency token. OS identity is always recorded. Metadata approval
  creates a registry revision; it never rewrites executed sheets.
- Reviewed exports are manifest catalogs, not copied data or model training arrays.
  Record all candidates, exclusions, exceptions and denominators. Ordinary exports
  are ungated. The status page stays read-only and loopback-only.

## Existing entry points and baseline evidence

`pixi run genesis` dispatches through `execution.controller`; `pipeline` invokes the
DAP shell wrapper; `pipeline-atac` invokes `atac.run`. `genesis-tools` exposes typed
task helpers. Schematics and benchmarking already have independent delegated code.
There is no existing production dataset registry or AI/provider implementation.
Archived schemas under validation/design are historical prototypes, not production
contracts or evidence that legacy runs meet the new contracts.

The fast suite is `pixi run checks` (shellcheck, ruff, ty and script-based checks).
Real-tool synthetic regressions are `pixi run validate-docker --keep` and
`pixi run validate-atac --keep`. Live SSH/scheduler tests are separate opt-in work.

Planning baseline on system Python 3.12.3: verify_reference_cache.py,
verify_multiqc.py, verify_build_tags.py and verify_metro.py passed. `pixi run checks`
exited 127 because Pixi was absent. uv and Python 3.14 were also absent from PATH.
These four checks do not establish Python 3.14, real-tool or remote acceptance.
Implementation validation records commands, versions, limitations and exact outcomes
in the accompanying validation report; unrun checks are never reported as passing.

## Delivered milestone

The final implementation and evidence are described in the
[curation guide](../usage/curation.md) and
[validation report](../../validation/reports/curation-foundations-validation.md).
The pinned full suite passed after recovering exact cached Nextflow plugins.
Installed-wheel acceptance, real BAM/bigWig validation and a 10,000-library,
100,000-location synthetic catalog were exercised. That report describes the foundations milestone only. The extension adds a
standard-library provider, separately deployed digest-pinned vLLM containers,
field-evidence curation, bounded read-only assistance and deterministic diagnosis.
Its separate validation report records offline acceptance and unrun live checks.


## Extension contracts and operational boundaries

- Preserve version 1 bytes/hashes and review behavior. Version 2 adds rich invocation,
  source bundle, proposal, metadata revision, model inspection, deployment and diagnosis
  envelopes. Registry schema 3 adds projections and indexes via transactional migration.
- Rich proposal approval and application are separate. Source/manifest/canonical
  changes invalidate decisions; reviewers use authenticated local OS identity.
- One provider adapter supports disabled, mock and explicitly configured live modes.
  Endpoints/models/capabilities are probed, output validated locally, budgets enforced,
  egress classified and secrets redacted. Model aliases/unknown costs stay explicit.
- Model service ownership is independent of processing jobs. Reuse local/SSH transport,
  exact reviewed plans, node-local reservations and detached supervision. No shared
  worker database or filesystem is assumed. UNKNOWN retains reservations.
- Deployment applies only after explicit exact-plan authorization and fresh resource,
  revision, license and runtime checks. No model/GPU/service is selected automatically.
  Containers/serving clients stay outside core Python; use loopback and owned SSH tunnels.
- Metadata extraction precedes optional model proposals. Source snapshots and exact
  field locators remain authoritative evidence; JSON correctness is not biological truth.
  Control/reference proposals never alter executed or compiled scientific choices.
- Diagnosis only proposes typed next steps. It does not run retries, shell, SQL, repair,
  policy changes or approval. Existing worker retry/reconciliation semantics remain.
- The README contains complete workflows, with a runnable offline tutorial. Synthetic
  evaluation, fake HTTP and lifecycle simulations remain distinct from live acceptance.

## Prepared-study milestone

The next development milestone connects prepared sheets/references to the delivered
curation and execution components. It does not add accession-first acquisition or a
second scheduler. The public interface is `genesis study init|plan|run|resume|status|
collect|export`, documented in the [study guide](../usage/studies.md).

- Schema 3 records describe input manifests, study revisions, immutable plans and
  collection receipts. Registry schema 4 stores input heads, separate input decisions
  and collection lineage. Registration is not a scientific result or QC observation.
- Metadata/review use explicit input/result scopes. Changed source evidence invalidates
  review tokens. Applying an input proposal updates descriptive metadata; only an
  explicit plan compiles executable documents, preserving all scientific choices.
- ATAC jobs contain one library with all technical lanes. DAP jobs contain shared-control
  groups, with separate library identities. Exact worker assignments, paths, profiles
  and Git revisions are configuration. SSH inputs need explicit path mappings.
- The existing controller and detached local/SSH supervisors own execution. A study
  coordinator blocks stale queued launches while continuing to observe existing work.
  No LLM/provider participates in job submission or deterministic collection.
- Owned collection supervisors scan worker-local outputs with bounded budgets and
  transfer checksummed receipts. Import, diagnostic QC and receipt lineage commit in
  one registry transaction. Collection retries/readers do not resubmit analysis.
- Matching input metadata approval can carry forward with its original evidence.
  QC/eligibility still require current result decisions. Late or superseded receipts
  remain history; source classifications cannot be downgraded across review scopes.
- Legacy scientific outputs and parameters remain unchanged. DAP provenance remains
  incomplete where existing reports lack evidence; default reviewed export excludes it.
  Local synthetic lifecycle tests, actual binary readers, full regressions and wheel
  acceptance are distinct from unrun live SSH or new scientific-container acceptance.
