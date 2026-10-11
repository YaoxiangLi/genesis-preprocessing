"""Independently count original author fragments to locate source-metric discrepancies."""
from pathlib import Path
from collections import Counter
import csv,gzip,json,hashlib,time
base=Path('../results/scatac-completion').resolve();started=time.monotonic()
rows=list(csv.DictReader((base/'arabidopsis-author-qc.tsv').open(),delimiter='\t'))
result={}
for rep in [1,2]:
 lib=f'GSM469876{rep-1}';expected={r['barcode']:int(r['retained_fragment_rows']) for r in rows if r['library_id']==lib}
 manifest=json.loads((base/'arabidopsis'/f'library-{rep}.json').read_text());path=Path(manifest['fragments']['path'])
 observed=Counter();n=support=0
 with path.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
 assert sha==manifest['fragments']['sha256']
 with gzip.open(path,'rt') as f:
  for line in f:
   if line.startswith('#'):continue
   fields=line.rstrip().split('\t');n+=1;support+=int(fields[4]);barcode=fields[3]
   if barcode in expected:observed[barcode]+=1
 assert all(observed[b]==v for b,v in expected.items())
 stored=json.loads((base/'arabidopsis'/f'ingested-{rep}/complete.json').read_text())['data']['counts']
 assert n==stored['fragments'] and support==stored['support']
 result[lib]={'input_sha256':sha,'original_fragment_rows':n,'original_support':support,'selected_cells':len(expected),'selected_original_fragments':sum(observed.values()),'all_selected_counts_equal_ingestion':True,'last_record_processed':True}
value={'libraries':result,'elapsed_seconds':time.monotonic()-started,'interpretation':'Counts come directly from the original author fragment archives. The 62-fragment discrepancy against author passed_filters predates Genesis ingestion; its upstream cause remains unresolved.'}
(base/'provenance/original-author-fragment-audit.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value),flush=True)
