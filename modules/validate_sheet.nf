include { dotenv } from 'plugin/nf-dotenv'

process VALIDATE_SHEET {
    // Recheck FASTA and product bytes even when size and mtime are unchanged.
    cache false
    cpus 1
    memory '1 GB'
    time '1h'
    conda "environments/GENESIS_TOOLS.yaml"
    container "${dotenv('GENESIS_TOOLS_IMAGE')}"
    input:
    path sheet
    path references
    val recipes
    path toolsSource
    output:
    path 'validated.tsv', emit: sheet
    script:
    def recipesJson = groovy.json.JsonOutput.toJson(recipes)
    """
    cat > reference_recipes.json << 'REFERENCE_RECIPES'
${recipesJson}
REFERENCE_RECIPES
    # Stage the checked-out validator explicitly; the pinned image supplies its dependencies.
    export PYTHONPATH='${toolsSource}'
    export PYTHONDONTWRITEBYTECODE=1
    genesis-tools validate-sheet --sheet '${sheet}' \
        --references '${references}' --output validated.tsv \
        --reference-recipes reference_recipes.json --reference-mode real
    """
    stub:
    def recipesJson = groovy.json.JsonOutput.toJson(recipes)
    """
    cat > reference_recipes.json << 'REFERENCE_RECIPES'
${recipesJson}
REFERENCE_RECIPES
    export PYTHONPATH='${toolsSource}'
    export PYTHONDONTWRITEBYTECODE=1
    genesis-tools validate-sheet --sheet '${sheet}' \
        --references '${references}' --output validated.tsv \
        --reference-recipes reference_recipes.json --reference-mode stub
    """
}
