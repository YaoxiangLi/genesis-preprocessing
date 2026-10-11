"""Replicate concordance on shared genomic bins without pooling molecules."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from ..benchmark.metrics import correlation, intersection, intervals, merged
from .common import verify_output


def bins(path: Path, sizes: dict[str, int], width: int) -> dict[tuple[str, int], float]:
    result = {}
    with path.open() as stream:
        for line in stream:
            chrom, left, right, value = line.split()
            start, end, count = int(left), int(right), float(value)
            if (
                chrom not in sizes
                or not 0 <= start < end <= sizes[chrom]
                or not math.isfinite(count)
                or count < 0
            ):
                raise ValueError("Invalid cut-count interval")
            for index in range(start // width, (end - 1) // width + 1):
                key = (chrom, index)
                result[key] = result.get(key, 0) + count * (
                    min(end, (index + 1) * width) - max(start, index * width)
                )
    return result


def run(left: Path, right: Path, width: int = 1000) -> dict[str, Any]:
    if type(width) is not int or width < 1:
        raise ValueError("Positive integer bin width required")
    a, b = (verify_output(p, "scatac-group") for p in (left, right))
    x, y = a["data"]["group"], b["data"]["group"]
    omit = {"biological_sample_id", "biological_replicate_id", "library_scope"}
    if (
        {k: v for k, v in x["identity"].items() if k not in omit}
        != {k: v for k, v in y["identity"].items() if k not in omit}
        or x["reference"] != y["reference"]
        or a["data"]["policy"] != b["data"]["policy"]
    ):
        raise ValueError("Compare the same cell type, reference, context and processing policy")
    if x["identity"]["biological_replicate_id"] == y["identity"]["biological_replicate_id"]:
        raise ValueError("Replicate concordance requires distinct biological replicates")
    sizes = x["reference"]["contigs"]
    n = sum((length + width - 1) // width for length in sizes.values())
    if n > 1_000_000:
        raise ValueError("More than one million bins; choose a larger explicit bin width")
    counts = [bins(p / "cuts.bedGraph", sizes, width) for p in (left, right)]
    vectors = [
        [
            values.get((c, i), 0.0)
            for c, length in sizes.items()
            for i in range((length + width - 1) // width)
        ]
        for values in counts
    ]
    active = [i for i, (u, v) in enumerate(zip(*vectors, strict=True)) if u or v]
    peaks = [intervals(p / "peaks_peaks.narrowPeak")[0] for p in (left, right)]
    shared = intersection(*peaks)
    union = sum(e - s for _, s, e in merged(peaks[0] + peaks[1]))
    return {
        "schema_version": 1,
        "parents": [a["version"], b["version"]],
        "biological_replicates": [g["identity"]["biological_replicate_id"] for g in (x, y)],
        "cell_type": x["identity"]["cell_type"],
        "bin_width": width,
        "bins": n,
        "nonzero_union_bins": len(active),
        "pearson_all_bins": correlation(*vectors),
        "spearman_all_bins": correlation(*vectors, rank=True),
        "pearson_nonzero_union": correlation(*[[v[i] for i in active] for v in vectors]),
        "spearman_nonzero_union": correlation(
            *[[v[i] for i in active] for v in vectors], rank=True
        ),
        "peak_base_jaccard": shared / union if union else None,
        "peak_intersection_bases": shared,
        "peak_union_bases": union,
        "definition": "Raw cut-count sums in identical BED0 bins; include partial terminal bins",
        "null_reason": "Fewer than two observations, constant vector or empty peak union",
        "plant_thresholds": "UNSPECIFIED",
    }
