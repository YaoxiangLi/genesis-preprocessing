"""An empty Nextflow flag must not masquerade as an organellar contig list."""

import subprocess
import tempfile
from pathlib import Path

source = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix="atac-parameters-") as directory:
    work = Path(directory)
    result = subprocess.run(
        [
            "nextflow",
            "-C",
            str(source / "nextflow.config"),
            "run",
            str(source / "main.nf"),
            "--adapter_policy",
            "none-synthetic-adapter-free",
            "--mapq",
            "30",
            "--genome_size",
            "1000",
            "--organelles",
            "",
            "--outdir",
            str(work / "outputs"),
        ],
        cwd=work,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
    assert "Supply --organelles NONE" in result.stdout + result.stderr
    trace = work / "outputs/trace.tsv"
    if trace.exists():
        assert len(trace.read_text().splitlines()) <= 1, "Rejected policy launched tasks"
print("PASS: empty organellar argument rejected before task execution")
