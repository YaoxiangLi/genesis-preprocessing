"""Translate audited ARC barcodes; measure orientation and author-cell concordance."""
from pathlib import Path
import collections,csv,gzip,hashlib,json
root=Path('../results/scatac-completion').resolve();source=root/'sources';w=source/'whitelists'
atac=gzip.open(w/'737K-arc-v1(ATAC).txt.gz','rt').read().splitlines()
gex=gzip.open(w/'737K-arc-v1(GEX).txt.gz','rt').read().splitlines()
assert len(atac)==len(gex)==len(set(atac))==len(set(gex))==736320
translation=dict(zip(atac,[b+'-1' for b in gex],strict=True));wl=set(atac)
(w/'ATAC-to-GEX.tsv').write_text(''.join(f'{g}\t{a}\n' for a,g in translation.items()))
(w/'ATAC-whitelist.txt').write_text('\n'.join(atac)+'\n')
cells={r['barcode']:r for r in csv.DictReader((source/'GSE248919/sorghum_multiome_RNA_combined-cells.tsv').open(),delimiter='\t')}
maps={}
for path in sorted((source/'GSE248919').glob('barcode-map-*.tsv')):
 rows=list(csv.DictReader(path.open(),delimiter='\t'));treatments={cells[r['cell_id']]['Treatment'] for r in rows}
 assert len(treatments)==1;name=treatments.pop();maps[name]={r['source_barcode'] for r in rows}
 assert maps[name]<=set(translation.values())
complement=str.maketrans('ACGTN','TGCAN')
def rc(s):return s.translate(complement)[::-1]
results={}
folders=list((root/'sorghum-runs/fastq').glob('SRR*'))+[root/'sra-preview']
for folder in folders:
 paths=sorted(folder.glob('*_3.fastq.gz'))
 for path in paths:
  accession=path.name.split('_')[0];counts=collections.Counter();bc=collections.Counter();n=0
  with gzip.open(path,'rt') as stream:
   for _ in range(10000):
    h=stream.readline();seq=stream.readline().strip();plus=stream.readline();quality=stream.readline().strip()
    if not h:break
    assert len(seq)==len(quality)==24 and h.startswith('@') and plus.startswith('+');n+=1
    for name,candidate in [('first16',seq[:16]),('last16',seq[8:]),('rc_first16',rc(seq[:16])),('rc_last16',rc(seq[8:]))]:counts[name]+=candidate in wl
    if rc(seq[8:]) in translation:bc[translation[rc(seq[8:])]]+=1
  assert counts['rc_last16']==max(counts.values()) and counts['rc_last16']>0
  results[accession]={'preview_spots':n,'orientation_exact_matches':dict(counts),'author_library_matching_spots':{name:sum(bc[b] for b in barcodes) for name,barcodes in maps.items()},'read_format':'r1:0:-1,r2:0:-1,bc:8:23:-'}
summary={'protocol':'10x Multiome ARC; paired whitelist line order retained','references':['https://www.10xgenomics.com/support/software/cell-ranger-arc/latest/analysis/atac-barcoded-bam','https://scg-lib-structs.readthedocs.io/en/latest/multi/10x_multiome.html'],'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in w.iterdir() if p.suffix in {'.gz','.tsv','.txt'}},'previews':results}
(root/'sorghum-runs/barcode-provenance.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
