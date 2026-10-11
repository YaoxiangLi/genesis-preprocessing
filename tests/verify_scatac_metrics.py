"""Hand-computable TSS profiles, FRiP denominators and bounded GC matching."""

from __future__ import annotations

import copy
import tempfile
from pathlib import Path
from typing import Any

import pysam
from genesis_tools.scatac import backgrounds, compare, products, qc
from genesis_tools.scatac.common import complete, digest, verify_output
from verify_scatac_exports import rejects


def main() -> None:
    tiles = {"background_method": "gc-matched-genome-tiles-v1"}
    windows = {"background_method": "gc-matched-genome-windows-v1", "background_stride": 1000}
    assert backgrounds.candidate_stride(tiles, 1057) == 2114
    assert backgrounds.candidate_stride(windows, 1057) == 1000
    for value in (None, 0, -1, 1.5, True):
        rejects(backgrounds.candidate_stride, {**windows, "background_stride": value}, 1057)
    rejects(backgrounds.candidate_stride, {**tiles, "background_stride": 1000}, 1057)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        tss = root / "tss.tsv"
        tss.write_text("chr1\t3000\t+\nchr1\t3000\t+\nchr2\t3000\t-\nchr1\t3\t+\n")
        cuts = root / "cuts.bedGraph"
        cuts.write_text(
            "chr1\t1000\t1100\t1\nchr1\t3000\t3001\t10\nchr1\t4901\t5001\t1\n"
            "chr2\t1000\t1100\t2\nchr2\t3000\t3001\t20\nchr2\t4901\t5001\t2\n"
        )
        result = qc.tss_profile(
            cuts, {"path": str(tss), "sha256": digest(tss)}, {"chr1": 7000, "chr2": 7000}
        )
        assert result["tss_enrichment"] == 10
        assert result["usable_tss"] == 2
        assert result["edge_excluded_tss"] == result["duplicate_tss_coordinates"] == 1
        assert result["tss_profile"][2000] == 30
        cuts.write_text("chr1\t3000\t3001\t10\n")
        assert (
            qc.tss_profile(
                cuts, {"path": str(tss), "sha256": digest(tss)}, {"chr1": 7000, "chr2": 7000}
            )["tss_enrichment"]
            is None
        )
        fragments, peaks = root / "fragments.tsv", root / "peaks.bed"
        fragments.write_text("chr1\t0\t10\tA\t4\nchr1\t10\t20\tA\t1\nchr1\t30\t40\tA\t1\n")
        peaks.write_text("chr1\t5\t15\tx\t0\t.\t1\t1\t1\t5\nchr1\t6\t14\ty\t0\t.\t1\t1\t1\t5\n")
        result = products.frip(fragments, peaks, {"chr1": 100})
        assert result["frip"] == 2 / 3
        assert result["total_support"] == 6
        assert result["support_redundancy_fraction"] == 0.5
        assert result["fragment_lengths"] == {"10": 3}
        assert result["peak_widths"] == {"8": 1, "10": 1}
        # Widths 8 and 10 sort differently as integers and JSON string keys.
        # A freshly published real QC distribution must verify after reload.
        roundtrip = root / "qc-roundtrip"
        roundtrip.mkdir()
        recorded = complete(roundtrip, "scatac-qc-test", {"qc": result}, 0)
        assert verify_output(roundtrip, "scatac-qc-test")["version"] == recorded["version"]
        fasta = root / "genome.fa"
        fasta.write_text(">chr1\n" + "A" * 200 + "G" * 200 + "A" * 200 + "G" * 200 + "\n")
        pysam.faidx(str(fasta))

        def row(center: int) -> str:
            return f"chr1\t{center - 1}\t{center + 1}\tx\t0\t.\t0\t0\t0\t1"

        positive = {"train": [row(100), row(300)]}
        candidate = {"train": [row(500), row(700)]}
        matched, report = backgrounds.match(fasta, positive, candidate, 100, 7)
        assert matched == candidate
        assert report["folds"]["train"]["gc_percentage_point_differences"] == {0: 2}
        assert backgrounds.match(fasta, positive, candidate, 100, 7) == (matched, report)
        rejects(backgrounds.match, fasta, positive, {"train": [row(500)]}, 100, 7)
        ordered = {"train": [row(100)], "test": [row(100)]}
        pools = {split: [row(center) for center in range(50, 151, 10)] for split in ordered}
        expected = backgrounds.match(fasta, ordered, pools, 100, 7)
        reversed_folds = dict(reversed(list(ordered.items())))
        assert backgrounds.match(fasta, reversed_folds, pools, 100, 7) == expected
        data: dict[str, Any] = {
            "group": {
                "identity": {"study_id": "toy", "biological_replicate_id": "r1", "cell_type": "A"},
                "reference": {"contigs": {"chr1": 400}},
            },
            "policy": {},
        }
        for name, rep, signal, peak in (("one", "r1", "1", "0\t10"), ("two", "r2", "2", "5\t15")):
            directory = root / name
            directory.mkdir()
            value = copy.deepcopy(data)
            value["group"]["identity"]["biological_replicate_id"] = rep
            (directory / "cuts.bedGraph").write_text(f"chr1\t0\t10\t{signal}\n")
            (directory / "peaks_peaks.narrowPeak").write_text(
                f"chr1\t{peak}\tx\t0\t.\t1\t1\t1\t1\n"
            )
            complete(directory, "scatac-group", value, 0)
        concordance = compare.run(root / "one", root / "two", 100)
        assert concordance["pearson_all_bins"] == 1.0
        assert concordance["peak_base_jaccard"] == 1 / 3
        assert concordance["pearson_nonzero_union"] is None
        rejects(compare.run, root / "one", root / "one", 100)
    print(
        "PASS: known-answer TSS/FRiP/support denominators and deterministic bounded GC backgrounds"
    )


if __name__ == "__main__":
    main()
