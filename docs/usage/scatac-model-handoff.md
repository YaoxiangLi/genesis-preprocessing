# Loading scATAC exports

A Genesis model bundle contains `genome.fa`, `chrom.sizes`, `signal.bw`, separate
peak/background BEDs for each fold, `loader.json`, `config.json`, QC, source-cell
membership and checksum provenance. Keep the entire directory together.

Before training, verify the bundle, confirm biological identity and annotation
review, and inspect the declared chromosome folds. `model_ready: false` means
that Genesis has not approved a scientific handoff. File-format compatibility
alone is insufficient.

## Cherimoya

Use commit `8ecf7f791ec07c05a701076cc58a0f845bf97609`. Its `PeakGenerator` accepts
one unstranded signal channel for this adapter:

```python
from cherimoya.io import PeakGenerator

loader = PeakGenerator(
    peaks="train.peaks.bed",
    negatives="train.background.bed",
    sequences="genome.fa",
    signals=["signal.bw"],
    controls=None,
    in_window=2114,
    out_window=1000,
    max_jitter=0,
    summits=True,
    negative_ratio=1,
    random_state=7,
    num_workers=0,
)
```

Use the actual window/jitter values in `loader.json`, not these fixture values
when they differ. The model's `fit` function expects the sampler
`loader.dataset`; it constructs its own loader. The validation environment tests
IO only. Install the pinned model repository's full declared environment before
training. Model architecture, loss, optimizer and compute resources remain model
configuration decisions.

## ChromBPNet

Use commit `ece97c93ccaa2d9ee5bc5687e62f4dbf8d055367`. The adapter's narrowPeak-like
regions include a valid summit offset in column 10. The actual
`ChromBPNetBatchGenerator` was tested against the exported FASTA and raw cut-count
bigWig. Its sequence tensor is `[batch,2114,4]`, whereas Cherimoya's loader returns
`[batch,4,2114]`; do not interchange tensors or infer shared model defaults.

ChromBPNet needs a suitable bias model and its own training configuration. No
human bias model is chosen automatically. Exported bigWigs already use the audited
ATAC cut convention. Do not run an additional fragment-to-track shift on them.

## Reproduce loader acceptance

The real-tool fixture generator is `tests/validate_scatac_products.py`. Export its
products with a config naming the exact target SHA, input window 2114, output
window 1000, jitter 0, no controls, `nonoverlapping-genome-tiles-v1` background,
and folds `chr1` / `chr2` / `chr3`. For ChromBPNet declare the unsupplied fixture
bias model explicitly.

Frozen Cherimoya IO dependencies are in
`validation/environments/scatac-loaders/`. Run:

```bash
pixi run uv run --frozen --project validation/environments/scatac-loaders python validation/experiments/scatac/cherimoya_loader.py --model-root ../benchmarks/cherimoya --bundle ../results/scatac-products-fixture/cherimoya
```

`validation/experiments/scatac/chrombpnet_loader.py` takes the same arguments and
runs in the recorded ChromBPNet container. Both scripts test all three folds with
a positive and a background window. Exact recorded Docker arguments and timings
are in `validation/reports/scatac-command-summary.json`.

The deterministic fixture should yield 600 counts in each positive window and
zero in its background. Those values validate the fixture only; they are not
plant QC thresholds. No training result or biological pilot release is implied.
