"""Complete whole-library aggregation and products after atomic ingestion publication."""
from pathlib import Path
import json,subprocess,time
from genesis_tools.contracts.records import load,dump
from genesis_tools.scatac import pseudobulk,products
root=Path('../results/scatac-completion/arabidopsis').resolve()
deadline=time.monotonic()+4*3600
while not all((root/f'ingested-{i}/complete.json').exists() for i in [1,2]):
 if time.monotonic()>deadline:raise TimeoutError('Whole-library ingestion did not finish')
 time.sleep(10)
result=pseudobulk.aggregate([root/'ingested-1',root/'ingested-2'],root/'cells.jsonl',root/'policy.json',root/'core')
print(json.dumps({'stage':'core','result':result}),flush=True)
assert pseudobulk.aggregate([root/'ingested-1',root/'ingested-2'],root/'cells.jsonl',root/'policy.json',root/'core',resume=True)['cached']
groups=sorted(p for p in (root/'core').iterdir() if p.is_dir() and (p/'complete.json').is_file())
assert len(groups)==12
for group in groups:
 output=root/'products'/group.name
 result=products.run(group,output)
 assert products.run(group,output,resume=True)['cached']
 print(json.dumps({'stage':'products','task':group.name,'result':result}),flush=True)
print('PASS: both full Arabidopsis libraries; 12 separate groups; stable core/products resume',flush=True)
