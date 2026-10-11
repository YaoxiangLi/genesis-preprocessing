"""Offline archive/identity fixtures: no live-service dependency in regression checks."""

from __future__ import annotations

import hashlib
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest.mock import patch

from genesis_tools.contracts.records import dump, load
from genesis_tools.scatac import discovery, identities, inventory
from verify_scatac_inventory import fixture


def rejected(function: Callable[..., Any], *args: object) -> None:
    try:
        function(*args)
    except ValueError:
        return
    raise AssertionError("Invalid evidence accepted")


def main() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        fixture(root / "source.xlsx")
        directory = root / "inventory"
        inventory.import_workbook(root / "source.xlsx", directory, root / "registry", "test")
        series = (
            "!Series_title = A new plant study\n"
            "!Series_relation = BioProject: PRJNA99999\n"
            "!Series_sample_id = GSM99991\n"
            "!Series_sample_id = GSM99992\n"
            "!Series_sample_id = GSM99993"
        )
        atac = (
            "!Sample_title = ATAC biological replicate 1\n"
            "!Sample_organism_ch1 = Arabidopsis thaliana\n"
            "!Sample_relation = SRA: SRX99991\n"
            "!Sample_characteristics_ch1 = tissue: root\n"
            "!Sample_supplementary_file_1 = ftp://ftp.ncbi.nlm.nih.gov/fragments.tsv.gz"
        )
        content = {
            discovery.geo_url("GSE99999"): series,
            discovery.geo_url("GSM99991"): atac,
            discovery.geo_url("GSM99992"): atac.replace("ATAC", "RNA").replace(
                "fragments.tsv.gz", "matrix.h5"
            ),
            discovery.geo_url("GSM99993"): atac + "\n!Sample_organism_ch1 = Heterodera schachtii",
        }
        with patch.object(discovery.Archive, "get", lambda self, url: content[url]):
            first = discovery.run(directory, species=[discovery.SPECIES[0]], series=["GSE99999"])
            assert first == discovery.run(
                directory, species=[discovery.SPECIES[0]], series=["GSE99999"]
            )
        assert first["samples"] == 3 and first["complete"]
        report = inventory.audit(directory)
        assert len(report["libraries"]) == 5  # RNA and mixed-species remain in the source ledger.
        added = next(r for r in report["libraries"] if r["candidate_id"] == "geo:GSM99991")
        assert added["library_id"] == "" and added["multiome"] == "unknown"
        assert len(load(directory / "discovery.json")["records"]) == 3
        sha = hashlib.sha256(atac.encode()).hexdigest()
        (directory / "sources" / (sha + ".txt")).write_text(atac)
        value = {
            "schema_version": 1,
            "bindings": identities.binding(directory),
            "mappings": [
                {
                    "candidate_id": added["candidate_id"],
                    "study_key": added["study_key"],
                    "biological_sample_id": "root-1",
                    "biological_replicate_id": "rep-1",
                    "library_id": "atac-1",
                    "asserted_by": "fixture",
                    "evidence": [
                        {
                            "snapshot_sha256": sha,
                            "quote": "ATAC biological replicate 1",
                            "supports": list(identities.FIELDS),
                        }
                    ],
                }
            ],
        }
        source = root / "identities.json"
        dump(source, value)
        candidates = {r["candidate_id"] for r in report["libraries"]}
        assert identities.attach(directory, source, candidates)["documented_candidates"] == 1
        report = inventory.audit(directory)
        assert report["summary"][discovery.SPECIES[0]]["documented_biological_replicates"] == 1
        assert report["summary"][discovery.SPECIES[0]]["confirmed_biological_replicates"] == 0
        assert not any(
            i["row"] == "GSM99991" and i["code"] == "REPLICATE_UNRESOLVED"
            for i in report["metadata_issues"]
        )
        value["mappings"][0]["evidence"][0]["quote"] = "imaginary biological replicate 2"
        rejected(identities.validate, directory, value)
        value["mappings"][0]["evidence"][0]["quote"] = "ATAC biological replicate 1"
        value["bindings"]["inventory_version"] = "stale"
        rejected(identities.validate, directory, value)
        rejected(discovery.soft, "<html>temporary archive error</html>")
        rejected(discovery.geo_url, "GSE1&api_key=invalid")
        cached = discovery.Archive(directory / "cache")
        rejected(cached.get, "https://example.org/private")
        inventory.export(directory, root / "export")
        assert (root / "export/discovery.json").is_file()
    print(
        "PASS: repeat discovery, source preservation, modality/species separation, bound identities"
    )


if __name__ == "__main__":
    main()
