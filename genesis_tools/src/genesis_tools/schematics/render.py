"""Render deterministic, editable Genesis SVG schematics without network access."""

from __future__ import annotations

import argparse
import hashlib
import json
import textwrap
import xml.etree.ElementTree as ET
from html import escape
from importlib.resources import files
from pathlib import Path
from typing import Any

ASSETS = files("genesis_tools.schematics").joinpath("assets")
COLORS = {
    "reads": "#147d79",
    "reference": "#4473a0",
    "qc": "#8a63a5",
    "results": "#aa6927",
    "execution": "#3c805c",
}
W, H, DX, DY = 250, 132, 320, 206


def catalog() -> dict[str, Any]:
    return json.loads(ASSETS.joinpath("catalog.json").read_text())


def artwork(name: str) -> str:
    record = catalog()[name]
    data = ASSETS.joinpath(record["file"]).read_bytes()
    if hashlib.sha256(data).hexdigest() != record["sha256"]:
        raise ValueError(f"Artwork checksum mismatch: {name}")
    element = ET.fromstring(data)
    allowed = {"svg", "g", "path", "line", "polyline", "polygon", "circle", "ellipse", "rect"}
    attributes = {
        "xmlns",
        "width",
        "height",
        "viewBox",
        "fill",
        "stroke",
        "stroke-width",
        "stroke-linecap",
        "stroke-linejoin",
        "class",
        "d",
        "x",
        "y",
        "x1",
        "x2",
        "y1",
        "y2",
        "cx",
        "cy",
        "r",
        "rx",
        "ry",
        "points",
        "transform",
        "opacity",
    }
    for part in element.iter():
        if part.tag.split("}")[-1] not in allowed or not set(part.attrib) <= attributes:
            raise ValueError(f"Unsupported artwork markup: {name}")
        if any("url(" in value.lower() for value in part.attrib.values()):
            raise ValueError(f"External artwork reference: {name}")
        part.tag = part.tag.split("}")[-1]
    return "".join(ET.tostring(child, encoding="unicode") for child in element)


def text(value: object, limit: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"Expected nonempty text of at most {limit} characters")
    if any(ord(c) < 32 or 0xD800 <= ord(c) <= 0xDFFF or ord(c) in (0xFFFE, 0xFFFF) for c in value):
        raise ValueError("Control characters are not allowed in labels")
    return value


def position(node: dict[str, Any]) -> tuple[int, int]:
    return 64 + node["col"] * DX, 200 + node["row"] * DY


def points(a: dict[str, Any], b: dict[str, Any]) -> list[tuple[float, float]]:
    x, y = position(a)
    xx, yy = position(b)
    if x == xx:
        port = W * (0.4 if yy > y else 0.6)
        return [(x + port, y + H if yy > y else y), (xx + port, yy if yy > y else yy + H)]
    start = x + W if xx > x else x
    end = xx if xx > x else xx + W
    lane = 0.5 if yy == y else 0.3 if yy > y else 0.7
    mid = start + (DX - W) * lane * (1 if xx > x else -1)
    source_y = y + H * (0.5 if yy == y else 0.25 if yy < y else 0.75)
    target_y = yy + H * (0.5 if yy == y else 0.8 if yy < y else 0.2)
    return [(start, source_y), (mid, source_y), (mid, target_y), (end, target_y)]


