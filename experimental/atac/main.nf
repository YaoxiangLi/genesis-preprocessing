nextflow.enable.dsl = 2

process RAW_FASTQC {
    container 'sha256:97ca1e181a55a1d87653984956983fea3ff76cab5875f45ae2143168ff4fd73d'
    publishDir "${params.outdir}/fastqc", mode: 'copy'
    input:
    tuple val(mate), path(read)
    output:
    path 'raw_*_fastqc.*', emit: reports
    script:
    """
    export XDG_CACHE_HOME="\$PWD/.cache"
    ln -s '${read}' raw_${mate}.fastq.gz
    fastqc --threads 1 --memory 512 --noextract raw_${mate}.fastq.gz
    """
}

process ALIGN_AND_MARK {
    container 'kundajelab/dap_seq_alignment@sha256:4764008ba8fbb5d831bd6f9ed6a720fd494062b39f0bae63ff2e4efd316ad842'
    input:
    path read1, stageAs: 'R1.fastq.gz'
    path read2, stageAs: 'R2.fastq.gz'
    path fasta, stageAs: 'reference.fa.gz'
    output:
    path 'marked.bam', emit: bam
    path 'raw.*.txt', emit: qc
    path 'versions.txt', emit: versions
    script:
    """
    gzip -t R1.fastq.gz R2.fastq.gz reference.fa.gz
    gzip -dc reference.fa.gz > reference.fa
    bwa-mem2 index reference.fa
    bwa-mem2 mem -t ${task.cpus} -R '@RG\\tID:toy\\tSM:toy\\tLB:toy' reference.fa R1.fastq.gz R2.fastq.gz |
      samtools sort -n -o query.bam
    samtools fixmate -m query.bam fixed.bam
    samtools sort -o coordinate.bam fixed.bam
    samtools markdup -s coordinate.bam marked.bam 2> duplicate-marking.txt
    samtools index marked.bam
    samtools flagstat marked.bam > raw.flagstat.txt
    samtools stats marked.bam > raw.stats.txt
    samtools idxstats marked.bam > raw.idxstats.txt
    { bwa-mem2 version; samtools --version; } > versions.txt
    """
}

process FRAGMENTS {
    container 'kundajelab/genesis_tools@sha256:31458d4a6a83541f463ea4b0e692a0afc65c6df441f70c3f71fc4ccf1a11eb59'
    publishDir "${params.outdir}/fragments", mode: 'copy', pattern: '*.{json,bed,bedgraph,txt}'
    input:
    path bam
    path driver
    val organelles
    output:
    path 'usable.bam', emit: bam
    path 'fragments.json', emit: fragments
    path 'metrics.json', emit: metrics
    path 'usable.*.txt', emit: qc
    script:
    """
    python '${driver}' --bam '${bam}' --mapq ${params.mapq} --organelles '${organelles.join(',')}'
    """
}

process PEAKS {
    container 'kundajelab/dap_seq_peaks@sha256:10467dd29e3d25ce7769f76f57402bd1a5a582006e911d06479bfcc3e3325df3'
    publishDir "${params.outdir}/peaks", mode: 'copy', pattern: 'atac*'
    input:
    path bam
    output:
    path 'atac_peaks.narrowPeak', emit: peaks
    script:
    """
    macs3 callpeak -t '${bam}' -f BAMPE -g ${params.genome_size} -q 0.01 --keep-dup all -n atac
    macs3 --version > macs3.version.txt
    """
}

process ENRICHMENT {
    container 'kundajelab/genesis_tools@sha256:31458d4a6a83541f463ea4b0e692a0afc65c6df441f70c3f71fc4ccf1a11eb59'
    publishDir "${params.outdir}/metrics", mode: 'copy'
    input:
    path fragments
    path peaks
    path tss
    path metric_driver
    path driver
    output:
    path 'enrichment.json'
    script:
    """
    PYTHONDONTWRITEBYTECODE=1 python '${driver}' '${fragments}' '${peaks}' '${tss}'
    """
}

