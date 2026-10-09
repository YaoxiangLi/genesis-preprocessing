#!/usr/bin/env bash
set -euo pipefail
project=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
exec nextflow -C "$project/experimental/atac/nextflow.config" run "$project/experimental/atac/main.nf" --source_sha "$(git -C "$project" rev-parse HEAD)" "$@"