def validate(spec: dict[str, Any]) -> None:
    if set(spec) != {"version", "title", "subtitle", "notes", "nodes", "edges"}:
        raise ValueError("Expected version, title, subtitle, notes, nodes and edges")
    if type(spec["version"]) is not int or spec["version"] != 1:
        raise ValueError("Unsupported schematic version")
    text(spec["title"], 38)
    text(spec["subtitle"], 150)
    if not isinstance(spec["notes"], list) or len(spec["notes"]) > 2:
        raise ValueError("Use at most two footer notes")
    for note in spec["notes"]:
        text(note, 140)
    nodes, edges = spec["nodes"], spec["edges"]
    if not isinstance(nodes, list) or not 1 <= len(nodes) <= 16:
        raise ValueError("Use 1–16 stages on a four-column grid")
    identifiers, occupied = set(), set()
    for node in nodes:
        if not isinstance(node, dict) or set(node) != {
            "id",
            "title",
            "detail",
            "icon",
            "col",
            "row",
            "kind",
        }:
            raise ValueError("Invalid stage fields")
        ident = text(node["id"], 40)
        if not ident.isascii() or not ident.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Stage IDs use ASCII letters, digits, dashes and underscores")
        text(node["title"], 36)
        text(node["detail"], 62)
        if len(textwrap.wrap(node["title"], 18)) > 2 or len(textwrap.wrap(node["detail"], 31)) > 2:
            raise ValueError("Shorten stage labels to fit two lines")
        if (
            not isinstance(node["icon"], str)
            or not isinstance(node["kind"], str)
            or node["icon"] not in catalog()
            or node["kind"] not in COLORS
        ):
            raise ValueError("Unknown icon or stage kind")
        for field in ("col", "row"):
            if type(node[field]) is not int or not 0 <= node[field] <= 3:
                raise ValueError("Rows and columns must be integers from 0 to 3")
        cell = node["col"], node["row"]
        if ident in identifiers or cell in occupied:
            raise ValueError("Duplicate stage ID or occupied layout cell")
        identifiers.add(ident)
        occupied.add(cell)
    if not isinstance(edges, list) or len(edges) > 40:
        raise ValueError("Use at most 40 connections")
    lookup = {node["id"]: node for node in nodes}
    seen = set()
    for edge in edges:
        if (
            not isinstance(edge, list)
            or len(edge) != 2
            or not all(isinstance(v, str) for v in edge)
        ):
            raise ValueError("Connections must be pairs of stage IDs")
        a, b = edge
        if a not in lookup or b not in lookup or a == b or (a, b) in seen:
            raise ValueError("Unknown, self or duplicate connection")
        seen.add((a, b))
        route = points(lookup[a], lookup[b])
        for first, second in zip(route, route[1:], strict=False):
            for node in nodes:
                if node["id"] in edge:
                    continue
                x, y = position(node)
                left, right = sorted((first[0], second[0]))
                top, bottom = sorted((first[1], second[1]))
                if left < x + W and right > x and top < y + H and bottom > y:
                    raise ValueError(f"Connection {a} → {b} crosses {node['id']}; move that stage")


