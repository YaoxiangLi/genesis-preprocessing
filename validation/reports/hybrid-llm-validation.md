# Hybrid LLM and curation extension validation

Date: 2026-10-09. Implementation tested:
`accaf04f64833bd4fbb16bfd4bdb2ef083d0eb8c` on `main`, including the foundations
milestone `117e5dc`. Public baseline:
`bb16baca5d9bb09bfff8825fc537fcb125809c07`.
Subsequent validation/report commits change documentation and evidence only.

**PASS:** full project regressions, fake HTTP and deployment lifecycle tests,
binary artifact validation, an installed-wheel offline workflow, synthetic metadata
evaluation, and documented command parsing. **NOT RUN:** live paid/private APIs,
model downloads, local/remote GPU serving, real SSH acceptance, and production
sequencing. No result below establishes real biological annotation accuracy or
production model/runtime compatibility.

## Implementation scope

The extension is integrated into the existing `pixi run genesis` dispatcher.
It does not install a second scheduler or make preprocessing depend on AI/review.

| Plan stage | Implemented behavior |
| --- | --- |
| 0: audit and boundary | Shared implementation brief, compatibility boundary, baseline evidence and checkpoints |
| 1: contracts | Shipped versioned schemas, adapters, bounded artifact/reference validation, separate completeness and execution status |
| 2: registry | Controller-local SQLite, immutable provenance, worker-qualified locations, search, migration, export, backup/restore |
| 3: QC/review | Versioned declarative assessments, explicit missing values, stale-review rejection, metadata/QC/eligibility decisions, read-only summaries, reviewed export |
| 4: providers | Disabled/manual, deterministic mock and configured live compatible HTTP providers; egress rules, redaction, budgets, retries, cancellation, capability probes, invocation history and read-only assistant |
| 5: model services | HF metadata inspection, revision-pinned plans, local/SSH transport, isolated vLLM container backend, resource reservations, lifecycle reconciliation, private tunnels and ownership-checked stop |
| 6: metadata | Bounded local/public source ingestion, deterministic extraction, evidence-checked optional proposals, vocabulary validation, separate approval/apply, immutable metadata revisions |
| 7: diagnosis | Bounded redacted evidence, deterministic classification, optional cited explanation, typed proposed actions; no automatic repair or uncertain-job retry |
| 8: integration | Offline example, synthetic evaluation, fake HTTP/lifecycle tests, separate opt-in live runners, full README recipes and detailed usage guides |

Schemas 1 and 2 remain readable where supported; the registry migrates to schema 3
without rewriting historical decisions. Metadata proposal approval and application
are separate for the new proposal format. The compiled input description preserves
original scientific parameters and requires an explicit new campaign; it is not an
automatically executable replacement sample sheet.

## Exact source, environment and artifacts

[Source and environment](../evidence/hybrid-llm/source-and-environment.json) records
129 implementation/test/resource hashes, Python/package versions and the checked
scientific paths. Comparison against the public baseline found no changes to
`main.nf`, workflows, modules, scientific configuration, ATAC helpers, sample and
metadata processing, reference-cache logic or MultiQC reporting. Existing worker
retry/reconciliation behavior is covered by the full regression suite; the shared
transport extraction preserves its local/SSH request interface.

Core environment: Linux x86_64, Python 3.14.5, SQLite 3.53.1, pysam 0.24.1,
jsonschema 4.26.0, Ruff 0.16.10 and ty 0.0.84. Tooling: Pixi 0.81.0,
uv 0.11.33, Nextflow 25.10.4 build 11173 and ShellCheck 0.11.0.
The optional real bigWig reader used Python 3.12.3, pyBigWig 0.3.26 and NumPy 2.5.3;
see the unchanged [reader environment](../evidence/curation/bigwig-environment.json).

Nextflow tests used the exact pinned plugin cache prepared during foundation
validation, with `NXF_OFFLINE=true`. Archive SHA256 values:

- `nf-schema@2.4.2`: `02c2fc38cefd5a38238a208ec6ae52927a3f509f07c97f0e266841924cbbfd9d`.
- `nf-dotenv@1.0.0`: `bb75972f8557f547b3e1472004e6d71a586b1614431437d3ec64590f550735d4`.

The final wheel is `genesis_tools-0.1.0-py3-none-any.whl`, SHA256
`7b323b2040cdd96fadc39696c399dce0308b7e1be9f7de0a5ed0a2f9e1c00b8d`.
All 95 package files matched the tested checkout. Installed schemas, prompts,
vocabularies and policies loaded outside the repository. Torch, vLLM, HF Hub and
vendor API SDKs were absent from the installed core environment.
[Wheel evidence](../evidence/hybrid-llm/wheel-acceptance.json),
[build/install log](../evidence/hybrid-llm/wheel-build.log) and
[locked runtime requirements](../evidence/hybrid-llm/locked-runtime-requirements.txt)
identify the artifact and installation. No real serving image, model revision or
GPU digest is claimed: deployment tests use explicitly synthetic fixtures.

