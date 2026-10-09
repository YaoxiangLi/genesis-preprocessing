# Minimum runtime environment for baseline tests

Date: 2026-10-07. Workspace: `/home/exouser/projects/genesis-preprocessing-validation`.
Baseline: `repo/`, branch `main`, SHA **`4468c712e4c171b573e2ec2806fdc5327b5379e9`**.

**Installation acceptance: PASS.** The repository's normal installation task completed using locked dependencies, a repeat installation succeeded, and all 73 tracked file hashes remained identical. No lockfile, manifest, workflow source or `.env` changed. No source branch/commit was created because this task made no source edits. No sudo, system installation, group/daemon/security changes, privileged container, image build, or push occurred.

This establishes the installed dependencies for the existing **default** checks, including its Nextflow stub workflows. It does not establish that the full test suite passes: the suite was not executed in this environment-setup task. The separate opt-in real-tool Docker suite still needs its five configured workflow images, which are absent locally. Real public-data runs additionally need the exact reference files; synthetic tests create their own fixtures.

## Initial availability and installation choice

Preflight found Git 2.43.0, curl 8.5.0, Docker client/server 29.1.3, host Java 21.0.12.1 and PATH Python 3.12.12. Pixi, Nextflow, micromamba, uv and ShellCheck were absent from PATH. User `~/.pixi` was absent. Docker's daemon query succeeded for the current user before installation work; no Docker remediation was necessary.

The primary specification is the unmodified root `pixi.toml` and `pixi.lock`; Python subproject dependencies come from the existing `genesis_tools/pyproject.toml`, `uv.lock` and `.python-version`. Pixi **0.70.1** was deliberately selected to match the version stated by the repository's pinned Pixi Docker builder, rather than selecting an unspecified latest binary.

