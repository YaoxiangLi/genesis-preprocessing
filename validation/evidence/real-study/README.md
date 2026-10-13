# Real study evidence, 2026-10-13

These are observations from clean implementation revision
`311567b7c327ad1fc9b177f193b4b5e1951e02e5`. The [report](../../reports/real-study-validation.md)
explains the commands, failures found and repaired, limits and rollback.

- `real-study`, `real-dap`, `real-atac`, `full-checks` and `installed-wheel` JSON/log pairs
  record exact commands, start times, exit codes, durations, environment overrides and log hashes.
- `study-commands.json` records all 145 public CLI calls and hashes of their full logs, archived verbatim in `study-cli-logs.tar.gz`.
  `study-summary.json` records all export denominators, job/task counts and provenance identities.
- `scientific-invariance.json` records 59 exact scientific artifact hashes compared with the
  preceding lab revision; narrowPeak gzip payloads are compared after decompression.
- Raw trace TSVs preserve measured task resources. Requested reservations, process peak RSS,
  host memory and network traffic are different quantities; no host/network claim is made.
- `initial-*.log` retains failures discovered before the fixes. None is counted as a pass.
- `runners/` holds the actual observation scripts with this host's temporary paths. Use the
  documented Pixi commands on another server instead of reusing these historical paths.

Large synthetic inputs, FASTQs/BAMs, Nextflow work directories, environments and registries
are not a GitHub backup. All review decisions in acceptance were explicitly synthetic.
The ordinary test suite remains Docker-free; real tools require the opt-in command.

`publication.json` verifies the lab and fork remote heads. `fresh-clone*` and
`final-docs*` record the published checkout handoff and documentation checks.
The final evidence-only commit leaves the tested implementation unchanged.

`study-cli-logs.tar.gz` contains all 290 CLI stdout/stderr files; each digest matches
`study-commands.json`. The owned temporary checkouts, environments, registries and large
scientific work products were removed after the compact evidence and logs were archived.
