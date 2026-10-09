"""Modality-specific inclusion preserves all barcode records and annotations."""
import copy,importlib.util,json
from pathlib import Path
root=Path(__file__).resolve().parents[2]
p=root/'fixtures/pseudobulk/contract.py';spec=importlib.util.spec_from_file_location('contract',p);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
fixture=json.loads((root/'fixtures/pseudobulk/fixture.json').read_text())
cases=[('both',True,True,True,True,'not-assessed'),('atac_only_pass',True,True,True,False,'not-assessed'),('rna_only_pass',True,True,False,True,'not-assessed'),('doublet',True,True,False,False,'flagged'),('missing_rna',True,False,True,False,'not-assessed')]
cells=[];fragments=[]
for name,ap,rp,ai,ri,doublet in cases:
 cell=dict(fixture['cells'][0],barcode=name,atac_present=ap,rna_present=rp,atac_include=ai,rna_include=ri,doublet_status=doublet,annotation_source='toy-author-RNA',author_original_label='Original A')
 cells.append(cell);fragments.append(dict(fixture['fragments'][0],barcode=name))
args={'libraries':[fixture['libraries'][0]],'cells':cells,'fragments':fragments}
groups=module.form_groups(**args)
assert len(cells)==5 and len(groups)==1
assert groups[0]['usable_fragments']==3
assert {c['barcode'] for c in groups[0]['cells']}=={'both','atac_only_pass','missing_rna'}
assert all(c['author_original_label']=='Original A' for c in cells)
# RNA inclusion is not allowed to alter ATAC pseudobulk selection.
changed=copy.deepcopy(args)
for c in changed['cells']:c['rna_include']=False
assert module.form_groups(**changed)[0]['fragments']==groups[0]['fragments']
(root/'fixtures/multiome/fixture.json').write_text(json.dumps(args,indent=2)+'\n')
(root/'results/contracts/multiome.json').write_text(json.dumps({'cells_preserved':5,'ATAC_usable_fragments':3,'RNA_policy_independence':True,'fixture':args,'groups':groups},indent=2)+'\n')
print('PASS: five modality cases, preserved identity and independent inclusion')