The official documented installer is `curl -fsSL https://pixi.sh/install.sh | sh`. The command was shown to the user before execution, downloaded for inspection, and run with a version pin and user-only destination. [Official Pixi installation documentation](https://pixi.prefix.dev/latest/installation/).

Exact installation commands from workspace root:

```bash
mkdir -p scratch/runtime-environment
curl -fsSL https://pixi.sh/install.sh -o scratch/runtime-environment/pixi-install.sh
/usr/bin/time -v -o scratch/runtime-environment/pixi-install.time \
  env PIXI_VERSION=0.70.1 PIXI_HOME=/home/exouser/.pixi \
  PIXI_BIN_DIR=/home/exouser/.pixi/bin PIXI_NO_PATH_UPDATE=1 \
  PIXI_NO_TELEMETRY=1 NETRC=/dev/null \
  sh scratch/runtime-environment/pixi-install.sh \
  > scratch/runtime-environment/pixi-install.stdout \
  2> scratch/runtime-environment/pixi-install.stderr
```

The script downloaded `https://github.com/prefix-dev/pixi/releases/download/v0.70.1/pixi-x86_64-unknown-linux-musl.tar.gz` and installed `/home/exouser/.pixi/bin/pixi`. The installer itself identifies its script revision as v0.81.0; that is distinct from the requested/observed binary version 0.70.1. Its downloaded script hash and installed binary hash are recorded below. Shell startup files were not edited. `NETRC=/dev/null` avoided using a credential file for the public installer download. No secret values were printed.

## Normal project installation, unchanged

Working directory: `repo/`.

```bash
/usr/bin/time -v -o ../scratch/runtime-environment/install-all.time \
  env PATH=/home/exouser/.pixi/bin:$PATH \
  /home/exouser/.pixi/bin/pixi run --locked install-all \
  > ../scratch/runtime-environment/install-all.stdout \
  2> ../scratch/runtime-environment/install-all.stderr
```

The additional outer `--locked` prevents task startup from updating the root lock before invoking the normal task. `scripts/install-projects.sh` then runs exactly the existing procedure:

```bash
pixi install --manifest-path "$root/pixi.toml" --locked
uv python install "$(sed 's/+gil$//' "$root/genesis_tools/.python-version")"
uv sync --project "$root/genesis_tools" --locked
```

The first install exited 0 in 8.73 s, peak RSS 345,344 KiB. It created the root Pixi environment, downloaded CPython 3.14.5, created the Python subproject venv and installed the nine applicable Python packages. The ten-package lock also contains platform-conditional dependencies; count alone is not a missing-package finding. No install warnings/errors were observed. Raw outputs are retained.

The same locked installation was repeated, with outputs under `install-repeat.*`: exit 0, 0.26 s, peak RSS 37,288 KiB. It reported the environment installed, Python already installed and nine packages checked. This verifies repeat installation in the same host/cache, not a second independent clean-room build.

## Exact installed versions

| Component | Observed version | Evidence |
|---|---|---|
| Pixi | **0.70.1** | `/home/exouser/.pixi/bin/pixi --version` |
| Nextflow | **25.10.4 build 11173** | Project `nextflow -version` and `nextflow info` |
| Java actually used by Nextflow | **OpenJDK 23.0.2-internal**, build `23.0.2-internal-adhoc.conda.src` | Project `java -version`; `nextflow info` explicitly reports this VM |
| Groovy in Nextflow | **4.0.28** | `nextflow info` |
| micromamba | **2.5.0** | Project `micromamba --version` |
| uv | **0.11.33**, x86_64-unknown-linux-gnu | Project `uv --version` |
| ShellCheck | **0.11.0** | Project `shellcheck --version` |
| Python used by genesis-tools/tests | **CPython 3.14.5**, standard GIL build | `sys.version`; `Py_GIL_DISABLED=0`; `.python-version` requests `3.14.5+gil` |
| genesis-tools | **0.1.0**, editable local project | Installed distribution metadata |
| pysam | **0.24.1**; bundled samtools **1.24** | Distribution metadata and `pysam.__samtools_version__` |
| defopt | **7.0.0** | Installed distribution metadata |
| Ruff | **0.16.10** | Installed distribution metadata |
| ty | **0.0.84** | Installed distribution metadata |
| Isolated build backend | **setuptools 84.0.0** | Installed genesis-tools `WHEEL` says `Generator: setuptools (84.0.0)` |
| nf-schema | **2.4.2** | Explicit plugin install and offline startup log |
| nf-dotenv | **1.0.0** | Explicit plugin install and offline startup log |
| Docker client/server | **29.1.3 / 29.1.3** | `docker version` |
| Docker server / tested container platform | **linux/amd64** | Server API, manifest and local image inspection |

`command -v` inside Pixi resolves Nextflow, Java, micromamba and uv below `repo/.pixi/envs/default/bin`. Nextflow does not use the host's Java 21 in this invocation. Python is `repo/genesis_tools/.venv/bin/python3`, resolving to `/home/exouser/.local/share/uv/python/cpython-3.14.5-linux-x86_64-gnu/bin/python3.14`.

Full installed package metadata, including root conda artifact/build information, is retained in `../scratch/runtime-environment/pixi-packages.json` (`pixi list --locked --json`) and `python-packages.json` (`pixi run --locked uv pip list --python genesis_tools/.venv/bin/python --format json`). Full version stdout/stderr is retained in `runtime-versions.*`, `nextflow-info.*`, and `python-versions.*`.

Reproducibility limit: `pyproject.toml` specifies `setuptools>=82` for isolated builds rather than locking an exact build backend. The installed wheel records 84.0.0, but a future fresh build may choose a different allowed backend. This baseline setup did not silently edit the specification to pin it. Successful locked installation and unchanged locks do not establish byte-for-byte build reproducibility or future remote artifact availability.

## Nextflow plugin preparation and readiness probes

The existing regression driver sets `NXF_OFFLINE=true`. Therefore the two versions already declared in `nextflow.config` were explicitly installed into the user's Nextflow plugin cache before future tests:

```bash
# Run from repo/
/usr/bin/time -v -o ../scratch/runtime-environment/plugins-install.time \
  /home/exouser/.pixi/bin/pixi run --locked nextflow plugin install \
  nf-schema@2.4.2,nf-dotenv@1.0.0 \
  > ../scratch/runtime-environment/plugins-install.stdout \
  2> ../scratch/runtime-environment/plugins-install.stderr
```

Exit 0, 3.78 s, peak RSS 202,316 KiB. Files reside under `~/.nextflow/plugins/nf-schema-2.4.2` and `nf-dotenv-1.0.0`; all 101 plugin files were checksummed in `verification.json`.

Readiness probes:

- `pixi run --locked nextflow info`: exit 0; establishes JVM actually used.
- `pixi run --locked uv run --frozen --project genesis_tools genesis-tools --help`: exit 0.
- Both existing test scripts loaded with Python `runpy.run_path(path, run_name="audit_import")`: exit 0, 0.23 s, peak RSS 35,496 KiB. This checks imports only; it does **not** execute their `main()` or assertions.
- Docker smoke execution below: exit 0.

Failed diagnostic probes are preserved rather than described as passing:

1. The first version probe requested `importlib.metadata.version("setuptools")` in the runtime venv. It exited 1 with `PackageNotFoundError`; setuptools is an isolated build dependency rather than an installed runtime dependency. A corrected probe of declared runtime packages passed. The installed wheel separately records build backend 84.0.0. No package was added to satisfy the mistaken probe.
2. `nextflow plugin --help` exited 1 with `Missing plugin command - usage: nextflow plugin install <pluginId,..>`. The documented-by-CLI install command then succeeded.
3. Offline `nextflow run main.nf --help` exited 1 because this workflow does not short-circuit required-parameter validation for `--help`. It reported missing `input` and absent `repo/references`, with a warning listing parameter values as invalid and a first-run warning that configured resume was ignored. The complete output is in `offline-help.stdout`, `offline-help.stderr` and `offline-help.nextflow.log`. These are unchanged-workflow startup diagnostics, not dependency-install failures.

The offline startup log confirms **both pinned plugins started successfully without downloading**. Its execution trace contains only a header: no process tasks ran and no reads/references were downloaded. Nextflow emitted HTML/trace artifacts, moved from the automatically selected `repo/workspace/null` to `../scratch/runtime-environment/offline-help-run/` to keep generated outputs outside the checkout. Ignored Nextflow cache/history may remain in `repo/.nextflow/`; raw diagnostic log is in scratch. The help behavior was not fixed and no test assertion was weakened.

Exact offline command (from `repo/`):

```bash
/usr/bin/time -v -o ../scratch/runtime-environment/offline-help.time \
  env NXF_OFFLINE=true NXF_DISABLE_CHECK_LATEST=true \
  /home/exouser/.pixi/bin/pixi run --locked nextflow \
  -log /home/exouser/projects/genesis-preprocessing-validation/scratch/runtime-environment/offline-help.nextflow.log \
  run main.nf --help \
  > ../scratch/runtime-environment/offline-help.stdout \
  2> ../scratch/runtime-environment/offline-help.stderr
```

## Docker validation without host changes

Preflight commands succeeded:

```bash
docker version --format 'client={{.Client.Version}} server={{.Server.Version}} server_os={{.Server.Os}} server_arch={{.Server.Arch}}'
docker info --format 'OSType={{.OSType}} Architecture={{.Architecture}}'
```

The official-library `hello-world` manifest was inspected, its linux/amd64 manifest digest selected, then that immutable digest was used for execution. The moving `latest` tag was used only for discovery; the executed identity is pinned below. No workflow image was substituted with this image.

```bash
docker manifest inspect --verbose hello-world:latest
/usr/bin/time -v -o scratch/runtime-environment/docker-smoke.time \
  docker run --rm --network none --platform linux/amd64 \
  hello-world@sha256:d1a8d0a4eeb63aff09f5f34d4d80505e0ba81905f36158cc3970d8e07179e59e \
  > scratch/runtime-environment/docker-smoke.stdout \
  2> scratch/runtime-environment/docker-smoke.stderr
```

Smoke result: exit 0, “Hello from Docker!”, 1.20 s, client-process peak RSS 28,236 KiB. GNU time does not measure Docker daemon/container memory. The image was initially absent, pulled by digest, and remains cached; the temporary container was automatically removed. Local image ID: `sha256:e2ac70e7319a02c5a477f5825259bd118b94e8b02c279c67afa63adab6d8685b`; manifest digest above; platform `linux/amd64`. Runtime networking was disabled; the daemon used network access to pull the image.

Docker is usable by the current user, so the conditional Ubuntu Docker Engine installation/remediation instructions are **not applicable**. No sudo commands were needed, proposed for execution or executed; group membership, daemon configuration and system settings were left untouched.

## Workflow image identities and opt-in boundary

The tracked `.env` was parsed using a strict allowlist for public image references; it was never sourced or printed wholesale. These are declared image digests, not proof of the image contents or platform availability:

| Setting | Exact image | Local state / architecture |
|---|---|---|
| `DAP_SEQ_ALIGNMENT_IMAGE` | `kundajelab/dap_seq_alignment@sha256:4764008ba8fbb5d831bd6f9ed6a720fd494062b39f0bae63ff2e4efd316ad842` | Not present (inspect exit 1); image architecture UNVERIFIED |
| `DAP_SEQ_TRACKS_IMAGE` | `kundajelab/dap_seq_tracks@sha256:e6dd6ceb79e50fc6db83e9346a920e51fd2bf0dcffbc18c9305b1b6e8c806390` | Not present (inspect exit 1); image architecture UNVERIFIED |
| `DAP_SEQ_QC_IMAGE` | `kundajelab/dap_seq_qc@sha256:ace177a497934a26adb305bc0dc92cc6a447fe8ca714b79f72a007c7acb53239` | Not present (inspect exit 1); image architecture UNVERIFIED |
| `DAP_SEQ_PEAKS_IMAGE` | `kundajelab/dap_seq_peaks@sha256:10467dd29e3d25ce7769f76f57402bd1a5a582006e911d06479bfcc3e3325df3` | Not present (inspect exit 1); image architecture UNVERIFIED |
| `GENESIS_TOOLS_IMAGE` | `kundajelab/genesis_tools@sha256:31458d4a6a83541f463ea4b0e692a0afc65c6df441f70c3f71fc4ccf1a11eb59` | Not present (inspect exit 1); image architecture UNVERIFIED |

The repository's build scripts target linux/amd64 and linux/arm64, but that declaration is not a measured manifest platform. No workflow images were pulled or built for the default tests. `images.json` preserves each `docker image inspect` command, error and elapsed time. The opt-in `validate-docker` suite requires these images; its readiness remains incomplete. The previously observed no-tag build-script failure remains unchanged and is not needed to install the default test environment.

## Commands for the next validation task

No PATH startup edits were made. For a future shell, use the explicit user binary and process-local PATH:

```bash
cd /home/exouser/projects/genesis-preprocessing-validation/repo
export PATH="$HOME/.pixi/bin:$PATH"
pixi run --locked install-all
# Full existing default suite; NOT run during this environment task:
pixi run --locked checks
```

The existing test driver supports `--keep` for retaining fixture/work evidence; the default `checks` task does not pass it. Future baseline test execution should preserve failure evidence without changing tests. The project remains untouched here; no wrapper or custom regression code was added.

## Provenance, acceptance and limitations

All operations refer to the SHA at the top of this report. Input hashes were captured before installation and compared after it for **all 73 tracked files**, including every root/tool lockfile, manifest, source file and `.env`. `before-sha256.json` and `after-sha256.json` are identical. No restore was required because no lock changed. Final Git porcelain status (including untracked files) is empty; ignored environments are present as intended.

Environment/probe stdout, stderr, timing and image metadata are under `../scratch/runtime-environment/`. These retained logs include warnings/errors; no log filter was used to claim success. Host tool versions remain documented in audit 00; acquisition used existing Git 2.43.0, curl 8.5.0, Bash 5.2.21 and host Python 3.12.12 for audit JSON/hash collection. Project execution used the installed versions listed above. Untimed lightweight probes have elapsed/peak RAM marked UNAVAILABLE rather than inferred. No biological QC thresholds were selected.

| Operation | Wall time | Peak RSS (KiB) | Exit / acceptance |
|---|---:|---:|---|
| Pinned user Pixi install | 2.00 s | 22,152 | 0 / PASS |
| Normal locked project install | 8.73 s | 345,344 | 0 / PASS |
| Repeat locked project install | 0.26 s | 37,288 | 0 / PASS |
| Pinned Nextflow plugins | 3.78 s | 202,316 | 0 / PASS |
| Initial combined version probe | 1.47 s | 151,896 | 1 / setuptools runtime metadata query failed; later runtime query passed |
| Offline workflow-help startup | 5.41 s | 594,028 | 1 / missing required inputs; plugins loaded, no tasks |
| Both test-script imports | 0.23 s | 35,496 | 0 / PASS, imports only |
| Docker manifest discovery | 5.36 s | 33,344 | 0 / PASS |
| Pinned Docker smoke | 1.20 s | 28,236 | 0 / PASS; client-process memory only |
| Java/Nextflow info, corrected Python query, CLI help, installed-package lists | UNAVAILABLE | UNAVAILABLE | Succeeded except plugin-help syntax probe documented above |

**What passed:** pinned user installation; project locked install and repeat; tool/version identification; test imports; plugin offline loading; Docker execution; unchanged tracked hashes/locks/manifests and clean Git tree.

**What failed:** three diagnostic invocations described above, none silently discarded. The workflow-help invocation failed validation; it is not a successful test-suite run. Five workflow-image inspections failed because images are absent locally.

**What remains ambiguous/unresolved:** actual full-suite results; real-tool image availability/architecture/source correspondence; cross-machine and byte-identical reproducibility; future resolution of the unpinned isolated build backend. These do not prevent executing the installed default suite, but no passing-suite claim is made.

**Files/state changed:** new `audit/02-runtime-environment.md`; supporting scratch evidence; user `~/.pixi/bin/pixi`, uv-managed Python/cache and Nextflow plugins; ignored `repo/.pixi/`, `repo/genesis_tools/.venv/`, build metadata and Nextflow cache/log artifacts; one cached hello-world image. No tracked repository file, dependency manifest, lockfile or pipeline logic changed. No full workflow tests or public biological data processing were run. Stop after this environment report.

## Input and artifact checksums

| File | SHA256 |
|---|---|
| `repo/.env` | `0279cdae1bd2822b2fabb50cfe6edee79bac6274065cbd4de69c27897a499a22` |
| `repo/environments/DAP_SEQ_ALIGNMENT.lock` | `b4e1aadbaf84b5bff4ef3a3b7de301d3ca2eace1dd5eb3f4d5407207f97e34c1` |
| `repo/environments/DAP_SEQ_ALIGNMENT.toml` | `c0cfb397febf9f8426e048054b4a2649cc5589020da59405fcae4c6cf69fe0ea` |
| `repo/environments/DAP_SEQ_ALIGNMENT.yaml` | `37c5f28d34972d2af3de6c8e809bdd1577235befc3479fc72fb3c9534427b2be` |
| `repo/environments/DAP_SEQ_PEAKS.lock` | `bd1ff7c93326bcae049515168c327150c69d4e46f3332f5c88ae26ad0734d67b` |
| `repo/environments/DAP_SEQ_PEAKS.toml` | `8b6ea7e8c56c1694420be247076a89aa2f367966dcb625148cdd8a2ab5dae55d` |
| `repo/environments/DAP_SEQ_PEAKS.yaml` | `b697950d20f00d486663bf1602baedf490a3117dae23bcdaf59acbdb812a3e24` |
| `repo/environments/DAP_SEQ_QC.lock` | `067f9f6ee235f50e01bf2daa70218738182efb91149a50894d7aad5e30fd6fb8` |
| `repo/environments/DAP_SEQ_QC.toml` | `5aa5fb5cbe3de5107a3c87fdabdae64fe5836e7ac6dea0021d497ee351a80c1d` |
| `repo/environments/DAP_SEQ_QC.yaml` | `8712f230e0882d5015b2843a281f75cd30de540c42589f508122dd26b59a37b9` |
| `repo/environments/DAP_SEQ_TRACKS.lock` | `293bdf88f5b7570bc76dcd2ff7fe81ff2d46de2b168d2b986c58a2154e76e74d` |
| `repo/environments/DAP_SEQ_TRACKS.toml` | `22b12df97da39e526df3f7b118290ef688535e2d6e661fd87078b8b4e6282fc2` |
| `repo/environments/DAP_SEQ_TRACKS.yaml` | `26d6c9f58eecc9d848cb803f37f912fa94233a82eeffd8fc12ee0fffe8d3b970` |
| `repo/environments/GENESIS_TOOLS.yaml` | `f1d671abfe016035e2ad7b2d16275f3738d8955deb6162813afbef4c25bcd61a` |
| `repo/genesis_tools/.python-version` | `60300f4be98e02fe6abde5ac922562e3dc98af494079a44c73d14540ece967a4` |
| `repo/genesis_tools/pyproject.toml` | `7602a953712ff2f1fbc971b09e2e5d00ab73fbbb6cbbd3467abf88bcbdcb587e` |
| `repo/genesis_tools/uv.lock` | `1132c51537ac229ce768fcf0edde8475a970be017cef82c0d46601b228f998f5` |
| `repo/nextflow.config` | `fc9631faf354591deaf221d03bb05a07ba21e8f0d5a62327608f33adf95af3c6` |
| `repo/pixi.lock` | `874cbf7d41658470853868c86e5b6d4f2734b85a47b1973f9bb8e78833a7047c` |
| `repo/pixi.toml` | `aade98b8e94983459fd229060b933c99363b3ad29a139a3a07e994cd9a860005` |
| `repo/scripts/install-projects.sh` | `dcaf30cbd3a323292f481dbb2a6bbc039d5900f73bf11bb8ee879d82490f0d44` |
| `/home/exouser/.pixi/bin/pixi` | `6d51531f4ae7b83fe68e72fe0935ed192e7f8e2eb04e3c4cd45f03a24f217ac6` |
| `scratch/runtime-environment/pixi-install.sh` | `e90779b74d26b5070d5e909e4c857f2f2b8b3c4c9e8904d1954cd2e91ae7ef5d` |
| `repo/.pixi/envs/default/bin/java` | `f2275ea8fc204f6c2173fdf6bb332db16795ae54c3ef283cc9d19e4a5e2be24a` |
| `repo/.pixi/envs/default/bin/nextflow` | `7160c467c9652684b0c70e53a4752ea61a1f19d9e9d234025e2591df1b89d8ab` |
| `repo/genesis_tools/.venv/bin/python3` | `c27397da5541f67655be462e128ca3d3eb6e0a8eb0d39036896c9042529f4304` |

The complete tracked-file and 101 plugin-file checksum lists, executable resolutions and clean-status result are retained in `verification.json` and the before/after checksum JSONs. These include the installed artifacts; no claim is made that an upstream signature was independently verified.
