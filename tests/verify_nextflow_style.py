"""Focused, dependency-free checks for the Nextflow/environment style refactor."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from genesis_tools.quantification import finish_quantification, prepare_quantification

ROOT = Path(__file__).resolve().parents[1]

FAKE_COMMAND = r"""
import json
import os
from pathlib import Path
import sys

name = Path(sys.argv[0]).name
args = sys.argv[1:]
with Path(os.environ["BUILD_LOG"]).open("a") as stream:
    stream.write(json.dumps([name, args]) + "\n")
if name == "git":
    print("0.1.0")
elif name == "pixi":
    if args[0] == "init":
        folder = Path(args[-1])
        folder.mkdir(exist_ok=True)
        (folder / "pixi.toml").write_text("mock manifest\n")
    elif args[0] == "lock":
        manifest = Path(args[args.index("--manifest-path") + 1])
        if manifest.is_dir():
            manifest = manifest / "pixi.toml"
        manifest.with_name("pixi.lock").write_text("mock lock\n")
elif name == "docker":
    if args[0] == "build":
        if os.environ.get("FAIL_BUILD") and "ENV_NAME=DAP_SEQ_ALIGNMENT" in args:
            sys.exit(7)
    elif args[0] == "images":
        print("REPOSITORY TAG DIGEST IMAGE_ID CREATED SIZE")
        print(args[-1].split(":")[0] + " test sha256:" + "a" * 64 + " fake now 1MB")
