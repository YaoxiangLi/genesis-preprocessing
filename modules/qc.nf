include { dotenv } from 'plugin/nf-dotenv'

process QC {
    cpus { resources.cpus }
    memory { resources.memory }
    time { resources.time }
    conda "environments/DAP_SEQ_QC.yaml"
    container "${dotenv('DAP_SEQ_QC_IMAGE')}"
    tag "${meta.id}"
    publishDir "${params.workspace}/${meta.species}/${meta.id}", mode: 'copy',
        pattern: '*.qc.report.*'
    input:
    tuple val(meta), path(bam), path(bai), path(qc_bam), path(qc_bai)
    val resources
    path spp_script
    output:
    tuple val(meta), path("${meta.id}.qc.report.*"), emit: reports
    script:
    def insert = meta.layout == 'PE' ? """
        awk 'BEGIN {OFS="\\t"; print "insert_length","count","fraction"}
            \$1 == "IS" {n++; lengths[n]=\$2; counts[n]=\$3; total+=\$3}
            END {for (i=1;i<=n;i++) print lengths[i],counts[i],(total ? counts[i]/total : 0)}' \
            '${meta.id}.qc.report.main.stats.txt' > '${meta.id}.qc.report.insert_lengths.tsv'
        """ : ''
    """
    samtools flagstat '${bam}' > '${meta.id}.qc.report.flagstat.txt'
    samtools idxstats '${bam}' > '${meta.id}.qc.report.idxstats.tsv'
    samtools stats '${bam}' > '${meta.id}.qc.report.main.stats.txt'
    samtools stats '${qc_bam}' > '${meta.id}.qc.report.read1.stats.txt'
    ${insert}
    mkdir qc-bin
    ln -s "\$(command -v gawk)" qc-bin/awk
    export PATH="\$PWD/qc-bin:\$PATH"
    Rscript "${spp_script}" -c='${qc_bam}' \
        -p=${task.cpus} -rf -s=-0:2:400 \
        '-savp=${meta.id}.qc.report.spp.pdf' '-out=${meta.id}.qc.report.spp.tsv'
    """
    stub:
    """
    printf 'stub\\n' > '${meta.id}.qc.report.spp.tsv'
    touch '${meta.id}.qc.report.spp.pdf' '${meta.id}.qc.report.flagstat.txt'
    """
}
