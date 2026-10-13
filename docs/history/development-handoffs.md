# Earlier development handoffs

These notes were moved from the developer guide on 2026-10-13. Each validation
claim applies to the named revision and environment. For a current checkout, use
the [developer guide](../development.md) and [validation index](../../validation/README.md).

## Current implementation and next work

The completed implementation is on `main`; there are no unpublished local feature
branches or stashes needed to resume it. Milestones:

- `117e5dc`: versioned validation, scientific registry, QC and accountable review.
- `accaf04`: hybrid providers, metadata curation, diagnosis and private model-service management.
- `b04bee2`: README architecture overview and capability status table.

The full update integrates the fork's curation, LLM, bulk ATAC, scATAC and prepared-study
features into lab main, preserving both Git histories and the six earlier lab fixes.
The [promotion validation record](../../validation/reports/lab-main-promotion.md)
records its source revisions, acceptance results and publication checks. The
[original DAP README](dapseq-readme-fb60096.md) and
[current DAP guide](../usage/dapseq-reference.md) preserve the detailed scientific
documentation; read the [upgrade notes](../usage/dapseq-reference.md#upgrade-from-the-dap-only-release)
before reusing existing reference caches or run directories.

The earlier six-PR milestone (#2, #4, #6, #8, #10 and #12) ended at
`fb600968b3abf5d79756aaf7e6d1e4ff43a1b41d`. Its
[review and validation record](../../validation/reports/upstream-pr-review.md) remains
historical evidence for that smaller update, including its issue/merge receipts.

Start with the [README](../../README.md#architecture-and-current-capabilities), the
[shared specification](../curation/IMPLEMENTATION_BRIEF.md), and the
[completed checklist](../curation/CHECKLIST.md). Baseline-audit passages in the
specification describe the earlier checkout; the README and validation reports
describe the implemented state.

For evidence, see [scientific processing](../../validation/reports/supported-atac-execution-validation.md),
[curation and hybrid LLMs](../../validation/reports/hybrid-llm-validation.md), and
[the historical architecture figure](../../validation/reports/architecture-overview-validation.md)
(the overview image has since been removed from the README).
Real API, GPU/SSH service and remote-scheduler acceptance remain separate next
steps. Synthetic metadata tests do not establish real biological annotation
accuracy. The [provider guide](../usage/ai-providers.md#opt-in-live-acceptance) and
[model-service guide](../usage/llm-deployment.md#opt-in-real-local-or-ssh-acceptance)
list the live acceptance commands and prerequisites.

Keep scientific processing deterministic and AI optional. Preserve existing
parameters and resume behavior; metadata changes create reviewed revisions rather
than rewriting executed campaigns. A model proposal is not an approval or a job
operation. Run focused checks while developing and the applicable full suite
before publishing a code change.

## What Git does and does not transfer

Git transfers code, locks, small fixtures, bundled schema/template/icon resources
and recorded validation evidence. The tracked root `.env` contains scientific
image references, not personal API credentials.

Generated environments, caches, build products, reference genomes, sequencing
files, run/work directories, live registry/campaign databases, model weights and
personal credentials are not a GitHub backup. Some validation reports cite large
historical outputs outside Git; the committed reports retain their scope and
recorded evidence. These files are not needed for the synthetic development demo.

If you also need existing scientific data on the new server, transfer it through
your approved storage workflow. Use the documented [registry backup/restore](../usage/curation.md)
path for a consistent catalog snapshot, and preserve worker-qualified artifact
locations. Cloning the code does not relocate data, migrate running jobs or grant
credentials on the new host.

Keep secrets and machine-specific provider/site configurations outside the checkout.
Use the committed example configurations as templates, provision existing approved
credentials on the target host, and inspect `git status` before committing.

## Handoff verification

The [2026-10-13 real-study report](../../validation/reports/real-study-validation.md)
records the current provenance and full scientific study milestone. A fresh lab-main
clone of `f2a1a73` installed successfully and passed documentation, DAP provenance,
study/binary checks and the offline tutorial. All 574 tracked files matched and the
checkout stayed clean; [commands and results](../../validation/evidence/real-study/fresh-clone-details.json)
record the scope. Earlier handoffs below retain their named revisions.

The [2026-10-12 full-update report](../../validation/reports/lab-main-promotion.md)
is the acceptance record for the lab promotion. A fresh lab-main clone of
`aceb6f4` installed successfully and passed CLI help/doctor, 197 documented
CLI recipes and the complete offline tutorial. All 521 tracked files matched and
the checkout stayed clean; see [the handoff receipt](../../validation/evidence/lab-main-promotion/fresh-clone-details.json).
The final evidence follow-up leaves the tested implementation unchanged. Earlier
handoffs below retain their original dates and revisions; their measurements are
not new-server promises.

The prepared-study milestone adds the [complete study workflow](../usage/studies.md),
registry migration 4, version 3 records and separate input/result metadata review.
Its [validation report](../../validation/reports/study-workflow-validation.md) records
current source revisions, full checks, real bigWig validation, packaging and publication
evidence. The earlier handoff below remains historical evidence for its named revision.

A fresh GitHub clone of `a85ba7f` installed successfully and passed all 170 README/guide
command checks, study acceptance with the separate binary reader, and the existing
offline tutorial. All 411 tracked files matched the published checkout and it remained
clean. The full clone/install/focused acceptance took 39.048 seconds using existing
package caches on this Linux host. [Commands and per-step results](../../validation/evidence/study-workflow/github-checkout.json)
record the scope; this is not acceptance on an unspecified destination server.

For focused development, run:

```bash
pixi run uv run --frozen --project genesis_tools python tests/verify_study.py
# Optional existing pyBigWig environment; no dependency is installed by this test.
pixi run uv run --frozen --project genesis_tools python tests/verify_study.py \
  --bigwig-python /path/to/track-environment/bin/python
```

These tests launch real local worker supervisors with a clearly synthetic output
writer. They cover two workers with different data paths, DAP shared controls,
controller restart, collection recovery, input review, stale evidence, binary scans,
reviewed export and failure isolation. They do not execute Nextflow scientific tasks.
The fixture writer lives only in `tests/`; it is not a production CLI mode.

The real scientific study milestone now includes DAP run provenance and opt-in
`pixi run validate-study` acceptance through standard full validation and reviewed export.
See the [test prerequisites and command](../usage/studies.md#real-tool-acceptance-on-synthetic-inputs)
and [recorded evidence](../../validation/reports/real-study-validation.md).

The next acceptance priority is an explicitly authorized SSH worker run on the destination
site, followed by a small reviewed public dataset. Accession-first acquisition and
expert-reviewed biological metadata evaluation remain separate development work. Existing
API/GPU acceptance runners remain opt-in; study commands select no service or hardware.

Implementation map: `study/inputs.py` owns prepared registration; `planning.py` owns
compilation; `staging.py` owns generated documents; `workflow.py` coordinates existing
execution and collection; `collector.py` runs on workers. The execution controller
remains the authoritative scheduler. `registry/store.py` owns scientific records and
migrations, and `curation/review.py` owns scoped decisions and export eligibility.

On 2026-10-10, a fresh GitHub clone of `b04bee2` installed successfully, passed CLI
help/doctor and the complete offline demo, and passed the full check suite in
133.200 seconds after applying the verified plugin-cache recovery above. The first
default suite attempt stopped at the registry lookup; it is recorded as a failure,
not a pass. The checkout stayed clean and contained all 383 tracked files, with no
LFS pointers or submodules. This handoff adds documentation/evidence to that code.

[Recorded commands, results and plugin hashes](../../validation/evidence/development-handoff/checks.json)
and the [full suite log](../../validation/evidence/development-handoff/checks.log)
are committed. This check used a new checkout and new project environments on the
existing Linux host, with existing package caches; it does not claim acceptance
on the as-yet-unspecified destination server or a completely uncached installation.
