"""Infer layout, genome size, and uniform read length from actual inputs."""

from __future__ import annotations

import csv
import gzip
from pathlib import Path

METADATA_HEADER = (
    "sample_id",
    "species",
    "reference_fasta",
    "layout",
    "genome_size",
    "analysis_read_length",
    "read1_reads_checked",
    "read2_reads_checked",
)


def chromosome_sizes(path: Path) -> dict[str, int]:
    """Read positive chromosome lengths, rejecting duplicates and malformed rows."""
    sizes: dict[str, int] = {}
    with path.open() as stream:
        for number, line in enumerate(stream, 1):
            fields = line.split()
            if len(fields) != 2 or not fields[1].isascii() or not fields[1].isdigit():
                raise ValueError(f"{path}:{number}: expected chromosome and integer size")
            size = int(fields[1])
            if size <= 0 or fields[0] in sizes:
                raise ValueError(f"{path}:{number}: sizes must be positive and names unique")
            sizes[fields[0]] = size
    if not sizes:
        raise ValueError(f"{path}: chromosome sizes file is empty")
    return sizes


def inspect_read_length(path: Path, limit: int = 100) -> tuple[int, int]:
    """Return uniform sequence length and number of records inspected."""
    length = 0
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
                not header.startswith("@")
                or not separator.startswith("+")
                or not sequence
                or len(quality) != len(sequence)
            ):
                raise ValueError(f"{path}: malformed FASTQ record {record}")
            if checked and len(sequence) != length:
                raise ValueError(f"{path}: the first {limit} reads must have identical lengths")
            length = len(sequence)
            checked += 1
    if not checked:
        raise ValueError(f"{path}: FASTQ contains no reads")
    return length, checked


def infer_metadata(
    *,
    sample_id: str,
    species: str,
    reference_fasta: str,
    chrom_sizes: Path,
    read1: Path,
    output: Path,
    read2: Path | None = None,
) -> None:
    """Write one validated sample metadata row.

    :param sample_id: Sample identifier.
    :param species: Species from the sample sheet.
    :param reference_fasta: Reference FASTA basename.
    :param chrom_sizes: Derived chromosome sizes.
    :param read1: Gzipped first reads.
    :param output: Metadata TSV destination.
    :param read2: Optional gzipped second reads.
    """
    genome_size = sum(chromosome_sizes(chrom_sizes).values())
    length, count1 = inspect_read_length(read1)
    count2 = 0
    if read2 is not None:
        mate_length, count2 = inspect_read_length(read2)
        if mate_length != length:
            raise ValueError(
                f"{read2}: mate length {mate_length} differs from read1 length {length}"
            )
    partial = output.with_name(output.name + ".partial")
    try:
        with partial.open("w", newline="") as stream:
            writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
            writer.writerow(METADATA_HEADER)
            writer.writerow(
                [
                    sample_id,
                    species,
                    reference_fasta,
                    "PE" if read2 else "SE",
                    genome_size,
                    length,
                    count1,
                    count2,
                ]
            )
        partial.replace(output)
    finally:
        partial.unlink(missing_ok=True)
