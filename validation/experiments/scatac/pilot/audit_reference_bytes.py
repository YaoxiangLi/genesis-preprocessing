"""Distinguish downloaded gzip bytes from the uncompressed FASTA delivered to models."""
from pathlib import Path
import gzip,hashlib,json

base=Path('../results/scatac-completion').resolve();result={}
for species in ['arabidopsis','sorghum']:
    manifest=next((base/species).glob('ingested-*/input.json'))
    reference=json.loads(manifest.read_text())['reference'];source=Path(reference['fasta']['path'])
    with source.open('rb') as stream:compressed=hashlib.file_digest(stream,'sha256').hexdigest()
    assert compressed==reference['fasta']['sha256']
    uncompressed=hashlib.sha256();size=0
    with gzip.open(source,'rb') as stream:
        while block:=stream.read(4*1024*1024):
            uncompressed.update(block);size+=len(block)
    observed={json.loads(p.read_text())['outputs']['genome.fa'] for p in (base/species/'models').glob('*/*/complete.json')}
    if observed:assert observed=={uncompressed.hexdigest()}
    result[species]={'reference_id':reference['reference_id'],'source_gzip':str(source.relative_to(base)),
                     'source_gzip_sha256':compressed,'decompressed_fasta_sha256':uncompressed.hexdigest(),
                     'decompressed_bytes':size,'contigs':len(reference['contigs']),
                     'sequence_bases':sum(reference['contigs'].values()),
                     'completed_model_bundle_fasta_hashes':sorted(observed),
                     'note':'FASTA hashes cover bytes, including headers and wrapping; source archives and model FASTA identities are distinct.'}
(base/'provenance/reference-bytes.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