"""


def check_quantification(work: Path) -> None:
    """Verify split counting retains MAPQ 0, NH fractions, and original rows."""
    sizes = work / "genome.chrom.sizes"
    sizes.write_text("chr1\t1000\n")
    sam = work / "reads.sam"
    sam.write_text(
        "unique\t0\tchr1\t1\t0\t50M\t*\t0\t0\t*\t*\tNH:i:1\n"
        "multi\t0\tchr1\t21\t0\t50M\t*\t0\t0\t*\t*\tNH:i:2\n"
        "multi\t256\tchr1\t221\t0\t50M\t*\t0\t0\t*\t*\tNH:i:2\n"
    )
    bed = work / "peaks.bed"
    bed.write_text("chr1\t0\t100\tfirst\nchr1\t0\t100\tduplicate\nchr1\t200\t300\tsecond\n")
    prepare_quantification(
        bed=bed,
        sam=sam,
        chrom_sizes=sizes,
        output_dir=work,
        weighting="NH",
    )
    details = json.loads((work / "quantification.json").read_text())
    assert details["denominator"] == 2
    assert (work / "alignments.bed").read_text().count("\n") == 3
    reads = work / "reads.overlaps.tsv"
    reads.write_text(
        "chr1\t0\t50\t1\tchr1\t0\t100\t0\n"
        "chr1\t20\t70\t0.5\tchr1\t0\t100\t0\n"
        "chr1\t0\t50\t1\tchr1\t0\t100\t1\n"
        "chr1\t20\t70\t0.5\tchr1\t0\t100\t1\n"
        "chr1\t220\t270\t0.5\tchr1\t200\t300\t2\n"
    )
    coverage = work / "coverage.overlaps.tsv"
    coverage.write_text(
        "chr1\t0\t10\t2\tchr1\t0\t100\t0\n"
        "chr1\t10\t40\t4\tchr1\t0\t100\t0\n"
        "chr1\t0\t10\t2\tchr1\t0\t100\t1\n"
        "chr1\t10\t40\t4\tchr1\t0\t100\t1\n"
    )
    rpm, rpkm = work / "rpm.tsv", work / "rpkm.tsv"
    finish_quantification(
        details=work / "quantification.json",
        read_overlaps=reads,
        coverage_overlaps=coverage,
        rpm_output=rpm,
        rpkm_output=rpkm,
    )
    assert [float(line.split("\t")[-1]) for line in rpm.read_text().splitlines()] == [
        750000,
        750000,
        250000,
    ]
    assert [float(line.split("\t")[-1]) for line in rpkm.read_text().splitlines()] == [
        1.4,
        1.4,
        0,
    ]
    assert [
        line.rsplit("\t", 1)[0] for line in rpm.read_text().splitlines()
    ] == bed.read_text().splitlines()
    prepare_quantification(
        bed=bed,
        sam=sam,
        chrom_sizes=sizes,
        output_dir=work,
        weighting="primary",
    )
    assert json.loads((work / "quantification.json").read_text())["denominator"] == 2
    assert (work / "alignments.bed").read_text().splitlines() == [
        "chr1\t0\t50\t1",
        "chr1\t20\t70\t1",
    ]


def check_builds(work: Path, bash: str) -> None:
    """Verify the reference scripts build both architectures and honor --no-push."""
    repo = work / "repository with spaces"
    scripts = repo / "scripts"
    scripts.mkdir(parents=True)
    for name in (
        "find-projects.sh",
        "build-dockers.sh",
        "build-project-docker.sh",
        "build-yaml-docker.sh",
    ):
        destination = scripts / name
        shutil.copyfile(ROOT / "scripts" / name, destination)
        destination.chmod(0o755)
    (repo / "dockers").mkdir()
    (repo / "dockers" / ".dockerignore").write_text(".venv/\n")
    (repo / "environments").mkdir()
    (repo / "environments" / "DAP_SEQ_ALIGNMENT.yaml").write_text("name: dap_seq_alignment\n")
    (repo / "environments" / "GENESIS_TOOLS.yaml").write_text("name: genesis_tools\n")
    project = repo / "genesis_tools"
    project.mkdir()
    for name in ("pyproject.toml", "uv.lock"):
        (project / name).write_text("mock\n")
    envfile = repo / ".env"
    envfile.write_text("UNRELATED=keep\nDAP_SEQ_ALIGNMENT_IMAGE=old\n")
    binaries = work / "bin"
    binaries.mkdir()
    for name in ("docker", "pixi", "uv", "git"):
        executable = binaries / name
        executable.write_text(f"#!{sys.executable}\n" + FAKE_COMMAND)
        executable.chmod(0o755)
    log = work / "commands.jsonl"
    environment = {
        **os.environ,
        "PATH": f"{binaries}:{os.environ['PATH']}",
        "BUILD_LOG": str(log),
    }

    def run(arguments: list[str], *, fail: bool = False) -> subprocess.CompletedProcess[str]:
        env = {**environment, **({"FAIL_BUILD": "1"} if fail else {})}
        return subprocess.run(
            [bash, str(scripts / "build-dockers.sh"), *arguments],
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=20,
        )

    result = run(["--tag", "test", "--no-push"])
    assert result.returncode == 0, result.stderr
    contents = envfile.read_text()
    assert "UNRELATED=keep" in contents
    assert "DAP_SEQ_ALIGNMENT_IMAGE=kundajelab/dap_seq_alignment@sha256:" in contents
    assert "GENESIS_TOOLS_IMAGE=kundajelab/genesis_tools@sha256:" in contents
    commands = [json.loads(line) for line in log.read_text().splitlines()]
    assert not any(command[0] == "docker" and command[1][0] == "push" for command in commands)
    builds = [args for name, args in commands if name == "docker" and args[0] == "build"]
    assert len(builds) == 2
    for args in builds:
        assert args[args.index("--platform") + 1] == "linux/amd64,linux/arm64"
    assert (repo / "environments" / "DAP_SEQ_ALIGNMENT.lock").read_text() == "mock lock\n"
    assert not (project / ".dockerignore").exists()
    log.write_text("")
    result = run(["--tag", "published", "--push", "--", "genesis_tools"])
    assert result.returncode == 0, result.stderr
    commands = [json.loads(line) for line in log.read_text().splitlines()]
    assert sum(name == "docker" and args[0] == "push" for name, args in commands) == 1
    assert sum(name == "docker" and args[0] == "build" for name, args in commands) == 1
    assert "DAP_SEQ_ALIGNMENT_IMAGE=kundajelab/dap_seq_alignment@sha256:" in envfile.read_text()
    log.write_text("")
    result = run(["--no-push", "--", "genesis_tools"])
    assert result.returncode == 0, result.stderr
    commands = [json.loads(line) for line in log.read_text().splitlines()]
    build = next(args for name, args in commands if name == "docker" and args[0] == "build")
    assert "genesis_tools:0.1.0" in build
    assert not any(name == "docker" and args[0] == "push" for name, args in commands)
    unchanged = envfile.read_text()
    result = run(["--tag", "broken", "--no-push"], fail=True)
    assert result.returncode != 0
    assert envfile.read_text() == unchanged


def main() -> None:
    """Run focused checks without external services, Docker, or genomic data."""
    assert not (ROOT / "lib" / "WorkflowSupport.groovy").exists()
    assert not (ROOT / "custom_tools").exists()
    modules = list((ROOT / "modules").glob("*.nf"))
    assert modules
    for path in modules:
        source = path.read_text()
        assert "WorkflowSupport" not in source, path
        assert "include { dotenv } from 'plugin/nf-dotenv'" in source, path
        assert "    cpus " in source and "    memory " in source and "    time " in source, path
        assert source.count("    conda ") == 1, path
        assert "with-environment.sh" not in source and "uv run" not in source, path
    interpreters = list(dict.fromkeys(["/bin/bash", shutil.which("bash") or "/bin/bash"]))
    with tempfile.TemporaryDirectory(prefix="genesis-style-") as temporary:
        work = Path(temporary)
        quant = work / "quantification"
        quant.mkdir()
        check_quantification(quant)
        for index, bash in enumerate(interpreters):
            folder = work / f"builds-{index}"
            folder.mkdir()
            check_builds(folder, bash)
    print("Nextflow style, split quantification, and mocked Docker build checks passed.")


if __name__ == "__main__":
    main()
