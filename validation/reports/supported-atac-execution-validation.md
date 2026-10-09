# Bulk ATAC and distributed execution validation

Date: 2026-10-09. Platform: Ubuntu 24.04, Linux amd64, 32 CPUs, approximately
115 GiB RAM. This report covers supported paired-end bulk ATAC, local execution,
deployment profiles and the dataset controller. It does not establish biological
quality or live remote-site performance.

## Result and scope

The formal ATAC workflow processes explicit libraries and references, keeps
biological replicates separate, and produces fragments, cut-site tracks, peaks
and QC. Standalone Linux with Docker is the default. Native scheduler profiles
and an SSH worker protocol provide deployment options; authentication remains
under site control. A persistent controller isolates failed datasets, limits
temporary retries and exposes unresolved work for human review.

The comparison starts at fork commit
`4b682f700d539698b271ca652306f46b6230aea1`. The final production-code commit is
`bad67391acda37a53f584b7ded9cbdf27096aa2b`; later commits retain evidence and
documentation. The original upstream audit baseline remains
`4468c712e4c171b573e2ec2806fdc5327b5379e9`.

Commands, exact revisions, input checksums, elapsed time, exit status and retained
log locations are recorded in `validation/evidence/supported-atac/commands.json`.
Full logs and large outputs remain under workspace `results/incremental-prs/`
and `results/supported-atac/`. GNU time measures the launcher process tree;
Nextflow trace RSS measures individual tasks, not aggregate host peak memory.

## Tests and observed results

| Test | Result | Evidence |
| --- | --- | --- |
| Full `pixi run checks` | PASS | Python lint/format/types, shell checks, Nextflow stubs, reference rejection, benchmark, execution and deployment checks |
| `pixi run validate-atac --keep` | PASS | Two libraries, two technical lanes each, distinct biological replicates; real pinned tools |
| Stable synthetic resumes | PASS | All 21 tasks cached on two consecutive resumes |
| Helper-source mutation | PASS | Isolated helper change reruns all eight Python-backed tasks and affected descendants; old source bundle unchanged; next 21-task resume cached |
| Raw and scientific preservation | PASS | Raw fixture checksums and scientific outputs unchanged across stable resumes and a behavior-neutral helper edit |
| Adapter known answer | PASS | Both 53-base raw mates remain unchanged; declared adapter removal yields exactly 40-base inserts and qualities; report published |
| Output publication | PASS | FastQC HTML/ZIP, required MultiQC parsed modules, adapter JSON and MACS3 version present; no raw FASTQs or BAMs published |
| DAP Docker regression | PASS | SE/PE, control reuse, reference reuse, failures and resume assertions retained |
| DAP scientific comparison | PASS | 51 scientific files equal; BAM records equal after excluding variable headers |
| Public plant integration | PASS | Four libraries, 42 tasks; 17 input hashes unchanged; independent fragment/FRiP/track/QC checks passed |
| Public stable resumes | PASS | 42/42 tasks cached on each final resume; 28 scientific files byte-identical |
| Controller isolation | PASS | Two healthy jobs succeeded; invalid checksum entered review; 45.84 seconds |
| Browser status page | PASS | GET `/` 200; unknown file path 404; POST 501; localhost only |
| SVG rendering | PASS | Visually inspected ATAC and execution maps; no label overlap or routes crossing labels; animation and reduced motion checked |
| Remote scheduler execution | NOT VERIFIED | Profiles parse locally; no live NERSC, Sherlock or other remote allocation available |

The final full suite took 105.97 seconds; final ATAC regression including the
adapter fixture took 78.08 seconds. These checks used the exact tracked patch
subsequently committed as `bad6739`; the recording includes file SHA256 values.
The DAP Docker check with portable public QC images took 306.40 seconds.

## Public plant inputs

Each library contains the **first 200,000 pairs**, selected positionally, not
randomly. The subsets test computation across two plant genome sizes. They are
not full-depth reconstructions of the source studies. Full source FASTQ MD5s
were not verified because HTTP reads stopped after the selected records;
compressed subset SHA256 values are retained and checked.

| Species and study | Libraries | Biological context | Exact assembly and annotation |
| --- | --- | --- | --- |
| Arabidopsis thaliana, GSE85203 | SRR4000468, SRR4000469 | Col-0, seven-day seedlings, 50,000-nucleus FANS-ATAC, replicates 1/2 | TAIR10; Ensembl Plants 59 |
| Zea mays, GSE252638 / PRJNA1061549 | SRR27443454, SRR27443453 | B73, ten-day seedlings, 2,500 nuclei, replicates 1/2 | B73_RefGen_v4 (AGPv4); Ensembl Plants 46 |

The maize study includes gDNA controls; this control-free BAMPE integration
check does not reproduce that study's full analysis. Original study reference
file checksums are unavailable. The assembly names match the studies, while
the exact provider files used here are independently identified:

