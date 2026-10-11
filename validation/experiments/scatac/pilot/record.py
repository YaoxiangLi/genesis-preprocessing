"""Run a validation command with complete separate logs and immutable receipts."""
import argparse, datetime, hashlib, json, pathlib, subprocess, time
p=argparse.ArgumentParser(); p.add_argument('label'); p.add_argument('--input',action='append',default=[]); p.add_argument('command',nargs=argparse.REMAINDER); a=p.parse_args()
root=pathlib.Path(__file__).resolve().parents[2]; repo=root/'repo'; out=root/'results/scatac-completion/commands'/a.label
out.mkdir(parents=True,exist_ok=False)
cmd=a.command[1:] if a.command and a.command[0]=='--' else a.command
checks={}
for name in a.input:
 path=pathlib.Path(name).resolve()
 with path.open('rb') as f: checks[str(path)]=hashlib.file_digest(f,'sha256').hexdigest()
start_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
source_checks={str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (repo/'genesis_tools/src/genesis_tools/scatac').rglob('*.py')}
start=time.monotonic(); start_date=datetime.datetime.now(datetime.timezone.utc).isoformat()
with (out/'stdout.log').open('wb') as stdout,(out/'stderr.log').open('wb') as stderr:
 result=subprocess.run(['/usr/bin/time','-v','-o',str(out/'resources.txt'),*cmd],cwd=repo,stdout=stdout,stderr=stderr,check=False)
receipt={'label':a.label,'command':cmd,'cwd':str(repo),'git_sha':start_sha,'scatac_source_sha256':source_checks,'diff_sha256':hashlib.sha256(subprocess.check_output(['git','diff','HEAD'],cwd=repo)).hexdigest(),'started_utc':start_date,'elapsed_seconds':time.monotonic()-start,'exit_status':result.returncode,'input_sha256':checks,'logs':str(out),'acceptance':'PASS' if result.returncode==0 else 'FAIL'}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n'); print(json.dumps({k:v for k,v in receipt.items() if k != "scatac_source_sha256"})); raise SystemExit(result.returncode)
