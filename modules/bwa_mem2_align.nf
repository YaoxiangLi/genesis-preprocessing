include { dotenv } from 'plugin/nf-dotenv'

process BWA_MEM2_ALIGN {
    cpus { resources.cpus }
    memory { resources.memory }
    time { resources.time }
    conda "environments/DAP_SEQ_ALIGNMENT.yaml"
    container "${dotenv('DAP_SEQ_ALIGNMENT_IMAGE')}"
    tag "${meta.id}"
    publishDir "${params.workspace}/${meta.species}/${meta.id}", mode: 'copy',
        pattern: '*.alignment.tsv'
    input:
    tuple val(meta), path(reads), path(metadata), path(index)
    val resources
    val bwa_options
    output:
    tuple val(meta), path("${meta.id}.primary.bam"), path("${meta.id}.primary.bam.bai"),
        path("${meta.id}.qc.bam"), path("${meta.id}.qc.bam.bai"), emit: aligned
    tuple val(meta), path("${meta.id}.alignment.tsv"), emit: provenance
    script:
    def files = reads instanceof List ? reads.sort { it.name } : [reads]
    def inputs = files.collect { "'${it}'" }.join(' ')
    def threads = Math.max(1, task.cpus - 1)
    def options = "-K ${bwa_options.batch_size} -k ${bwa_options.seed_length} " +
        "-c ${bwa_options.max_seed_occurrences} -T ${bwa_options.score_threshold}"
    """
    bwa-mem2 mem -t ${threads} ${options} -R '@RG\\tID:${meta.id}\\tSM:${meta.id}\\tPL:ILLUMINA' \
        "${index}/genome" ${inputs} \
        2> main.bwa.log | samtools view -u -F 2308 - | \
        samtools sort -m 512M -o '${meta.id}.primary.bam' -
    samtools index '${meta.id}.primary.bam'
    bwa-mem2 mem -t ${threads} ${options} -R '@RG\\tID:${meta.id}.qc\\tSM:${meta.id}\\tPL:ILLUMINA' \
        "${index}/genome" '${files[0]}' \
        2> qc.bwa.log | samtools view -u -F 2308 - | \
        samtools sort -m 512M -o '${meta.id}.qc.bam' -
    samtools index '${meta.id}.qc.bam'
    printf 'sample_id\\taligner\\tversion\\tlayout\\tread_length\\tmapq_filter\\tflag_exclude\\tbwa_options\\tqc_reads\\n' > '${meta.id}.alignment.tsv'
    printf '%s\\tbwa-mem2\\t%s\\t%s\\t%s\\tnone\\t2308\\t%s\\tfull_read1_unpaired\\n' \
        '${meta.id}' "\$(bwa-mem2 version)" '${meta.layout}' '${meta.read_length}' '${options}' >> '${meta.id}.alignment.tsv'
    """
    stub:
    """
    touch '${meta.id}.primary.bam' '${meta.id}.primary.bam.bai' '${meta.id}.qc.bam' '${meta.id}.qc.bam.bai'
    printf 'stub\\n' > '${meta.id}.alignment.tsv'
    """
}
