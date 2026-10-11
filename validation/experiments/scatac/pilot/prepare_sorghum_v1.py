"""Author-label crosswalk for two biological batches; technical libraries stay explicit."""
from pathlib import Path
import collections,copy,csv,gzip,json
import pysam
from genesis_tools.contracts.records import load,dump,canonical
from genesis_tools.scatac.common import digest
root=Path('..').resolve();source=root/'results/scatac-completion/sources';out=root/'results/scatac-completion/sorghum';out.mkdir(exist_ok=True)
fasta=source/'Sbicolor_454_v3.0.1.fa.gz';annotation=source/'Sbicolor_454_v3.1.1.gene.gff3.gz'
with pysam.FastxFile(str(fasta)) as stream:sizes={r.name:len(r.sequence) for r in stream}
ref={'reference_id':'Sbicolor-v3.0.1-'+digest(fasta)[:12],'assembly':'Sorghum bicolor v3.0.1','species':'Sorghum bicolor','fasta':{'path':str(fasta),'sha256':digest(fasta)},'contigs':sizes,'mitochondrial_contigs':[],'plastid_contigs':[]}
points=set()
with gzip.open(annotation,'rt') as stream:
 for line in stream:
  if line.startswith('#'):continue
  f=line.rstrip().split('\t')
  if f[2]!='gene':continue
  pos=int(f[3])-1 if f[6]=='+' else int(f[4])-1
  assert f[0] in sizes and 0<=pos<sizes[f[0]] and f[6] in ['+','-'];points.add((f[0],pos,f[6]))
tss=out/'tss-gene-v3.1.1.tsv';tss.write_text(''.join(f'{c}\t{p}\t{s}\n' for c,p,s in sorted(points)))
metadata={r['barcode']:r for r in csv.DictReader((source/'GSE248919/sorghum_multiome_RNA_combined-cells.tsv').open(),delimiter='\t')}
labels={r['cell_id']:r['author_active_label'] for r in csv.DictReader((source/'GSE248919/active-labels.tsv').open(),delimiter='\t')}
maps={r['cell_id']:r['source_barcode'] for p in (source/'GSE248919').glob('barcode-map-*.tsv') for r in csv.DictReader(p.open(),delimiter='\t')}
selected={'Sorghum_Dark_2_RNA':('GSM7922845','SRX22683056','multiome-bio1','GEO replicate 1'),'Sorghum_Dark_1_Rep2_RNA':('GSM7922873','SRX22683080','multiome-bio2','GEO replicate 3')}
fixture=load(Path('validation/fixtures/pseudobulk/fixture.json'));counts=collections.Counter();unknown=collections.Counter();n=0
with (out/'cells.jsonl').open('w') as stream,(out/'author-membership.tsv').open('w') as mapping:
 writer=csv.writer(mapping,delimiter='\t');writer.writerow(['library_id','biological_replicate_id','author_treatment','author_cell_id','source_barcode','author_label','atac_include'])
 for author_id,row in metadata.items():
  if row['Treatment'] not in selected:continue
  gsm,experiment,rep,original=selected[row['Treatment']];label=labels[author_id];included=label!='unknown';n+=1
  cell=copy.deepcopy(fixture['cells'][0]);cell.update(library_id=gsm,barcode=maps[author_id],author_original_label=label,harmonized_label=label.replace('_',' '),annotation_source='GSE248919 author combined RData active.ident; C3-C4 Script 54',annotation_status='AUTHOR_RNA_LABEL; UNREVIEWED',atac_present=True,rna_present=True,atac_include=included,rna_include=False,cell_calling_status='author-retained nucleus',doublet_status='UNSPECIFIED')
  # nCount_ATAC is a peak-feature sum, not an independent fragment count.
  stream.write(canonical(cell)+'\n');writer.writerow([gsm,rep,row['Treatment'],author_id,maps[author_id],label,included])
  (counts if included else unknown)[(gsm,label)]+=1
for treatment,(gsm,experiment,rep,original) in selected.items():
 library={**fixture['libraries'][0],'study_id':'PRJNA1046450','biological_sample_id':f'GSE248919-dark-{rep}','biological_replicate_id':rep,'library_id':gsm,'species':'Sorghum bicolor','assembly':ref['assembly'],'reference_id':ref['reference_id'],'reference_fasta_sha256':ref['fasta']['sha256'],'annotation_sha256':digest(annotation),'accession_cultivar_ecotype':'BTx623','tissue':'shoot','developmental_stage':'GEO: 7-day-old; paper: 1 day imbibition plus 5 days dark growth (review required)','treatment':'0 h light; etiolated','condition':'dark before de-etiolation','assay':'multiome-ATAC','protocol':'10x Multiome v1.0','technical_merge_group':None}
 dump(out/(gsm+'-template.json'),{'schema_version':1,'library':library,'reference':ref,'source':{'author_treatment':treatment,'archive_experiment':experiment,'archive_replicate_label':original,'technical_libraries_selected_per_biological_replicate':1,'organellar_fraction':'UNAVAILABLE: exact nuclear reference has no declared organellar contigs'}})
policy={'schema_version':1,'version':'GSE248919-Chromap-sensitivity-v1','signal_convention':'chrombpnet-atac-v1','organellar':'retain','boundary_cuts':'exclude-and-report','independent_library_merges':[],'peak_calling':{'qvalue':0.01,'effective_genome_sizes':{ref['reference_id']:sum(sizes.values())}},'tss':{'path':str(tss),'sha256':digest(tss)},'experiment_label':'SENSITIVITY: explicit Chromap MAPQ30, cell-coordinate duplicate collapse with support, adapter trimming; MACS3 BEDPE; no production default changes'}
dump(out/'policy.json',policy);dump(out/'preparation.json',{'cells':n,'included':sum(counts.values()),'groups':{f'{g}:{label}':n for (g,label),n in counts.items()},'unknown_label_exclusions':{g:n for (g,_),n in unknown.items()},'reference':ref,'annotation_sha256':digest(annotation),'tss_method':'unique gene BED0 TSS; positive start-1, negative end-1; no contig renaming','biological_review':'UNREVIEWED','source_limits':['GEO age differs from paper growth description','only one of several technical libraries per biological batch selected','nuclear reference cannot measure organellar reads','author labels derived from RNA; RNA processing is outside this pilot']})
print(json.dumps({'cells':n,'included':sum(counts.values()),'groups':len(counts),'unknown':sum(unknown.values())}))
