include { dotenv } from 'plugin/nf-dotenv'

process BWA_MEM2_INDEX {
    cpus { resources.cpus }
    memory { resources.memory }
    time { resources.time }
    conda "environments/DAP_SEQ_ALIGNMENT.yaml"
    container "${dotenv('DAP_SEQ_ALIGNMENT_IMAGE')}"
    tag "${ref.id}"
    publishDir params.references, mode: 'copy', pattern: '*.bwa-mem2'
    input:
    tuple val(ref), path(fasta)
    val resources
    output:
    tuple val(ref), path("${ref.id}.bwa-mem2"), emit: index
    script:
    """
    gzip -dc -- '${fasta}' > reference.fa
    mkdir '${ref.id}.bwa-mem2'
    bwa-mem2 index -p '${ref.id}.bwa-mem2/genome' reference.fa
    for suffix in .0123 .amb .ann .bwt.2bit.64 .pac; do
        test -s '${ref.id}.bwa-mem2/genome'"\$suffix"
    done
    """
    stub:
    """
    mkdir '${ref.id}.bwa-mem2'
    for suffix in .0123 .amb .ann .bwt.2bit.64 .pac; do
        printf 'stub\\n' > '${ref.id}.bwa-mem2/genome'"\$suffix"
    done
    """
}
