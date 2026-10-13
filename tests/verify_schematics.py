"""Check offline artwork, deterministic figures, layout rejection and CLI export."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from unittest.mock import patch

from genesis_tools.schematics.render import ASSETS, artwork, catalog, points, render, validate

ROOT = Path(__file__).resolve().parents[1]
NS = {"s": "http://www.w3.org/2000/svg"}


def rejects(spec: dict[str, Any]) -> None:
    try:
        validate(spec)
    except ValueError:
        return
    raise AssertionError("Invalid schematic accepted")


def main() -> None:
    for name in catalog():
        assert artwork(name)
    for workflow, stages in (("dap", 11), ("atac", 13), ("execution", 9)):
        spec = json.loads(ASSETS.joinpath(f"{workflow}.json").read_text())
        lookup = {node["id"]: node for node in spec["nodes"]}
        for index, (a, b) in enumerate(spec["edges"]):
            first = points(lookup[a], lookup[b])
            for c, d in spec["edges"][index + 1 :]:
                if {a, b} & {c, d}:
                    continue
                second = points(lookup[c], lookup[d])
                for p, q in zip(first, first[1:], strict=False):
                    for r, s in zip(second, second[1:], strict=False):
                        for axis in (0, 1):
                            if p[axis] == q[axis] == r[axis] == s[axis]:
                                other = 1 - axis
                                overlap = min(max(p[other], q[other]), max(r[other], s[other]))
                                overlap -= max(min(p[other], q[other]), min(r[other], s[other]))
                                assert overlap <= 0, (workflow, a, b, c, d)
        for theme in ("light", "dark"):
            for animated in (False, True):
                with patch(
                    "socket.socket", side_effect=AssertionError("Rendering used the network")
                ):
                    svg = render(spec, theme=theme, animated=animated)
                assert svg == render(spec, theme=theme, animated=animated)
                tree = ET.fromstring(svg)
                assert len(tree.findall("s:g[@class='stage']", NS)) == stages
                assert len(tree.findall("s:path[@class='route']", NS)) == len(spec["edges"])
                assert bool(tree.findall("s:path[@class='flow']", NS)) == animated
                assert not tree.findall(".//s:script", NS) and not tree.findall(".//s:image", NS)
                assert not any("href" in k for el in tree.iter() for k in el.attrib)
                metadata = json.loads(tree.findtext("s:metadata", namespaces=NS) or "")
                assert "MIT License" in metadata["licenses"]["TABLER-LICENSE.txt"]
                assert "Paweł Kuna" in metadata["licenses"]["TABLER-LICENSE.txt"]
                assert "Yaoxiang Li" in metadata["licenses"]["GENESIS-ART-LICENSE.txt"]
                assert "prefers-reduced-motion" in svg
        assert (ROOT / f"docs/images/genesis_{workflow}_schematic.svg").read_text() == render(spec)
    spec = json.loads(ASSETS.joinpath("atac.json").read_text())
    for key, value in (("col", -1), ("icon", "missing"), ("icon", []), ("title", "\ud800")):
        invalid = copy.deepcopy(spec)
        invalid["nodes"][0][key] = value
        rejects(invalid)
    invalid = copy.deepcopy(spec)
    invalid["nodes"].append(invalid["nodes"][0])
    rejects(invalid)
    invalid = copy.deepcopy(spec)
    invalid["edges"].append(["reads", "missing"])
    rejects(invalid)
    invalid = copy.deepcopy(spec)
    invalid["edges"].append(["reads", "align"])
    rejects(invalid)  # Would cross the acquire/adapters cards.
    spec["title"] = 'Plants <DNA> & "reads"'
    assert ET.fromstring(render(spec)).findtext("s:title", namespaces=NS) == (
        'Genesis / Plants <DNA> & "reads"'
    )
    command = [sys.executable, "-m", "genesis_tools.execution.controller", "schematic"]
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "diagram.svg"
        template = Path(directory) / "template.json"
        subprocess.run(command + ["--workflow", "atac", "--template", str(template)], check=True)
        subprocess.run(command + ["--spec", str(template), "--output", str(output)], check=True)
        before = output.read_bytes()
        collision = subprocess.run(command + ["--output", str(output)], capture_output=True)
        assert collision.returncode == 2 and output.read_bytes() == before
        subprocess.run(
            command + ["--output", str(output), "--theme", "dark", "--force"], check=True
        )
        assert before != output.read_bytes()
        template.write_text('{"bad": true}')
        invalid_run = subprocess.run(
            command + ["--spec", str(template), "--output", str(output), "--force"],
            capture_output=True,
        )
        assert invalid_run.returncode == 2
    print(
        "PASS: 12 render variants, licensed offline artwork, valid geometry, escaped text and CLI"
    )


if __name__ == "__main__":
    main()
