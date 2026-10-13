"""Validate DAP provenance without trusting a self-declared completeness flag."""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from importlib.resources import files
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator, validators

from ..dap_provenance import sha256
from ..reference_cache import INDEX_SUFFIXES, validate_provenance
from ..samples import IDENTIFIER
from .records import load, loads


def read_run(
    path: Path, samples: list[dict[str, Any]], sheet: Path | None
) -> tuple[dict[str, Any], list[str]]:
    value = load(path)
    schema = loads(files(__package__).joinpath("schemas/dap-run-v1.json").read_text())
    checker = Draft202012Validator.TYPE_CHECKER.redefine("integer", lambda _, v: type(v) is int)
    errors = list(
        validators.extend(Draft202012Validator, type_checker=checker)(schema).iter_errors(value)
    )
    if errors:
        raise ValueError(
            f"Malformed DAP run provenance: {errors[0].json_path}: {errors[0].message}"
        )
    declared = value["samples"]
    names = [s["sample_id"] for s in declared]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate DAP provenance sample")
    converted = [
        {
            "id": s["sample_id"],
            "species": s["species"],
            "reference_fasta": s["reference_fasta"],
            "ref_id": s["reference_fasta"].rsplit(".", 2)[0],
            "layout": "SE" if s["read2_url"] == "-" else "PE",
            "control": s["control_sample"],
        }
        for s in declared
    ]
    if sorted(converted, key=lambda s: s["id"]) != sorted(samples, key=lambda s: s["id"]):
        raise ValueError("DAP provenance disagrees with MultiQC samples/controls/references")
    if sheet is not None and sha256(sheet) != value["sheet_sha256"]:
        raise ValueError("DAP provenance sample sheet checksum mismatch")
    for row in declared:
        if not all(
            IDENTIFIER.fullmatch(row[k]) for k in ("sample_id", "species", "reference_fasta")
        ):
            raise ValueError("Unsafe DAP provenance identity")
        control = next((s for s in converted if s["id"] == row["control_sample"]), None)
        own = next(s for s in converted if s["id"] == row["sample_id"])
        if row["control_sample"] != "-" and (
            control is None
            or control["control"] != "-"
            or any(control[k] != own[k] for k in ("species", "reference_fasta", "layout"))
        ):
            raise ValueError("Incompatible DAP provenance control")
    expected_reads = {
        (s["sample_id"], mate): s[mate + "_url"]
        for s in declared
        for mate in ("read1", "read2")
        if s[mate + "_url"] != "-"
    }
    actual_reads = {(i["sample_id"], i["mate"]): i["url"] for i in value["inputs"]}
    if expected_reads != actual_reads or len(actual_reads) != len(value["inputs"]):
        raise ValueError("DAP provenance input receipts do not match the sample sheet")
    references = value["references"]
    if {r["filename"] for r in references} != {s["reference_fasta"] for s in declared} or len(
        {r["id"] for r in references}
    ) != len(references):
        raise ValueError("DAP provenance reference set mismatch")
    incomplete = []
    for ref in references:
        if ref["id"] != ref["filename"].rsplit(".", 2)[0]:
            raise ValueError("DAP provenance reference identity mismatch")
        sizes, index = ref["sizes_cache"], ref["index_cache"]
        for cache, kind in ((sizes, "chrom-sizes"), (index, "bwa-mem2")):
            validate_provenance(cache)
            if cache["kind"] != kind or cache["source_basename"] != ref["filename"]:
                raise ValueError("DAP reference cache kind/source mismatch")
            if cache["mode"] != "real" or not pinned(
                cache["generator"].get("engine"), cache["generator"]["container"]
            ):
                incomplete.append(
                    "Reference generation lacks a real, immutable execution environment"
                )
        if any(sizes[k] != index[k] for k in ("fasta_sha256", "compressed_fasta_sha256")):
            raise ValueError("DAP reference caches disagree about FASTA identity")
        if sizes["artifacts"] != {ref["id"] + ".chrom.sizes": ref["sizes_sha256"]} or set(
            index["artifacts"]
        ) != {"genome" + s for s in INDEX_SUFFIXES}:
            raise ValueError("DAP reference cache artifact mismatch")
        if set(ref["contig_order"]) != set(ref["contigs"]):
            raise ValueError("DAP reference contig order mismatch")
        encoded = "".join(
            f"{name}\t{ref['contigs'][name]}\n" for name in ref["contig_order"]
        ).encode()
        if hashlib.sha256(encoded).hexdigest() != ref["sizes_sha256"]:
            raise ValueError("DAP reference contig lengths disagree with size receipt")
    for relative in value["outputs"]:
        p = PurePosixPath(relative)
        if p.is_absolute() or p.as_posix() != relative or ".." in p.parts or "\\" in relative:
            raise ValueError("Unsafe DAP provenance output path")
    expected_tasks = Counter({("MULTIQC", "run"): 1})
    for s in converted:
        name = s["id"]
        for step in ("DOWNLOAD", "METADATA", "BWA_MEM2_ALIGN", "QC", "TRACKS"):
            expected_tasks[step, name] = 1
        for mate in ("read1", "read2") if s["layout"] == "PE" else ("read1",):
            expected_tasks["FASTQC", name + "." + mate] = 1
        if s["control"] != "-":
            expected_tasks["CALL_PEAKS", name] = expected_tasks["QUANTIFY", name] = 1
    actual_tasks = Counter((t["step"], s) for t in value["tasks"] for s in t["subjects"])
    if actual_tasks != expected_tasks:
        raise ValueError("DAP provenance task receipts are missing, duplicated or unrelated")
    for task in value["tasks"]:
        if task["mode"] != "real" or not pinned(task["engine"], task["container"]):
            incomplete.append("Task execution lacks a real, immutable container identity")
    context = value["context"]
    if context["source_status"] != "clean" or not re.fullmatch(r"[0-9a-f]{40}", context["git_sha"]):
        incomplete.append("Pipeline checkout lacks a clean, pinned Git identity")
    return value, sorted(set(incomplete))


def pinned(engine: str | None, container: str | None) -> bool:
    return (
        engine in {"docker", "apptainer", "singularity", "podman"}
        and isinstance(container, str)
        and re.search(r"@sha256:[0-9a-f]{64}$", container) is not None
    )
