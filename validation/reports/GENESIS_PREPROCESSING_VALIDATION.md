# Genesis preprocessing validation

## Executive summary

The local computational validation, reference-cache hardening, QC additions, isolated PE ATAC prototype, model-facing contracts and workflow diagrams are implemented and tested within their stated scope. This is **not full biological validation**. The exact Sorghum reference and Plant Data Sets workbook remain missing; no assembly or workbook was substituted. Synthetic data cannot settle plant MAPQ, duplication, motif or QC-threshold policies.

Original upstream baseline: `4468c712e4c171b573e2ec2806fdc5327b5379e9`. DAP development branch: `validation/completion`. Isolated ATAC branch: `validation/bulk-atac-prototype`, commit `0b8850207e94a3d4909bf4ab99d18c03cd010cc2`. Baseline observations in audit/00–06 remain separate from later changes. Exact current revisions, checksums, resource logs, container identities and artifact inventory are linked in results/completion/.

The combined DAP checks and real-container validation pass. All 15 compared BAMs remain byte-identical to the retained baseline; existing scientific output payloads match, with gzip/PDF metadata differences explicitly separated. The ATAC prototype and pinned nf-core benchmark agree on 31,554 usable synthetic fragments and 200 peak intervals. Those agreements establish computational behavior on this fixture, not plant biological optimality.

## Confirmed strengths

Pinned project environments/containers, DSL2 workflow structure, deterministic fixtures, control fan-out, SE/PE tests, input rejection, retained Nextflow traces and publication boundaries provide a strong base. Raw FASTQs and BAMs remain outside published DAP outputs. Independent checks inspect contents, molecule counts, output hashes and cache states rather than accepting exit status alone. See audit/03 and reports/reference-hardening-validation.md.

## Confirmed software defects

| Finding | Severity | Evidence | Owner | Disposition |
| --- | --- | --- | --- | --- |
| Docker BAM-inspection helper used a different UID from caller-owned fixtures | MEDIUM | REPRODUCED, audit/03 | preprocessing team | Local fix; PR #2 |
| Explicit image tags still required resolving a default Git tag | MEDIUM | REPRODUCED, incremental PR evidence | preprocessing team | Local fix; PR #4 |
| Track plotting attempted unwritable default cache | LOW | OBSERVED in Docker logs | preprocessing team | Task-local cache fix; PR #6 |
| Different accepted FASTA suffixes collapsed to one reference ID | HIGH | REPRODUCED with native and Docker rejection regression | preprocessing team | Local fix; PR #10 |
| ENCODE_scatac fragment converter drops terminal coordinate group | HIGH | REPRODUCED component fixture | preprocessing team | Reference clone unchanged; do not import this logic without fix/tests |
| ENCODE_scatac multimapper filter drops terminal query group | HIGH | REPRODUCED component fixture | preprocessing team | Reference clone unchanged; independent EOF tests required |

The two scATAC defects are in the pinned external reference implementation, not Genesis production code. Their isolated component tests do not establish full reference-workflow execution.

## Confirmed reproducibility risks

| Risk | Severity | Evidence | Owner | Current handling |
| --- | --- | --- | --- | --- |
| Path/existence-based reference reuse can silently use stale derived files | HIGH | REPRODUCED, audit/04 | preprocessing team | Local content/generator/product verification; unverified cache stops |
| Missing exact Sorghum assembly manifest/checksum | HIGH | OBSERVED prerequisite absence; identity unresolved | wet-lab/data producer | BLOCKED, audit/05; no substitution |
| Local FastQC/MultiQC images are not portable published artifacts | MEDIUM | DOCUMENTED image IDs | infrastructure/admin | Exact local IDs recorded; no image push authorized/executed |
| Launch-directory config/schema leakage between Nextflow projects | MEDIUM | OBSERVED during nf-core benchmark | preprocessing team | Isolated config and launch directory; failures retained |
| Reference benchmark output directory implied narrow mode while command called broad peaks | MEDIUM | OBSERVED actual MACS2 argv | preprocessing team | Explicit CLI mode/q and separate matched run; no reference source edit |
| nf-core version aggregation/MultiQC rerun on otherwise stable resume | LOW | OBSERVED 36/38 cached | preprocessing team | Reporting-layer rerun documented; biological tasks cached |
| scATAC published mark-only doublet specification differs from the pinned filterDoublets call | MEDIUM | OBSERVED code/specification discrepancy | preprocessing team | Preserve distinction; no cell-loss estimate claimed |
| Concurrent mutation of a reference during execution | HIGH | HYPOTHESIS; not tested | infrastructure/admin | Immutable-during-run requirement; launch hashes are not a lock |

