"""Assemble the two-species candidate only after every actual model loader passes."""
from pathlib import Path
import json,subprocess,time
from genesis_tools.contracts.records import dump,load
from genesis_tools.scatac import release
from genesis_tools.scatac.common import digest,verify_output

base=Path('../results/scatac-completion').resolve();deadline=time.monotonic()+6*3600
while not all((base/s/'release-groups.json').is_file() for s in ['arabidopsis','sorghum']):
 if time.monotonic()>deadline:raise TimeoutError('Both species must finish all model loaders')
 time.sleep(10)
subprocess.run(['python3','../scratch/scatac-completion/record.py','independent-real-pilot-conservation','--','/home/exouser/.pixi/bin/pixi','run','uv','run','--frozen','--project','genesis_tools','python','../scratch/scatac-completion/audit_pilot.py'],check=True)
groups=[];libraries={};evidence={}
def include(name,path):
 assert name not in evidence
 evidence[name]={'path':str(path.resolve()),'sha256':digest(path)}
for species in ['arabidopsis','sorghum']:
 root=base/species;groups.extend(json.loads((root/'release-groups.json').read_text()))
 for p in root.glob('ingested-*/complete.json'):
  library=load(p)['data']['input']['library']['library_id'];assert library not in libraries;libraries[library]=str(p.parent)
 for name in ['cells.jsonl','policy.json','preparation.json']:
  include(species+'-'+name,root/name)
 for p in sorted((root/'concordance').glob('*.json')):
  include(species+'-concordance-'+p.name.replace(' ','_'),p)
for name in ['independent-conservation.json','pseudobulk-qc.tsv','cell-fragment-qc.tsv','selected-identities.json']:
 include(name,base/name)
for p in sorted((base/'provenance').glob('*.json')):include(p.name,p)
include('MODEL_HANDOFF.md',Path('docs/usage/scatac-model-handoff.md'))
for p in sorted((base/'inventory-tables').glob('*.tsv')):include(p.name,p)
include('arabidopsis-author-qc.tsv',base/'arabidopsis-author-qc.tsv')
for name in ['acquisition.json','download-summary.json','barcode-provenance.json']:
 include('sorghum-'+name,base/'sorghum-runs'/name)
for p in sorted((base/'sorghum-runs/fastq').glob('*/extraction.json')):include(p.parent.name+'-extraction.json',p)
for p in sorted((base/'sorghum-runs/mapped').glob('*/mapping.json')):include(p.parent.name+'-mapping.json',p)
config={'schema_version':1,'required_species':['Arabidopsis thaliana','Sorghum bicolor'],'libraries':libraries,'source_evidence':evidence,'handoff_document':'provenance/sources/MODEL_HANDOFF.md','groups':groups}
dump(base/'release.json',config)
result=release.run(base/'release.json',base/'catalog',base/'genesis-scatac-pilot-v1')
assert result['data']['groups']==24 and not result['data']['release_issues']
assert not result['data']['model_ready']  # Human decisions are not inferred from software success.
verify_output(base/'genesis-scatac-pilot-v1','scatac-release')
dump(base/'release-acceptance.json',{'computational_acceptance':'PASS','groups':24,'actual_model_loader_tests':48,'biological_review':'UNREVIEWED','training':'NOT_RUN','release':result['version']})
print(json.dumps(result['data']),flush=True)
