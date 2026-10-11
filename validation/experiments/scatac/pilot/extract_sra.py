"""Extract all four read roles with explicit disk/thread limits; preserve raw SRA."""
from pathlib import Path
import argparse,hashlib,json,resource,subprocess,time
p=argparse.ArgumentParser();p.add_argument('accession');a=p.parse_args()
root=Path('../results/scatac-completion/sorghum-runs').resolve();source=root/'sra'/(a.accession+'.sra')
entry=next(r for r in json.loads((root/'acquisition.json').read_text())['runs'] if r['run_accession']==a.accession)
assert source.stat().st_size==int(entry['sra']['size'])
out=root/'fastq'/a.accession;out.mkdir(parents=True,exist_ok=False)
binary=Path('../scratch/scatac-completion/raw-env/bin/fasterq-dump').absolute()
resource.setrlimit(resource.RLIMIT_AS,(16*1024**3,16*1024**3))
command=[str(binary),str(source),'--split-files','--include-technical','-e','6','-m','2G','-O',str(out),'-t',str(out/'temp'),'--disk-limit','160G','--disk-limit-tmp','220G','--seq-defline','@$ac.$si/$ri','--qual-defline','+']
start=time.monotonic()
with (out/'extraction.stdout').open('w') as stdout,(out/'extraction.stderr').open('w') as stderr:
 subprocess.run(command,stdout=stdout,stderr=stderr,check=True)
paths=sorted(out.glob('*.fastq'));assert len(paths)==4
outputs={}
for path in paths:
 # gzip's content CRC and the source digest are retained; only generated plain text is removed.
 with path.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
 subprocess.run(['pigz','-n','-p','6','-1',str(path)],check=True)
 gz=path.with_suffix(path.suffix+'.gz')
 with gz.open('rb') as f:compressed=hashlib.file_digest(f,'sha256').hexdigest()
 outputs[gz.name]={'uncompressed_sha256':sha,'sha256':compressed,'bytes':gz.stat().st_size}
receipt={'accession':a.accession,'command':command,'pigz_version':subprocess.check_output(['pigz','--version'],text=True).strip(),'compression':['pigz','-n','-p','6','-1'],'input':json.loads(source.with_suffix('.receipt.json').read_text()),'elapsed_seconds':time.monotonic()-start,'outputs':outputs}
(out/'extraction.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
