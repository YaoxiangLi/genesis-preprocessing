"""Bounded PE ATAC prototype metrics; no DAP-seq production integration."""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import NotRequired, TypedDict

import pysam


class Fragment(TypedDict):
    chrom: str
    start: int
    end: int
    name: NotRequired[str]


def overlap(start: int, end: int, regions: list[tuple[int, int]]) -> bool:
    return any(start < stop and end > begin for begin, stop in regions)


def cuts(start: int, end: int) -> tuple[int, int]:
    # This prototype records ENCODE tagAlign-style +4/-5 intervals explicitly.
    return start + 4, end - 5 - 1


def tss_profile(
    fragments: list[Fragment],
    tss: list[tuple[str, int, str]],
    radius: int = 100,
    center: int = 10,
    flank: int = 20,
) -> dict[str, object]:
    counts = [0] * (2 * radius + 1)
    for chrom, pos, strand in tss:
        for frag in fragments:
            if frag["chrom"] != chrom:
                continue
            for cut in cuts(frag["start"], frag["end"]):
                relative = (cut - pos) * (1 if strand == "+" else -1)
                if -radius <= relative <= radius:
                    counts[relative + radius] += 1
    background = sum(counts[:flank] + counts[-flank:]) / (2 * flank)
    signal = sum(counts[radius - center : radius + center + 1]) / (2 * center + 1)
    return {
        "radius": radius,
        "center_half_width": center,
        "flank_width": flank,
        "counts": counts,
        "background": background,
        "enrichment": signal / background if background else None,
        "zero_background": background == 0,
    }


def select(
    records: list[pysam.AlignedSegment],
    min_mapq: int,
    organelles: set[str],
    exclude_duplicates: bool = True,
) -> tuple[list[pysam.AlignedSegment], list[Fragment], dict[str, object]]:
    """Evaluate both mates; never retain an orphan after asymmetric MAPQ filtering."""
    by_name = defaultdict(list)
    for read in records:
        if not read.is_secondary and not read.is_supplementary:
            by_name[read.query_name].append(read)
    counts = Counter(total_query_groups=len(by_name))
    chosen = []
    fragments = []
    positions = Counter()
    for name, mates in sorted(by_name.items()):
        if (
            len(mates) != 2
            or sum(r.is_read1 for r in mates) != 1
            or sum(r.is_read2 for r in mates) != 1
        ):
            counts["invalid_pair"] += 1
            continue
        if (
            any(
                r.is_unmapped or r.mate_is_unmapped or not r.is_proper_pair or r.is_qcfail
                for r in mates
            )
            or mates[0].reference_id != mates[1].reference_id
        ):
            counts["unusable_pair"] += 1
            continue
        counts["mapped_proper_pairs"] += 1
        if any(r.mapping_quality < min_mapq for r in mates):
            counts["low_mapq_pairs"] += 1
            continue
        chrom = mates[0].reference_name
        if chrom in organelles:
            counts["organellar_pairs"] += 1
            continue
        start = min(r.reference_start for r in mates)
        end = max(r.reference_end for r in mates)
        positions[(chrom, start, end)] += 1
        counts["eligible_before_dedup"] += 1
        if any(r.is_duplicate for r in mates):
            counts["duplicate_pairs"] += 1
            if exclude_duplicates:
                continue
        left, right = cuts(start, end)
        if right < left:
            counts["invalid_shifted_span"] += 1
            continue
        chosen.extend(mates)
        fragments.append({"chrom": chrom, "start": start, "end": end, "name": name})
    counts["usable_fragments"] = len(fragments)
    total = sum(positions.values())
    distinct = len(positions)
    singleton = sum(v == 1 for v in positions.values())
    doubleton = sum(v == 2 for v in positions.values())
    summary = {
        "counts": dict(counts),
        "NRF": distinct / total if total else None,
        "PBC1": singleton / distinct if distinct else None,
        "PBC2": singleton / doubleton if doubleton else None,
        "duplicate_fraction": counts["duplicate_pairs"] / total if total else None,
        "mapq_policy": min_mapq,
        "organellar_contigs": sorted(organelles),
        "duplicate_policy": "exclude_marked" if exclude_duplicates else "retain_marked",
        "coordinate_offsets": [4, -5],
        "plant_thresholds": "UNSPECIFIED",
        "fragment_lengths": dict(sorted(Counter(f["end"] - f["start"] for f in fragments).items())),
    }
    return chosen, fragments, summary


def run(args: argparse.Namespace) -> None:
    with pysam.AlignmentFile(args.bam, "rb") as source:
        reads = list(source)
        chosen, fragments, summary = select(
            reads, args.mapq, set(args.organelles.split(",")) - {""}
        )
        with pysam.AlignmentFile("unsorted.bam", "wb", header=source.header) as output:
            for read in chosen:
                output.write(read)
    pysam.sort("-o", "usable.bam", "unsorted.bam")
    pysam.index("usable.bam")
    Path("unsorted.bam").unlink()
    Path("fragments.json").write_text(json.dumps(fragments, sort_keys=True) + "\n")
    with Path("fragments.bed").open("w") as output:
        for f in sorted(fragments, key=lambda f: (f["chrom"], f["start"], f["end"], f["name"])):
            output.write(f"{f['chrom']}\t{f['start']}\t{f['end']}\t{f['name']}\n")
    signals = Counter((f["chrom"], cut) for f in fragments for cut in cuts(f["start"], f["end"]))
    Path("cuts.bedgraph").write_text(
        "".join(
            f"{chrom}\t{pos}\t{pos + 1}\t{count}\n"
            for (chrom, pos), count in sorted(signals.items())
        )
    )
    summary["bam_sha256"] = hashlib.sha256(Path(args.bam).read_bytes()).hexdigest()
    summary["pysam_version"] = pysam.__version__
    Path("metrics.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    for command, filename in [
        (pysam.flagstat, "usable.flagstat.txt"),
        (pysam.stats, "usable.stats.txt"),
        (pysam.idxstats, "usable.idxstats.txt"),
    ]:
        Path(filename).write_text(command("usable.bam"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bam", required=True)
    parser.add_argument("--mapq", required=True, type=int)
    parser.add_argument("--organelles", default="")
    run(parser.parse_args())
