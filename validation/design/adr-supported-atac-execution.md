# ADR: supported paired-end ATAC and explicit deployment

Date: 2026-10-09. Status: implemented; live remote-site acceptance remains outstanding.

## Decision

Use a dedicated bulk ATAC workflow with an explicit lane/library/reference
contract. Keep DAP-seq scientific policy unchanged. Local Docker is the default;
schedulers require an explicit profile. Share pinned environments where the
underlying tool fits, while retaining separate assay processing and metrics.

ATAC streams BAM templates and spills coordinate counts to SQLite. It writes
indexed fragments and cut-site signal without holding the whole BAM in memory.
Adapters, MAPQ and duplicate retention are explicit inputs. Mitochondrial and
plastid counts remain separate. Biological replicates are not merged; comparisons
are descriptive peak overlap, not IDR or a biological acceptance threshold.

Each invocation verifies reference and FASTQ checksums. Task source bundles are
immutable and their SHA256 is an explicit Nextflow input. A directory path alone
is insufficient cache identity: the public-data resume reproduced stale reuse
after a helper edit. The regression now mutates only an isolated helper copy and
requires the affected tasks to rerun, followed by a fully cached stable resume.
JSON metadata is materialized before concurrent task dispatch; lazy map
initialization caused an observed resume race.

Use native scheduler executors for Slurm, PBS Pro, LSF and SGE. NERSC uses a
command-scoped Podman-HPC adapter located on shared storage; Sherlock uses
Apptainer. Authentication, scheduler services and permissions remain site-managed.
No remote deployment is described as validated without a live acceptance run.

Independent SSH workers execute complete analysis units through a persistent
controller. Inputs are explicitly prestaged and verified on each worker. A
controller-local SQLite ledger reserves immutable attempt IDs before launch.
Detached worker supervisors publish atomic heartbeats and terminal status.
The controller reconnects instead of assuming that a lost connection killed work.

Only explicit temporary failures receive automatic retries, capped at two.
Other failures require review. Unknown workers keep their capacity reserved.
Reconciliation requires a human to verify that prior processes and scheduler
jobs have stopped; fresh active heartbeats block it. The localhost browser page
is read-only. Human actions are CLI operations with recorded notes.

## Alternatives and limits

A custom SSH executor for individual Nextflow tasks would duplicate scheduler
responsibilities and complicate data placement. Whole analysis units give clear
failure isolation; treatments sharing a DAP control must remain together.
Automatic credential provisioning and automatic transfer of private datasets
are outside the execution contract.

A controller with database services, distributed locks and automatic failover
would add operational dependencies before there is evidence they are needed.
This implementation uses one active controller and local SQLite state. It does
not claim high-availability controller failover or tested hundred-node throughput.
Worker slots limit concurrent jobs; Nextflow resource limits and site allocations
still govern memory, CPU and wall time.

Public validation uses positional 200,000-pair subsets from two Arabidopsis and
two maize libraries. These establish computational coverage across two genome
sizes; they do not reproduce full-depth published biological results. Plant
pass/fail thresholds remain UNSPECIFIED. See the validation report for exact
references, commands, versions, failures and measured resource costs.
