#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "$0")/.." && pwd)
pixi install --manifest-path "$root/pixi.toml" --locked
uv sync --project "$root/genesis_tools" --locked
# YAML environments are created by Nextflow's conda profile, or by Docker builds.
