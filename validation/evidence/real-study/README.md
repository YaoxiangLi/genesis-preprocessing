# Real study evidence, 2026-10-13

These are observations from clean implementation revision
`311567b7c327ad1fc9b177f193b4b5e1951e02e5`. The [report](../../reports/real-study-validation.md)
explains the commands, failures found and repaired, limits and rollback.

- `real-study`, `real-dap`, `real-atac`, `full-checks` and `installed-wheel` JSON/log pairs
  record exact commands, start times, exit codes, durations, environment overrides and log hashes.
- `study-commands.json` records all 145 public CLI calls and original log hashes.
  Public command arguments and the logs in `study-cli-logs.tar.gz` omit review-state tokens.
  `study-summary.json` records all export denominators, job/task counts and provenance identities.
- `scientific-invariance.json` records 59 exact scientific artifact hashes compared with the
  comparison baseline; narrowPeak gzip payloads are compared after decompression.
- Raw trace TSVs preserve measured task resources. Requested reservations, process peak RSS,
  host memory and network traffic are different quantities; no host/network claim is made.
- `initial-*.log` retains failures discovered before the fixes. None is counted as a pass.
- `runners/` holds the actual observation scripts with this host's temporary paths. Use the
  documented Pixi commands on another server instead of reusing these historical paths.

Large synthetic inputs, FASTQs/BAMs, Nextflow work directories, environments and registries
are not a GitHub backup. All review decisions in acceptance were explicitly synthetic.
The ordinary test suite remains Docker-free; real tools require the opt-in command.

`fresh-clone*` and `final-docs*` record installation from a clean checkout and
documentation checks at the tested revision.

`study-cli-logs.tar.gz` contains all 290 CLI stdout/stderr files as sanitized publication
copies. [publication-manifest.json](publication-manifest.json) records original and
published SHA-256 digests for each member and the sanitized standalone files.
The original member digests match `study-commands.json`; published member digests
verify the archive available here. Review-state fingerprints are concurrency checks,
not authentication credentials. Their public values are replaced with `REDACTED`;
these log snapshots are evidence for inspection, not replayable review inputs.
Scientific measurements and artifact checksums are unchanged.
The owned temporary checkouts, environments, registries and large
scientific work products were removed after the compact evidence and logs were archived.
