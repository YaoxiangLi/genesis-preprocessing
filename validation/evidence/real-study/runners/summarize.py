import collections, csv, gzip, hashlib, json, platform, shutil, subprocess, sys
from pathlib import Path
base=Path('/var/tmp/genesis-study-MQ6B5glk');repo=base/'checkout';out=base/'evidence'
def load(p):return json.loads(p.read_text())
def dump(name,data):(out/name).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tail_fixture(log,prefix):
 for line in log.read_text().splitlines():
  if line.startswith(prefix):return Path(line.removeprefix(prefix))
 raise ValueError(log)
study=tail_fixture(out/'real-study.log','Real study acceptance evidence: ')
assert load(study/'result.json')['status']=='PASS'
shutil.copy2(study/'result.json',out/'study-result.json')
commands=load(study/'commands.json')['commands']
for c in commands:
 for f in ('stdout','stderr'): c[f+'_sha256']=digest(study/c[f])
dump('study-commands.json',{'commands':commands})
summary={}
for tag in ('dap','atac'):
 result=load(study/(tag+'-result.json')); jobs=result.pop('jobs');details=[]
 for jobid,j in jobs.items():
  root=Path(j['root'])
  trace=next((root/'trace').glob('execution_trace_*.txt')) if tag=='dap' else root/'output/trace.tsv'
  rows=list(csv.DictReader(trace.open(),delimiter='\t'))
  shutil.copy2(trace,out/(tag+'-'+jobid+'-trace.tsv'))
  owned=list((root.parent.parent.parent/'attempts').glob('*'+jobid+'-1/status.json'))
  details.append({'job_id':jobid,'names':j['names'],'run_root':str(root),
                  'trace_rows':len(rows),'trace_status':dict(collections.Counter(r['status'] for r in rows)),
                  'trace_sha256':digest(trace), 'task_runtime_measurements':'See raw trace; task peak RSS, not whole-host memory'})
  if tag=='dap':
   p=root/'output/provenance/dap-run.json';d=load(p)
   details[-1]['provenance']={'sha256':digest(p),'schema_version':d['schema_version'],
    'git_sha':d['context']['git_sha'],'source_status':d['context']['source_status'],
    'inputs':len(d['inputs']),'outputs':len(d['outputs']),'tasks':len(d['tasks']),
    'engines':sorted({t['engine'] for t in d['tasks']}),'observed_resources':None}
 exports={}
 for p in sorted((study/(tag+'-study')).glob('export-*.json')):
  v=load(p);exports[p.stem]={'sha256':digest(p),'denominators':v['denominators']}
 result.update(jobs=details,exports=exports)
 summary[tag]=result
dump('study-summary.json',summary)
# Exact science comparison to the prior lab release; exclude provenance/report presentation.
dap=tail_fixture(out/'real-dap.log','Running Docker tools (run) in ')
original=load(base/'science-comparison/comparison.json')['files']
current={}
for rel in original:
 p=dap/'published/samples/output'/rel
 raw=gzip.decompress(p.read_bytes()) if rel.endswith('.narrowPeak.gz') else p.read_bytes()
 current[rel]=hashlib.sha256(raw).hexdigest()
assert current==original
comp=load(base/'science-comparison/comparison.json');comp['candidate_revision']=load(out/'real-dap.json')['source_revision'];comp['candidate_fixture']=str(dap)
dump('scientific-invariance.json',comp)
for suffix in ('run','resume','stable'):
 shutil.copy2(dap/('trace-'+suffix+'.tsv'),out/('dap-'+suffix+'-trace.tsv'))
shutil.copy2(base/'science-comparison/trace-run.tsv',out/'dap-baseline-trace.tsv')
counts={s:dict(collections.Counter(r['status'] for r in csv.DictReader((dap/('trace-'+s+'.tsv')).open(),delimiter='\t'))) for s in ('run','resume','stable')}
dump('dap-summary.json',{'trace_counts':counts,'scientific_products_equal':len(original),'baseline_revision':comp['baseline_revision'],'candidate_revision':comp['candidate_revision']})
atac=tail_fixture(out/'real-atac.log','ATAC regression evidence: ')
for p in atac.glob('*-trace.tsv'):shutil.copy2(p,out/('atac-'+p.name))
# Report exact dependency/image identities; include only approved public container references.
images=set(load(repo/'conf/atac-images.json').values())
images.update(l.split('=',1)[1] for l in (repo/'.env').read_text().splitlines() if '_IMAGE=' in l)
image_records=[]
for image in sorted(images):
 d=json.loads(subprocess.check_output(['docker','image','inspect',image],text=True))[0]
 image_records.append({'reference':image,'id':d['Id'],'architecture':d['Architecture'],'os':d['Os']})
dump('environment.json',{'python':sys.version,'platform':platform.platform(),'images':image_records,'pyBigWig':subprocess.check_output(['/tmp/genesis-bigwig-env/bin/python','-c','import pyBigWig; print(pyBigWig.__version__)'],text=True).strip(),'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),'scope':'tiny synthetic fixtures on local workers; no live SSH/API/GPU/public biological acceptance'})
print('PASS: compact evidence, exports, traces, resources and 59 unchanged science products')
