#!/usr/bin/env bash
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
root=$(dirname -- "$script_dir")

profile=$("$script_dir/get-default-profile.sh")
workspace=$("$script_dir/get-default-workspace.sh")
run_name=""

function usage {
    cat << EOF
Usage: $0 [ARGS] [--] INPUT.tsv [NEXTFLOW_ARGS]

Run the pipeline on exactly one sample sheet.
* Work, published output, trace files and the Nextflow log go in WORKSPACE/RUN_NAME/.
* Nextflow is launched from WORKSPACE/RUN_NAME, so -resume picks up that run's history.
  Relative paths in NEXTFLOW_ARGS resolve against that folder; prefer absolute paths.
* NEXTFLOW_ARGS are passed directly to nextflow (e.g. -resume, --slurm_queue owners).

ARGS:
    -h|--help: Show this message and exit.
    -p|--profile: Use comma-separated nextflow profiles. Default inferred from environment ($profile)
    -w|--workspace: Where to put run folders. Default inferred from environment ($workspace)
    -n|--run-name: Name of the run folder in the workspace. Default: INPUT.tsv basename without .tsv
EOF
}

while (($# >= 1)); do
    case "$1" in
        -h | --help)
            usage
            exit 0
            ;;
        -p | --profile)
            profile=$2
            shift 2
            ;;
        -w | --workspace)
            workspace=$2
            shift 2
            ;;
        -n | --run-name)
            run_name=$2
            shift 2
            ;;
        --)
            shift 1
            break
            ;;
        -*)
            printf 'Unknown argument: %s\n\n' "$1" >&2
            usage >&2
            exit 2
            ;;
        *)
            break
            ;;
    esac
done

if (($# < 1)); then
    usage >&2
    exit 2
fi
sheet=$1
shift
if [[ ! -f $sheet ]]; then printf 'Missing input TSV: %s\n' "$sheet" >&2; exit 2; fi
if [[ $sheet != /* ]]; then sheet="$PWD/$sheet"; fi
# Make the workspace absolute: nextflow is launched from inside the run folder.
if [[ $workspace != /* ]]; then workspace="$PWD/$workspace"; fi
if [[ -z $run_name ]]; then
    run_name=$(basename -- "$sheet" .tsv)
fi

profile_given=false
option_value=false
for argument in "$@"; do
    case "$argument" in
        --input|--input=*) printf 'Supply exactly one input TSV.\n' >&2; exit 2 ;;
        --workspace|--workspace=*|--run_name|--run_name=*|--run_dir|--run_dir=*)
            printf 'Use -w/--workspace or -n/--run-name before INPUT.tsv instead of %s.\n' \
                "$argument" >&2
            exit 2
            ;;
        *.tsv)
            if ! "$option_value"; then
                printf 'Supply exactly one input TSV.\n' >&2
                exit 2
            fi
            ;;
        -profile|-profile=*) profile_given=true ;;
    esac
    case "$argument" in
        -*=*) option_value=false ;;
        -*) option_value=true ;;
        *) option_value=false ;;
    esac
done
arguments=()
if ! "$profile_given"; then arguments=(-profile "$profile"); fi

run_folder="$workspace/$run_name"
mkdir -p -- "$run_folder"
# Launch from the run folder so .nextflow/ history and .nextflow.log are kept with the run.
cd -- "$run_folder"
exec nextflow run "$root/main.nf" --input "$sheet" --workspace "$workspace" \
    --run_name "$run_name" ${arguments[@]+"${arguments[@]}"} "$@"
