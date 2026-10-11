"""Run both actual pinned loaders for every completed real-pilot pseudobulk."""
from pathlib import Path
import argparse,json,time
from genesis_tools.contracts.records import dump,load
from genesis_tools.contracts.validation import Budget
from genesis_tools.scatac import model,loaders,registry,compare

p=argparse.ArgumentParser();p.add_argument('species',choices=['arabidopsis','sorghum']);a=p.parse_args()
base=Path('../results/scatac-completion').resolve();root=base/a.species
deadline=time.monotonic()+4*3600
while len(list((root/'products').glob('*/complete.json')))<12:
 if time.monotonic()>deadline:raise TimeoutError('Twelve complete products required')
 time.sleep(10)
folds=({'train':['1','2','3'],'validation':['4'],'test':['5']} if a.species=='arabidopsis' else {'train':[f'Chr{i:02}' for i in range(1,9)],'validation':['Chr09'],'test':['Chr10']})
items=[];pairs={}
for marker in sorted((root/'products').glob('*/complete.json')):
 group=marker.parent;metadata=load(marker)['data']['group'];task=group.name;models={}
 pairs.setdefault(metadata['identity']['cell_type'],[]).append(group)
 for target,sha in model.MODELS.items():
  config={'schema_version':1,'target':target,'model_sha':sha,'folds':folds,'input_window':2114,'output_window':1000,'max_jitter':0,'controls':None,'background_method':'gc-matched-genome-windows-v1','background_stride':1000,'background_seed':7,'experiment_label':'SENSITIVITY: model background windows with explicit 1000 bp stride; full positive contexts excluded; chromosome folds unchanged','bias_model':{'status':'REQUIRED_BEFORE_TRAINING','plant_model':None} if target=='chrombpnet' else None}
  config_path=root/'model-config'/f'{target}.json';dump(config_path,config)
  bundle=root/'models'/target/task;validation=root/'loader-validation'/target/task
  result=model.export(group,config_path,bundle,resume=True)
  assert model.export(group,config_path,bundle,resume=True)['cached']
  assert model.validate(bundle)['context_windows']=='PASS'
  result=loaders.run(bundle,Path('../benchmarks').resolve()/target,validation,resume=True)
  assert result['manifest']['data']['loader_test']=='PASS'
  assert loaders.run(bundle,Path('../benchmarks').resolve()/target,validation,resume=True)['cached']
  models[target]={'bundle':str(bundle),'validation':str(validation)}
  print(json.dumps({'stage':'model-loader','species':a.species,'task':task,'target':target,'status':'PASS'}),flush=True)
 catalog=base/'catalog'
 projected=registry.register(group,catalog,level='full',budget=Budget(max_bytes=20*1024**3,max_records=100_000_000,max_seconds=1800),bigwig_python=Path('validation/environments/scatac-loaders/.venv/bin/python').resolve())
 dump(root/'registry'/f'{task}.json',projected)
 assert projected['validation']['data']['complete']
 assert all(f['data']['result']=='PASS' for f in projected['validation']['data']['findings'])
 items.append({'products':str(group),'models':models})
for label,groups in pairs.items():
 assert len(groups)==2
 result=compare.run(*groups,width=1000)
 dump(root/'concordance'/f'{label}.json',result)
dump(root/'release-groups.json',items)
print(json.dumps({'species':a.species,'groups':len(items),'models':2*len(items),'comparisons':len(pairs),'status':'PASS'}),flush=True)
