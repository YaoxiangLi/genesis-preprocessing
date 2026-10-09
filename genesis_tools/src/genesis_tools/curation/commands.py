"""Small registration/error boundary shared by the delegated curation commands."""

from __future__ import annotations

import argparse
import sqlite3
import sys

from ..contracts import cli as validation_cli
from ..contracts.records import canonical
from ..qc_policy import cli as qc_cli
from ..registry import cli as registry_cli
from . import cli as review_cli


def configure(commands: argparse._SubParsersAction) -> None:
    for name, module in (
        ("validate", validation_cli),
        ("registry", registry_cli),
        ("qc", qc_cli),
        ("review", review_cli),
    ):
        module.configure(commands.add_parser(name))


def execute(args: argparse.Namespace) -> None:
    try:
        result, code = args.curation_handler(args)
        print(result if isinstance(result, str) else canonical(result))
    except (ValueError, OSError, KeyError, TypeError, sqlite3.Error) as error:
        print(canonical({"error": str(error), "operation": args.operation}), file=sys.stderr)
        code = 2
    raise SystemExit(code)
