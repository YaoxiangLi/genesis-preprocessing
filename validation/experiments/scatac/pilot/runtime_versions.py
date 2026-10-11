"""Record selected public software identity without reading environment credentials."""
from pathlib import Path
import json,platform,subprocess
from genesis_tools.scatac.products import IMAGES
from genesis_tools.scatac.loaders import CHROMBPNET_IMAGE
import pysam

repo=Path.cwd();workspace=repo.parent;pixi='/home/exouser/.pixi/bin/pixi'
commands={'pixi':[pixi,'--version'],'uv':[pixi,'run','uv','--version'],'micromamba':[pixi,'run','micromamba','--version'],'nextflow':[pixi,'run','nextflow','-version'],'java':[pixi,'run','java','-version'],'docker':['docker','version','--format','{{.Client.Version}} {{.Server.Version}} {{.Server.Arch}}'],'chromap':[str(workspace/'scratch/scatac-completion/raw-env/bin/chromap'),'--version'],'fasterq_dump':[str(workspace/'scratch/scatac-completion/raw-env/bin/fasterq-dump'),'--version'],'pigz':['pigz','--version']}
out={'python':platform.python_version(),'pysam':pysam.__version__,'architecture':platform.machine(),'git_sha':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'software':{},'images':{}}
for name,cmd in commands.items():
 result=subprocess.run(cmd,capture_output=True,text=True,check=False);assert result.returncode==0,(name,result.returncode)
 out['software'][name]={'argv':cmd,'stdout':result.stdout,'stderr':result.stderr}
for image in [*IMAGES.values(),CHROMBPNET_IMAGE,'kundajelab/dap_seq_qc@sha256:ace177a497934a26adb305bc0dc92cc6a447fe8ca714b79f72a007c7acb53239']:
 data=json.loads(subprocess.check_output(['docker','image','inspect',image],text=True))[0]
 out['images'][image]={'architecture':data['Architecture'],'os':data['Os'],'id':data['Id'],'repo_digests':data['RepoDigests']}
(workspace/'results/scatac-completion/provenance/runtime-versions.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'status':'PASS','tools':len(commands),'images':len(out['images'])}))
