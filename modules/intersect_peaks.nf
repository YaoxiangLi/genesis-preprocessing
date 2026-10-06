include { dotenv } from 'plugin/nf-dotenv'

process INTERSECT_PEAKS {
    tag "${meta.id}"
    cpus 1
    memory '4 GB'
    time '2h'
    conda "environments/DAP_SEQ_PEAKS.yaml"
    container "${dotenv('DAP_SEQ_PEAKS_IMAGE')}"
    input:
    tuple val(meta), path(weights), path(indexed_peaks), path(coverage)
    output:
    tuple val(meta), path('reads.overlaps.tsv'), path('coverage.overlaps.tsv'), emit: overlaps
    script:
    """
    bedtools intersect -a '${weights}' -b '${indexed_peaks}' -wa -wb > reads.overlaps.tsv
    bedtools intersect -a '${coverage}' -b '${indexed_peaks}' -wa -wb > coverage.overlaps.tsv
    """
    stub:
    """
    printf 'chr1\\t100\\t150\\t1\\tchr1\\t100\\t200\\t0\\n' > reads.overlaps.tsv
    printf 'chr1\\t0\\t1000\\t0\\tchr1\\t100\\t200\\t0\\n' > coverage.overlaps.tsv
    """
}
