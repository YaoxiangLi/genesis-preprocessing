"""Modernized interval RPM/RPKM counting, using managed samtools and bedtools."""

from __future__ import annotations

import bz2
import gzip
import json
import math
import re
import subprocess
import tempfile
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TextIO

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


def read_regions(path: Path, sizes: dict[str, int] | None = None) -> list[Region]:
    """Read BED regions, preserving row order and rejecting invalid coordinates."""
    regions: list[Region] = []
    with open_text(path) as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip() or line.startswith(("#", "track ", "browser ")):
                continue
            fields = tuple(line.rstrip("\r\n").split("\t"))
            if len(fields) < 3:
                raise ValueError(f"{path}:{number}: expected at least three BED fields")
            start, end = int(fields[1]), int(fields[2])
            if start < 0 or end <= start:
                raise ValueError(f"{path}:{number}: invalid BED interval")
            if sizes is not None and (fields[0] not in sizes or end > sizes[fields[0]]):
                raise ValueError(f"{path}:{number}: interval outside the reference")
            regions.append(Region(fields, fields[0], start, end))
    return regions


def command_lines(command: list[str]) -> Iterator[str]:
    """Stream checked command output, terminating the child on validation failure."""
    with subprocess.Popen(command, stdout=subprocess.PIPE, text=True) as process:
        if process.stdout is None:
            raise RuntimeError("Subprocess stdout was not captured")
        try:
            yield from process.stdout
            status = process.wait()
            if status:
                raise subprocess.CalledProcessError(status, command)
        finally:
            process.stdout.close()
            if process.poll() is None:
                process.terminate()
                process.wait()


def reference_span(cigar: str) -> int:
    """Compute the bounding reference span used by legacy pysam.fetch counting."""
    operations = re.findall(r"(\d+)([MIDNSHP=X])", cigar)
    if not operations or "".join(n + op for n, op in operations) != cigar:
        raise ValueError(f"Invalid CIGAR: {cigar}")
    span = sum(int(n) for n, op in operations if op in "MDN=X")
    if span <= 0:
        raise ValueError(f"CIGAR consumes no reference: {cigar}")
    return span


def weighted_alignments(
    bam: Path,
    sizes: dict[str, int],
    destination: Path,
    weighting: str,
) -> float:
    """Write bounding BED spans and return the legacy read-end denominator.

    NH mode weights each reported alignment by 1/NH, counting each multimapping
    read end once in the denominator. Primary mode requires no NH tag and counts
    one retained primary alignment per read end, including MAPQ 0. Paired ends
    count independently, as in the historical invocation.
    """
    if weighting not in ("NH", "primary"):
        raise ValueError(f"Unknown weighting mode: {weighting}")
    unique = 0
    multimappers: set[tuple[str, int]] = set()
    with destination.open("w") as stream:
        for line in alignment_lines(bam):
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 11:
                raise ValueError("Malformed SAM alignment")
            flag = int(fields[1])
            if flag & 0x804 or (weighting == "primary" and flag & 0x100):
                continue
            chromosome = fields[2]
            if chromosome not in sizes:
                continue
            start = int(fields[3]) - 1
            end = start + reference_span(fields[5])
            if start < 0 or end > sizes[chromosome]:
                raise ValueError(f"Alignment outside reference: {fields[0]}")
            nh = 1
            if weighting == "NH":
                tags = [tag[5:] for tag in fields[11:] if tag.startswith("NH:i:")]
                if len(tags) != 1 or int(tags[0]) < 1:
                    raise ValueError("NH weighting requires a positive NH tag on every alignment")
                nh = int(tags[0])
            if nh == 1:
                unique += 1
            else:
                mate = 1 if flag & 0x40 else 2 if flag & 0x80 else 0
                multimappers.add((fields[0], mate))
            stream.write(f"{chromosome}\t{start}\t{end}\t{1 / nh:.17g}\n")
    return float(unique + len(multimappers))


def indexed_regions(regions: list[Region], destination: Path) -> None:
    """Write BED intervals with stable row indexes for duplicate and overlapping peaks."""
    with destination.open("w") as stream:
        for index, region in enumerate(regions):
            stream.write(f"{region.chromosome}\t{region.start}\t{region.end}\t{index}\n")


def overlap_sums(
    lines: Iterable[str],
    region_count: int,
    *,
    length_weighted: bool,
) -> list[float]:
    """Sum weights from bedtools output, using original peak row indexes."""
    sums = [0.0] * region_count
    for line in lines:
        fields = line.rstrip("\n").split("\t")
        if len(fields) != 8:
            raise ValueError("Expected four columns from each intersected BED file")
        value = float(fields[3])
        if not math.isfinite(value) or value < 0:
            raise ValueError("Coverage and alignment weights must be finite and nonnegative")
        index = int(fields[7])
        if not 0 <= index < region_count:
            raise ValueError("Invalid peak index")
        if length_weighted:
            overlap = min(int(fields[2]), int(fields[6])) - max(int(fields[1]), int(fields[5]))
            if overlap <= 0:
                raise ValueError("Intersected intervals must overlap")
            value *= overlap
        sums[index] += value
    return sums


def interval_sums(
    values: Path,
    peaks: Path,
    region_count: int,
    *,
    length_weighted: bool,
) -> list[float]:
    """Run bedtools and sum weights or overlap-length-weighted coverage."""
    command = ["bedtools", "intersect", "-a", str(values), "-b", str(peaks), "-wa", "-wb"]
    return overlap_sums(command_lines(command), region_count, length_weighted=length_weighted)


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


