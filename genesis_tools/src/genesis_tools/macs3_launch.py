#!/usr/bin/env python3
"""Run MACS3 within a Linux CPU allocation; usable without installing Genesis."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import sys
import sysconfig
from pathlib import Path

SOURCE_REVISION = "22eb40f7b51f5b20b635614ca0b1759dc5398c5c"
SOURCE_SHA256 = "791cc59bd1daa290ccaa53f2552301b293db8cff44ddaa208ef6b8a1a7fb7857"
THREAD_VARIABLES = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "BLIS_NUM_THREADS",
)


def constrain(cpus: int) -> list[int]:
    if cpus < 1:
        raise ValueError("CPU allocation must be positive")
    if not hasattr(os, "sched_getaffinity"):
        raise ValueError("Bounded MACS3 execution requires Linux CPU affinity")
    allowed = sorted(os.sched_getaffinity(0))
    # Spread independent local tasks within the inherited allocation. This is
    # not a reservation; a scheduler-provided cpuset remains the outer boundary.
    offset = os.getpid() % len(allowed) if allowed else 0
    selected = sorted((allowed[offset:] + allowed[:offset])[:cpus])
    if not selected:
        raise ValueError("Empty CPU affinity mask")
    os.sched_setaffinity(0, selected)
    for name in THREAD_VARIABLES:
        os.environ[name] = "1"
    return selected


def executable() -> str:
    path = Path(sysconfig.get_path("scripts")) / "macs3"
    if not path.is_file():
        raise ValueError("macs3 is not installed alongside this Python environment")
    return str(path)


def identity() -> dict[str, object]:
    distribution = importlib.metadata.distribution("MACS3")
    direct = json.loads(distribution.read_text("direct_url.json") or "{}")
    digest = direct.get("archive_info", {}).get("hashes", {}).get("sha256")
    revision = direct.get("vcs_info", {}).get("commit_id")
    return {
        "version": distribution.version,
        "source_revision": SOURCE_REVISION if digest == SOURCE_SHA256 else revision,
        "source_archive_sha256": digest,
        "launcher_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpus", type=int, required=True)
    parser.add_argument("--receipt", type=Path, default=Path("macs3.runtime.json"))
    parser.add_argument("--require-source", help="Require this exact upstream Git revision")
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    arguments = args.arguments
    if arguments[:1] == ["--"]:
        arguments = arguments[1:]
    if not arguments:
        parser.error("MACS3 arguments are required after --")
    try:
        program = executable()
        observed = identity()
        if args.require_source and observed["source_revision"] != args.require_source:
            raise ValueError("Installed MACS3 source revision does not match the required revision")
        if not hasattr(os, "sched_getaffinity") and observed["source_revision"] is None:
            # Preserve released-package execution on non-Linux hosts. This does not
            # certify bounded execution of the new threaded source build there.
            if args.cpus < 1:
                raise ValueError("CPU allocation must be positive")
            selected = []
        else:
            selected = constrain(args.cpus)
        with args.receipt.open("x") as stream:
            json.dump(
                observed
                | {
                    "requested_cpus": args.cpus,
                    "affinity": selected,
                    "native_library_threads": 1 if selected else None,
                    "resource_enforcement": "PASS" if selected else "NOT_ASSESSED",
                },
                stream,
                indent=2,
            )
            stream.write("\n")
        os.execvpe(program, [program, *arguments], os.environ)
    except (OSError, ValueError, importlib.metadata.PackageNotFoundError) as error:
        print(f"MACS3 launch failed: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
