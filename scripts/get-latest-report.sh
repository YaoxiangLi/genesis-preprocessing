#!/usr/bin/env bash
# Print the path to the most recent execution report in the workspace.
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

if [[ ${1:-} == -h || ${1:-} == --help ]]; then
    printf 'Usage: %s [WORKSPACE]\n' "$0"
    exit 0
fi
workspace=${1:-$("$script_dir/get-default-workspace.sh")}
if [[ ! -d $workspace ]]; then
    printf 'Workspace not found: %s\n' "$workspace" >&2
    exit 1
fi
# Report names end in a sortable timestamp; sort on the file name, not the run folder.
report=$(
    find "$workspace" -mindepth 3 -maxdepth 3 -type f -path '*/trace/execution_report_*.html' \
    | awk -F/ '{print $NF "\t" $0}' | sort | tail -n1 | cut -f2
)
if [[ -z "$report" ]]; then
    printf 'No execution reports found in %s\n' "$workspace" >&2
    exit 1
fi
echo "$report"