## Commands and observed results

Run from the repository unless a different working directory is shown. The
[command record](../evidence/hybrid-llm/commands.json) distinguishes observed
checks from reproduction instructions. The final full-suite receipt records the
actual command, revision, exit status, start time and elapsed time.

| Check | Result | Evidence |
| --- | --- | --- |
| `PATH="/tmp/genesis-tooling/bin:$PATH" NXF_PLUGINS_DIR=/tmp/genesis-nextflow-plugins-v1 NXF_OFFLINE=true pixi run checks` | PASS, exit 0, 136.781 s | [Receipt](../evidence/hybrid-llm/checks-receipt.json), [log](../evidence/hybrid-llm/checks.log) |
| `genesis_tools/.venv/bin/python tests/verify_curation_artifacts.py --bigwig-python /tmp/genesis-bigwig-env/bin/python` | PASS | [Binary validation](../evidence/hybrid-llm/binary-checks.log) |
| Installed wheel, from `/tmp`, with `PYTHONPATH` unset: run `examples/curation/offline_workflow.py /tmp/genesis-installed-demo-final` | PASS | [Workflow log](../evidence/hybrid-llm/installed-demo.log), [result](../evidence/hybrid-llm/offline-acceptance.json) |
| Same installed interpreter and working directory: run `tests/verify_ai.py` and `tests/verify_llm_deployment.py` | PASS | [Installed AI/lifecycle log](../evidence/hybrid-llm/installed-ai.log) |
| `genesis_tools/.venv/bin/python tests/evaluate_metadata.py --output /tmp/genesis-hybrid-metadata-evaluation-final.json` | PASS, synthetic software evaluation | [Measurements](../evidence/hybrid-llm/metadata-evaluation.json) |
| `genesis_tools/.venv/bin/python tests/benchmark_curation.py --libraries 1000 --batch-size 100 --output /tmp/genesis-hybrid-catalog-scale-v2.json` | PASS, bounded local catalog measurement | [Measurements](../evidence/hybrid-llm/catalog-scale.json) |
| `genesis_tools/.venv/bin/python tests/verify_readme.py` | PASS, 130 documented command invocations parse and local documentation links resolve | Full suite log; final documentation check |
| `git diff --check` | PASS | Final publication checks |

The full suite runs shellcheck, lint/format and strict type checks, existing DAP
Nextflow stub/resume/reference-failure checks, ATAC known-answer fixtures,
reference-cache/MultiQC/benchmark/schematics tests, local worker recovery, all
curation scripts, fake HTTP providers, mocked service lifecycle, synthetic metadata
evaluation and documentation parsing. Its default binary test prints NOT RUN for
bigWig; the separate command above supplies actual binary-format coverage.

The installed example imports two synthetic DAP/ATAC artifact bundles, validates
them, evaluates diagnostic policy, makes mock proposals, records six explicit
demonstration decisions, applies metadata, exports both eligible datasets,
diagnoses a synthetic log, and checks backup/restore. Export accounting is two
candidates, two included and zero excluded. This example does not execute a
sequencing pipeline. [Fixture hashes](../evidence/hybrid-llm/fixture-sha256.json)
bind the observed inputs and outputs; timestamps/decision identities make newly
generated records differ between runs.

## Behavioral acceptance

| Area | Exercised cases |
| --- | --- |
| Provider and egress | Valid responses; unsupported schemas; 429/5xx; timeout; bounded repair; refusal/truncation; malformed/wrong-model output; context/concurrency budgets; cancellation; no implicit fallback; local-only egress rejection; secret redaction; cache identities; tool/stream probes; reasoning-field removal |
| Source and metadata | JSON/CSV/GEO-format extraction; exact source version, pointer/line and quote; fabricated evidence and ontology rejection; conflicting tissue, missing treatment, ambiguous protocols, interspecies DAP and technical lanes; classification retention; optimistic/stale review; separate approval/apply; immutable exports |
| Registry and QC | Repeated and concurrent import, interrupted rollback, worker path identity, pruned/moved artifacts, absent versus zero, incompatible policy, stale eligibility, schema 1/2-to-3 migration, populated history and backup/restore |
| Model planning | Immutable revision, license/gating, architecture/context/quantization, resource and allocation limits, insufficient disk/VRAM, exact plan authorization, local/SSH command construction |
| Service lifecycle | Partial/corrupt snapshots, ownership labels, duplicate launch and resource collision, start/probe failure, wrong model, stale heartbeat, restart/reconciliation, tunnel loss, safe stop; all runtime/GPU responses mocked |
| Diagnosis | Temporary/access/input/checksum failures, ambiguous exit 137 versus evidence-confirmed OOM, biological QC concern, running/unreachable worker, malicious/secret-bearing logs, stale target and provider outage; no execution of proposed actions |
| Compatibility | Known-answer BAM/ATAC metrics and cut coordinates, existing execution tests, escaped read-only reports, installed resources and optional-dependency absence |

