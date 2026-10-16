include { dotenv } from 'plugin/nf-dotenv'
include { dapReceipt } from '../workflows/dap_receipt'

process CALL_PEAKS {
    cpus 1
    memory '1 GB'
    time '1h'
    conda "environments/DAP_SEQ_PEAKS.yaml"
    container "${dotenv('DAP_SEQ_PEAKS_IMAGE')}"
    tag "${meta.id}"
    publishDir "${params.run_dir}/output/${meta.species}/${meta.id}", mode: 'copy',
        pattern: '*.macs3*'
    input:
    tuple val(meta), path(bam), path(bai), path(control_bam), path(control_bai)
    path launcher
    output:
    path "*.genesis-task.json", emit: receipt
    tuple val(meta), path("${meta.id}.macs3_peaks.narrowPeak.gz"), emit: peaks
    tuple val(meta), path("${meta.id}.macs3*"), emit: results
    script:
    def format = meta.layout == 'PE' ? 'BAMPE' : 'BAM'
    def revision = task.ext.macs3_revision ?: ''
    if (revision && !(revision ==~ /[0-9a-f]{40}/)) {
        error 'MACS3 source revision must be a full Git SHA'
    }
    def sourceOption = revision ? "--require-source ${revision}" : ''
    """
    ${dapReceipt(task, 'CALL_PEAKS', [meta.id], workflow.containerEngine, false)}
    python '${launcher}' --cpus ${task.cpus} --receipt '${meta.id}.macs3.runtime.json' ${sourceOption} -- callpeak -t '${bam}' -c '${control_bam}' \
        -f ${format} -g ${meta.genome_size} -n '${meta.id}.macs3'
    gzip -f '${meta.id}.macs3_peaks.narrowPeak'
    """
    stub:
    """
    ${dapReceipt(task, 'CALL_PEAKS', [meta.id], workflow.containerEngine, true)}
    printf 'chr1\\t100\\t200\\tpeak1\\t100\\t.\\t1\\t2\\t3\\t50\\n' | gzip > '${meta.id}.macs3_peaks.narrowPeak.gz'
    touch '${meta.id}.macs3_peaks.xls'
    """
}
