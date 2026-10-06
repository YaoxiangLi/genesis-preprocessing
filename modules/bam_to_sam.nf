include { dotenv } from 'plugin/nf-dotenv'

process BAM_TO_SAM {
    tag "${meta.id}"
    cpus 1
    memory '1 GB'
    time '1h'
    conda "environments/DAP_SEQ_ALIGNMENT.yaml"
    container "${dotenv('DAP_SEQ_ALIGNMENT_IMAGE')}"
    input:
    tuple val(meta), path(bam), path(bai)
    output:
    tuple val(meta), path("${meta.id}.mapped.sam"), emit: sam
    script:
    """
    samtools view '${bam}' > '${meta.id}.mapped.sam'
    """
    stub:
    """
    printf 'read1\\t0\\tchr1\\t101\\t0\\t50M\\t*\\t0\\t0\\t*\\t*\\n' > '${meta.id}.mapped.sam'
    """
}
