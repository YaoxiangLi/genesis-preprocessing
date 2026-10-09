"""Bounded execution, complete logs, verified caching and explicit public downloads."""

from __future__ import annotations

import datetime
import json
import os
import shutil
import signal
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any

from .spec import public_url, sha256, write_json


def disk_bytes(root: Path) -> int:
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file() and not p.is_symlink())


class Runtime:
    def __init__(self, plan: dict[str, Any], out: Path, *, resume: bool) -> None:
        self.plan, self.out, self.resume = plan, out.resolve(), resume
        self.start = time.monotonic()
        self.limits = plan["spec"]["limits"]
        self.events: list[dict[str, Any]] = []
        self.images: dict[str, Any] = {}
        self.out.mkdir(parents=True, exist_ok=True)
        lock = self.out / "experiment.json"
        if lock.exists():
            previous = json.loads(lock.read_text())
            if not resume or previous["experiment_id"] != plan["experiment_id"]:
                raise ValueError(
                    "Existing results require --resume and identical scientific identity; "
                    "use a new output directory"
                )
        elif resume:
            raise ValueError("Cannot resume a missing experiment")
        else:
            write_json(lock, plan)
        self.check()

    def check(self) -> None:
        if time.monotonic() - self.start > self.limits["seconds"]:
            raise ValueError("Campaign wall-time limit exceeded")
        if disk_bytes(self.out) > self.limits["disk_bytes"]:
            raise ValueError("Campaign output-storage limit exceeded")

    def asset(self, name: str) -> Path:
        return Path(self.plan["assets"][name]["path"])

    def cached(self, folder: Path, inputs: list[Path], recipe: object) -> bool:
        marker = folder / "task.json"
        if not self.resume or not marker.exists():
            return False
        record = json.loads(marker.read_text())
        hashes = {str(p): sha256(p) for p in inputs}
        valid = (
            record["status"] == "COMPLETE"
            and record["inputs"] == hashes
            and record["recipe"] == recipe
            and bool(record["outputs"])
        )
        valid = valid and all(
            Path(p).is_file() and sha256(Path(p)) == h for p, h in record["outputs"].items()
        )
        if valid:
            self.events.append({"task": str(folder.relative_to(self.out)), "status": "CACHED"})
        return valid

    def seal(
        self,
        folder: Path,
        inputs: list[Path],
        outputs: list[Path],
        recipe: object,
        *,
        elapsed: float = 0.0,
    ) -> None:
        if not outputs or any(not p.is_file() for p in outputs):
            raise ValueError("Required task outputs are missing")
        write_json(
            folder / "task.json",
            {
                "status": "COMPLETE",
                "recipe": recipe,
                "inputs": {str(p): sha256(p) for p in inputs},
                "outputs": {str(p): sha256(p) for p in outputs},
                "wall_seconds": elapsed,
            },
        )
        self.events.append({"task": str(folder.relative_to(self.out)), "status": "COMPLETED"})
        self.check()

    def command(
        self,
        label: str,
        argv: list[str],
        cwd: Path,
        inputs: list[Path],
        *,
        image: str | None = None,
        network: bool = False,
    ) -> None:
        self.check()
        cwd.mkdir(parents=True, exist_ok=True)
        log = self.out / "commands" / label
        attempt = 1
        while (log / f"attempt-{attempt}").exists():
            attempt += 1
        log = log / f"attempt-{attempt}"
        log.mkdir(parents=True)
        command = argv
        container_name = f"genesis-bench-{os.getpid()}-{label}"[:120]
        if image:
            image_ref = self.plan["spec"]["images"][image]
            inspected = subprocess.check_output(
                [
                    "docker",
                    "image",
                    "inspect",
                    "--format",
                    "{{json .Id}} {{json .Architecture}} {{json .RepoDigests}}",
                    image_ref,
                ],
                text=True,
            ).strip()
            self.images[image] = {"requested": image_ref, "resolved": inspected}
            # Every source asset is read-only; only this campaign output is writable.
            mounts = {p.parent for p in inputs} | {Path(__file__).resolve().parents[4]}
            mounts = {p for p in mounts if p != self.out and self.out not in p.parents}
            command = [
                "docker",
                "run",
                "--rm",
                "--pull=never",
                "--name",
                container_name,
                "--cpus",
                str(self.limits["cpus"]),
                "--memory",
                f"{self.limits['memory_gb']}g",
                "--user",
                f"{os.getuid()}:{os.getgid()}",
                "--network",
                "bridge" if network else "none",
            ]
            for mount in sorted(mounts):
                command += ["-v", f"{mount}:{mount}:ro"]
            command += [
                "-v",
                f"{self.out}:{self.out}:rw",
                "-w",
                str(cwd),
                image_ref,
                "bash",
                "-c",
                '"$@"; result=$?; cat /sys/fs/cgroup/memory.peak > "$BENCH_MEMORY" 2>/dev/null; '
                'cat /sys/fs/cgroup/io.stat > "$BENCH_IO" 2>/dev/null; exit "$result"',
                "benchmark",
                *argv,
            ]
            # Add only explicit non-secret runtime variables before the image name.
            position = command.index(image_ref)
            command[position:position] = [
                "-e",
                f"BENCH_MEMORY={log / 'container-memory.peak'}",
                "-e",
                f"BENCH_IO={log / 'container-io.stat'}",
            ]
        timed = (
            ["/usr/bin/time", "-v", "-o", str(log / "time.txt"), *command]
            if Path("/usr/bin/time").is_file()
            else command
        )
        record = {
            "argv": command,
            "tool_argv": argv,
            "cwd": str(cwd),
            "image": self.images.get(image),
            "source": self.plan["source"],
            "inputs": {str(p): sha256(p) for p in inputs},
            "utc": datetime.datetime.now(datetime.UTC).isoformat(),
        }
        start = time.monotonic()
        status = "FAILED"
        with (log / "stdout").open("wb") as stdout, (log / "stderr").open("wb") as stderr:
            process = subprocess.Popen(
                timed, cwd=cwd, stdout=stdout, stderr=stderr, start_new_session=True
            )
            try:
                while process.poll() is None:
                    time.sleep(0.1)
                    self.check()
                status = "COMPLETE" if process.returncode == 0 else "FAILED"
            except BaseException:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                if image:
                    subprocess.run(
                        ["docker", "stop", "-t", "1", container_name],
                        capture_output=True,
                        check=False,
                    )
                raise
            finally:
                record.update(
                    status=status,
                    exit_status=process.returncode,
                    wall_seconds=time.monotonic() - start,
                )
                write_json(log / "run.json", record)
        if status != "COMPLETE":
            raise ValueError(f"Command failed: {label}; full logs retained in {log}")


