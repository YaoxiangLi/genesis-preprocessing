# Direct Genesis CLI and README update

Date: 2026-10-13 UTC. Base revision: `1ce11f66afc21021e6228a1eee90d105fe511132`.
Tests ran against the implementation working tree. The
[source and evidence hashes](../evidence/direct-cli/checksums.json) identify the
tested files; the logs below retain exact commands, paths and results.
Archived text logs have trailing whitespace trimmed; warnings are retained.

## Behavior

`pixi run install-all --install-cli` exposes the existing `genesis` console script
through a user-selected bin directory (default `~/.local/bin`). Installation is
repeatable and rejects conflicting files, directories and symlinks. Shell startup
files are not changed.

The new `genesis pipeline`, `genesis pipeline-atac` and `genesis benchmark` commands
delegate to existing scientific implementations through Pixi. They use the selected
checkout's Python environment, expose its `genesis-tools` helpers to local tasks,
preserve argument boundaries and working-directory semantics, and propagate exit
status and interruption. `GENESIS_REPO` explicitly selects a checkout for a wheel
installation. Core curation and help remain available without Pixi.

The configured Pixi prefix is inspected before execution. A missing or incomplete
environment is rejected with installation instructions; `pixi run --as-is` alone
would otherwise permit execution using host tools. Runtime inspection supports
the prefix reported by Pixi, including detached environments.

The README overview SVG and its current links were removed. Its dated validation
report now links to the original Git revision. Current guides use direct commands;
the original DAP README, scientific settings and dependency locks are preserved.

## Results

| Check | Result and evidence |
| --- | --- |
| `pixi run checks` | **PASS**: ShellCheck, Ruff, formatting, types, Nextflow stubs and all existing scientific/control/curation regressions; [complete log](../evidence/direct-cli/checks.log) |
| `python tests/verify_cli.py` | **PASS**: installation/conflicts, paths with spaces, literal shell-looking arguments, DAP/ATAC option and resume forwarding, exit 23, SIGINT, benchmark delegation, missing runtime rejection, offline core commands and actual Pixi cwd/argv preservation; [log](../evidence/direct-cli/cli.log) |
| Documentation | **PASS**: 212 CLI examples parse, 29 Pixi recipes resolve, links/anchors in 13 documents resolve, original DAP README hash preserved; [log](../evidence/direct-cli/documentation.log) |
| Actual locked installation | **PASS**: install into a temporary bin directory, repeat install, direct help and doctor from outside the checkout; [commands](../evidence/direct-cli/installation.json), [log](../evidence/direct-cli/installation.log) |
| Direct DAP CLI with actual Nextflow stubs | **PASS**: initial 43 completed tasks; first resume 29 completed/10 cached; stable resume one reference validator completed/38 cached; [commands](../evidence/direct-cli/nextflow-stubs.json), [stable trace](../evidence/direct-cli/trace-stable.tsv) |
| Fresh wheel in an independent Python environment | **PASS**: 14 commands, 40 shipped resources checked, core commands without Pixi, explicit-checkout benchmark fixture/plan, and complete offline curation workflow; [commands and results](../evidence/direct-cli/installed-wheel.json), [log](../evidence/direct-cli/installed-wheel.log) |
| Scientific source and locks | **PASS**: no changes to `main.nf`, workflows, modules, scientific configs, Nextflow schema or dependency locks compared with the base revision |

Runtime: Linux x86_64, Python 3.14.5, Pixi 0.81.0, uv 0.11.33 and Nextflow 25.10.4.
Nextflow checks used the already verified plugin cache with `NXF_OFFLINE=true`;
installation checks used existing dependency caches. Temporary paths in evidence
identify these runs and are not installation paths to copy onto another server.

The direct DAP acceptance initially detected a missing `genesis-tools` PATH entry;
the launcher was corrected, regression coverage added, and the final complete
suite, direct pipeline acceptance and wheel checks passed after the correction.
An exploratory wheel harness initially requested `manifest.json` instead of the
fixture's `experiment.toml`; the final independent wheel run uses the correct file.

## Limits and rollback

Pixi 0.81.0 emits an existing deprecation warning for the manifest's
`[system-requirements]` table. It is retained in the logs; this change does not
migrate platform requirements or dependency resolution.
The initial Nextflow run also reports that resume is ignored without previous
history: the existing `nextflow.config` sets `resume = true`. That setting is
unchanged, and subsequent resumes use the retained run history.

These runs validate the CLI, installation and workflow wiring. The direct
Nextflow runs use stubs, and the ATAC launcher regression uses a simulated
Nextflow process. Real scientific-container runs, live SSH, GPU services and API
inference were **NOT RUN** for this update. The earlier
[real-study scientific acceptance](real-study-validation.md) remains separately
dated evidence; no new biological-accuracy claim is made here.

Existing Pixi commands remain supported. To remove the exposed command, inspect
and remove only its installed symlink, following the
[maintenance instructions](../../docs/development.md#command-installation-and-maintenance).
Changing the code revision does not remove run directories or data; synchronize
the selected revision's environments with `pixi run install-all` before use.
