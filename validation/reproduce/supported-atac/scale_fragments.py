"""Measure fragment selection on coordinate-disjoint synthetic template copies.

Run in the installed genesis_tools environment. Inputs are the marked BAM and
library JSON retained by validate-atac. This fixture is not biological data.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import pysam
from genesis_tools.atac.inputs import digest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bam", type=Path)
    parser.add_argument("policy", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--copies", nargs="+", type=int, default=[1, 10, 40])
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    policy = json.loads(args.policy.read_text())
    (output / "policy.json").write_text(json.dumps(policy))
    for copies in args.copies:
        if copies <= 0:
            raise ValueError("Copy counts must be positive")
        started = time.monotonic()
        path = output / f"{copies}.bam"
        with pysam.AlignmentFile(str(args.bam), "rb") as source:
            header = source.header.to_dict()
        if header["SQ"][0]["LN"] != 2000000:
            raise ValueError("Expected the deterministic 2 Mb synthetic reference")
        header["HD"]["SO"] = "unsorted"
        header["SQ"][0]["LN"] = 2000000 + copies * 3000000
        with pysam.AlignmentFile(str(path), "wb", header=header) as target:
            for repeat in range(copies):
                with pysam.AlignmentFile(str(args.bam), "rb") as source:
                    for read in source:
                        read.query_name = f"{repeat:04d}_" + read.query_name
                        if read.reference_id == 0:
                            read.reference_start += repeat * 3000000
                        if read.next_reference_id == 0:
                            read.next_reference_start += repeat * 3000000
                        target.write(read)
        script = (
            "from pathlib import Path;import json,sys;"
            "from genesis_tools.atac.fragments import select;"
            "select(Path(sys.argv[1]),json.loads(Path(sys.argv[2]).read_text()),Path(sys.argv[3]))"
        )
        command = [
            "/usr/bin/time",
            "-v",
            "-o",
            str(output / f"{copies}.time.txt"),
            sys.executable,
            "-c",
            script,
            str(path),
            str(output / "policy.json"),
            str(output / f"output-{copies}"),
        ]
        record = {
            "command": command,
            "input_sha256": digest(path),
            "source_sha256": digest(args.bam),
            "copies": copies,
            "generation_seconds": time.monotonic() - started,
        }
        with (output / f"{copies}.stdout").open("w") as stdout:
            with (output / f"{copies}.stderr").open("w") as stderr:
                result = subprocess.run(command, stdout=stdout, stderr=stderr)
        record["exit_status"] = result.returncode
        (output / f"{copies}.command.json").write_text(json.dumps(record, indent=2) + "\n")
        result.check_returncode()
        metrics = json.loads((output / f"output-{copies}/metrics.json").read_text())
        assert metrics["counts"]["total_templates"] == 32000 * copies
        assert metrics["counts"]["usable_fragments"] == 31557 * copies
        print(copies, metrics["counts"]["usable_fragments"], flush=True)


if __name__ == "__main__":
    main()
