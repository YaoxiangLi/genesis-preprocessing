"""Independently check paired fragments, organelles, MAPQ and shifted cut sites."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import tempfile
from pathlib import Path

import pysam
from genesis_tools.atac.fragments import select
from genesis_tools.atac.inputs import identifier
from genesis_tools.atac.stages import acquire


def check_acquisition(root: Path) -> None:
    previous = Path.cwd()
    try:
        for name, contents in {
            "valid": [b"@read/1\nACGT\n+\nIIII\n", b"@read/2\nACGT\n+\nIIII\n"],
            "empty": [b"", b""],
            "truncated": [b"@read/1\nACGT\n+\nIIII\n", b"@read/2\nACGT\n+\n"],
            "corrupt": [b"not gzip", b"not gzip"],
        }.items():
            folder = root / name
            folder.mkdir()
            paths = [folder / "source1.gz", folder / "source2.gz"]
            for path, content in zip(paths, contents, strict=True):
                path.write_bytes(content if name == "corrupt" else gzip.compress(content, mtime=0))
            before = [p.read_bytes() for p in paths]
            lane = {"lane_id": "one"}
            for mate, path in zip(("read1", "read2"), paths, strict=True):
                lane[mate] = str(path)
                lane[mate + "_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            os.chdir(folder)
            try:
                acquire({"lanes": [lane]})
            except ValueError, OSError, EOFError:
                assert name != "valid"
            else:
                assert name == "valid", name
                assert (folder / "raw_R1.fastq.gz").read_bytes() == before[0]
                assert (folder / "raw_R2.fastq.gz").read_bytes() == before[1]
            assert before == [p.read_bytes() for p in paths]
    finally:
        os.chdir(previous)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="genesis-fragments-") as temporary:
        root = Path(temporary)
        check_acquisition(root)
        sam = root / "input.sam"
        lines = [
            "@HD\tVN:1.6\tSO:unsorted",
            "@SQ\tSN:nuclear\tLN:10000",
            "@SQ\tSN:mito\tLN:10000",
            "@SQ\tSN:plastid\tLN:10000",
        ]
        for name, chrom, mapq, duplicate, start in [
            ("good", "nuclear", 60, 0, 101),
            ("duplicate", "nuclear", 60, 1024, 101),
            ("low", "nuclear", 0, 0, 201),
            ("unknown", "nuclear", 255, 0, 301),
            ("mito", "mito", 60, 0, 401),
            ("plastid", "plastid", 60, 0, 501),
        ]:
            for flag, pos, mate, span in [
                (99, start, start + 100, 150),
                (147, start + 100, start, -150),
            ]:
                lines.append(
                    f"{name}\t{flag + duplicate}\t{chrom}\t{pos}\t{mapq}\t50M\t=\t{mate}\t{span}\t"
                    + "A" * 50
                    + "\t"
                    + "I" * 50
                )
        sam.write_text("\n".join(lines) + "\n")
        bam = root / "input.bam"
        with (
            pysam.AlignmentFile(str(sam)) as source,
            pysam.AlignmentFile(str(bam), "wb", template=source) as target,
        ):
            for read in source:
                target.write(read)
        policy = {
            "mapq": 30,
            "duplicates": "exclude",
            "reference": {
                "mitochondrial_contigs": ["mito"],
                "plastid_contigs": ["plastid"],
            },
        }
        result = select(bam, policy, root / "exclude")
        counts = result["counts"]
        assert counts["total_templates"] == 6
        assert counts["usable_fragments"] == 1
        assert counts["low_or_unknown_mapq_pairs"] == 2
        assert counts["raw_mitochondrial_pairs"] == counts["raw_plastid_pairs"] == 1
        assert result["duplicate_fraction"] == 0.5
        assert result["NRF"] == 0.5 and result["PBC1"] == 0 and result["PBC2"] == 0
        assert (root / "exclude/fragments.unsorted.bed").read_text() == "nuclear\t100\t250\tgood\n"
        assert (
            root / "exclude/cuts.unsorted.bed"
        ).read_text() == "nuclear\t104\t105\nnuclear\t244\t245\n"
        result = select(bam, {**policy, "duplicates": "retain", "mapq": 0}, root / "retain")
        assert result["counts"]["usable_fragments"] == 3
        assert (
            json.loads((root / "retain/metrics.json").read_text())["plant_thresholds"]
            == "UNSPECIFIED"
        )
        for value in ["..", "../escape", "a\nb", "a b"]:
            try:
                identifier(value)
            except ValueError:
                pass
            else:
                raise AssertionError("Unsafe identifier accepted")
    print("PASS: known-answer paired ATAC filtering and cut-site coordinates")


if __name__ == "__main__":
    main()
