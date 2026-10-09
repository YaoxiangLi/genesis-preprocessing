"""Real-tool two-library ATAC regression with an unchanged second resume."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import shutil
import tempfile
from pathlib import Path

from genesis_tools.atac.inputs import FIELDS, digest
from genesis_tools.atac.run import execute, prepare
from genesis_tools.benchmark.fixture import create

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args()
    base = ROOT / "tests/.runs"
    base.mkdir(exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix="supported-atac-", dir=base))
    print(f"ATAC regression evidence: {folder}", flush=True)
    fixture = folder / "fixture"
    create(fixture, assay="bulk-ATAC")
    ref = {
        "reference_id": "toy",
        "species": "synthetic",
        "assembly": "synthetic-v1",
        "annotation_release": "synthetic-v1",
        "genome_size": 2002000,
        "genome_size_method": "synthetic total bases",
        "fasta": str(fixture / "reference.fa.gz"),
        "fasta_sha256": digest(fixture / "reference.fa.gz"),
        "tss": str(fixture / "tss.bed"),
        "tss_sha256": digest(fixture / "tss.bed"),
        "mitochondrial_contigs": ["mitochondria"],
        "plastid_contigs": ["plastid"],
    }
    registry = folder / "references.json"
    registry.write_text(json.dumps({"schema_version": 1, "references": [ref]}))
    # Divide a library into technical lanes; both use the same basenames in different folders.
    for mate in (1, 2):
        with gzip.open(fixture / f"pe_treatment.R{mate}.fastq.gz", "rt") as source:
            for lane in (1, 2):
                target = fixture / f"lane{lane}"
                target.mkdir(exist_ok=True)
                with gzip.open(target / f"R{mate}.fastq.gz", "wt") as output:
                    for _ in range(16000):
                        for _ in range(4):
                            output.write(source.readline())
    sheet = folder / "samples.tsv"
    rows = []
    for library, rep in [("first", "1"), ("second", "2")]:
        for lane in (1, 2):
            r1, r2 = [fixture / f"lane{lane}/R{mate}.fastq.gz" for mate in (1, 2)]
            rows.append(
                {
                    "library_id": library,
                    "sample_id": "plant",
                    "biological_replicate": rep,
                    "lane_id": str(lane),
                    "reference_id": "toy",
                    "read1": str(r1),
                    "read2": str(r2),
                    "read1_sha256": digest(r1),
                    "read2_sha256": digest(r2),
                    "mapq": 30,
                    "duplicates": "exclude",
                    "adapter_r1": "-",
                    "adapter_r2": "-",
                }
            )
    with sheet.open("w") as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(FIELDS), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    before = {str(p): digest(p) for p in fixture.rglob("*") if p.is_file()}
    run = folder / "run"
    assert execute(sheet, registry, run) == 0
    output = run / "output"
    trace = list(csv.DictReader((output / "trace.tsv").open(), delimiter="\t"))
    assert len(trace) == 21 and all(r["status"] == "COMPLETED" for r in trace), trace
    shutil.copy2(output / "trace.tsv", folder / "fresh-trace.tsv")
    scientific = {
        str(p): digest(p)
        for p in output.rglob("*")
        if p.is_file() and p.suffix in {".gz", ".bw", ".narrowPeak"}
    }
    for library in ("first", "second"):
        reports = output / library / "qc"
        assert len(list((reports / "fastqc").glob("*.zip"))) == 2
        modules = json.loads((reports / "multiqc_data/required-modules.json").read_text())
        assert set(modules.values()) == {2} and len(modules) == 4
        assert (output / library / "peaks/atac_peaks.narrowPeak").stat().st_size > 0
        acquisition = json.loads((output / library / "provenance/acquisition.json").read_text())
        assert acquisition["templates"] == 32000 and len(acquisition["sources"]) == 4
    assert not list(output.rglob("*.bam")) and not list(output.rglob("*.fastq.gz"))
    comparisons = json.loads((output / "replicate-comparisons.json").read_text())["comparisons"]
    assert len(comparisons) == 1 and comparisons[0]["peak_bp_jaccard"] == 1
    assert not comparisons[0]["same_biological_replicate"]
    for repetition in (1, 2):
        assert execute(sheet, registry, run, resume=True) == 0
        trace = list(csv.DictReader((output / "trace.tsv").open(), delimiter="\t"))
        assert len(trace) == 21 and all(r["status"] == "CACHED" for r in trace), trace
        shutil.copy2(output / "trace.tsv", folder / f"resume-{repetition}-trace.tsv")
        assert scientific == {p: digest(Path(p)) for p in scientific}
    assert before == {p: digest(Path(p)) for p in before}
    original = (run / "inputs/first.json").read_bytes()
    sheet.write_text(sheet.read_text().replace("\t30\t", "\t10\t"))
    try:
        prepare(sheet, registry, run)
    except ValueError:
        pass
    else:
        raise AssertionError("Changed run inputs accepted")
    assert (run / "inputs/first.json").read_bytes() == original
    print(
        "PASS: two libraries, technical lanes, 21 cached tasks twice; "
        "raw/scientific outputs unchanged"
    )
    if not args.keep:
        shutil.rmtree(folder)


if __name__ == "__main__":
    main()
