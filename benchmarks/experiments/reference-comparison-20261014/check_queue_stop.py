"""A budget stop must reach scientific tools that started their own session."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from run_queue import stop_owned_tree


def main() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        ready = Path(temporary) / "child.pid"
        child_code = "import time; time.sleep(60)"
        code = (
            "import subprocess,sys,pathlib; "
            "p=subprocess.Popen([sys.executable,'-c',sys.argv[2]], start_new_session=True); "
            "pathlib.Path(sys.argv[1]).write_text(str(p.pid)); p.wait()"
        )
        process = subprocess.Popen(
            [sys.executable, "-c", code, str(ready), child_code], start_new_session=True
        )
        try:
            deadline = time.monotonic() + 10
            while not ready.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            if not ready.exists():
                raise AssertionError("Child fixture did not start")
            child = int(ready.read_text())
            assert os.getpgid(child) != os.getpgid(process.pid)
            stop_owned_tree(process)
            assert process.returncode is not None
            child_stat = Path(f"/proc/{child}/stat")
            assert (
                not child_stat.exists()
                or child_stat.read_text().rsplit(")", 1)[1].split()[0] == "Z"
            )
        finally:
            if process.poll() is None:
                stop_owned_tree(process)
    print("PASS queue budget stop terminates separately-sessioned descendant tools")


if __name__ == "__main__":
    main()
