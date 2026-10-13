# Multiome identity and inclusion contract

Status: tested synthetic contract; no combined RNA/ATAC production pipeline. Shared entity identity is study/sample/replicate/library plus a declared cross-modality barcode mapping. A matching barcode string across different libraries is not evidence of the same nucleus. Original and corrected barcodes, correction provenance, chemistry and mapping cardinality must be retained; ambiguous many-to-one links are rejected by an ingestion adapter, not guessed.

ATAC and RNA have independent present, QC metrics and include fields. A nucleus failing one modality remains represented and may contribute to the other. Shared doublet/cell-calling annotations are evidence; application to each modality is an explicit selection-policy decision. No universal joint pass rule is imposed.

| Toy barcode | ATAC present/include | RNA present/include | ATAC pseudobulk |
| --- | --- | --- | --- |
| both | yes/yes | yes/yes | included |
| atac_only_pass | yes/yes | yes/no | included |
| rna_only_pass | yes/no | yes/yes | excluded, metadata retained |
| doublet | yes/no | yes/no | excluded by fixture policy, metadata retained |
| missing_rna | yes/yes | no/no | included |

Annotation source is explicit: RNA-only, ATAC-only, joint embedding or author-supplied labels, with original label, harmonized label, ontology and confidence/status. Annotation provenance can cross modalities; QC inclusion does not automatically cross modalities. Replicate boundaries and technical merge rules are those in scatac-pseudobulk-spec.md. ATAC modeling consumes fragment/cut-site bundles and source-cell membership. Exploratory analysis may also retain RNA counts, embeddings and modality matrices, but those are not sequence-model targets.

`fixtures/multiome/test_contract.py` preserves all five metadata rows, produces three ATAC fragments, preserves author labels and proves changing RNA inclusion does not alter ATAC selection. `results/contracts/multiome.json` records outputs; complete command/time/exit evidence is in `results/incremental-prs/multiome-contract/`. Fixture doublet exclusion is an explicit example, not a production default or a biological threshold.
