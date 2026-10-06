include { dotenv } from 'plugin/nf-dotenv'

process DOWNLOAD {
    cpus 1
    memory '1 GB'
    time '1h'
    conda "environments/DAP_SEQ_ALIGNMENT.yaml"
    container "${dotenv('DAP_SEQ_ALIGNMENT_IMAGE')}"
    tag "${meta.id}"
    publishDir "${params.workspace}/${meta.species}/${meta.id}", mode: 'copy',
        pattern: '*.fastq.lines'
    input:
    tuple val(meta), path(local_read1, stageAs: 'read1/*'), path(local_read2, stageAs: 'read2/*')
    output:
    tuple val(meta), path("${meta.id}.read*.fastq.gz"), emit: reads
    tuple val(meta), path("${meta.id}.fastq.lines"), emit: counts
    script:
    def source1 = meta.read1_url.startsWith('file://') ? local_read1 : meta.read1_url
    def source2 = meta.read2_url.startsWith('file://') ? local_read2 : meta.read2_url
    def second = meta.layout == 'PE' ?
        "download '${source2}' '${meta.id}.read2.fastq.gz'\n" +
        "test \"\$(gzip -cd '${meta.id}.read2.fastq.gz' | wc -l)\" -eq \"\$(cat '${meta.id}.fastq.lines')\"" : ''
    """
    download() {
        local url=\$1 destination=\$2
        if [[ \$url != http://* && \$url != https://* ]]; then
            cp -- "\$url" "\$destination"
        else
            wget --tries=3 --timeout=60 --no-verbose -O "\$destination" "\$url"
        fi
        gzip -t -- "\$destination"
    }
    download '${source1}' '${meta.id}.read1.fastq.gz'
    gzip -cd '${meta.id}.read1.fastq.gz' | \
        awk 'END {if (NR == 0 || NR % 4) exit 1; print NR}' > '${meta.id}.fastq.lines'
    ${second}
    """
    stub:
    def second = meta.layout == 'PE' ? "cp '${meta.id}.read1.fastq.gz' '${meta.id}.read2.fastq.gz'" : ''
    """
    printf '@read1\\nAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\\n+\\nIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII\\n' | gzip > '${meta.id}.read1.fastq.gz'
    printf '4\\n' > '${meta.id}.fastq.lines'
    ${second}
    """
}
