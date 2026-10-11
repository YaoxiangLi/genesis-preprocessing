from pathlib import Path
import json,urllib.parse,xml.etree.ElementTree as ET
from genesis_tools.scatac.discovery import Archive
from genesis_tools.contracts.records import dump
root=Path('../results/scatac-completion/sorghum-runs');a=Archive(root/'sources');selected=json.loads((root/'selected.json').read_text());output=[]
for experiment in selected.values():
 for run in experiment['runs']:
  accession=run['run_accession'];b='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
  result=json.loads(a.get(b+'esearch.fcgi?'+urllib.parse.urlencode({'db':'sra','term':accession,'retmode':'json'})))['esearchresult']
  text=a.get(b+'efetch.fcgi?'+urllib.parse.urlencode({'db':'sra','id':','.join(result['idlist']),'retmode':'xml'}));tree=ET.fromstring(text)
  packages=[r for r in tree.findall('.//RUN') if r.attrib.get('accession')==accession]
  assert len(packages)==1;package=packages[0]
  sources=[f.attrib for f in package.findall('.//SRAFile') if f.attrib.get('semantic_name')=='SRA Normalized' and f.attrib.get('filename')==accession]
  assert len(sources)==1;s=sources[0]
  originals=[f.attrib['filename'] for f in package.findall('.//SRAFile') if f.attrib.get('supertype')=='Original']
  out={**run,'sra':s,'original_filenames':originals};output.append(out);print(accession,s['size'],originals[:1])
dump(root/'acquisition.json',{'runs':output,'sources':a.sources,'total_sra_bytes':sum(int(r['sra']['size']) for r in output)})
