"""Peak read-end RPM and mean coverage RPKM, reading BAMs directly with pysam."""

from __future__ import annotations

import bz2
import gzip
import math
from bisect import bisect_left
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TextIO

import pysam

from .metadata import chromosome_sizes


@dataclass(frozen=True)
class Region:
    """A BED interval with its original columns preserved."""

    fields: tuple[str, ...]
    chromosome: str
    start: int
    end: int


def open_text(path: Path) -> TextIO:
    """Open plain, gzip, or bzip2 text without invoking a shell."""
    if path.suffix == ".gz":
        return gzip.open(path, "rt")
    if path.suffix == ".bz2":
        return bz2.open(path, "rt")
    return path.open()


def bed_lines(path: Path) -> Iterator[tuple[int, tuple[str, ...]]]:
    """Yield numbered BED fields, skipping blank, comment, track, and browser lines."""
    with open_text(path) as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip() or line.startswith(("#", "track ", "browser ")):
                continue
            yield number, tuple(line.rstrip("\r\n").split("\t"))


def read_regions(path: Path, sizes: dict[str, int] | None = None) -> list[Region]:
    """Read BED regions, preserving row order and rejecting invalid coordinates."""
    regions: list[Region] = []
    for number, fields in bed_lines(path):
        if len(fields) < 3:
            raise ValueError(f"{path}:{number}: expected at least three BED fields")
        start, end = int(fields[1]), int(fields[2])
        if start < 0 or end <= start:
            raise ValueError(f"{path}:{number}: invalid BED interval")
        if sizes is not None and (fields[0] not in sizes or end > sizes[fields[0]]):
            raise ValueError(f"{path}:{number}: interval outside the reference")
        regions.append(Region(fields, fields[0], start, end))
    return regions


class PeakIndex:
    """Find peaks sharing at least one base with an interval, as bedtools intersect does.

    Duplicate and overlapping peaks are reported separately, by their original row index.
    """

    def __init__(self, regions: list[Region]) -> None:
        peaks: dict[str, list[tuple[int, int, int]]] = {}
        for index, region in enumerate(regions):
            peaks.setdefault(region.chromosome, []).append((region.start, region.end, index))
        self._peaks = {chromosome: sorted(rows) for chromosome, rows in peaks.items()}
        self._starts = {
            chromosome: [start for start, _, _ in rows] for chromosome, rows in self._peaks.items()
        }
        self._longest = {
            chromosome: max(end - start for start, end, _ in rows)
            for chromosome, rows in self._peaks.items()
        }

    def overlaps(self, chromosome: str, start: int, end: int) -> Iterator[tuple[int, int]]:
        """Yield (peak row index, overlap length) for peaks overlapping [start, end)."""
        peaks = self._peaks.get(chromosome)
        if peaks is None:
            return
        starts = self._starts[chromosome]
        # A peak can only reach past start if it begins within the longest peak length of it.
        first = bisect_left(starts, start - self._longest[chromosome] + 1)
        last = bisect_left(starts, end)
        for position in range(first, last):
            peak_start, peak_end, index = peaks[position]
            if peak_end > start:
                yield index, min(end, peak_end) - max(start, peak_start)


def count_reads(
    bam: Path,
    sizes: dict[str, int],
    peaks: PeakIndex,
    region_count: int,
    weighting: Literal["NH", "primary"],
    threads: int = 1,
) -> tuple[list[float], float]:
    """Sum alignment weights over peaks and return them with the read-end denominator.

    Each alignment covers its bounding reference span, as legacy pysam.fetch counting did.
    NH mode weights each reported alignment by 1/NH, counting each multimapping read end once
    in the denominator. Primary mode requires no NH tag and counts one retained primary
    alignment per read end, including MAPQ 0. Paired ends count independently, as in the
    historical invocation. Alignments on contigs absent from sizes are ignored.
    """
    if weighting not in ("NH", "primary"):
        raise ValueError(f"Unknown weighting mode: {weighting}")
    counts = [0.0] * region_count
    unique = 0
    multimappers: set[tuple[str, int]] = set()
    with pysam.AlignmentFile(str(bam), threads=threads) as alignments:
        for alignment in alignments.fetch(until_eof=True):
            flag = alignment.flag
            if flag & 0x804 or (weighting == "primary" and flag & 0x100):
                continue
            chromosome = alignment.reference_name
            if chromosome is None or chromosome not in sizes:
                continue
            start, end = alignment.reference_start, alignment.reference_end
            if end is None or end <= start:
                raise ValueError(f"Alignment consumes no reference: {alignment.query_name}")
            if start < 0 or end > sizes[chromosome]:
                raise ValueError(f"Alignment outside reference: {alignment.query_name}")
            nh = 1
            if weighting == "NH":
                tag = alignment.get_tag("NH") if alignment.has_tag("NH") else None
                if not isinstance(tag, int) or tag < 1:
                    raise ValueError("NH weighting requires a positive NH tag on every alignment")
                nh = tag
            if nh == 1:
                unique += 1
            else:
                mate = 1 if flag & 0x40 else 2 if flag & 0x80 else 0
                multimappers.add((alignment.query_name or "", mate))
            weight = 1 / nh
            for index, _ in peaks.overlaps(chromosome, start, end):
                counts[index] += weight
    return counts, float(unique + len(multimappers))


