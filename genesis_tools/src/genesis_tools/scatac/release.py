"""Assemble portable pilot candidates with explicit loader and human-review gates."""

from __future__ import annotations

import contextlib
import re
import shutil
import time
from pathlib import Path
from typing import Any

from ..contracts.records import dump, fingerprint, identity, load
from ..curation.review import CATEGORIES, exclusions, latest, profile, status
from ..registry import store
from .common import checked_asset, complete, digest, publication, verify_output
from .model import MODELS, validate


def source_provenance(config: dict[str, Any], base: Path, stage: Path) -> dict[str, str]:
    """Retain verified library manifests without duplicating the raw fragment libraries."""
    versions = {}
    for library, location in config.get("libraries", {}).items():
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", library):
            raise ValueError("Invalid provenance library identifier")
        directory = (base / location).resolve()
        manifest = verify_output(directory, "scatac-fragments")
        if manifest["data"]["input"]["library"]["library_id"] != library:
            raise ValueError("Provenance library identifier does not match its manifest")
        versions[library] = manifest["version"]
        destination = stage / "provenance" / "libraries" / library
        destination.mkdir(parents=True)
        for name in ("complete.json", "input.json", "source-headers.json", "execution.json"):
            shutil.copyfile(directory / name, destination / name)
    for name, asset in config.get("source_evidence", {}).items():
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", name):
            raise ValueError("Source evidence requires a plain unique filename")
        path = checked_asset(asset, base)
        destination = stage / "provenance" / "sources" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
    dump(stage / "provenance" / "library-versions.json", versions)
    return versions


def run(config_path: Path, registry: Path, output: Path) -> dict[str, Any]:
    started = time.monotonic()
    config = load(config_path)
    if config.get("schema_version") != 1 or not config.get("groups"):
        raise ValueError("A versioned release manifest with explicit groups is required")
    groups, observed, issues = [], {}, []
    seen = set()
    with contextlib.closing(store.connect(registry)) as db, publication(output) as stage:
        library_versions = source_provenance(config, config_path.parent, stage)
        db.execute("BEGIN")
        for item in config["groups"]:
            path = (config_path.parent / item["products"]).resolve()
            parent = verify_output(path, "scatac-group")
            bio = parent["data"]["group"]["identity"]
            key = fingerprint(bio)
            if key in seen:
                raise ValueError("Duplicate pseudobulk in release manifest")
            seen.add(key)
            dataset = identity("pseudobulk", "scatac:" + bio["study_id"], key)
            current = store.current(db, dataset)
            manifest = store.get(db, "manifest", current["manifest"])
            if manifest["data"]["metadata"]["scatac_manifest"] != parent["version"]:
                raise ValueError("Registry points to a different pseudobulk revision")
            state = status(db, dataset)
            reasons = exclusions(db, dataset, profile())
            if not parent["data"]["parents"] or any(
                library_versions.get(library) != version
                for library, version in parent["data"]["parents"].items()
            ):
                reasons.append("Matching source-library provenance is required for delivery")
            if state["structural"] != "PASS":
                reasons.append("Complete structural validation is required for model delivery")
            observed.setdefault(bio["species"], set()).add(
                (bio["study_id"], bio["biological_replicate_id"])
            )
            shutil.copytree(path, stage / "pseudobulk" / key)
            models = []
            if set(item.get("models", {})) != set(MODELS):
                reasons.append("Both model adapters and loader receipts are required")
            for target, paths in item.get("models", {}).items():
                if target not in MODELS:
                    raise ValueError("Unknown model adapter")
                model_path = (config_path.parent / paths["bundle"]).resolve()
                loader_path = (config_path.parent / paths["validation"]).resolve()
                validate(model_path)
                model = verify_output(model_path, "scatac-model")
                loader = verify_output(loader_path, "scatac-loader-validation")
                if (
                    model["data"]["parent"] != parent["version"]
                    or model["data"]["config"]["target"] != target
                ):
                    raise ValueError("Model bundle does not belong to this pseudobulk/adapter")
                if (
                    loader["data"]["bundle_version"] != model["version"]
                    or loader["data"]["loader_test"] != "PASS"
                ):
                    raise ValueError("Missing or stale actual model-loader test")
                shutil.copytree(model_path, stage / "models" / target / key)
                shutil.copytree(loader_path, stage / "provenance" / "loaders" / target / key)
                models.append(
                    {"target": target, "version": model["version"], "loader": loader["version"]}
                )
            groups.append(
                {
                    "id": key,
                    "dataset": dataset,
                    "identity": bio,
                    "parent": parent["version"],
                    "registry_state": state,
                    "decisions": [latest(db, dataset, name) for name in CATEGORIES],
                    "models": models,
                    "exclusions": reasons,
                    "model_ready": not reasons,
                }
            )
        for species in config.get("required_species", []):
            entries = observed.get(species, set())
            if not any(sum(s == study for s, _ in entries) >= 2 for study, _ in entries):
                issues.append(species + ": fewer than two documented biological replicates")
        ready = not issues and all(g["model_ready"] for g in groups)
        dump(stage / "manifest/groups.json", groups)
        dump(stage / "manifest/release-config.json", config)
        dump(stage / "qc/review-status.json", {"groups": groups, "release_issues": issues})
        (stage / "README.md").write_text(
            "# Genesis scATAC pilot\n\n"
            + (
                "Approved model-input release.\n"
                if ready
                else "Review candidate; not approved for model training.\n"
            )
            + "\nEach pseudobulk preserves its biological replicate and source-cell membership. "
            "Model directories contain pinned loader configurations, exact FASTA files, raw "
            "cut-count tracks and disjoint chromosome folds. Do not apply another Tn5 shift. "
            "See manifest/groups.json and qc/review-status.json for acceptance evidence. "
            "Source-library manifests are retained under provenance/libraries; raw library "
            "fragment files are identified by checksum and are not duplicated in this release. "
            "Loader compatibility is distinct from training. ChromBPNet still needs the "
            "bias-model preparation recorded in loader.json; no human bias model is supplied.\n"
        )
        (stage / "checksums.sha256").write_text(
            "".join(
                f"{digest(path)}  {path.relative_to(stage)}\n"
                for path in sorted(stage.rglob("*"))
                if path.is_file()
            )
        )
        result = complete(
            stage,
            "scatac-release",
            {
                "groups": len(groups),
                "model_ready": ready,
                "release_issues": issues,
                "training_validated": False,
                "required_species": config.get("required_species", []),
            },
            started,
        )
    return result
