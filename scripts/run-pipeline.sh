#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "$0")/.." && pwd)
if (($# < 1)) || [[ $1 == -* ]]; then
    printf 'Usage: pixi run pipeline INPUT.tsv [Nextflow options]\n' >&2
    exit 2
fi
sheet=$1
shift
if [[ ! -f $sheet ]]; then printf 'Missing input TSV: %s\n' "$sheet" >&2; exit 2; fi
if [[ $sheet != /* ]]; then sheet="$PWD/$sheet"; fi
profile_given=false
option_value=false
for argument in "$@"; do
    case "$argument" in
        --input|--input=*) printf 'Supply exactly one input TSV.\n' >&2; exit 2 ;;
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
if ! "$profile_given"; then arguments=(-profile 'local,conda'); fi
cd -- "$root"
exec nextflow run "$root/main.nf" --input "$sheet" ${arguments[@]+"${arguments[@]}"} "$@"
