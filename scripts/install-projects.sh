#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "$0")/.." && pwd)
install_cli=false
bin_args=()
while (($#)); do
    case "$1" in
        --install-cli) install_cli=true; shift ;;
        --bin-dir)
            if (($# < 2)) || [[ -z $2 || $2 == --* ]]; then
                printf '%s\n' '--bin-dir requires a directory.' >&2
                exit 2
            fi
            bin_args=(--bin-dir "$2")
            shift 2
            ;;
        -h|--help)
            printf '%s\n' 'Usage: pixi run install-all [--install-cli [--bin-dir DIRECTORY]]' \
                'Install locked dependencies; optionally expose genesis in ~/.local/bin.'
            exit 0
            ;;
        *) printf 'Unknown installation option: %s\n' "$1" >&2; exit 2 ;;
    esac
done
if ((${#bin_args[@]})) && ! "$install_cli"; then
    printf '%s\n' '--bin-dir requires --install-cli.' >&2
    exit 2
fi
pixi install --manifest-path "$root/pixi.toml" --locked
# genesis_tools pins a "+gil" Python, which uv selects but cannot download; install the plain
# version so a managed free-threaded build of the same version is never chosen instead.
uv python install "$(sed 's/+gil$//' "$root/genesis_tools/.python-version")"
uv sync --project "$root/genesis_tools" --locked
if "$install_cli"; then
    "$root/genesis_tools/.venv/bin/python" -m genesis_tools.execution.install \
        --repo "$root" ${bin_args[@]+"${bin_args[@]}"}
fi
# YAML environments are created by Nextflow's conda profile, or by Docker builds.
