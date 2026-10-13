from pathlib import Path
import datetime,hashlib,json,os,shutil,subprocess,time
ROOT=Path('/var/tmp/genesis-installed-package-fix-20261013')
LIVE=Path('/data/homes/yl814/package/genesis/genesis-preprocessing')
BASE=LIVE/'results/method-benchmark-20261013'
OUT=Path('/tmp/genesis-wheel-release-20261013')
PY=str(OUT/'venv/bin/python');CLI=str(OUT/'venv/bin/genesis')
ENV=dict(os.environ);ENV.pop('GENESIS_REPO',None);ENV.pop('PYTHONPATH',None)
ENV['PATH']='/tmp/genesis-tooling/bin:'+ENV['PATH']
RECORDS=json.loads((BASE/'installed-wheel-release-progress.json').read_text())

def run(name,argv,expected=0,configured=False):
    for record in RECORDS:
        if record['name']==name and record['argv']==argv and record['exit']==expected:
            return (OUT/f'{name}.stdout').read_text()
    env=dict(ENV)
    if configured:env['GENESIS_REPO']=str(ROOT)
    start=time.monotonic();utc=datetime.datetime.now(datetime.UTC).isoformat()
    r=subprocess.run(argv,cwd=OUT,env=env,text=True,capture_output=True)
    for stream,data in [('stdout',r.stdout),('stderr',r.stderr)]:
        (OUT/f'{name}.{stream}').write_text(data)
    RECORDS.append({'name':name,'argv':argv,'utc':utc,'seconds':time.monotonic()-start,'expected_exit':expected,'exit':r.returncode,'configured_checkout':configured,'stdout_sha256':hashlib.sha256(r.stdout.encode()).hexdigest(),'stderr_sha256':hashlib.sha256(r.stderr.encode()).hexdigest()})
    (BASE/'installed-wheel-release-progress.json').write_text(json.dumps(RECORDS,indent=2)+'\n')
    if r.returncode!=expected:raise RuntimeError(name+': '+r.stderr[-3000:])
    print(name,r.returncode,flush=True)
    return r.stdout

run('cli-help',[CLI,'--help'])
run('benchmark-help',[CLI,'benchmark','--help'])
run('missing-checkout-help',[CLI,'pipeline','--help'],expected=2)
run('missing-checkout-run',[CLI,'pipeline','missing.tsv'],expected=2)
run('core-registry',[CLI,'registry','init',str(OUT/'standalone-catalog')])
run('configured-plan',[CLI,'benchmark','plan',str(BASE/'synthetic-dap-v5-inputs/production-baseline.json')],configured=True)
run('installed-fixture',[PY,'-m','genesis_tools.benchmark','fixture','--adapter','methods','--checkout',str(LIVE),'--out',str(OUT/'fixture')])
plan=json.loads(run('installed-plan',[PY,'-m','genesis_tools.benchmark','plan',str(OUT/'fixture/experiment.json')]))
assert plan['status']=='READY'
assert plan['source']['source_kind']=='installed-package' and plan['source']['git_sha'] is None
if not (OUT/'report').exists():shutil.copytree(BASE/'synthetic-dap-v5-results',OUT/'report')
run('installed-report',[PY,'-m','genesis_tools.benchmark','report',str(OUT/'report')])
if not (OUT/'tutorial').exists():shutil.copytree(ROOT/'examples/curation',OUT/'tutorial')
run('offline-tutorial',[PY,str(OUT/'tutorial/offline_workflow.py'),str(OUT/'tutorial-results')])
summary=json.loads((OUT/'tutorial-results/acceptance.json').read_text())
assert summary['status']=='PASS' and summary['denominators']['included']==2 and summary['decisions']==6
code="""from pathlib import Path
import json
import genesis_tools
from importlib.resources import files
p=Path(genesis_tools.__file__).resolve()
assert 'site-packages' in p.parts
names=['benchmark/report.html','contracts/schemas/records-v1.json','contracts/schemas/records-v4.json','llm/schemas/metadata-proposal-v1.json']
all_files=[]
for subtree in ['contracts/schemas','llm/schemas','llm/prompts','qc_policy/policies','curation/vocabularies']:
 root=files('genesis_tools').joinpath(subtree)
 assert root.is_dir(),subtree
 all_files += [subtree+'/'+x.name for x in root.iterdir() if x.is_file()]
assert files('genesis_tools').joinpath('benchmark/report.html').is_file()
print(json.dumps({'package':str(p),'packaged_files':all_files}))
"""
assets=json.loads(run('packaged-assets',[PY,'-c',code]))
wheel=OUT/'wheels/genesis_tools-0.1.0-py3-none-any.whl'
result={'status':'PASS','source_commit':subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),'cwd':str(OUT),'wheel_sha256':hashlib.sha256(wheel.read_bytes()).hexdigest(),'commands':RECORDS,'assets':assets,'installed_source':plan['source'],'offline_tutorial':summary,'scope':'Fresh installed wheel outside the checkout, no editable source or PYTHONPATH. Direct CLI routing/core commands, packaged benchmark fixture/plan/report and complete offline curation tutorial. No scientific workflow rerun.'}
(BASE/'installed-wheel-release.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS',len(RECORDS),'commands',flush=True)
