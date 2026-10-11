"""Verify public fragment endpoints without downloading additional sequencing data."""
from pathlib import Path
import datetime,hashlib,json,urllib.request

source=Path('../results/scatac-discovery/inventory/discovery.json');records=json.loads(source.read_text())['records'];results=[]
for gsm in ['GSM9536803','GSM9536804']:
 row=next(r for r in records if r['geo_sample']==gsm)
 for url in row['supplementary_files']:
  if not url.endswith('fragments.tsv.gz'):continue
  request=urllib.request.Request(url,method='HEAD',headers={'User-Agent':'Genesis-metadata/1'})
  with urllib.request.urlopen(request,timeout=30) as response:
   results.append({'geo_sample':gsm,'organisms':row['organisms'],'url':url,'http_status':response.status,'content_length':response.headers.get('Content-Length'),'content_type':response.headers.get('Content-Type'),'last_modified':response.headers.get('Last-Modified'),'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'file_sha256':None,'downloaded_bytes':0,'interpretation':'Public endpoint accessible; complete file checksum and biological metadata not yet validated'})
out={'metadata_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'files':results}
Path('../results/scatac-completion/provenance/extra-fragment-access.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
