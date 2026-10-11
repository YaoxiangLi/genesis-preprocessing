from pathlib import Path
import urllib.parse,json,csv,io
from genesis_tools.scatac.discovery import Archive
from genesis_tools.contracts.records import dump
r=Path('../results/scatac-completion/sorghum-runs');a=Archive(r/'sources')
t=a.get('https://www.ebi.ac.uk/ena/portal/api/filereport?'+urllib.parse.urlencode({'accession':'PRJNA1046450','result':'read_run','fields':'run_accession,experiment_accession,sample_accession,scientific_name,library_strategy,fastq_bytes,fastq_ftp','format':'tsv'}))
rows=list(csv.DictReader(io.StringIO(t),delimiter='\t'));dump(r/'runs.json',{'rows':rows,'sources':a.sources})
for row in rows:
 if row['experiment_accession'] in ['SRX22683055','SRX22683056','SRX22683076','SRX22683077','SRX22683080','SRX22683084']:print(row)
