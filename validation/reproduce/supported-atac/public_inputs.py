"""Recreate the pinned, positional public ATAC subsets in a new output directory.

Run with Python 3.12. Gzip compression builds can differ; mismatches fail rather
than silently changing the validated input identity. Full source FASTQ checksums
are not verified because only the first 200,000 records are downloaded.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import shutil
import time
import urllib.request
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def fetch(record: dict[str, Any], output: Path) -> None:
    target = output / record["file"]
    started = time.monotonic()
    if not target.exists():
        temporary = target.with_suffix(".part")
        with urllib.request.urlopen(record["url"], timeout=120) as source:
            if "selection" in record:
                with gzip.GzipFile(fileobj=source) as raw, temporary.open("wb") as destination:
                    with gzip.GzipFile(fileobj=destination, mode="wb", mtime=0, filename="") as out:
                        for _ in range(200000):
                            lines = [raw.readline() for _ in range(4)]
                            if not lines[-1]:
                                raise ValueError(f"Short FASTQ: {target.name}")
                            out.write(b"".join(lines))
            else:
                with temporary.open("wb") as destination:
                    shutil.copyfileobj(source, destination, length=1024 * 1024)
        if digest(temporary) != record["sha256"]:
            raise ValueError(f"Checksum mismatch: {target.name}; retained .part for inspection")
        temporary.rename(target)
    if digest(target) != record["sha256"]:
        raise ValueError(f"Existing input checksum mismatch: {target.name}")
    result = {
        "file": target.name,
        "sha256": record["sha256"],
        "seconds": time.monotonic() - started,
    }
    with (output / "acquisition.jsonl").open("a") as stream:
        stream.write(json.dumps(result) + "\n")


def prepare(output: Path) -> None:
    registry = json.loads((HERE / "references.json").read_text())
    for reference in registry["references"]:
        name = reference["reference_id"]
        fasta = output / f"{name}.fa.gz"
        annotation = output / f"{name}.gtf.gz"
        organelles = reference["mitochondrial_contigs"] + reference["plastid_contigs"]
        nuclear_bases = 0
        sizes: dict[str, int] = {}
        contig = ""
        with gzip.open(fasta, "rt") as stream:
            for line in stream:
                if line.startswith(">"):
                    contig = line[1:].split()[0]
                    sizes[contig] = 0
                else:
                    sequence = line.strip().upper()
                    sizes[contig] += len(sequence)
                    if contig not in organelles:
                        nuclear_bases += sum(sequence.count(base) for base in "ACGT")
        if nuclear_bases != reference["genome_size"] or not set(organelles) <= sizes.keys():
            raise ValueError(f"Reference composition changed: {name}")
        positions: set[tuple[str, int, str]] = set()
        with gzip.open(annotation, "rt") as stream:
            for line in stream:
                if line.startswith("#"):
                    continue
                fields = line.rstrip().split("\t")
                if fields[2] == "transcript" and fields[0] in sizes and fields[0] not in organelles:
                    position = int(fields[3]) - 1 if fields[6] == "+" else int(fields[4]) - 1
                    positions.add((fields[0], position, fields[6]))
        tss = output / f"{name}.tss.bed"
        tss.write_text("".join(f"{c}\t{p}\t{s}\n" for c, p, s in sorted(positions)))
        if digest(tss) != reference["tss_sha256"]:
            raise ValueError(f"Derived TSS checksum mismatch: {name}")
        reference.update(fasta=str(fasta), tss=str(tss))
    (output / "references.json").write_text(json.dumps(registry, indent=2) + "\n")
    with (HERE / "samples.tsv").open() as source:
        reader = csv.DictReader(source, delimiter="\t")
        rows = list(reader)
    for row in rows:
        for mate in ("read1", "read2"):
            row[mate] = str(output / Path(row[mate]).name)
    with (output / "samples.tsv").open("w") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if (output / "samples.tsv").exists() or (output / "references.json").exists():
        raise ValueError("Use a new output directory; existing manifests are never overwritten")
    for record in json.loads((HERE / "downloads.json").read_text()):
        fetch(record, output)
    prepare(output)
    print(f"Verified inputs and manifests: {output}")


if __name__ == "__main__":
    main()
