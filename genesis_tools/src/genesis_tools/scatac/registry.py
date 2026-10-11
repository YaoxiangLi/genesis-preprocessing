"""Register verified outputs as immutable, unreviewed scientific artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..contracts.adapters import artifact, reference, snapshot
from ..contracts.records import (
    ArtifactManifest,
    QCMeasurement,
    SourceEvidence,
    fingerprint,
    identity,
    load,
    record,
)
from ..contracts.validation import Budget, bundle
from ..registry import store
from .common import verify_output

KINDS = {
    "scatac-fragments",
    "scatac-pseudobulk-core",
    "scatac-group-core",
    "scatac-group",
    "scatac-model",
    "scatac-loader-validation",
}


def projection(directory: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    data = manifest["data"]
    group = data["group"]
    bio = group["identity"]
    source_id = "scatac:" + bio["study_id"]
    if bio["assay"] not in {"scATAC", "snATAC", "multiome-ATAC"}:
        raise ValueError("Explicit single-cell assay identity is required")
    dataset = identity("pseudobulk", source_id, fingerprint(bio))
    ref = group["reference"]
    reference_value = reference(
        {**ref, "fasta": ref["fasta"]["path"], "fasta_sha256": ref["fasta"]["sha256"]}
    )
    artifacts = []
    for name, checksum in manifest["outputs"].items():
        fmt = "json" if name.endswith(".json") else "file"
        if name == "signal.bw":
            fmt = "bigwig"
        if name == "peaks_peaks.narrowPeak":
            fmt = "narrowPeak"
        artifacts.append(
            artifact(
                directory,
                name,
                "local",
                dataset,
                name,
                fmt,
                ref["reference_id"],
                checksum=checksum,
                signal={
                    "kind": "raw_counts",
                    "unit": "cut",
                    "normalization": "none",
                    "strand": "both",
                    "derivation": data["policy"]["signal_convention"],
                }
                if name == "signal.bw"
                else None,
            )
        )
    execution = load(directory / "execution.json")
    qc_source = snapshot(directory / "qc.json", "local")
    qc = data["qc"]
    measurements = []
    for name, metric, definition, units, denominator in (
        (
            "frip",
            "FRiP",
            "unique-cell-fragment-frip/v1",
            "fraction",
            "unique library/barcode fragments",
        ),
        (
            "support_redundancy_fraction",
            "support_redundancy_fraction",
            "1 - unique fragments / read-pair support",
            "fraction",
            "read-pair support",
        ),
        (
            "tss_enrichment",
            "TSS_enrichment",
            qc.get("tss_definition", "UNSPECIFIED"),
            "ratio",
            "mean declared TSS flanks",
        ),
        ("peak_count", "peak_count", "MACS3 BEDPE; keep-dup all", "peaks", "not applicable"),
    ):
        measurements.append(
            QCMeasurement(
                dataset,
                metric,
                definition,
                units,
                denominator,
                qc.get(name),
                SourceEvidence(
                    str((directory / "qc.json").resolve()),
                    qc_source["data"]["sha256"],
                    "/" + name,
                    "local",
                ),
                depth="full",
                denominator_value=qc["denominator_fragments"]
                if name == "frip"
                else qc["total_support"]
                if name == "support_redundancy_fraction"
                else None,
            ).export()
        )
    return ArtifactManifest(
        source_id,
        dataset,
        bio["cell_type"] + ":" + bio["biological_replicate_id"],
        bio["assay"],
        bio["species"],
        bio["study_id"],
        bio["biological_sample_id"],
        fingerprint(bio),
        [],
        reference_value,
        "local",
        {
            "campaign_id": None,
            "job_id": None,
            "attempt": None,
            "execution_state": "SUCCEEDED",
            "git_sha": execution["git_sha"],
            "parameters": data["policy"],
            "provenance_complete": True,
            "root": str(directory.resolve()),
        },
        {
            **bio,
            "organism": bio["species"],
            "protocol": bio["assay"],
            "biological_replicate": bio["biological_replicate_id"],
            "role": "pseudobulk",
            "library_composition": group["library_composition"],
            "scatac_manifest": manifest["version"],
            "qc": data["qc"],
            "model_ready": False,
        },
        artifacts,
        [snapshot(directory / "complete.json", "local"), qc_source],
        measurements,
    ).export()


def register(
    directory: Path,
    registry: Path,
    *,
    level: str = "metadata",
    budget: Budget | None = None,
    bigwig_python: Path | None = None,
) -> dict[str, Any]:
    header = load(directory / "complete.json")
    kind = header.get("kind")
    if kind not in KINDS:
        raise ValueError("Unsupported scientific output")
    manifest = verify_output(directory, kind)
    value = record(
        "scatac_output",
        {
            "location": str(directory.resolve()),
            "output_kind": kind,
            "manifest_version": manifest["version"],
            "manifest": manifest,
            "review_status": "UNREVIEWED",
            "model_ready": False,
        },
        identity("scatac-output", manifest["version"]),
        version=5 if kind == "scatac-loader-validation" else 4,
    )
    store.initialize(registry)
    projected = None
    checked = None
    if kind == "scatac-group":
        projected = projection(directory, manifest)
        checked = bundle([projected], level=level, budget=budget, bigwig_python=bigwig_python)
    with store.write(registry) as db:
        store.put(db, value)
        if checked is not None:
            store.import_bundle_db(db, checked)
    return {
        "record": value["version"],
        "manifest": manifest["version"],
        "review_status": "UNREVIEWED",
        "model_ready": False,
        "dataset": projected["id"] if projected else None,
        "validation": checked["data"]["validations"][0] if checked else None,
    }
