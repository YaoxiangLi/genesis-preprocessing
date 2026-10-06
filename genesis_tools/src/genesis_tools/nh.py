"""Add NH tags to query-name-grouped SAM for optional Bowtie comparisons."""

from __future__ import annotations

from collections import Counter
from itertools import chain, groupby
from pathlib import Path


def add_nh(*, input: Path, output: Path) -> None:
    """Add reported-alignment multiplicities to a name-sorted SAM file.

    :param input: Query-name-grouped SAM from samtools sort -n -O SAM.
    :param output: SAM with NH tags assigned separately to each mate.
    """
    with input.open() as source, output.open("w") as destination:
        first = ""
        for line in source:
            if line.startswith("@"):
                destination.write(line)
            else:
                first = line
                break
        if not first:
            return
        lines = chain([first], source)
        records = (line.rstrip("\n").split("\t") for line in lines)
        for _, group in groupby(records, key=lambda fields: fields[0]):
            alignments = list(group)
            if any(len(fields) < 11 for fields in alignments):
                raise ValueError("Malformed SAM alignment")
            counts = Counter(int(fields[1]) & 0xC0 for fields in alignments)
            for fields in alignments:
                tags = [tag for tag in fields[11:] if not tag.startswith("NH:")]
                nh = counts[int(fields[1]) & 0xC0]
                destination.write("\t".join([*fields[:11], *tags, f"NH:i:{nh}"]) + "\n")
