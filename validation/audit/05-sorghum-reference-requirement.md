# Sorghum reference requirement — BLOCKED

Date: 2026-10-07T17:03:59.850074+00:00. Upstream SHA: `4468c712e4c171b573e2ec2806fdc5327b5379e9`. Local branch: `validation/reference-cache-experiment`.

Input: `repo/test-Sorghum_bicolor-PRJNA1177471.tsv`; SHA256 `b56fa04c5cd76817a2d85270d597e37572588b3046654b3c9c90167ac9b9a512`.

## Observations

The exact requested filename is **`Sbicolor_730_v5.0.softmasked.fa.gz`**, in all six rows. The default required path is `repo/references/Sbicolor_730_v5.0.softmasked.fa.gz` (`nextflow.config:18`). That file and the default references directory are absent. `genesis_tools/src/genesis_tools/samples.py:38` requires this file to exist.

Read-only filename search covered `/home/exouser`, `/mnt`, `/media`, and `/tmp`, including hidden and ignored files. It found no matching requested reference. Search exited 2 because of permission-denied directories (systemd-private temporary directories, snap-private-tmp, and `/media/volume/data/lost+found`); complete stdout/stderr are retained. Symlink directories were not followed. This is absence in the configured location and searched accessible scope, not proof of absence on every storage device.

The only other matching FASTA was `results/baseline/runs/regression-ocblnax2/sheet-references/Sorghum_bicolor.Sorbi1.19.fa.gz`, a prior regression fixture. It is not the requested file and was not used. No FASTA or FASTQ was downloaded, replaced, renamed, or modified.

## Identity and candidate authoritative sources

| Item | Finding |
| --- | --- |
| Filename-implied assembly | Sorghum bicolor, filename assembly token `v5.0`, softmasked gzipped FASTA; `730` is an apparent Phytozome dataset identifier, not a verified assembly accession or genome size. |
| Exact accession/content identity | UNRESOLVED: the sheet supplies neither accession, download URL, release manifest, nor checksum. Filename alone cannot authenticate contents. |
| Primary candidate | [JGI Phytozome Sbicolor v5.1 information page](https://phytozome-next.jgi.doe.gov/info/Sbicolor_v5_1), then the [JGI Phytozome download collection](https://data.jgi.doe.gov/refine-download/phytozome). Both returned JavaScript-page shells without an inspectable exact-file manifest through the web reader. |
| Additional official metadata lead | [JGI BTx623 Standard Draft v5.1 project](https://genome.jgi.doe.gov/portal/SorbicStaDraftv2_4/SorbicStaDraftv2_4.info.html), project 1335879. This is a candidate identity lead only; it does not establish that its FASTA is the requested artifact. |
| Expected compressed byte size | UNKNOWN: no authoritative exact-file listing or Content-Length obtained. Do not substitute a genome-length estimate for a compressed file size. |
| Expected uncompressed size / sequence span | UNKNOWN for this exact artifact; obtain from the release manifest and verify after acquisition. |

JGI explicitly recommends its download collection for finding a particular organism and genome version, including historical releases. [Official archive/access guidance](https://jgi.doe.gov/user-science/science-stories/more-intuitive-phytozome-interface).

**Version interpretation remains a prerequisite.** A portal label v5.1 may combine an assembly version and annotation version, but that relationship was not established here. Do not infer that a v5.1 FASTA is interchangeable with the requested v5.0 file. Obtain a release manifest explicitly listing `Sbicolor_730_v5.0.softmasked.fa.gz` and documenting its assembly and annotation versions. Do not rename another assembly to satisfy the filename check.

Sample names identify RTx430 material; candidate reference pages identify BTx623. This is a potential reference-genotype assumption requiring documentation, not permission to select an RTx430 assembly instead.

## Authentication and data-use requirements

JGI download access has a login/policy workflow. Current official guidance states that JGI login uses ORCID with two-factor authentication from July 27, 2026. Exact-file anonymous access was not established; treat authenticated portal access as an acquisition prerequisite unless an official anonymous exact-file URL is confirmed. No credentials or tokens were requested, inspected, or stored. [JGI portals notice](https://jgi.doe.gov/analyze-data/jgi-portals).

The official download guidance requires acceptance of its data-use policy. Dataset-specific license/use-restriction status is UNKNOWN until its accompanying policy is inspected; do not equate free access with unrestricted redistribution. Historical and current project rules differ. [Download-area guidance](https://portal-web-1.jgi.doe.gov/portal/help/download.jsf), [JGI data policy](https://jgi.doe.gov/data-policy-support/data-policy).

## Proposed acquisition and checksum strategy (not executed)

1. Obtain the exact-file authoritative manifest: stable file/project identifier, assembly accession/version, masking status, byte size, published checksum and applicable data-use notice. Resolve the v5.0/v5.1 relationship explicitly.
2. Acquire only that exact artifact via the official portal or a locally supplied copy with the same provenance. Keep authentication values out of commands, logs and reports. No substitution is authorized.
3. Compare downloaded byte size and provider checksum (MD5 or SHA256 as supplied); independently calculate SHA256 of the compressed bytes. Run gzip integrity validation.
4. Also record SHA256 of the decompressed FASTA bytes, sequence identifiers, per-sequence lengths and sequence hashes preserving case/softmasking. Recompression can change the compressed hash without changing FASTA contents; record both levels without normalizing away differences.
5. Store source URL without credentials, retrieval time, manifest, policy and checksums. Use a fresh reference directory with no stale sizes/index products, in light of audit/04. Hash all derived products once built.

## Acceptance and evidence

Reference acquisition is BLOCKED. Exact basename is known; exact biological/content identity, byte size, checksum and artifact-specific access terms remain unresolved. The user-required stop condition was honored.

Evidence: `scratch/sorghum-reference-check/preflight.json`, `filename-search.stdout.txt`, `filename-search.stderr.txt`. Search command and elapsed time are in preflight.json (40.645 seconds); peak RAM was not measured. Python 3.12.12, ripgrep 15.2.0, git 2.43.0. No container ran for this preflight; previously measured runtime and image digests remain in audit/02 and audit/03.
