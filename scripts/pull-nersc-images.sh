#!/usr/bin/env bash
# Pull every image pinned in conf/genesis-images.lock with podman-hpc, on a NERSC login node.
# Compute nodes only run images that podman-hpc has pulled and squashed into $SCRATCH; tasks
# that pull for themselves run out of memory. Images already squashed are skipped: each pull
# asks Docker Hub for the manifest even then, and a few submissions in a row would reach its
# unauthenticated pull limit. An image pulled but not squashed (an interrupted pull) is pulled again.
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
squashed=$(podman-hpc images --format '{{.Repository}}@{{.Digest}} {{.ReadOnly}}' |
    awk '$2 == "true" {print $1}')
while IFS='=' read -r _key image; do
    if ! grep -qxF "docker.io/$image" <<<"$squashed"; then
        podman-hpc pull "docker.io/$image"
    fi
done < <(grep '_IMAGE=' "$repo_dir/conf/genesis-images.lock")
