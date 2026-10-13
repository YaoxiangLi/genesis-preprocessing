# Validation studies

Use these reports to check what was tested, on which revision, with which inputs.
Start with the task guides in [the documentation index](../docs/README.md) when
running a new analysis. Each report retains its observation date, commands,
measurements and limits; an earlier successful test is not a test of later code.

| Evidence | What it covers |
| --- | --- |
| [Pipeline package comparison](reports/pipeline-method-comparison.md) | Measured package/workflow comparisons, metric definitions, tables and figures; completed and pending work distinguished |
| [Documentation review](reports/documentation-review.md) | User-guide changes, preserved scientific information, command and link checks |
| [Real study acceptance](reports/real-study-validation.md) | DAP/ATAC processing through registration, collection, validation and reviewed export on synthetic inputs |
| [Supported bulk ATAC](reports/supported-atac-execution-validation.md) | Synthetic fixtures and small public Arabidopsis/maize subsets; [compact evidence](evidence/supported-atac/README.md) and [reproduction](reproduce/supported-atac/README.md) |
| [Curation and AI](reports/hybrid-llm-validation.md) | Registry/review, mock and HTTP providers, simulated model services; live GPU/API acceptance is separate |
| [Single-cell delivery](reports/scatac-delivery-validation.md) | Fragment/pseudobulk contracts and pinned model-loader checks |
| [Direct command installation](reports/direct-cli-validation.md) | Installation and use of `genesis` outside the checkout |
| [Figure commands](reports/schematic-cli-validation.md) | Offline SVG rendering, licensed assets and browser checks |
| [Integration validation](reports/integration-validation-20261012.md) | Regression tests, scientific output checks and installation at the recorded revision |
| [DAP regressions](reports/dap-regressions-20261012.md) | Reference-cache validation, container permissions, build behavior and duplicate-count semantics |
| [Earlier sensitivity study](reports/dapseq-sensitivity-study.md) | Explicit MAPQ/duplicate experiments; not an aligner-selection benchmark |

For comparing pipeline packages, use [benchmarks](../benchmarks/README.md). Keep
computational correctness, biological quality and execution performance separate.
Small synthetic or shallow public subsets cannot establish full-study accuracy.

## Find the underlying evidence

- `evidence/` contains compact command receipts, tables, traces and selected logs.
- `reports/` explains results and their limitations.
- `design/` records proposed contracts and method decisions; consult current guides
  to determine what is implemented.
- `audit/` preserves the original environment and repository inspection.
- `reproduce/` contains portable recipes for specified public fixtures.

Large reads, BAMs, reference indexes, environments and analysis work directories
are excluded from Git. Historical workspace paths in reports identify original
observations; they are not download links or setup paths. Where logs are committed,
reports link to those files. A Git clone is not a backup of scientific data.

`snapshot.json` records the original validation snapshot's checksums; later additions
are listed in its `updates` records or their own validation reports. A later report
does not change an earlier NOT RUN or blocked result. The unresolved Sorghum DAP
reference and metadata workbook remain documented in the original reports.

## Reproduce archived contract checks

To rerun the standalone contract checks with the project environment, create their
workspace output directories first:

```bash
mkdir -p validation/results/contracts validation/scratch/completion
pixi run uv run --frozen --project genesis_tools python validation/fixtures/pseudobulk/test_contract.py
pixi run uv run --frozen --project genesis_tools python validation/fixtures/multiome/test_contract.py
```

Schema checks additionally require the previously recorded jsonschema environment;
these archived fixtures do not add a dependency to the production environment.
