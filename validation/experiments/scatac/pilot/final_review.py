"""Check the completed pilot evidence and publication scope without rerunning science."""
from pathlib import Path
import datetime
import hashlib
import json
import re
import subprocess
from urllib.parse import unquote

root = Path(__file__).resolve().parents[2]
repo = root / "repo"
base = root / "results/scatac-completion"
evidence = repo / "validation/evidence/scatac-completion"
tested = "f83bd75d71db74f080c93ee7090a54cee8295504"
baseline = "4d5aa600acb29fb1662231dc830e0e3785b76d7a"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def load(path):
    return json.loads(path.read_text())


scopes = ["genesis_tools/src", "genesis_tools/tests", "tests", "modules",
          "main.nf", "nextflow.config", "pixi.toml", "pixi.lock",
          "genesis_tools/pyproject.toml", "genesis_tools/uv.lock"]
assert not git("diff", "--name-only", tested, "--", *scopes)
assert not git("ls-files", "--others", "--exclude-standard", "--", *scopes)
unchanged = scopes[3:]
assert not git("diff", "--name-only", baseline, "--", *unchanged)
assert not git("diff", "--check")

release = load(base / "genesis-scatac-pilot-v1/complete.json")
acceptance = load(base / "release-acceptance.json")
portable = load(base / "portable-release-acceptance.json")
assert release["version"] == acceptance["release"] == portable["release_version"]
assert release["data"]["groups"] == 24
assert release["data"]["release_issues"] == []
assert release["data"]["model_ready"] is False
assert release["data"]["training_validated"] is False
assert acceptance["computational_acceptance"] == portable["status"] == "PASS"
assert len(portable["relocated_loader_tests"]) == 4
models = load(evidence / "models.json")
assert len(models) == 48
for model in models:
    assert model["loader_manifest"]["data"]["loader_test"] == "PASS"
    folds = model["loader_result"]["folds"]
    assert {f["split"] for f in folds} == {"train", "validation", "test"}
    assert all(f["per_base_sequence"] == f["per_base_signal"] == "PASS" for f in folds)
summary = load(evidence / "summary.json")
assert sum(s["groups"] for s in summary["species"].values()) == 24
assert sum(s["cells"] for s in summary["species"].values()) == 6170
assert len(list((evidence / "concordance").glob("*/*.json"))) == 12

checks = {}
for label in ["completed-code-frozen-checks", "diagnostic-frozen-docker-regression",
              "bulk-atac-docker-regression", "independent-real-pilot-conservation",
              "two-species-pilot-release-v3", "portable-real-pilot-loaders"]:
    path = base / "commands" / label / "receipt.json"
    record = load(path)
    assert record["acceptance"] == "PASS" and record["exit_status"] == 0, label
    checks[label] = hashlib.sha256(path.read_bytes()).hexdigest()

names = set(git("diff", "--name-only", baseline).splitlines())
names.update(git("ls-files", "--others", "--exclude-standard").splitlines())
patterns = {
    "private_key": r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
    "github_token": r"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,})",
    "huggingface_token": r"hf_[A-Za-z0-9]{25,}",
    "openai_token": r"(?<![A-Za-z0-9_])sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{40,}",
    "aws_access_key": r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",
    "url_credentials": r"https?://[^\s/@:]+:[^\s/@]+@",
    "signed_url": r'[?&](?:X-Amz-Signature|X-Goog-Signature|access_token)=[^\s&"<>]+',
}
hits = []
large = []
broken = []
for name in sorted(names):
    path = repo / name
    if not path.is_file():
        continue
    data = path.read_bytes()
    if len(data) > 5_000_000:
        large.append(name)
    text = data.decode("utf-8", errors="replace")
    hits.extend({"path": name, "category": category}
                for category, pattern in patterns.items() if re.search(pattern, text))
    if path.suffix == ".md":
        for target in re.findall(r"\]\(([^\s)]+)\)", text):
            if ":" in target or target.startswith("#"):
                continue
            destination = unquote(target.split("#", 1)[0])
            if not (path.parent / destination).exists():
                broken.append({"path": name, "target": target})
assert not hits, hits  # Paths and categories only; never print matched values.
assert not large, large
assert not broken, broken
assert "still running" not in (repo / "validation/reports/scatac-completion.md").read_text()

result = {
    "status": "PASS", "captured_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "head": git("rev-parse", "HEAD"), "tested_code_sha": tested,
    "production_code_unchanged_since_checks": True,
    "unchanged_from_baseline": unchanged, "acceptance_receipt_sha256": checks,
    "groups": 24, "included_cells": 6170, "actual_model_tests": 48,
    "portable_model_tests": 4, "replicate_comparisons": 12,
    "changed_files_scanned": len(names), "credential_pattern_findings": hits,
    "files_over_5MB": large, "broken_local_markdown_file_links": broken,
    "scan_scope": "Known credential patterns in changed/new files; not proof that arbitrary secrets cannot exist. No matched values emitted.",
    "scientific_review": "UNREVIEWED", "training": "NOT_RUN",
}
path = base / "provenance/final-artifact-review.json"
assert not path.exists()
path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, indent=2))