def fetch(plan: dict[str, Any]) -> None:
    if plan["dataset"]["status"] != "READY":
        raise ValueError(
            "Dataset reference/metadata unresolved; candidate catalogs cannot be fetched"
        )
    missing = [a for a in plan["assets"].values() if not Path(a["path"]).is_file()]
    if any("url" not in a or "bytes" not in a for a in missing):
        raise ValueError("Every missing asset needs a public URL, exact size and SHA256")
    budget = plan["spec"]["limits"]["download_bytes"]
    if sum(a["bytes"] for a in missing) > budget:
        raise ValueError("Download byte budget exceeded before fetching")
    start = time.monotonic()
    for asset in missing:
        public_url(asset["url"])
        target = Path(asset["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        if shutil.disk_usage(target.parent).free < asset["bytes"]:
            raise ValueError("Insufficient free disk for download")
        temporary = target.with_suffix(target.suffix + ".partial")
        try:
            with (
                urllib.request.urlopen(asset["url"], timeout=30) as response,
                temporary.open("xb") as stream,
            ):
                public_url(response.geturl())
                total = 0
                while block := response.read(1024 * 1024):
                    total += len(block)
                    if (
                        total > asset["bytes"]
                        or time.monotonic() - start > plan["spec"]["limits"]["seconds"]
                    ):
                        raise ValueError("Download size or time limit exceeded")
                    stream.write(block)
            if total != asset["bytes"] or sha256(temporary) != asset["sha256"]:
                raise ValueError("Downloaded artifact size/checksum mismatch")
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
