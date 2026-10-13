"""Exercise the pinned real ChromBPNet batch generator on each exported fold."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--model-root", type=Path, required=True)
parser.add_argument("--bundle", type=Path, required=True)
args = parser.parse_args()
observed = subprocess.check_output(
    ["git", "-C", str(args.model_root), "rev-parse", "HEAD"], text=True
).strip()
if observed != "ece97c93ccaa2d9ee5bc5687e62f4dbf8d055367":
    raise ValueError("Wrong model source revision")
sys.path.insert(0, str(args.model_root))
import numpy as np
import pandas as pd
from chrombpnet.training.data_generators.batchgen_generator import ChromBPNetBatchGenerator

root = args.bundle
columns = ["chr", "start", "end", "name", "score", "strand", "signal", "p", "q", "summit"]
for split in ("train", "validation", "test"):
    regions = pd.read_csv(root / f"{split}.peaks.bed", sep="\t", names=columns)
    background = pd.read_csv(root / f"{split}.background.bed", sep="\t", names=columns).iloc[:1]
    generator = ChromBPNetBatchGenerator(
        regions,
        background,
        str(root / "genome.fa"),
        2,
        2114,
        1000,
        0,
        1,
        str(root / "signal.bw"),
        False,
        True,
        False,
    )
    x, y, coords = generator[0]
    assert x.shape == (2, 2114, 4) and y[0].shape == (2, 1000)
    assert float(y[0][0].sum()) == 600 and float(y[0][1].sum()) == 0
    assert np.isfinite(x).all() and np.isfinite(y[0]).all()
    print(
        json.dumps(
            {
                "loader": "ChromBPNetBatchGenerator",
                "split": split,
                "sequence_shape": list(x.shape),
                "signal_shape": list(y[0].shape),
                "peak_counts": 600,
                "background_counts": 0,
                "training": "NOT_RUN",
            }
        )
    )
