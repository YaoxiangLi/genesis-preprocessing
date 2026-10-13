include { dotenv } from 'plugin/nf-dotenv'

process DAP_PROVENANCE {
    cpus 1
    memory '1 GB'
    time '1h'
    conda "environments/GENESIS_TOOLS.yaml"
    container "${dotenv('GENESIS_TOOLS_IMAGE')}"
    tag 'run'
    publishDir "${params.run_dir}/output/provenance", mode: 'copy', pattern: 'dap-run.json'
    input:
    tuple val(names), path(products, stageAs: 'products/*')
    path receipts, stageAs: 'tasks/*'
    path checksums, stageAs: 'reads/*'
    val references
    val context
    path sheet
    path driver
    output:
    path 'dap-run.json', emit: manifest
    script:
    def manifest = groovy.json.JsonOutput.toJson([context: context, references: references,
        products: [names, products.collect { it.toString() }].transpose()])
    """
    cat > context.json << 'GENESIS_PROVENANCE_CONTEXT'
${manifest}
GENESIS_PROVENANCE_CONTEXT
    python '${driver}' --context context.json --sheet '${sheet}' --output dap-run.json
    """
    stub:
    def manifest = groovy.json.JsonOutput.toJson([context: context, references: references,
        products: [names, products.collect { it.toString() }].transpose()])
    """
    cat > context.json << 'GENESIS_PROVENANCE_CONTEXT'
${manifest}
GENESIS_PROVENANCE_CONTEXT
    python '${driver}' --context context.json --sheet '${sheet}' --output dap-run.json
    """
}
