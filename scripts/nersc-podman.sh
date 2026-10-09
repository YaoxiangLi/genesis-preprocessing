#!/usr/bin/env bash
# Run a command with a private Podman-HPC adapter; never modify global executables.
set -euo pipefail
command -v podman-hpc >/dev/null || { echo 'podman-hpc is unavailable on this host' >&2; exit 2; }
[[ $# -gt 0 ]] || { echo 'Usage: nersc-podman.sh COMMAND [ARGUMENTS...]' >&2; exit 2; }
adapter=$(mktemp -d "${TMPDIR:-/tmp}/genesis-podman.XXXXXXXX")
trap 'rm -rf -- "$adapter"' EXIT
printf '%s\n' '#!/usr/bin/env bash' 'exec podman-hpc "$@"' > "$adapter/podman"
chmod 700 "$adapter/podman"
export PATH="$adapter:$PATH"
"$@"
