"""Known-answer test of the pinned optional raw-pilot fragment producer."""

from __future__ import annotations

import argparse
import random
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chromap", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    binary = str(args.chromap.resolve())
    rng = random.Random(234)
    sequence = "".join(rng.choices("ACGT", k=50_000))
    complement = str.maketrans("ACGT", "TGCA")

    def rc(value: str) -> str:
        return value.translate(complement)[::-1]

    root = args.output.resolve()
    (root / "ref.fa").write_text(">chr1\n" + sequence + "\n")
    barcodes = ["ACAGCGGGTGTGTTAC", "ACAGCGGGTTGTTCTT"]
    translated = ["AAACAGCCAAACAACA-1", "AAACAGCCAAACATAG-1"]
    (root / "whitelist.txt").write_text("\n".join(barcodes) + "\n")
    (root / "translation.tsv").write_text(
        "".join(
            f"{target}\t{source}\n" for target, source in zip(translated, barcodes, strict=True)
        )
    )
    records = [(1000, 1300, 0), (1000, 1300, 0), (1000, 1300, 1), (4000, 4300, 0)]
    for mate in (1, 2, 3):
        with (root / f"read{mate}.fq").open("w") as stream:
            for n, (start, end, barcode) in enumerate(records):
                read = (
                    sequence[start : start + 75]
                    if mate == 1
                    else rc(sequence[end - 75 : end])
                    if mate == 2
                    else "CAGACGCG" + rc(barcodes[barcode])
                )
                stream.write(f"@pair{n}\n{read}\n+\n{'I' * len(read)}\n")
    commands = [
        [binary, "-i", "-r", "ref.fa", "-o", "ref.index"],
        [
            binary,
            "--preset",
            "atac",
            "-r",
            "ref.fa",
            "-x",
            "ref.index",
            "-1",
            "read1.fq",
            "-2",
            "read2.fq",
            "-b",
            "read3.fq",
            "-q",
            "30",
            "-t",
            "2",
            "--read-format",
            "r1:0:-1,r2:0:-1,bc:8:23:-",
            "--barcode-whitelist",
            "whitelist.txt",
            "--barcode-translate",
            "translation.tsv",
            "--summary",
            "summary.tsv",
            "-o",
            "fragments.tsv",
        ],
    ]
    for n, command in enumerate(commands):
        with (
            (root / f"command-{n}.stdout").open("w") as out,
            (root / f"command-{n}.stderr").open("w") as err,
        ):
            subprocess.run(command, cwd=root, stdout=out, stderr=err, check=True)
    rows = [line.split() for line in (root / "fragments.tsv").read_text().splitlines()]
    observed = {(c, int(s), int(e), b): int(n) for c, s, e, b, n in rows}
    assert len(rows) == 3
    assert observed == {
        ("chr1", 1004, 1295, translated[0]): 2,
        ("chr1", 1004, 1295, translated[1]): 1,
        ("chr1", 4004, 4295, translated[0]): 1,
    }
    assert sum(observed.values()) == len(records)
    print(
        "PASS: exact +4/-5 coordinates, barcode orientation/translation, cell-level support and EOF"
    )


if __name__ == "__main__":
    main()
