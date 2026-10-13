# Plant processing comparison evidence

These files contain measured results and command records from the October 2026
package comparison. See the [reproduction recipe](../../../benchmarks/experiments/plant-methods-20261013/README.md)
for inputs, software, scientific settings and commands.

Each archive has a `manifest.json` with the SHA256 and size of every member.
Archive contents were read back and verified. FASTQs, BAMs, indexes and installed
environments remain outside Git. Paths in archived commands identify the test
server; use the recipe to prepare paths on another server.

| Directory | Scope |
| --- | --- |
| [synthetic-dap](synthetic-dap/) | Verified production BWA-MEM2 2.3 baseline, four methods × three technical repetitions; 12 completed cases |
| [synthetic-atac](synthetic-atac/) | Verified production baseline, eight methods × three technical repetitions; 24 completed cases |
| [whole-workflows](whole-workflows/) | Current Genesis and pinned nf-core ATAC on two public Arabidopsis libraries, one million input pairs each; common metric definitions |
| [workflow-summary](workflow-summary/) | Common workflow table and figure, with renderer and source hashes |
| [acceptance](acceptance/) | Test receipts, complete-workflow logs, software/image records and baseline correction |
| [older-bwa-mem2-2.2.1-synthetic-dap](older-bwa-mem2-2.2.1-synthetic-dap/) | Earlier comparison using the older 2.2.1 package as baseline; 15 completed cases |
| [older-bwa-mem2-2.2.1-synthetic-atac](older-bwa-mem2-2.2.1-synthetic-atac/) | Earlier comparison using the older 2.2.1 package as baseline; 27 completed cases |
| [interrupted-older-baseline-dap-se](interrupted-older-baseline-dap-se/) | Public run stopped after discovering the baseline version-label error; incomplete results and original work retained |
| [failed-14cpu-8gib-fixture](failed-14cpu-8gib-fixture/) | Failed early synthetic configuration; no confirmed OOM diagnosis and no successful timing inferred |

The production BWA-MEM2 package is 2.3 although its executable banner says 2.2.1.
The [binary identity record](../../../benchmarks/experiments/plant-methods-20261013/sources/production-aligner-identity.json)
verifies which native build matches production. The older-baseline records have
not been relabelled as production comparisons.

Synthetic fixtures test integration and known-answer calculations. Complete
workflow runs use different filters and callers; neither a higher retained count
nor a shorter single execution establishes better biological quality.

To inspect an archive without extracting it:

```bash
tar -tzf validation/evidence/method-comparison-20261013/synthetic-dap/evidence.tar.gz
```

To inspect the offline report and full records, extract into a new directory:

```bash
mkdir -p /scratch/genesis-evidence
tar -xzf validation/evidence/method-comparison-20261013/synthetic-dap/evidence.tar.gz \
  -C /scratch/genesis-evidence
```

Open `/scratch/genesis-evidence/report.html` in a browser. Files intentionally
excluded from the archive cannot be used to resume execution; regenerate them
from the pinned inputs in a new result directory.
