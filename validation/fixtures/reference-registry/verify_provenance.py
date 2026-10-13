import datetime,hashlib,json,subprocess
from pathlib import Path
import jsonschema
root=Path(__file__).resolve().parents[2]
schema=json.loads((root/'design/processing-provenance-schema.yaml').read_text())
validator=jsonschema.Draft202012Validator(schema,format_checker=jsonschema.FormatChecker())
record={'execution_kind':'contract-validation','genesis_git_sha':'e8b37e281b4cace2522179ac7208cfef15cd4dea','sample_sheet_sha256':None,'reference_registry_sha256':hashlib.sha256((root/'fixtures/reference-registry/reference.json').read_bytes()).hexdigest(),'container_identities':{'validator':'sha256:3f8fc8c57e57994b95408cd02a7ced44a6fb90396b9067bbe2d2dcdebb396b50'},'parameters':{'fixture':'reference-registry','thresholds':'UNSPECIFIED'},'execution_timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'nextflow_version':None,'task_versions':{'jsonschema':'4.26.0'},'original_accessions_urls':['urn:genesis:synthetic:tiny-v1']}
validator.validate(record)
for field in ['genesis_git_sha','reference_registry_sha256','container_identities','task_versions']:
 bad=record.copy();del bad[field]
 try:validator.validate(bad)
 except jsonschema.ValidationError:pass
 else:raise AssertionError(field)
bad=record|{'execution_kind':'nextflow-run'}
try:validator.validate(bad)
except jsonschema.ValidationError:pass
else:raise AssertionError('pipeline missing Nextflow/sample sheet accepted')
(root/'results/contracts/processing-provenance.json').write_text(json.dumps(record,indent=2)+'\n')
print('PASS: explicit component provenance; Nextflow runs require version/sample-sheet identity')
