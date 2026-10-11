# Plant Data Sets workbook inventory

Update (2026-10-10): the user-specified Google workbook export is now available.
The [scATAC delivery audit](scatac-delivery-validation.md) records its checksum,
eight-tab snapshot and focused Arabidopsis/Sorghum inventory. The remaining text
is the historical missing-input observation. A full column-level audit of every
other worksheet remains outstanding.

## Historical observation

Status: **BLOCKED — required input absent**. The specified `inputs/Plant Data Sets.xlsx` is not present in this validation workspace. No substitute workbook was used or downloaded.

No worksheet counts, missingness, accession groupings, candidate ranks or biological-replicate reconstructions can be asserted without the source workbook. All tabs must be audited after the exact file is supplied, preserving its SHA256 and original bytes. An experiment accession will not be treated as a biological replicate or model training example.

Required resumption: read every sheet; produce column-level missingness and duplicate/accession checks; preserve original species/assay/label strings; inspect Arabidopsis and Sorghum scATAC studies for FASTQ/BAM/fragments/labels/multiome availability; rank readiness only from evidence. No bulk downloading is authorized by the inventory audit. `results/metadata-audit/status.json` records this prerequisite explicitly.
