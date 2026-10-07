#!/usr/bin/env bash
# Follow a task's .command.log (by task hash) or any log file, hiding bash -x trace lines.
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

if (($# < 1)) || [[ $1 == -h || $1 == --help ]]; then
    printf 'Usage: %s TASK_HASH|LOG_FILE [WORKSPACE]\n' "$0" >&2
    printf 'TASK_HASH is the "ab/123456" prefix that Nextflow prints for each task.\n' >&2
    exit 2
fi
if work_dir=$("$script_dir/get-workdir.sh" "$@" 2> /dev/null); then
    log_file="$work_dir/.command.log"
else
    log_file=$1
fi

echo "Following $log_file"
# The Sherlock login profile makes sleep a function wrapping it in timeout, which moves it
# out of the terminal process group so Ctrl-C cannot stop it. command runs the real sleep.
while [[ ! -f $log_file ]]; do
    command sleep 1
done
tail -f -n+1 "$log_file" | grep --line-buffered -v '^+'