def render(spec: dict[str, Any], *, theme: str = "light", animated: bool = False) -> str:
    validate(spec)
    if theme not in {"light", "dark"}:
        raise ValueError("Unknown theme")
    bg, card, ink, muted, border = (
        ("#f6f4ed", "#ffffff", "#173c32", "#52685f", "#d4ddd3")
        if theme == "light"
        else ("#112820", "#1b382f", "#edf5ec", "#b5c9bd", "#426152")
    )
    height = 200 + (max(n["row"] for n in spec["nodes"]) + 1) * DY + 90
    style = f"""
    svg{{background:{bg};font-family:Arial,Helvetica,sans-serif;color:{ink}}}
    text{{fill:{ink}}}.detail,.subtitle,.note{{fill:{muted}}}
    .card{{fill:{card};stroke:{border};stroke-width:1.5}}
    .route{{fill:none;stroke-width:2.5;stroke-linejoin:round;stroke-linecap:round}}
    .flow{{fill:none;stroke:{ink};stroke-width:2;stroke-dasharray:2 24;
    animation:flow 10s linear infinite}}
    @keyframes flow{{to{{stroke-dashoffset:-260}}}}
    @media(prefers-reduced-motion:reduce){{.flow{{display:none}}}}
    @media print{{.flow{{display:none}}}}
    """
    title = escape(spec["title"])
    result = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1340 {height}" '
        'role="img" aria-labelledby="title description">',
        f'<title id="title">Genesis / {title}</title>',
        f'<desc id="description">{escape(spec["subtitle"])}. '
        "Arrows show selected data dependencies; this is not a live execution graph.</desc>",
        f'<style>{style}</style><rect width="1340" height="{height}" fill="{bg}"/>',
        f'<svg x="54" y="28" width="100" height="120" viewBox="0 0 24 24" '
        f'fill="none" stroke="{ink}" stroke-width="1.4" stroke-linecap="round" '
        f'stroke-linejoin="round">{artwork("genesis-seed")}</svg>',
        '<text x="180" y="55" font-size="14" letter-spacing="4">GENESIS / PLANT GENOMICS</text>',
        f'<text class="heading" x="180" y="99" font-size="32" font-weight="700">{title}</text>',
    ]
    for i, line in enumerate(textwrap.wrap(spec["subtitle"], 95)):
        result.append(
            f'<text class="subtitle" x="180" y="{130 + i * 21}" font-size="16">'
            f"{escape(line)}</text>"
        )
    result.append(
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        '<path d="M1 1 L9 5 L1 9" fill="none" stroke="context-stroke" stroke-width="1.5"/>'
        "</marker></defs>"
    )
    lookup = {node["id"]: node for node in spec["nodes"]}
    for a, b in spec["edges"]:
        route = points(lookup[a], lookup[b])
        geometry = "M " + " L ".join(f"{x:g} {y:g}" for x, y in route)
        color = COLORS[lookup[a]["kind"]]
        result.append(
            f'<path d="{geometry}" fill="none" stroke="{bg}" stroke-width="7" '
            'stroke-linejoin="round"/>'
        )
        result.append(
            f'<path class="route" data-from="{a}" data-to="{b}" '
            f'd="{geometry}" stroke="{color}" marker-end="url(#arrow)"/>'
        )
        if animated:
            result.append(f'<path class="flow" d="{geometry}"/>')
    for node in spec["nodes"]:
        x, y = position(node)
        color = COLORS[node["kind"]]
        result.append(
            f'<g id="stage-{node["id"]}" class="stage">'
            f'<rect class="card" x="{x}" y="{y}" width="{W}" height="{H}" rx="16"/>'
            f'<path d="M{x + 18} {y} H{x + W - 18}" stroke="{color}" stroke-width="4"/>'
            f'<svg x="{x + 18}" y="{y + 21}" width="36" height="36" viewBox="0 0 24 24" '
            f'fill="none" stroke="{color}" stroke-width="1.7" stroke-linecap="round" '
            f'stroke-linejoin="round">{artwork(node["icon"])}</svg>'
        )
        for i, line in enumerate(textwrap.wrap(node["title"], 18)):
            result.append(
                f'<text class="label" x="{x + 68}" y="{y + 32 + i * 23}" font-size="18" '
                f'font-weight="700">{escape(line)}</text>'
            )
        for i, line in enumerate(textwrap.wrap(node["detail"], 31)):
            result.append(
                f'<text class="detail" x="{x + 18}" y="{y + 88 + i * 20}" font-size="14">'
                f"{escape(line)}</text>"
            )
        result.append("</g>")
    result.append(f'<path d="M64 {height - 83} H1274" stroke="{border}"/>')
    for i, note in enumerate(spec["notes"]):
        result.append(
            f'<text class="note" x="64" y="{height - 55 + i * 22}" font-size="14">'
            f"{escape(note)}</text>"
        )
    credits = {
        "renderer": "Genesis botanical schematic v1",
        "theme": theme,
        "spec_sha256": hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest(),
        "assets": {
            name: catalog()[name]
            for name in sorted({"genesis-seed"} | {n["icon"] for n in spec["nodes"]})
        },
        "licenses": {
            name: ASSETS.joinpath(name).read_text()
            for name in ("TABLER-LICENSE.txt", "GENESIS-ART-LICENSE.txt")
        },
    }
    result.append(f"<metadata>{escape(json.dumps(credits, sort_keys=True))}</metadata></svg>")
    return "\n".join(result) + "\n"


def configure(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--workflow", choices=("dap", "atac", "execution"), default="dap")
    group.add_argument("--spec", type=Path, help="Render an edited JSON template")
    parser.add_argument("--output", type=Path, help="Write a self-contained SVG")
    parser.add_argument(
        "--template", type=Path, help="Export the selected template as editable JSON"
    )
    parser.add_argument("--theme", choices=("light", "dark"), default="light")
    parser.add_argument(
        "--animate", action="store_true", help="Animate connectors, not live status"
    )
    parser.add_argument(
        "--list-icons", action="store_true", help="List bundled artwork and licenses"
    )
    parser.add_argument("--force", action="store_true", help="Replace the selected output file")


def execute(args: argparse.Namespace) -> None:
    if args.list_icons:
        print(json.dumps(catalog(), indent=2))
        return
    if bool(args.output) == bool(args.template):
        raise ValueError("Choose exactly one of --output SVG or --template JSON")
    spec = (
        json.loads(args.spec.read_text())
        if args.spec
        else json.loads(ASSETS.joinpath(f"{args.workflow}.json").read_text())
    )
    if not isinstance(spec, dict):
        raise ValueError("Schematic JSON must be an object")
    validate(spec)
    destination = args.output or args.template
    expected = ".svg" if args.output else ".json"
    if destination.suffix.lower() != expected:
        raise ValueError(f"Output must use the {expected} extension")
    if args.spec and destination.resolve() == args.spec.resolve():
        raise ValueError("Use a different output path from the input specification")
    content = (
        render(spec, theme=args.theme, animated=args.animate)
        if args.output
        else (json.dumps(spec, indent=2) + "\n")
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w" if args.force else "x") as stream:
        stream.write(content)
    print(destination)
