# Curation foundations validation

Date: 2026-10-09. Scope: the agreed Prompts **0–3** (audit, contracts,
scientific registry, QC and manual review). Source baseline:
`bb16baca5d9bb09bfff8825fc537fcb125809c07`, branch `main`.
Implementation changes were uncommitted when this evidence was captured; the
foundation milestone was subsequently committed as `117e5dc`. No release was
claimed by the original validation run.
The exact implementation/test/resource hashes, dependency versions and final wheel
digest are in [environment-and-source.json](../evidence/curation/environment-and-source.json).

## Outcome

**PASS:** the final full project check suite, additional real binary-format checks,
installed-wheel offline curation acceptance, and the bounded catalog benchmark.
These results do not establish production sequencing throughput, biological
acceptance thresholds, live remote execution or any LLM behavior.

Existing scientific sources were checked against the baseline: `main.nf`, workflows,
modules, configuration, ATAC helpers, samples, metadata, reference-cache logic and
MultiQC reporting have no changes. The controller changes delegate new commands
and add opt-in read-only summaries/downloads. Existing retry/reconciliation logic
is unchanged. Core installation adds `jsonschema`; no serving/GPU dependencies
or scientific environment changes were introduced.

## Commands and evidence

Commands below ran from the checkout unless another directory is stated. Temporary
tooling was on PATH; no sudo, worker credentials, firewall or scheduler changes were
made. [commands.json](../evidence/curation/commands.json) records the command strings
and exit statuses. Only observed measurements are reported; unmeasured elapsed
times, network bytes, host-wide RAM and costs remain unknown.

| Check | Result | Evidence |
| --- | --- | --- |
| `PATH="/tmp/genesis-tooling/bin:$PATH" NXF_PLUGINS_DIR=/tmp/genesis-nextflow-plugins-v1 NXF_OFFLINE=true pixi run checks` | PASS, exit 0 | [Full suite log](../evidence/curation/checks.log) |
| `uv run --frozen --project genesis_tools python tests/verify_curation_artifacts.py --bigwig-python /tmp/genesis-bigwig-env/bin/python` | PASS, exit 0 | [Binary check log](../evidence/curation/binary-checks.log) |
| `uv run --frozen --project genesis_tools python tests/benchmark_curation.py --libraries 10000 --batch-size 100 --output /tmp/genesis-catalog-scale.json` | PASS, exit 0 | [Measurements](../evidence/curation/catalog-scale.json) |
| Build final wheel; install it in `/tmp/genesis-curation-installed` with locked runtime dependencies | PASS, exit 0 | [Source/wheel digest](../evidence/curation/environment-and-source.json) |
| From `/tmp`: `/tmp/genesis-curation-installed/bin/python -I /data/homes/yl814/package/genesis/genesis-preprocessing/tests/verify_curation.py` | PASS, exit 0 | [Installed acceptance log](../evidence/curation/installed-acceptance.log) |
| From `/tmp`: installed import/resource/CLI probe, matching installed files to the implementation hashes | PASS | [Installed-wheel evidence](../evidence/curation/installed-wheel.json) |
| `git diff --check` | PASS | Final local diff inspection |

The full suite includes shellcheck, Ruff lint/format, strict source/test type checks,
Nextflow style and BAM quantification, mocked image-build checks, MultiQC,
reference-cache tests, DAP stub execution/resume/reference failures, benchmark
contracts and metric fixtures, ATAC fixtures, local worker supervision/retry
tests, deployment-profile parsing, schematics and all three curation scripts.
Its default bigWig test explicitly says NOT RUN; the separate real binary command
above supplies that coverage. The dedicated reader is not silently assumed present.

The final wheel contains the JSON Schemas and default diagnostic/export policies.
The installed acceptance ran the registry/review/export workflow outside the
repository. The probe confirmed that imported code came from the installed wheel,
its implementation/resource hashes matched the source manifest, and both `torch`
and `pyBigWig` were absent from that core environment.

## Acceptance coverage

All data in the new tests are explicitly synthetic. Common raw fixture digests are
recorded in [fixture-sha256.json](../evidence/curation/fixture-sha256.json); generator
and test source hashes are included in the implementation evidence.

| Area | Exercised behavior |
| --- | --- |
| Contracts and validation | Unknown versions/types/fields, duplicate keys, stale nested hashes, NaN, reference mismatch, reference mutation during scanning, bad intervals, valid zero peaks, scan-budget exhaustion, wrong signal units, optional pruned BAMs, changed artifact checksums |
| Binary formats | Real BAM header/reference/index checks; narrowPeak finite values/bounds; large unwrapped FASTA; real corrupt/readable bigWigs, nonfinite and fractional raw-count signals |
| Adapters | ATAC lanes/metric units and denominators; changed provenance-manifest digest; DAP shared controls remaining separate from TF libraries; SE/PE output roles; unavailable historical provenance |
| Registry | Repeated imports, source namespaces, worker-qualified equal paths, pruned locations, injected interrupted-import rollback, simultaneous import writers, concurrent WAL reader, FTS and literal fallback, schema 1-to-2 migration/backup, backup/restore, catalog round trips |
| QC/review/export | Zero versus missing, incompatible species policy, execution success with unevaluated QC, stale/concurrent review token rejection, immutable records, metadata revision, reassessment, current metadata/proposals in export, stale eligibility exclusion, evidence-locator rejection, explicit exception and candidate accounting |
| Integration | Delegated CLI help/JSON/error exit, campaign observation without job execution, escaped HTML, approved local report download restrictions, installed-package operation without AI or binary bigWig dependencies |

