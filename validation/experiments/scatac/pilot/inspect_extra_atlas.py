"""Inspect the public atlas's source code and archive metadata without fetching its data files."""
from pathlib import Path
import datetime,hashlib,json,re,subprocess,urllib.request

root=Path('..').resolve();base=root/'results/scatac-completion';repo=root/'benchmarks/regulatory-neighborhoods'
source_url='https://code.jgi.doe.gov/AMoralesCruz/regulatory-neighborhoods'
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
expected=(base/'commands/extra-atlas-source-revision/stdout.log').read_text().split()[0]
assert sha==expected
paths=subprocess.check_output(['git','ls-tree','-r','--name-only','HEAD'],cwd=repo,text=True).splitlines()
files={};mentions=[];urls=set()
for name in paths:
    raw=subprocess.check_output(['git','show',f'HEAD:{name}'],cwd=repo)
    files[name]=hashlib.sha256(raw).hexdigest()
    text=raw.decode()
    if name.endswith('.ipynb'):
        notebook=json.loads(text)
        text='\n'.join(''.join(c.get('source',[])) for c in notebook.get('cells',[]))
    if re.search(r'(?i)fragments?\.(?:tsv|bed)',text):mentions.append(name)
    for url in re.findall(r'https?://[^\s\"\'<>]+',text):
        if not re.search(r'(?i)(token|secret|password|api[_-]?key|://[^/]+@)',url):urls.add(url.rstrip(').,;'))
output=base/'extra-atlas-metadata';output.mkdir(exist_ok=False)
url='https://zenodo.org/api/records/18407668'
with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Genesis-validation/1.0'}),timeout=30) as response:
    data=response.read(5*1024*1024+1);assert len(data)<=5*1024*1024
    status=response.status
(output/'zenodo.json').write_bytes(data)
record=json.loads(data)
summary={'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_repository':source_url,
         'source_commit':sha,'source_file_sha256':files,'source_file_count':len(files),
         'files_with_fragment_filename_mentions':mentions,'public_links':sorted(urls),
         'zenodo_url':'https://zenodo.org/records/18407668','zenodo_api_url':url,
         'zenodo_http_status':status,'zenodo_snapshot_sha256':hashlib.sha256(data).hexdigest(),
         'zenodo_metadata_bytes':len(data),'zenodo_license':record.get('metadata',{}).get('license'),
         'zenodo_files':[{'name':f['key'],'size':f['size'],'checksum':f['checksum']} for f in record.get('files',[])],
         'full_data_files_downloaded':False,
         'finding':'Additional processed atlas data and author analysis code exist; no directly downloadable fragment file was identified by this bounded code/metadata inspection. This is not evidence of absence from every possible source.',
         'status':'NEEDS_METADATA / NEEDS_PROCESSED_FILES'}
(base/'provenance/extra-atlas-source-audit.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:summary[k] for k in ['source_commit','source_file_count','files_with_fragment_filename_mentions','zenodo_metadata_bytes','zenodo_license','full_data_files_downloaded','status']},indent=2))
