"""Read-only, bounded-memory inspection of downloaded five-column author fragments."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import resource
import time
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    started = time.monotonic()
    with args.source.open("rb") as stream:
        checksum = hashlib.file_digest(stream, "sha256").hexdigest()
    counts = Counter()
    maxima = {}
    previous = None
    duplicate_adjacent = 0
    with gzip.open(args.source, "rt") as stream:
        for line in stream:
            if line.startswith("#"):
                continue
            chrom, start, end, barcode, support = line.rstrip().split("\t")
            start, end, support = int(start), int(end), int(support)
            if start < 0 or end <= start or support < 1 or not barcode:
                raise ValueError("Invalid author fragment")
            identity = (chrom, start, end, barcode)
            duplicate_adjacent += identity == previous
            previous = identity
            counts[chrom] += 1
            counts["total_fragments"] += 1
            counts["total_support"] += support
            maxima[chrom] = max(maxima.get(chrom, 0), end)
    result = {
        "input": str(args.source),
        "sha256": checksum,
        "counts": dict(counts),
        "max_fragment_end": maxima,
        "adjacent_duplicate_rows": duplicate_adjacent,
        "duplicate_check_scope": "Adjacent only; not a full uniqueness proof",
        "elapsed_seconds": time.monotonic() - started,
        "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
