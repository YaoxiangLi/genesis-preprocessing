"""Keep compact method evidence; optionally remove completed, reproducible work.

The archive includes measurements, peaks, command logs, task hashes and figures.
It excludes sequencing reads, BAMs and reference indexes. Pruning is explicit and
prevents execution resume; reproduce that experiment in a new result directory.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shutil
import tarfile
from pathlib import Path
from typing import Any

from genesis_tools.benchmark.spec import identifier, sha256


def archive(source: Path, out: Path, *, prune_work: bool = False) -> dict[str, Any]:
    source, out = source.resolve(), out.resolve()
    if out.is_relative_to(source) or out.exists():
        raise ValueError("Choose a new archive directory outside the experiment")
    if (source / "retention.json").exists():
        raise ValueError("Work has a retention record; use its existing verified archive")
    lock = source / ".running"
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(descriptor, "w") as stream:
            stream.write(f"archive pid={os.getpid()}\n")
        plan = json.loads((source / "experiment.json").read_text())
        result = json.loads((source / "results.json").read_text())
        if plan["spec"]["adapter"] != "methods":
            raise ValueError("This archive recipe is for native method experiments")
        if prune_work and result["status"] != "COMPLETE":
            raise ValueError("Keep work from incomplete experiments for diagnosis")
        work = {source / "indexes"}
        for case in result.get("results", []):
            identifier(case["arm"])
            rep = case["repetition"]
            if type(rep) is not int or rep < 1:
                raise ValueError("Invalid repetition")
            work.add(source / f"{case['arm']}-r{rep}")
        for folder in work:
            if folder.is_symlink():
                raise ValueError("Work must not be a symlink")
            if any(
                Path(a["path"]).resolve().is_relative_to(folder) for a in plan["assets"].values()
            ):
                raise ValueError("An input lies inside work selected for pruning")
        selected = []
        for path in sorted(source.rglob("*")):
            if not path.is_file() or path.is_symlink() or path == lock:
                continue
            # Genrich keeps a name-sorted BAM beside its peak output. Directory
            # membership alone must not include that large sequencing artifact.
            if path.suffix in {".bam", ".bai", ".cram", ".crai"} or ".fastq" in path.name:
                continue
            relative = path.relative_to(source)
            if (
                path.parent == source
                or relative.parts[0] in {"commands", "invocations", "figures"}
                or path.suffix == ".json"
                or "peaks" in relative.parts[:-1]
                or path.name == "bedtools.tsv"
            ):
                selected.append(path)
        manifest = {
            str(p.relative_to(source)): {"sha256": sha256(p), "bytes": p.stat().st_size}
            for p in selected
        }
        out.mkdir(parents=True)
        packed = out / "evidence.tar.gz"
        with packed.open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w|") as tar:
                for path in selected:
                    info = tar.gettarinfo(str(path), arcname=str(path.relative_to(source)))
                    info.uid = info.gid = info.mtime = 0
                    info.uname = info.gname = ""
                    with path.open("rb") as stream:
                        tar.addfile(info, stream)
        # Verify all archived bytes before any removal, without extracting paths.
        verified = set()
        with tarfile.open(packed, "r:gz") as tar:
            for item in tar:
                stream = tar.extractfile(item)
                if stream is None or item.name not in manifest:
                    raise ValueError("Archive contains an unexpected member")
                with stream:
                    digest = hashlib.sha256()
                    while block := stream.read(1024 * 1024):
                        digest.update(block)
                    checksum = digest.hexdigest()
                if checksum != manifest[item.name]["sha256"]:
                    raise ValueError("Archive verification failed")
                verified.add(item.name)
        if verified != set(manifest):
            raise ValueError("Archive omitted evidence")
        missing_tables = []
        for name in ("metrics.tsv", "processing.tsv", "resources.tsv", "library-qc.tsv"):
            if (source / name).is_file():
                shutil.copyfile(source / name, out / name)
            else:
                missing_tables.append(name)
        if (source / "figures").is_dir():
            shutil.copytree(source / "figures", out / "figures")
        record: dict[str, Any] = {
            "schema_version": 1,
            "experiment_id": plan["experiment_id"],
            "source": str(source),
            "status": result["status"],
            "script_sha256": sha256(Path(__file__)),
            "archive_sha256": sha256(packed),
            "archive_bytes": packed.stat().st_size,
            "members": manifest,
            "pruned_work": [],
            "prune_status": "NOT_REQUESTED",
            "missing_tables": missing_tables,
            "retention": (
                "Inputs stay at their original locations; BAMs/indexes are not in this archive"
            ),
        }

        def save_record() -> None:
            for path in (out / "manifest.json", source / "retention.json"):
                partial = path.with_suffix(path.suffix + ".partial")
                partial.write_text(json.dumps(record, indent=2) + "\n")
                partial.replace(path)

        if prune_work:
            # The runner uses this same exclusive lock. Recheck identities before
            # pruning, even though cooperating execution cannot write meanwhile.
            for name in ("experiment.json", "results.json"):
                if sha256(source / name) != manifest[name]["sha256"]:
                    raise ValueError("Experiment changed during archiving")
            record["prune_status"] = "PRUNING"
            record["planned_pruning"] = [str(p) for p in sorted(work) if p.exists()]
            record["retention"] += (
                "; listed work intentionally pruned; execution resume unavailable"
            )
            save_record()
            for folder in sorted(work):
                if folder.exists():
                    record["current_pruning"] = str(folder)
                    save_record()
                    shutil.rmtree(folder)
                    record["pruned_work"].append(str(folder))
                    save_record()
            record["prune_status"] = "PRUNED"
            record["current_pruning"] = None
            save_record()
        (out / "manifest.json").write_text(json.dumps(record, indent=2) + "\n")
        return record
    finally:
        lock.unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--prune-work", action="store_true")
    args = parser.parse_args()
    record = archive(args.source, args.out, prune_work=args.prune_work)
    print(record["archive_sha256"], record["archive_bytes"], "bytes")