| Input | SHA256 |
| --- | --- |
| TAIR10 compressed FASTA | `80a13166003333ba4982b57abdb3d2b62037bc831f4da29ea378c1b776fff8e2` |
| B73_RefGen_v4 compressed FASTA | `44efbdce055e03cd55432748efa74cf7606c320cc9a67124e7d3ca39fc517447` |
| Arabidopsis derived TSS | `8262db9fa150f528c6dd0836fcfe329455f26600ac256dd788e4540aa9ab9ff3` |
| Maize derived TSS | `0f8104ad685733ddf54d6c517507cf0e7286bc59ca91a8d7941792b7e81ddd42` |

The reproduction manifest includes authoritative URLs, GTF checksums and every
FASTQ subset checksum. TSS positions are unique nuclear transcript starts:
GTF start−1 on `+`, end−1 on `−`. `Mt` and `Pt` are explicitly identified,
reported separately and excluded from nuclear analysis. MACS3 genome sizes are
118,960,141 and 2,103,640,168, respectively: counts of nuclear A/C/G/T bases,
not estimates of uniquely mappable genome size.

The preparation script was rerun against retained files; its TSS bytes and
registry metadata matched after accounting for relocated paths. A fresh
Arabidopsis mate download reproduced the pinned subset SHA256.

## Observations and scientific interpretation

All four baseline libraries explicitly selected MAPQ ≥30, duplicate exclusion
and no trimming. These are benchmark settings, not silently imposed defaults.

| Library | Mapped pairs | Usable fragments | Duplicate fraction | Peaks | FRiP | TSS score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SRR4000468 | 139,723 | 90,943 | 0.006826 | 224 | 0.023157 | 3.942935 |
| SRR4000469 | 193,008 | 107,537 | 0.006045 | 47 | 0.004836 | 2.716428 |
| SRR27443454 | 175,538 | 103,774 | 0.124839 | 5 | 0.000819 | 5.858070 |
| SRR27443453 | 176,181 | 80,548 | 0.288319 | 1 | 0.000199 | 3.025830 |

Duplicate fraction uses nuclear proper pairs passing MAPQ before duplicate
exclusion. FRiP counts each usable fragment span once if it overlaps any peak.
TSS uses strand-aware ±2 kb windows, the center bin and the mean 100-base flank
background; 46,216 Arabidopsis and 100,061 maize TSS windows fit completely.
These definitions must accompany comparisons with other tools.

Raw FastQC produced 7 WARN and 14 FAIL flags across 88 module results. Adapter
content passed for Arabidopsis and failed for all four maize mates. Maximum
Nextera detector values were 45.41–48.05%; poly-G signals were also present.
These observations did not cause automatic dataset rejection.

### Explicit adapter sensitivity experiment

