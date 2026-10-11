# Two-species pilot reproduction

These experiment and inspection helpers are preserved with SHA256 checksums.
Execution receipts identify which commands ran and their outcomes. They are not
an additional production CLI. Supported commands are documented in
[scATAC processing](../../../../docs/usage/scatac.md).

Use a validation workspace with this checkout at `repo/`, pinned model repositories
at `benchmarks/`, and data outside Git under `results/`. Copy the helpers unchanged
to `scratch/scatac-completion/` and run them from `repo/`. The scripts deliberately
refuse to overwrite completed acquisition/processing directories. Start with a
new workspace for an independent reproduction.

The execution receipts give exact download URLs, arguments and input paths.
Read `validation/reports/scatac-completion.md` before downloading data. This pilot
uses substantial disk and compute resources; its resource budget is not a default
for ordinary fragment ingestion.

1. Install the project's frozen Pixi/uv environment. Create the raw-read environment
   with project micromamba and
   `validation/environments/scatac-raw-pilot-linux-64.lock` at
   `scratch/scatac-completion/raw-env`. The inspection environment has a separate
   explicit lock. Existing `pigz 2.8` is used for deterministic FASTQ compression.
2. Fetch the declared source assets with `fetch.py`, retaining receipt files.
   Extract author annotations with the R helpers in the pinned QC container.
   `prepare_arabidopsis.py` and `prepare_sorghum.py` produce explicit cell,
   reference, annotation and processing manifests. Review these before execution.
3. Ingest both Arabidopsis libraries with `ingest_library.py` and then run
   `run_arabidopsis_core.py`. The wrapper tests stable resume after each stage.
4. For the separately labeled Sorghum sensitivity experiment,
   `prepare_sorghum_runs.py` establishes the five SRA run identities;
   `acquire_sra.py` validates their public checksums. Run `extract_sra.py` once per
   accession. Preserve all four read roles, including the barcode read.
5. Obtain the paired public ATAC/GEX whitelists. `barcode_sorghum.py` records their
   translation, orientation and author-library matches. Build the pinned Chromap
   index from the declared v3.0.1 reference. Run `map_sorghum.py SRX22683056`
   with four threads and `map_sorghum_retry.py SRX22683080` with eight threads
   and a 40 GiB address-space limit.
   The initial four-thread second-replicate attempt was interrupted to reuse CPUs
   after regression tests finished; its logs remain in the original run evidence.
   The 24 GiB attempt aligned all reads but failed during final merging with
   `std::bad_alloc`. The retry preserves the same scientific settings and inputs.
6. `run_sorghum_core.py` ingests both reconstructions and creates separate
   cell-type/replicate products. The raw-read reconstruction is not the author
   Cell Ranger pipeline and does not change Genesis production defaults.
7. `run_models.py arabidopsis` exports both pinned model formats and validates the
   real loaders. Run `prepare_model_configs.py sorghum` to create the same frozen
   model configurations without starting a serial validation run. Then
   `run_models_parallel.py sorghum` completes independent groups with three worker
   processes, then performs registry validation and replicate comparisons serially.
   The serial Sorghum attempt was intentionally stopped without a child process
   running; completed bundles and loader receipts are reused by verified resume.
   Its exit status and the transition receipt are preserved. Chromosome folds,
   GC backgrounds and scientific parameters stay identical.
8. `audit_pilot.py` independently reconciles library barcode totals, cell membership,
   pseudobulk totals and bigWig sums. Assemble a candidate using the supported
   `genesis scatac release` command and its explicit group manifest.

`assemble_pilot.py` applies that final gate after both species finish. The native
producer's 255-support cap is tested separately; `audit_chromap_support.py` counts
real rows at the cap without modifying any fragment. The `*_v1.py` / `*_v2.py`
files preserve earlier orchestration/preparation attempts. Use the unversioned
helpers for the final path. In particular, producer version capture includes
Chromap's stderr, and each library can start ingestion as soon as its mapping
receipt is complete.

`validate_portable_pilot.py` then tests both model loaders against copied release
bundles. `audit_resources.py` records the final resource snapshot;
`summarize_pilot.py` collects compact evidence, and `finish_report.py`
derives the report's counts and ranges from those observations. Neither records
scientific approval. The additional atlas inspection retrieves public code and
archive metadata only; it does not download the atlas's sequencing files.
`final_review.py` checks the completed acceptance receipts, source freeze,
publication file sizes, credential patterns and documentation links. It does not
rerun biological processing or replace the full regression suite.

`record.py` wraps commands with complete stdout/stderr and GNU time measurements.
Its receipt records the starting Git SHA and scATAC source hashes. The diff hash
is taken at completion and does not include untracked files; it must not be used
alone to infer that an early development run used a clean checkout. Scientific
stage manifests and the archived source hashes provide the implementation identity.

Model-loader success does not establish biological suitability or successful
training. Preserve missing QC as null, keep biological replicates separate, and
complete the existing metadata/QC/eligibility reviews before release approval.
