include { dotenv } from 'plugin/nf-dotenv'

process VALIDATE_SHEET {
    cpus 1
    memory '1 GB'
    time '1h'
    conda "environments/GENESIS_TOOLS.yaml"
    container "${dotenv('GENESIS_TOOLS_IMAGE')}"
    input:
    path sheet
    path references
    output:
    path 'validated.tsv', emit: sheet
    script:
    """
    genesis-tools validate-sheet --sheet '${sheet}' \
        --references '${references}' --output validated.tsv
    """
    stub:
    """
    genesis-tools validate-sheet --sheet '${sheet}' \
        --references '${references}' --output validated.tsv
    """
}