The maize experiment alone supplied `CTGTCTCTTATACACATCT` for both mates,
following the [official adapter sequence](https://support-docs.illumina.com/SHARE/AdapterSequences/Content/Nextera_Illumina-Sequences.htm).
All other settings and exact references were unchanged. The experiment reused
the existing index only after checksum verification. Cutadapt retained all
200,000 pairs per library; original FASTQ bytes remained unchanged.

| Library | Usable fragments, before → after | Peaks, before → after | FRiP, before → after | TSS, before → after |
| --- | --- | --- | --- | --- |
| SRR27443454 | 103,774 → 112,808 | 5 → 10 | 0.000819 → 0.001090 | 5.8581 → 6.2092 |
| SRR27443453 | 80,548 → 86,822 | 1 → 0 | 0.000199 → 0 | 3.0258 → 2.8388 |

Runtime was 193.14 seconds, excluding index construction. Zero peaks in the
second trimmed subset is a valid observed result, not a suppressed failure.
Trimming increased mapped and usable counts but did not improve every metric.
The shallow positional subsets do not justify a universal adapter decision or
biological acceptance threshold. Full-depth, protocol-aware assessment remains
necessary. Genesis plant thresholds remain **UNSPECIFIED**.

## Resource costs

The initial four-library run completed in 1,076.21 seconds. Its task trace
reported approximately 2.7 GiB peak RSS and 57.6 seconds for Arabidopsis indexing,
and 47.7 GiB and 14 minutes 12 seconds for maize indexing. Maize alignment used
about 12–12.2 GiB per task. Concurrent jobs need capacity for combined requests;
worker slots alone are not a global memory allocator.

Fragment selection was measured separately using coordinate-disjoint copies of
the deterministic synthetic BAM. GNU time reports KiB; temporary sort files and
SQLite coordinate counts use disk.

| Templates | Expected and observed usable fragments | Wall seconds | Peak RSS KiB | Output bytes |
| ---: | ---: | ---: | ---: | ---: |
| 32,000 | 31,557 | 2.78 | 48,676 | 3,742,045 |
| 320,000 | 315,570 | 18.19 | 186,508 | 39,923,101 |
| 1,280,000 | 1,262,280 | 56.70 | 194,384 | 163,416,584 |

This supports bounded-memory fragment processing at the tested sizes. It does
not establish whole-pipeline RAM scaling or hundred-node throughput. Total
network transfer was not measured; retained input sizes and task character-I/O
counters are recorded, and are not substitutes for network byte counts. The
retained disk footprint is recorded separately; a synchronized clean-run
before/after disk measurement was not captured.

## Failures found and preserved

| Finding | Resolution or remaining uncertainty |
| --- | --- |
| MultiQC generated a differently named parsed-data directory | Explicit data-directory configuration; required-module assertions retained |
| Python bytecode changed staged source-directory identity | Bytecode disabled; clean immutable source bundles |
| Helper contents changed but public resume reused 42 cached tasks | Explicit source SHA256 is now a task input; isolated mutation regression verifies invalidation |
| Concurrent resume raised a Groovy `LazyMap.buildIfNeeded` error | Eager JSON parsing before dispatch; repeated resumes retested |
| Adapter report and peak-caller version were created but not declared outputs | Output declarations and publication assertions added; known-answer trimming test included |
| One earlier DAP stub run missed an expected invalid-reference diagnostic | Immediate retained rerun and later full suites passed. Detailed failed fixture had been deleted by the old harness, so the cause remains unconfirmed; failed fixtures are now retained |
| Development lint/format/type failures | Corrected without relaxing checks; final suite passes |

The DAP diagnostic failure is not attributed to the later ATAC JSON race without
evidence. Intentional checksum, invalid-input and temporary-worker failures are
negative test cases. Logs preserve their errors rather than treating every
nonzero subprocess exit as an unexpected regression.

Changing the metadata parser changes task identity once and therefore caused a
one-time reference rebuild. Reference artifacts were compared after independent
construction. Stable cache acceptance is based on unchanged runs after all
implementation changes, not on that migration invocation. Both reference artifact
checksum manifests matched after independent rebuilds. The final unchanged
public resumes took 26.58 and 25.56 seconds, with all 42 tasks cached each time.

## Execution and deployment boundaries

The controller tests cover two local workers, immutable job identity, checksum
rejection, one-time failure recovery, the three-attempt cap for exit 75,
unreachable/stale status, reconnect without duplicate launch, and manual review.
Unknown jobs reserve capacity; confirmed-stop reconciliation requires a recorded
human decision and rejects a fresh active heartbeat. The browser has no write
endpoint or file browser.

Slurm, Sherlock, NERSC, PBS Pro, LSF and SGE configurations were parsed locally.
The NERSC Podman-HPC adapter was tested with a deterministic command fixture,
including argument preservation, success cleanup and failure retention on
shared storage. These tests do not validate a real site's scheduler or runtime.

Live deployment still requires an existing authorized account, host-key trust,
approved authentication, a clean pinned checkout, installed environments,
prestaged checksummed inputs, accessible work storage, and site-approved resource
and controller allocations. No credentials, keys, Docker permissions, scheduler
services or security settings were changed. No sudo was used.

The controller has one active owner and local SQLite state. Automatic node
provisioning, data transfer, multi-controller failover, remote cancellation and
unattended fixes to scientific metadata are outside its contract. Site acceptance
and throughput testing remain necessary before a large remote deployment.

## Software, files and reproducibility

Runtime: Pixi 0.70.1, Nextflow 25.10.4, Java 23.0.2, uv 0.11.33,
micromamba 2.5.0, Docker 29.1.3. Tool images resolve to Linux amd64.
Tools: bwa-mem2 2.2.1, samtools 1.24, MACS3 3.0.5, FastQC 0.12.1,
MultiQC 1.35, Cutadapt 5.2, pysam 0.24.1, pyBigWig 0.3.26.
Complete image digests and actual version commands are in the evidence directory
and `conf/atac-images.json`. The FastQC and MultiQC DAP defaults now use public,
digest-pinned images at the same tool versions instead of local-only image IDs.

Both dependency locks are unchanged from the fork base:

- `pixi.lock`: `874cbf7d41658470853868c86e5b6d4f2734b85a47b1973f9bb8e78833a7047c`
- `genesis_tools/uv.lock`: `1132c51537ac229ce768fcf0edde8475a970be017cef82c0d46601b228f998f5`

Changed areas are `workflows/atac.nf`, `modules/atac/`, `conf/`, typed ATAC and
execution helpers, launcher and validation scripts, README/guides and generated
SVGs. The DAP scientific process modules are unchanged. Detailed filenames and
commits are retained with the release evidence. Reproduction instructions are in
`validation/reproduce/supported-atac/README.md`; the deployment decision is in
`validation/design/adr-supported-atac-execution.md`.

Primary study records: [GSE85203](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE85203),
[GSE252638](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE252638), and the
[maize methods paper](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2024.1370618/full).
