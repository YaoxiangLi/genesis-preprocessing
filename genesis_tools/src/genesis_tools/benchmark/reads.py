"""FASTQ integrity and deterministic nested, paired template subsampling."""

from __future__ import annotations

import gzip
import hashlib
import heapq
import itertools
from collections.abc import Iterator
from pathlib import Path


def fastq(path: Path) -> Iterator[tuple[bytes, bytes]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rb") as stream:
        while header := stream.readline():
            sequence, plus, quality = stream.readline(), stream.readline(), stream.readline()
            if (
                not header.startswith(b"@")
                or not plus.startswith(b"+")
                or not quality.endswith(b"\n")
                or not sequence.strip()
                or len(sequence.rstrip(b"\r\n")) != len(quality.rstrip(b"\r\n"))
            ):
                raise ValueError("Corrupt or truncated FASTQ record")
            name = header[1:].split()[0]
            if name.endswith((b"/1", b"/2")):
                name = name[:-2]
            yield name, header + sequence + plus + quality


def paired(read1: Path, read2: Path) -> Iterator[tuple[bytes, bytes, bytes]]:
    found = False
    for first, second in itertools.zip_longest(fastq(read1), fastq(read2)):
        if first is None or second is None or first[0] != second[0]:
            raise ValueError("FASTQ mates differ in record count or template names")
        found = True
        yield first[0], first[1], second[1]
    if not found:
        raise ValueError("Empty FASTQ library")


def subset(
    read1: Path, read2: Path, out1: Path, out2: Path, *, templates: int, seed: int, expected: int
) -> dict[str, int | str]:
    """Select the lowest seeded hashes of (record index, template name), preserving order.

    Index disambiguates repeated source names. Smaller caps are nested subsets for
    fixed input bytes/seed; iteration order is part of the checksummed input contract.
    """
    if out1.resolve() == out2.resolve() or out1.exists() or out2.exists():
        raise ValueError("Subset outputs must be distinct new files")
    if templates <= 0:
        raise ValueError("Template cap must be positive")
    if read1.resolve() in {out1.resolve(), out2.resolve()} or read2.resolve() in {
        out1.resolve(),
        out2.resolve(),
    }:
        raise ValueError("Subsampling may not overwrite original FASTQs")
    heap: list[tuple[int, int]] = []
    count = 0
    for index, (name, _, _) in enumerate(paired(read1, read2)):
        score = int.from_bytes(hashlib.sha256(f"{seed}:{index}:".encode() + name).digest(), "big")
        item = (-score, -index)
        if len(heap) < templates:
            heapq.heappush(heap, item)
        elif item > heap[0]:
            heapq.heapreplace(heap, item)
        count += 1
    if count != expected:
        raise ValueError("Declared raw template count disagrees with FASTQs")
    selected = {-index for _, index in heap}
    with out1.open("xb") as first_raw, out2.open("xb") as second_raw:
        with (
            gzip.GzipFile(fileobj=first_raw, mode="wb", filename="", mtime=0) as first,
            gzip.GzipFile(fileobj=second_raw, mode="wb", filename="", mtime=0) as second,
        ):
            for index, (_, r1, r2) in enumerate(paired(read1, read2)):
                if index in selected:
                    first.write(r1)
                    second.write(r2)
    return {
        "input_templates": count,
        "selected_templates": len(selected),
        "seed": seed,
        "method": (
            "lowest SHA256(seed, record index, canonical template name); "
            "original record order retained"
        ),
    }
