include { dotenv } from 'plugin/nf-dotenv'

process QUANTIFY {
    tag "${meta.id}"
    cpus 1
    memory '4 GB'
    time '1h'
    conda "environments/GENESIS_TOOLS.yaml"
    container "${dotenv('GENESIS_TOOLS_IMAGE')}"
    publishDir "${params.workspace}/${meta.species}/${meta.id}", mode: 'copy',
        pattern: '*.peaks.*.tsv'
    input:
    tuple val(meta), path(details), path(reads), path(coverage)
    output:
    tuple val(meta), path("${meta.id}.peaks.RPM.tsv"),
        path("${meta.id}.peaks.mean_RPKM.tsv"), emit: quantified
    script:
    """
    genesis-tools finish-quantification --details '${details}' \
        --read-overlaps '${reads}' --coverage-overlaps '${coverage}' \
        --rpm-output '${meta.id}.peaks.RPM.tsv' --rpkm-output '${meta.id}.peaks.mean_RPKM.tsv'
    """
    stub:
    """
    genesis-tools finish-quantification --details '${details}' \
        --read-overlaps '${reads}' --coverage-overlaps '${coverage}' \
        --rpm-output '${meta.id}.peaks.RPM.tsv' --rpkm-output '${meta.id}.peaks.mean_RPKM.tsv'
    """
}
