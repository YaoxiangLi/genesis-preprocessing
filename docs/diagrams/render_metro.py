"""Render the Genesis documentation maps with Python's standard library.

Run from any directory: python docs/diagrams/render_metro.py
The geometry is deliberately authored, not inferred from Nextflow text. Review
routes against main.nf whenever scientific stages or publication boundaries change.
"""
from pathlib import Path
from html import escape
import hashlib

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/images'
COLORS = {'reads':'#087f8c', 'reference':'#4169b1', 'qc':'#9260b7',
          'peaks':'#d76a35', 'tracks':'#438362', 'spp':'#bd527d', 'future':'#81909f'}


def route(points):
    """Orthogonal routes with radius-limited rounded corners."""
    d = f'M {points[0][0]} {points[0][1]}'
    for i in range(1, len(points)-1):
        a, b, c = points[i-1], points[i], points[i+1]
        before = min(15, (abs(b[0]-a[0])+abs(b[1]-a[1]))/2,
                     (abs(c[0]-b[0])+abs(c[1]-b[1]))/2)
        l1 = abs(b[0]-a[0])+abs(b[1]-a[1])
        l2 = abs(c[0]-b[0])+abs(c[1]-b[1])
        p = (b[0]+(a[0]-b[0])*before/l1, b[1]+(a[1]-b[1])*before/l1)
        q = (b[0]+(c[0]-b[0])*before/l2, b[1]+(c[1]-b[1])*before/l2)
        d += f' L {p[0]:g} {p[1]:g} Q {b[0]} {b[1]} {q[0]:g} {q[1]:g}'
    return d + f' L {points[-1][0]} {points[-1][1]}'


def document(title, subtitle, nodes, edges, sections, notes, animated=False, roadmap=False):
    css = '''
    svg{--bg:#fbfcfe;--text:#172c3d;--muted:#536779;--panel:#eef2f6;--white:#fff;background:var(--bg);font-family:Arial,Helvetica,sans-serif}
    .title{font-size:31px;font-weight:700;letter-spacing:1px;fill:var(--text)}
    .subtitle,.note{font-size:14px;fill:var(--muted)}
    .section{font-size:12px;font-weight:700;letter-spacing:1.8px;fill:var(--muted)}
    .label{font-size:17px;font-weight:700;fill:var(--text);paint-order:stroke;stroke:var(--bg);stroke-width:5px;stroke-linejoin:round}
    .detail{font-size:12px;fill:var(--muted);paint-order:stroke;stroke:var(--bg);stroke-width:4px}
    .station{fill:var(--bg);stroke-width:4}
    .line{fill:none;stroke-width:5;stroke-linecap:round;stroke-linejoin:round}
    .planned{stroke-dasharray:9 9;opacity:.8}
    .flow{fill:none;stroke:var(--white);stroke-width:2;stroke-dasharray:2 38;stroke-linecap:round;animation:travel 12s linear infinite;pointer-events:none}
    @keyframes travel{to{stroke-dashoffset:-400}}
    @media(prefers-reduced-motion:reduce){.flow{display:none}}
    @media(prefers-color-scheme:dark){svg{--bg:#14212d;--text:#eff6fc;--muted:#bdcbd6;--panel:#213342;--white:#fff}.line{filter:brightness(1.25)}}
    @media print{.flow{display:none}svg{--bg:#fff;--text:#172c3d;--muted:#536779;--panel:#eef2f6}}
    '''
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1480 870" role="img" aria-labelledby="title description">',
             f'<title id="title">{escape(title)}</title>',
             f'<desc id="description">{escape(subtitle)}. Routes show data dependencies, not timing. '+
             escape(' '.join(notes))+'</desc>', f'<style>{css}</style>',
             '<rect width="1480" height="870" fill="var(--bg)"/>',
             '<path d="M42 34 L57 20 L72 34 L57 48 Z" fill="#087f8c"/>',
             f'<text class="title" x="90" y="46">{escape(title)}</text>',
             f'<text class="subtitle" x="90" y="74">{escape(subtitle)}</text>']
    for x,w,label in sections:
        parts += [f'<rect x="{x}" y="99" width="{w}" height="32" rx="8" fill="var(--panel)"/>',
                  f'<text class="section" x="{x+14}" y="120">{escape(label)}</text>']
    for i,(color,points,label,status) in enumerate(edges):
        path = route(points)
        cls = 'line planned' if status == 'planned' else 'line'
        parts.append(f'<path id="route-{i}" class="{cls}" stroke="{COLORS[color]}" d="{path}"><title>{escape(label)}</title></path>')
        if animated and status != 'planned':
            parts.append(f'<path class="flow" style="animation-delay:-{i%12}s" d="{path}"/>')
    for ident,x,y,label,detail,color,status in nodes:
        parts += [f'<g id="{ident}"><title>{escape(label+": "+detail+"; "+status)}</title>',
                  f'<circle class="station" cx="{x}" cy="{y}" r="8" stroke="{COLORS[color]}"/>',
                  f'<text class="label" text-anchor="middle" x="{x}" y="{y+32}">{escape(label)}</text>',
                  f'<text class="detail" text-anchor="middle" x="{x}" y="{y+50}">{escape(detail)}</text></g>']
    parts.append('<path d="M42 770 H1438" stroke="var(--panel)" stroke-width="2"/>')
    for i,note in enumerate(notes):
        parts.append(f'<text class="note" x="48" y="{797+i*23}">{escape(note)}</text>')
    fingerprint = hashlib.sha256((ROOT/'main.nf').read_bytes()).hexdigest()
    parts.append(f'<metadata>Genesis diagram schema 1; workflow SHA256 {fingerprint}; animation is schematic.</metadata>')
    parts.append('</svg>')
    return '\n'.join(parts)+'\n'