No cache manifests, tests or logs were weakened to hide these conditions. Legacy cache compatibility deliberately changes: old unverified products require preservation and regeneration in a fresh reference directory.

## Scientific design risks

MAPQ, duplicate exclusion, trimming, reference choice, peak mode, Tn5 offsets and biological replicate pooling are scientific policies, not interchangeable bug fixes. Plant organellar identities must include plastids and cannot assume human chrM naming. QC metrics need exact numerators/denominators and annotation/coordinate conventions. Plant acceptance thresholds remain **UNSPECIFIED**. Decision owner for defaults is Ted/project lead with preprocessing/modeling input; current evidence is DOCUMENTED or synthetic REPRODUCED, not real-data validation.

## DAP-seq findings

The original workflow preserves full-read primary alignment and treatment/control assignment, including one shared control. SPP has a separate shortened-R1 alignment. Baseline references, tracks, peaks, quantification and output boundaries were inspected. Real Sorghum integration remains blocked by the exact requested FASTA. A successful synthetic run does not certify enrichment quality, TF specificity or cultivar/reference appropriateness.

## FastQC and MultiQC findings

FastQC 0.12.1 runs once per raw mate and preserves HTML/ZIP without trimming. WARN/FAIL labels remain advisory. MultiQC 1.35 preserves parsed machine-readable data and requires every expected FastQC/samtools identity; tests exposed and prevented default sample-name cleaning collisions. SPP native parsing was investigated but NA fragment estimates prevent reliable unmodified ingestion; original SPP TSV/PDF remain available. See the two implementation reports and ADRs. Production image publication remains a separate deployment step.

## Picard decision

The measured experiment in audit/06 and design/adr-picard.md supports optional additional alignment/duplicate diagnostics, not routine duplicate removal. Insert-size metrics substantially overlap existing samtools output. Library-complexity estimates on small synthetic/enriched libraries are limited; SE is not a valid substitute for PE-only assumptions. Keep Picard outside production defaults pending an actionable real-data use case. Measuring duplicates and excluding duplicate reads remain distinct actions.

## MAPQ sensitivity findings

The nine-arm synthetic study compared no cutoff, MAPQ10 and MAPQ30 with three duplicate treatments. MAPQ0 reads affect some output counts/peak boundaries. MAPQ10 and MAPQ30 are indistinguishable in these fixtures because the needed intermediate spectrum is absent. Recommendation: retain the current DAP default; expose policy only through explicit, labeled sensitivity configuration after review. No biological optimum is established.

## Duplicate-handling findings

Marked-but-retained BAMs preserve analysis payloads in the experiment. Exclusion changes quantification even where peaks remain unchanged. Genesis's MACS3 invocation inherits keep-dup=1, so retained BAM duplicates do not mean all duplicates contribute to peaks. Documentation was corrected separately (PR #8). Recommendation: retain the current DAP behavior pending real data; make every future policy explicit and regenerate affected analysis if changed.

## Reference/assembly findings

The registry/schema prototype records genome and annotation identity, masking, provider, source, checksums, organellar names and TSS derivation. Known-answer tests reject changed content, duplicate canonical identities and damaged sizes. Production hardening records decompressed FASTA, product hashes, generator version/image/recipe and checks each invocation. Mtime/gzip-header changes alone preserve identity; altered bytes and unrecorded auxiliary files fail closed. Large-genome hash I/O and multi-run locking remain unmeasured. See design/adr-reference-identity.md.

## Bulk ATAC readiness

The comparison TSV covers ENCODE/nf-core choices without silently inheriting DAP assumptions. The isolated PE prototype exercises actual tools plus independently computable filtering/fragment/Tn5/FRiP/TSS tests. The pinned nf-core 2.1.2 benchmark completes; fragment coordinates, length histogram and peak intervals match on the synthetic input. Tool-reported FRiP and TSS differ by definition and are not forced equal. Eight prototype tasks are cached on resume and 39 published files remain byte-identical. This is prototype readiness, not production plant ATAC readiness. See reports/bulk-atac-prototype-validation.md.

