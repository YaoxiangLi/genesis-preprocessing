"""Dependency-free checks; fake tools test orchestration, not biological results."""

from __future__ import annotations

import csv
import gzip
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "dap_seq_pipeline.sh"
EXPECTED = {
    "01-Arabidopsis_thaliana-GSE60141": (936, 934, "SE"),
    "15-Arabidopsis_lyrata-PRJNA1177479": (405, 378, "PE"),
    "16-Arabidopsis_thaliana-PRJNA1177481": (800, 748, "PE"),
    "24-Sorghum_bicolor-PRJNA1177471": (142, 134, "PE"),
}

# Each fake tool checks that its upstream files exist before creating outputs.
FAKE_TOOL = r'''
import gzip
import json
import os
from pathlib import Path
import sys

name = Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ["FAKE_LOG"], "a") as log:
    log.write(json.dumps([name, args]) + "\n")
if os.environ.get("FAIL_TOOL") == name:
    sys.exit(17)

def require(filename: str) -> None:
    assert Path(filename).is_file(), filename

def write(filename: str) -> None:
    Path(filename).write_text("fake output\n")

if name == "wget":
    with gzip.open(args[args.index("-O") + 1], "wt") as out:
        length = int(os.environ["FAKE_READ_LENGTH"])
        for i in range(105):
            out.write(f"@read{i}\n" + "A" * length + "\n+\n" + "I" * length + "\n")
elif name in ("trimfastq.py", "PEFastqToTabDelimited.py"):
    require(args[0])
    if name == "PEFastqToTabDelimited.py":
        require(args[1])
    print("fake reads")
elif name == "bowtie":
    assert "--sam-nh" in args
    sys.stdin.read()
    print("fake SAM")
elif name == "samtools":
    if args[0] == "view":
        require(args[args.index("-bT") + 1])
        print(sys.stdin.read())
    elif args[0] == "sort":
        sys.stdin.read()
        output = args[args.index("-o") + 1] if "-o" in args else args[-1] + ".bam"
        write(output)
    elif args[0] == "index":
        require(args[1])
        write(args[1] + ".bai")
    else:
        raise AssertionError(args)
elif name == "Rscript":
    require(args[0])
    require(next(a[3:] for a in args if a.startswith("-c=")))
    write(next(a[5:] for a in args if a.startswith("-out=")))
elif name == "SAMstats.py":
    require(args[0])
    write(args[1] + ".txt")
elif name == "PEInsertDistFromBAM.py":
    require(args[0])
    write(args[2])
elif name in ("makewigglefromBAM-NH.py", "make5primeWigglefromBAM-NH.py"):
    require(args[1])
    require(args[2])
    write(args[3])
elif name == "wigToBigWig":
    require(args[0])
    require(args[1])
    write(args[2])
elif name == "macs2":
    require(args[args.index("-t") + 1])
    require(args[args.index("-c") + 1])
    prefix = args[args.index("-n") + 1]
    write(prefix + "_peaks.narrowPeak")
elif name == "bedRPKMfromBAM.py":
    with gzip.open(args[0], "rt") as peaks:
        assert peaks.read()
    require(args[2])
    require(args[3])
    write(args[4])
else:
    raise AssertionError(name)
'''


def invoke(
    bash: str, arguments: list[str], env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [bash, str(PIPELINE), *arguments],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=45,
        check=False,
    )


