"""Validate independent model bundles with three bounded workers and serial registry writes."""
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import argparse, json
from genesis_tools.contracts.records import dump, load
from genesis_tools.contracts.validation import Budget
from genesis_tools.scatac import compare, loaders, model, registry

base = Path('../results/scatac-completion').resolve()


def validate_group(location):
    group = Path(location)
    root = group.parent.parent
    task = group.name
    targets = {}
    for target, sha in model.MODELS.items():
        config = root / 'model-config' / (target + '.json')
        settings = load(config)
        assert settings['model_sha'] == sha
        assert settings['background_method'] == 'gc-matched-genome-windows-v1'
        assert settings['background_stride'] == 1000
        bundle = root / 'models' / target / task
        validation = root / 'loader-validation' / target / task
        exported = model.export(group, config, bundle, resume=True)
        assert model.export(group, config, bundle, resume=True)['cached']
        assert model.validate(bundle)['context_windows'] == 'PASS'
        checked = loaders.run(bundle, Path('../benchmarks').resolve() / target, validation, resume=True)
        assert checked['manifest']['data']['loader_test'] == 'PASS'
        assert loaders.run(bundle, Path('../benchmarks').resolve() / target, validation, resume=True)['cached']
        targets[target] = {'bundle': str(bundle), 'validation': str(validation)}
        print(json.dumps({'stage': 'model-loader', 'species': root.name, 'task': task,
                          'target': target, 'status': 'PASS',
                          'reused_export': exported['cached'], 'reused_loader': checked['cached']}), flush=True)
    return {'products': str(group), 'models': targets}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('species', choices=['arabidopsis', 'sorghum'])
    args = parser.parse_args()
    root = base / args.species
    groups = sorted(p.parent for p in (root / 'products').glob('*/complete.json'))
    assert len(groups) == 12
    # Every worker owns distinct output directories. Existing configs remain read-only.
    with ProcessPoolExecutor(max_workers=3) as pool:
        items = list(pool.map(validate_group, map(str, groups)))
    pairs = {}
    for group in groups:
        task = group.name
        metadata = load(group / 'complete.json')['data']['group']
        pairs.setdefault(metadata['identity']['cell_type'], []).append(group)
        projected = registry.register(
            group, base / 'catalog', level='full',
            budget=Budget(max_bytes=20*1024**3, max_records=100_000_000, max_seconds=1800),
            bigwig_python=Path('validation/environments/scatac-loaders/.venv/bin/python').resolve())
        dump(root / 'registry' / (task + '.json'), projected)
        assert projected['validation']['data']['complete']
        assert all(f['data']['result'] == 'PASS' for f in projected['validation']['data']['findings'])
    for label, pair in pairs.items():
        assert len(pair) == 2
        dump(root / 'concordance' / (label + '.json'), compare.run(*pair, width=1000))
    dump(root / 'release-groups.json', items)
    print(json.dumps({'species': args.species, 'groups': len(items), 'models': 2*len(items),
                      'comparisons': len(pairs), 'workers': 3, 'status': 'PASS'}), flush=True)
