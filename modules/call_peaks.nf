include { dotenv } from 'plugin/nf-dotenv'

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
    output:
    tuple val(meta), path("${meta.id}.macs3_peaks.narrowPeak.gz"), emit: peaks
    tuple val(meta), path("${meta.id}.macs3*"), emit: results
    script:
    def format = meta.layout == 'PE' ? 'BAMPE' : 'BAM'
    """
    macs3 callpeak -t '${bam}' -c '${control_bam}' \
        -f ${format} -g ${meta.genome_size} -n '${meta.id}.macs3'
    gzip -f '${meta.id}.macs3_peaks.narrowPeak'
    """
    stub:
    """
    printf 'chr1\\t100\\t200\\tpeak1\\t100\\t.\\t1\\t2\\t3\\t50\\n' | gzip > '${meta.id}.macs3_peaks.narrowPeak.gz'
    touch '${meta.id}.macs3_peaks.xls'
    """
}
