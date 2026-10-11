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
import pandas as pd
from cherimoya.io import PeakGenerator

loader = PeakGenerator(
    peaks=pd.read_csv("train.peaks.bed", sep="\t", header=None, dtype={0: str}),
    negatives=pd.read_csv("train.background.bed", sep="\t", header=None, dtype={0: str}),
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
Reading the chromosome column as text also preserves leading zeros in contig
names. Passing an untyped filename directly can lose those zeros during parsing.

## ChromBPNet

Use commit `ece97c93ccaa2d9ee5bc5687e62f4dbf8d055367`. The adapter's narrowPeak-like
regions include a valid summit offset in column 10. The actual
`ChromBPNetBatchGenerator` was tested against the exported FASTA and raw cut-count
bigWig. Its sequence tensor is `[batch,2114,4]`, whereas Cherimoya's loader returns
`[batch,4,2114]`; do not interchange tensors or infer shared model defaults.

ChromBPNet needs a suitable bias model and its own training configuration. No
human bias model is chosen automatically. Exported bigWigs already use the audited
ATAC cut convention. Do not run an additional fragment-to-track shift on them.

Keep chromosome names as strings. The pinned ChromBPNet training CLI infers
numeric names such as Arabidopsis `1` as integers, which can discard chromosome
folds or fail during FASTA/bigWig lookup. Genesis tests its actual batch generator
with explicitly typed tables, preserving the original reference names:

```python
import pandas as pd
from chrombpnet.training.data_generators.batchgen_generator import ChromBPNetBatchGenerator

columns = ["chr", "start", "end", "name", "score", "strand", "signal", "p", "q", "summit"]
peaks = pd.read_csv("train.peaks.bed", sep="\t", names=columns, dtype={"chr": str})
background = pd.read_csv("train.background.bed", sep="\t", names=columns, dtype={"chr": str})
loader = ChromBPNetBatchGenerator(
    peak_regions=peaks, nonpeak_regions=background, genome_fasta="genome.fa",
    batch_size=64, inputlen=2114, outputlen=1000, max_jitter=0,
    negative_sampling_ratio=1, cts_bw_file="signal.bw", add_revcomp=False,
    return_coords=True, shuffle_at_epoch_start=False,
)
```

This supports data loading without renaming the genome. It does not establish
compatibility with the unmodified ChromBPNet training CLI for numeric contigs.
Use the bundle's declared windows and configure training separately.

## Reproduce loader acceptance

The real-tool fixture generator is `tests/validate_scatac_products.py`. Export its
products with a config naming the exact target SHA, input window 2114, output
window 1000, jitter 0, no controls, `gc-matched-genome-tiles-v1` background with seed 7,
and folds `chr1` / `chr2` / `chr3`. For ChromBPNet declare the unsupplied fixture
bias model explicitly.

Frozen Cherimoya IO dependencies are in
`validation/environments/scatac-loaders/`. Run:

```bash
pixi run genesis scatac model validate --input models/cherimoya/TASK_ID --model-root ../benchmarks/cherimoya --output loader-tests/cherimoya/TASK_ID
pixi run genesis scatac model validate --input models/chrombpnet/TASK_ID --model-root ../benchmarks/chrombpnet --output loader-tests/chrombpnet/TASK_ID
```

The ChromBPNet check uses an immutable Docker image; the Cherimoya check uses
the frozen IO environment. Both test all three folds with a positive and a
background window. Each result retains commands, versions, logs and checksums.
Repeat with `--resume` to verify reuse. The complete fixture check is
`tests/validate_scatac_loaders.py`; it also verifies registry and release gates.
Generate a second product fixture with `--numeric-chromosomes` to exercise
Arabidopsis-style names through both actual loaders.
The additional fixture `--chromosomes 01 02 03` checks leading-zero preservation.
Pass `--background-stride 1000` to the loader fixture test to exercise the explicit
overlapping-window background method. The real pilot uses this recorded choice;
the earlier disjoint-tile attempt is preserved. Always inspect `backgrounds.json`
for candidate counts, within-fold overlap and GC matching deviations.

The deterministic fixture should yield 600 counts in each positive window and
zero in its background. Those values validate the fixture only; they are not
plant QC thresholds. No training result or biological pilot release is implied.
