include { dotenv } from 'plugin/nf-dotenv'

process PREPARE_QUANTIFICATION {
    tag "${meta.id}"
    cpus 1
    memory '4 GB'
    time '2h'
    conda "environments/GENESIS_TOOLS.yaml"
    container "${dotenv('GENESIS_TOOLS_IMAGE')}"
    input:
    tuple val(meta), path(peaks), path(sam), path(chrom_sizes)
    output:
    tuple val(meta), path('alignments.bed'), path('indexed_peaks.bed'),
        path('quantification.json'), emit: prepared
    script:
    """
    genesis-tools prepare-quantification --bed '${peaks}' --sam '${sam}' \
        --chrom-sizes '${chrom_sizes}' --weighting primary --output-dir .
    """
    stub:
    """
    genesis-tools prepare-quantification --bed '${peaks}' --sam '${sam}' \
        --chrom-sizes '${chrom_sizes}' --weighting primary --output-dir .
    """
}
