# Scientific purpose

The goal is reliable plant sequence-to-function prediction and experimentally
testable sequence design. Genesis supplies traceable preprocessing and curated
measurements. It does not itself establish a plant foundation model, train the
models discussed below, or provide an MPRA processing/experimental platform.

A useful handoff connects **data → declared measurement → model input → downstream
test**. File readability is one step in that chain. A successful pipeline, a
checksum match and a successful model loader answer different questions.
Nextflow executes supported scientific workflows.

## What does a signal measure?

| Readout | Implemented measurement | Current model interface / limitation |
| --- | --- | --- |
| DAP binding | Retained mapped primary read ends; total/strand CPM coverage and strand-specific 5′ counts. Peak RPM counts read ends; mean RPKM is coverage. Paired ends count independently. | Peaks and tracks are available; the scATAC model adapters are not DAP adapters. In-vitro TF binding is not tissue-specific transcription or accessibility. |
| Bulk ATAC accessibility | Usable paired outer fragments in BED0 half-open coordinates; raw one-base cuts at `start + 4` and `end − 6`. FRiP counts usable reads in peaks, as ENCODE does. | Fragment, peak and raw-cut outputs; no automatic conversion through the scATAC adapters. Declare and audit the model convention before reuse. |
| scATAC accessibility | Existing 10x fragments, already offset +4/−5; selected fragment rows count once, independent of supporting read-pair count. Biological replicates stay separate. | The audited `chrombpnet-atac-v1` conversion puts cuts at `s` and `e` for source `[s,e)`. One unstranded raw-count channel, no normalization or further shift; separate pinned ChromBPNet/Cherimoya adapters. |
| TSS initiation | Per-base 5′ ends of capped or nascent RNAs on each strand, after method-specific trimming; paraclu clusters. Annotation-derived TSS QC in bulk ATAC is not TSS-assay processing. | Tag and cluster outputs; initiation is not steady-state expression. |
| RNA expression | Uniquely mapped reads per gene (featureCounts) and a CPM track, with declared strandedness. | Gene counts and tracks; no model adapter. |
| WGBS / MPRA | Contextual or future prediction targets, not implemented here. | Methylation and reporter activity require distinct measurement definitions and acceptance criteria. |

Identical bigWig or BED formats do not make targets interchangeable. Preserve count
unit, strand, normalization, coordinates and shift provenance. The
[DAP](usage/dapseq-reference.md#analysis-choices), [bulk
ATAC](usage/bulk-atac.md#analysis-and-metrics),
[scATAC](usage/scatac-seq.md), [RNA-seq](usage/rna-seq.md) and [TSS](usage/tss-seq.md)
guides specify the actual policies.

Sequence-source organism, assayed DNA organism, TF-source organism and experimental
host/context are distinct concepts. This matters for interspecies DAP and for
sequences tested in a heterologous reporter host. Where these distinctions are
absent from an existing manifest, they are future metadata/review requirements;
do not invent values or interpret a single species field as all four.

## Limits

Pipeline outputs, checksums and model loaders answer different questions from model training,
and training is not independent biological validation. Motif plausibility is not experimental
confirmation, and neither more peaks nor a higher FRiP or mapping rate is enough to choose a
method. Synthetic test fixtures check integration, not biological accuracy.

Chromosome folds do not establish absence of homology leakage. The current model
backgrounds are unmatched genome tiles. ChromBPNet's bias-model plan does not
supply a fitted plant bias model. scATAC TSS enrichment remains unassessed, and
absence of organellar fragments in a filtered input does not mean zero original
organellar contamination. No universal plant QC cutoff is implied.

## The next data-to-model decision

A bounded first acceptance exercise is one reviewed Arabidopsis root cell type,
with separate bundles for its two biological replicates, targeting the audited
ChromBPNet revision. Select the cell type, resolve reference/annotation evidence,
agree on raw-cut and background/bias acceptance, then test each exact bundle with
the model loader. This is a proposed handoff, not a released or approved dataset.

The archived [model
inspection](https://github.com/kundajelab/genesis-curation/blob/12bb02cb9ec98fe8c4c0ec660adcfdeb7384f20e/docs/usage/scatac-model-handoff.md#inspect-a-bundle) guide shows how
to distinguish observed structure, declarations and missing acceptance. The modeling
team still needs to define the held-out prediction task and evidence required before
training.