The synthetic gold set has two development and seven held-out cases. In the
separate recorded evaluation, both deterministic and mock paths matched 12 of
12 specified fields, validated evidence in seven of seven cases, detected one
conflict and made four abstentions. Elapsed time was 0.0314 s and 0.2157 s
respectively. Human correction rate and reported tokens are unknown (`null`).
These small constructed examples test software contracts, not real curation
accuracy; no real-provider ranking or calibration is inferred.

## Bounded registry measurement

One local current-schema run, 100 libraries per transaction batch, ten declared
unavailable artifact locations per library. No sequencing bytes were scanned.

| Observation | Value |
| --- | ---: |
| Libraries / artifact locations | 1,000 / 10,000 |
| Stored immutable records | 1,011 |
| Time inside imports | 6.607 s |
| Total generation/import/query time | 10.568 s |
| Text query returning 100 rows | 0.001960 s |
| Database/WAL bytes at observation | 16,379,904 |
| Process-image peak RSS, Linux `VmHWM` | 46,092 KiB |

The tool launcher passed an inherited `ru_maxrss` high-water value of 2,719,096 KiB
into the process; it was already present at startup and did not change. It is
recorded for transparency, not attributed to Genesis. `/proc/self/status` `VmHWM`
measures this Python process image, not whole-host RAM. Concurrent host activity,
filesystem cache and this one selected query limit comparisons. The earlier
foundation report has a separate 10,000-library run; neither run promises a
production scale/throughput guarantee. Controller network bytes, host-wide RAM,
live model latency/tokens/cost and curator corrections were not measured.

## Limitations and tests not run

| Status | Scope and reason |
| --- | --- |
| NOT RUN | Real external/private API acceptance: no real credentials, egress or spending selected for this validation |
| NOT RUN | Real HF snapshot download or vLLM image execution: no model/license/revision/image/hardware deployment was selected |
| NOT RUN | Local GPU, remote SSH/GPU, scheduler allocation, tunnel and restart acceptance against live hosts: tests simulate these boundaries; opt-in runners are supplied |
| NOT RUN | Full DAP/ATAC scientific-container execution: unchanged computation sources, existing known-answer fixtures and Nextflow stubs were checked; this report is not an independent real pipeline rerun |
| NOT EVALUATED | Biological annotation quality, expert agreement, model confidence calibration and effectiveness of repair proposals on real failures |

The first live adapter targets compatible Chat Completions endpoints; native
vendor-specific APIs are not implemented. Provider capabilities are probed per
endpoint/model and local schemas still validate every output. Initial serving
supports one isolated Docker/vLLM backend and GPUs within a node. Cross-host
sharding, MIG scheduling, public gateways, model fine-tuning and new infrastructure
provisioning are outside this implementation. Runtime/model compatibility needs a
real acceptance run for the chosen digest and revision.

Source ingestion supports bounded local formats and fixed public accession APIs,
not arbitrary paper scraping or executable supplements. The shipped vocabulary
is deliberately small; unsupported terms retain raw values or enter review.
Scientific reference/control proposals do not change executed inputs. Review
identity is the OS account; shared accounts limit accountability. Hashes establish
consistency, not protection from a malicious database administrator.

Pixi emits the pre-existing `[system-requirements]` deprecation warning. No new
lint/type warning remains. Core runtime checks are offline; installing dependencies
on a fresh machine may require package downloads. No production jobs, services,
SSH credentials, firewall rules, cloud resources or scientific thresholds were
changed during validation.

## Reproduce, operate and roll back

Start with the [README](../../README.md), then follow the detailed
[curation](../../docs/usage/curation.md),
[provider](../../docs/usage/ai-providers.md), and
[deployment](../../docs/usage/llm-deployment.md) instructions. The README includes
disabled/mock/live modes, all CLI families and separate opt-in live acceptance
commands. Its deployment example intentionally requires site-specific choices.

Back up a registry with `genesis registry backup` before migration and retain its
original database plus migration backup. Restore into a separate location with
the matching application version; inspect history before replacing any active
registry. Downgrading source does not downgrade a database. Stop an owned service
through `genesis ai deployment stop` before removing its controller state;
checking out older code alone does not stop containers or tunnels. Caches and
logs are retained by normal stop. A code rollback should use a reviewed revert
or separate checkout, preserving campaign payloads and scientific files.

For real deployment the team must select the model/revision/license, a tested
image digest, authorized nodes/GPU/resource budgets and any scheduler allocation.
For external inference it must select endpoint/model, secret references, allowed
data classifications/tasks and budgets. Biological exclusion thresholds and
reviewed real gold cases still require scientific approval; the software does
not invent those choices.
