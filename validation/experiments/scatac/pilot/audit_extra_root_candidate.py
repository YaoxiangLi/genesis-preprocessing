"""Quantify deposited Arabidopsis candidate metadata without inventing cell labels."""
from pathlib import Path
from collections import Counter
import csv, datetime, hashlib, json

root = Path(__file__).resolve().parents[2]
base = root / 'results/scatac-completion'
source = base / 'sources/GSE299784/author-cells.tsv'
with source.open() as stream:
    rows = list(csv.DictReader(stream, delimiter='\t'))
assert len(rows) == 14466
assert len({r['barcode'] for r in rows}) == len(rows)
clusters = Counter(r['seurat_clusters'] for r in rows)
libraries = Counter(r['dataset'] for r in rows)
assert all(label.isdigit() for label in clusters)
assert len(clusters) == 18 and set(libraries) == {'atac_1', 'atac_2'}
receipt = json.loads((base / 'sources/GSE299784/atlas.RDS.receipt.json').read_text())
soft = root / 'results/scatac-discovery/sources/GSE299784.soft'
result = {'retrieved_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'study': 'GSE299784', 'source_url': 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE299784',
          'source_object_sha256': receipt['sha256'],
          'metadata_tsv_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'series_snapshot_sha256': hashlib.sha256(soft.read_bytes()).hexdigest(),
          'deposited_cell_records': len(rows), 'cells_by_deposited_library_label': dict(libraries),
          'cells_by_numeric_cluster': dict(sorted(clusters.items(), key=lambda x: int(x[0]))),
          'available_source_qc_fields': [name for name in rows[0] if name in (
              'total', 'duplicate', 'chimeric', 'unmapped', 'lowmapq', 'mitochondrial',
              'passed_filters', 'TSS.enrichment', 'nucleosome_signal', 'pct_reads_in_peaks')],
          'author_cell_type_crosswalk': None,
          'readiness': 'NEEDS_METADATA',
          'reason': 'Numeric ATAC clusters have no verified author cell-type mapping. RNA atlas cluster numbers cannot be substituted across independent assays.',
          'new_sequencing_data_downloaded': False,
          'pilot_included': False}
(base / 'provenance/extra-root-candidate-audit.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps({k: result[k] for k in ['study', 'deposited_cell_records', 'cells_by_deposited_library_label', 'readiness']}, indent=2))
