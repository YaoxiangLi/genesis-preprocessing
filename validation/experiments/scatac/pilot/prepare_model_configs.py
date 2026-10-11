"""Create the pilot's explicit model configurations without starting model validation."""
from pathlib import Path
import argparse, json
from genesis_tools.contracts.records import dump, load
from genesis_tools.scatac.model import MODELS
from genesis_tools.scatac.common import digest

parser = argparse.ArgumentParser()
parser.add_argument('species', choices=['arabidopsis', 'sorghum'])
args = parser.parse_args()
root = Path('../results/scatac-completion').resolve() / args.species
folds = ({'train': ['1', '2', '3'], 'validation': ['4'], 'test': ['5']}
         if args.species == 'arabidopsis'
         else {'train': [f'Chr{i:02}' for i in range(1, 9)], 'validation': ['Chr09'], 'test': ['Chr10']})
for target, sha in MODELS.items():
    config = {'schema_version': 1, 'target': target, 'model_sha': sha, 'folds': folds,
              'input_window': 2114, 'output_window': 1000, 'max_jitter': 0, 'controls': None,
              'background_method': 'gc-matched-genome-windows-v1', 'background_stride': 1000,
              'background_seed': 7,
              'experiment_label': 'SENSITIVITY: model background windows with explicit 1000 bp stride; full positive contexts excluded; chromosome folds unchanged',
              'bias_model': {'status': 'REQUIRED_BEFORE_TRAINING', 'plant_model': None}
              if target == 'chrombpnet' else None}
    path = root / 'model-config' / (target + '.json')
    existed = path.exists()
    if existed:
        assert load(path) == config, 'Existing model configuration differs; do not overwrite it'
    else:
        dump(path, config)
    print(json.dumps({'target': target, 'path': str(path), 'sha256': digest(path),
                      'reused_unchanged': existed}), flush=True)