process REPORT {
    container 'sha256:3f8fc8c57e57994b95408cd02a7ced44a6fb90396b9067bbe2d2dcdebb396b50'
    publishDir "${params.outdir}/multiqc", mode: 'copy'
    input:
    path reports
    path enrichment
    path config
    path driver
    output:
    path 'multiqc_report.html'
    path 'multiqc_data'
    path 'required-modules.json'
    script:
    """
    export HOME="\$PWD" XDG_CACHE_HOME="\$PWD/.cache"
    multiqc . --config '${config}' --force --require-logs -m fastqc -m samtools --filename multiqc_report.html
    python '${driver}'
    """
}

process PROVENANCE {
    container 'kundajelab/genesis_tools@sha256:31458d4a6a83541f463ea4b0e692a0afc65c6df441f70c3f71fc4ccf1a11eb59'
    publishDir "${params.outdir}", mode: 'copy'
    input:
    path read1, stageAs: 'R1.fastq.gz'
    path read2, stageAs: 'R2.fastq.gz'
    path fasta, stageAs: 'reference.fa.gz'
    path tss
    path source
    path metrics_source
    path completed
    val settings
    output:
    path 'provenance.json'
    script:
    def settingsJson = groovy.json.JsonOutput.toJson(settings)
    """
    cat > settings.json << 'SETTINGS'
${settingsJson}
SETTINGS
    python - <<'PYTHON'
import hashlib,json,platform
from pathlib import Path
report=json.loads(Path('settings.json').read_text())
report['files']={}
for name in ['R1.fastq.gz','R2.fastq.gz','reference.fa.gz','${tss}','${source}','${metrics_source}']:
    with Path(name).open('rb') as stream:
        report['files'][name]=hashlib.file_digest(stream,'sha256').hexdigest()
report['python']=platform.python_version()
report['architecture']=platform.machine()
Path('provenance.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\\n')
PYTHON
    """
}

workflow {
    assert params.adapter_policy == 'none-synthetic-adapter-free', 'Explicit adapter-free synthetic policy required'
    assert params.mapq != null && params.mapq.toInteger() >= 0, 'Explicit MAPQ required'
    assert params.genome_size != null && params.genome_size.toLong() > 0, 'Exact fixture genome size required'
    assert params.organelles instanceof String, 'Supply --organelles NONE or a comma-separated contig list; empty flags are invalid'
    assert params.organelles ==~ /[A-Za-z0-9_.:,\-]+/, 'Invalid organellar list'
    def organelles = params.organelles == 'NONE' ? [] : params.organelles.tokenize(',')
    assert params.outdir, 'Output directory required'
    def read1 = file(params.read1, checkIfExists: true)
    def read2 = file(params.read2, checkIfExists: true)
    RAW_FASTQC(Channel.of(tuple('R1', read1), tuple('R2', read2)))
    ALIGN_AND_MARK(read1, read2, file(params.fasta, checkIfExists: true))
    FRAGMENTS(ALIGN_AND_MARK.out.bam, file("${projectDir}/metrics.py"), organelles)
    PEAKS(FRAGMENTS.out.bam)
    ENRICHMENT(FRAGMENTS.out.fragments, PEAKS.out.peaks, file(params.tss, checkIfExists: true),
               file("${projectDir}/metrics.py"), file("${projectDir}/enrichment.py"))
    reports = RAW_FASTQC.out.reports.mix(ALIGN_AND_MARK.out.qc).mix(FRAGMENTS.out.qc).flatten().collect()
    REPORT(reports, ENRICHMENT.out, file("${projectDir}/multiqc_config.yaml"), file("${projectDir}/verify_multiqc.py"))
    def settings = [source_sha: params.source_sha, nextflow: nextflow.version.toString(),
        mapq: params.mapq, organelles: organelles, adapter_policy: params.adapter_policy,
        duplicate_policy: 'mark_then_exclude', tn5_offsets: [4, -5], genome_size: params.genome_size,
        plant_thresholds: 'UNSPECIFIED', scope: 'experimental synthetic PE fixture']
    PROVENANCE(read1, read2, file(params.fasta), file(params.tss),
               file("${projectDir}/main.nf"), file("${projectDir}/metrics.py"),
               REPORT.out[0], settings)
}
