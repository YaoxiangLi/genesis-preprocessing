"""Prepared-study acceptance: input review, immutable execution and result collection."""

from __future__ import annotations

import contextlib
import csv
import gzip
import sqlite3
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

from genesis_tools.atac.inputs import FIELDS, digest
from genesis_tools.contracts.records import dump, load, loads
from genesis_tools.curation import harmonize, review
from genesis_tools.registry import store
from genesis_tools.study import inputs
from verify_curation import rejects


def prepared(root: Path, assay: str = "bulk-ATAC") -> tuple[Path, Path]:
    root.mkdir(parents=True)
    fasta = root / "tiny.fa.gz"
    fasta.write_bytes(gzip.compress(b">chr1\n" + b"A" * 100 + b"\n", mtime=0))
    sheet = root / "samples.tsv"
    if assay == "DAP-seq":
        sheet.write_text(
            "sample_id\tspecies\tread1_url\tread2_url\tcontrol_sample\treference_fasta\n"
            + "".join(
                f"{name}\tplant\thttps://example.invalid/{name}.fq.gz\t-\t{control}\ttiny.fa.gz\n"
                for name, control in (
                    ("TF1", "control"),
                    ("TF2", "control"),
                    ("control", "-"),
                )
            )
        )
        return sheet, root
    tss = root / "tss.bed"
    tss.write_text("chr1\t20\t+\n")
    registry = root / "references.json"
    dump(
        registry,
        {
            "schema_version": 1,
            "references": [
                {
                    "reference_id": "tiny",
                    "species": "synthetic plant",
                    "assembly": "synthetic-v1",
                    "annotation_release": "synthetic-v1",
                    "genome_size_method": "fixture length",
                    "genome_size": 100,
                    "fasta": str(fasta),
                    "fasta_sha256": digest(fasta),
                    "tss": str(tss),
                    "tss_sha256": digest(tss),
                    "mitochondrial_contigs": [],
                    "plastid_contigs": [],
                }
            ],
        },
    )
    rows = []
    for name, lanes in (("lib-a", ("lane1", "lane2")), ("lib-b", ("lane1",))):
        for lane in lanes:
            row = {
                "library_id": name,
                "sample_id": name,
                "biological_replicate": name,
                "lane_id": lane,
                "reference_id": "tiny",
                "mapq": "30",
                "duplicates": "exclude",
                "adapter_r1": "-",
                "adapter_r2": "-",
            }
            for mate in ("read1", "read2"):
                path = root / f"{name}-{lane}-{mate}.fq.gz"
                path.write_bytes(gzip.compress(b"@read\nAAAA\n+\nIIII\n", mtime=0))
                row[mate], row[mate + "_sha256"] = str(path), digest(path)
            rows.append(row)
    with sheet.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(FIELDS), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    return sheet, registry


def approve_inputs(catalog: Path, dataset: str, root: Path) -> dict[str, Any]:
    source = root / "curator.json"
    dump(source, {"tissue": "leaf", "treatment": "explicit synthetic treatment"})
    harmonize.ingest(catalog, dataset, [source], [], "local-only", scope="inputs")
    proposal = harmonize.propose(catalog, dataset, scope="inputs")
    with contextlib.closing(store.connect(catalog, scope="inputs")) as db:
        token = review.token(db, dataset)
    review.decide(
        catalog,
        dataset,
        "metadata",
        "approve",
        token,
        "Review of this synthetic fixture only",
        proposal["data"]["evidence"],
        proposal["version"],
        scope="inputs",
    )
    return harmonize.apply(
        catalog, dataset, proposal["version"], root / "approved.json", scope="inputs"
    )


def input_checks(root: Path) -> None:
    sheet, refs = prepared(root / "raw")
    study = root / "study"
    first = inputs.initialize(study, "test", "bulk-ATAC", sheet, refs)
    assert inputs.initialize(study, "test", "bulk-ATAC", sheet, refs) == first
    catalog = inputs.catalog(study)
    dataset = first["datasets"][0]["id"]
    with contextlib.closing(store.connect(catalog)) as db:
        assert len(store.search(db)) == 2
        assert review.status(db, dataset)["execution"] == "NOT_RUN"
        token = review.token(db, dataset)
    rejects(
        lambda: review.decide(catalog, dataset, "metadata", "approve", token, "test", []),
        "--scope inputs",
    )
    revision = approve_inputs(catalog, dataset, root)
    with contextlib.closing(store.connect(catalog, scope="inputs")) as db:
        assert review.effective(db, dataset, "metadata") == "APPROVED"
        assert loads(store.current(db, dataset)["metadata"])["tissue"] == "leaf"
    assert revision["data"]["compiled_inputs"]["parameters"]["mapq"] == 30
    before = sheet.read_text()
    sheet.write_text(before.replace("\t30\t", "\t31\t"))
    second = inputs.initialize(study, "test", "bulk-ATAC", sheet, refs)
    assert second["study"]["version"] != first["study"]["version"]
    with contextlib.closing(store.connect(catalog, scope="inputs")) as db:
        assert review.effective(db, dataset, "metadata") == "STALE"
        assert loads(store.current(db, dataset)["metadata"])["tissue"] == "leaf"
    # Real prior schema, rather than merely changing the version pragma on a new database.
    old = root / "prior"
    with patch.object(store, "SCHEMA_VERSION", 3):
        store.initialize(old)
    with sqlite3.connect(old / "registry.sqlite") as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 3
    store.initialize(old)
    assert list(old.glob("before-v3-to-v4-*.sqlite"))
    backup = root / "backup.sqlite"
    store.backup(catalog, backup)
    store.restore(backup, root / "restored")
    with contextlib.closing(store.connect(root / "restored", scope="inputs")) as db:
        assert review.effective(db, dataset, "metadata") == "STALE"
    dap_sheet, dap_refs = prepared(root / "dap-raw", "DAP-seq")
    dap = inputs.initialize(root / "dap", "dap-test", "DAP-seq", dap_sheet, dap_refs)
    assert len(dap["datasets"]) == 3
    assert load(study / "study.json") == second["study"]
    print(
        "PASS: prepared input registration, scoped review, stale evidence, v3 migration and restore"
    )


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="genesis-study-") as temporary:
        input_checks(Path(temporary))


if __name__ == "__main__":
    main()
