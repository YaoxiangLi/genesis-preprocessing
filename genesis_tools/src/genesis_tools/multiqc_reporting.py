"""Aggregate Genesis QC with explicit identities and a checked parsed-data contract."""

from __future__ import annotations

import argparse
import base64
import csv
import gzip
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import uuid
import zipfile
from pathlib import Path
from typing import Any

IDENTIFIER = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*")
RAW_KEYS = {
    "fastqc": "multiqc_fastqc",
    "stats": "multiqc_samtools_stats",
    "flagstat": "multiqc_samtools_flagstat",
    "idxstats": "multiqc_samtools_idxstats",
}


def dump(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n")


def inventory(
    manifest: dict[str, Any],
    inputs: Path,
) -> tuple[dict[str, list[str]], dict[str, dict[str, str]], list[dict[str, str]]]:
    """Require one source per identity before MultiQC can overwrite anything."""
    expected: dict[str, list[str]] = {key: [] for key in RAW_KEYS}
    metadata: dict[str, dict[str, str]] = {}
    sources: list[dict[str, str]] = []
    paths: dict[str, Path] = {}
    for path in sorted(inputs.rglob("*")):
        if not path.is_file():
            continue
        if path.name in paths:
            raise ValueError(f"Duplicate input basename: {path.name}")
        paths[path.name] = path
    samples = sorted(manifest["samples"], key=lambda sample: sample["id"])
    if not samples:
        raise ValueError("No samples for MultiQC")
    for sample in samples:
        name = sample["id"]
        if not IDENTIFIER.fullmatch(name) or name in metadata:
            raise ValueError(f"Unsafe or duplicate sample ID: {name}")
        if sample["layout"] not in ("SE", "PE"):
            raise ValueError(f"Invalid layout: {name}")
        meta_path = paths.get(f"{name}.metadata.tsv")
        if meta_path is None:
            raise ValueError(f"Missing metadata: {name}")
        with meta_path.open() as stream:
            rows = list(csv.DictReader(stream, delimiter="\t"))
        if len(rows) != 1 or any(
            rows[0].get(key) != sample[value]
            for key, value in (
                ("sample_id", "id"),
                ("species", "species"),
                ("reference_fasta", "reference_fasta"),
                ("layout", "layout"),
            )
        ):
            raise ValueError(f"Metadata identity mismatch: {name}")
        metadata[name] = {
            "species": sample["species"],
            "reference_id": sample["ref_id"],
            "layout": sample["layout"],
            "control": sample["control"],
        }
        required: list[tuple[str, str, str]] = [
            ("stats", f"{name}.qc.report.main.stats.txt", f"{name}.qc.report.main.stats.txt"),
            ("stats", f"{name}.qc.report.read1.stats.txt", f"{name}.qc.report.read1.stats.txt"),
            ("flagstat", f"{name}.qc.report.flagstat.txt", f"{name}.qc.report.flagstat.txt"),
            ("idxstats", f"{name}.qc.report.idxstats.tsv", f"{name}.qc.report.idxstats.tsv"),
        ]
        for mate in ("read1", "read2") if sample["layout"] == "PE" else ("read1",):
            required.append(("fastqc", f"{name}.{mate}_fastqc.zip", f"{name}.{mate}.fastq.gz"))
        for kind, filename, identity in required:
            path = paths.get(filename)
            if path is None or path.stat().st_size == 0:
                raise ValueError(f"Missing or empty required {kind} report: {filename}")
            if identity in expected[kind]:
                raise ValueError(f"Duplicate {kind} identity: {identity}")
            if kind == "fastqc":
                with zipfile.ZipFile(path) as archive:
                    if archive.testzip() is not None:
                        raise ValueError(f"Corrupt FastQC ZIP: {filename}")
                    reports = [
                        key for key in archive.namelist() if key.endswith("/fastqc_data.txt")
                    ]
                    if len(reports) != 1:
                        raise ValueError(f"Expected one FastQC data file: {filename}")
                    contents = archive.read(reports[0]).decode()
                    names = re.findall(r"^Filename\t(.+)$", contents, re.MULTILINE)
                    if names != [identity]:
                        raise ValueError(f"FastQC internal identity mismatch: {filename}")
            expected[kind].append(identity)
            sources.append(
                {
                    "sample": name,
                    "kind": kind,
                    "identity": identity,
                    "filename": filename,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
    return expected, metadata, sources


def verify_parsed(data: Path, expected: dict[str, list[str]]) -> dict[str, Any]:
    """Fail even when MultiQC exits zero if a required module/sample was lost."""
    parsed = json.loads((data / "multiqc_data.json").read_text())
    raw = parsed.get("report_saved_raw_data", {})
    for kind, key in RAW_KEYS.items():
        actual = raw.get(key, {})
        if set(actual) != set(expected[kind]):
            raise ValueError(
                f"Parsed {kind} sample mismatch: expected {sorted(expected[kind])}, "
                f"found {sorted(actual)}"
            )
        if any(not values for values in actual.values()):
            raise ValueError(f"Empty parsed {kind} metrics")
    return raw


def canonicalize_html(path: Path, context: object) -> dict[str, str]:
    """Normalize only v1.35 renderer entropy; retain native timing in MultiQC JSON."""
    text = path.read_text()
    pattern = r'(<script type="text/plain" id="mqc_compressed_plotdata">)([^<]+)(</script>)'
    matches = list(re.finditer(pattern, text))
    if len(matches) != 1:
        raise ValueError("Expected one MultiQC compressed plot payload")
    payload = gzip.decompress(base64.b64decode(matches[0][2]))
    encoded = base64.b64encode(gzip.compress(payload, mtime=0)).decode()
    text = text[: matches[0].start(2)] + encoded + text[matches[0].end(2) :]
    digest = hashlib.sha256(json.dumps(context, sort_keys=True).encode() + payload).hexdigest()
    for pattern, replacement in (
        (r'reportUuid = "[^"]+";', f'reportUuid = "{uuid.uuid5(uuid.NAMESPACE_URL, digest)}";'),
        (
            r'configCreationDate = "[^"]+";',
            'configCreationDate = "Recorded in multiqc_data/multiqc_data.json";',
        ),
    ):
        text, count = re.subn(pattern, replacement, text)
        if count != 1:
            raise ValueError("Unsupported MultiQC HTML metadata layout")
    path.write_text(text)
    return {
        "plot_payload_sha256": hashlib.sha256(payload).hexdigest(),
        "html_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def aggregate(manifest_path: Path, inputs: Path, config: Path, output: Path) -> None:
    manifest = json.loads(manifest_path.read_text())
    expected, metadata, sources = inventory(manifest, inputs)
    # Scan only explicitly identified reports. Preserve their original filenames and contents.
    scan = Path("multiqc_scan")
    scan.mkdir()
    for source in sources:
        matches = list(inputs.rglob(source["filename"]))
        if len(matches) != 1:
            raise ValueError(f"Ambiguous input path: {source['filename']}")
        shutil.copyfile(matches[0], scan / source["filename"])
    custom = {
        "id": "genesis_metadata",
        "section_name": "Genesis metadata",
        "description": "Library identities and control associations; no biological QC thresholds.",
        "plot_type": "table",
        "pconfig": {"id": "genesis_metadata", "title": "Genesis metadata"},
        "headers": {
            key: {"title": title, "scale": False}
            for key, title in (
                ("species", "Species"),
                ("reference_id", "Reference ID"),
                ("layout", "Layout"),
                ("control", "Control sample"),
            )
        },
        "data": metadata,
    }
    dump(scan / "genesis_metadata_mqc.json", custom)
    run = manifest["run"]
    header = {
        "title": "Genesis QC: " + str(run["name"]),
        "report_header_info": [
            {"Run": html.escape(str(run["name"]))},
            {"Pipeline Git SHA": html.escape(str(run["git_sha"]))},
            {"Pipeline version": html.escape(str(run["pipeline_version"]))},
            {"Source tree": html.escape(str(run["source_status"]))},
        ],
    }
    dump(Path("multiqc_run_config.json"), header)
    environment = {**os.environ, "XDG_CACHE_HOME": str(Path(".cache").resolve())}
    command = [
        "multiqc",
        str(scan),
        "--config",
        str(config),
        "--config",
        "multiqc_run_config.json",
        "--filename",
        "multiqc_report.html",
        "--outdir",
        str(output),
    ]
    subprocess.run(command, env=environment, check=True)
    data = output / "multiqc_data"
    raw = verify_parsed(data, expected)
    if set(raw.get("multiqc_genesis_metadata", {})) != set(metadata):
        raise ValueError("Genesis metadata missing from parsed report")
    report = output / "multiqc_report.html"
    if not report.is_file() or report.stat().st_size == 0:
        raise ValueError("MultiQC HTML report is missing")
    canonical = canonicalize_html(
        report,
        {
            "run": run,
            "metadata": metadata,
            "sources": sources,
            "config_sha256": hashlib.sha256(config.read_bytes()).hexdigest(),
        },
    )
    # Keep a small explicit per-parser export as well as all native MultiQC data.
    for kind, key in RAW_KEYS.items():
        dump(data / f"genesis_{kind}.json", raw[key])
    dump(
        data / "genesis_provenance.json",
        {
            **manifest,
            "sources": sources,
            "expected": expected,
            "html_canonicalization": canonical,
            "spp_aggregation": "DEFERRED: native parser cannot handle Genesis NA fallback",
            "config_sha256": hashlib.sha256(config.read_bytes()).hexdigest(),
            "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    )
    shutil.copyfile(config, data / "genesis_multiqc_config.yaml")
    shutil.copyfile(scan / "genesis_metadata_mqc.json", data / "genesis_metadata_mqc.json")
    print(
        "Genesis MultiQC contract verified: " + json.dumps({k: len(v) for k, v in expected.items()})
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    aggregate(args.manifest, args.inputs, args.config, args.output)


if __name__ == "__main__":
    main()