def quantify_peaks(
    *,
    bed: Path,
    bam: Path,
    chrom_sizes: Path,
    output: Path,
    weighting: Literal["NH", "primary"] = "NH",
    normalization: Literal["RPM", "RPKM"] = "RPM",
) -> None:
    """Append legacy read-end RPM or RPKM scores to BED/narrowPeak rows.

    :param bed: Plain, gzipped, or bzip2-compressed BED/narrowPeak input.
    :param bam: Input BAM, read using samtools on PATH.
    :param chrom_sizes: Chromosome sizes defining the counting reference.
    :param output: BED-like output with an appended score.
    :param weighting: NH fractional counting, or explicit primary-alignment counting.
    :param normalization: Read-end RPM, or read-end RPM divided by peak length in kb.
    """
    if normalization not in ("RPM", "RPKM"):
        raise ValueError(f"Unknown normalization: {normalization}")
    sizes = chromosome_sizes(chrom_sizes)
    regions = read_regions(bed, sizes)
    if not regions:
        write_scores([], [], output)
        return
    with tempfile.TemporaryDirectory(prefix="genesis-rpm-") as temporary:
        work = Path(temporary)
        values = work / "alignments.bed"
        peaks = work / "peaks.bed"
        denominator = weighted_alignments(bam, sizes, values, weighting)
        if denominator == 0:
            raise ValueError("Cannot normalize peaks: no retained mapped read ends")
        indexed_regions(regions, peaks)
        counts = interval_sums(values, peaks, len(regions), length_weighted=False)
    scores = [count * 1_000_000 / denominator for count in counts]
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
    if not regions:
        write_scores([], [], output)
        return
    with tempfile.TemporaryDirectory(prefix="genesis-rpkm-") as temporary:
        peaks = Path(temporary) / "peaks.bed"
        indexed_regions(regions, peaks)
        sums = interval_sums(coverage, peaks, len(regions), length_weighted=True)
    scores = [
        total / (region.end - region.start) for region, total in zip(regions, sums, strict=True)
    ]
    write_scores(regions, scores, output)


def alignment_lines(path: Path) -> Iterator[str]:
    """Read exported SAM directly, or stream a BAM through managed samtools."""
    if path.suffix == ".sam":
        with path.open() as stream:
            for line in stream:
                if line.startswith(("@HD\t", "@SQ\t", "@RG\t", "@PG\t", "@CO\t")):
                    continue
                yield line
    else:
        yield from command_lines(["samtools", "view", str(path)])


def prepare_quantification(
    *,
    bed: Path,
    sam: Path,
    chrom_sizes: Path,
    output_dir: Path,
    weighting: Literal["NH", "primary"] = "NH",
) -> None:
    """Prepare weighted BEDs and original peak rows without external tools.

    :param bed: Original compressed or plain BED/narrowPeak.
    :param sam: SAM exported by the alignment environment.
    :param chrom_sizes: Chromosome sizes.
    :param output_dir: Directory for alignments.bed, indexed_peaks.bed, and quantification.json.
    :param weighting: NH fractional weighting or primary read-end counting.
    """
    if sam.suffix != ".sam":
        raise ValueError("Preparation requires an exported .sam file")
    sizes = chromosome_sizes(chrom_sizes)
    regions = read_regions(bed, sizes)
    output_dir.mkdir(parents=True, exist_ok=True)
    denominator = weighted_alignments(sam, sizes, output_dir / "alignments.bed", weighting)
    indexed_regions(regions, output_dir / "indexed_peaks.bed")
    details = {"denominator": denominator, "regions": [list(region.fields) for region in regions]}
    (output_dir / "quantification.json").write_text(json.dumps(details) + "\n")


def read_details(path: Path) -> tuple[list[Region], float]:
    """Validate the preparation artifact and restore original BED fields."""
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError("Quantification details must be an object")
    denominator = payload.get("denominator")
    if (
        not isinstance(denominator, (int, float))
        or isinstance(denominator, bool)
        or not math.isfinite(denominator)
        or denominator < 0
    ):
        raise ValueError("Invalid read-end denominator")
    rows = payload.get("regions")
    if not isinstance(rows, list):
        raise ValueError("Quantification details require regions")
    regions: list[Region] = []
    for row in rows:
        if not isinstance(row, list) or len(row) < 3:
            raise ValueError("Expected at least three BED fields")
        fields: list[str] = []
        for value in row:
            if not isinstance(value, str):
                raise ValueError("BED fields must be strings")
            fields.append(value)
        start, end = int(fields[1]), int(fields[2])
        if start < 0 or end <= start:
            raise ValueError("Invalid BED interval")
        regions.append(Region(tuple(fields), fields[0], start, end))
    return regions, float(denominator)


def finish_quantification(
    *,
    details: Path,
    read_overlaps: Path,
    coverage_overlaps: Path,
    rpm_output: Path,
    rpkm_output: Path,
) -> None:
    """Append RPM and mean coverage RPKM using exported intersection files.

    :param details: Validated quantification.json from preparation.
    :param read_overlaps: Weighted read/peak intersections from bedtools.
    :param coverage_overlaps: RPKM bedGraph/peak intersections from bedtools.
    :param rpm_output: Original BED rows with appended read-end RPM.
    :param rpkm_output: Original BED rows with appended mean coverage RPKM.
    """
    regions, denominator = read_details(details)
    if regions and denominator == 0:
        raise ValueError("Cannot normalize peaks: no retained mapped read ends")
    with read_overlaps.open() as stream:
        counts = overlap_sums(stream, len(regions), length_weighted=False)
    with coverage_overlaps.open() as stream:
        totals = overlap_sums(stream, len(regions), length_weighted=True)
    rpm = [count * 1_000_000 / denominator for count in counts]
    rpkm = [
        total / (region.end - region.start) for region, total in zip(regions, totals, strict=True)
    ]
    write_scores(regions, rpm, rpm_output)
    write_scores(regions, rpkm, rpkm_output)
