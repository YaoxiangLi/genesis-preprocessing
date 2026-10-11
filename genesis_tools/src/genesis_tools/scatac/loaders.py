"""Execute the actual pinned model loader with retained logs and content-bound evidence."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from ..contracts.records import dump, fingerprint, load
from .common import complete, digest, publication, software, verify_output

CHROMBPNET_IMAGE = (
    "kundajelab/chrombpnet@sha256:6f41e0f59fc025285645e2cbfd1bb6347431b4e0ab6088804d11843cd6aed169"
)


def run(bundle: Path, model_root: Path, output: Path, *, resume: bool = False) -> dict[str, Any]:
    started = time.monotonic()
    bundle, model_root = bundle.resolve(), model_root.resolve()
    manifest = verify_output(bundle, "scatac-model")
    config = load(bundle / "loader.json")
    sha = subprocess.check_output(
        ["git", "-C", str(model_root), "rev-parse", "HEAD"], text=True
    ).strip()
    if sha != config["model_sha"]:
        raise ValueError("Wrong pinned model revision")
    if subprocess.run(
        ["git", "-C", str(model_root), "diff", "--quiet", "HEAD"], check=False
    ).returncode:
        raise ValueError("Modified model source")
    environment = Path(__file__).resolve().parents[4] / "validation/environments/scatac-loaders"
    runtime = (
        {"container": CHROMBPNET_IMAGE}
        if config["target"] == "chrombpnet"
        else {
            "uv_lock_sha256": digest(environment / "uv.lock"),
            "pyproject_sha256": digest(environment / "pyproject.toml"),
        }
    )
    signature = fingerprint(
        {
            "bundle": manifest["version"],
            "model_sha": sha,
            "software": software("loaders.py", "assets/model_loader.py"),
            "runtime": runtime,
        }
    )
    if resume and output.exists():
        previous = verify_output(output, "scatac-loader-validation")
        if previous["data"]["signature"] != signature:
            raise ValueError("Changed loader validation inputs")
        return {"cached": True, "manifest": previous}
    script = Path(__file__).parent / "assets/model_loader.py"
    with publication(output) as stage:
        if config["target"] == "chrombpnet":
            command = [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--cpus",
                "2",
                "--memory",
                "8g",
                "--user",
                f"{os.getuid()}:{os.getgid()}",
                "-e",
                "PYTHONDONTWRITEBYTECODE=1",
                "-v",
                f"{bundle}:/bundle:ro",
                "-v",
                f"{model_root}:/model:ro",
                "-v",
                f"{script}:/loader.py:ro",
                "-v",
                f"{stage.resolve()}:/result",
                CHROMBPNET_IMAGE,
                "python",
                "/loader.py",
                "--model-root",
                "/model",
                "--bundle",
                "/bundle",
                "--output",
                "/result",
            ]
        else:
            uv = shutil.which("uv")
            if uv is None or not (environment / "uv.lock").is_file():
                raise ValueError(
                    "Use the project Pixi environment and committed loader environment"
                )
            command = [
                uv,
                "run",
                "--frozen",
                "--project",
                str(environment),
                "python",
                str(script),
                "--model-root",
                str(model_root),
                "--bundle",
                str(bundle),
                "--output",
                str(stage),
            ]
        with (stage / "loader.stdout").open("w") as out, (stage / "loader.stderr").open("w") as err:
            result = subprocess.run(
                command,
                stdout=out,
                stderr=err,
                timeout=1800,
                check=False,
                env={**os.environ, "OMP_NUM_THREADS": "2", "OPENBLAS_NUM_THREADS": "2"},
            )
        dump(
            stage / "loader.command.json",
            {
                "argv": command,
                "exit_status": result.returncode,
                "elapsed_seconds": time.monotonic() - started,
            },
        )
        if result.returncode:
            raise ValueError("Actual model loader failed; full logs retained in staging directory")
        evidence = load(stage / "loader-result.json")
        if (
            evidence["status"] != "PASS"
            or evidence["model_sha"] != sha
            or len(evidence["folds"]) != 3
        ):
            raise ValueError("Incomplete model-loader evidence")
        verify_output(bundle, "scatac-model")
        value = complete(
            stage,
            "scatac-loader-validation",
            {
                "signature": signature,
                "bundle_version": manifest["version"],
                "runtime": runtime,
                "loader_test": "PASS",
                "evidence": evidence,
                "scientific_review": "UNREVIEWED",
                "training": "NOT_RUN",
            },
            started,
        )
    return {"cached": False, "manifest": value}
