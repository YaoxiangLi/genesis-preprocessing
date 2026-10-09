"""Run validated paired-end plant ATAC libraries with a pinned Nextflow workflow."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

from .inputs import digest, libraries, references
from .summary import summarize

ROOT = Path(__file__).resolve().parents[4]


def write_stable(path: Path, value: object) -> None:
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if not path.exists() or path.read_text() != text:
        path.write_text(text)


def prepare(sheet: Path, registry: Path, run_dir: Path) -> Path:
    refs = references(registry)
    records = libraries(sheet, refs)
    run_dir.mkdir(parents=True, exist_ok=True)
    inputs = run_dir / "inputs"
    inputs.mkdir(exist_ok=True)
    for library in records:
        path = inputs / f"{library['library_id']}.json"
        library["manifest"] = str(path)
    value = {
        "schema_version": 1,
        "libraries": records,
        "sample_sheet_sha256": digest(sheet),
        "registry_sha256": digest(registry),
    }
    manifest = run_dir / "manifest.json"
    if manifest.exists() and json.loads(manifest.read_text()) != value:
        raise ValueError(
            "Run inputs changed. Choose a new run directory to preserve the previous results"
        )
    for library in records:
        write_stable(Path(library["manifest"]), library)
    write_stable(manifest, value)
    return manifest


def execute(
    sheet: Path,
    registry: Path,
    out: Path,
    profile: str = "local,docker",
    config: Path | None = None,
    resume: bool = False,
) -> int:
    sheet, registry, out = sheet.resolve(), registry.resolve(), out.resolve()
    manifest = prepare(sheet, registry, out)
    source = ROOT / "genesis_tools/src"
    staged = out / "inputs/code"
    wanted = set()
    for original in sorted(source.rglob("*")):
        if not original.is_file() or "__pycache__" in original.parts:
            continue
        relative = original.relative_to(source)
        wanted.add(relative)
        target = staged / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.read_bytes() != original.read_bytes():
            target.write_bytes(original.read_bytes())
    for target in staged.rglob("*"):
        if target.is_file() and target.relative_to(staged) not in wanted:
            target.unlink()
    args = ["nextflow", "-C", str(ROOT / "conf/atac.config")]
    if config:
        args[2] += "," + str(config.resolve())
    args += [
        "run",
        str(ROOT / "workflows/atac.nf"),
        "-profile",
        profile,
        "--manifest",
        str(manifest),
        "--source",
        str(staged),
        "--outdir",
        str(out / "output"),
        "-w",
        str(out / "work"),
    ]
    if resume:
        args.append("-resume")
    provenance = {
        "git_sha": subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
        ).strip(),
        "manifest_sha256": digest(manifest),
        "profile": profile,
        "config_sha256": digest(config.resolve()) if config else None,
        "containers": json.loads((ROOT / "conf/atac-images.json").read_text()),
        "plant_thresholds": "UNSPECIFIED",
        "source_sha256": {
            str(p.relative_to(ROOT)): digest(p)
            for folder in ("workflows", "modules/atac", "conf", "genesis_tools/src")
            for p in sorted((ROOT / folder).rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts
        },
    }
    provenance["working_tree_dirty"] = bool(
        subprocess.check_output(
            ["git", "-C", str(ROOT), "status", "--porcelain"], text=True
        ).strip()
    )
    history = out / "invocations"
    history.mkdir(exist_ok=True)
    stamp = str(time.time_ns())
    provenance["command"] = args
    provenance["started_unix"] = time.time()
    write_stable(history / f"{stamp}.json", provenance)
    result = subprocess.run(args, cwd=out, check=False).returncode
    provenance["exit_code"] = result
    provenance["elapsed_seconds"] = time.time() - provenance["started_unix"]
    write_stable(history / f"{stamp}.json", provenance)
    write_stable(out / "provenance.json", provenance)
    if result == 0:
        summarize(json.loads(manifest.read_text()), out / "output")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("samples", type=Path)
    parser.add_argument("--references", type=Path, required=True)
    parser.add_argument("--outdir", type=Path)
    parser.add_argument("--profile", default="local,docker")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--resume", "-resume", action="store_true")
    args = parser.parse_args()
    try:
        raise SystemExit(
            execute(
                args.samples,
                args.references,
                args.outdir or ROOT / "workspace" / args.samples.stem,
                args.profile,
                args.config,
                args.resume,
            )
        )
    except (ValueError, OSError, KeyError) as error:
        parser.exit(2, f"Cannot start ATAC: {error}\n")


if __name__ == "__main__":
    main()
