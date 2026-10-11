"""Attach observed pilot availability without inventing human approval."""
from pathlib import Path
import json
from genesis_tools.contracts.records import dump,load
from genesis_tools.scatac import evidence,inventory
base=Path('../results/scatac-completion').resolve()
root=Path('../results/scatac-discovery/inventory').resolve()
value=load(root/'evidence.json')
assets=load(base/'provenance/source-assets.json')
def source(suffix):
 matches=[x for x in assets if x['receipt'].endswith(suffix+'.receipt.json')]
 assert len(matches)==1
 a=matches[0]
 return {'url':a['url'],'sha256':a['sha256'],'retrieved_date':a['retrieved_utc'][:10]}
def finding(status,detail,*sources):
 return {'status':status,'review_status':'UNREVIEWED','detail':detail,'sources':list(sources)}
ara=value['studies']['PRJNA649267'];sor=value['studies']['PRJNA1046450']
ara['cell_annotations']=finding('AVAILABLE','All 4764 author nuclei retain original cluster labels; six cell classes follow published Figure 3C. Seven barcode metrics establish library membership. This is documented evidence, not human review.',source('farmer2021.pdf'),*ara['cell_annotations']['sources'])
ara['reference_compatibility']['detail']='Declared TAIR10 assembly; complete ingestion validates all intervals against the named Ensembl Plants 55 FASTA. Original author FASTA byte identity and exact Araport11 release remain unverified. Posthoc TSS annotation is a recorded sensitivity choice.'
rdata=source('GSE248919/combined.RData.gz');paper=source('sorghum2024.xml')
sor['cell_annotations']=finding('AVAILABLE','Author RData contains RNA-derived identities and explicit library/barcode membership. The selected two biological batches contain 2184 nuclei; 1406 have six known classes, 778 remain unknown and are not guessed.',rdata,paper)
sor['cell_barcodes']=finding('AVAILABLE','Author Signac fragment objects retain exact library-scoped barcode maps. Public paired ATAC/GEX whitelists establish explicit namespace translation for the raw-read reconstruction.',rdata)
sor['processed_matrices']=finding('AVAILABLE','Public combined RData inspected with the pinned R environment. Matrix availability does not replace fragment coordinates.',rdata)
sor['biological_replicates']=finding('AVAILABLE','Paper documents two biological replicates with technical libraries. Author library/batch identifiers select one technical library per biological replicate; GEO replicate 1/3 labels remain separate.',paper,rdata)
sor['fastq']=finding('AVAILABLE','Original public SRA objects for SRR26989999, SRR26990000, SRR26990001, SRR26990002 and SRR26989943 were checksum-verified and extracted with all four read roles. Ordinary ENA paired exports omit the barcode read.',*sor['fragments']['sources'])
sor['reference_compatibility']=finding('AVAILABLE','Exact named Sbicolor v3.0.1 FASTA and v3.1.1 GFF were retrieved from PlantGARDEN and checksum-pinned. These match author-declared releases; original author file bytes are not independently certified. No organellar contigs are declared.',source('Sbicolor_454_v3.0.1.fa.gz'),source('Sbicolor_454_v3.1.1.gene.gff3.gz'),paper)
sor['fragments']['detail']='No public author fragment endpoint verified; the author RData points to local paths. Genesis reconstructs fragments from public SRA under an explicit Chromap sensitivity policy. This is not author-fragment or Cell Ranger equivalence.'
p=base/'provenance/availability-evidence.json';dump(p,value)
attached=evidence.attach(root,p)
exported=inventory.export(root,base/'inventory-tables')
print(json.dumps({'attached':attached,'exported':exported}),flush=True)
