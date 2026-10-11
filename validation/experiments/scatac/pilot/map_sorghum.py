"""Explicit raw-read sensitivity reconstruction; no production defaults are changed."""
from pathlib import Path
import argparse,hashlib,json,resource,subprocess,time
p=argparse.ArgumentParser();p.add_argument('experiment',choices=['SRX22683056','SRX22683080']);a=p.parse_args()
root=Path('../results/scatac-completion').resolve();base=root/'sorghum-runs'
runs=sorted(r['run_accession'] for r in json.loads((base/'acquisition.json').read_text())['runs'] if r['experiment_accession']==a.experiment)
assert len(runs)==(4 if a.experiment=='SRX22683056' else 1)
out=base/'mapped'/a.experiment;out.mkdir(parents=True,exist_ok=False)
def sha(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
files={i:[base/'fastq'/r/f'{r}_{i}.fastq.gz' for r in runs] for i in [2,3,4]}
for r in runs:
 receipt=json.loads((base/'fastq'/r/'extraction.json').read_text())
 for path in (base/'fastq'/r).glob('*.fastq.gz'):assert sha(path)==receipt['outputs'][path.name]['sha256']
reference=root/'sources/Sbicolor_454_v3.0.1.fa.gz';index=base/'Sbicolor_454_v3.0.1.chromap.index'
assert sha(reference)=='8683530943438cee02ca14340010b2b897b4dcff45238dd8efeabb604c7c3936'
whitelist=root/'sources/whitelists/ATAC-whitelist.txt';translation=root/'sources/whitelists/ATAC-to-GEX.tsv'
binary=Path('../scratch/scatac-completion/raw-env/bin/chromap').absolute()
command=[str(binary),'--preset','atac','-r',str(reference),'-x',str(index),'-1',','.join(map(str,files[2])),'-2',','.join(map(str,files[4])),'-b',','.join(map(str,files[3])),
 '--read-format','r1:0:-1,r2:0:-1,bc:8:23:-','--barcode-whitelist',str(whitelist),'--barcode-translate',str(translation),
 '-q','30','-l','2000','--bc-error-threshold','1','--bc-probability-threshold','0.9','-t','4','--summary',str(out/'summary.tsv'),'-o',str(out/'fragments.tsv')]
resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3))
start=time.monotonic()
with (out/'chromap.stdout').open('w') as stdout,(out/'chromap.stderr').open('w') as stderr:subprocess.run(command,stdout=stdout,stderr=stderr,check=True)
result={'experiment_label':'SENSITIVITY: Chromap reconstruction, not Cell Ranger equivalence','experiment':a.experiment,'runs':runs,'command':command,'command_sha256':hashlib.sha256(json.dumps(command,separators=(',',':')).encode()).hexdigest(),'elapsed_seconds':time.monotonic()-start,'chromap_version':subprocess.check_output([str(binary),'--version'],text=True).strip(),'reference_sha256':sha(reference),'index_sha256':sha(index),'whitelist_sha256':sha(whitelist),'translation_sha256':sha(translation),'outputs':{p.name:sha(p) for p in out.iterdir() if p.suffix=='.tsv'}}
(out/'mapping.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
