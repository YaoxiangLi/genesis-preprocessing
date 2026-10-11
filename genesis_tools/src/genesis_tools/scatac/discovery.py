"""Snapshot public archive metadata; discovery never establishes biological identity."""

from __future__ import annotations

import datetime
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any

from ..contracts.records import dump, fingerprint, load

SPECIES = ("Arabidopsis thaliana", "Sorghum bicolor")
HOSTS = {"eutils.ncbi.nlm.nih.gov", "www.ncbi.nlm.nih.gov", "www.ebi.ac.uk"}


class Archive:
    """Small, cached metadata requests with explicit errors and a transfer budget."""

    def __init__(self, directory: Path, *, refresh: bool = False) -> None:
        self.directory = directory
        self.refresh = refresh
        self.bytes = 0
        self.sources: list[dict[str, Any]] = []
        directory.mkdir(parents=True, exist_ok=True)

    def get(self, url: str) -> str:
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname not in HOSTS or parsed.username:
            raise ValueError("Metadata requests require a supported public HTTPS archive")
        key = hashlib.sha256(url.encode()).hexdigest()
        receipt_path = self.directory / (key + ".json")
        if receipt_path.exists() and not self.refresh:
            receipt = load(receipt_path)
            content = (self.directory / (receipt["sha256"] + ".txt")).read_bytes()
            if hashlib.sha256(content).hexdigest() != receipt["sha256"]:
                raise ValueError("Changed metadata snapshot")
        else:
            if self.bytes >= 128 * 1024**2:
                raise ValueError("Metadata transfer budget exceeded")
            # Public NCBI rate limit without API credentials: at most three requests/sec.
            time.sleep(0.4)
            request = urllib.request.Request(url, headers={"User-Agent": "Genesis-metadata/1"})
            with urllib.request.urlopen(request, timeout=30) as response:
                content = response.read(min(8 * 1024**2, 128 * 1024**2 - self.bytes) + 1)
            self.bytes += len(content)
            if len(content) > 8 * 1024**2 or self.bytes > 128 * 1024**2:
                raise ValueError("Metadata transfer budget exceeded")
            digest = hashlib.sha256(content).hexdigest()
            receipt = {
                "url": url,
                "sha256": digest,
                "bytes": len(content),
                "retrieved_date": datetime.date.today().isoformat(),
            }
            path = self.directory / (digest + ".txt")
            if not path.exists():
                path.write_bytes(content)
            dump(receipt_path, receipt)
        self.sources.append(receipt)
        return content.decode("utf-8")


def soft(text: str) -> dict[str, list[str]]:
    fields: dict[str, list[str]] = defaultdict(list)
    for line in text.splitlines():
        if line.startswith("!") and " = " in line:
            key, value = line[1:].split(" = ", 1)
            fields[key].append(value)
    if not fields:
        raise ValueError("Archive response is not SOFT metadata")
    return dict(fields)


def geo_url(accession: str) -> str:
    if not re.fullmatch(r"GS[EM]\d+", accession):
        raise ValueError("Invalid GEO accession")
    return "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?" + urllib.parse.urlencode(
        {"acc": accession, "targ": "self", "form": "text", "view": "brief"}
    )


def sample(
    accession: str, series: str, project: str, fields: dict[str, list[str]]
) -> dict[str, Any]:
    title = "; ".join(fields.get("Sample_title", []))
    organisms = fields.get("Sample_organism_ch1", [])
    characteristics = {}
    for item in fields.get("Sample_characteristics_ch1", []):
        key, separator, value = item.partition(":")
        if separator:
            characteristics.setdefault(key.strip().lower(), []).append(value.strip())
    relations = " ".join(fields.get("Sample_relation", []))
    files = [
        v.replace("ftp://ftp.ncbi.nlm.nih.gov/", "https://ftp.ncbi.nlm.nih.gov/")
        for k, values in fields.items()
        if k.startswith("Sample_supplementary_file")
        for v in values
        if v != "NONE"
    ]
    atac = bool(re.search(r"ATAC|chromatin accessibility", title, re.I))
    # Fragment files are direct evidence of an ATAC product, unlike generic processing prose.
    atac = atac or any("fragments.tsv" in v for v in files)
    values = {
        "geo_sample": accession,
        "geo_series": series,
        "bioproject": project,
        "species": organisms[0] if len(organisms) == 1 else ";".join(organisms),
        "sample_name": title,
        "biosample": ";".join(sorted(set(re.findall(r"SAM[NED][A-Z]?\d+", relations)))),
        "experiment_accession": ";".join(sorted(set(re.findall(r"[SED]RX\d+", relations)))),
        "tissue": ";".join(characteristics.get("tissue", [])),
        "genotype": ";".join(characteristics.get("genotype", [])),
        "treatment": ";".join(characteristics.get("treatment", [])),
        "dev_stage": ";".join(characteristics.get("developmental stage", [])),
        "assay": "ATAC_CANDIDATE" if atac else "OTHER_OR_UNRESOLVED",
        "multiome": "unknown",
    }
    return {
        "geo_sample": accession,
        "geo_series": series,
        "values": values,
        "organisms": organisms,
        "classification": values["assay"],
        "supplementary_files": files,
        "raw_metadata": fields,
        "review_status": "UNREVIEWED",
    }


