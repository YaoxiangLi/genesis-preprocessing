"""Actual data-loader acceptance for both pinned downstream model implementations."""

from __future__ import annotations

import argparse
from pathlib import Path

from genesis_tools.contracts.records import dump
from genesis_tools.scatac import loaders, model, registry, release
from genesis_tools.scatac.common import verify_output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--references", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    bundles = {}
    for target, sha in model.MODELS.items():
        config = {
            "schema_version": 1,
            "target": target,
            "model_sha": sha,
            "folds": {"train": ["chr1"], "validation": ["chr2"], "test": ["chr3"]},
            "input_window": 2114,
            "output_window": 1000,
            "max_jitter": 0,
            "controls": None,
            "background_method": "gc-matched-genome-tiles-v1",
            "background_seed": 7,
            "bias_model": {"status": "REQUIRED_BEFORE_TRAINING", "plant_model": None}
            if target == "chrombpnet"
            else None,
        }
        path = args.output / (target + ".json")
        dump(path, config)
        bundle = args.output / target
        model.export(args.input, path, bundle)
        assert model.export(args.input, path, bundle, resume=True)["cached"]
        validation = args.output / (target + "-loader")
        result = loaders.run(bundle, args.references / target, validation)
        assert result["manifest"]["data"]["loader_test"] == "PASS"
        assert loaders.run(bundle, args.references / target, validation, resume=True)["cached"]
        assert model.validate(bundle)["context_windows"] == "PASS"
        bundles[target] = {"bundle": str(bundle.resolve()), "validation": str(validation.resolve())}
    catalog = args.output / "catalog"
    projected = registry.register(
        args.input,
        catalog,
        level="full",
        bigwig_python=(
            Path(__file__).resolve().parents[1]
            / "validation/environments/scatac-loaders/.venv/bin/python"
        ),
    )
    assert projected["validation"]["data"]["complete"]
    assert all(f["data"]["result"] == "PASS" for f in projected["validation"]["data"]["findings"])
    config_path = args.output / "release.json"
    dump(
        config_path,
        {
            "schema_version": 1,
            "required_species": ["Synthetic fixture"],
            "groups": [{"products": str(args.input.resolve()), "models": bundles}],
        },
    )
    released = release.run(config_path, catalog, args.output / "candidate")
    assert not released["data"]["model_ready"]
    assert released["data"]["release_issues"]  # One replicate is not a two-replicate pilot.
    verify_output(args.output / "candidate", "scatac-release")
    print(
        "PASS: real Cherimoya and ChromBPNet loaders; "
        "tensor shapes and per-base source counts; stable resume"
    )


if __name__ == "__main__":
    main()
