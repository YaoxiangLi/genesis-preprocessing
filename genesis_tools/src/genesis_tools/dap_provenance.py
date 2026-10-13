"""Assemble DAP run evidence from completed channels (standalone stdlib task driver)."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        data = stream.read(32 * 1024 * 1024 + 1)
    if len(data) > 32 * 1024 * 1024:
        raise ValueError("DAP provenance document exceeds 32 MiB")
    value = json.loads(data)
    if not isinstance(value, dict):
        raise ValueError("Expected a provenance object")
    return value


def assemble(context_path: Path, sheet: Path, output: Path) -> dict[str, Any]:
    context = read_json(context_path)
    with sheet.open() as stream:
        samples = list(csv.DictReader(stream, delimiter="\t"))
    reads = {}
    for path in sorted(Path("reads").glob("*.reads.sha256")):
        for line in path.read_text().splitlines():
            checksum, name = line.split("  ", 1)
            if name in reads:
                raise ValueError("Duplicate input receipt")
            reads[name] = checksum
    inputs = []
    for sample in samples:
        for mate in ("read1", "read2") if sample["read2_url"] != "-" else ("read1",):
            name = f"{sample['sample_id']}.{mate}.fastq.gz"
            inputs.append(
                {
                    "sample_id": sample["sample_id"],
                    "mate": mate,
                    "url": sample[mate + "_url"],
                    "sha256": reads.pop(name),
                    "retention": "work-cache",
                }
            )
    if reads:
        raise ValueError("Input receipts outside the declared sample sheet")
    products = {}
    for relative, staged in context["products"]:
        path = Path(staged)
        for item in sorted(path.rglob("*")) if path.is_dir() else [path]:
            if not item.is_file():
                continue
            name = (
                (Path(relative) / item.relative_to(path)).as_posix() if path.is_dir() else relative
            )
            if name in products:
                raise ValueError("Duplicate published artifact")
            products[name] = {"sha256": sha256(item), "size": item.stat().st_size}
    value = {
        "schema_version": 1,
        "kind": "genesis-dap-run",
        "context": context["context"],
        "sheet_sha256": sha256(sheet),
        "samples": samples,
        "inputs": inputs,
        "references": context["references"],
        "outputs": products,
        "tasks": [read_json(p) for p in sorted(Path("tasks").glob("*.genesis-task.json"))],
    }
    text = json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if len(text.encode()) > 32 * 1024 * 1024:
        raise ValueError("DAP run provenance exceeds 32 MiB")
    temporary = output.with_suffix(".partial")
    temporary.write_text(text)
    temporary.replace(output)
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context", type=Path, required=True)
    parser.add_argument("--sheet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assemble(args.context, args.sheet, args.output)


if __name__ == "__main__":
    main()