nodes = [
 ('samples',110,300,'Sample sheet','SE / PE • explicit controls','reads','implemented'),
 ('VALIDATE_SHEET',290,300,'Validate','Samples + reference provenance','reads','implemented'),
 ('DOWNLOAD',480,300,'Download','Original mates remain unchanged','reads','implemented'),
 ('FASTQC',680,185,'FastQC','One report per mate','qc','implemented'),
 ('METADATA',680,420,'Metadata','Genome size + read length','reads','implemented'),
 ('BWA_MEM2_ALIGN',850,300,'bwa-mem2','Primary full-read alignments','reads','implemented'),
 ('QC',1080,245,'samtools QC','flagstat · stats · idxstats','qc','implemented'),
 ('MULTIQC',1320,185,'MultiQC','Run-level HTML + parsed data','qc','implemented'),
 ('CALL_PEAKS',1110,425,'MACS3 peaks','Treatment + assigned control','peaks','implemented'),
 ('QUANTIFY',1330,425,'Quantify','Peak RPM + mean RPKM','peaks','implemented'),
 ('spp',1080,565,'SPP','Separate first-50-bp R1 alignment','spp','implemented'),
 ('TRACKS',1080,690,'deepTools tracks','Published BigWig signal','tracks','implemented'),
 ('reference',110,620,'Exact FASTA','User-supplied assembly','reference','implemented'),
 ('CHROM_SIZES',470,550,'Chromosome sizes','Verified reference products','reference','implemented'),
 ('BWA_MEM2_INDEX',680,690,'bwa-mem2 index','Verified reference products','reference','implemented')]
edges = [
 ('reads',[(110,300),(290,300)],'Sample sheet validation','implemented'),
 ('reference',[(110,620),(180,620),(180,380),(290,380),(290,300)],'Exact reference participates in validation','implemented'),
 ('reads',[(290,300),(480,300)],'Validated libraries are downloaded','implemented'),
 ('reference',[(290,300),(370,300),(370,550),(470,550)],'Build or verify chromosome sizes','implemented'),
 ('reference',[(290,300),(330,300),(330,690),(680,690)],'Build or verify FASTA index','implemented'),
 ('reference',[(470,550),(510,550),(510,690),(680,690)],'Reference length sizes indexing resources','implemented'),
 ('reads',[(480,300),(850,300)],'Unmodified downloaded reads feed alignment','implemented'),
 ('qc',[(480,300),(540,300),(540,185),(680,185)],'Raw-read QC runs in parallel','implemented'),
 ('reads',[(480,300),(510,300),(510,420),(680,420)],'Read metadata','implemented'),
 ('reference',[(470,550),(570,550),(570,420),(680,420)],'Chromosome sizes feed metadata','implemented'),
 ('reads',[(680,420),(770,420),(770,300),(850,300)],'Metadata accompanies full-read alignment','implemented'),
 ('reference',[(680,690),(850,690),(850,300)],'Verified index feeds alignment','implemented'),
 ('qc',[(680,185),(1320,185)],'FastQC ZIP reports','implemented'),
 ('qc',[(680,420),(735,420),(735,150),(1260,150),(1260,185),(1320,185)],'Metadata joins run-level reporting','implemented'),
 ('qc',[(850,300),(970,300),(970,245),(1080,245)],'Alignment metrics','implemented'),
 ('qc',[(1080,245),(1220,245),(1220,185),(1320,185)],'Native samtools metrics','implemented'),
 ('peaks',[(850,300),(940,300),(940,425),(1110,425)],'Treatments and their assigned controls','implemented'),
 ('peaks',[(1110,425),(1330,425)],'Treatment peaks','implemented'),
 ('reads',[(850,300),(1410,300),(1410,425),(1330,425)],'Primary treatment BAM supports quantification','implemented'),
 ('spp',[(850,300),(900,300),(900,565),(1080,565)],'Independent first-50-bp R1 alignment inside BWA_MEM2_ALIGN; SPP is published separately','implemented'),
 ('tracks',[(850,300),(930,300),(930,690),(1080,690)],'Full-read alignments feed coverage','implemented'),
 ('tracks',[(1080,690),(1330,690),(1330,425)],'RPKM coverage feeds quantification','implemented'),
 ('reference',[(470,550),(470,750),(1380,750),(1380,425),(1330,425)],'Chromosome sizes bound quantification','implemented')]
