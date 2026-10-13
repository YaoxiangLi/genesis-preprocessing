include { dotenv } from 'plugin/nf-dotenv'

process CHROM_SIZES {
    cpus 1
    memory '1 GB'
    time '1h'
    conda "environments/DAP_SEQ_ALIGNMENT.yaml"
    container "${dotenv('DAP_SEQ_ALIGNMENT_IMAGE')}"
    tag "${ref.id}"
    publishDir params.references, mode: 'copy', pattern: '*.chrom.sizes*'
    input:
    tuple val(ref), path(fasta)
    path provenanceScript
    output:
    tuple val(ref), path("${ref.id}.chrom.sizes"), emit: sizes
    path "${ref.id}.chrom.sizes.provenance.json", emit: provenance
    script:
    """
    gzip -dc -- '${fasta}' > reference.fa
    samtools faidx reference.fa
    cut -f1,2 reference.fa.fai > '${ref.id}.chrom.sizes'
    python '${provenanceScript}' --fasta '${fasta}' --artifact '${ref.id}.chrom.sizes' \\
        --kind chrom-sizes --mode real --container '${ref.generator_container}' \\
        --recipe '${ref.sizes_recipe}'
    """
    stub:
    """
    printf 'chr1\\t1000\\n' > '${ref.id}.chrom.sizes'
    python '${provenanceScript}' --fasta '${fasta}' --artifact '${ref.id}.chrom.sizes' \\
        --kind chrom-sizes --mode stub --container '${ref.generator_container}' \\
        --recipe '${ref.sizes_recipe}'
    """
}