## sc/snATAC readiness

The pinned Kundaje reference audit identifies protocol/barcode/whitelist, mapping, duplicate, fragment and ArchR assumptions, including human-specific resources and two EOF defects. Full execution with its old environment/portal inputs was not established. Genesis scATAC production implementation is deliberately not attempted before protocol/reference/cell-calling decisions. Canonical fragments and explicit producer offsets are the integration boundary.

## Multiome readiness

A tested five-barcode contract keeps ATAC/RNA presence, QC and inclusion separate, preserves author annotations and does not drop both modalities when one fails. Three explicit ATAC inclusions yield three fragments; changing RNA inclusion leaves ATAC fragments unchanged. No monolithic RNA/ATAC workflow or universal joint filtering rule is introduced.

## Pseudobulk contract

Two biological replicates × three cell types yield exact counts r1=(3,1,1), r2=(1,2,1), total nine unique fragments versus twelve read-pair supports. Library-scoped barcodes, deterministic task IDs, source-cell membership, explicit technical merges and cross-replicate rejection are tested. Fragment offsets and ChromBPNet/Cherimoya signal/window/split/control requirements were inspected from pinned code. BGZF production export, real-data ingestion and model training remain later implementations; the contract and toy formation tests are complete. See design/scatac-pseudobulk-spec.md.

## Metadata inventory findings

**BLOCKED:** inputs/Plant Data Sets.xlsx is absent. No worksheet counts, missingness, replicate reconstruction or candidate ranking are fabricated. reports/plant-data-inventory-audit.md records the exact resumption requirements. No bulk data download occurred.

## Open ambiguities requiring project-level decisions

Only unresolved policy choices are collected in reports/questions-for-ted-draft.md, which has not been sent. Exact source files/manifests must be supplied before real-data gates can close. Default MAPQ/duplicate/adapter policies, plant QC acceptance, biological replicate/technical merge identities, supported initial scATAC chemistries and plant-compatible model bias strategy require project evidence/decisions. Code-discoverable questions were resolved in the audits rather than delegated to Ted.

## Recommended changes before scaling

| Recommendation | Benefit | Risk | Effort | Changes biological results? | Old outputs need regeneration? |
| --- | --- | --- | --- | --- | --- |
| Adopt collision rejection and fail-closed reference provenance | Prevent silent reference confusion | Legacy caches stop; hash I/O cost | small fixes + integration | Correctly identified fresh references: no | Unverified derived references: yes, preserved originals |
| Deploy validated FastQC/MultiQC with published immutable images | Raw/read-level QC and complete aggregation | Image portability and extra runtime | small/moderate | No read/alignment change | QC reports only |
| Resolve exact Sorghum artifact and workbook | Enables biological/metadata validation | Access/provenance ambiguity | external prerequisite + run | Assembly choice may matter; no substitution | Exact run required |
| Require explicit replicate/reference/coordinate contracts | Prevent pooling, barcode and off-by-one errors | Rejects incomplete metadata | moderate | Can change previously ambiguous processing | Ambiguous old exports require review |
| Benchmark a real plant ATAC and real TF-identified DAP subset | Tests policies beyond toy data | Dataset selection/confounding | moderate | Experimental only until approved | No automatic regeneration |

## Recommended changes that can wait

Production scATAC/multiome, optical-duplicate/complexity expansions, automatic trimming, universal QC cutoffs, bulk replicate pooling/IDR and model training should wait for explicit data/protocol decisions and acceptance fixtures. Benefits are broader scope and biological evidence; risks are unvalidated assumptions and policy drift; effort is substantial. These would change or create scientific outputs and require versioned regeneration, not silent in-place updates.

The current/animated metro SVG and separate architecture roadmap are in repo/docs/images/. Roadmap labels distinguish implemented DAP processing, experimental bulk ATAC, tested contracts and planned production routes. Small contributions remain isolated; publication is paced at least two hours apart, no automatic merge or container push is performed.
