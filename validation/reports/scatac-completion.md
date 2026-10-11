# scATAC discovery, processing and model delivery

Date: 2026-10-11. Base: `4d5aa600acb29fb1662231dc830e0e3785b76d7a`.
Final verified code: `f83bd75d71db74f080c93ee7090a54cee8295504`.
Individual stage receipts retain their original Git revisions and source hashes;
earlier successful stages were reused only when their implementation signatures
and output checksums still matched.
Branch: `feature/scatac-completion`. Large data and complete logs are retained
outside Git in the validation workspace's `results/scatac-completion/`.

## Scope

The implementation connects workbook discovery, evidence-backed sample identities,
fragment ingestion, replicate-preserving pseudobulks, QC, model exports, actual
loader tests and the existing registry review gates. DAP-seq and bulk ATAC
scientific defaults are unchanged. Plant QC thresholds remain `UNSPECIFIED`.

The real pilot uses one tissue/condition and two documented biological replicates
per species. All verifiable author cell types are retained. Sorghum is an explicit
raw-read sensitivity reconstruction; it is not a reproduction of Cell Ranger.
Computational acceptance, scientific review and training are separate outcomes.

| Deliverable | Completed work | Remaining decision |
| --- | --- | --- |
| Dataset discovery | Workbook import, public archive reconciliation, auditable readiness exports and additional candidate studies | Resolve missing identities and annotations before expanding processing |
| Fragment ingestion | Four real libraries; coordinate, barcode, support, index and checksum validation | Review original reference provenance where author bytes are unavailable |
| Cell-type pseudobulks | 24 groups, separate biological replicates, membership, peaks, raw signals and measured QC | Approve cell annotations and group eligibility |
| Model adapters | Both pinned loaders passed for all 24 groups; four copied-bundle checks also passed | Choose plant bias models and training settings |
| Real biological pilot | Two species, two biological replicates each; independent conservation and replicate comparisons | Scientific approval; no training outcome is claimed |

## Inputs and biological identity

| Species / study | Library | Biological replicate | Source | Author cells | Included cells |
| --- | --- | --- | --- | ---: | ---: |
| Arabidopsis / GSE155304 | GSM4698760 / SRX8840342 | root replicate 1 | Author fragments | 2,728 | 2,728 |
| Arabidopsis / GSE155304 | GSM4698761 / SRX8840343 | root replicate 2 | Author fragments | 2,036 | 2,036 |
| Sorghum / GSE248919 | GSM7922845 / SRX22683056 | multiome biological batch 1 | Four sequencing runs of one technical library | 729 | 550 |
| Sorghum / GSE248919 | GSM7922873 / SRX22683080 | multiome biological batch 2 | One sequencing run of one technical library | 1,455 | 856 |

