"""Record final pilot storage, verified acquisition volume and stage resource costs."""
from pathlib import Path
import datetime, hashlib, json, shutil, subprocess

root = Path(__file__).resolve().parents[2]
base = root / 'results/scatac-completion'
assert json.loads((base / 'portable-release-acceptance.json').read_text())['status'] == 'PASS'
sources = json.loads((base / 'provenance/source-assets.json').read_text())
archives = json.loads((base / 'sorghum-runs/download-summary.json').read_text())
transition_path = base / 'provenance/model-parallel-transition.json'
transition = (json.loads(transition_path.read_text()) if transition_path.exists()
              else {'completed_manifest_sha256': {}})
for location, expected in transition['completed_manifest_sha256'].items():
    assert hashlib.sha256((base / location).read_bytes()).hexdigest() == expected
stages = []
for species in ['arabidopsis', 'sorghum']:
    directory = base / species
    paths = list(directory.glob('ingested-*/execution.json')) + [directory / 'core/execution.json']
    paths += list((directory / 'products').glob('*/execution.json'))
    paths += list((directory / 'loader-validation').glob('*/*/execution.json'))
    for path in sorted(paths):
        record = json.loads(path.read_text())
        stages.append({'species': species, 'path': str(path.relative_to(base)),
                       'elapsed_seconds': record['elapsed_seconds'],
                       'peak_process_rss_kib': record['process_peak_rss_kib'],
                       'git_sha': record['git_sha']})
native = []
for label in ['sorghum-map-SRX22683056', 'sorghum-map-SRX22683080-40GiB']:
    directory = base / 'commands' / label
    record = json.loads((directory / 'receipt.json').read_text())
    assert record['acceptance'] == 'PASS'
    resource_lines = (directory / 'resources.txt').read_text().splitlines()
    peak = next(int(line.rsplit(':', 1)[1]) for line in resource_lines
                if 'Maximum resident set size (kbytes):' in line)
    native.append({'command': label, 'elapsed_seconds': record['elapsed_seconds'],
                   'peak_process_rss_kib': peak, 'git_sha': record['git_sha']})
directories = [root / 'results/scatac-completion', root / 'results/scatac-discovery',
               root / 'scratch/scatac-completion']
storage = []
for directory in directories:
    argv = ['du', '-s', '--block-size=1', str(directory)]
    output = subprocess.check_output(argv, text=True)
    storage.append({'path': str(directory.relative_to(root)), 'allocated_bytes': int(output.split()[0]),
                    'command': argv})
disk = shutil.disk_usage(base)
result = {
    'captured_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'budget': {'cpus': 16, 'ram_gib': 64, 'downloads_gb': 150, 'new_working_data_gb': 500},
    'verified_new_source_asset_bytes': sum(r['bytes'] for r in sources),
    'verified_new_sra_bytes': sum(r['bytes'] for r in archives),
    'verified_major_download_bytes': sum(r['bytes'] for r in sources + archives),
    'download_scope': 'Successful recorded major source assets and SRA objects; reused Arabidopsis files excluded. Metadata, software, retries and transport overhead are not a measured network total.',
    'storage': storage,
    'storage_scope': 'Allocated blocks in the named directories, with hard links counted once within each du invocation. Existing shared model/tool environments, Docker layers and retained historical data are outside this snapshot.',
    'disk_free_bytes_after': disk.free,
    'exact_disk_free_bytes_before': None,
    'disk_before_note': 'Acquisition checked for more than 500 GB free; no exact pre-run filesystem snapshot was retained.',
    'resource_scope': 'Stage execution timers exclude prerequisite waiting. Peak process RSS is a process high-water mark, not incremental stage memory. Docker daemon children are excluded; limits are not measured peaks.',
    'parallel_transition_manifests_unchanged': len(transition['completed_manifest_sha256']),
    'native_mapping': native,
    'stages': stages,
}
(base / 'provenance/resource-accounting.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps({k: result[k] for k in ['verified_major_download_bytes', 'storage', 'disk_free_bytes_after']}, indent=2))
