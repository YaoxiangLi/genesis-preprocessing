# Prepared-study workflow validation

Date: 2026-10-11 UTC / 2026-10-10 America/New_York.
Baseline: `e260f2238e2ad1b1c45333bc5038523bcc2b3761`.
Tested implementation: `98d5525a0aea752dad536d64d8356f1c7d01b90a`.
The accompanying documentation commit extends README command checks to the new guide.

The milestone joins prepared DAP/ATAC inputs, scoped metadata review, deterministic
campaign planning, existing worker execution, asynchronous collection, registry/QC
and reviewed export. It introduces no scientific parameter or pipeline changes,
dependencies, model downloads, production execution or live provider calls.

Implementation checkpoints are `2d5b50a` (input records/review/migration), `934102b`
(compilation/owned staging), and `98d5525` (orchestration/collection/export). Usage is
in the [study guide](../../docs/usage/studies.md) and the README. The
[implementation brief](../../docs/curation/IMPLEMENTATION_BRIEF.md) records ownership
and compatibility decisions.

## Executed checks

| Check | Result | Observed elapsed time |
| --- | --- | --- |
| Full `pixi run checks` | **PASS**: lint/format/types, Nextflow stubs, existing scientific fixtures, execution, contracts/registry/review, providers, deployment simulations, documentation and new study acceptance | 150.562 s |
| `tests/verify_study.py --bigwig-python /tmp/genesis-bigwig-env/bin/python` | **PASS**: real local supervisors and binary readers with synthetic scientific output writers | 22.357 s |
| `tests/verify_curation_artifacts.py --bigwig-python /tmp/genesis-bigwig-env/bin/python` | **PASS**: actual BAM/bigWig, corrupt formats, reference mismatch, bounded scans and worker separation | 1.506 s |
| Build/install wheel and run outside checkout | **PASS**: shipped schemas 1/2/3, seven study subcommand help pages, full study acceptance with binary reader, existing offline tutorial | 36.034 s, including build/install |
| README and usage recipes | **PASS**: 170 documented commands parse; linked local files exist | Included in full suite |
| Architecture overview | **PASS**: 57 native browser labels, no overlap/panel escape/connector crossing; 11 licensed asset hashes; responsive light/dark embedding at 1040/390 px | Not benchmarked |
| Scientific-source comparison against baseline | **PASS**: no changes to `main.nf`, workflows, modules, profiles, ATAC scientific code, samples or reference-cache implementation | Not benchmarked |

Logs and exact command receipts:
[full suite](../evidence/study-workflow/full-checks.json),
[study/binary acceptance](../evidence/study-workflow/study-binary.json),
[artifact validation](../evidence/study-workflow/artifact-binary.json),
[installed wheel](../evidence/study-workflow/installed-wheel.json),
[environment and file hashes](../evidence/study-workflow/environment.json),
[diagram geometry](../evidence/study-workflow/architecture.json).
Each timed receipt links its command to a log digest; adjacent `.log` files contain output.
These small-fixture elapsed times are observations on this host, not throughput or
whole-host resource guarantees. Network bytes, whole-host peak RAM and production
controller overhead were not measured.

