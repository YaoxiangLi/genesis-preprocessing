#!/usr/bin/env bash
# Print the default workspace: $SCRATCH on clusters that provide it, otherwise the repository.
set -euo pipefail
if [[ -n "${SCRATCH:-}" ]]; then
    echo "$SCRATCH/workspace"
else
    root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
    echo "$root/workspace"
fi
