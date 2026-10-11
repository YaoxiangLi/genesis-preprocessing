"""Download only the five audited Sorghum runs, verifying archive MD5 and SHA256."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import datetime, hashlib, json, shutil, time, urllib.request

root=Path('../results/scatac-completion/sorghum-runs')
manifest=json.loads((root/'acquisition.json').read_text())
assert manifest['total_sra_bytes'] < 30_000_000_000
assert {r['run_accession'] for r in manifest['runs']} == {'SRR26989943','SRR26989999','SRR26990000','SRR26990001','SRR26990002'}
out=root/'sra';out.mkdir(exist_ok=True)
assert shutil.disk_usage(out).free > 500_000_000_000
def fetch(row):
 source=row['sra'];path=out/(row['run_accession']+'.sra');temp=path.with_suffix('.partial')
 assert not path.exists() and not temp.exists()
 assert source['url'].startswith('https://sra-pub-run-odp.s3.amazonaws.com/sra/')
 start=time.monotonic();sha=hashlib.sha256();md5=hashlib.md5();size=0
 with urllib.request.urlopen(source['url'],timeout=120) as response,temp.open('xb') as stream:
  while block:=response.read(4*1024**2):
   size+=len(block)
   if size>int(source['size']):raise ValueError('Archive size exceeds metadata')
   sha.update(block);md5.update(block);stream.write(block)
 assert size==int(source['size']) and md5.hexdigest()==source['md5']
 temp.rename(path)
 result={'accession':row['run_accession'],'url':source['url'],'bytes':size,'md5':md5.hexdigest(),'sha256':sha.hexdigest(),'elapsed_seconds':time.monotonic()-start,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 path.with_suffix('.receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
 return result
with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(fetch,sorted(manifest['runs'],key=lambda r:-int(r['sra']['size']))))
(root/'download-summary.json').write_text(json.dumps(results,indent=2)+'\n')
