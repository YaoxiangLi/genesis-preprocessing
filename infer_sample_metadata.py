"""Infer sample metadata from chromosome sizes and up to 100 reads per FASTQ."""

from __future__ import annotations

import argparse
import csv
import gzip
from pathlib import Path
import sys

METADATA_HEADER = (
    "sample_id", "layout", "genome_size", "analysis_read_length",
    "read1_reads_checked", "read2_reads_checked",
)


def genome_size_from_chrom_sizes(path: Path) -> int:
    total = 0
    chromosomes: set[str] = set()
    with path.open() as stream:
        for line_number, line in enumerate(stream, 1):
            fields = line.split()
            if len(fields) != 2 or not fields[1].isascii() or not fields[1].isdigit():
                raise ValueError(f"{path}:{line_number}: expected chromosome and integer size")
            size = int(fields[1])
            if size <= 0 or fields[0] in chromosomes:
                raise ValueError(f"{path}:{line_number}: sizes must be positive and names unique")
            chromosomes.add(fields[0])
            total += size
    if not chromosomes:
        raise ValueError(f"{path}: chromosome sizes file is empty")
    return total


def inspect_read_length(path: Path, limit: int = 100) -> tuple[int, int]:
    """Return uniform sequence length and count; reject malformed FASTQ records."""
    read_length = 0
    checked = 0
    with gzip.open(path, "rt", encoding="ascii") as stream:
        for record in range(1, limit + 1):
            header = stream.readline()
            if not header:
                break
            sequence = stream.readline().rstrip("\r\n")
            separator = stream.readline()
            quality = stream.readline().rstrip("\r\n")
            if (
                not header.startswith("@") or not separator.startswith("+")
                or not sequence or len(quality) != len(sequence)
            ):
                raise ValueError(f"{path}: malformed FASTQ record {record}")
            length = len(sequence)
            if checked and length != read_length:
                raise ValueError(
                    f"{path}: read {record} has length {length}, expected {read_length}; "
                    "the first 100 reads must have identical lengths"
                )
            read_length = length
            checked += 1
    if not checked:
        raise ValueError(f"{path}: FASTQ contains no reads")
    return read_length, checked


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--chrom-sizes", required=True, type=Path)
    parser.add_argument("--read1", required=True, type=Path)
    parser.add_argument("--read2", type=Path)
    args = parser.parse_args()
    try:
        genome_size = genome_size_from_chrom_sizes(args.chrom_sizes)
        length, read1_checked = inspect_read_length(args.read1)
        read2_checked = 0
        if args.read2 is not None:
            mate_length, read2_checked = inspect_read_length(args.read2)
            if mate_length != length:
                raise ValueError(
                    f"{args.read2}: mate length {mate_length} differs from read1 length {length}"
                )
    except (OSError, ValueError, EOFError) as error:
        parser.exit(1, f"Error: {error}\n")
    writer = csv.writer(sys.stdout, delimiter="\t", lineterminator="\n")
    writer.writerow(METADATA_HEADER)
    writer.writerow([
        args.sample_id, "PE" if args.read2 is not None else "SE", genome_size,
        length, read1_checked, read2_checked,
    ])


if __name__ == "__main__":
    main()
