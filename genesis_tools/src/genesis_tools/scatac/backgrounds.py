"""Deterministic within-fold GC matching on explicitly spaced genomic windows."""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pysam


def candidate_stride(config: dict[str, Any], radius: int) -> int:
    """Keep disjoint tiles unchanged; require an explicit stride for window sampling."""
    method = config.get("background_method")
    if method not in {
        "nonoverlapping-genome-tiles-v1",
        "gc-matched-genome-tiles-v1",
        "gc-matched-genome-windows-v1",
    }:
        raise ValueError("Select a declared background method")
    stride = config.get("background_stride")
    if method != "gc-matched-genome-windows-v1":
        if stride is not None:
            raise ValueError("A background stride requires the explicit window method")
        return 2 * radius
    if type(stride) is not int or stride < 1:
        raise ValueError("Background windows require an explicit positive integer stride")
    return stride


def match(
    fasta: Path,
    positives: dict[str, list[str]],
    candidates: dict[str, list[str]],
    window: int,
    seed: int,
) -> tuple[dict[str, list[str]], dict[str, Any]]:
    if type(seed) is not int:
        raise ValueError("GC matching requires an explicit integer seed")
    rng = random.Random(seed)
    result = {}
    summaries = {}
    with pysam.FastaFile(str(fasta)) as reference:

        def gc(row: str) -> tuple[int, bool]:
            fields = row.split("\t")
            center = int(fields[1]) + int(fields[9])
            seq = reference.fetch(fields[0], center - window // 2, center + window // 2).upper()
            if len(seq) != window:
                raise ValueError("Truncated GC sequence window")
            return round(100 * (seq.count("G") + seq.count("C")) / window), bool(
                set(seq) - set("ACGT")
            )

        for split, peaks in positives.items():
            pools: dict[int, list[str]] = defaultdict(list)
            excluded = 0
            for row in candidates[split]:
                bucket, ambiguous = gc(row)
                excluded += ambiguous
                pools[bucket].append(row)
            for pool in pools.values():
                rng.shuffle(pool)
            if sum(map(len, pools.values())) < len(peaks):
                raise ValueError("Insufficient nonpeak tiles for one background per peak")
            matched = []
            deviations: Counter[int] = Counter()
            unknown_positive = 0
            for row in peaks:
                bucket, ambiguous = gc(row)
                unknown_positive += ambiguous
                available = [key for key, pool in pools.items() if pool]
                chosen = min(available, key=lambda key: (abs(key - bucket), key))
                matched.append(pools[chosen].pop())
                deviations[chosen - bucket] += 1
            result[split] = matched
            summaries[split] = {
                "requested": len(peaks),
                "selected": len(matched),
                "retained_ambiguous_candidates": excluded,
                "retained_ambiguous_positives": unknown_positive,
                "gc_percentage_point_differences": dict(sorted(deviations.items())),
            }
    return result, {
        "method": "gc-matched-genome-tiles-v1",
        "seed": seed,
        "definition": (
            "1% GC bins; nearest available bin within fold, lower-bin ties; without replacement"
        ),
        "ambiguous_sequence": "Retained; G+C / full window length, as in pinned ChromBPNet helper",
        "folds": summaries,
    }
