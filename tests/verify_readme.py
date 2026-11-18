"""Check published Pixi recipes and links without running network, pipelines or models."""

from __future__ import annotations

import re
import shlex
import subprocess
import tomllib
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "README.md",
    ROOT / "docs/README.md",
    ROOT / "docs/scientific-overview.md",
    ROOT / "docs/development.md",
    ROOT / "docs/nextflow-style.md",
    ROOT / "docs/diagrams/README.md",
    ROOT / "genesis_tools/README.md",
    *sorted((ROOT / "docs/usage").glob("*.md")),
]


def anchors(text: str) -> set[str]:
    """Collect GitHub-style heading fragments and explicit IDs outside fenced code."""
    prose = re.sub(r"^```.*?^```[^\n]*$", "", text, flags=re.M | re.S)
    result = set(re.findall(r'<a\s+id="([^"]+)"', prose))
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", prose, re.M):
        heading = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", heading)
        base = re.sub(r"[^\w\-\s]", "", heading.lower()).replace(" ", "-")
        slug = base
        duplicate = 0
        while slug in result:
            duplicate += 1
            slug = f"{base}-{duplicate}"
        result.add(slug)
    return result


def check_links(document: Path) -> None:
    prose = re.sub(r"^```.*?^```[^\n]*$", "", document.read_text(), flags=re.M | re.S)
    for target in re.findall(r"\]\(([^)]+)\)", prose):
        if "://" in target or target.startswith("mailto:"):
            continue
        relative, separator, fragment = unquote(target).partition("#")
        path = (document.parent / relative).resolve() if relative else document
        if not path.exists():
            raise AssertionError(f"Broken documentation link in {document.name}: {target}")
        if separator and path.suffix == ".md" and fragment not in anchors(path.read_text()):
            raise AssertionError(f"Broken documentation anchor in {document.name}: {target}")


def check_required_links() -> None:
    readme = (ROOT / "README.md").read_text()
    index = (ROOT / "docs/README.md").read_text()
    assert "](docs/usage/dapseq-reference.md)" in readme, "README must link to the DAP guide"
    assert "](usage/dapseq-reference.md)" in index, "Documentation index must link to the DAP guide"
    assert "pixi run submit-pipeline" in readme, "README must lead with cluster submission"
    for path in (ROOT / "README.md", ROOT / "docs/development.md"):
        assert "https://github.com/kundajelab/genesis-preprocessing.git" in path.read_text()


def main() -> None:
    check_required_links()
    all_documents = sorted(
        {
            ROOT / name
            for name in subprocess.check_output(
                [
                    "git",
                    "ls-files",
                    "--cached",
                    "--others",
                    "--exclude-standard",
                    "--",
                    "*.md",
                ],
                cwd=ROOT,
                text=True,
            ).splitlines()
        }
    )
    for document in all_documents:
        check_links(document)
    tasks = tomllib.loads((ROOT / "pixi.toml").read_text())["tasks"]
    task_count = 0
    for document in DOCS:
        text = document.read_text()
        for block in re.findall(r"```bash\n(.*?)```", text, re.S):
            for line in block.replace("\\\n", " ").splitlines():
                if line.strip().startswith("pixi run "):
                    command = shlex.split(line, comments=True)[2]
                    # uv is an installed dependency, rather than a named Pixi task.
                    assert command in tasks or command == "uv", (document, line)
                    task_count += 1
    print(
        f"PASS {task_count} Pixi recipes resolve; "
        f"links/anchors in {len(all_documents)} documents resolve"
    )


if __name__ == "__main__":
    main()
