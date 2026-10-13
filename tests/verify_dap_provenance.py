"""Strict DAP receipt contracts; synthetic evidence is never biological validation."""

from __future__ import annotations

import copy
import hashlib
import tempfile
from pathlib import Path
from typing import Any

from genesis_tools.contracts.adapters import from_dap
from genesis_tools.contracts.dap import read_run
from genesis_tools.contracts.records import dump
from genesis_tools.reference_cache import INDEX_SUFFIXES
from verify_curation import rejects

H = "a" * 64
IMAGE = "fixture/test@sha256:" + H


def fixture(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    samples = [
        {
            "id": name,
            "species": "plant",
            "reference_fasta": "toy.fa.gz",
            "ref_id": "toy",
            "layout": "SE",
            "control": control,
        }
        for name, control in (("TF", "control"), ("control", "-"))
    ]
    dump(
        root / "output/multiqc/multiqc_data/genesis_provenance.json",
        {"run": {"git_sha": "b" * 40}, "samples": samples},
    )
    legacy = from_dap(root, "synthetic", "local", None, None, None)
    assert all(not m["data"]["run"]["provenance_complete"] for m in legacy)
    outputs = {
        str(Path(a["path"]).relative_to(root / "output")): {"sha256": H, "size": 0}
        for m in legacy
        for a in m["data"]["artifacts"]
    }
    tasks = []
    for step, subjects in (
        [("MULTIQC", ["run"]), ("DOWNLOAD", ["TF", "control"])]
        + [
            (step, [s["id"] + ".read1" if step == "FASTQC" else s["id"]])
            for s in samples
            for step in ("FASTQC", "METADATA", "BWA_MEM2_ALIGN", "QC", "TRACKS")
        ]
        + [(step, ["TF"]) for step in ("CALL_PEAKS", "QUANTIFY")]
    ):
        tasks.append(
            {
                "schema_version": 1,
                "step": step,
                "subjects": subjects,
                "mode": "real",
                "attempt": 1,
                "engine": "docker",
                "container": IMAGE,
                "requested": {"cpus": 2, "memory_bytes": 1024, "time_ms": 5000},
                "observed": None,
                "script_sha256": H,
            }
        )
    sizes_hash = hashlib.sha256(b"chr2\t20\nchr1\t10\n").hexdigest()
    cache = {
        "schema_version": 1,
        "mode": "real",
        "source_basename": "toy.fa.gz",
        "fasta_sha256": H,
        "compressed_fasta_sha256": H,
        "generator": {
            "container": IMAGE,
            "engine": "docker",
            "recipe_sha256": H,
            "version": "fixture-only",
            "version_stderr": "",
        },
    }
    data = {
        "schema_version": 1,
        "kind": "genesis-dap-run",
        "sheet_sha256": H,
        "context": {
            "schema_version": 1,
            "git_sha": "b" * 40,
            "source_status": "clean",
            "nextflow_version": "25.10.4",
            "profile": "local,test,docker",
            "source_hashes": {"fixture.nf": H},
            "parameters": {
                "bwa": {
                    "batch_size": 10000000,
                    "seed_length": 19,
                    "max_seed_occurrences": 10000,
                    "score_threshold": 30,
                },
                "spp_read_length": 50,
                "spp_script_sha256": H,
                "download_batch_size": 8,
                "mapq_filter": "none",
                "flag_exclude": 2308,
                "alignment_duplicates": "retain",
                "peak_duplicates": "default",
                "peak_format": "SE:BAM;PE:BAMPE",
                "quantification_unit": "read ends",
                "track_normalization": "CPM",
                "track_bin_size": 1,
                "strand_denominator": "all retained mapped read ends",
            },
        },
        "samples": [
            {
                "sample_id": s["id"],
                "species": "plant",
                "read1_url": f"https://example.invalid/{s['id']}.fq.gz",
                "read2_url": "-",
                "control_sample": s["control"],
                "reference_fasta": "toy.fa.gz",
            }
            for s in samples
        ],
        "inputs": [
            {
                "sample_id": s["id"],
                "mate": "read1",
                "url": f"https://example.invalid/{s['id']}.fq.gz",
                "sha256": H,
                "retention": "work-cache",
            }
            for s in samples
        ],
        "references": [
            {
                "id": "toy",
                "filename": "toy.fa.gz",
                "contigs": {"chr1": 10, "chr2": 20},
                "contig_order": ["chr2", "chr1"],
                "sizes_sha256": sizes_hash,
                "sizes_cache": {
                    **copy.deepcopy(cache),
                    "kind": "chrom-sizes",
                    "artifacts": {"toy.chrom.sizes": sizes_hash},
                },
                "index_cache": {
                    **copy.deepcopy(cache),
                    "kind": "bwa-mem2",
                    "artifacts": {"genome" + s: H for s in INDEX_SUFFIXES},
                },
            }
        ],
        "outputs": outputs,
        "tasks": tasks,
    }
    return data, samples


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="genesis-dap-contract-") as temporary:
        root = Path(temporary)
        data, samples = fixture(root)
        path = root / "output/provenance/dap-run.json"
        dump(path, data)
        assert read_run(path, samples, None) == (data, [])
        manifests = from_dap(root, "synthetic", "local", None, None, None)
        assert all(m["data"]["run"]["provenance_complete"] for m in manifests)
        assert all(m["data"]["reference"]["contigs"] == {"chr1": 10, "chr2": 20} for m in manifests)
        # Recorded inputs may have been pruned; receipts preserve their identity.
        assert not (root / "work").exists()
        for field, value in (
            ("schema_version", 99),
            ("schema_version", True),
            ("provenance_complete", True),
        ):
            changed = copy.deepcopy(data)
            changed[field] = value
            dump(path, changed)
            rejects(lambda: read_run(path, samples, None), "Malformed")
        for change, message in (
            (lambda d: d["inputs"].pop(), "input receipts"),
            (lambda d: d["tasks"].pop(), "task receipts"),
            (lambda d: d["tasks"][0]["requested"].update(cpus=True), "Malformed"),
            (
                lambda d: d["outputs"].update({"../escape": {"sha256": H, "size": 0}}),
                "Unsafe",
            ),
            (lambda d: d["samples"][0].update(control_sample="TF"), "disagrees"),
            (lambda d: d["references"][0]["contigs"].update(chr1=11), "contig lengths"),
            (
                lambda d: d["references"][0]["index_cache"].update(
                    compressed_fasta_sha256="c" * 64
                ),
                "disagree",
            ),
        ):
            changed = copy.deepcopy(data)
            change(changed)
            dump(path, changed)
            rejects(lambda: read_run(path, samples, None), message)
        for change in (
            lambda d: d["context"].update(source_status="dirty"),
            lambda d: d["tasks"][0].update(mode="stub"),
            lambda d: d["tasks"][0].update(engine="none"),
            lambda d: d["tasks"][0].update(container="mutable:tag"),
            lambda d: d["references"][0]["sizes_cache"]["generator"].pop("engine"),
        ):
            changed = copy.deepcopy(data)
            change(changed)
            dump(path, changed)
            assert read_run(path, samples, None)[1]
        dump(path, data)
        sheet = root / "changed.tsv"
        sheet.write_text("changed bytes")
        rejects(lambda: read_run(path, samples, sheet), "sheet checksum mismatch")
        changed = copy.deepcopy(data)
        changed["outputs"].clear()
        dump(path, changed)
        rejects(lambda: from_dap(root, "synthetic", "local", None, None, None), "Malformed")
    print(
        "PASS: DAP strict schema, bindings, cache identity, incomplete evidence and legacy import"
    )


if __name__ == "__main__":
    main()
