nextflow.enable.dsl = 2

include { validateParameters; paramsSummaryLog } from 'plugin/nf-schema'
include { dotenv } from 'plugin/nf-dotenv'
include { VALIDATE_SHEET } from './modules/validate_sheet'
include { CHROM_SIZES } from './modules/chrom_sizes'
include { BWA_MEM2_INDEX } from './modules/bwa_mem2_index'
include { DOWNLOAD } from './modules/download'
include { FASTQC } from './modules/fastqc'
include { METADATA } from './modules/metadata'
include { BWA_MEM2_ALIGN } from './modules/bwa_mem2_align'
include { QC } from './modules/qc'
include { MULTIQC } from './modules/multiqc'
include { TRACKS } from './modules/tracks'
include { CALL_PEAKS } from './modules/call_peaks'
include { QUANTIFY } from './modules/quantify'
include { DAP_PROVENANCE } from './modules/dap_provenance'

// Bowtie 1 modules deliberately have no imports or calls here.
workflow {
    // nextflow_schema.json checks the input sheet, paths, resources, and BWA options.
    validateParameters()
    log.info(paramsSummaryLog(workflow))
    def sheet = file(params.input)
    def referencesDir = file(params.references).toAbsolutePath()
    def resources = [cpus: params.cpus, memory: params.memory, time: params.time]
    def bwaOptions = [
        batch_size: params.bwa_batch_size, seed_length: params.bwa_seed_length,
        max_seed_occurrences: params.bwa_max_seed_occurrences,
        score_threshold: params.bwa_score_threshold
    ]
    def provenanceScript = file("${projectDir}/genesis_tools/src/genesis_tools/reference_cache.py")
    def recipeHash = { module ->
        def digest = java.security.MessageDigest.getInstance('SHA-256')
        digest.update(file("${projectDir}/modules/${module}.nf").bytes)
        digest.update(provenanceScript.bytes)
        digest.digest().encodeHex().toString()
    }
    def generator = dotenv('DAP_SEQ_ALIGNMENT_IMAGE')
    def sizesRecipe = recipeHash('chrom_sizes')
    def indexRecipe = recipeHash('bwa_mem2_index')
    def recipes = [
        'chrom-sizes': [container: generator, recipe_sha256: sizesRecipe],
        'bwa-mem2': [container: generator, recipe_sha256: indexRecipe]
    ]
    VALIDATE_SHEET(Channel.value(sheet), Channel.value(referencesDir), recipes,
                   file("${projectDir}/genesis_tools/src"))
    samples = VALIDATE_SHEET.out.sheet.splitCsv(header: true, sep: '\t')
        .map { row ->
            [id: row.sample_id, species: row.species, read1_url: row.read1_url,
             read2_url: row.read2_url, control: row.control_sample,
             reference_fasta: row.reference_fasta,
             ref_id: row.reference_fasta.replaceFirst(/\.(fa|fasta|fna)\.gz$/, ''),
             layout: row.read2_url == '-' ? 'SE' : 'PE']
        }
    referenceInputs = samples.unique { sample -> sample.ref_id }
        .map { meta ->
            def ref = [id: meta.ref_id, filename: meta.reference_fasta,
                       generator_container: generator, sizes_recipe: sizesRecipe,
                       index_recipe: indexRecipe]
            tuple(ref, file("${referencesDir}/${ref.filename}", checkIfExists: true))
        }
    sizesBranches = referenceInputs.branch { ref, _fasta ->
        cached: file("${referencesDir}/${ref.id}.chrom.sizes").exists() &&
                file("${referencesDir}/${ref.id}.chrom.sizes").size() > 0
        missing: true
    }
    CHROM_SIZES(sizesBranches.missing, provenanceScript)
    sizes_ch = sizesBranches.cached.map { ref, _fasta ->
            tuple(ref.id, ref, file("${referencesDir}/${ref.id}.chrom.sizes"))
        }
        .mix(CHROM_SIZES.out.sizes.map { ref, path -> tuple(ref.id, ref, path) })
    indexBranches = referenceInputs.branch { ref, _fasta ->
        cached: ['.0123', '.amb', '.ann', '.bwt.2bit.64', '.pac'].every { suffix ->
            def path = file("${referencesDir}/${ref.id}.bwa-mem2/genome${suffix}")
            path.exists() && path.size() > 0
        }
        missing: true
    }
    // Indexing sizes its memory and time from the reference length.
    genomeLengths = sizes_ch.map { id, _ref, path ->
        tuple(id, path.readLines().sum { line -> line.tokenize('\t')[1].toLong() })
    }
    indexInputs = indexBranches.missing.map { ref, fasta -> tuple(ref.id, ref, fasta) }
        .join(genomeLengths, by: 0, failOnDuplicate: true)
        .map { _id, ref, fasta, length -> tuple(ref + [length: length], fasta) }
    BWA_MEM2_INDEX(indexInputs, provenanceScript)
    indexes = indexBranches.cached.map { ref, _fasta ->
            tuple(ref.id, ref, file("${referencesDir}/${ref.id}.bwa-mem2"))
        }
        .mix(BWA_MEM2_INDEX.out.index.map { ref, path -> tuple(ref.id, ref, path) })
    DOWNLOAD(samples.collate(params.download_batch_size))
    // Split each batch back into one tuple per sample: a single read path for SE, a list for PE.
    downloaded = DOWNLOAD.out.downloads.flatMap { batch, reads, _counts ->
        def files = reads instanceof List ? reads : [reads]
        batch.collect { meta ->
            def names = ['read1', 'read2'].collect { mate -> "${meta.id}.${mate}.fastq.gz".toString() }
            def mates = files.findAll { read -> read.name in names }.sort { read -> read.name }
            tuple(meta.id, meta, mates.size() == 1 ? mates[0] : mates)
        }
    }
    // Observe each raw mate independently; alignment continues to consume the original reads.
    fastqcInputs = downloaded.flatMap { _id, meta, reads ->
        def files = reads instanceof List ? reads : [reads]
        files.collect { read ->
            def mate = read.name.endsWith('.read2.fastq.gz') ? 'read2' : 'read1'
            tuple(meta, mate, read)
        }
    }
    FASTQC(fastqcInputs)
    metadataInputs = downloaded.map { _id, meta, reads -> tuple(meta.ref_id, meta, reads) }
        .combine(sizes_ch, by: 0)
        .map { _refId, meta, reads, _ref, path -> tuple(meta, reads, path) }
    METADATA(metadataInputs)
    inferred = METADATA.out.metadata.map { meta, path ->
        def lines = path.readLines()
        def values = [lines[0].split('\t').toList(), lines[1].split('\t').toList()]
            .transpose().collectEntries { it }
        tuple(meta.id, meta + [
            genome_size: values.genome_size.toLong(),
            read_length: values.analysis_read_length.toInteger()
        ], path)
    }
    alignmentInputs = downloaded.join(inferred, by: 0, failOnDuplicate: true, failOnMismatch: true)
        .map { _id, _original, reads, meta, metadata -> tuple(meta.ref_id, meta, reads, metadata) }
        .combine(indexes, by: 0)
        .map { _refId, meta, reads, metadata, _ref, index -> tuple(meta, reads, metadata, index) }
    BWA_MEM2_ALIGN(alignmentInputs, bwaOptions, params.spp_read_length)
    aligned = BWA_MEM2_ALIGN.out.aligned
    mainBams = aligned.map { meta, bam, bai, _qcBam, _qcBai -> tuple(meta, bam, bai) }
    sppBams = BWA_MEM2_ALIGN.out.spp.map { meta, sppBam -> tuple(meta.id, sppBam) }
    qcInputs = aligned
        .map { meta, bam, bai, qcBam, qcBai -> tuple(meta.id, meta, bam, bai, qcBam, qcBai) }
        .join(sppBams, by: 0, failOnDuplicate: true, failOnMismatch: true)
        .map { _id, meta, bam, bai, qcBam, qcBai, sppBam ->
            tuple(meta, bam, bai, qcBam, qcBai, sppBam)
        }
    QC(qcInputs, resources, file(params.spp_script))
    // Collect channels, not publishDir contents: wait for every library's QC and metadata.
    multiqcFiles = FASTQC.out.reports.map { _meta, _mate, _html, zip -> zip }
        .mix(QC.out.reports.map { _meta, reports -> reports })
        .mix(METADATA.out.metadata.map { _meta, path -> path })
        .flatten().collect().map { paths -> paths.sort { it.name } }
    multiqcSamples = samples.map { meta ->
        [id: meta.id, species: meta.species, ref_id: meta.ref_id,
         reference_fasta: meta.reference_fasta, layout: meta.layout, control: meta.control]
    }.collect().map { rows -> rows.sort { it.id } }
    // Local Nextflow runs can have a null commitId. Git is needed only for provenance.
    def gitSha = workflow.commitId ?: 'UNKNOWN'
    def sourceStatus = 'UNKNOWN'
    try {
        def revision = ['git', '-C', projectDir.toString(), 'rev-parse', 'HEAD'].execute()
        def revisionText = revision.text.trim()
        if (revision.waitFor() == 0) {
            gitSha = revisionText
            def status = ['git', '-C', projectDir.toString(), 'status', '--porcelain',
                          '--untracked-files=no'].execute()
            def statusText = status.text.trim()
            if (status.waitFor() == 0) sourceStatus = statusText ? 'dirty' : 'clean'
        }
    } catch (IOException ignored) {
        log.warn('Git unavailable: MultiQC source provenance may be UNKNOWN')
    }
    def reportProvenance = [name: file(params.run_dir).name, git_sha: gitSha,
                           source_status: sourceStatus, pipeline_version: workflow.manifest.version]
    MULTIQC(multiqcFiles, multiqcSamples, reportProvenance,
            file("${projectDir}/multiqc_config.yaml"),
            file("${projectDir}/genesis_tools/src/genesis_tools/multiqc_reporting.py"))
    TRACKS(aligned, resources)
    treatments = mainBams.filter { meta, _bam, _bai -> meta.control != '-' }
        .map { meta, bam, bai -> tuple(meta.control, meta, bam, bai) }
    controls = mainBams.filter { meta, _bam, _bai -> meta.control == '-' }
        .map { meta, bam, bai -> tuple(meta.id, bam, bai) }
    peakInputs = treatments.combine(controls, by: 0)
        .map { _controlId, meta, bam, bai, controlBam, controlBai ->
            tuple(meta, bam, bai, controlBam, controlBai)
        }
    CALL_PEAKS(peakInputs)
    peaksBySample = CALL_PEAKS.out.peaks.map { meta, peaks -> tuple(meta.id, meta, peaks) }
    bamsBySample = mainBams.map { meta, bam, bai -> tuple(meta.id, bam, bai) }
    coverageBySample = TRACKS.out.rpkm.map { meta, coverage -> tuple(meta.id, coverage) }
    quantificationInputs = peaksBySample.join(bamsBySample, by: 0, failOnDuplicate: true)
        .join(coverageBySample, by: 0, failOnDuplicate: true)
        .map { _id, meta, peaks, bam, _bai, coverage ->
            tuple(meta.ref_id, meta, peaks, bam, coverage)
        }
        .combine(sizes_ch, by: 0)
        .map { _refId, meta, peaks, bam, coverage, _ref, path ->
            tuple(meta, peaks, bam, coverage, path)
        }
    QUANTIFY(quantificationInputs)

    // Feed completed channels, never an asynchronously published output directory.
    def entries = { meta, paths, suffix = '' ->
        (paths instanceof List ? paths : [paths]).collect { path ->
            [relative: "${meta.species}/${meta.id}/${suffix}${path.name}".toString(), file: path]
        }
    }
    provenanceProducts = DOWNLOAD.out.downloads.flatMap { batch, _reads, counts ->
            (counts instanceof List ? counts : [counts]).collect { path ->
                def meta = batch.find { "${it.id}.fastq.lines" == path.name }
                entries(meta, path)[0]
            }
        }
        .mix(FASTQC.out.reports.flatMap { meta, _mate, html, zip -> entries(meta, [html, zip], 'qc/fastqc/') })
        .mix(FASTQC.out.version.flatMap { meta, _mate, path -> entries(meta, path, 'qc/fastqc/') })
        .mix(METADATA.out.metadata.flatMap { meta, path -> entries(meta, path) })
        .mix(BWA_MEM2_ALIGN.out.provenance.flatMap { meta, path -> entries(meta, path) })
        .mix(QC.out.reports.flatMap { meta, paths -> entries(meta, paths) })
        .mix(TRACKS.out.tracks.flatMap { meta, paths -> entries(meta, paths) })
        .mix(CALL_PEAKS.out.results.flatMap { meta, paths -> entries(meta, paths) })
        .mix(QUANTIFY.out.quantified.flatMap { meta, rpm, rpkm -> entries(meta, [rpm, rpkm]) })
        .mix(MULTIQC.out.html.map { path -> [relative: 'multiqc/multiqc_report.html', file: path] })
        .mix(MULTIQC.out.data.map { path -> [relative: 'multiqc/multiqc_data', file: path] })
        .collect().map { rows ->
            def ordered = rows.sort { it.relative }
            tuple(ordered.collect { it.relative }, ordered.collect { it.file })
        }
    taskReceipts = DOWNLOAD.out.receipt.mix(FASTQC.out.receipt, METADATA.out.receipt,
        BWA_MEM2_ALIGN.out.receipt, QC.out.receipt, TRACKS.out.receipt, CALL_PEAKS.out.receipt,
        QUANTIFY.out.receipt, MULTIQC.out.receipt).collect().map { paths -> paths.sort { it.name } }
    readReceipts = DOWNLOAD.out.checksums.collect().map { paths -> paths.sort { it.name } }
    def digestFile = { path ->
        java.security.MessageDigest.getInstance('SHA-256').digest(path.bytes).encodeHex().toString()
    }
    referenceReceipts = sizes_ch.combine(indexes, by: 0).map { id, ref, sizes, _indexRef, index ->
        def parse = { path -> new groovy.json.JsonSlurper().parseText(path.text) }
        [id: id, filename: ref.filename,
         contigs: sizes.readLines().collectEntries { line ->
             def fields = line.split('\t'); [(fields[0]): fields[1].toLong()]
         },
         contig_order: sizes.readLines().collect { it.split('\t')[0] },
         sizes_sha256: digestFile(sizes),
         sizes_cache: parse(file("${sizes}.provenance.json")),
         index_cache: parse(index.resolve('provenance.json'))]
    }.collect().map { rows -> rows.sort { it.id } }
    // Hash the implementation and locked tool definitions, including dirty working copies.
    // Clean Git identity is required for complete provenance; dirty runs remain inspectable.
    def sourceFiles = [file("${projectDir}/main.nf"), file("${projectDir}/nextflow.config"),
        file("${projectDir}/.env"), file("${projectDir}/multiqc_config.yaml"), file(params.spp_script)] +
        file("${projectDir}/modules/*.nf") + [file("${projectDir}/workflows/dap_receipt.nf")] +
        file("${projectDir}/environments/*.yaml") + file("${projectDir}/environments/*.lock") +
        [provenanceScript, file("${projectDir}/genesis_tools/src/genesis_tools/dap_provenance.py"),
         file("${projectDir}/genesis_tools/uv.lock")]
    def runContext = [schema_version: 1, git_sha: gitSha, source_status: sourceStatus,
        nextflow_version: nextflow.version.toString(), profile: workflow.profile,
        source_hashes: sourceFiles.collectEntries { path -> [(path.toString()): digestFile(path)] },
        parameters: [bwa: bwaOptions, spp_read_length: params.spp_read_length,
            spp_script_sha256: digestFile(file(params.spp_script)), download_batch_size: params.download_batch_size,
            mapq_filter: 'none', flag_exclude: 2308, alignment_duplicates: 'retain',
            peak_duplicates: 'MACS3 default keep-dup=1', peak_format: 'SE:BAM;PE:BAMPE',
            quantification_unit: 'primary mapped read ends', track_normalization: 'CPM',
            track_bin_size: 1, strand_denominator: 'all retained mapped read ends']]
    DAP_PROVENANCE(provenanceProducts, taskReceipts, readReceipts, referenceReceipts,
        runContext, sheet, file("${projectDir}/genesis_tools/src/genesis_tools/dap_provenance.py"))
}
