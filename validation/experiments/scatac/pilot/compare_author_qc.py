"""Compare like-for-like author QC; retain incompatible denominators explicitly."""
from pathlib import Path
import csv,json,math,statistics,time,hashlib
base=Path('../results/scatac-completion').resolve()
author=Path('../results/scatac-pilot/sources/GSE155304/author-cells.tsv').resolve()
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def distribution(values):
 values=sorted(values)
 return {'n':len(values),'min':values[0] if values else None,'median':statistics.median(values) if values else None,'max':values[-1] if values else None}
rows=list(csv.DictReader(author.open(),delimiter='\t'));selected={}
for r in rows:
 lib='GSM4698760' if r['lib']=='g10' else 'GSM4698761';assert r['lib'] in ['g10','n5']
 barcode=r['barcode'][2:] if r['lib']=='g10' else r['barcode'];key=(lib,barcode);assert key not in selected;selected[key]=r
observed={};inputs={str(author):sha(author)}
for i in [1,2]:
 p=base/'arabidopsis'/f'ingested-{i}'/'barcodes.tsv';inputs[str(p)]=sha(p)
 for r in csv.DictReader(p.open(),delimiter='\t'):
  key=(f'GSM469876{i-1}',r['barcode'])
  if key in selected:observed[key]=r
assert set(observed)==set(selected)
comparisons=[]
for k,r in selected.items():
 x=observed[k];passed=int(r['passed_filters']);peak=int(r['peak_region_fragments']);total=int(r['total']);observed_n=int(x['unique_fragments'])
 comparisons.append({'library_id':k[0],'barcode':k[1],'author_passed_filters':passed,'retained_fragment_rows':observed_n,'delta':observed_n-passed,'author_peak_region_fragments':peak,'author_total':total,'author_named_pct_reads_in_peaks':float(r['pct_reads_in_peaks']),'author_peak_over_total':100*peak/total,'author_peak_over_passed':peak/passed,'source_duplicate_fraction':int(r['duplicate'])/total,'source_mitochondrial_fraction':int(r['mitochondrial'])/total,'source_lowmapq_fraction':int(r['lowmapq'])/total,'author_nucleosome_signal':float(r['nucleosome_signal'])})
with (base/'arabidopsis-author-qc.tsv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(comparisons[0]),delimiter='\t');w.writeheader();w.writerows(comparisons)
summary={'arabidopsis':{'source_cells':len(rows),'fragment_count_exact_matches':sum(x['delta']==0 for x in comparisons),'fragment_count_deltas':distribution([x['delta'] for x in comparisons]),'author_passed_filters_sum':sum(x['author_passed_filters'] for x in comparisons),'retained_fragment_rows_sum':sum(x['retained_fragment_rows'] for x in comparisons),'pct_reads_in_peaks_uses_total_denominator_matches':sum(math.isclose(x['author_named_pct_reads_in_peaks'],x['author_peak_over_total'],rel_tol=1e-10,abs_tol=1e-10) for x in comparisons),'metrics':{k:distribution([x[k] for x in comparisons]) for k in ['author_named_pct_reads_in_peaks','author_peak_over_passed','source_duplicate_fraction','source_mitochondrial_fraction','source_lowmapq_fraction','author_nucleosome_signal']},'interpretation':['Published pct_reads_in_peaks uses total, not passed fragments, as denominator.','Genesis group FRiP uses newly called group peaks, so it is not an exact comparison with author library peak sets.','Author retained fragment files have no organellar rows; original mitochondrial counts remain source QC.','No equivalent source TSS-enrichment score found; TSS_fragments is a count, not enrichment.']},'inputs_sha256':inputs,'plant_thresholds':'UNSPECIFIED'}
(base/'provenance/author-qc-comparison.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
print(json.dumps(summary),flush=True)
