import json
import sys
from collections import defaultdict
from pathlib import Path

from metrics import overlap, tss_profile

fragments = json.loads(Path(sys.argv[1]).read_text())
regions = defaultdict(list)
for line in Path(sys.argv[2]).read_text().splitlines():
    row = line.split("\t")
    regions[row[0]].append((int(row[1]), int(row[2])))
tss = []
for line in Path(sys.argv[3]).read_text().splitlines():
    chrom, pos, strand = line.split("\t")
    tss.append((chrom, int(pos), strand))
in_peaks = sum(overlap(f["start"], f["end"], regions[f["chrom"]]) for f in fragments)
report = {
    "usable_fragments": len(fragments),
    "peak_count": sum(map(len, regions.values())),
    "fragments_in_peaks": in_peaks,
    "FRiP": in_peaks / len(fragments) if fragments else None,
    "tss": tss_profile(fragments, tss),
    "plant_thresholds": "UNSPECIFIED",
    "interpretation": "synthetic computational fixture; not biological ATAC quality",
}
Path("enrichment.json").write_text(json.dumps(report, indent=2) + "\n")
