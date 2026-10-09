"""Known-answer ATAC checks; opt-in real-tool fresh/resume regression."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docker", action="store_true")
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args()
    command(str(ROOT / "scripts/run-atac-prototype.sh"), "--help")
    for name in ("verify_metrics.py", "verify_parameters.py"):
        command(sys.executable, str(ROOT / "experimental/atac" / name))
    if not args.docker:
        return

    from genesis_tools.benchmark.fixture import create
    from genesis_tools.benchmark.runner import run
    from genesis_tools.benchmark.spec import load

    base = ROOT / "tests/.runs"
    base.mkdir(exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix="atac-", dir=base))
    print(f"Retained ATAC validation: {folder}", flush=True)
    manifest = create(folder / "fixture", assay="bulk-ATAC", adapter="genesis-atac", checkout=ROOT)
    inputs = {str(p): digest(p) for p in (folder / "fixture").iterdir() if p.is_file()}
    out = folder / "run"
    plan = load(manifest)
    assert not plan["blockers"], plan["blockers"]
    run(plan, out)
    workflow = out / "workflows/r1-pe_treatment"
    published = workflow / "published"
    command(
        sys.executable,
        str(ROOT / "experimental/atac/verify_outputs.py"),
        str(published),
        "plastid",
        "mitochondria",
    )
    trace = workflow / "trace.tsv"
    fresh = list(csv.DictReader(trace.open(), delimiter="\t"))
    assert len(fresh) == 8 and all(r["status"] == "COMPLETED" for r in fresh)
    shutil.copy2(trace, folder / "fresh-trace.tsv")
    before = {str(p): digest(p) for p in published.rglob("*") if p.is_file()}
    run(load(manifest), out, resume=True)
    resumed = list(csv.DictReader(trace.open(), delimiter="\t"))
    assert len(resumed) == 8 and all(r["status"] == "CACHED" for r in resumed)
    assert before == {str(p): digest(p) for p in published.rglob("*") if p.is_file()}
    assert all(digest(Path(p)) == value for p, value in inputs.items())
    result = {
        "pass": True,
        "fresh_tasks": len(fresh),
        "cached_tasks": len(resumed),
        "input_sha256": inputs,
        "published_sha256": before,
    }
    (folder / "validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print("PASS: eight tasks cached; published outputs and raw input bytes unchanged")
    if not args.keep:
        shutil.rmtree(folder)


if __name__ == "__main__":
    main()
