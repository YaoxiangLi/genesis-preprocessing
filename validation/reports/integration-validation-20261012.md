# Integration validation — October 2026

> Validation record for the revision and date below. Use the
> [current task guides](../../docs/README.md) for a new analysis. Recorded temporary
> paths identify the original test environment.

Acceptance date: 2026-10-12 (America/New_York; command receipts use UTC).

The tests cover DAP, bulk ATAC and scATAC processing, prepared studies,
validation, registry/review, optional AI providers and model-service contracts.
They use synthetic fixtures and the software identities recorded below.

## Revisions and preserved behavior

- Tested source: `392ada4d38fe5f6d2a67d04c00998319d461ce84`.
- Scientific comparison baseline: `fb600968b3abf5d79756aaf7e6d1e4ff43a1b41d`.

The original four public sample sheets, DAP alignment/QC/track/peak/quantification
modules, parameter schema, quantification implementation and vendored SPP script
are byte-identical to the comparison baseline. [File hashes](../evidence/integration-20261012/preserved-science.json)
record all 16 comparisons. Reference modules add provenance enforcement; FastQC
and MultiQC are new reporting branches. Neither curation nor AI changes scientific
parameters or requires approval for ordinary preprocessing.

The [archived DAP README](../../docs/history/dapseq-readme-fb60096.md) preserves its
full original text, including the reported 2026-10-06 ARM64 results. Two relative
links are pinned to that original commit. A checksum regression reverses only
those link rewrites and verifies the original README SHA256
`3ce68770e50460992a2768f58b2c6ed9a69985f80b3ea4dcbcf4f02ae9f830ff`.
The archive's original validation claim was not independently rerun here.

The [current DAP guide](../../docs/usage/dapseq-reference.md) retains all six old
sections and documents changed defaults/cache requirements. All six original
README fragment bookmarks resolve to the detailed instructions.

## Acceptance

All commands used a clean checkout of the tested revision on Linux x86_64, with
Python 3.14.5 and the committed dependency locks. The existing verified Nextflow
plugin cache was selected with `NXF_PLUGINS_DIR=/tmp/genesis-nextflow-plugins-v1`
and `NXF_OFFLINE=true`; `UV_LINK_MODE=copy` avoided cross-filesystem hardlink
fallback. `/tmp/genesis-tooling/bin` supplied Pixi and uv. [Environment](../evidence/integration-20261012/environment.json)
and [pinned image identities](../evidence/integration-20261012/images.json) record
actual versions and digests. Images were pulled by their committed digests; no
images were built or published.

This host uses Snap Docker: its daemon cannot see host `/tmp` or `/data/homes`
bind mounts. Tests ran from a worktree under daemon-visible `/var/tmp`; no daemon,
firewall or permission changes were made. Use a runtime-visible checkout and work
root on another host. Package caches were already populated; this is not an
uncached-installation benchmark.

