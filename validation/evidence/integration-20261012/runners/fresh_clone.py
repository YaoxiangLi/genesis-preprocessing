import datetime, hashlib, json, os, subprocess, time
from pathlib import Path
source = Path.cwd()
root = source.parent
clone = root / 'fresh-lab'
expected = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
env = os.environ.copy()
env.pop('PYTHONPATH', None)
steps = []
def run(command, cwd):
    begin = time.monotonic()
    print('+', ' '.join(str(x) for x in command), flush=True)
    result = subprocess.run(command, cwd=cwd, env=env)
    steps.append({'command': [str(x) for x in command], 'cwd': str(cwd), 'exit_code': result.returncode, 'seconds': round(time.monotonic()-begin, 3)})
    result.check_returncode()
run(['git', 'clone', '--branch', 'main', '--single-branch', 'https://github.com/kundajelab/genesis-preprocessing.git', str(clone)], root)
actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=clone, text=True).strip()
assert actual == expected, (actual, expected)
run(['pixi', 'run', 'install-all'], clone)
run(['pixi', 'run', 'genesis', '--help'], clone)
run(['pixi', 'run', 'genesis', 'doctor'], clone)
run(['pixi', 'run', 'uv', 'run', '--frozen', '--project', 'genesis_tools', 'python', 'tests/verify_readme.py'], clone)
run(['pixi', 'run', 'uv', 'run', '--frozen', '--project', 'genesis_tools', 'python', 'examples/curation/offline_workflow.py', str(root / 'fresh-demo')], clone)
files = subprocess.check_output(['git', 'ls-files', '-z'], cwd=clone).decode().split('\0')
count = 0
for name in files:
    if name:
        assert (clone / name).read_bytes() == (source / name).read_bytes(), name
        count += 1
assert subprocess.check_output(['git', 'status', '--porcelain'], cwd=clone, text=True) == ''
assert subprocess.check_output(['git', 'status', '--porcelain'], cwd=source, text=True) == ''
record = {'status': 'PASS', 'checked_revision': actual, 'clone_url': 'https://github.com/kundajelab/genesis-preprocessing.git', 'steps': steps, 'tracked_files_byte_identical': count, 'checkout_clean': True, 'PYTHONPATH': 'unset', 'scope': 'fresh GitHub clone and new environments on this existing Linux host using populated package/plugin caches; not acceptance on an unspecified destination server', 'offline_demo': json.loads((root / 'fresh-demo/acceptance.json').read_text())}
(root / 'evidence/fresh-clone-details.json').write_text(json.dumps(record, indent=2)+'\n')
print(json.dumps(record, indent=2), flush=True)
