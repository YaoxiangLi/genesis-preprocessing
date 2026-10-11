"""Read copied release bundles through both pinned model loaders without source paths."""
from pathlib import Path
import json,time
from genesis_tools.contracts.records import dump,load
from genesis_tools.scatac import loaders,model
from genesis_tools.scatac.common import verify_output

base=Path('../results/scatac-completion').resolve()
release=base/'genesis-scatac-pilot-v1'
deadline=time.monotonic()+3*3600
while not (base/'release-acceptance.json').is_file():
    if time.monotonic()>deadline:
        raise TimeoutError('Complete pilot release required')
    time.sleep(10)
manifest=verify_output(release,'scatac-release')
assert manifest['data']['groups']==24
assert not manifest['data']['model_ready']
groups=json.loads((release/'manifest/groups.json').read_text())
results=[]
for species in ['Arabidopsis thaliana','Sorghum bicolor']:
    chosen=sorted([g for g in groups if g['identity']['species']==species],key=lambda g:g['id'])[0]
    for target in ['cherimoya','chrombpnet']:
        bundle=release/'models'/target/chosen['id']
        assert model.validate(bundle)['context_windows']=='PASS'
        output=base/'portable-loader-validation'/target/chosen['id']
        evidence=loaders.run(bundle,Path('../benchmarks').resolve()/target,output,resume=True)
        assert evidence['manifest']['data']['loader_test']=='PASS'
        assert loaders.run(bundle,Path('../benchmarks').resolve()/target,output,resume=True)['cached']
        results.append({'species':species,'target':target,'group':chosen['id'],
                        'bundle':str(bundle.relative_to(release)),
                        'loader_version':evidence['manifest']['version'],
                        'evidence':evidence['manifest']['data']['evidence'],'status':'PASS'})
        print(json.dumps(results[-1]),flush=True)
dump(base/'portable-release-acceptance.json',{'status':'PASS','release_version':manifest['version'],
     'relocated_loader_tests':results,'training':'NOT_RUN','scientific_review':'UNREVIEWED'})