def check_sheets(bash: str) -> list[str]:
    header: list[str] = []
    for dataset, (total, treatments, layout) in EXPECTED.items():
        sheet = ROOT / dataset / "samples.tsv"
        with sheet.open(newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            assert reader.fieldnames is not None
            header = reader.fieldnames
            assert not {"layout", "genome_size", "analysis_read_length"}.intersection(header)
            assert len(header) == 7
            rows = list(reader)
        assert len(rows) == total
        samples = {row["sample_id"]: row for row in rows}
        assert len(samples) == total
        assert sum(row["control_sample"] != "-" for row in rows) == treatments
        for row in rows:
            assert row["read1_url"].startswith("https://ftp.sra.ebi.ac.uk/")
            assert (row["read2_url"] == "-") == (layout == "SE")
            control = row["control_sample"]
            if control != "-":
                assert control in samples and control != row["sample_id"]
        treatment = next(row["sample_id"] for row in rows if row["control_sample"] != "-")
        result = invoke(bash, ["--dry-run", "--sample", treatment, str(sheet)])
        assert result.returncode == 0, result.stderr
        assert result.stdout.count(" callpeak ") == 1
        assert "-p 2 " in result.stdout
        if layout == "PE":
            assert ".SE.a.bam" not in result.stdout
            assert "-trim INFERRED_READ_LENGTH INFERRED_READ_LENGTH" in result.stdout
            assert "-f BAMPE" in result.stdout
        else:
            assert " INFERRED_READ_LENGTH -stdout" in result.stdout and "-f BAM " in result.stdout
        assert "-g INFERRED_GENOME_SIZE" in result.stdout
    return header


def check_execution(bash: str, header: list[str], layout: str, sort_style: str) -> None:
    with tempfile.TemporaryDirectory(prefix="dap seq verification ") as directory:
        temp = Path(directory)
        tools = temp / "tools"
        tools.mkdir()
        names = [
            "wget", "bowtie", "samtools", "Rscript", "macs2", "wigToBigWig",
            "trimfastq.py", "PEFastqToTabDelimited.py", "SAMstats.py",
            "PEInsertDistFromBAM.py", "makewigglefromBAM-NH.py",
            "make5primeWigglefromBAM-NH.py", "bedRPKMfromBAM.py",
        ]
        for name in names:
            tool = tools / name
            tool.write_text(f"#!{sys.executable}\n" + FAKE_TOOL)
            tool.chmod(0o755)
        (tools / "run_spp.R").touch()
        genomes = temp / "genomes"
        genomes.mkdir()
        for name in ("reference.fa", "reference.chrom.sizes", "index.1.ebwt"):
            (genomes / name).write_text("reference\t100\n")
        (genomes / "reference.chrom.sizes").write_text("chr1\t100\nchr2\t250\n")
        dataset = temp / "dataset"
        dataset.mkdir()
        sheet = dataset / "samples.tsv"
        length = "84" if layout == "PE" else "61"
        # Alphabetical treatment first: the pipeline must still map its control
        # before invoking MACS2. An unused control must be excluded by --sample.
        with sheet.open("w", newline="") as stream:
            writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
            writer.writerow(header)
            for sample, control in (
                ("a_treatment", "z_control"), ("unused", "-"), ("z_control", "-")
            ):
                writer.writerow([
                    sample, "https://example.test/read1.fastq.gz",
                    "https://example.test/read2.fastq.gz" if layout == "PE" else "-",
                    control, "index", "reference.fa", "reference.chrom.sizes",
                ])
        # A valid last row without a newline must still be processed.
        sheet.write_text(sheet.read_text().rstrip("\n"))
        env = os.environ.copy()
        env.update({
            "PATH": f"{tools}{os.pathsep}{env['PATH']}",
            "CODE_DIR": str(tools), "GENOME_DIR": str(genomes),
            "LEGACY_PYTHON": sys.executable, "BOWTIE": str(tools / "bowtie"),
            "SAMTOOLS": str(tools / "samtools"), "MACS2": str(tools / "macs2"),
            "WIG_TO_BIGWIG": str(tools / "wigToBigWig"), "RSCRIPT": str(tools / "Rscript"),
            "SPP_SCRIPT": str(tools / "run_spp.R"), "RPM_SCRIPT": str(tools / "bedRPKMfromBAM.py"),
            "SAMTOOLS_SORT_STYLE": sort_style, "FAKE_LOG": str(temp / "calls.jsonl"),
            "THREADS": "2",
            "METADATA_PYTHON": sys.executable, "FAKE_READ_LENGTH": length,
        })
        env.pop("FAIL_TOOL", None)
        output = temp / "output"
        arguments = ["--output-dir", str(output), "--sample", "a_treatment", str(sheet)]
        dry = invoke(bash, ["--dry-run", *arguments], env)
        assert dry.returncode == 0, dry.stderr
        assert not output.exists() and not (temp / "calls.jsonl").exists()
        real = invoke(bash, arguments, env)
        assert real.returncode == 0, real.stdout + real.stderr
        result_dir = output / "dataset"
        assert (result_dir / "a_treatment.fastq.lines").read_text().strip() == "420"
        suffix = "PE.a" if layout == "PE" else "SE.a"
        for sample in ("a_treatment", "z_control"):
            with (result_dir / f"{sample}.metadata.tsv").open() as stream:
                metadata_rows = list(csv.DictReader(stream, delimiter="\t"))
            assert metadata_rows == [{
                "sample_id": sample, "layout": layout, "genome_size": "350",
                "analysis_read_length": length, "read1_reads_checked": "100",
                "read2_reads_checked": "100" if layout == "PE" else "0",
            }]
            for stem in (f"{sample}.{suffix}", f"{sample}.1x36mers.unique"):
                assert (result_dir / f"{stem}.bam").exists()
                assert (result_dir / f"{stem}.bam.bai").exists()
            stems = [f"{sample}.{suffix}"]
            if layout == "PE":
                stems.append(f"{sample}.1x36mers.unique")
            for stem in stems:
                for track in ("", ".plus", ".minus", ".5p.counts.plus", ".5p.counts.minus"):
                    assert (result_dir / f"{stem}{track}.bigWig").exists()
        peak_stem = f"a_treatment.{suffix}.MACS-2.1.0_peaks"
        assert (result_dir / f"{peak_stem}.narrowPeak.gz").exists()
        assert (result_dir / f"{peak_stem}.RPM").exists()
        assert not list(result_dir.glob("unused*"))
        assert not list(result_dir.glob("z_control*MACS*"))
        assert not list(result_dir.glob("*.partial.*"))
        calls = [json.loads(line) for line in (temp / "calls.jsonl").read_text().splitlines()]
        macs_calls = [args for name, args in calls if name == "macs2"]
        assert len(macs_calls) == 1
        assert macs_calls[0][-1] == ("BAMPE" if layout == "PE" else "BAM")
        assert macs_calls[0][macs_calls[0].index("-g") + 1] == "350"
        trim_calls = [args for name, args in calls if name == "trimfastq.py"]
        assert any(args[1] == "36" for args in trim_calls)
        if layout == "PE":
            mate_calls = [args for name, args in calls if name == "PEFastqToTabDelimited.py"]
            assert all(args[args.index("-trim") + 1:] == [length, length] for args in mate_calls)
        else:
            assert any(args[1] == length for args in trim_calls)
        if layout == "PE" and sort_style == "modern":
            # Standalone mapping can create missing metadata. Peak calling can
            # later use it after FASTQs have been removed.
            for sample in ("a_treatment", "z_control"):
                (result_dir / f"{sample}.metadata.tsv").unlink()
            remap = invoke(bash, ["--stage", "map", *arguments], env)
            assert remap.returncode == 0, remap.stderr
            for sample in ("a_treatment", "z_control"):
                assert (result_dir / f"{sample}.metadata.tsv").exists()
                for mate in ("end1", "end2"):
                    (result_dir / f"{sample}.{mate}.fastq.gz").unlink()
            cached_env = env.copy()
            cached_env["METADATA_PYTHON"] = "false"
            repeak = invoke(bash, ["--stage", "peaks", *arguments], cached_env)
            assert repeak.returncode == 0, repeak.stderr
            metadata_path = result_dir / "a_treatment.metadata.tsv"
            saved_metadata = metadata_path.read_text()
            metadata_path.write_text(saved_metadata.replace("\t350\t", "\tinvalid\t"))
            invalid_metadata = invoke(bash, ["--stage", "peaks", *arguments], cached_env)
            assert invalid_metadata.returncode != 0
            assert "Invalid metadata" in invalid_metadata.stderr
            metadata_path.write_text(saved_metadata)
        # A failing aligner must abort before tracks or peak calls; partial BAMs
        # must be cleaned even if downstream commands in the pipe wrote files.
        env["FAIL_TOOL"] = "bowtie"
        (temp / "calls.jsonl").unlink()
        failure = invoke(bash, arguments, env)
        assert failure.returncode != 0
        failed_calls = (temp / "calls.jsonl").read_text()
        assert '"macs2"' not in failed_calls and '"wigToBigWig"' not in failed_calls
        assert not list(result_dir.glob("*.partial.*"))
        # An invalid control must be rejected without creating an output folder.
        bad = dataset / "bad.tsv"
        bad.write_text(sheet.read_text().replace("\tz_control\t", "\tmissing\t"))
        rejected_output = temp / "rejected"
        invalid = invoke(bash, ["--output-dir", str(rejected_output), str(bad)], env)
        assert invalid.returncode != 0 and not rejected_output.exists()


def check_metadata_inference(bash: str, header: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="dap metadata verification ") as directory:
        temp = Path(directory)
        dataset = temp / "dataset"
        dataset.mkdir()
        output = temp / "output"
        result_dir = output / "dataset"
        result_dir.mkdir(parents=True)
        chrom_sizes = temp / "chrom.sizes"
        sheet = dataset / "samples.tsv"
        metadata_file = result_dir / "sample.metadata.tsv"
        env = os.environ.copy()
        env["METADATA_PYTHON"] = sys.executable
        arguments = ["--stage", "metadata", "--output-dir", str(output), str(sheet)]

        def write_reads(name: str, lengths: list[int]) -> None:
            with gzip.open(result_dir / name, "wt") as stream:
                for index, length in enumerate(lengths):
                    stream.write(f"@read{index}\n{'A' * length}\n+\n{'I' * length}\n")

        def infer(
            lengths: list[int], mates: list[int] | None = None,
            sizes: str = "chr1\t100\nchr2\t250\n", error: str | None = None,
        ) -> dict[str, str]:
            chrom_sizes.write_text(sizes)
            with sheet.open("w", newline="") as stream:
                writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
                writer.writerow(header)
                writer.writerow([
                    "sample", "https://example.test/read1.gz",
                    "https://example.test/read2.gz" if mates is not None else "-",
                    "-", "index", "reference.fa", str(chrom_sizes),
                ])
            if mates is None:
                write_reads("sample.fastq.gz", lengths)
            else:
                write_reads("sample.end1.fastq.gz", lengths)
                write_reads("sample.end2.fastq.gz", mates)
            previous = metadata_file.read_bytes() if metadata_file.exists() else None
            result = invoke(bash, arguments, env)
            if error is not None:
                assert result.returncode != 0
                assert error in result.stderr, result.stderr
                # Inference failures must not replace existing valid metadata.
                assert previous is None or metadata_file.read_bytes() == previous
                assert not list(result_dir.glob("*.partial.*"))
                return {}
            assert result.returncode == 0, result.stderr
            with metadata_file.open() as stream:
                rows = list(csv.DictReader(stream, delimiter="\t"))
            assert len(rows) == 1
            return rows[0]

        short = infer([61] * 3)
        assert short["read1_reads_checked"] == "3" and short["read2_reads_checked"] == "0"
        assert short["analysis_read_length"] == "61" and short["genome_size"] == "350"
        # Only the first 100 reads determine the metadata; a 101st read with a
        # different length must not affect this explicitly bounded check.
        bounded = infer([61] * 100 + [62])
        assert bounded["read1_reads_checked"] == "100"
        assert bounded["analysis_read_length"] == "61"
        paired = infer([84] * 105, [84] * 104)
        assert paired["layout"] == "PE" and paired["read2_reads_checked"] == "100"
        assert paired["analysis_read_length"] == "84"
        infer([61] * 99 + [62], error="read 100 has length 62")
        infer([84] * 100, [84] * 99 + [85], error="read 100 has length 85")
        infer([84] * 100, [85] * 100, error="mate length 85 differs")
        infer([], error="FASTQ contains no reads")
        infer([84], [], error="FASTQ contains no reads")
        infer([61], sizes="", error="chromosome sizes file is empty")
        infer([61], sizes="chr1\t-100\n", error="expected chromosome and integer size")
        infer([61], sizes="chr1\t1.5\n", error="expected chromosome and integer size")
        infer([61], sizes="chr1\t0\n", error="sizes must be positive")
        infer([61], sizes="chr1\t100\nchr1\t250\n", error="names unique")
        infer([61])
        with gzip.open(result_dir / "sample.fastq.gz", "wt") as stream:
            stream.write("@read\nACGT\n+\nIII\n")
        malformed = invoke(bash, arguments, env)
        assert malformed.returncode != 0 and "malformed FASTQ record" in malformed.stderr
        assert not list(result_dir.glob("*.partial.*"))


def main() -> None:
    bash = shutil.which("bash")
    assert bash is not None
    header = check_sheets(bash)
    check_metadata_inference(bash, header)
    shells = list(dict.fromkeys([bash, "/bin/bash"]))
    for shell in shells:
        for layout in ("SE", "PE"):
            for sort_style in ("legacy", "modern"):
                check_execution(shell, header, layout, sort_style)
    default = invoke(bash, ["--dry-run", "--stage", "peaks"])
    assert default.returncode == 0, default.stderr
    assert default.stdout.count(" callpeak ") == sum(row[1] for row in EXPECTED.values())
    print(
        f"Verified four sample sheets, metadata edge cases, "
        f"and {len(shells) * 4} fake-tool workflows."
    )


if __name__ == "__main__":
    main()