Review identity is captured from the executing OS account. These tests exercise
software consistency, not real curator agreement or biological correctness.
Known-answer DAP/BAM and ATAC fragment/cut-site fixtures retained their expected
scientific answers; DAP full-pipeline evidence here is stub execution, not a real
alignment/peak-calling rerun.

## Environment and baseline recovery

Core: Linux x86_64, Python 3.14.5, SQLite 3.53.1, jsonschema 4.26.0,
pysam 0.24.1, Ruff 0.16.10 and ty 0.0.84. Tooling: Pixi 0.81.0, uv 0.11.33,
Nextflow 25.10.4 build 11173 and ShellCheck 0.11.0. Python package dependencies were
resolved from the checked-in `genesis_tools/uv.lock`.

The first pinned baseline `pixi run checks` passed the initial lint/type/helper
checks but stopped when Nextflow could not resolve `nf-schema@2.4.2` through its
registry lookup. This was not recorded as a baseline suite pass. Exact pinned
plugin archives were then fetched from the official Nextflow registry and
unpacked into `/tmp/genesis-nextflow-plugins-v1`:

- `nf-schema@2.4.2`: SHA256
  `02c2fc38cefd5a38238a208ec6ae52927a3f509f07c97f0e266841924cbbfd9d`.
- `nf-dotenv@1.0.0`: SHA256
  `bb75972f8557f547b3e1472004e6d71a586b1614431437d3ec64590f550735d4`.

An independent retry of `tests/verify_pipeline.py` passed with those exact cached
plugins, followed by the complete final suite. The plugin directory and offline
mode are documented by [Nextflow](https://docs.seqera.io/nextflow/plugins/using-plugins).
No plugin version or scientific expectation was relaxed. Pixi reports an existing
`[system-requirements]` deprecation warning; no new lint/type warning remains.

The separate binary-reader check used Python 3.12.3, pyBigWig 0.3.26 and NumPy 2.5.3.
[Reader environment evidence](../evidence/curation/bigwig-environment.json) distinguishes
this local check from acceptance of the whole pinned scientific track container.
The tests caught and corrected interpreter-path resolution through a virtualenv
symlink; retaining its interpreter path preserves the environment's dependencies.

An initial offline wheel dependency installation failed because `defopt` index
metadata was not in that cache. Exporting the exact locked runtime requirements
and installing from PyPI succeeded. The installed acceptance itself requires no
network, external service, credentials or GPU. This is runtime-offline evidence,
not a claim that a fresh installation needs no package downloads.

## Bounded catalog measurements

One local synthetic run, 100 records per transaction batch. Each library has ten
declared unavailable artifact locations; sequencing bytes are not created or read.
This measures catalog storage/import and one FTS query, not end-to-end CLI review
rendering or scientific processing. Other verification processes ran on the host.

| Observation | Measured value |
| --- | ---: |
| Libraries | 10,000 |
| Artifact locations | 100,000 |
| Stored immutable records | 10,101 |
| Time inside imports | 93.148 s |
| Total generator/import/query time | 137.752 s |
| Text query, 100 results | 0.012581 s |
| Process peak RSS | 47,724 KiB (Linux `ru_maxrss`) |
| Database and WAL bytes at observation | 161,124,352 |

FTS5 was available. These measurements establish one tested catalog size on this
environment, not a production scale guarantee or whole-host memory estimate.

## Not run and practical limits

| Scenario | Status / reason |
| --- | --- |
| `pixi run validate-docker --keep` full real-tool DAP pipeline | NOT RUN: Genesis scientific images were not installed; large image/tool acquisition was outside this milestone's local acceptance |
| `pixi run validate-atac --keep` full real-tool ATAC pipeline | NOT RUN: same image/runtime acceptance limitation; actual local known-answer fragment tests did run |
| Live SSH, site scheduler and remote artifact transport | NOT RUN: no authorized live worker/site acceptance was exercised; local worker simulation and command/profile checks ran |
| GPUs, external APIs, model download/serving, AI diagnosis or harmonization | NOT RUN / outside Prompts 0–3; no inference or deployment is implemented here |
| Real biological cohort thresholds or curation accuracy | NOT RUN: synthetic fixtures do not establish biological acceptance or measured curator accuracy |

Legacy DAP provenance can remain incomplete and be excluded by the default reviewed
profile. Full validation covers the manifest's declared artifact scope; an authored
generic manifest does not prove assay-wide completeness. Files can change after an
observation: consumers must revalidate worker-local bytes before use. Hashes provide
content identity, not authentication against a malicious database administrator.
Shared OS accounts do not uniquely identify individual reviewers.

The optional status page scans a bounded first page of 1,000 catalog records and
serves only current approved controller-local report attachments. Use paginated
CLI search for complete catalogs. SQLite requires local serialized ownership;
the implementation does not provide multi-controller or NFS writer coordination.
No automatic export arrays or bulk sequencing-file copies are produced.

## Rollback and remaining decisions

Pipeline execution is independent of curation; stop invoking curation commands or
omit `serve --registry` to disable it. Use `registry backup`, then restore into a
new local directory; migrations create pre-migration backups. Preserve campaign
state and artifacts. Full instructions are in the [curation guide](../../docs/usage/curation.md).

Project decisions before biological use are the intended export profile and its
required artifact roles; scientifically approved metric policies and exceptions;
stable study/worker namespaces; and accountable reviewer OS identities. Providers
and model deployment can build on these contracts in later milestones. Nothing
was committed, pushed, deployed or executed against production datasets.
