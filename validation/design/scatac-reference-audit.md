# sc/snATAC reference implementation audit

Pinned unmodified checkout: `benchmarks/ENCODE_scatac`, https://github.com/kundajelab/ENCODE_scatac, SHA `2c61bd523af482a79b35ab5c354d54707191c669`. README describes work in progress. Audit covers config, Snakemake rules, fragment and multimapper scripts, environments and ArchR script. This is not a successful end-to-end benchmark.

| Capability | ENCODE_scatac implementation | 10x semantics / Genesis proposal | Unresolved |
| --- | --- | --- | --- |
| Inputs | 10x, multiome and ren configuration; portal accession workflow | Protocol-specific read/barcode structure required | Validate each non-10x chemistry |
| Barcode correction | Whitelist, max distance 1; separate 10x/multiome lists | Preserve original/corrected barcode and whitelist checksum | Collision/ambiguous-correction policy needs fixture |
| Mapping | Bowtie2 -X 2000, SAM comments, multiple placements (configured limit 4) | Explicit alternative to bulk alignment | Plant repeat sensitivity |
| Filtering | samtools -F 524 -f 2, multimapper count filter, fixmate; no inferred MAPQ30 default | Preserve exact filter policy in provenance | Scientific default for plants UNSPECIFIED |
| Multimappers | Script emits all alignments for query groups below count cutoff, followed by filtering | Do not describe as random unique assignment | Terminal group defect below |
| Duplicates | Picard queryname sorting, CB barcode tag, marking retained; later samtools -F 1804 -f 2 removes marked records | Barcode-aware molecular scope required | Cross-technical-library molecular identity |
| Organellar | filter_mito hard-codes chrM; ArchR removes chrM | Registry-provided mitochondrial AND plastid contigs | No silent naming assumptions |
| Fragments | BGZF/tabix BED, +4/-4 interval offsets | 10x documents +4/-5; preserve and declare producer convention | Explicit model adapters, tested endpoints |
| Per-cell QC | ArchR createArrowFiles, tile/gene matrices, doublet scores and filtering | Separate metrics, cell calls and selection policies | ArchR defaults are not plant thresholds |
| Cell calling/annotations | ArchR defaults partly implicit; clustering and downstream peak/motif stages | Author labels preserved alongside harmonization | Defaults require version-specific validation |
| References | Built-in GRCh38/mm10 annotations, blacklist and BSgenome | Exact plant FASTA/annotation/organellar registry required | Plant annotation sources |
| Automation | Snakemake upstream and downstream analysis; portal account/config/reference setup manual | Canonical fragments + metadata boundary before pseudobulk | Full deployment feasibility |

Executable feasibility: README expects Snakemake >=6.6.1 and ENCODE DCC access. Older environment pins include Python 3.9.6, pysam 0.16, samtools 1.13 and NumPy 1.21.2 for fragments. Some whitelist/BSgenome resource URLs use HTTP. No credentials were changed, portal submissions attempted or reference substitutions made. Full execution is not verified on this server; reference/account/protocol prerequisites prevent treating it as a drop-in plant pipeline. Isolated Python components were exercised using existing pysam 0.24.1; this is explicitly not reproduction of its original environment.

Two component defects were reproduced without changing the checkout:

1. `workflow/scripts/bam_to_fragments.py` never flushes the final coordinate buffer. Two input groups expected two fragment rows; only the first was emitted. A one-group input is therefore at risk of an empty output. Evidence: results/contracts/scatac-terminal-buffer.json, exact source/input hashes and command logs in results/incremental-prs/scatac-terminal-buffer/.
2. `workflow/scripts/assign_multimappers.py` never flushes the final query-name group. Two eligible single-end query groups expected two records; only the first was emitted. Evidence: results/contracts/scatac-multimapper-terminal.json and results/incremental-prs/scatac-multimapper-buffer-corrected/. This isolates EOF buffering; it does not assert full PE workflow performance.

Both are HIGH, REPRODUCED software risks in the reference implementation, not reasons to abandon scATAC or silently modify its clone. Genesis should use independent EOF and count-conservation fixtures when adopting equivalent logic. The prototype contract includes conservation/identity tests and does not reuse these scripts.

10x fragment specifications describe unique-fragment rows with support counts including duplicate pairs and indexed BGZF coordinates; current documentation also describes a strand field. ARC preserves ATAC-specific fragment semantics alongside joint barcode identity. The contract must permit declared producer columns, not assume every file has exactly five fields. Sources: [ATAC fragments](https://www.10xgenomics.com/support/software/cell-ranger-atac/latest/analysis/outputs/fragments-file), [ARC fragments](https://www.10xgenomics.com/support/software/cell-ranger-arc/latest/analysis/outputs/fragments-file). Human reference choices and default cell thresholds are not transferred to Genesis.

The repository-linked [published pipeline specification](https://docs.google.com/document/u/2/d/e/2PACX-1vTlgtT4WeXbvRicybUHXnhZs8RKyB4EkTbcWooQ6qBxxQ_zIHpFEVHy38D5lC_s8_YDGfUTsyomJcs3/pub) was retrieved successfully with curl after the web reader could not access it. Its stated update date is 2021-12-07. It separates automated barcode processing/alignment/fragments and initial ArchR QC from manual expert cluster annotation and cross-dataset integration. It describes barcode orientation detection, protocol-specific whitelists, trimming and multiplet flags.

A specification/code discrepancy remains: the specification describes doublets as flagged without removal, but the pinned R script calls `filterDoublets(proj)` before later analysis and saving. This is an OBSERVED documentation/implementation mismatch, not a measured cell-loss estimate. The separate fragment multiplet detector writes status/statistics without rewriting the fragment file. Genesis must distinguish these stages rather than infer one universal doublet policy.

Specification snapshot SHA256: `941feeebd8c8cc29876d7fe45f8421917bea9adadee03a93ffdbcf2fab78b6fa`; command, HTTP200, size and timing: results/incremental-prs/scatac-public-spec/.
