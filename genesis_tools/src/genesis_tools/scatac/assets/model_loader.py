"""Run inside a pinned model environment; compare real loader tensors to source tracks."""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads((args.bundle / "loader.json").read_text())
    sha = subprocess.check_output(
        ["git", "-C", str(args.model_root), "rev-parse", "HEAD"], text=True
    ).strip()
    if sha != config["model_sha"]:
        raise ValueError("Wrong model source revision")
    if subprocess.run(
        ["git", "-C", str(args.model_root), "diff", "--quiet", "HEAD"], check=False
    ).returncode:
        raise ValueError("Modified model source")
    np = importlib.import_module("numpy")
    bw_module = importlib.import_module("pyBigWig")
    target = config["target"]
    in_window, out_window = config["input_window"], config["output_window"]
    if target == "cherimoya":
        spec = importlib.util.spec_from_file_location(
            "genesis_pinned_io", args.model_root / "cherimoya/io.py"
        )
        if spec is None or spec.loader is None:
            raise ValueError("Missing Cherimoya IO module")
        io = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(io)
        version = importlib.import_module("torch").__version__
    else:
        sys.path.insert(0, str(args.model_root))
        io = importlib.import_module("chrombpnet.training.data_generators.batchgen_generator")
        version = importlib.import_module("tensorflow").__version__
    args.output.mkdir(parents=True, exist_ok=True)
    fasta_index = {
        f[0]: tuple(map(int, f[1:5]))
        for f in (line.split() for line in (args.bundle / "genome.fa.fai").read_text().splitlines())
    }

    def sequence(chrom: str, start: int, length: int) -> str:
        # Independent byte-offset read, without using either model's FASTA reader.
        _, offset, bases, width = fasta_index[chrom]
        with (args.bundle / "genome.fa").open("rb") as stream:
            stream.seek(offset + start // bases * width + start % bases)
            raw = stream.read(length + (length // bases + 2) * (width - bases))
        return raw.replace(b"\n", b"").replace(b"\r", b"")[:length].decode().upper()

    folds = []
    with bw_module.open(str(args.bundle / "signal.bw")) as bw:
        for split in ("train", "validation", "test"):
            selected = []
            paths = []
            for kind in ("peaks", "background"):
                with (args.bundle / f"{split}.{kind}.bed").open() as source:
                    row = source.readline().rstrip()
                if not row:
                    raise ValueError("Missing positive or background regions")
                selected.append(row.split("\t"))
                path = args.output / f"{split}.{kind}.bed"
                path.write_text(row + "\n")
                paths.append(path)
            pd = importlib.import_module("pandas")
            columns = [
                "chr",
                "start",
                "end",
                "name",
                "score",
                "strand",
                "signal",
                "p",
                "q",
                "summit",
            ]
            # Both loaders accept dataframes. Preserve identifiers before inference
            # can turn "1" into an integer or strip leading zeros from "01".
            regions = [pd.read_csv(p, sep="\t", names=columns, dtype={"chr": str}) for p in paths]
            if target == "cherimoya":
                loader = io.PeakGenerator(
                    regions[0],
                    regions[1],
                    str(args.bundle / "genome.fa"),
                    [str(args.bundle / "signal.bw")],
                    in_window=in_window,
                    out_window=out_window,
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
                x, values = x.numpy(), y.numpy()[:, 0, :]
                expected_shape = (2, 4, in_window)
            else:
                loader = io.ChromBPNetBatchGenerator(
                    regions[0],
                    regions[1],
                    str(args.bundle / "genome.fa"),
                    2,
                    in_window,
                    out_window,
                    0,
                    1,
                    str(args.bundle / "signal.bw"),
                    False,
                    True,
                    False,
                )
                x, y, _ = loader[0]
                values = y[0]
                expected_shape = (2, in_window, 4)
            if x.shape != expected_shape or values.shape != (2, out_window):
                raise ValueError("Unexpected model tensor shape")
            if not np.isfinite(x).all() or not np.isfinite(values).all() or (values < 0).any():
                raise ValueError("Nonfinite or negative raw model signal")
            counts = []
            for index, row in enumerate(selected):
                center = int(row[1]) + int(row[9])
                expected = np.nan_to_num(
                    bw.values(
                        row[0], center - out_window // 2, center + out_window // 2, numpy=True
                    )
                )
                if not np.array_equal(expected, values[index]):
                    raise ValueError("Loader signal differs from independently read bigWig bases")
                seq = sequence(row[0], center - in_window // 2, in_window)
                expected_sequence = np.array(
                    [[base == letter for letter in "ACGT"] for base in seq]
                )
                observed_sequence = x[index].T if target == "cherimoya" else x[index]
                if not np.array_equal(expected_sequence, observed_sequence):
                    raise ValueError("Loader one-hot sequence differs from the source FASTA")
                if target == "chrombpnet" and not np.allclose(
                    y[1][index], np.log1p(expected.sum())
                ):
                    raise ValueError("ChromBPNet count target differs from raw source counts")
                counts.append(float(values[index].sum()))
            folds.append(
                {
                    "split": split,
                    "sequence_shape": list(x.shape),
                    "signal_shape": list(values.shape),
                    "counts": counts,
                    "per_base_signal": "PASS",
                    "per_base_sequence": "PASS",
                    "chromosomes": [row[0] for row in selected],
                }
            )
    result = {
        "target": target,
        "model_sha": sha,
        "folds": folds,
        "status": "PASS",
        "framework_version": version,
        "numpy": np.__version__,
        "pyBigWig": bw_module.__version__,
        "training": "NOT_RUN",
    }
    (args.output / "loader-result.json").write_text(json.dumps(result, sort_keys=True) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
