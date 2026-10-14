"""Evidence-backed identity assertions, separate from scientific release approval."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..contracts.records import dump, fingerprint, load
from .common import digest

FIELDS = ("study_key", "biological_sample_id", "biological_replicate_id", "library_id")


def binding(directory: Path) -> dict[str, Any]:
    discovery = directory / "discovery.json"
    return {
        "inventory_version": load(directory / "inventory.json")["version"],
        "discovery_version": fingerprint(load(discovery)) if discovery.exists() else None,
    }


def validate(directory: Path, value: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if value.get("schema_version") != 1 or value.get("bindings") != binding(directory):
        raise ValueError("Identity assertions are missing or bound to a different inventory")
    mappings = {}
    libraries = {}
    samples = {}
    for item in value["mappings"]:
        candidate = item["candidate_id"]
        if candidate in mappings or any(
            not isinstance(item.get(k), str)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,255}", item[k])
            for k in FIELDS
        ):
            raise ValueError("Distinct candidates and explicit biological/library IDs required")
        if not item.get("evidence") or not item.get("asserted_by"):
            raise ValueError("Identity assertions require an accountable source and evidence")
        supported = set()
        for evidence in item["evidence"]:
            sha = evidence["snapshot_sha256"]
            if not re.fullmatch(r"[a-f0-9]{64}", sha):
                raise ValueError("Invalid evidence checksum")
            path = directory / "sources" / (sha + ".txt")
            if not path.is_file() or digest(path) != sha:
                raise ValueError("Missing or changed identity evidence snapshot")
            quote = evidence["quote"]
            if not isinstance(quote, str) or not quote.strip() or quote not in path.read_text():
                raise ValueError("Identity evidence quotation does not match its snapshot")
            supported.update(evidence["supports"])
        if set(FIELDS) - supported:
            raise ValueError("Evidence must support all identity relationships")
        biological = tuple(item[k] for k in FIELDS[:-1])
        library = (item["study_key"], item["library_id"])
        if library in libraries and libraries[library] != biological:
            raise ValueError("One library cannot belong to conflicting biological identities")
        libraries[library] = biological
        sample = (item["study_key"], item["biological_sample_id"])
        replicate = item["biological_replicate_id"]
        if sample in samples and samples[sample] != replicate:
            raise ValueError("One biological sample cannot denote different replicates")
        samples[sample] = replicate
        mappings[candidate] = item
    return mappings


def attach(directory: Path, source: Path, candidates: set[str]) -> dict[str, Any]:
    value = load(source)
    mappings = validate(directory, value)
    if set(mappings) - candidates:
        raise ValueError("Identity assertion refers to an unknown candidate")
    version = fingerprint(value)
    dump(directory / "identity-revisions" / (version + ".json"), value, immutable=True)
    dump(directory / "identities.json", value)
    return {
        "identity_version": version,
        "documented_candidates": len(mappings),
        "review_status": "UNREVIEWED",
    }


def apply(directory: Path, libraries: list[dict[str, Any]], issues: list[dict[str, Any]]) -> None:
    path = directory / "identities.json"
    if not path.exists():
        return
    mappings = validate(directory, load(path))
    accession_libraries: dict[tuple[str, str], str] = {}
    for row in libraries:
        item = mappings.get(row["candidate_id"])
        if not item:
            continue
        if row["study_key"] != item["study_key"]:
            raise ValueError("Identity assertion contradicts the source study")
        for kind in ("experiment_accession", "run_accessions"):
            for acc in re.split(r"[;,]", row.get(kind, "")):
                if not acc:
                    continue
                previous = accession_libraries.setdefault((kind, acc), item["library_id"])
                if previous != item["library_id"]:
                    raise ValueError("One archive experiment/run maps to conflicting libraries")
        row.update({k: item[k] for k in FIELDS})
        row.update(identity_status="DOCUMENTED", identity_evidence_version=fingerprint(item))
    documented = {r["row"] for r in libraries if r["identity_status"] == "DOCUMENTED"}
    issues[:] = [
        i for i in issues if not (i["row"] in documented and i["code"] == "REPLICATE_UNRESOLVED")
    ]
