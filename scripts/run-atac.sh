#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
exec uv run --frozen --project "$root/genesis_tools" python -m genesis_tools.atac.run "$@"
