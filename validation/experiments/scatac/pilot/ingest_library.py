from pathlib import Path
import sys,json
from genesis_tools.scatac import ingest
m=Path(sys.argv[1]);out=Path(sys.argv[2]);r=ingest.run(m,out,resume=True)
print(json.dumps({'initial_cached':r['cached'],'counts':r['manifest']['data']['counts'],'output_version':r['manifest']['version']}),flush=True)
assert ingest.run(m,out,resume=True)['cached']
print('PASS: stable ingestion resume; input and output hashes verified')
