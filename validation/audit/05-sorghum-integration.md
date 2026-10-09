# Sorghum integration — BLOCKED before execution

Date: 2026-10-07T17:03:59.850074+00:00. Upstream SHA: `4468c712e4c171b573e2ec2806fdc5327b5379e9`. Local branch: `validation/reference-cache-experiment`.

Input: `repo/test-Sorghum_bicolor-PRJNA1177471.tsv`; SHA256 `b56fa04c5cd76817a2d85270d597e37572588b3046654b3c9c90167ac9b9a512`.

## Input inspection

Six data rows (seven lines including header), six unique libraries: **one control, five treatments, all PE**. Twelve FASTQ URLs, all HTTPS on `ftp.sra.ebi.ac.uk`. Every row is `Sorghum_bicolor` and requests `Sbicolor_730_v5.0.softmasked.fa.gz`. No replicate pooling or input edits were performed.

C = `Control_TF_DNA_S_bicolor_RTx430_DAPi712A12-ORGi5019-96P247`.

| Sheet row | Sample ID | Role | Layout | SRA run | Control |
| --- | --- | --- | --- | --- | --- |
| 2 | `AL1G11460.t1_S_bicolor_RTx430_DAPi712A10-ORGi5019-96P247` | Treatment | PE | SRR31219424 | C |
| 3 | `AT1G01060_S_bicolor_RTx430_DAPi712H05-ORGi5019-96P220` | Treatment | PE | SRR31219425 | C |
| 4 | `Carub.0001s0116.1_S_bicolor_RTx430_DAPi712C10-ORGi5019-96P247` | Treatment | PE | SRR31219399 | C |
| 5 | `Control_TF_DNA_S_bicolor_RTx430_DAPi712A12-ORGi5019-96P247` | Control | PE | SRR31219427 | None |
| 6 | `LOC_Os01g17260.2_S_bicolor_RTx430_DAPi712H07-ORGi5019-96P247` | Treatment | PE | SRR31219463 | C |
| 7 | `XP_013586407.1_S_bicolor_RTx430_DAPi712F07-ORGi5019-96P247` | Treatment | PE | SRR31219475 | C |

The sample/control graph is a single shared-control star: every treatment in the table points to C, and C has no control. All five references resolve to the control row; no self-links, missing controls, or duplicate sample IDs were observed. Species, reference basename and PE layout agree across all edges. This verifies sheet associations, not executed MACS3 command associations.

## Stop condition

The exact FASTA is absent from the configured `repo/references/` directory and was not found in the accessible filename-search scope. See [reference requirement](05-sorghum-reference-requirement.md) for source candidates, version ambiguity, authentication, size and checksum requirements. A different Sorghum-named file in retained synthetic fixtures is not an acceptable substitute. No pipeline or downloads were started.

## Execution and output status

| Requested verification | Result |
| --- | --- |
| `pixi run pipeline test-Sorghum_bicolor-PRJNA1177471.tsv` from repo | NOT RUN: missing exact reference, explicit stop condition. |
| Same command with `-resume` | NOT RUN; no Sorghum task/cache history was created. |
| Cached tasks, unexpected reruns, byte-identical outputs | NOT VERIFIED. Prior synthetic tests do not establish this integration's behavior. |
| Peaks for five treatments | NOT VERIFIED; no integration peak outputs. |
| QC for all six libraries | NOT VERIFIED; no integration QC outputs. |
| Executed treatment/control assignment | NOT VERIFIED; sheet graph only is verified. |
| flagstat, idxstats, samtools stats | NOT GENERATED / NOT INSPECTED for this integration. |
| SPP, insert-size, tracks | NOT GENERATED / NOT INSPECTED for this integration. |
| Peak files, quantification, workflow provenance | NOT GENERATED / NOT INSPECTED for this integration. Input/repository provenance is recorded here. |
| Nextflow trace/report/timeline/DAG | NOT GENERATED: workflow not launched. |
| Pipeline wall time, maximum memory, failures/retries | N/A: no tasks launched; no pipeline exit status. Missing-reference preflight blocker is not an observed task failure. |
| Pipeline disk before/after, network volume | N/A: no pipeline ran and no FASTA/FASTQ payload transfer occurred. Web metadata lookup traffic was not measured. |

## Commands, resources and warnings

Read-only inspection used `git -C repo status --short`, `git -C repo rev-parse HEAD`, Python csv.DictReader and hashlib.sha256 on the exact sheet, repository config/validator reads, and:

```bash
rg --files --hidden --no-ignore -g '*Sbicolor*' -g '*Sorghum*' /home/exouser /mnt /media /tmp
```

Search command, rows, full URLs, input checksum, UTC timestamp, SHA and duration are preserved in `scratch/sorghum-reference-check/preflight.json`. Filename stdout and permission-denied stderr are separate retained files. Search/preflight elapsed 40.645 seconds; peak RAM not measured. Search exit 2 is retained and limits the absence claim. An initial attempt to read `genesis_tools/src/genesis_tools/load_samples.py` returned “No such file”; the actual validator was then located at `genesis_tools/src/genesis_tools/samples.py` and inspected. No source changes were needed.

Host inspection tools: Python 3.12.12; ripgrep 15.2.0; git 2.43.0. No workflow/container version was exercised in this task. Exact previously resolved runtime versions and container digests are in audit/02-runtime-environment.md and audit/03-baseline-tests.md. One preflight `df -B1 .` observation reported 1,179,968,430,080 available bytes on `/dev/sda1` (88% used); this is not a pipeline disk-delta measurement.

## Acceptance

- PASS: exact test sheet identified/checksummed; counts, layouts, hosts and graph inspected; no reference substitution or real-reference modification.
- PASS: repository SHA unchanged; source/tests/manifests untouched; clean Git working tree confirmed after report creation.
- BLOCKED: exact reference content identity/acquisition; full run, resume and output inspection await that prerequisite.
- UNRESOLVED: authoritative checksum/size, assembly/annotation version mapping and file-specific policy/access. Local search was not exhaustive across inaccessible paths.
- Biological quality: NOT ASSESSED. Neither sheet validity nor eventual computational success establishes biological quality. Plant-specific QC thresholds remain UNSPECIFIED.

Created files: `audit/05-sorghum-reference-requirement.md`, `audit/05-sorghum-integration.md`, and preflight evidence under `scratch/sorghum-reference-check/`. No upstream file changed. Stop here as instructed; no reference acquisition attempted.
