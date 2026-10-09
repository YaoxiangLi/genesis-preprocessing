# ADR: independent raw-read FastQC branch

Date: 2026-10-07. Status: implemented and validated; local commit `430cfe31aab5fb9638d18c75a087a9bcb7a868c5`.
Baseline: `4468c712e4c171b573e2ec2806fdc5327b5379e9`. Branch: `validation/fastqc`.

## Decision before implementation

Add `FASTQC` immediately downstream of `DOWNLOAD`, once per downloaded mate, on
an independent DSL2 channel branch. SE produces one task; PE produces two tasks.
Metadata and alignment retain their existing input channel and original files.
FastQC is observational: no trimming, filtering, duplicate removal, MAPQ changes,
reference changes, or dependency from alignment to a FastQC quality assessment.

Use an isolated `DAP_SEQ_FASTQC` environment rather than modifying `DAP_SEQ_QC`.
The existing QC environment contains R/SPP and samtools; adding Java/FastQC there
would expand dependency resolution and change the container identity/cache of
scientific QC tasks. A separate environment bounds the change and permits an
independent version upgrade. Pin FastQC **0.12.1**, generate the project's normal
YAML-derived Pixi TOML/lock, and build with its existing digest-pinned
`dockers/pixi-yaml.Dockerfile`. Existing environment manifests/locks and scientific
image references remain unchanged. User authorization to add FastQC overrides the
AGENTS.md general guidance to avoid new dependencies.

Keep one CPU, 1 GB task memory, a 512 MB FastQC heap and four-hour time per mate.
Use explicit FASTQ format and `--noextract`. Require nonempty HTML and ZIP outputs,
and record `fastqc --version`. Publish under
`output/<species>/<sample_id>/qc/fastqc/`, with downloaded basenames retaining
`.read1` or `.read2`. Do not publish FASTQs or intermediate extraction trees.

FastQC PASS/WARN/FAIL module labels are retained verbatim, with no dataset rejection
based on those labels. Plant/assay-specific thresholds are UNSPECIFIED. Actual
execution failures or missing reports remain computational failures, not biological
failures. Empty/corrupt inputs are tested explicitly; existing DOWNLOAD gzip and
nonzero line-count checks are retained unchanged.

FastQC's documented purpose is raw sequence QC, with HTML and machine-readable
reports; it does not establish assay suitability. [Official FastQC documentation](https://www.bioinformatics.babraham.ac.uk/projects/fastqc/).

## Validation plan

- Use existing deterministic SE/PE fixture: three SE libraries and two PE libraries,
  hence seven FastQC tasks and seven HTML/ZIP pairs. Assert identities, report content,
  ZIP integrity, publication, original/downloaded input SHA256 equality, and mate counts.
- Require all FastQC tasks cached on resume, report checksums unchanged, and a stable
  resume of existing scientific tasks. No assertion is weakened to accommodate a failure.
- Exercise module behavior on valid low-complexity reads with QC FAIL labels, empty,
  malformed and corrupt gzip inputs; preserve errors and distinguish computational
  failures from quality flags.
- Compare all alignment BAMs and published scientific outputs against retained
  unmodified-baseline artifacts. Compare bytes first; inspect metadata-only differences
  (e.g. gzip/PDF timestamps or BAM command paths) separately and compare semantic content.
- Run focused tests, full `pixi run checks`, and `pixi run validate-docker --keep`.
  Existing Docker BAM-inspection helper lacks the workflow's explicit caller UID/GID;
  baseline audit/03 demonstrated permission failure. If needed, correct only that helper
  to run as the caller, preserving every BAM assertion; identify this separately in report.

## Local container and reproducibility boundary

No image will be pushed. The existing build wrapper fails before parsing options in
this tagless clone (`git describe --tags`). Do not change those scripts or fabricate
an upstream tag: invoke the same Dockerfile directly with the new locked environment.
Record exact command, base digests, platform and local image ID. A local image ID is
immutable but is not a registry digest or a remotely pullable artifact. Document this
limitation and require an explicit publication step for remote Docker/Apptainer use.

Reports and experiments remain outside upstream source under design/, reports/,
results/fastqc/ and scratch/fastqc/. Source and tests are committed locally only.

## Findings and implementation refinements

The isolated image resolves FastQC `0.12.1-hdfd78af_0` and Java 25.0.2 for Linux;
Nextflow retains its separate Java 23.0.2 runtime. Only the new environment was
resolved. The local image ID is
`sha256:97ca1e181a55a1d87653984956983fea3ff76cab5875f45ae2143168ff4fd73d`.

The first real run exposed Fontconfig's unwritable cache directory under the
caller's UID. FASTQC now creates its own `XDG_CACHE_HOME` inside the task directory;
this cache is not published. Original diagnostics were retained, then focused,
full-check and Docker validation were repeated after the fix.

A short quality string is accepted by FastQC 0.12.1. The initial experimental
assertion expecting rejection failed and remains in retained logs. Inspection of
its [versioned parser source](https://raw.githubusercontent.com/s-andrews/FastQC/v0.12.1/uk/ac/babraham/FastQC/Sequence/FastQFile.java)
confirmed that it checks record structure but not equal sequence/quality lengths.
The test cases now distinguish this observed parser limitation from missing `+`
separators and gzip corruption. A complete FASTQ structural validator is outside
this observational-QC change; the existing bounded metadata checks remain intact.
This is not evidence that malformed FASTQ is scientifically acceptable.

Buildx was missing; official v0.37.2 was installed under the user's Docker CLI
plugin directory after matching the release SHA256. No sudo, Docker daemon,
group, socket permission or credential change was needed. See the validation
report for exact build commands, digests, unsuccessful attempts and resource logs.
