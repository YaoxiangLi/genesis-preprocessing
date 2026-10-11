from pathlib import Path
import json,urllib.parse,xml.etree.ElementTree as ET
from genesis_tools.scatac.discovery import Archive
from genesis_tools.contracts.records import dump
root=Path('../results/scatac-completion/raw-layouts').resolve();a=Archive(root/'sources')
for run in ['SRR26989943','SRR27500250']:
 b='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
 s=json.loads(a.get(b+'esearch.fcgi?'+urllib.parse.urlencode({'db':'sra','term':run,'retmode':'json'})))['esearchresult']
 text=a.get(b+'efetch.fcgi?'+urllib.parse.urlencode({'db':'sra','id':','.join(s['idlist']),'retmode':'xml'}));(root/(run+'.xml')).write_text(text)
 tree=ET.fromstring(text)
 print(run,'uids',s['idlist'])
 for tag in ['READ_SPEC','FILE','SRAFile']:
  for e in tree.findall('.//'+tag):print(ET.tostring(e,encoding='unicode')[:2500])
dump(root/'receipts.json',a.sources)