The full suite used Python 3.14.5, Pixi 0.81.0, uv 0.11.33, ruff 0.16.10 and ty 0.0.84.
It used the existing verified Nextflow plugin cache with `NXF_OFFLINE=true`; the
[handoff guide](../../docs/development.md#recovery-when-plugin-lookup-fails) records
recovery instructions and exact pinned plugin hashes. Pixi emitted its existing
`system-requirements` deprecation warning. No new code/type/lint warning was introduced.
The separate binary reader was Python 3.12.3 with pyBigWig 0.3.26.

The wheel SHA256 was
`35797fde4833227f5bd46d90d389106736a14f2fd013a747e3c8e1d64ef7ce8e`.
Dependencies were exported from the frozen lock, installed with required hashes in
a new environment, and the wheel installed without resolving extra dependencies.
Acceptance ran from `/tmp/genesis-study-wheel-dba3psu2`, with `PYTHONPATH` removed.
Imports resolved to installed `site-packages`; torch, vLLM and pyBigWig were absent
from that core environment. The optional binary reader remained a separate interpreter.
The existing offline tutorial exported two synthetic datasets with six explicit
demonstration decisions; its pipeline/live-inference status remained `NOT RUN`.

## What the new acceptance establishes

- Input registration is idempotent, source changes create versions and stale review,
  and input-only records report `NOT_RUN`. A real schema-3 database migrates to 4;
  backup/restore retains input decisions. Input queues paginate through mixed catalogs.
- Rich metadata approval/apply is separate. Curated values and explicit nulls survive
  result import. A local-only input source cannot be reclassified as public by choosing
  result-scope assistance. Changed evidence also changes the optimistic review token.
- ATAC compilation preserves both technical lanes and declared MAPQ. DAP shared
  controls produce one analysis group with three separately cataloged libraries.
  Unmapped SSH inputs are blocked; mapped paths compile without network access.
- Two independent local workers use distinct physical input paths. Real detached
  supervisors execute a **test-only output writer**, reconnect after coordinator
  restart and collect/import results. The writer counts invocations to verify that
  revalidation, transfer recovery and collection retries do not repeat analysis.
- Full bigWig validation can be enabled after execution through worker-qualified
  `study collect --reader`. Tiny scan budgets stay incomplete. Zero peaks are accepted
  structurally. Bad receipt identity, traversal and stale scientific inputs are rejected.
- Failed-job isolation leaves healthy libraries running. Collection interruption
  reports `UNKNOWN` and reconnects to the same receipt; uncertain analysis is not
  resubmitted. Interrupted import rolls back records, QC and receipt lineage together.
- A late collection against changed source evidence remains immutable history and
  cannot replace current heads. Matching input approval carries its actual decision
  and sources into a reviewed ATAC export. Unapproved/incomplete candidates are excluded.
- DAP scans retain incomplete scientific provenance rather than inventing it. A
  separately reviewed synthetic catalog profile demonstrates an explicit exception;
  it does not make DAP provenance complete or waive structural errors.
- The read-only status page escapes hostile names and collection errors. No web write
  endpoint, arbitrary filesystem browsing, remote report copying or new scheduler was added.

Fixtures are defined by [the study test](../../tests/verify_study.py) and
[the synthetic writer](../../tests/study_pipeline_fixture.py); their exact source hashes
are recorded. Tiny reads/references, empty peaks and supplied metrics are explicitly
synthetic. Fake fragment-index content does not establish tabix correctness. Real BAM
validation is covered separately by the artifact suite. No metadata accuracy or
scientific output correctness is inferred from the synthetic output writer.

## Limits and remaining acceptance

| Scenario | Status |
| --- | --- |
| New coordinator with real DAP/ATAC scientific containers | **NOT RUN**; existing scientific implementations and fixtures are unchanged |
| Authenticated remote SSH / live scheduler execution and collection | **NOT RUN**; configuration/transport behavior and local workers were tested |
| External API, private live model, GPU service | **NOT RUN**; existing fake HTTP/lifecycle tests passed |
| Real biological metadata accuracy or curator correction rate | **NOT EVALUATED**; synthetic evidence cases only |
| Production data transfer, production QC thresholds, model downloads | **NOT RUN** |

The DAP adapter's current reports do not contain full scientific provenance. Default
reviewed export excludes that incompleteness even after a readable full scan. The
plant diagnostic policy still has unspecified biological thresholds. Explicit human
decisions and a purpose-specific profile remain necessary; no approval is automated.

## Reproduce and roll back

```bash
pixi run install-all
pixi run checks
pixi run uv run --frozen --project genesis_tools python tests/verify_study.py
pixi run uv run --frozen --project genesis_tools python tests/verify_study.py \
  --bigwig-python /path/to/existing/track-environment/bin/python
```

The binary test needs an already available reader. The default test requires no
Docker, scheduler, credentials, GPU or external service. Initial dependency/plugin
installation may need network access. Follow the [development handoff](../../docs/development.md)
for a new server; paths in evidence receipts identify this test host only.

Keep the previous registry's pre-migration backup. To roll back software, stop
orchestration and catalog writers, preserve immutable study/attempt/output directories,
and restore the older-schema backup into a new directory with the matching old software.
Do not overwrite schema-4 databases with old code or delete attempt state to force a
retry. The legacy standalone scientific commands remain available independently.