def coverage_sums(coverage: Path, peaks: PeakIndex, region_count: int) -> list[float]:
    """Sum bedGraph values over peaks, weighting each value by its overlap length."""
    sums = [0.0] * region_count
    for number, fields in bed_lines(coverage):
        if len(fields) != 4:
            raise ValueError(f"{coverage}:{number}: expected four bedGraph fields")
        start, end, value = int(fields[1]), int(fields[2]), float(fields[3])
        if start < 0 or end <= start:
            raise ValueError(f"{coverage}:{number}: invalid bedGraph interval")
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{coverage}:{number}: coverage must be finite and nonnegative")
        for index, overlap in peaks.overlaps(fields[0], start, end):
            sums[index] += value * overlap
    return sums


def write_scores(regions: list[Region], scores: list[float], destination: Path) -> None:
    """Atomically append one score to every original BED row."""
    partial = destination.with_name(destination.name + ".partial")
    try:
        with partial.open("w") as stream:
            for region, score in zip(regions, scores, strict=True):
                stream.write("\t".join(region.fields) + f"\t{score:.12g}\n")
        partial.replace(destination)
    finally:
        partial.unlink(missing_ok=True)


def read_end_rpm(
    regions: list[Region],
    bam: Path,
    sizes: dict[str, int],
    weighting: Literal["NH", "primary"],
    threads: int,
) -> list[float]:
    """Read-end RPM for each region, rejecting a BAM with no retained read ends."""
    counts, denominator = count_reads(
        bam, sizes, PeakIndex(regions), len(regions), weighting, threads
    )
    if regions and denominator == 0:
        raise ValueError("Cannot normalize peaks: no retained mapped read ends")
    return [count * 1_000_000 / denominator for count in counts] if regions else []


def mean_coverage(regions: list[Region], coverage: Path) -> list[float]:
    """Length-weighted mean bedGraph value for each region, counting uncovered bases as zero."""
    sums = coverage_sums(coverage, PeakIndex(regions), len(regions))
    return [
        total / (region.end - region.start) for region, total in zip(regions, sums, strict=True)
    ]


def quantify(
    *,
    bed: Path,
    bam: Path,
    coverage: Path,
    chrom_sizes: Path,
    rpm_output: Path,
    rpkm_output: Path,
    weighting: Literal["NH", "primary"] = "NH",
    threads: int = 1,
) -> None:
    """Append read-end RPM and mean coverage RPKM to each original BED/narrowPeak row.

    :param bed: Original plain, gzipped, or bzip2-compressed BED/narrowPeak.
    :param bam: Coordinate-sorted BAM of retained alignments.
    :param coverage: RPKM-normalized bedGraph generated by bamCoverage.
    :param chrom_sizes: Chromosome sizes defining the counting reference.
    :param rpm_output: Original BED rows with appended read-end RPM.
    :param rpkm_output: Original BED rows with appended mean coverage RPKM.
    :param weighting: NH fractional weighting or primary read-end counting.
    :param threads: Threads for BAM decompression.
    """
    sizes = chromosome_sizes(chrom_sizes)
    regions = read_regions(bed, sizes)
    write_scores(regions, read_end_rpm(regions, bam, sizes, weighting, threads), rpm_output)
    write_scores(regions, mean_coverage(regions, coverage), rpkm_output)


def quantify_peaks(
    *,
    bed: Path,
    bam: Path,
    chrom_sizes: Path,
    output: Path,
    weighting: Literal["NH", "primary"] = "NH",
    normalization: Literal["RPM", "RPKM"] = "RPM",
    threads: int = 1,
) -> None:
    """Append legacy read-end RPM or RPKM scores to BED/narrowPeak rows.

    :param bed: Plain, gzipped, or bzip2-compressed BED/narrowPeak input.
    :param bam: Input BAM or SAM.
    :param chrom_sizes: Chromosome sizes defining the counting reference.
    :param output: BED-like output with an appended score.
    :param weighting: NH fractional counting, or explicit primary-alignment counting.
    :param normalization: Read-end RPM, or read-end RPM divided by peak length in kb.
    :param threads: Threads for BAM decompression.
    """
    if normalization not in ("RPM", "RPKM"):
        raise ValueError(f"Unknown normalization: {normalization}")
    sizes = chromosome_sizes(chrom_sizes)
    regions = read_regions(bed, sizes)
    scores = read_end_rpm(regions, bam, sizes, weighting, threads)
    if normalization == "RPKM":
        scores = [
            score * 1000 / (region.end - region.start)
            for region, score in zip(regions, scores, strict=True)
        ]
    write_scores(regions, scores, output)


def mean_peak_rpkm(*, bed: Path, coverage: Path, output: Path) -> None:
    """Append length-weighted mean deepTools RPKM coverage to each original peak.

    :param bed: Original BED/narrowPeak rows.
    :param coverage: RPKM-normalized bedGraph generated by bamCoverage.
    :param output: BED-like output with an appended mean RPKM value.
    """
    regions = read_regions(bed)
    write_scores(regions, mean_coverage(regions, coverage), output)
