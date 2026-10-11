"""Parse published CLI recipes without executing network, pipelines or model deployment."""

from __future__ import annotations

import argparse
import contextlib
import io
import re
import shlex
import sys
from collections.abc import Sequence
from pathlib import Path
from unittest.mock import patch

from genesis_tools.benchmark import __main__ as benchmark
from genesis_tools.execution import controller

ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "README.md",
    *(
        ROOT / "docs/usage" / name
        for name in (
            "curation.md",
            "ai-providers.md",
            "llm-deployment.md",
            "studies.md",
            "scatac.md",
        )
    ),
]


class Parsed(Exception):
    pass


ORIGINAL_PARSE = argparse.ArgumentParser.parse_args


def parse_only(
    self: argparse.ArgumentParser,
    args: Sequence[str] | None = None,
    namespace: argparse.Namespace | None = None,
) -> argparse.Namespace:
    ORIGINAL_PARSE(self, args, namespace)
    raise Parsed


def main() -> None:
    count = 0
    for document in DOCS:
        text = document.read_text()
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if "://" in target or target.startswith("#"):
                continue
            path = (document.parent / target.split("#", 1)[0]).resolve()
            if not path.exists():
                raise AssertionError(f"Broken documentation link in {document.name}: {target}")
        for block in re.findall(r"```bash\n(.*?)```", text, re.S):
            for line in block.replace("\\\n", " ").splitlines():
                if not line.strip().startswith(("pixi run genesis ", "pixi run benchmark ")):
                    continue
                argv = shlex.split(line, comments=True)
                entry = controller.main if argv[2] == "genesis" else benchmark.main
                with (
                    patch.object(sys, "argv", [argv[2], *argv[3:]]),
                    patch.object(argparse.ArgumentParser, "parse_args", parse_only),
                    contextlib.redirect_stdout(io.StringIO()),
                ):
                    try:
                        entry()
                    except Parsed:
                        count += 1
                    except SystemExit as error:
                        if error.code not in (None, 0):
                            raise AssertionError(f"Invalid documented command: {line}") from error
                        count += 1
                    else:
                        raise AssertionError("Documentation parser reached an executable action")
    print(f"PASS {count} documented CLI commands parse; local documentation links resolve")


if __name__ == "__main__":
    main()
