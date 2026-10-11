"""Fill the real-pilot report with measured final evidence, not inferred success."""
from pathlib import Path
from collections import Counter
import json

root=Path(__file__).resolve().parents[2]
base=root/'results/scatac-completion'
evidence=root/'repo/validation/evidence/scatac-completion'
summary=json.loads((evidence/'summary.json').read_text())
counts=json.loads((evidence/'independent-conservation.json').read_text())
assert summary['release_acceptance']['computational_acceptance']=='PASS'
assert json.loads((base/'portable-release-acceptance.json').read_text())['status']=='PASS'
lines=['## Real pilot results','','All 24 cell-type/replicate groups passed structural validation, both actual model',
       'loaders and stable resume. Each species contributes six cell types from two',
       'biological replicates. An independent audit reconciled every ingested fragment',
       'and supporting pair with selection/exclusion totals, group membership, cut counts',
       'and bigWig sums.','','| Species | Source cells | Included cells | Selected unique fragments | Read-pair support | Groups |',
       '| --- | ---: | ---: | ---: | ---: | ---: |']
for species,title in [('arabidopsis','Arabidopsis'),('sorghum','Sorghum')]:
    d=summary['species'][species];c=counts[species]
    lines.append(f"| {title} | {c['source_cells']:,} | {d['cells']:,} | {d['unique_fragments']:,} | {d['support']:,} | {d['groups']} |")
lines+=['','| Fragment conservation | Arabidopsis | Sorghum |','| --- | ---: | ---: |']
for field,label in [('input_fragments','Ingested unique fragments'),('input_support','Ingested read-pair support'),
                    ('excluded_unannotated','Fragments without an author-selected cell'),
                    ('excluded_cell_policy','Fragments from explicitly excluded cell labels')]:
    lines.append('| '+label+' | '+' | '.join(f"{counts[s]['counts'].get(field,0):,}" for s in ['arabidopsis','sorghum'])+' |')
lines.append('| Source cell barcodes absent from ingested fragments | '+' | '.join(str(len(counts[s]['missing_source_cell_barcodes'])) for s in ['arabidopsis','sorghum'])+' |')
cap=json.loads((base/'provenance/chromap-support-audit.json').read_text())
assert all(v['counts']['rows_at_255']==0 for v in cap.values())
lines+=['','All four inputs retain their supplied coordinates and support during ingestion.',
        'A separate scan of both native Sorghum outputs found zero records at Chromap\'s',
        '255-support cap. The producer limit was reproduced on a deterministic fixture,',
        'but no capped support was observed in these two real libraries.']
lines+=['','| Observed range across groups or matched replicate pairs | Arabidopsis | Sorghum |',
        '| --- | ---: | ---: |']
for field,label in [('peaks','Peaks per group'),('frip','Group fragment-based FRiP'),
                    ('tss_enrichment','Declared gene-TSS enrichment'),
                    ('support_redundancy_fraction','Support redundancy fraction'),
                    ('peak_base_jaccard','Replicate peak-base Jaccard'),
                    ('pearson_nonzero_union','Replicate signal Pearson, nonzero-union bins'),
                    ('spearman_nonzero_union','Replicate signal Spearman, nonzero-union bins')]:
    values=[]
    for species in ['arabidopsis','sorghum']:
        d=summary['species'][species][field]
        values.append('UNAVAILABLE' if not d['n'] else (f"{d['min']:,.0f}–{d['max']:,.0f}" if field=='peaks' else f"{d['min']:.4f}–{d['max']:.4f}"))
    lines.append('| '+label+' | '+' | '.join(values)+' |')
lines+=['','These ranges describe this pilot. They are not acceptance thresholds or evidence',
        'that a cell type is biologically good or bad. Replicate comparisons use identical',
        '1,000 bp bins; the full table also retains all-bin correlations.',
        'Library depth, read length, peak calling and annotation choices can affect these values.',
        'Sorghum peak-set agreement varies substantially across cell types. The',
        '[replicate table](../evidence/scatac-completion/replicate-qc.tsv) places each comparison',
        'beside cell counts and fragment depth for review before selecting training tasks.','']
models=json.loads((evidence/'models.json').read_text())
lines+=['Model exports use Arabidopsis chromosomes 1–3 / 4 / 5 and Sorghum',
        'chromosomes Chr01–Chr08 / Chr09 / Chr10 for train / validation / test.',
        'Each input window is 2,114 bp, each signal window is 1,000 bp, and jitter is zero.',
        'Unplaced contigs remain in the reference and scientific products but are excluded',
        'from these declared model folds. Boundary-window exclusions are also counted.',
        'The explicit 1,000 bp background stride retains one distinct background per peak.','',
        '| Model preparation totals across groups | Arabidopsis | Sorghum |',
        '| --- | ---: | ---: |']
