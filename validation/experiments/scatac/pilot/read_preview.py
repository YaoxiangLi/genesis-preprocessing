import urllib.request,zlib,json,hashlib,pathlib
out=pathlib.Path('results/scatac-completion/sources/raw-previews');out.mkdir(parents=True,exist_ok=True)
for run,path in [('SRR26989943','SRR269/043/SRR26989943'),('SRR27500250','SRR275/050/SRR27500250')]:
 u=f'https://ftp.sra.ebi.ac.uk/vol1/fastq/{path}/{run}_1.fastq.gz'
 try:
  with urllib.request.urlopen(u,timeout=30) as r:b=r.read(1024*1024)
  text=zlib.decompressobj(16+zlib.MAX_WBITS).decompress(b).decode(); lines=text.splitlines(); complete=len(lines)//4
  summary={'accession':run,'url':u,'prefix_bytes':len(b),'prefix_sha256':hashlib.sha256(b).hexdigest(),'complete_records_examined':complete,'headers_first_three':[lines[i*4] for i in range(min(complete,3))],'read_lengths_first_three':[len(lines[i*4+1]) for i in range(min(complete,3))]}
  (out/(run+'.json')).write_text(json.dumps(summary,indent=2)+'\n'); print(json.dumps(summary))
 except Exception as e: print(json.dumps({'accession':run,'error':type(e).__name__,'status':getattr(e,'code',None)}))