sections=[(48,460,'01  INPUTS & REFERENCE'),(535,365,'02  ALIGNMENT & METADATA'),(925,505,'03  QC, SIGNAL & QUANTIFICATION')]
notes=[
 'QC is diagnostic: FastQC warnings do not reject a dataset. MultiQC aggregates FastQC, samtools and Genesis metadata; SPP stays separate.',
 'Controls can serve multiple treatments. Controls receive QC and tracks; only treatments receive peaks and quantification.',
 'FASTQs and BAMs remain intermediate files. Reference products publish separately. Animated movement indicates dependencies, not runtime.']
OUT.mkdir(parents=True,exist_ok=True)
for animated,name in [(False,'genesis_metro_map.svg'),(True,'genesis_metro_map_animated.svg')]:
    (OUT/name).write_text(document('GENESIS / DAP-seq', 'Implemented validation workflow • explicit references • reproducible processing',nodes,edges,sections,notes,animated))

road_nodes=[
 ('manifest',150,220,'Sample manifest','Implemented • library/control IDs','reads','implemented'),
 ('reference_registry',450,220,'Reference registry','Tested schema • versioned identities','reference','planned'),
 ('acquisition',150,380,'Acquisition + QC','Implemented • raw reads retained','reads','implemented'),
 ('dap',530,370,'DAP-seq','Implemented • validated fixtures','reads','implemented'),
 ('dap_outputs',890,370,'Peaks + quantification','Implemented • per treatment','reads','implemented'),
 ('bulk_atac',530,490,'Bulk ATAC','Experimental • synthetic PE','future','planned'),
 ('bulk_outputs',890,490,'Fragments + ATAC QC','Experimental • known-answer QC','future','planned'),
 ('single_cell',530,610,'sc/snATAC','Planned • protocol-aware barcodes','future','planned'),
 ('cells',890,610,'Fragments + cell metadata','Specified • replicate boundaries','future','planned'),
 ('multiome',150,690,'Multiome identity','Tested contract • linked modalities','future','planned'),
 ('rna',530,715,'RNA modality','External route • separate QC','future','planned'),
 ('pseudobulk',1230,610,'Pseudobulks','Tested contract • type × replicate','future','planned'),
 ('models',1230,400,'Model-ready outputs','Specified • model-specific export','future','planned'),
 ('reports',1230,220,'QC + provenance','Implemented for DAP-seq','qc','implemented')]
road_edges=[
 ('reads',[(150,220),(150,380)],'Validated study/library inputs','implemented'),
 ('reference',[(150,220),(450,220)],'Registry resolves exact references','planned'),
 ('reads',[(150,380),(300,380),(300,370),(530,370)],'DAP-seq route','implemented'),
 ('reads',[(530,370),(890,370)],'Existing DAP-seq analysis','implemented'),
 ('qc',[(890,370),(1000,370),(1000,220),(1230,220)],'Existing run-level reporting','implemented'),
 ('future',[(150,380),(300,380),(300,490),(530,490)],'Experimental bulk ATAC route','planned'),
 ('future',[(530,490),(890,490)],'ATAC-specific processing','planned'),
 ('future',[(150,380),(270,380),(270,610),(530,610)],'Protocol-specific sc/snATAC','planned'),
 ('future',[(530,610),(890,610),(1230,610)],'Barcode-resolved fragments to replicate-specific pseudobulk','planned'),
 ('future',[(150,690),(330,690),(330,610),(530,610)],'Shared nucleus identity links ATAC','planned'),
 ('future',[(150,690),(330,690),(330,715),(530,715)],'Independent RNA modality','planned'),
 ('future',[(530,715),(890,715),(890,610)],'Annotation provenance joins barcode metadata','planned'),
 ('future',[(890,490),(1100,490),(1100,400),(1230,400)],'Bulk signal and reference metadata','planned'),
 ('future',[(1230,610),(1230,400)],'Replicate-specific pseudobulk model contract','planned'),
 ('reference',[(450,220),(450,370),(530,370)],'Registry identity feeds DAP-seq','planned'),
 ('reference',[(450,370),(450,490),(530,490)],'Registry identity feeds bulk ATAC','planned'),
 ('reference',[(450,490),(450,610),(530,610)],'Registry identity feeds scATAC','planned')]
road_notes=[
 'Solid routes: implemented in the validation branch. Dashed routes: experimental, specified or planned; no production readiness is implied.',
 'Biological replicates remain separate. Technical merges require explicit metadata. RNA and ATAC retain modality-specific QC and inclusion.',
 'Plant biological acceptance thresholds remain UNSPECIFIED. Exact Sorghum reference and the inventory workbook remain external prerequisites.']
(OUT/'genesis_architecture_metro_map.svg').write_text(document('GENESIS / ARCHITECTURE','Implementation status • assay-specific science • traceable model inputs',road_nodes,road_edges,[(48,350,'01  SHARED INFRASTRUCTURE'),(440,520,'02  ASSAY-SPECIFIC ROUTES'),(1030,400,'03  MODEL-FACING CONTRACTS')],road_notes,roadmap=True))
print('Rendered 3 Genesis SVG maps')
