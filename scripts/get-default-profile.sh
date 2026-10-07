#!/usr/bin/env bash
# Print the default Nextflow profiles for this machine.
set -euo pipefail
if command -v sbatch &> /dev/null; then
    # slurm is available, use slurm and apptainer
    echo "sherlock,apptainer"
elif command -v docker &> /dev/null; then
    # run locally: prefer docker but can fall back to conda
    echo "local,docker"
else
    echo "local,conda"
fi
