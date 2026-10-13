import hashlib, json, os, shutil, subprocess, sys, zipfile
from pathlib import Path
repo = Path.cwd()
root = Path('/var/tmp/genesis-study-MQ6B5glk/installed')
root.mkdir(exist_ok=False)
env = os.environ.copy()
env.pop('PYTHONPATH', None)
env['UV_OFFLINE'] = 'true'
commands = []
def run(args, cwd=root):
    commands.append({'command': [str(a) for a in args], 'cwd': str(cwd)})
    print('+', ' '.join(str(a) for a in args), flush=True)
    subprocess.run(args, cwd=cwd, env=env, check=True)
run(['uv', 'build', '--wheel', '--out-dir', str(root / 'dist'), str(repo / 'genesis_tools')])
wheel, = (root / 'dist').glob('*.whl')
run(['uv', 'export', '--frozen', '--project', str(repo / 'genesis_tools'), '--no-dev', '--no-emit-project', '--output-file', str(root / 'requirements.txt')])
run(['uv', 'venv', '--python', sys.executable, '--no-python-downloads', str(root / 'env')])
python = root / 'env/bin/python'
run(['uv', 'pip', 'install', '--offline', '--python', str(python), '-r', str(root / 'requirements.txt')])
run(['uv', 'pip', 'install', '--offline', '--no-deps', '--python', str(python), str(wheel)])
run([str(root / 'env/bin/genesis'), '--help'])
run([str(root / 'env/bin/genesis-tools'), '--help'])
resources = []
for folder in ('contracts/schemas', 'qc_policy/policies', 'llm/schemas', 'llm/prompts', 'curation/vocabularies', 'schematics/assets', 'scatac/assets'):
    resources.extend(str(p.relative_to(repo / 'genesis_tools/src')) for p in (repo / 'genesis_tools/src/genesis_tools' / folder).rglob('*') if p.is_file())
resources.append('genesis_tools/benchmark/report.html')
with zipfile.ZipFile(wheel) as archive:
    for resource in resources:
        assert archive.read(resource) == (repo / 'genesis_tools/src' / resource).read_bytes(), resource
for name in ('create_demo.py', 'offline_workflow.py', 'providers.mock.json'):
    shutil.copy2(repo / 'examples/curation' / name, root / name)
run([str(python), str(root / 'offline_workflow.py'), str(root / 'demo')])
acceptance = json.loads((root / 'demo/acceptance.json').read_text())
assert acceptance['status'] == 'PASS' and acceptance['decisions'] == 6
run([str(root / 'env/bin/genesis'), 'schematic', 'render', '--help'])
result = {'commands': commands, 'wheel_sha256': hashlib.sha256(wheel.read_bytes()).hexdigest(), 'checked_package_resources': resources, 'PYTHONPATH': 'unset', 'installation': 'wheel in a new environment; dependencies frozen from committed lock using existing cache; UV_OFFLINE=true', 'demo': acceptance}
Path('/var/tmp/genesis-study-MQ6B5glk/evidence/installed-wheel-details.json').write_text(json.dumps(result, indent=2) + '\n')
for name in ('verify_curation.py', 'verify_dap_provenance.py'):
    shutil.copy2(repo / 'tests' / name, root / name)
run([str(python), str(root / 'verify_dap_provenance.py')])
print('PASS: installed wheel outside checkout, packaged resources, CLI entry points and offline review workflow')
