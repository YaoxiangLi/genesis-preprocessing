"""Explicit cut-based TSS measurements without universal biological thresholds."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..benchmark.metrics import Regions
from .common import bounded_lines, checked_asset, text_file


def tss_profile(cuts: Path, source: dict[str, Any], sizes: dict[str, int]) -> dict[str, Any]:
    tss_file = checked_asset(source, cuts.parent)
    points = []
    seen = set()
    edge = duplicate = 0
    with text_file(tss_file) as stream:
        for line in bounded_lines(stream):
            if line.startswith("#") or not line.strip():
                continue
            fields = line.rstrip().split("\t")
            if len(fields) != 3:
                raise ValueError("TSS input requires contig, BED0 point, and strand")
            chrom, position, strand = fields
            pos = int(position)
            if chrom not in sizes or not 0 <= pos < sizes[chrom] or strand not in {"+", "-"}:
                raise ValueError("TSS is inconsistent with the reference dictionary")
            key = (chrom, pos, strand)
            if key in seen:
                duplicate += 1
                continue
            seen.add(key)
            if pos < 2000 or pos + 2000 >= sizes[chrom]:
                edge += 1
            else:
                points.append(key)
    windows = Regions([(chrom, pos - 2000, pos + 2001) for chrom, pos, _ in points])
    profile = [0] * 4001
    with cuts.open() as stream:
        for line in bounded_lines(stream):
            chrom, left, right, value = line.rstrip().split("\t")
            start, end, count = int(left), int(right), int(value)
            if chrom not in sizes or not 0 <= start < end <= sizes[chrom] or count < 0:
                raise ValueError("Invalid raw cut-count interval")
            for i in windows.hits(chrom, start, end):
                _, pos, strand = points[i]
                for cut in range(max(start, pos - 2000), min(end, pos + 2001)):
                    offset = cut - pos if strand == "+" else pos - cut
                    profile[offset + 2000] += count
    background = (sum(profile[:100]) + sum(profile[-100:])) / 200
    value = profile[2000] / background if points and background else None
    return {
        "tss_enrichment": value,
        "tss_status": "MEASURED" if value is not None else "NO_FULL_WINDOWS_OR_ZERO_FLANKS",
        "tss_definition": (
            "Declared raw cuts; strand-oriented +/-2000 bp; center base / mean 100 bp flanks"
        ),
        "tss_sha256": source["sha256"],
        "usable_tss": len(points),
        "edge_excluded_tss": edge,
        "duplicate_tss_coordinates": duplicate,
        "tss_flank_mean": background,
        "tss_profile": profile,
        "plant_thresholds": "UNSPECIFIED",
    }