matched={}
for m in models:
    key=(m['species'],m['task_id'])
    regions={k:v for k,v in m['manifest']['outputs'].items() if k.endswith('.bed') or k=='backgrounds.json'}
    if key in matched:assert regions==matched[key]
    matched[key]=regions
aggregates={}
for species in ['arabidopsis','sorghum']:
    a=Counter()
    for m in models:
        if m['species']!=species or m['target']!='cherimoya':continue
        d=m['manifest']['data'];a.update(d['excluded_peaks'])
        for fold in m['backgrounds']['folds'].values():
            a['backgrounds']+=fold['selected']
            a['exact_gc_bin']+=fold['gc_percentage_point_differences'].get('0',0)
    aggregates[species]=a
for key,label in [('boundary_window','Peak records excluded at context boundaries'),
                  ('unassigned_chromosome','Peak records outside declared folds'),
                  ('backgrounds','Selected background windows'),('exact_gc_bin','Backgrounds matched in the exact 1% GC bin')]:
    lines.append('| '+label+' | '+' | '.join(f"{aggregates[s][key]:,}" for s in ['arabidopsis','sorghum'])+' |')
lines+=['','Both model adapters produced the same region selections under these settings.',
        'The 48 loader tests each checked a positive and a background window in all three',
        'folds: 288 sequence/signal examples, compared base by base with the exact FASTA',
        'and bigWig. Four further loader tests passed on copied release bundles, one per',
        'species and model, with verified resume. This is data-loading acceptance, not training.','',
        'The portable candidate is `results/scatac-completion/genesis-scatac-pilot-v1/`.',
        'It contains source-library manifests, cell membership, fragments, peaks, tracks,',
        'both model bundles, QC, loader receipts, source evidence and checksums.',
        'Its registry correctly retains `model_ready: false`: metadata, QC and eligibility',
        'review are still unapproved. The [handoff checklist](../../docs/usage/scatac-model-handoff.md)',
        'states the remaining modeling-group decisions.','',
        'Compact measured evidence is committed under',
        '[validation/evidence/scatac-completion](../evidence/scatac-completion/README.md).',
        'Full logs, per-cell tables and large artifacts remain outside Git.']
section='\n'.join(lines)+'\n'
path=root/'repo/validation/reports/scatac-completion.md';text=path.read_text()
start='<!-- REAL_PILOT_RESULTS -->';end='<!-- END_REAL_PILOT_RESULTS -->'
assert text.count(start)==text.count(end)==1
before,rest=text.split(start);_,after=rest.split(end)
path.write_text(before+start+'\n'+section+end+after)
(base/'report-section.md').write_text(section)
resources=json.loads((base/'provenance/resource-accounting.json').read_text())
resource_lines=['| Species | Native mapping elapsed | Fragment ingestion, summed stage time | Pseudobulk aggregation elapsed |',
                '| --- | ---: | ---: | ---: |']
for species,title in [('arabidopsis','Arabidopsis'),('sorghum','Sorghum')]:
    rows=[r for r in resources['stages'] if r['species']==species]
    ingest=sum(r['elapsed_seconds'] for r in rows if '/ingested-' in r['path'])
    core=next(r['elapsed_seconds'] for r in rows if r['path'].endswith('/core/execution.json'))
    mapping='Author fragments; not rerun' if species=='arabidopsis' else ' / '.join(f"{r['elapsed_seconds']:.1f} s" for r in resources['native_mapping'])
    resource_lines.append(f'| {title} | {mapping} | {ingest:.1f} s | {core:.1f} s |')
resource_lines+=['','Stage times exclude prerequisite waiting. Summed ingestion times are work totals,',
                'not elapsed time for concurrent jobs. Each product and loader has its own timer',
                'in the compact resource evidence. Process memory is a high-water mark; it is',
                'not an incremental allocation for an individual stage.','',
                f"Verified major source downloads total {resources['verified_major_download_bytes']:,} bytes "
                f"({resources['verified_major_download_bytes']/1e9:.2f} GB). Reused Arabidopsis files, "
                'software, metadata, retries and transport overhead are outside this byte count.',
                f"The completion directory occupies {resources['storage'][0]['allocated_bytes']/1e9:.2f} GB "
                f"at this snapshot, with {resources['disk_free_bytes_after']/1e9:.2f} GB free on its filesystem.",
                'An exact pre-run disk snapshot was not retained; acquisition checked for more',
                'than 500 GB free. No exact before/after delta or total network traffic is claimed.']
text=path.read_text();start='<!-- RESOURCE_RESULTS -->';end='<!-- END_RESOURCE_RESULTS -->'
assert text.count(start)==text.count(end)==1
before,rest=text.split(start);_,after=rest.split(end)
path.write_text(before+start+'\n'+'\n'.join(resource_lines)+'\n'+end+after)
print(json.dumps({'status':'PASS','groups':24,'source':str(evidence/'summary.json'),'report':str(path)}))
