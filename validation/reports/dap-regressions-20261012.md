# DAP regression validation — October 2026

> Validation record for the revision and date below. Use the
> [current task guides](../../docs/README.md) for a new analysis. Recorded temporary
> paths identify the original test environment.

Observed: 2026-10-13 UTC / 2026-10-12 America/New_York.

These checks cover reference-cache provenance, container file permissions,
Docker build configuration, track rendering and duplicate-count semantics.
They use synthetic sequencing fixtures and the pinned scientific images.

## Tested source and regression cases

- Comparison baseline: `4468c712e4c171b573e2ec2806fdc5327b5379e9`.
- Combined test revision: `9fa85ca9b2d3548fe30d5accaeffa1d6acb26b53`.
- Source tree: `ecf1857fcdbdb2566ca5343a67b37e0d81629ab8`.
- Reproducible revision with that tree: `fb600968b3abf5d79756aaf7e6d1e4ff43a1b41d`.
- Additional full-suite test revision: `b44061d5a881cf8a3a546d982312af1894bba5d5`.

Scientific parameters, dependency locks, image pins and fixture expectations were
unchanged in this comparison.

| Behavior | Observed result |
| --- | --- |
| Container BAM inspection | The default image user cannot read a mode-0700 fixture; the invoking UID/GID can. The complete fixture inspects 15 BAMs. |
| Docker build tags | Explicit/default/missing tags, help, both builders and unchanged files on errors are covered by mocked builds. |
| Matplotlib cache | All 10 real track task invocations across initial/resume runs omit the temporary-cache warning when using a writable task-local cache. |
| Duplicate semantics | BAM retention, MACS3 duplicate limits and independent read-end quantification were checked against the implementation. |
| Reference name collisions | Unit, stub and real-container checks reject colliding reference IDs in `VALIDATE_SHEET` before downloads. |
| Reference-cache provenance | Missing and malformed provenance is rejected; valid source and generator identities are required. |

Duplicate handling was checked against the official [MACS3 callpeak documentation](https://macs3-project.github.io/MACS/docs/callpeak.html)
and [v3.0.5 BAM parsers](https://github.com/macs3-project/MACS/blob/v3.0.5/MACS3/IO/Parser.py).
The pinned peak-calling image reports `macs3 3.0.5`. Its BAM parsing mask does not
exclude the duplicate flag; the default peak-calling duplicate limit is a separate
operation. The Genesis quantifier counts paired read ends independently and its
flag filter does not exclude duplicate-marked records.

## Reference-cache regression

The earlier reference-cache verifier accepted missing source names, missing compressed
FASTA digests, missing generator versions and a boolean schema version.
[Reproduction](../evidence/dap-regressions-20261012/pr12-reproduction.log) and the
[failing regression](../evidence/dap-regressions-20261012/pr12-regression-before.log)
were captured before the fix.

Commit `35eab454cb3e3229586e7b47a88defa618a05370` requires an integer schema
version, complete correctly typed provenance fields, valid recorded SHA256
strings and nonempty generator version output. Version output on stderr is
supported. A writer receiving no version output fails before replacing an existing
manifest. Tests cover missing/malformed fields, version output on either stream
and preservation of the prior manifest on failure. The original gzip-metadata,
renamed-source, same-size/same-mtime content, damaged/missing/extra product and
stub/real checks remain intact.

## Executed validation

| Check | Status | Evidence |
| --- | --- | --- |
| Baseline `pixi run checks` | PASS | [Log](../evidence/dap-regressions-20261012/baseline-checks.log) |
| Combined candidate `pixi run checks` | PASS | [Log](../evidence/dap-regressions-20261012/candidate-checks.log) |
| Focused Docker UID/GID reproduction | PASS | [Log](../evidence/dap-regressions-20261012/pr2-permissions.log) |
| Reference-cache regression after correction | PASS | [Log](../evidence/dap-regressions-20261012/pr12-regression-after.log) |
| Real `pixi run validate-docker --keep` | PASS | [Log](../evidence/dap-regressions-20261012/candidate-docker.log) |
| Additional revision `pixi run checks` | PASS | [Log](../evidence/dap-regressions-20261012/fork-checks.log) |

The real Docker fixture used five deterministic SE/PE libraries, the committed
images by digest, 34 successful initial tasks and 15 inspected BAMs. The first
resume completed 27 tasks and reused 3; the stable resume reused all 30 tasks.
The deliberate reference-collision run has exactly one failed `VALIDATE_SHEET`
task and no download tasks. This expected failure is a passing negative test.
[Trace summaries and fixture hashes](../evidence/dap-regressions-20261012/docker-fixture-summary.json)
and adjacent trace TSVs preserve the observations.

The additional full-suite test covers existing DAP/ATAC fixtures, execution, curation,
registry/review, provider and deployment mocks, prepared studies, scATAC and
182 documented CLI commands. Their live-provider, GPU/SSH and biological-accuracy
limitations remain unchanged; passing synthetic tests does not validate those.

[Command receipts and log digests](../evidence/dap-regressions-20261012/checks.json)
record exit codes and source revisions. Published logs omit trailing line-end
whitespace; receipts retain the original capture digest wherever it differs.
[Environment evidence](../evidence/dap-regressions-20261012/review-environment.json)
records changed-source hashes, all five image references and plugin hashes.
The checks used Python 3.14.5, Pixi 0.81.0, uv 0.11.33, ruff 0.16.10,
ty 0.0.84, Nextflow 25.10.4 and Docker client/server 29.1.3/29.8.0.
The existing Pixi `system-requirements` warning remains. Installation across
filesystems also reported uv's existing copy fallback; neither was suppressed
by changing dependency manifests. Aggregate host memory/network use and pipeline
throughput were not measured.

## Reproduce the tests

Use a fresh checkout of the recorded revision:

```bash
git clone https://github.com/kundajelab/genesis-preprocessing.git
cd genesis-preprocessing
git switch --detach fb600968b3abf5d79756aaf7e6d1e4ff43a1b41d
pixi run install-all
pixi run checks
pixi run validate-docker --keep
```

The last command requires working Docker and the five digest-pinned images.
It uses synthetic sequencing inputs and a temporary HTTP fixture server.
The initial test from this host's `/tmp` failed because Snap Docker could not see
the bind-mounted checkout (`.command.run: No such file or directory`);
that [failed attempt](../evidence/dap-regressions-20261012/candidate-docker-unshared-path.log)
is preserved. A fresh checkout under the verified daemon-visible `/var/tmp`
completed successfully. The development checkout under `/data/homes` was also
invisible to this daemon. Use a location visible to your Docker daemon; no Docker
permissions, daemon settings or host security policy were changed here.

Nextflow checks used the already verified plugin cache with `NXF_PLUGINS_DIR`
and `NXF_OFFLINE=true`. On another server, populate the pinned plugins first;
see the [plugin recovery instructions](../../docs/development.md#recovery-when-plugin-lookup-fails).
Recorded absolute paths identify this test run and should not be copied into a
new server configuration. Generated environments and large fixture outputs are
not included in this evidence snapshot.

At this revision, reference-cache helpers were tested independently; integration
into the production workflow was not part of these tests. See the
[current DAP guide](../../docs/usage/dapseq-reference.md) for present cache behavior.
