from pathlib import Path
import csv,copy,gzip,collections,json
import pysam
from genesis_tools.contracts.records import load,dump,canonical
from genesis_tools.scatac.common import digest
root=Path('..').resolve();source=root/'results/scatac-pilot/sources/GSE155304';out=root/'results/scatac-completion/arabidopsis';out.mkdir(exist_ok=True)
ref_file=root/'results/scatac-completion/sources/GSE299784/Arabidopsis_thaliana.TAIR10.55.dna.toplevel.fa.gz'
# This TAIR10 assembly has numeric nuclear names matching the deposited fragments.
contigs={}
with pysam.FastxFile(str(ref_file)) as f:
 for r in f:contigs[r.name]=len(r.sequence)
annotation=root/'results/scatac-completion/sources/Araport11_GFF3_genes_transposons.201606.gff.gz'
anno_sha=digest(annotation);ref_sha=digest(ref_file)
ref={'reference_id':'TAIR10-EnsemblPlants55-'+ref_sha[:12],'assembly':'TAIR10','species':'Arabidopsis thaliana','fasta':{'path':str(ref_file),'sha256':ref_sha},'contigs':contigs,'mitochondrial_contigs':['Mt'],'plastid_contigs':['Pt']}
# Declared post-hoc QC annotation, not an assertion about the authors' unspecified Araport11 revision.
tss=out/'tss-gene-201606.tsv';alias={'Chr'+str(i):str(i) for i in range(1,6)};alias.update(ChrM='Mt',ChrC='Pt');points=set();excluded=collections.Counter()
with gzip.open(annotation,'rt') as f:
 for line in f:
  if line.startswith('#'):continue
  fields=line.strip().split('\t')
  if fields[2]!='gene':continue
  chrom=alias.get(fields[0],fields[0]);pos=int(fields[3])-1 if fields[6]=='+' else int(fields[4])-1
  if chrom not in contigs or pos>=contigs[chrom]:excluded[fields[0]]+=1;continue
  points.add((chrom,pos,fields[6]))
tss.write_text(''.join(f'{c}\t{p}\t{s}\n' for c,p,s in sorted(points)))
dump(out/'tss-provenance.json',{'source':str(annotation),'sha256':anno_sha,'method':'gene feature TSS; +:start-1, -:end-1; BED0; unique chrom/position/strand','explicit_contig_aliases':alias,'excluded_gene_features':dict(excluded),'experiment':'SENSITIVITY: explicit Araport11 201606 post-hoc QC; original annotation revision unknown'})
base=load(Path('validation/fixtures/pseudobulk/fixture.json'))['libraries'][0]
for rep in (1,2):
 lib={**base,'study_id':'PRJNA649267','biological_sample_id':f'GSE155304-root-{rep}','biological_replicate_id':f'root-rep{rep}','library_id':f'GSM469876{rep-1}','species':'Arabidopsis thaliana','assembly':'TAIR10','reference_id':ref['reference_id'],'reference_fasta_sha256':ref_sha,'annotation_sha256':anno_sha,'accession_cultivar_ecotype':'Col-0','tissue':'root','developmental_stage':'7 days after germination','condition':'16h light / 8h dark','assay':'snATAC','protocol':'10x Chromium Single Cell ATAC','technical_merge_group':None}
 frag=source/f'extracted/sNucATAC-seq_rep{rep}/fragments.tsv.gz'
 value={'schema_version':1,'library':lib,'reference':ref,'fragments':{'path':str(frag),'sha256':digest(frag)},'producer':{'format':'10x-atac','version':'Cell Ranger ATAC 1.2.0','offsets':[4,-5],'interval':'BED0-half-open','deduplication_scope':'library-barcode','barcode_correction':'Author Cell Ranger ATAC; exact whitelist unavailable','whitelist_sha256':None}}
 dump(out/f'library-{rep}.json',value)
classes={n:label for label,ns in [('trichoblast',range(1,4)),('atrichoblast',range(4,8)),('meristematic cell',range(8,11)),('cortical cell',range(11,13)),('endodermal cell',range(13,17)),('stele cell',range(17,22))] for n in ns}
rows=list(csv.DictReader((source/'author-cells.tsv').open(),delimiter='\t'));counts=collections.Counter()
with (out/'cells.jsonl').open('w') as f:
 for row in rows:
  rep=1 if row['lib']=='g10' else 2;assert row['lib'] in ['g10','n5'];barcode=row['barcode'];barcode=barcode[2:] if rep==1 else barcode
  cluster=int(row['seurat_clusters_renamed']);assert row['predicted.id'].rsplit('_',1)[-1]==str(cluster)
  cell=copy.deepcopy(load(Path('validation/fixtures/pseudobulk/fixture.json'))['cells'][0]);cell.update(library_id=f'GSM469876{rep-1}',barcode=barcode,author_original_label=str(cluster),harmonized_label=classes[cluster],annotation_source='Farmer et al. 2021 Fig.3C; GEO GSE155304 atacseq_integration.rds seurat_clusters_renamed',annotation_status='AUTHOR_LABEL_TRANSFER; UNREVIEWED',cell_calling_status='author-retained',doublet_status='UNSPECIFIED')
  total=int(row['total']);cell['qc_metrics'].update(unique_fragments=int(row['passed_filters']),duplicate_fraction=int(row['duplicate'])/total,mitochondrial_fraction=int(row['mitochondrial'])/total,low_mapq_fraction=int(row['lowmapq'])/total,frip=int(row['peak_region_fragments'])/int(row['passed_filters']))
  f.write(canonical(cell)+'\n');counts[(rep,classes[cluster])]+=1
policy={'schema_version':1,'version':'GSE155304-pilot-v1','signal_convention':'chrombpnet-atac-v1','organellar':'retain','boundary_cuts':'exclude-and-report','independent_library_merges':[],'peak_calling':{'qvalue':0.01,'effective_genome_sizes':{ref['reference_id']:sum(contigs[str(i)] for i in range(1,6))}},'tss':{'path':str(tss),'sha256':digest(tss)},'experiment_label':'SENSITIVITY: replicate-specific MACS3 peaks and explicit Araport11-201606 TSS; no raw read reprocessing'}
dump(out/'policy.json',policy);dump(out/'preparation.json',{'counts':{f'{r}:{c}':n for (r,c),n in counts.items()},'cells':len(rows),'reference':ref,'annotation_original_revision':'UNSPECIFIED','author_cluster_mapping':classes,'excluded_tss_features':dict(excluded),'biological_review':'UNREVIEWED'})
print(json.dumps({'cells':len(rows),'groups':len(counts),'counts':{f'{r}:{c}':n for (r,c),n in counts.items()},'reference':ref},indent=2))
