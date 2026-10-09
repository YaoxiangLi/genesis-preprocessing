"""Benchmark CLI. Planning never executes workflows or fetches inputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .spec import load


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    fixture = commands.add_parser("fixture")
    fixture.add_argument("--out", type=Path, required=True)
    fixture.add_argument(
        "--adapter", choices=["postalign", "genesis-atac", "nfcore-atac"], default="postalign"
    )
    fixture.add_argument("--checkout", type=Path)
    fixture.add_argument("--assay", choices=["DAP-seq", "bulk-ATAC"], default="DAP-seq")
    for name in ("plan", "fetch", "run"):
        command = commands.add_parser(name)
        command.add_argument("manifest", type=Path)
        if name == "run":
            command.add_argument("--out", type=Path, required=True)
            command.add_argument("--resume", action="store_true")
    for name in ("compare", "report"):
        command = commands.add_parser(name)
        command.add_argument("results", type=Path)
        if name == "compare":
            command.add_argument("--against", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "fixture":
            from .fixture import create

            print(create(args.out, assay=args.assay, adapter=args.adapter, checkout=args.checkout))
        elif args.command == "plan":
            plan = load(args.manifest)
            print(json.dumps(plan, indent=2))
            if plan["blockers"]:
                raise SystemExit(2)
        elif args.command == "fetch":
            from .runtime import fetch

            fetch(load(args.manifest))
        elif args.command == "run":
            from .runner import run

            run(load(args.manifest), args.out, resume=args.resume)
        elif args.command == "compare" and args.against:
            from .reporting import compare_runs

            print(compare_runs(args.results, args.against))
        else:
            from .reporting import report

            report(args.results)
    except (ValueError, OSError, EOFError, KeyError) as error:
        parser.exit(2, f"Benchmark error: {error}\n")


if __name__ == "__main__":
    main()
