"""Ingest explicit Chromap reconstructions and preserve biological replicate groups."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,subprocess,time,threading
from genesis_tools.contracts.records import dump,load
from genesis_tools.scatac import pseudobulk,products
from genesis_tools.scatac.common import digest

base=Path('../results/scatac-completion').resolve();root=base/'sorghum'
selected=[('GSM7922845','SRX22683056'),('GSM7922873','SRX22683080')];abort=threading.Event()
def prepare_ingest(item):
 gsm,srx=item;deadline=time.monotonic()+4*3600
 while not (base/'sorghum-runs/mapped'/srx/'mapping.json').is_file():
  if abort.is_set():raise RuntimeError('A peer library failed; stop waiting')
  if time.monotonic()>deadline:raise TimeoutError('Raw reconstruction required: '+srx)
  time.sleep(10)
 mapped=base/'sorghum-runs/mapped'/srx;receipt=load(mapped/'mapping.json')
 # Chromap writes --version to stderr. Preserve the original mapping receipt.
 version_result=subprocess.run([receipt['command'][0],'--version'],capture_output=True,text=True,check=True)
 version=(version_result.stdout+version_result.stderr).strip();assert version=='0.3.2-r518'
 version_receipt=mapped/'version-evidence.json'
 dump(version_receipt,{'command':[receipt['command'][0],'--version'],'stdout':version_result.stdout,'stderr':version_result.stderr,'version':version,'executable_sha256':digest(Path(receipt['command'][0])),'environment_lock_sha256':digest(Path('validation/environments/scatac-raw-pilot-linux-64.lock')),'original_version_capture':'empty stdout; version was emitted on stderr'})
 manifest=load(root/(gsm+'-template.json'))
 manifest.update(fragments={'path':str(mapped/'fragments.tsv'),'sha256':receipt['outputs']['fragments.tsv']},producer={'format':'chromap-atac','version':version,'offsets':[4,-5],'interval':'BED0-half-open','deduplication_scope':'library-barcode','barcode_correction':{'hamming_distance':1,'posterior_minimum':0.9,'translation':'paired ATAC-to-GEX whitelist; GEX suffix -1'},'whitelist_sha256':receipt['whitelist_sha256'],'mapq_min':30,'duplicates':'coordinate-collapsed-with-support','adapter_trimming':True,'maximum_fragment_length':2000,'barcode_read_format':'r1:0:-1,r2:0:-1,bc:8:23:-','barcode_translation_sha256':receipt['translation_sha256'],'command_sha256':receipt['command_sha256']})
 manifest['source'].update(mapping_receipt={'path':str(mapped/'mapping.json'),'sha256':digest(mapped/'mapping.json')},producer_version_receipt={'path':str(version_receipt),'sha256':digest(version_receipt)},sequencing_runs=receipt['runs'],experiment_label=receipt['experiment_label'])
 dump(root/(gsm+'.json'),manifest)
 command=['python3','../scratch/scatac-completion/record.py','sorghum-ingest-'+gsm+'-v3','--','/home/exouser/.pixi/bin/pixi','run','uv','run','--frozen','--project','genesis_tools','python','../scratch/scatac-completion/ingest_library.py',str(root/(gsm+'.json')),str(root/('ingested-'+gsm))]
 subprocess.run(command,check=True)
def ingest(item):
 try:prepare_ingest(item)
 except BaseException:
  abort.set();raise
with ThreadPoolExecutor(max_workers=2) as pool:
 list(pool.map(ingest,selected))
result=pseudobulk.aggregate([root/('ingested-'+g) for g,_ in selected],root/'cells.jsonl',root/'policy.json',root/'core',resume=True)
assert pseudobulk.aggregate([root/('ingested-'+g) for g,_ in selected],root/'cells.jsonl',root/'policy.json',root/'core',resume=True)['cached']
print(json.dumps({'stage':'core','result':result}),flush=True)
groups=sorted(p for p in (root/'core').iterdir() if p.is_dir() and (p/'complete.json').is_file());assert len(groups)==12
def process(group):
 output=root/'products'/group.name;result=products.run(group,output,resume=True)
 assert products.run(group,output,resume=True)['cached']
 print(json.dumps({'stage':'products','task':group.name,'result':result}),flush=True)
with ThreadPoolExecutor(max_workers=2) as pool:
 list(pool.map(process,groups))
print('PASS: two Sorghum biological replicates; 12 separate groups; stable resume',flush=True)
