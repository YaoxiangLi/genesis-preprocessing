# Curation foundations specification

Baseline: `bb16baca5d9bb09bfff8825fc537fcb125809c07`, clean `main` at audit.
This specification implements the agreed Prompts 0–3 in the existing repository.
No provider, serving, automatic metadata extraction, or diagnostic agent is in this milestone.

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

All core curation works offline, without models, credentials or GPUs. Future LLMs
may propose evidence-backed changes; deterministic validation and accountable human
review remain authoritative. No hidden chain-of-thought is collected. Logs, metadata
and proposed changes are untrusted data. No production runs, model downloads, public
services, credentials, sudo, firewall changes, commits or pushes are authorized here.

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
100,000-location synthetic catalog were exercised. New provider, AI curation,
model-serving and diagnostic-agent work remains outside this milestone.
