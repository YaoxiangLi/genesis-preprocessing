nextflow.enable.dsl = 2

include { VALIDATE_SHEET } from './modules/validate_sheet'
include { CHROM_SIZES } from './modules/chrom_sizes'
include { BWA_MEM2_INDEX } from './modules/bwa_mem2_index'
include { DOWNLOAD } from './modules/download'
include { METADATA } from './modules/metadata'
include { BWA_MEM2_ALIGN } from './modules/bwa_mem2_align'
include { QC } from './modules/qc'
include { TRACKS } from './modules/tracks'
include { CALL_PEAKS } from './modules/call_peaks'
include { BAM_TO_SAM } from './modules/bam_to_sam'
include { PREPARE_QUANTIFICATION } from './modules/prepare_quantification'
include { INTERSECT_PEAKS } from './modules/intersect_peaks'
include { QUANTIFY } from './modules/quantify'

// Bowtie 1 modules deliberately have no imports or calls here.
workflow {
    if (!params.input || params.input instanceof List || params.input.toString().contains(',')) {
        error 'Supply exactly one input TSV with --input INPUT.tsv'
    }
    def sheet = file(params.input, checkIfExists: true)
    if (!sheet.isFile()) { error 'The input must be a single TSV file' }
    def referencesDir = file(params.references).toAbsolutePath()
    for (name in ['bwa_batch_size', 'bwa_seed_length', 'bwa_max_seed_occurrences', 'bwa_score_threshold']) {
        if (!(params[name].toString() ==~ /[1-9][0-9]*/)) {
            error "Parameter --${name} must be a positive integer"
        }
    }
    def resources = [cpus: params.cpus, memory: params.memory, time: params.time]
    def indexResources = [cpus: 1, memory: params.index_memory, time: params.index_time]
    def bwaOptions = [
        batch_size: params.bwa_batch_size, seed_length: params.bwa_seed_length,
        max_seed_occurrences: params.bwa_max_seed_occurrences,
        score_threshold: params.bwa_score_threshold
    ]
    VALIDATE_SHEET(Channel.value(sheet), Channel.value(referencesDir))
    samples = VALIDATE_SHEET.out.sheet.splitCsv(header: true, sep: '\t')
        .map { row ->
            [id: row.sample_id, species: row.species, read1_url: row.read1_url,
             read2_url: row.read2_url, control: row.control_sample,
             reference_fasta: row.reference_fasta,
             ref_id: row.reference_fasta.replaceFirst(/\.(fa|fasta|fna)\.gz$/, ''),
             layout: row.read2_url == '-' ? 'SE' : 'PE']
        }
    referenceInputs = samples.unique { it.ref_id }
        .map { meta ->
            def ref = [id: meta.ref_id, filename: meta.reference_fasta]
            tuple(ref, file("${referencesDir}/${ref.filename}", checkIfExists: true))
        }
    sizesBranches = referenceInputs.branch { ref, fasta ->
        cached: file("${referencesDir}/${ref.id}.chrom.sizes").exists() &&
                file("${referencesDir}/${ref.id}.chrom.sizes").size() > 0
        missing: true
    }
    CHROM_SIZES(sizesBranches.missing)
    sizes = sizesBranches.cached.map { ref, fasta ->
            tuple(ref.id, ref, file("${referencesDir}/${ref.id}.chrom.sizes"))
        }
        .mix(CHROM_SIZES.out.sizes.map { ref, path -> tuple(ref.id, ref, path) })
    indexBranches = referenceInputs.branch { ref, fasta ->
        cached: ['.0123', '.amb', '.ann', '.bwt.2bit.64', '.pac'].every { suffix ->
            def path = file("${referencesDir}/${ref.id}.bwa-mem2/genome${suffix}")
            path.exists() && path.size() > 0
        }
        missing: true
    }
    BWA_MEM2_INDEX(indexBranches.missing, indexResources)
    indexes = indexBranches.cached.map { ref, fasta ->
            tuple(ref.id, ref, file("${referencesDir}/${ref.id}.bwa-mem2"))
        }
        .mix(BWA_MEM2_INDEX.out.index.map { ref, path -> tuple(ref.id, ref, path) })
    DOWNLOAD(samples.map { meta ->
        tuple(meta,
            meta.read1_url.startsWith('file://') ? file(meta.read1_url, checkIfExists: true) : [],
            meta.read2_url.startsWith('file://') ? file(meta.read2_url, checkIfExists: true) : [])
    })
    downloaded = DOWNLOAD.out.reads.map { meta, reads -> tuple(meta.id, meta, reads) }
    metadataInputs = downloaded.map { id, meta, reads -> tuple(meta.ref_id, meta, reads) }
        .combine(sizes, by: 0)
        .map { refId, meta, reads, ref, path -> tuple(meta, reads, path) }
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
        .map { id, original, reads, meta, metadata -> tuple(meta.ref_id, meta, reads, metadata) }
        .combine(indexes, by: 0)
        .map { refId, meta, reads, metadata, ref, index -> tuple(meta, reads, metadata, index) }
    BWA_MEM2_ALIGN(alignmentInputs, resources, bwaOptions)
    aligned = BWA_MEM2_ALIGN.out.aligned
    mainBams = aligned.map { meta, bam, bai, qcBam, qcBai -> tuple(meta, bam, bai) }
    QC(aligned, resources, file(params.spp_script, checkIfExists: true))
    TRACKS(aligned, resources)
    treatments = mainBams.filter { meta, bam, bai -> meta.control != '-' }
        .map { meta, bam, bai -> tuple(meta.control, meta, bam, bai) }
    controls = mainBams.filter { meta, bam, bai -> meta.control == '-' }
        .map { meta, bam, bai -> tuple(meta.id, bam, bai) }
    peakInputs = treatments.combine(controls, by: 0)
        .map { controlId, meta, bam, bai, controlBam, controlBai ->
            tuple(meta, bam, bai, controlBam, controlBai)
        }
    CALL_PEAKS(peakInputs)
    peaksBySample = CALL_PEAKS.out.peaks.map { meta, peaks -> tuple(meta.id, meta, peaks) }
    bamsBySample = mainBams.map { meta, bam, bai -> tuple(meta.id, bam, bai) }
    coverageBySample = TRACKS.out.rpkm.map { meta, coverage -> tuple(meta.id, coverage) }
    quantificationInputs = peaksBySample.join(bamsBySample, by: 0, failOnDuplicate: true)
        .join(coverageBySample, by: 0, failOnDuplicate: true)
        .map { id, meta, peaks, bam, bai, coverage ->
            tuple(meta.ref_id, meta, peaks, bam, bai, coverage)
        }
        .combine(sizes, by: 0)
        .map { refId, meta, peaks, bam, bai, coverage, ref, path ->
            tuple(meta, peaks, bam, bai, coverage, path)
        }
    BAM_TO_SAM(quantificationInputs.map { meta, peaks, bam, bai, coverage, sizes ->
        tuple(meta, bam, bai)
    })
    samBySample = BAM_TO_SAM.out.sam.map { meta, sam -> tuple(meta.id, sam) }
    preparationInputs = quantificationInputs
        .map { meta, peaks, bam, bai, coverage, sizes -> tuple(meta.id, meta, peaks, sizes) }
        .join(samBySample, by: 0, failOnDuplicate: true)
        .map { id, meta, peaks, sizes, sam -> tuple(meta, peaks, sam, sizes) }
    PREPARE_QUANTIFICATION(preparationInputs)
    preparedBySample = PREPARE_QUANTIFICATION.out.prepared
        .map { meta, weights, indexedPeaks, details ->
            tuple(meta.id, meta, weights, indexedPeaks, details)
        }
    intersections = preparedBySample.join(coverageBySample, by: 0, failOnDuplicate: true)
        .map { id, meta, weights, indexedPeaks, details, coverage ->
            tuple(meta, weights, indexedPeaks, coverage)
        }
    INTERSECT_PEAKS(intersections)
    overlapsBySample = INTERSECT_PEAKS.out.overlaps
        .map { meta, reads, coverage -> tuple(meta.id, reads, coverage) }
    scoringInputs = preparedBySample.join(overlapsBySample, by: 0, failOnDuplicate: true)
        .map { id, meta, weights, indexedPeaks, details, reads, coverage ->
            tuple(meta, details, reads, coverage)
        }
    QUANTIFY(scoringInputs)
}
