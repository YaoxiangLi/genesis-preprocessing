"""Validate registry schema, content identity and canonical-ID uniqueness on tiny fixtures."""
from pathlib import Path
import copy,gzip,hashlib,json,tempfile
import jsonschema
root=Path(__file__).resolve().parents[2]
schema=json.loads((root/'design/reference-schema.yaml').read_text())
validator=jsonschema.Draft202012Validator(schema,format_checker=jsonschema.FormatChecker())
reference=json.loads((root/'fixtures/reference-registry/reference.json').read_text())
def validate(records,base):
 ids=set();identities=set();aliases=set()
 for record in records:
  validator.validate(record)
  if record['reference_id'] in ids:raise ValueError('duplicate reference ID')
  identity=(record['fasta_sha256'],record['annotation']['sha256'],record['masking'])
  if identity in identities:raise ValueError('duplicate canonical identity; declare aliases')
  names={record['reference_id'],*record['aliases']}
  if aliases & names:raise ValueError('ambiguous alias')
  if Path(record['fasta_basename']).name!=record['fasta_basename']:raise ValueError('unsafe basename')
  raw=(base/record['fasta_basename']).read_bytes()
  if record['compressed_fasta_sha256'] is not None and hashlib.sha256(raw).hexdigest()!=record['compressed_fasta_sha256']:raise ValueError('compressed FASTA mismatch')
  payload=gzip.decompress(raw) if record['fasta_basename'].endswith('.gz') else raw
  if hashlib.sha256(payload).hexdigest()!=record['fasta_sha256']:raise ValueError('FASTA content mismatch')
  sizes=base/record['chrom_sizes_basename']
  if sizes.name != record['chrom_sizes_basename']:raise ValueError('unsafe sizes basename')
  if hashlib.sha256(sizes.read_bytes()).hexdigest()!=record['chrom_sizes_sha256']:raise ValueError('chromosome sizes content mismatch')
  ids.add(record['reference_id']);identities.add(identity);aliases.update(names)
results=[]
with tempfile.TemporaryDirectory(dir=root/'scratch/completion',prefix='registry-') as directory:
 base=Path(directory);base.joinpath('tiny.fa').write_bytes((root/'fixtures/reference-registry/tiny.fa').read_bytes())
 base.joinpath('tiny.chrom.sizes').write_bytes((root/'fixtures/reference-registry/tiny.chrom.sizes').read_bytes())
 validate([reference],base);results.append('valid fixture')
 compressed=copy.deepcopy(reference);compressed['fasta_basename']='tiny.fa.gz'
 raw=gzip.compress(base.joinpath('tiny.fa').read_bytes(),mtime=0);base.joinpath('tiny.fa.gz').write_bytes(raw)
 compressed['compressed_fasta_sha256']=hashlib.sha256(raw).hexdigest()
 validate([compressed],base);results.append('compressed FASTA identity verified')
 cases=[]
 missing=copy.deepcopy(reference);del missing['assembly_version'];cases.append(('missing identity',[missing]))
 bad=copy.deepcopy(reference);bad['fasta_sha256']='bad';cases.append(('malformed checksum',[bad]))
 alias=copy.deepcopy(reference);alias['reference_id']='other';cases.append(('ambiguous canonical identity',[reference,alias]))
 cases.append(('duplicate ID',[reference,reference]))
 for name,records in cases:
  try:validate(records,base)
  except (ValueError,jsonschema.ValidationError):results.append(name+' rejected')
  else:raise AssertionError(name)
 base.joinpath('tiny.chrom.sizes').write_text('chr1\t99\n')
 try:validate([reference],base)
 except ValueError:results.append('damaged chromosome sizes rejected')
 else:raise AssertionError('damaged sizes accepted')
 base.joinpath('tiny.chrom.sizes').write_bytes((root/'fixtures/reference-registry/tiny.chrom.sizes').read_bytes())
 base.joinpath('tiny.fa').write_bytes(b'>chr1\nTTTTACGTACGT\n')
 try:validate([reference],base)
 except ValueError:results.append('same filename changed FASTA rejected')
 else:raise AssertionError('changed FASTA accepted')
report={'checks':results,'schema_sha256':hashlib.sha256((root/'design/reference-schema.yaml').read_bytes()).hexdigest(),'reference_sha256':reference['fasta_sha256']}
(root/'results/contracts/reference-schema.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
