# Lab repository PR review and merge validation

> Validation record for the revision and date below. Use the
> [current task guides](../../docs/README.md) for a new analysis. Recorded temporary
> paths identify the original test environment.

Observed: 2026-10-13 UTC / 2026-10-12 America/New_York.

All six open PRs in `kundajelab/genesis-preprocessing` were reviewed, tested and
merged. Their six linked issues closed automatically. The final API snapshot has
zero open issues and zero open PRs. This is a record of source review and locally
executed tests, not a GitHub CI run or an independent human approval.

## Revisions and scope

- Lab baseline: `4468c712e4c171b573e2ec2806fdc5327b5379e9`.
- Local combined test candidate: `9fa85ca9b2d3548fe30d5accaeffa1d6acb26b53`.
- Tested Git tree: `ecf1857fcdbdb2566ca5343a67b37e0d81629ab8`.
- [Merged lab main](https://github.com/kundajelab/genesis-preprocessing/commit/fb600968b3abf5d79756aaf7e6d1e4ff43a1b41d):
  `fb600968b3abf5d79756aaf7e6d1e4ff43a1b41d`, with exactly that tested tree.
- Development fork baseline: `4d5aa600acb29fb1662231dc830e0e3785b76d7a`.
- [Tested development fork fix](https://github.com/YaoxiangLi/genesis-preprocessing/commit/b44061d5a881cf8a3a546d982312af1894bba5d5):
  `b44061d5a881cf8a3a546d982312af1894bba5d5`.

The temporary candidate's merge commits are local review artifacts; the published
lab commit is the reproducible source revision. Each GitHub merge used its exact
reviewed head SHA. The resulting tree and parents were checked after every merge.
The final tree was also compared with the locally tested candidate using Git.
No scientific parameters, dependency locks, image pins or fixture expectations
were changed during review.

| PR | Change | Linked issue | Review result |
| --- | --- | --- | --- |
| [#2](https://github.com/kundajelab/genesis-preprocessing/pull/2) | Run Docker BAM inspections as the invoking UID/GID | [#1](https://github.com/kundajelab/genesis-preprocessing/issues/1) | Default image user fails on a mode-0700 fixture; invoking user succeeds. Full fixture reads 15 BAMs. |
| [#4](https://github.com/kundajelab/genesis-preprocessing/pull/4) | Resolve Git tags only when a build needs a default | [#3](https://github.com/kundajelab/genesis-preprocessing/issues/3) | Mocked build tests cover explicit/default/missing tags, help, both builders and unchanged files on errors. No image builds or pushes. |
| [#6](https://github.com/kundajelab/genesis-preprocessing/pull/6) | Use a writable task-local Matplotlib cache | [#5](https://github.com/kundajelab/genesis-preprocessing/issues/5) | All 10 real track task invocations across initial/resume runs omit the temporary-cache warning. |
| [#8](https://github.com/kundajelab/genesis-preprocessing/pull/8) | Document duplicate handling separately for BAMs, peaks and quantification | [#7](https://github.com/kundajelab/genesis-preprocessing/issues/7) | Checked the workflow, counting implementation and pinned MACS3 behavior; documentation changes only. |
| [#10](https://github.com/kundajelab/genesis-preprocessing/pull/10) | Reject reference filenames mapping to the same derived ID | [#9](https://github.com/kundajelab/genesis-preprocessing/issues/9) | Unit, stub and real-container checks reject the collision in `VALIDATE_SHEET` before any download. |
| [#12](https://github.com/kundajelab/genesis-preprocessing/pull/12) | Add standalone reference-cache provenance helpers | [#11](https://github.com/kundajelab/genesis-preprocessing/issues/11) | Fixed incomplete-provenance acceptance and retained both new test commands during integration. |

Exact heads, merge commits and tree checks are in
[merges.json](../evidence/upstream-pr-review/merges.json). Final
[PR](../evidence/upstream-pr-review/prs-after.json) and
[issue](../evidence/upstream-pr-review/issues-after.json) snapshots record the
merged/closed states and timestamps.

PR #8 was checked against the official [MACS3 callpeak documentation](https://macs3-project.github.io/MACS/docs/callpeak.html)
and [v3.0.5 BAM parsers](https://github.com/macs3-project/MACS/blob/v3.0.5/MACS3/IO/Parser.py).
The pinned peak-calling image reports `macs3 3.0.5`. Its BAM parsing mask does not
exclude the duplicate flag; the default peak-calling duplicate limit is a separate
operation. The Genesis quantifier counts paired read ends independently and its
flag filter does not exclude duplicate-marked records.

## Findings corrected before merge

The original PR #12 verifier accepted missing source names, missing compressed
FASTA digests, missing generator versions and a boolean schema version.
[Reproduction](../evidence/upstream-pr-review/pr12-reproduction.log) and the
[failing regression](../evidence/upstream-pr-review/pr12-regression-before.log)
were captured before the fix.

Commit `35eab454cb3e3229586e7b47a88defa618a05370` requires an integer schema
version, complete correctly typed provenance fields, valid recorded SHA256
strings and nonempty generator version output. Version output on stderr is
supported. A writer receiving no version output fails before replacing an existing
manifest. Tests cover missing/malformed fields, version output on either stream
and preservation of the prior manifest on failure. The original gzip-metadata,
renamed-source, same-size/same-mtime content, damaged/missing/extra product and
stub/real checks remain intact. The same fix is on the development fork.

PRs #4 and #12 both added a line at the same location in `scripts/check-projects.sh`.
The integration conflict was resolved by keeping both `verify_build_tags.py` and
`verify_reference_cache.py`. Updating PR #12 with merged upstream main produced
head `dd068ae28bcf1aba28502ac16d0eafea25a7ba29`; its full Git tree matches the
tested candidate, so no untested source changes were introduced by that update.

## Executed validation

| Check | Status | Evidence |
| --- | --- | --- |
| Upstream baseline `pixi run checks` | PASS | [Log](../evidence/upstream-pr-review/baseline-checks.log) |
| Combined candidate `pixi run checks` | PASS | [Log](../evidence/upstream-pr-review/candidate-checks.log) |
| Focused Docker UID/GID reproduction | PASS | [Log](../evidence/upstream-pr-review/pr2-permissions.log) |
| Reference-cache regression after correction | PASS | [Log](../evidence/upstream-pr-review/pr12-regression-after.log) |
| Real `pixi run validate-docker --keep` | PASS | [Log](../evidence/upstream-pr-review/candidate-docker.log) |
| Development fork `pixi run checks` | PASS | [Log](../evidence/upstream-pr-review/fork-checks.log) |
| Every merged GitHub tree equals the reviewed candidate for that stage | PASS | [Merge receipts](../evidence/upstream-pr-review/merges.json) |

The real Docker fixture used five deterministic SE/PE libraries, the committed
images by digest, 34 successful initial tasks and 15 inspected BAMs. The first
resume completed 27 tasks and reused 3; the stable resume reused all 30 tasks.
The deliberate reference-collision run has exactly one failed `VALIDATE_SHEET`
task and no download tasks. This expected failure is a passing negative test.
[Trace summaries and fixture hashes](../evidence/upstream-pr-review/docker-fixture-summary.json)
and adjacent trace TSVs preserve the observations.

The fork's full checks cover existing DAP/ATAC fixtures, execution, curation,
registry/review, provider and deployment mocks, prepared studies, scATAC and
182 documented CLI commands. Their live-provider, GPU/SSH and biological-accuracy
limitations remain unchanged; passing synthetic tests does not validate those.

[Command receipts and log digests](../evidence/upstream-pr-review/checks.json)
record exit codes and source revisions. Published logs omit trailing line-end
whitespace; receipts retain the original capture digest wherever it differs.
[Environment evidence](../evidence/upstream-pr-review/review-environment.json)
records changed-source hashes, all five image references and plugin hashes.
The checks used Python 3.14.5, Pixi 0.81.0, uv 0.11.33, ruff 0.16.10,
ty 0.0.84, Nextflow 25.10.4 and Docker client/server 29.1.3/29.8.0.
The existing Pixi `system-requirements` warning remains. Installation across
filesystems also reported uv's existing copy fallback; neither was suppressed
by changing dependency manifests. Aggregate host memory/network use and pipeline
throughput were not measured.

## Reproduce and continue

For the reviewed lab version, use a fresh checkout of the published commit:

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
that [failed attempt](../evidence/upstream-pr-review/candidate-docker-unshared-path.log)
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

Continue the broader Genesis development from
[`YaoxiangLi/genesis-preprocessing`](https://github.com/YaoxiangLi/genesis-preprocessing)
using the [handoff guide](../../docs/development.md). These six upstream PRs do not
transfer the fork's curation, LLM, bulk-ATAC or scATAC extensions to the lab repo.
In upstream, #12 deliberately adds standalone helpers; production cache
enforcement and migration instructions remain a separate follow-up. The issue
was closed according to that explicitly scoped first increment.
