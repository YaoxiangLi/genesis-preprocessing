# Synthetic cell annotations

`cells.jsonl` reproduces the existing two-replicate, three-cell-type contract
fixture. These are synthetic identities, not real plant annotations. Run
`tests/verify_scatac_pseudobulk.py` for complete temporary library manifests and
exact expected counts. Run `tests/validate_scatac_products.py --output NEW_DIR`
for a persistent, three-chromosome fixture with real Docker peaks and tracks.
