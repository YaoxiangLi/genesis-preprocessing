The Nextflow scaffold follows igvf_pseudobulking_pipeline:

- Each process declares its resources, conda YAML, and nf-dotenv container image.
- Configurable resources are passed from main.nf through a resources input.
- BWA options and the pinned SPP script are also explicit inputs.
- Pure tool environments live in environments/*.yaml. Docker builds derive matching
  *.toml/*.lock files with Pixi and use dockers/pixi-yaml.Dockerfile.
- The environments are dap_seq_alignment, dap_seq_peaks (MACS3 and bedtools),
  dap_seq_qc, and dap_seq_tracks.
- genesis_tools/ is a Python 3.14.5 free-threading uv project, containerized with
  dockers/uv-project.Dockerfile. Its conda equivalent is GENESIS_TOOLS.yaml.
- Docker build/discovery scripts and dockers/.dockerignore are copied unchanged
  from the reference repository. Run them through Pixi, whose Nextflow dependency
  supplies GNU coreutils on macOS, including mktemp.
- The Dockerfiles retain the reference's pinned base images. The uv recipe copies
  .python-version before dependency installation to select free-threading Python.
- .env records image names for nf-dotenv.

Quantification is separated by environment:
BAM_TO_SAM (dap_seq_alignment), PREPARE_QUANTIFICATION (genesis_tools),
INTERSECT_PEAKS (dap_seq_peaks), QUANTIFY (genesis_tools).
Only the final two score files are published. Standalone peak-rpm still supports
direct BAM counting when samtools and bedtools are on PATH.

Use:
    pixi run install-all
    pixi run build-dockers --no-push
    pixi run build-dockers --no-push -- dap_seq_alignment genesis_tools
    pixi run pipeline INPUT.tsv -profile local,docker
    pixi run pipeline INPUT.tsv -profile sherlock,apptainer

Every Docker build targets both linux/amd64 and linux/arm64. The original scripts
default to pushing, so explicitly pass --no-push for local builds. They derive
image tags from the latest Git tag (currently 0.1.0), with --tag available to
override it. Image names match project/environment names without an extra prefix.
The scripts update .env using image digests. Publishing images requires user
approval; local images alone are not available to Sherlock's Apptainer.

Without a supplied profile, the pipeline wrapper uses local,conda. Run it through
root Pixi so Nextflow can find micromamba. Input TSV and references are staged
inputs, so container tasks do not depend on undeclared host source paths.

The four sample sheets use the six-column schema. The main README describes the
workflow and analysis policies; the superseded Bash pipeline and metadata helper
have been removed. tests/verify_pipeline.py exercises actual Nextflow wiring,
reference cache transitions, resume, validation failures, and publication boundaries.
Local file:// FASTQs are explicit staged path inputs, including both mates.

Style verification uses pixi run checks: ShellCheck, Ruff lint/format, ty,
quantification cases, and mocked Docker builds. The mock build checks cover both
architectures, explicit --no-push, project selection, Git tags, and failure handling.
Synthetic Nextflow stub runs check workflow wiring without biological workloads.
pixi run validate-docker runs the complete real-tool workflow on deterministic
SE/PE fixtures, including the pinned upstream SPP script. Full public dataset
comparisons are still needed to validate biological outputs.
