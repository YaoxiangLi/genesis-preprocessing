"""Collect compact, checksum-bound evidence after the real pilot has finished."""
from pathlib import Path
from collections import Counter
import csv, datetime, hashlib, json, shutil, subprocess

root = Path(__file__).resolve().parents[2]
base = root / 'results/scatac-completion'
repo = root / 'repo'
out = repo / 'validation/evidence/scatac-completion'
acceptance = json.loads((base / 'release-acceptance.json').read_text())
assert acceptance['computational_acceptance'] == 'PASS'
assert acceptance['groups'] == 24 and acceptance['actual_model_loader_tests'] == 48
reference_bytes = json.loads((base / 'provenance/reference-bytes.json').read_text())
portable = json.loads((base / 'portable-release-acceptance.json').read_text())
assert portable['status'] == 'PASS' and len(portable['relocated_loader_tests']) == 4
out.mkdir(parents=True, exist_ok=True)

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')

def copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    assert digest(source) == digest(destination)

for name in ['release-acceptance.json', 'independent-conservation.json',
             'pseudobulk-qc.tsv', 'selected-identities.json', 'portable-release-acceptance.json']:
    copy(base / name, out / name)
for p in sorted((base / 'provenance').glob('*.json')):
    copy(p, out / 'provenance' / p.name)
for p in sorted((base / 'inventory-tables').glob('*.tsv')):
    copy(p, out / 'inventory' / p.name)

stages = []
models = []
comparisons = []
for species in ['arabidopsis', 'sorghum']:
    directory = base / species
    for marker in sorted(directory.glob('ingested-*/complete.json')):
        data = json.loads(marker.read_text())
        execution = json.loads((marker.parent / 'execution.json').read_text())
        stages.append({'species': species, 'stage': 'ingestion',
                       'path': str(marker.parent.relative_to(base)),
                       'manifest_sha256': digest(marker), 'manifest': data,
                       'execution': execution})
    for marker in sorted((directory / 'products').glob('*/complete.json')):
        data = json.loads(marker.read_text())
        execution = json.loads((marker.parent / 'execution.json').read_text())
        stages.append({'species': species, 'stage': 'products',
                       'path': str(marker.parent.relative_to(base)),
                       'manifest_sha256': digest(marker), 'manifest': data,
                       'execution': execution})
    for p in sorted((directory / 'concordance').glob('*.json')):
        value = json.loads(p.read_text())
        comparisons.append({'species': species, **value})
        copy(p, out / 'concordance' / species / p.name)
    for target in ['cherimoya', 'chrombpnet']:
        for marker in sorted((directory / 'models' / target).glob('*/complete.json')):
            task = marker.parent.name
            assert json.loads(marker.read_text())['outputs']['genome.fa'] == reference_bytes[species]['decompressed_fasta_sha256']
            validation = directory / 'loader-validation' / target / task
            loader_marker = json.loads((validation / 'complete.json').read_text())
            assert loader_marker['data']['loader_test'] == 'PASS'
            models.append({'species': species, 'target': target, 'task_id': task,
                           'manifest': json.loads(marker.read_text()),
                           'backgrounds': json.loads((marker.parent / 'backgrounds.json').read_text()),
                           'loader_manifest': loader_marker,
                           'loader_result': json.loads((validation / 'loader-result.json').read_text()),
                           'execution': json.loads((validation / 'execution.json').read_text())})
write(out / 'stages.json', stages)
write(out / 'models.json', models)
assert len(models) == 48 and len(comparisons) == 12

commands = []
resources = []
for p in sorted((base / 'commands').glob('*/receipt.json')):
    record = json.loads(p.read_text())
    commands.append(record)
    usage = p.parent / 'resources.txt'
    peak = None
    if usage.is_file():
        for line in usage.read_text().splitlines():
            if 'Maximum resident set size (kbytes):' in line:
                peak = int(line.rsplit(':', 1)[1])
        copy(usage, out / 'resources' / (p.parent.name + '.txt'))
    resources.append({'command': p.parent.name, 'status': record['acceptance'],
                      'elapsed_seconds': record['elapsed_seconds'],
                      'peak_process_rss_kib': peak, 'git_sha': record['git_sha']})
write(out / 'commands.json', commands)
with (out / 'resources.tsv').open('w') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(resources[0]), delimiter='\t')
    writer.writeheader(); writer.writerows(resources)
