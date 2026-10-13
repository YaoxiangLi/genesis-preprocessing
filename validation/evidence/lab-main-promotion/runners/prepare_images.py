import concurrent.futures, json, subprocess
from pathlib import Path
images = sorted(set(json.loads(Path('conf/atac-images.json').read_text()).values()) | {line.split('=', 1)[1] for line in Path('.env').read_text().splitlines() if '_IMAGE=' in line})
def prepare(image):
    present = subprocess.run(['docker', 'image', 'inspect', image], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    if not present:
        subprocess.run(['docker', 'pull', image], check=True)
    result = json.loads(subprocess.check_output(['docker', 'image', 'inspect', image]))[0]
    return {'requested': image, 'id': result['Id'], 'architecture': result['Architecture'], 'os': result['Os'], 'size_bytes': result['Size'], 'already_present': present}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    records = list(pool.map(prepare, images))
Path('/var/tmp/genesis-promotion-nlkkcy4o/evidence/images.json').write_text(json.dumps(records, indent=2) + '\n')
print(json.dumps(records, indent=2))
