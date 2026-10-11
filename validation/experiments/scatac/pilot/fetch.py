import argparse, datetime, hashlib, json, pathlib, shutil, time, urllib.parse, urllib.request
p=argparse.ArgumentParser();p.add_argument('url');p.add_argument('output',type=pathlib.Path);p.add_argument('--max-bytes',type=int,required=True);a=p.parse_args()
u=urllib.parse.urlsplit(a.url)
if u.scheme!='https' or u.username or u.password or u.query: raise ValueError('Public HTTPS without credential/query parameters required')
a.output.parent.mkdir(parents=True,exist_ok=True)
if a.output.exists(): raise ValueError('Refusing to replace downloaded evidence')
if shutil.disk_usage(a.output.parent).free < a.max_bytes+200*1024**3: raise ValueError('200 GiB free-space floor')
start=time.monotonic();h=hashlib.sha256();n=0;temp=a.output.with_suffix(a.output.suffix+'.partial')
with urllib.request.urlopen(a.url,timeout=60) as response,temp.open('xb') as f:
 while b:=response.read(4*1024**2):
  n+=len(b)
  if n>a.max_bytes: raise ValueError('Download byte budget exceeded')
  h.update(b);f.write(b)
temp.rename(a.output)
receipt={'url':a.url,'sha256':h.hexdigest(),'bytes':n,'elapsed_seconds':time.monotonic()-start,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
a.output.with_suffix(a.output.suffix+'.receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
