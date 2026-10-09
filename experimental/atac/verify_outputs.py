"""Inspect the actual published fixture contract, not only task exit codes."""

import json
import sys
from collections import Counter
from pathlib import Path

output = Path(sys.argv[1])
expected_organelles = sys.argv[2:]
fragments = json.loads((output / "fragments/fragments.json").read_text())
metrics = json.loads((output / "fragments/metrics.json").read_text())
provenance = json.loads((output / "provenance.json").read_text())
bed = [line.split("\t") for line in (output / "fragments/fragments.bed").read_text().splitlines()]
assert len(bed) == len(fragments) == metrics["counts"]["usable_fragments"]
assert [(r[0], int(r[1]), int(r[2]), r[3]) for r in bed] == sorted(
    (f["chrom"], f["start"], f["end"], f["name"]) for f in fragments
)
expected = Counter((f["chrom"], cut) for f in fragments for cut in (f["start"] + 4, f["end"] - 6))
observed = {}
for line in (output / "fragments/cuts.bedgraph").read_text().splitlines():
    chrom, start, end, count = line.split("\t")
    assert int(end) == int(start) + 1
    assert (chrom, int(start)) not in observed
    observed[(chrom, int(start))] = int(count)
assert observed == expected
assert sum(observed.values()) == 2 * len(fragments)
assert provenance["organelles"] == metrics["organellar_contigs"] == expected_organelles
assert provenance["plant_thresholds"] == "UNSPECIFIED"
assert len(list((output / "fastqc").glob("*_fastqc.zip"))) == 2
assert len(list((output / "fastqc").glob("*_fastqc.html"))) == 2
required = json.loads((output / "multiqc/required-modules.json").read_text())
assert all(count == 2 for count in required["sample_counts"].values())
assert (output / "peaks/atac_peaks.narrowPeak").stat().st_size > 0
assert not list(output.rglob("*.bam")) and not list(output.rglob("*.fastq.gz"))
print(
    json.dumps(
        {
            "PASS": True,
            "fragments": len(bed),
            "cuts": sum(observed.values()),
            "organelles": expected_organelles,
            "raw_reads_or_bams_published": False,
        }
    )
)
