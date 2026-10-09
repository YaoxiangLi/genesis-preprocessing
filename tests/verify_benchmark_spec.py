"""Offline experiment planning and cache-integrity checks."""

from __future__ import annotations

import copy
import json
import tempfile
from collections.abc import Callable
from pathlib import Path

from genesis_tools.benchmark.runtime import Runtime, fetch
from genesis_tools.benchmark.spec import load, sha256
from genesis_tools.benchmark.workflows import verify_effective_commands

TOML = """schema_version = 1
id = "tiny"
assay = "DAP-seq"
adapter = "postalign"
dataset = "dataset.json"
baseline = "mapq0-retained"
comparison = "matched-stage"
seed = 60141
[parameters]
mapq = [0, 10, 30]
duplicates = ["retained"]
keep_dup = "1"
qvalue = 0.05
spp = false
quantify = false
[limits]
cpus = 2
memory_gb = 4
seconds = 1200
disk_bytes = 2000000000
download_bytes = 0
max_arms = 9
"""


def rejects(function: Callable[[], object]) -> None:
    try:
        function()
    except ValueError:
        return
    raise AssertionError("Expected rejection")


def main() -> None:
    policy = {
        "adapter": "nfcore-atac",
        "parameters": {"qvalue": 0.01, "keep_dup": "all", "mapq": [1]},
        "workflow": {"parameters": {"narrow_peak": True}},
    }
    commands = {
        "A:MACS2_CALLPEAK (lib)": {"command": "macs2 callpeak -q 0.01 --keep-dup all -f BAMPE"},
        "A:MULTIQC_CUSTOM_PEAKS (lib)": {"command": "irrelevant"},
        "A:BAMTOOLS_FILTER (lib)": {"command": "samtools view -q 1 -F 1024"},
    }
    verify_effective_commands(policy, commands)
    wrong = copy.deepcopy(commands)
    wrong["A:MACS2_CALLPEAK (lib)"]["command"] += " --broad"
    rejects(lambda: verify_effective_commands(policy, wrong))
    wrong["A:MACS2_CALLPEAK (lib)"]["command"] = "macs2 callpeak -q 0.05 --keep-dup all -f BAMPE"
    rejects(lambda: verify_effective_commands(policy, wrong))
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        (root / "ref.fa").write_text(">chr1\n" + "A" * 1000 + "\n")
        (root / "sizes").write_text("chr1\t1000\n")
        (root / "bam").write_bytes(b"checksum fixture; not an executable BAM")
        dataset = {
            "schema_version": 1,
            "id": "known",
            "assay": "DAP-seq",
            "synthetic": True,
            "status": "READY",
            "reference": {
                "id": "toy",
                "species": "synthetic",
                "assembly": "toy1",
                "cultivar": "NA",
                "fasta": "ref",
                "fasta_content_sha256": sha256(root / "ref.fa"),
                "chrom_sizes": "sizes",
                "genome_size": 1000,
                "mitochondrial": [],
                "plastid": [],
            },
            "assets": {
                name: {"path": path, "sha256": sha256(root / path)}
                for name, path in (
                    ("ref", "ref.fa"),
                    ("sizes", "sizes"),
                    ("bam", "bam"),
                )
            },
            "libraries": [
                {
                    "id": "one",
                    "layout": "SE",
                    "control": None,
                    "raw_templates": 1,
                    "biological_replicate": "synthetic",
                    "bam": "bam",
                }
            ],
        }
        manifest = root / "test.toml"
        manifest.write_text(TOML)
        datafile = root / "dataset.json"
        datafile.write_text(json.dumps(dataset))
        plan = load(manifest)
        assert plan["status"] == "READY" and len(plan["arms"]) == 3
        original_id = plan["experiment_id"]
        manifest.write_text(TOML.replace("[0, 10, 30]", "[0, 20, 30]"))
        assert load(manifest)["experiment_id"] != original_id
        manifest.write_text(TOML + "\nunknown = true\n")
        rejects(lambda: load(manifest))
        manifest.write_text(TOML.replace("max_arms = 9", "max_arms = 2"))
        rejects(lambda: load(manifest))
        manifest.write_text(TOML)
        collision = copy.deepcopy(dataset)
        libraries = collision["libraries"]
        assert isinstance(libraries, list)
        libraries.append(libraries[0].copy())
        datafile.write_text(json.dumps(collision))
        rejects(lambda: load(manifest))
        datafile.write_text(json.dumps(dataset))
        (root / "ref.fa").write_text(">chr1\nC\n")
        rejects(lambda: load(manifest))
        (root / "ref.fa").write_text(">chr1\n" + "A" * 1000 + "\n")
        out = root / "results"
        runtime = Runtime(load(manifest), out, resume=False)
        task = out / "task"
        task.mkdir()
        artifact = task / "metric.json"
        artifact.write_text("{}")
        runtime.seal(task, [root / "ref.fa"], [artifact], {"policy": "explicit"})
        resumed = Runtime(load(manifest), out, resume=True)
        assert resumed.cached(task, [root / "ref.fa"], {"policy": "explicit"})
        artifact.write_text('{"changed":true}')
        assert not resumed.cached(task, [root / "ref.fa"], {"policy": "explicit"})
        rejects(lambda: Runtime(load(manifest), out, resume=False))
        dataset["status"] = "NEEDS_REFERENCE"
        dataset["reason"] = "Exact reference missing"
        datafile.write_text(json.dumps(dataset))
        blocked = load(manifest)
        assert blocked["status"] == "BLOCKED"
        rejects(lambda: fetch(blocked))
    print(
        "PASS: strict manifests, identities, collisions, reference checksums and output-aware cache"
    )


if __name__ == "__main__":
    main()
