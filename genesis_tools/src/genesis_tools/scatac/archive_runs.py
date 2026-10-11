"""Archive run relationships, retained separately from original workbook values."""

from __future__ import annotations

import csv
import io
import re
import urllib.parse
from pathlib import Path
from typing import Any

from ..contracts.records import dump, fingerprint, load
from .discovery import Archive, rows


def run(directory: Path, *, refresh: bool = False) -> dict[str, Any]:
    inventory = load(directory / "inventory.json")
    candidates = rows(directory, inventory["data"]["rows"])
    projects = sorted({r["values"].get("bioproject", "").strip() for r in candidates})
    archive = Archive(directory / "sources", refresh=refresh)
    records, errors = [], []
    for project in projects:
        if not re.fullmatch(r"PRJ(?:NA|EB|DB)\d+", project):
            errors.append({"project": project, "condition": "UNRESOLVED_PROJECT"})
            continue
        url = "https://www.ebi.ac.uk/ena/portal/api/filereport?" + urllib.parse.urlencode(
            {
                "accession": project,
                "result": "read_run",
                "format": "tsv",
                "fields": (
                    "run_accession,experiment_accession,sample_accession,scientific_name,"
                    "library_strategy,fastq_ftp,fastq_bytes,fastq_md5"
                ),
            }
        )
        try:
            table = list(csv.DictReader(io.StringIO(archive.get(url)), delimiter="\t"))
            if not table:
                errors.append({"project": project, "condition": "NO_ARCHIVE_RUNS"})
            records.extend({"project": project, **r} for r in table)
        except (OSError, ValueError) as error:
            errors.append(
                {
                    "project": project,
                    "condition": type(error).__name__,
                    "http_status": getattr(error, "code", None),
                }
            )
    result = {
        "schema_version": 1,
        "inventory_version": inventory["version"],
        "records": records,
        "sources": archive.sources,
        "errors": errors,
    }
    dump(
        directory / "archive-run-revisions" / (fingerprint(result) + ".json"),
        result,
        immutable=True,
    )
    dump(directory / "archive-runs.json", result)
    return {
        "runs": len(records),
        "projects": len(projects),
        "errors": errors,
        "complete": not errors,
        "version": fingerprint(result),
    }


def apply(
    directory: Path,
    libraries: list[dict[str, Any]],
    accessions: list[dict[str, Any]],
    issues: list[dict[str, Any]],
) -> None:
    path = directory / "archive-runs.json"
    if not path.exists():
        return
    value = load(path)
    if value["inventory_version"] != load(directory / "inventory.json")["version"]:
        raise ValueError("Archive runs belong to a different workbook revision")
    for library in libraries:
        experiments = set(re.split("[;,]", library.get("experiment_accession", ""))) - {""}
        matches = [r for r in value["records"] if r["experiment_accession"] in experiments]
        if not matches:
            continue
        old = library.get("run_accessions", "")
        observed = {r["run_accession"] for r in matches}
        original = set(re.split("[;,]", old)) - {""}
        if original - observed or any(
            r["project"] != library["study_key"] or r["scientific_name"] != library["species"]
            for r in matches
        ):
            issues.append(
                {
                    "row": library["row"],
                    "code": "ARCHIVE_RELATIONSHIP_CONFLICT",
                    "detail": "Archive run/species/project relationships differ from source values",
                    "review_status": "UNREVIEWED",
                }
            )
            continue
        library["original_run_accessions"] = old
        library["run_accessions"] = ";".join(sorted(observed))
        library["archive_runs_version"] = fingerprint(value)
        for accession in sorted(observed - original):
            accessions.append(
                {
                    "candidate_id": library["candidate_id"],
                    "row": library["row"],
                    "kind": "run_accessions",
                    "accession": accession,
                    "syntax_valid": bool(re.fullmatch(r"[SED]RR\d+", accession)),
                    "study_key": library["study_key"],
                    "source": "ENA",
                }
            )
