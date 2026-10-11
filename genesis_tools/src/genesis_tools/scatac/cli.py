"""Discover plant single-cell ATAC inputs without inferring biological identities."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ..contracts.cli import scan_options
from ..contracts.validation import Budget
from . import (
    archive_runs,
    compare,
    discovery,
    evidence,
    identities,
    ingest,
    inventory,
    loaders,
    model,
    products,
    pseudobulk,
    registry,
    release,
)


def configure(parser: argparse.ArgumentParser) -> None:
    parser.set_defaults(operation="scatac")
    commands = parser.add_subparsers(dest="scatac_command", required=True)
    child = commands.add_parser("compare")
    child.add_argument("--input", type=Path, required=True)
    child.add_argument("--against", type=Path, required=True)
    child.add_argument("--bin-size", type=int, default=1000)
    child.add_argument("--output", type=Path, required=True)
    child.set_defaults(curation_handler=execute)
    child = commands.add_parser("release")
    child.add_argument("--manifest", type=Path, required=True)
    child.add_argument("--registry", type=Path, required=True)
    child.add_argument("--output", type=Path, required=True)
    child.set_defaults(curation_handler=execute)
    child = commands.add_parser("ingest")
    child.add_argument("--manifest", type=Path, required=True)
    child.add_argument("--output", type=Path, required=True)
    child.add_argument("--resume", action="store_true")
    child.set_defaults(curation_handler=execute, operation="ingest")
    for name in ("pseudobulk", "products"):
        child = commands.add_parser(name)
        child.add_argument("--output", type=Path, required=True)
        child.add_argument("--resume", action="store_true")
        if name == "pseudobulk":
            child.add_argument("--input", type=Path, action="append", required=True)
            child.add_argument("--annotations", type=Path, required=True)
            child.add_argument("--policy", type=Path, required=True)
        else:
            child.add_argument("--input", type=Path, required=True)
        child.set_defaults(curation_handler=execute)
    child = commands.add_parser("register")
    child.add_argument("--input", type=Path, required=True)
    child.add_argument("--registry", type=Path, required=True)
    scan_options(child)
    child.set_defaults(curation_handler=execute)
    child = commands.add_parser("qc")
    child.add_argument("--input", type=Path, required=True)
    child.set_defaults(curation_handler=execute)
    model_actions = commands.add_parser("model").add_subparsers(dest="model_action", required=True)
    for name in ("export", "validate"):
        child = model_actions.add_parser(name)
        child.add_argument("--input", type=Path, required=True)
        if name == "export":
            child.add_argument("--config", type=Path, required=True)
            child.add_argument("--output", type=Path, required=True)
            child.add_argument("--resume", action="store_true")
        else:
            child.add_argument("--model-root", type=Path)
            child.add_argument("--output", type=Path)
            child.add_argument("--resume", action="store_true")
        child.set_defaults(curation_handler=execute)
    actions = commands.add_parser("inventory").add_subparsers(dest="operation", required=True)
    for name in ("import", "audit", "export", "evidence", "discover", "resolve", "runs"):
        child = actions.add_parser(name)
        child.add_argument("directory", type=Path)
        child.set_defaults(curation_handler=execute)
        if name == "import":
            child.add_argument("--source", type=Path, required=True)
            child.add_argument("--source-id", required=True)
            child.add_argument("--registry", type=Path, required=True)
            child.add_argument("--sheet", default="scATAC Fable Curated")
        if name in {"evidence", "resolve"}:
            child.add_argument("--source", type=Path, required=True)
        if name == "discover":
            child.add_argument("--species", action="append", choices=discovery.SPECIES)
            child.add_argument("--series", action="append")
            child.add_argument("--max-studies", type=int, default=100)
            child.add_argument("--refresh", action="store_true")
        if name == "runs":
            child.add_argument("--refresh", action="store_true")
        if name == "export":
            child.add_argument("--output", type=Path, required=True)


def execute(args: argparse.Namespace) -> tuple[Any, int]:
    if args.scatac_command == "compare":
        from ..contracts.records import dump

        value = compare.run(args.input, args.against, args.bin_size)
        dump(args.output, value, immutable=True)
        return value, 0
    if args.scatac_command == "release":
        return release.run(args.manifest, args.registry, args.output), 0
    if args.scatac_command == "register":
        return registry.register(
            args.input,
            args.registry,
            level=args.level,
            budget=Budget(args.max_bytes, args.max_records, args.max_seconds),
            bigwig_python=args.bigwig_python,
        ), 0
    if args.scatac_command == "qc":
        from .common import verify_output

        value = verify_output(args.input, "scatac-group")
        return {"qc": value["data"]["qc"], "review_status": "UNREVIEWED"}, 0
    if args.scatac_command == "ingest":
        return ingest.run(args.manifest, args.output, resume=args.resume), 0
    if args.scatac_command == "pseudobulk":
        return pseudobulk.aggregate(
            args.input, args.annotations, args.policy, args.output, resume=args.resume
        ), 0
    if args.scatac_command == "products":
        return products.run(args.input, args.output, resume=args.resume), 0
    if args.scatac_command == "model":
        if args.model_action == "validate":
            if args.model_root is not None or args.output is not None:
                if args.model_root is None or args.output is None:
                    raise ValueError("Actual loader validation needs --model-root and --output")
                model.validate(args.input)
                return loaders.run(args.input, args.model_root, args.output, resume=args.resume), 0
            return model.validate(args.input), 0
        return model.export(args.input, args.config, args.output, resume=args.resume), 0
    if args.operation == "import":
        return inventory.import_workbook(
            args.source, args.directory, args.registry, args.source_id, args.sheet
        ), 0
    if args.operation == "evidence":
        return evidence.attach(args.directory, args.source), 0
    if args.operation == "runs":
        result = archive_runs.run(args.directory, refresh=args.refresh)
        return result, 0 if result["complete"] else 3
    if args.operation == "discover":
        result = discovery.run(
            args.directory,
            species=args.species or list(discovery.SPECIES),
            series=args.series,
            max_studies=args.max_studies,
            refresh=args.refresh,
        )
        return result, 0 if result["complete"] else 3
    if args.operation == "resolve":
        candidates = {
            r["candidate_id"]
            for r in inventory.audit(args.directory, resolve_identities=False)["libraries"]
        }
        return identities.attach(args.directory, args.source, candidates), 0
    if args.operation == "export":
        return inventory.export(args.directory, args.output), 0
    return inventory.audit(args.directory), 0
