# MACS3 builds and peak-calling resources

DAP-seq peak calling builds MACS3 from upstream source. The DAP environment,
`environments/GENESIS_MACS3.yaml`, and its image pin revision
`da19e1dcbf3a2ff06ab906abc0658edb0c7e82d1`. It includes the callpeak
optimization, later fixes to worker cleanup, process safety and concurrent
scoring, and a CPU budget (`--threads`) that bounds MACS3's threads and worker
processes. The package still reports `macs3 3.0.5`; the pinned revision in the
environment lock and `genesis-images.lock` distinguishes it from the released 3.0.5
package.

## Profiles and images

The DAP profiles (`local,docker`, `nersc`, `sherlock`) use this
environment's image. Until a rebuilt image is published,
`conf/genesis-images.lock` may still name an earlier peak-calling image for container
profiles. Each run copies that lock to its output folder as `genesis-images.lock`
(see [DAP run records](dapseq-reference.md#run-records)).

Source builds require a C compiler, zlib headers and the pinned SIMDe Git
submodule; the environment declares these build dependencies. Do not substitute
a GitHub source archive: it omits the submodule. Native macOS and ARM builds
require their own acceptance tests; resolving their lock entries does not
validate them.

Bulk ATAC uses the same pinned peak-calling image as DAP-seq.

## CPU limits

DAP peak calling runs `macs3 callpeak` directly with `--threads` set to the
task's CPU allocation. The budget includes MACS3's calling thread and bounds its
threads and peak worker processes on any operating system. MACS3 starts peak
worker processes only on Linux; elsewhere those phases run serially. A container
or scheduler CPU limit remains the outer bound.

The DAP peak-calling process requests four CPUs, 1 GB plus a quarter of the
treatment and control BAM sizes, and one hour, retrying twice with more memory and
time if killed. On a Sorghum sample, peaks were identical at every CPU budget and eight CPUs
were no faster than four. Use explicit Nextflow process overrides to change resources; faster
execution can use more memory. The caller's thresholds, controls, genome size,
duplicate policy and input formats are unchanged.

Bulk ATAC also calls `macs3 callpeak` directly with `--threads ${task.cpus}`; its peak, summit
and XLS outputs match released MACS3 3.0.5.
