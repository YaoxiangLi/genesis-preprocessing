# MACS3 builds and peak-calling resources

Genesis supports the optimized upstream MACS3 revision
`22eb40f7b51f5b20b635614ca0b1759dc5398c5c`. It includes the callpeak optimization
and subsequent fixes to worker cleanup, process safety and concurrent scoring.
The package still reports `macs3 3.0.5`; use the source revision in
`macs3.runtime.json` to distinguish it from the released 3.0.5 package.

## Select the source-pinned build

For DAP-seq on Linux, use the opt-in native environment profile:

```bash
genesis pipeline -p local,macs3_optimized -n study-optimized samples.tsv \
  --references /data/references
```

This profile enables Conda execution and disables Docker/Apptainer. It installs
the exact Git revision for peak calling; the other tools keep their existing
environments. Installation requires access to the package channels and upstream
Git repository. Use a new run name when comparing builds.

The source build requires a C compiler, zlib headers and the pinned SIMDe Git
submodule. The environment declares these build dependencies. Do not substitute
a GitHub source archive: it omits the submodule. The separate Pixi manifest and
lock in `environments/macs3-optimized/` provide a fully resolved environment for
standalone comparisons and container builds. Native macOS and ARM builds require
their own acceptance tests; resolving their lock entries does not validate them.

The public image pins used by default DAP, bulk ATAC and scATAC workflows still
refer to the released peak-calling image until a verified replacement is
published. Selecting a source environment does not update those images. The
scATAC workflow ingests existing fragments and calls peaks from BEDPE pseudobulks;
it does not process scATAC FASTQs or switch to MACS3's FRAG mode.

## CPU limits and provenance

Each peak call uses the task's requested CPU allocation. On Linux the launcher
narrows the inherited CPU affinity mask and limits numerical-library threads to
one before MACS3 starts. It never widens a scheduler allocation. Local calls
rotate their starting CPU within that mask to avoid always selecting its first
core; this does not reserve exclusive CPUs. The executable is selected from the
same Python environment as the recorded package metadata. This matters
because MACS3 derives its worker count from affinity, while a container CPU quota
alone can leave more CPUs visible.

`macs3.runtime.json` records the package version, available source identity,
launcher checksum, requested CPUs and effective affinity. DAP filenames begin
with the sample ID. These receipts identify execution; they do not approve QC or
model readiness. Released-package execution on non-Linux hosts is retained with
resource enforcement reported as NOT_ASSESSED. The optimized source launcher
requires Linux affinity support.

Defaults remain one CPU and 1 GB for the DAP peak-calling process; bulk ATAC keeps
its existing configured task limits, and scATAC products keep two CPUs and 8 GB.
Use explicit Nextflow process overrides to change resources. Benchmark results
at eight CPUs do not imply the same speedup at one CPU, and faster execution can
use more memory. The caller's thresholds, controls, genome size, duplicate policy
and input formats are unchanged.

## Compare versions or roll back

See the [measured results](../../validation/reports/macs3-optimization.md) for
performance, output agreement and the limits of the acceptance tests.

The [comparison recipe](../../benchmarks/experiments/macs3-optimization/README.md)
uses the same existing inputs and scientific arguments for both builds, with
1, 2 and 8 CPUs and three measured repetitions. It checks peak coordinates,
summits and scientific XLS fields before interpreting speedups. Timings cover
peak calling rather than the complete preprocessing pipeline.

To use the released caller again, omit `macs3_optimized` and select an existing
profile such as `local,conda` or `local,docker`, with a new run name. Historical
benchmark environments and results remain version-specific; do not overwrite
results from one caller build with those from another.
