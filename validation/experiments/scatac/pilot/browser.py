import urllib.request,re,json,pathlib,hashlib
u='https://epigenome.genetics.uga.edu/PlantEpigenome/dist/main.bundle.js'
try:
 with urllib.request.urlopen(u,timeout=30) as r:b=r.read(8000000)
 p=pathlib.Path('../results/scatac-completion/sources/browser.js');p.write_bytes(b)
 s=b.decode(); print(json.dumps({'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'urls':sorted(set(re.findall(r'https?://[^\s\"\x27<>]+',s)))[:40]}))
except Exception as e: print(type(e).__name__)
