"""Count producer support saturation without changing fragments or inferred molecule counts."""
from pathlib import Path
from collections import Counter,defaultdict
import json,time

base=Path('../results/scatac-completion');cells={(c['library_id'],c['barcode']):c for c in map(json.loads,(base/'sorghum/cells.jsonl').read_text().splitlines())}
results={}
for gsm,srx in [('GSM7922845','SRX22683056'),('GSM7922873','SRX22683080')]:
 directory=base/'sorghum-runs/mapped'/srx;deadline=time.monotonic()+4*3600
 while not (directory/'mapping.json').is_file():
  if time.monotonic()>deadline:raise TimeoutError(srx)
  time.sleep(10)
 start=time.monotonic();all_rows=Counter();selected=defaultdict(Counter)
 with (directory/'fragments.tsv').open() as stream:
  for line in stream:
   f=line.rstrip().split('\t');assert len(f)==5;support=int(f[4]);assert 1<=support<=255
   all_rows['fragments']+=1;all_rows['reported_support']+=support;all_rows['rows_at_255']+=support==255
   c=cells.get((gsm,f[3]))
   if c is not None:
    group=selected[c['harmonized_label']];group['fragments']+=1;group['reported_support']+=support;group['rows_at_255']+=support==255
 results[gsm]={'experiment':srx,'elapsed_seconds':time.monotonic()-start,'support_cap':255,'counts':dict(all_rows),'author_groups':{k:dict(v) for k,v in selected.items()},'interpretation':'Counts equal producer-reported support. Rows at 255 may be truncated; exact lost support is not recoverable from fragments. Unique fragments and unweighted cut counts are unaffected.','redundancy_fraction':'lower bound where support was capped','chromap_source_sha':'5bd17e1f1c50805e76904efd021603cb6a1b6e23','source_locations':['src/mapping_processor.h:184','src/mapping_writer.h:420']}
 print(json.dumps({gsm:results[gsm]}),flush=True)
 (base/'provenance/chromap-support-audit.json').write_text(json.dumps(results,indent=2)+'\n')
