"""Independently computable fragments and cut-site fixture."""

import json

import pysam
from metrics import cuts, overlap, select, tss_profile

header = pysam.AlignmentHeader.from_dict(
    {"HD": {"VN": "1.6"}, "SQ": [{"SN": "chr1", "LN": 1000}, {"SN": "plastid", "LN": 1000}]}
)


def pair(
    name: str,
    start: int = 100,
    chrom: int = 0,
    mapqs: tuple[int, int] = (60, 60),
    dup: bool = False,
) -> list[pysam.AlignedSegment]:
    result = []
    for mate in (0, 1):
        read = pysam.AlignedSegment(header)
        read.query_name = name
        read.flag = (99 if mate == 0 else 147) + (1024 if dup else 0)
        read.reference_id = chrom
        read.reference_start = start + mate * 50
        read.mapping_quality = mapqs[mate]
        read.cigarstring = "50M"
        read.query_sequence = "A" * 50
        read.next_reference_id = chrom
        read.next_reference_start = start + (1 - mate) * 50
        read.template_length = 100 if mate == 0 else -100
        result.append(read)
    return result


reads = (
    pair("one")
    + pair("dup", dup=True)
    + pair("two", start=300)
    + pair("low", mapqs=(60, 10))
    + pair("plastid", chrom=1)
)
chosen, frags, summary = select(reads, 30, {"plastid"})
assert len(chosen) == 4 and len(frags) == 2
assert summary["counts"]["low_mapq_pairs"] == 1 and summary["counts"]["organellar_pairs"] == 1
assert summary["counts"]["duplicate_pairs"] == 1 and summary["duplicate_fraction"] == 1 / 3
assert summary["NRF"] == 2 / 3 and summary["PBC1"] == 1 / 2 and summary["PBC2"] == 1
assert cuts(100, 200) == (104, 194)
assert sum(overlap(f["start"], f["end"], [(150, 160)]) for f in frags) / len(frags) == 0.5
assert not overlap(100, 200, [(200, 201)])
assert select(list(reversed(reads)), 30, {"plastid"})[1:] == (frags, summary)
profile = tss_profile([{"chrom": "chr1", "start": 100, "end": 200}], [("chr1", 104, "+")])
assert profile["counts"][100] == 1 and profile["counts"][190] == 1
assert profile["enrichment"] == 40 / 21
negative = tss_profile([{"chrom": "chr1", "start": 100, "end": 200}], [("chr1", 194, "-")])
assert negative["counts"] == profile["counts"]
assert tss_profile([], [("chr1", 100, "+")])["enrichment"] is None
print(
    json.dumps(
        {
            "PASS": [
                "both-mate MAPQ",
                "organellar accounting",
                "duplicate flag policy",
                "NRF/PBC",
                "Tn5 endpoints",
                "FRiP=0.5",
                "half-open overlap",
                "permutation invariance",
                "TSS=40/21",
                "strand orientation",
                "zero background null",
            ]
        },
        indent=2,
    )
)