with (base / 'pseudobulk-qc.tsv').open() as stream:
    qc = list(csv.DictReader(stream, delimiter='\t'))
replicate_rows = []
for comparison in sorted(comparisons, key=lambda r: (r['species'], r['cell_type'])):
    pair = {'species': comparison['species'], 'cell_type': comparison['cell_type']}
    for index, replicate in enumerate(comparison['biological_replicates'], start=1):
        candidates = [r for r in qc if r['species'] == comparison['species']
                      and r['cell_type'] == comparison['cell_type']
                      and r['biological_replicate'] == replicate]
        assert len(candidates) == 1
        pair[f'replicate_{index}'] = replicate
        for key in ['cells', 'unique_fragments', 'peaks', 'frip']:
            pair[f'{key}_{index}'] = candidates[0][key]
    for key in ['peak_base_jaccard', 'pearson_nonzero_union', 'spearman_nonzero_union']:
        pair[key] = comparison[key]
    pair['plant_qc_thresholds'] = 'UNSPECIFIED'
    replicate_rows.append(pair)
with (out / 'replicate-qc.tsv').open('w') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(replicate_rows[0]), delimiter='\t')
    writer.writeheader(); writer.writerows(replicate_rows)
copy(out / 'replicate-qc.tsv', base / 'replicate-qc.tsv')
summary = {'schema_version': 1, 'captured_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'git_sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip(),
           'release_acceptance': acceptance, 'species': {},
           'command_results': dict(Counter(r['acceptance'] for r in commands)),
           'resource_scope': 'GNU time process trees; Docker daemon children excluded; explicit limits are not measured peaks',
           'training': 'NOT_RUN', 'scientific_review': 'UNREVIEWED',
           'plant_qc_thresholds': 'UNSPECIFIED'}
for species in ['arabidopsis', 'sorghum']:
    rows = [r for r in qc if r['species'] == species]
    comparisons_here = [r for r in comparisons if r['species'] == species]
    results = {'groups': len(rows), 'cells': sum(int(r['cells']) for r in rows),
               'unique_fragments': sum(int(r['unique_fragments']) for r in rows),
               'support': sum(int(r['support']) for r in rows),
               'cuts': sum(int(r['cuts']) for r in rows),
               'boundary_cuts_excluded': sum(int(r['boundary_cuts_excluded']) for r in rows)}
    for metric in ['peaks', 'frip', 'tss_enrichment', 'support_redundancy_fraction']:
        values = [float(r[metric]) for r in rows if r[metric]]
        results[metric] = {'min': min(values) if values else None, 'max': max(values) if values else None, 'n': len(values)}
    for metric in ['peak_base_jaccard', 'pearson_all_bins', 'spearman_all_bins',
                   'pearson_nonzero_union', 'spearman_nonzero_union']:
        values = [r[metric] for r in comparisons_here if r[metric] is not None]
        results[metric] = {'min': min(values) if values else None, 'max': max(values) if values else None, 'n': len(values)}
    summary['species'][species] = results
write(out / 'summary.json', summary)
copy(base / 'genesis-scatac-pilot-v1/complete.json', out / 'release-manifest.json')
copy(base / 'genesis-scatac-pilot-v1/manifest/groups.json', out / 'release-groups.json')
copy(base / 'genesis-scatac-pilot-v1/checksums.sha256', out / 'release-checksums.sha256')
(out / 'README.md').write_text('''# Two-species scATAC evidence\n\nCompact observations from the real Arabidopsis and Sorghum pilot. Full command\nlogs and large data remain in `results/scatac-completion/` in the validation\nworkspace. See [the report](../../reports/scatac-completion.md) for interpretation.\n\n`summary.json` and `pseudobulk-qc.tsv` summarize measured counts. `stages.json`\nand `models.json` retain exact input/output identities, versions and loader\nevidence. `commands.json` and `resources.tsv` include successful and failed\nattempts. A failed attempt remains a failure even if a later correction passes.\nThe evidence-export command itself finishes after this snapshot and is retained\nin the workspace command ledger.\n\nThe candidate passed computational acceptance. Scientific review remains open,\nplant thresholds are unspecified, and no model training is claimed.\n''')
(out / 'checksums.sha256').write_text(''.join(f'{digest(p)}  {p.relative_to(out)}\n' for p in sorted(out.rglob('*')) if p.is_file() and p != out / 'checksums.sha256'))
print(json.dumps(summary, indent=2))