def run(
    directory: Path,
    *,
    species: list[str],
    series: list[str] | None = None,
    max_studies: int = 100,
    refresh: bool = False,
) -> dict[str, Any]:
    if not species or set(species) - set(SPECIES) or not 1 <= max_studies <= 500:
        raise ValueError("Select supported species and 1..500 studies")
    inventory = load(directory / "inventory.json")
    archive = Archive(directory / "sources", refresh=refresh)
    accessions = set(series or [])
    queries = []
    errors = []
    for row in inventory["data"]["rows"]:
        accessions.update(re.findall(r"GSE\d+", row["values"].get("geo_series", "")))
    if series is None:
        for organism in species:
            term = (
                f'"{organism}" AND (ATAC OR "chromatin accessibility" OR multiome) '
                'AND ("single cell" OR "single nucleus" OR scATAC OR snATAC) AND gse[ETYP]'
            )
            queries.append(term)
            base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
            try:
                result = json.loads(
                    archive.get(
                        base
                        + "esearch.fcgi?"
                        + urllib.parse.urlencode(
                            {"db": "gds", "term": term, "retmode": "json", "retmax": max_studies}
                        )
                    )
                )["esearchresult"]
                if int(result["count"]) > max_studies:
                    errors.append({"source": organism, "condition": "SEARCH_TRUNCATED"})
                if result["idlist"]:
                    summary = json.loads(
                        archive.get(
                            base
                            + "esummary.fcgi?"
                            + urllib.parse.urlencode(
                                {"db": "gds", "id": ",".join(result["idlist"]), "retmode": "json"}
                            )
                        )
                    )["result"]
                    accessions.update(summary[k]["accession"] for k in summary["uids"])
            except (OSError, ValueError, KeyError) as error:
                errors.append({"source": organism, "condition": type(error).__name__})
    records = []
    studies = []
    for accession in sorted(accessions)[:max_studies]:
        try:
            fields = soft(archive.get(geo_url(accession)))
            projects = sorted(
                set(re.findall(r"PRJ(?:NA|EB|DB)\d+", " ".join(fields.get("Series_relation", []))))
            )
            studies.append({"accession": accession, "projects": projects, "raw_metadata": fields})
            for gsm in fields.get("Series_sample_id", []):
                try:
                    fields_sample = soft(archive.get(geo_url(gsm)))
                    value = sample(
                        gsm, accession, projects[0] if len(projects) == 1 else "", fields_sample
                    )
                    if set(value["organisms"]) & set(species):
                        records.append(value)
                except (OSError, ValueError, KeyError) as error:
                    errors.append({"source": gsm, "condition": type(error).__name__})
        except (OSError, ValueError, KeyError) as error:
            errors.append({"source": accession, "condition": type(error).__name__})
    if len(accessions) > max_studies:
        errors.append({"source": "series", "condition": "STUDY_LIMIT"})
    data = {
        "schema_version": 1,
        "inventory_version": inventory["version"],
        "species": species,
        "queries": queries,
        "studies": studies,
        "records": records,
        "sources": archive.sources,
        "errors": errors,
        "complete": not errors,
    }
    version = fingerprint(data)
    dump(directory / "discovery-revisions" / (version + ".json"), data, immutable=True)
    dump(directory / "discovery.json", data)
    return {
        "version": version,
        "studies": len(studies),
        "samples": len(records),
        "errors": errors,
        "downloaded_metadata_bytes": archive.bytes,
        "complete": not errors,
    }


def rows(directory: Path, original: list[dict[str, Any]]) -> list[dict[str, Any]]:
    path = directory / "discovery.json"
    if not path.exists():
        return original
    discovery = load(path)
    if discovery["inventory_version"] != load(directory / "inventory.json")["version"]:
        raise ValueError("Discovery belongs to a different workbook revision; refresh it")
    known = {
        v
        for row in original
        for key in ("geo_sample", "experiment_accession")
        for v in re.split(r"[;,]", row["values"].get(key, ""))
        if v
    }
    result = list(original)
    seen = set()
    for item in discovery["records"]:
        value = item["values"]
        gsm = value["geo_sample"]
        if (
            item["classification"] != "ATAC_CANDIDATE"
            or len(item["organisms"]) != 1
            or gsm in seen
            or gsm in known
            or bool(set(re.split(r"[;,]", value["experiment_accession"])) & known)
        ):
            continue
        seen.add(gsm)
        result.append(
            {
                "row": gsm,
                "values": value,
                "cells": {},
                "candidate_id": "geo:" + gsm,
                "source": "discovery",
            }
        )
    return result
