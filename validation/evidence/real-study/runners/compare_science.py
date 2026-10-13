import csv, gzip, hashlib, json, shutil, sys
from pathlib import Path
from unittest.mock import patch
repo=Path('/var/tmp/genesis-study-MQ6B5glk/checkout')
sys.path.insert(0,str(repo/'tests'))
import verify_pipeline as v
candidate=repo/'tests/.runs/docker-3899qeba'
root=repo.parent/'science-comparison'
root.mkdir()
shutil.copytree(candidate/'inputs',root/'inputs')
(root/'references').mkdir()
for p in (candidate/'references').glob('*.fa.gz'): shutil.copy2(p,root/'references'/p.name)
shutil.copy2(candidate/'limits.config',root/'limits.config')
with v.serve(root/'inputs',docker=True) as url:
 rows=list(csv.DictReader((candidate/'samples.tsv').open(),delimiter='\t'))
 for row in rows:
  row['read1_url']=url+'/'+row['sample_id']+'/reads.fastq.gz'
  if row['read2_url']!='-': row['read2_url']=url+'/'+row['sample_id']+'/mate/reads.fastq.gz'
 sheet=root/'samples.tsv';v.write_sheet(sheet,rows)
 with patch.object(v,'ROOT',repo.parent/'baseline'):
  result=v.run_pipeline(root,sheet,docker=True)
 assert result.returncode==0,result.stdout[-4000:]
def scientific(folder):
 results={}
 for p in folder.rglob('*'):
  if p.is_file() and (p.suffix=='.bw' or p.name.endswith(('.narrowPeak.gz','.peaks.RPM.tsv','.peaks.mean_RPKM.tsv','.metadata.tsv','.qc.report.flagstat.txt','.qc.report.idxstats.tsv'))):
   raw=gzip.decompress(p.read_bytes()) if p.name.endswith('.narrowPeak.gz') else p.read_bytes()
   results[str(p.relative_to(folder))]=hashlib.sha256(raw).hexdigest()
 return results
baseline=scientific(root/'published/samples/output')
new=scientific(candidate/'published/samples/output')
assert len(baseline)==59,len(baseline)
assert baseline==new,{k:(v,new.get(k)) for k,v in baseline.items() if new.get(k)!=v}
record={'status':'PASS','baseline_revision':'36766e8887c2026030a4b0976c402ac834eded23','candidate_revision':'c36a275','compared_files':len(baseline),'method':'SHA256 of bigWigs, metadata, flagstat, idxstats and score TSVs; decompressed narrowPeak bytes','files':baseline}
(root/'comparison.json').write_text(json.dumps(record,indent=2)+'\n')
print('PASS: unchanged scientific products:',len(baseline),flush=True)
