#!/usr/bin/env bash
# Print the work directory of a task given its hash (e.g. "ab/123456"), searching every run
# in the workspace.
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

if (($# < 1)); then
    printf 'Usage: %s TASK_HASH [WORKSPACE]\n' "$0" >&2
    exit 2
fi
task_hash=$1
workspace=${2:-$("$script_dir/get-default-workspace.sh")}
first_dir=$(dirname -- "$task_hash")
second_dir=$(basename -- "$task_hash")
work_dir=$(
    find "$workspace" -mindepth 2 -maxdepth 2 -type d -name work \
    | while read -r run_work_dir; do
        sub_dir="$run_work_dir/$first_dir"
        if [[ -d "$sub_dir" ]]; then
            find "$sub_dir" -mindepth 1 -maxdepth 1 -type d -name "${second_dir}*"
        fi
    done \
    | tail -n1
)
if [[ -z "$work_dir" ]]; then
    printf 'No work directory found for %s in %s\n' "$task_hash" "$workspace" >&2
    exit 1
fi
echo "$work_dir"
