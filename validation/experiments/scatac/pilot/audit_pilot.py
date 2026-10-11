"""Independent conservation audit from library barcode totals and source-cell membership."""
from pathlib import Path
from collections import Counter,defaultdict
import csv,json
from genesis_tools.contracts.records import dump,load

base=Path('../results/scatac-completion').resolve()
summary={};table=[];cells_table=[]
for species in ['arabidopsis','sorghum']:
 root=base/species
 cells={}
 with (root/'cells.jsonl').open() as stream:
  for line in stream:
   c=json.loads(line);key=(c['library_id'],c['barcode']);assert key not in cells;cells[key]=c
 expected=defaultdict(Counter);totals=Counter();missing=set(cells)
 for (lib,barcode),c in cells.items():
  if c['atac_include']:expected[(lib,c['harmonized_label'])]
 for marker in sorted(root.glob('ingested-*/complete.json')):
  data=load(marker)['data'];lib=data['input']['library']['library_id'];counts=data['counts']
  if species=='sorghum':
   native=load(base/'provenance/chromap-support-audit.json')[lib]['counts']
   assert native['fragments']==counts['fragments'] and native['reported_support']==counts['support']
  counts_seen=Counter()
  with (marker.parent/'barcodes.tsv').open() as stream:
   for row in csv.DictReader(stream,delimiter='\t'):
    key=(lib,row['barcode']);unique=int(row['unique_fragments']);support=int(row['support'])
    counts_seen['fragments']+=unique;counts_seen['support']+=support;counts_seen['barcodes']+=1
    c=cells.get(key)
    if c is None:
     totals['excluded_unannotated']+=unique;totals['excluded_unannotated_support']+=support
     continue
    missing.discard(key)
    if not c['atac_include']:
     totals['excluded_cell_policy']+=unique;totals['excluded_cell_policy_support']+=support
    else:
     e=expected[(lib,c['harmonized_label'])];e['fragments']+=unique;e['support']+=support
     totals['selected_fragments']+=unique;totals['selected_support']+=support
    cells_table.append({'species':species,'library_id':lib,'barcode':row['barcode'],'cell_type':c['harmonized_label'],'included':c['atac_include'],'unique_fragments':unique,'support':support,'support_redundancy_fraction':1-unique/support if support else None,'mitochondrial_fraction':int(row['mitochondrial_fragments'])/unique if species=='arabidopsis' and unique else None,'plastid_fraction':int(row['plastid_fragments'])/unique if species=='arabidopsis' and unique else None,'organellar_scope':'author-retained fragments, not original reads' if species=='arabidopsis' else 'UNAVAILABLE: no declared organellar reference contigs'})
  assert dict(counts_seen)=={k:counts[k] for k in ['fragments','support','barcodes']}
  totals['input_fragments']+=counts['fragments'];totals['input_support']+=counts['support']
 core=load(root/'core/complete.json')['data']
 for key,value in totals.items():assert core['counts'].get(key,0)==value,(species,key,value,core['counts'])
 assert totals['input_fragments']==sum(totals[k] for k in ['selected_fragments','excluded_unannotated','excluded_cell_policy'])
 assert totals['input_support']==sum(totals[k] for k in ['selected_support','excluded_unannotated_support','excluded_cell_policy_support'])
 total_groups=0;seen=set()
 for marker in sorted((root/'products').glob('*/complete.json')):
  data=load(marker)['data'];g=data['group'];bio=g['identity'];q=data['qc'];lib=next(iter(g['library_composition']));key=(lib,bio['cell_type']);seen.add(key)
  assert len(g['library_composition'])==1
  assert g['unique_fragments']==expected[key]['fragments']
  assert g['total_support']==expected[key]['support']
  assert g['cell_count']==sum(c['atac_include'] and c['harmonized_label']==bio['cell_type'] for (l,b),c in cells.items() if l==lib)
  assert g['cut_count']+g['excluded_boundary_cuts']==2*g['unique_fragments']
  assert q['denominator_fragments']==g['unique_fragments'] and q['total_support']==g['total_support']
  assert load(marker.parent/'bigwig-validation.json')['sum_counts']==g['cut_count']
  table.append({'species':species,'task_id':marker.parent.name,'library_id':lib,'biological_replicate':bio['biological_replicate_id'],'cell_type':bio['cell_type'],'cells':g['cell_count'],'unique_fragments':g['unique_fragments'],'support':g['total_support'],'cuts':g['cut_count'],'boundary_cuts_excluded':g['excluded_boundary_cuts'],'peaks':q['peak_count'],'frip':q['frip'],'tss_enrichment':q['tss_enrichment'],'support_redundancy_fraction':q['support_redundancy_fraction']})
  total_groups+=1
 assert total_groups==12 and seen==set(expected)
 summary[species]={'status':'PASS','groups':total_groups,'source_cells':len(cells),'included_cells':sum(c['atac_include'] for c in cells.values()),'missing_source_cell_barcodes':sorted([list(x) for x in missing]),'counts':dict(totals),'plant_thresholds':'UNSPECIFIED'}
 for lib,barcode in sorted(missing):
  c=cells[(lib,barcode)]
  cells_table.append({'species':species,'library_id':lib,'barcode':barcode,'cell_type':c['harmonized_label'],'included':c['atac_include'],'unique_fragments':0,'support':0,'support_redundancy_fraction':None,'mitochondrial_fraction':None,'plastid_fraction':None,'organellar_scope':'NO_OBSERVED_FRAGMENTS; source cell retained in membership'})
for name,rows in [('pseudobulk-qc.tsv',table),('cell-fragment-qc.tsv',cells_table)]:
 with (base/name).open('w') as stream:
  w=csv.DictWriter(stream,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)
dump(base/'independent-conservation.json',summary)
print(json.dumps(summary),flush=True)
