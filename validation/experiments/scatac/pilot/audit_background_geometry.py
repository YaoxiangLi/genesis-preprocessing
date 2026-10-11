"""Measure candidate-window supply before choosing a model background experiment."""
from pathlib import Path
from collections import Counter
import json,time,hashlib
base=Path('../results/scatac-completion').resolve();rows=[];radius=1057
for p in sorted((base/'arabidopsis/products').glob('*/complete.json')):
 value=json.loads(p.read_text())['data'];g=value['group'];sizes=g['reference']['contigs'];folds={**{str(i):'train' for i in [1,2,3]},'4':'validation','5':'test'};regions={};positives=Counter()
 for line in (p.parent/'peaks_peaks.narrowPeak').read_text().splitlines():
  f=line.split('\t');c=f[0];start,end,center=int(f[1]),int(f[2]),int(f[1])+int(f[9])
  regions.setdefault(c,[]).append((min(start,center-radius),max(end,center+radius)))
  if c in folds and center-radius>=0 and center+radius<=sizes[c]:positives[folds[c]]+=1
 for stride in [2114,1000]:
  available=Counter()
  for c,fold in folds.items():
   intervals=sorted(regions.get(c,[]));cursor=0
   for center in range(radius,sizes[c]-radius+1,stride):
    left,right=center-radius,center+radius
    while cursor<len(intervals) and intervals[cursor][1]<=left:cursor+=1
    if cursor<len(intervals) and intervals[cursor][0]<right:continue
    available[fold]+=1
  rows.append({'task':p.parent.name,'cell_type':g['identity']['cell_type'],'replicate':g['identity']['biological_replicate_id'],'stride':stride,'positives':dict(positives),'candidates':dict(available),'one_to_one_possible':all(available[f]>=positives[f] for f in positives),'peak_sha256':value and json.loads(p.read_text())['outputs']['peaks_peaks.narrowPeak']})
value={'window':2*radius,'rows':rows,'method':'full positive context exclusion; chromosome-disjoint folds; within-fold candidate windows may overlap when stride < window','reference_method':'Pinned ChromBPNet get_genomewide_gc_bins.py defaults inputlen=2114, stride=1000; this does not declare a plant QC threshold'}
(base/'provenance/background-geometry.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({'groups':len(rows)//2,'one_to_one_possible_at_2114':sum(x['one_to_one_possible'] for x in rows if x['stride']==2114),'one_to_one_possible_at_1000':sum(x['one_to_one_possible'] for x in rows if x['stride']==1000)}))
