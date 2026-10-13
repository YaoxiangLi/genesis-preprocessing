"""Exercise the pinned real Cherimoya IO module, including background windows."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
from pathlib import Path

import torch

parser = argparse.ArgumentParser()
parser.add_argument("--model-root", type=Path, required=True)
parser.add_argument("--bundle", type=Path, required=True)
args = parser.parse_args()
observed = subprocess.check_output(
    ["git", "-C", str(args.model_root), "rev-parse", "HEAD"], text=True
).strip()
if observed != "8ecf7f791ec07c05a701076cc58a0f845bf97609":
    raise ValueError("Wrong model source revision")
source = args.model_root / "cherimoya/io.py"
spec = importlib.util.spec_from_file_location("cherimoya_pinned_io", source)
assert spec is not None and spec.loader is not None
io = importlib.util.module_from_spec(spec)
spec.loader.exec_module(io)
root = args.bundle
for split in ("train", "validation", "test"):
    loader = io.PeakGenerator(
        str(root / f"{split}.peaks.bed"),
        str(root / f"{split}.background.bed"),
        str(root / "genome.fa"),
        [str(root / "signal.bw")],
        in_window=2114,
        out_window=1000,
        max_jitter=0,
        negative_ratio=1,
        reverse_complement=False,
        shuffle=False,
        summits=True,
        random_state=7,
        pin_memory=False,
        num_workers=0,
        batch_size=2,
    )
    x, y = next(iter(loader))[:2]
    assert list(x.shape) == [2, 4, 2114] and list(y.shape) == [2, 1, 1000]
    assert float(y[0].sum()) == 600 and float(y[1].sum()) == 0
    print(
        json.dumps(
            {
                "loader": "PeakGenerator",
                "split": split,
                "sequence_shape": list(x.shape),
                "signal_shape": list(y.shape),
                "peak_counts": 600,
                "background_counts": 0,
                "torch": torch.__version__,
                "training": "NOT_RUN",
            }
        )
    )