Arabidopsis library membership was checked against seven author barcode metrics.
Cell classes follow the author object and published Figure 3C: trichoblast,
atrichoblast, meristematic, cortical, endodermal and stele. Original numeric labels
are retained. [Farmer et al., 2021](https://par.nsf.gov/servlets/purl/10297371).

Sorghum membership follows the author Signac fragment/barcode map and the original
RNA-derived identities. The six included classes are bundle sheath, epidermis,
guard, mesophyll, phloem and xylem. Another 778 author nuclei have unknown labels;
their metadata is retained and their exclusion from cell-type groups is explicit.
The paper documents two biological replicates with multiple technical libraries.
GEO's replicate 1/3 labels are preserved separately and do not define three
biological replicates. [Source study](https://doi.org/10.1038/s41586-024-08204-3).

Sorghum runs are SRR26989999, SRR26990000, SRR26990001, SRR26990002 and SRR26989943.
The first library contains 150,691,229 PE50 spots; the second contains 182,632,068
PE151 spots. All five original public SRA objects passed MD5/SHA256 checks.
Extraction preserved all four read roles. ENA's ordinary paired FASTQ export
omits the barcode read, so it was not used as a silent substitute.

## Exact reference and processing choices

| Source archive | Declared identity | Compressed-file SHA256 |
| --- | --- | --- |
| Arabidopsis FASTA | TAIR10, Ensembl Plants release 55 | `80a13166003333ba4982b57abdb3d2b62037bc831f4da29ea378c1b776fff8e2` |
| Arabidopsis annotation | Araport11 GFF3, 201606 | `22d8c42ec2ca667fc3f78105f568bf295ee10d2145b2bd76dcd290a469a27b99` |
| Sorghum FASTA | `Sbicolor_454_v3.0.1.fa.gz` | `8683530943438cee02ca14340010b2b897b4dcff45238dd8efeabb604c7c3936` |
| Sorghum annotation | `Sbicolor_454_v3.1.1.gene.gff3.gz` | `7206b0dddea6a507218386273211b255030a9373562b6f8e89050f65c3c211f0` |

The uncompressed model FASTA identities are distinct from the downloaded archives:
Arabidopsis `85c83b6dd6820769dae5df190adda7ca0762872d61e5634a91f1d14c8f4fd8ce`
and Sorghum `4a5e7894b8f2ff07d26a123c7ce32840cb37a203ae4253ee407ecd45dcbe52b4`.
The decompressed reference audit and every model bundle record these exact bytes.

Sorghum reference and annotation names match the author analysis; files came from
the named PlantGARDEN release. No v5 assembly was substituted. Arabidopsis uses the
author-declared TAIR10 assembly, but byte identity with the author's original
FASTA and exact annotation release is unverified. Its posthoc TSS calculation is
explicitly labeled a sensitivity choice.

The Sorghum reconstruction uses Chromap 0.3.2-r518, MAPQ ≥30, a 2,000 bp maximum
fragment length, adapter handling from the ATAC preset and per-barcode coordinate
collapse with retained read support. The barcode is the reverse complement of
bases 9–24 of the 24-base barcode read. Paired public ATAC/GEX whitelists provide
an explicit translation to the author's GEX barcode namespace. Orientation and
library association were checked on 10,000 spots from every run before mapping.
These are sensitivity parameters, not new Genesis defaults.

Canonical ingestion preserves BED0 half-open intervals, support, namespace and
source coordinates. Pseudobulk signals use two unweighted cut endpoints per
unique cell fragment with the documented ChromBPNet ATAC convention; no second
Tn5 shift is applied to stored fragments. MACS3 uses BEDPE, `--keep-dup all`,
q=0.01 and an explicit reference-specific genome size. Replicates remain separate.
The size is the declared reference-length sum (nuclear chromosomes for
Arabidopsis), not an independently measured mappable genome size.

TSS enrichment uses declared gene TSS coordinates, strand-oriented ±2,000 bp
windows, and the center base divided by the mean outer 100 bp flanks. This is an
explicit Genesis metric, not numerical equivalence with ENCODE or Cell Ranger.
FRiP counts unique fragments overlapping the union of that group's peaks.
Support redundancy is `1 - unique fragments / read-pair support`, not removal.

Chromap 0.3.2 caps reported support at 255. A 300-pair deterministic fixture
reproduced a single fragment with reported support 255. This producer limitation
does not change unweighted unique-fragment signals, but capped support can make
redundancy estimates lower bounds. Ingestion conserves the supplied fragment
values; it cannot recover truncated support. Real rows at the cap are counted
separately in `provenance/chromap-support-audit.json`. Chromap's estimated FRiP
is retained in raw logs and is not used as the observed plant FRiP metric.

## Validation evidence

| Check | Result | Evidence |
| --- | --- | --- |
| Full project checks | PASS | `commands/completed-code-frozen-checks/`; 155.3 s at `f83bd75`; two-CPU affinity keeps concurrent work within budget |
| DAP real-tool regression | PASS | `commands/diagnostic-frozen-docker-regression/`; 303.8 s at `6fae768`; stable resume, reference integrity, FastQC and MultiQC |
| Bulk ATAC real-tool regression | PASS | `commands/bulk-atac-docker-regression/`; 77.8 s; 21 tasks cached twice; unchanged scientific outputs |
| Deterministic streaming | PASS | `commands/streaming-100k-regression-v2/`; 100,000 fragments, 200,000 support, indexed last record and resume |
| Native Chromap fixture | PASS | `tests/validate_scatac_chromap.py`; four read pairs become three unique fragments with support four |
| Producer support boundary | REPRODUCED | `commands/chromap-support-saturation/`; 300 identical pairs report support 255; original conservation assertion remains intact |
| Actual pinned model fixture loaders | PASS | `commands/actual-model-loaders-v4/`; all folds, positive/background tensors, independent sequence and per-base count checks |
| Numeric chromosome fixtures | PASS after reproduced failure | `commands/numeric-chromosome-loaders-fixed/` and `commands/leading-zero-loaders-fixed/`; both actual loaders preserve `1` and `01` labels and return exact source sequences/counts |
| Explicit background geometry | PASS | `commands/background-window-actual-loaders/`; both actual loaders, preserved leading-zero contigs, 1,000 bp stride and registry/release gates |
| Arabidopsis library 1 ingestion | PASS | 81,811,226 fragments; 113,530,890 support; 1,459.2 s; peak process RSS 105,444 KiB |
| Arabidopsis library 2 ingestion | PASS | 98,254,384 fragments; 143,341,235 support; 1,764.7 s; peak process RSS 107,816 KiB |

Both Arabidopsis inputs were completely scanned, indexed and tested for stable
resume. There were zero ingestion exclusions and zero coordinate changes. The
two libraries total 180,065,610 fragment records and 256,872,125 supporting pairs.
The author fragment files contain no organellar rows; that does not imply zero
organellar reads in the original libraries.
Fresh deterministic fixtures test byte reproducibility. Real-data stages test
checksum-verified resume; a second complete raw-read reconstruction was not run
solely to test byte identity.

An independent scan of both original author fragment files confirms every input
record and all 4,764 selected barcode totals against ingestion. The source files
contain 49,237,758 selected fragments, while author `passed_filters` counters sum
to 49,237,820: 59 cells differ by one fragment and one differs by three. The
62-fragment difference predates Genesis; its upstream cause is unresolved.

All 4,764 author `pct_reads_in_peaks` values use the author's `total` counter as denominator.
Their median is 40.68%, whereas author peak fragments divided by passed fragments
has median 90.10%. Genesis group FRiP also uses newly called group-specific peaks,
so these values cannot be treated as a direct numerical reproduction. The author
mitochondrial fraction has median 9.44%; zero organellar rows in deposited
fragments must not erase that source QC. No source TSS-enrichment score was found;
`TSS_fragments` is a count, not an enrichment score.
The retained-fragment support redundancy also has a different denominator from
author duplicate counts divided by `total`; these are not interchangeable percentages.

<!-- REAL_PILOT_RESULTS -->
## Real pilot results

All 24 cell-type/replicate groups passed structural validation, both actual model
loaders and stable resume. Each species contributes six cell types from two
biological replicates. An independent audit reconciled every ingested fragment
and supporting pair with selection/exclusion totals, group membership, cut counts
and bigWig sums.

| Species | Source cells | Included cells | Selected unique fragments | Read-pair support | Groups |
| --- | ---: | ---: | ---: | ---: | ---: |
| Arabidopsis | 4,764 | 4,764 | 49,237,758 | 73,621,178 | 12 |
| Sorghum | 2,184 | 1,406 | 38,716,781 | 67,937,945 | 12 |

| Fragment conservation | Arabidopsis | Sorghum |
| --- | ---: | ---: |
| Ingested unique fragments | 180,065,610 | 118,143,094 |
| Ingested read-pair support | 256,872,125 | 204,804,593 |
| Fragments without an author-selected cell | 130,827,852 | 53,777,649 |
| Fragments from explicitly excluded cell labels | 0 | 25,648,664 |
| Source cell barcodes absent from ingested fragments | 0 | 0 |

All four inputs retain their supplied coordinates and support during ingestion.
A separate scan of both native Sorghum outputs found zero records at Chromap's
255-support cap. The producer limit was reproduced on a deterministic fixture,
but no capped support was observed in these two real libraries.

| Observed range across groups or matched replicate pairs | Arabidopsis | Sorghum |
| --- | ---: | ---: |
| Peaks per group | 10,122–26,974 | 285–35,540 |
| Group fragment-based FRiP | 0.2595–0.6065 | 0.0219–0.3653 |
| Declared gene-TSS enrichment | 2.9160–3.7157 | 4.2814–5.5845 |
| Support redundancy fraction | 0.2764–0.3644 | 0.3184–0.6258 |
| Replicate peak-base Jaccard | 0.3712–0.7230 | 0.0164–0.3282 |
| Replicate signal Pearson, nonzero-union bins | 0.9416–0.9857 | 0.8754–0.9565 |
| Replicate signal Spearman, nonzero-union bins | 0.8900–0.9701 | 0.3275–0.7631 |

These ranges describe this pilot. They are not acceptance thresholds or evidence
that a cell type is biologically good or bad. Replicate comparisons use identical
1,000 bp bins; the full table also retains all-bin correlations.
Library depth, read length, peak calling and annotation choices can affect these values.
Sorghum peak-set agreement varies substantially across cell types. The
[replicate table](../evidence/scatac-completion/replicate-qc.tsv) places each comparison
beside cell counts and fragment depth for review before selecting training tasks.

Model exports use Arabidopsis chromosomes 1–3 / 4 / 5 and Sorghum
chromosomes Chr01–Chr08 / Chr09 / Chr10 for train / validation / test.
Each input window is 2,114 bp, each signal window is 1,000 bp, and jitter is zero.
Unplaced contigs remain in the reference and scientific products but are excluded
from these declared model folds. Boundary-window exclusions are also counted.
The explicit 1,000 bp background stride retains one distinct background per peak.

| Model preparation totals across groups | Arabidopsis | Sorghum |
| --- | ---: | ---: |
| Peak records excluded at context boundaries | 3 | 0 |
| Peak records outside declared folds | 0 | 321 |
| Selected background windows | 250,905 | 159,688 |
| Backgrounds matched in the exact 1% GC bin | 250,206 | 159,687 |

Both model adapters produced the same region selections under these settings.
The 48 loader tests each checked a positive and a background window in all three
folds: 288 sequence/signal examples, compared base by base with the exact FASTA
and bigWig. Four further loader tests passed on copied release bundles, one per
species and model, with verified resume. This is data-loading acceptance, not training.

The portable candidate is `results/scatac-completion/genesis-scatac-pilot-v1/`.
It contains source-library manifests, cell membership, fragments, peaks, tracks,
both model bundles, QC, loader receipts, source evidence and checksums.
Its registry correctly retains `model_ready: false`: metadata, QC and eligibility
review are still unapproved. The [handoff checklist](../../docs/usage/scatac-model-handoff.md)
states the remaining modeling-group decisions.

Compact measured evidence is committed under
[validation/evidence/scatac-completion](../evidence/scatac-completion/README.md).
Full logs, per-cell tables and large artifacts remain outside Git.
<!-- END_REAL_PILOT_RESULTS -->

## Reproduction and resource accounting

Exact argv, complete stdout/stderr, exit codes and GNU time measurements are in
`commands/*/`. Stage `complete.json` files bind inputs, policies and outputs by
SHA256; `execution.json` retains runtime and software identity. Acquisition,
extraction, mapping and barcode receipts preserve the corresponding raw inputs.
The [executed helpers](../experiments/scatac/pilot/README.md) are archived unchanged.

Runtime: Pixi 0.70.1, uv 0.11.33, micromamba 2.5.0, Nextflow 25.10.4, OpenJDK
23.0.2-internal, Python 3.14.5, pysam 0.24.1, SRA Toolkit 3.2.1, pigz 2.8 and
Docker 29.1.3 on linux/amd64. Frozen environment locks are committed. Immutable
image identities and architectures are in `provenance/runtime-versions.json`.
The root Pixi and Python dependency manifests/locks were not re-resolved.

Peak RSS from GNU time includes native child processes but not Docker daemon
children. Container stages have explicit CPU/memory limits; absent measured
container peaks are not replaced with the limits as if they were observations.
The working budget is 16 CPUs, 64 GiB RAM, 150 GB downloads and 500 GB new data.

<!-- RESOURCE_RESULTS -->
| Species | Native mapping elapsed | Fragment ingestion, summed stage time | Pseudobulk aggregation elapsed |
| --- | ---: | ---: | ---: |
| Arabidopsis | Author fragments; not rerun | 3213.4 s | 1900.0 s |
| Sorghum | 1522.4 s / 2375.2 s | 1627.1 s | 1366.7 s |

Stage times exclude prerequisite waiting. Summed ingestion times are work totals,
not elapsed time for concurrent jobs. Each product and loader has its own timer
in the compact resource evidence. Process memory is a high-water mark; it is
not an incremental allocation for an individual stage.

Verified major source downloads total 37,958,418,114 bytes (37.96 GB). Reused Arabidopsis files, software, metadata, retries and transport overhead are outside this byte count.
The completion directory occupies 165.53 GB at this snapshot, with 944.68 GB free on its filesystem.
An exact pre-run disk snapshot was not retained; acquisition checked for more
than 500 GB free. No exact before/after delta or total network traffic is claimed.
<!-- END_RESOURCE_RESULTS -->

Early development receipts record a starting Git SHA and source-file hashes;
some implementations were uncommitted at that instant. The recorder's diff hash
is taken at completion and excludes untracked files. The scientific source hashes
and stage identities, not that diff hash alone, establish reproducibility. The
final DAP/ATAC regressions ran with their fixed revisions recorded in the table.
Subsequent changes were confined to scATAC model preparation and documentation;
DAP-seq and bulk ATAC modules, configuration and dependency locks are unchanged.

## Preserved failures and interpretation

- The first DAP resume check failed because Git metadata changed during the run,
  legitimately invalidating MultiQC. A frozen-revision rerun passed; no cache
  assertion was weakened.
- Initial archive timeouts were retried with retained logs. PRJNA1427083 still had
  no public ENA runs at retrieval. Submitted Sorghum cloud URLs denied access;
  public original SRA objects provided all required read roles.
- An early SRA inspection selected a multi-run response without filtering its run
  accession; the assertion caught this. Resolving the SRA executable's symlink
  also broke its argv-based dispatcher; keeping the executable path fixed it.
- A wrong container UID caused a permission error. The existing user's UID was
  then supplied; host permissions and security configuration were not changed.
- Initial type-check and nested-environment warnings were fixed and retested.
  The first streaming invocation omitted its required output argument; the
  corrected command passed. Both attempts remain recorded.
- Chromap emits its version on stderr. The experiment's first version capture
  read stdout only, and ingestion correctly rejected the empty producer version.
  A separate version receipt now records stderr, the executable hash and the
  environment lock; the original mapping receipt is preserved.
- The second Sorghum mapping attempt was intentionally restarted from four to
  eight threads after regressions released CPU capacity. The incomplete attempt
  and its reason are retained; scientific parameters were unchanged.
- The 24 GiB second-library attempt finished alignment but failed with
  `std::bad_alloc` in Chromap's final low-memory merge. It reached 23,066,312 KiB
  peak RSS in 2,244.1 seconds. The retry raises only the address-space limit to
  40 GiB, within the total 64 GiB budget. The retry passed in 2,375.2 seconds,
  with peak process RSS 24,817,828 KiB. Its alignment counters match the failed
  attempt. The original temporary mappings remain preserved; no unsupported
  recovery from partial native output was attempted.
- Real QC distributions exposed integer histogram keys whose sorted JSON order
  differed after reloading. The freshly written product failed its own manifest
  identity check. A widths-8-and-10 fixture reproduced it; serializing explicit
  string keys fixes the identity without changing metric values. The first real
  rerun has byte-identical fragments, cut counts, bigWig and peak output.
- Numeric chromosome names failed in the ChromBPNet adapter before explicit
  string parsing. A separate leading-zero fixture reproduced name loss in
  Cherimoya's filename parser. Both actual loaders now receive typed tables;
  the model repositories and reference names remain unchanged. The unmodified
  ChromBPNet training CLI still needs an equivalent input adapter for numeric
  chromosomes. These are loader tests, not evidence that its whole CLI trained.
- One full-check attempt failed because Nextflow's console tail omitted the
  expected reference-cache diagnostic. The complete failed task stderr contained
  it. The regression now inspects that exact task log and additionally requires
  one failed validation task with no downstream work. A wrong diagnostic still
  fails. Nextflow also warned that report rendering was interrupted on the
  expected-failure run; that warning is retained.
- An experiment helper passed a JSON list to the contract's object-only reader.
  The reader rejected it; the helper now uses list-aware JSON parsing. A waiting
  release wrapper was restarted with the same correction before assembly began.
- The serial Sorghum model wrapper was intentionally stopped with exit 143 after
  two complete groups, then resumed with three worker processes. No child loader
  was running at the stop. Completed bundle and loader manifest hashes are
  preserved in the transition receipt. Each worker owns different outputs;
  registry writes remain serial. This changes execution concurrency only.
- The disjoint-background experiment passed both real loaders for the first
  group, then correctly stopped on insufficient background candidates. An
  independent geometry audit found adequate one-to-one supply for 8/12 groups
  at a 2,114 bp stride and 12/12 at a 1,000 bp stride. The latter follows the
  pinned model helper's separation of window length and stride. It is a labeled
  model-preparation sensitivity choice, not a relaxed count assertion or a
  change to biological peaks. Full positive-context exclusion and chromosome
  split isolation remain required.
- Equivalent chromosome-fold mappings produced different seeded backgrounds
  when JSON key order changed the order of random draws. Canonical fold ordering
  fixes this reproducibility defect. The reordered-config regression passes;
  checksums for four previously completed real bundles remain unchanged.

## Scientific review still required

The Sorghum source reference lacks declared organellar contigs, so mitochondrial
and plastid fractions are unavailable. GEO's seven-day description differs from
the paper's imbibition/growth schedule; both are preserved. Only one technical
library per Sorghum biological batch is included. RNA-derived cell labels remain
author annotations, not newly validated cell identities.
The author object's `nCount_ATAC` sums peak-feature counts; it is not an independent
fragment total. Comparable original Sorghum FRiP, TSS-enrichment and duplicate
metrics were not available from the inspected object. PE50 versus PE151 read
length and depth also limit the interpretation of replicate differences.

Chromosome folds prevent coordinate/context overlap between train, validation and
test sets. Paralog/homology leakage is unassessed. Both adapters retain raw signal;
GC matching retains ambiguous reference bases and reports affected windows.
ChromBPNet still requires a suitable plant bias model. Loader success is not a
training result. Metadata, QC and eligibility approval must be recorded before a
candidate can be called model-ready.

See [additional public data](scatac-data-expansion.md) and the
[model handoff guide](../../docs/usage/scatac-model-handoff.md).
