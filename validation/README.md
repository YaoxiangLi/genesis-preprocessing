# Validation studies

This directory publishes the validation workspace's audit, design, reports and
small deterministic contract fixtures as of 2026-10-09. The current supported
paired-end bulk ATAC workflow is validated on synthetic fixtures and small
Arabidopsis and maize subsets. Its predecessor remains under `experimental/atac/`
for historical benchmark reproduction.

Start with the [bulk ATAC and execution validation](reports/supported-atac-execution-validation.md),
[compact evidence](evidence/supported-atac/README.md), and
[reproduction instructions](reproduce/supported-atac/README.md).

The [schematic CLI validation](reports/schematic-cli-validation.md) covers the
offline figure generator, bundled artwork and browser checks.

Earlier studies include the [benchmark validation](reports/benchmark-validation.md),
[overall validation](reports/GENESIS_PREPROCESSING_VALIDATION.md),
[benchmark design](design/benchmark-spec.md), and
[model-ready pseudobulk contract](design/scatac-pseudobulk-spec.md).

Reports retain their original observation dates, tested commit IDs and limitations.
Statements that work was local/unpushed describe the state at the time of testing;
this snapshot is now published on the fork. No unresolved biological claim becomes
validated by publication. The exact Sorghum DAP reference and metadata workbook
remain outstanding; public ATAC subset validation does not resolve those blockers.

Raw logs, BAMs, FASTQs, downloaded data and generated outputs remain in the original
workspace under `results/` and `scratch/`; links to those locations are workspace
evidence references and are not hosted here. Local absolute paths in provenance
are historical paths, not runnable paths for a new checkout. Generate portable
benchmark fixtures using the [benchmark guide](../benchmarks/README.md).
Scheduler state and the unsent questions draft are intentionally excluded.
`snapshot.json` records source and published content checksums for the original snapshot;
subsequent validation additions are recorded separately in `updates`. Markdown repository
links are adjusted for this directory's location. Small contract fixtures preserve
the workspace's relative `fixtures/` and `design/` relationship.

To rerun the standalone contract checks with the project environment, create their
workspace output directories first:

```bash
mkdir -p validation/results/contracts validation/scratch/completion
pixi run uv run --frozen --project genesis_tools python validation/fixtures/pseudobulk/test_contract.py
pixi run uv run --frozen --project genesis_tools python validation/fixtures/multiome/test_contract.py
```

Schema checks additionally require the previously recorded jsonschema environment;
these archived fixtures do not add a dependency to the production environment.
