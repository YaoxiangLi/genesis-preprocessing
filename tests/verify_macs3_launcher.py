"""CPU allocation and provenance checks without installing MACS3."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

from genesis_tools.scatac import products

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "launcher", ROOT / "genesis_tools/src/genesis_tools/macs3_launch.py"
)
assert SPEC and SPEC.loader
launcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(launcher)


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        script = Path(directory) / "macs3"
        script.write_text("fixture")
        with patch.object(launcher.sysconfig, "get_path", return_value=directory):
            assert launcher.executable() == str(script)
            script.unlink()
            try:
                launcher.executable()
            except ValueError:
                pass
            else:
                raise AssertionError("Missing environment-local executable accepted")
    before = os.environ.copy()
    with (
        patch.object(os, "sched_getaffinity", return_value={3, 7, 11}),
        patch.object(os, "getpid", return_value=0),
        patch.object(os, "sched_setaffinity") as set_affinity,
    ):
        assert launcher.constrain(2) == [3, 7]
        set_affinity.assert_called_once_with(0, [3, 7])
        assert all(os.environ[k] == "1" for k in launcher.THREAD_VARIABLES)
        assert launcher.constrain(8) == [3, 7, 11]
        with patch.object(os, "getpid", return_value=1):
            assert launcher.constrain(2) == [7, 11]
        try:
            launcher.constrain(0)
        except ValueError:
            pass
        else:
            raise AssertionError("Zero CPUs accepted")
    os.environ.clear()
    os.environ.update(before)
    with tempfile.TemporaryDirectory() as directory:
        receipt = Path(directory) / "run.json"
        with (
            patch.object(
                launcher,
                "identity",
                return_value={"source_revision": launcher.SOURCE_REVISION},
            ),
            patch.object(launcher, "constrain", return_value=[3, 7]),
            patch.object(launcher, "executable", return_value="/env/bin/macs3"),
            patch.object(launcher.os, "execvpe") as execute,
            patch.object(
                launcher.sys,
                "argv",
                [
                    "launcher",
                    "--cpus",
                    "2",
                    "--receipt",
                    str(receipt),
                    "--",
                    "callpeak",
                    "-f",
                    "BEDPE",
                    "--keep-dup",
                    "all",
                ],
            ),
        ):
            assert launcher.main() == 0
            assert execute.call_args.args[1] == [
                "/env/bin/macs3",
                "callpeak",
                "-f",
                "BEDPE",
                "--keep-dup",
                "all",
            ]
            assert json.loads(receipt.read_text())["affinity"] == [3, 7]
            assert launcher.main() == 2  # Existing provenance cannot be overwritten.
    with tempfile.TemporaryDirectory() as directory:
        receipt = Path(directory) / "wrong-source.json"
        with (
            patch.object(launcher, "identity", return_value={"source_revision": "0" * 40}),
            patch.object(launcher, "executable", return_value="/env/bin/macs3"),
            patch.object(launcher.os, "execvpe") as execute,
            patch.object(
                launcher.sys,
                "argv",
                [
                    "launcher",
                    "--cpus",
                    "2",
                    "--receipt",
                    str(receipt),
                    "--require-source",
                    launcher.SOURCE_REVISION,
                    "--",
                    "--version",
                ],
            ),
        ):
            assert launcher.main() == 2
            execute.assert_not_called()
            assert not receipt.exists()
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory)
        scientific = ["macs3", "callpeak", "-f", "BEDPE", "--keep-dup", "all"]
        with patch.object(
            products.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)
        ) as run:
            products.command(products.IMAGES["peaks"], scientific, folder, "peaks")
            argv = run.call_args.args[0]
            assert argv[-len(scientific[1:]) :] == scientific[1:]
            assert "/genesis-macs3.py" in argv
            assert any(arg.endswith(":/genesis-macs3.py:ro") for arg in argv)
            assert argv[argv.index("--memory") + 1] == "8g"
            assert argv[argv.index("--network") + 1] == "none"
            assert argv.count("--cpus") == 2  # Docker quota and the affinity launcher.
            products.command(products.IMAGES["peaks"], ["macs3", "--version"], folder, "version")
            assert "/genesis-macs3.py" not in run.call_args.args[0]
    print(
        "PASS MACS3 launcher: restricted affinity, inherited limits, thread caps, "
        "unchanged arguments and exclusive provenance"
    )


if __name__ == "__main__":
    main()
