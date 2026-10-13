import datetime, hashlib, json, os, subprocess, sys, time
from pathlib import Path
name, directory, *command = sys.argv[1:]
evidence = Path(__file__).parent / 'evidence'
evidence.mkdir(exist_ok=True)
log = evidence / f'{name}.log'
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=directory, text=True).strip()
status = subprocess.check_output(['git', 'status', '--porcelain'], cwd=directory, text=True)
environment = os.environ.copy()
overrides = {'PATH': '/tmp/genesis-tooling/bin:' + environment['PATH'], 'NXF_PLUGINS_DIR': '/tmp/genesis-nextflow-plugins-v1', 'NXF_OFFLINE': 'true', 'UV_LINK_MODE': 'copy'}
environment.update(overrides)
start = time.monotonic()
with log.open('w') as output:
    result = subprocess.run(command, cwd=directory, env=environment, stdout=output, stderr=subprocess.STDOUT)
record = {'command': command, 'cwd': directory, 'started_utc': started, 'seconds': round(time.monotonic()-start, 3), 'exit_code': result.returncode, 'status': 'PASS' if result.returncode == 0 else 'FAIL', 'source_revision': revision, 'working_tree_before': status, 'environment_overrides': {key: value for key, value in overrides.items() if key != 'PATH'}, 'tooling_path_prefix': '/tmp/genesis-tooling/bin', 'log_sha256': hashlib.sha256(log.read_bytes()).hexdigest()}
(evidence / f'{name}.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2), flush=True)
sys.exit(result.returncode)