| Check | Result | Evidence and scope |
| --- | --- | --- |
| `pixi run checks` | PASS, 156.296 s | [Receipt](../evidence/integration-20261012/full-checks.json), [log](../evidence/integration-20261012/full-checks.log): lint, format, types, Nextflow stubs, reference/cache failures, workers, study orchestration, registry/review, mock/fake HTTP AI, model lifecycle, metadata and scATAC regressions. |
| Documentation | PASS | 197 current CLI commands parse, 239 Pixi recipes resolve, local links/anchors in 13 documents resolve. Original DAP text and six README bookmarks are protected. Historical commands are excluded from current-command parsing. [GitHub rendering](../evidence/integration-20261012/readme-render.json) also checked the bookmarks, guide links and architecture image present at that revision; no new browser screenshot was taken. |
| DAP Docker | PASS, 345.516 s | [Receipt](../evidence/integration-20261012/dap-docker.json), [log](../evidence/integration-20261012/dap-docker.log), [trace/fixture summary](../evidence/integration-20261012/dap-fixture-summary.json). 42 initial completed tasks; first resume 28 completed/10 cached; stable resume 37 cached plus one completed reference validation. Three treatments each produced 200 peaks. Full/read1/SPP BAM policies, raw bytes, publication boundaries, four reference failures, corrupt/empty reads, FastQC advisory/parser cases and MultiQC identities/determinism were checked. |
| Bulk ATAC Docker | PASS, 83.702 s | [Receipt](../evidence/integration-20261012/bulk-atac.json), [log](../evidence/integration-20261012/bulk-atac.log), [trace summary](../evidence/integration-20261012/atac-fixture-summary.json). Two synthetic libraries, two lanes each; 21 initial completed tasks; all 21 cached on each unchanged resume. An isolated helper change reran 20 affected tasks with one cached; a subsequent resume cached all 21. Raw/scientific bytes remained unchanged; explicit adapter trimming was checked. |
| scATAC real products | PASS, 5.112 s | [Receipt](../evidence/integration-20261012/scatac-products.json), [log](../evidence/integration-20261012/scatac-products.log). 900 distinct fragments, 2,700 support, 1,800 cuts, three peaks and FRiP 1.0; resume and independent byte-identical products. Model loaders were not rerun in this test series; their earlier acceptance remains dated in the [scATAC report](scatac-delivery-validation.md). |
| Full binary artifact validation | PASS, 1.988 s | [Receipt](../evidence/integration-20261012/artifact-binary.json), [log](../evidence/integration-20261012/artifact-binary.log). The optional bigWig cases omitted by the default suite ran separately using an existing pyBigWig 0.3.26 environment. |
| Prepared study with binary reader | PASS, 24.138 s | [Receipt](../evidence/integration-20261012/study-binary.json), [log](../evidence/integration-20261012/study-binary.log). Synthetic output writers with real local workers and binary validation; not real sequencing through the study coordinator. |
| Installed wheel outside checkout | PASS, 11.537 s | [Receipt](../evidence/integration-20261012/installed-wheel.json), [commands/resources](../evidence/integration-20261012/installed-wheel-details.json), [log](../evidence/integration-20261012/installed-wheel.log). New environment, frozen dependencies from cache with `UV_OFFLINE=true`, no `PYTHONPATH`; CLI entry points and packaged schemas/templates/assets, full offline tutorial, two included datasets and six fixture-only decisions. |

The existing Pixi `system-requirements` deprecation warning remains visible in
logs. Expected negative-case diagnostics and advisory FastQC labels are preserved;
passing these tests does not mean all quality labels pass. Timings are observed
wall-clock durations on this host, with some independent checks running concurrently.
No throughput or biological accuracy guarantee is inferred from them.

## Reproduce the tests

Follow the [contributor guide](../../docs/development.md) for clone/install and
verified plugin-cache recovery. On a Docker-visible checkout:

```bash
pixi run checks
pixi run validate-docker --keep
pixi run validate-atac --keep
pixi run uv run --frozen --project genesis_tools python tests/validate_scatac_products.py \
  --output /var/tmp/genesis-scatac-acceptance
# Optional separate, existing pyBigWig environment:
pixi run uv run --frozen --project genesis_tools python tests/verify_curation_artifacts.py \
  --bigwig-python /path/to/bigwig-environment/bin/python
pixi run uv run --frozen --project genesis_tools python tests/verify_study.py \
  --bigwig-python /path/to/bigwig-environment/bin/python
```

Choose a new scATAC output path. Recorded temporary paths identify this execution;
they are not dependencies to copy to another server. Only compact logs, traces,
checksums and receipts belong in Git; environments, full work directories,
references, registries, sequencing files and credentials remain outside it.

## Limitations

Live SSH, scheduler, GPU/vLLM and external API acceptance: **NOT RUN**. Full public
biological comparisons and expert-reviewed metadata accuracy: **NOT EVALUATED**
in this test series. Mock and synthetic results do not establish those outcomes.
Private-model deployment and external egress still require their explicit plans,
site authorization and budgets. No production runs, policies or services changed.

## Installation from a fresh checkout

A separate installation test used revision
`aceb6f4dc5f2d693a8d78616a4cf5f4cc7c7c15c`.

A fresh checkout installed into new environments and passed
CLI help/doctor, all 197 current CLI/documentation checks and the complete offline
tutorial. All **521 tracked files** were byte-identical to the source revision;
the clone remained clean. The observed clone/install/check time was **20.400 s**,
using existing package caches on this host. This does not claim acceptance on an
unspecified destination server. [Receipt](../evidence/integration-20261012/fresh-clone.json),
[per-command results](../evidence/integration-20261012/fresh-clone-details.json) and
[log](../evidence/integration-20261012/fresh-clone.log) record the exact scope.
