"""Start the second reconstruction only after extraction checksums are finalized."""
from pathlib import Path
import runpy,sys,time
receipt=Path('../results/scatac-completion/sorghum-runs/fastq/SRR26989943/extraction.json')
deadline=time.monotonic()+3600
while not receipt.is_file():
 if time.monotonic()>deadline:raise TimeoutError('Extraction receipt missing')
 time.sleep(10)
sys.argv=['map_sorghum.py','SRX22683080']
runpy.run_path('../scratch/scatac-completion/map_sorghum.py',run_name='__main__')
