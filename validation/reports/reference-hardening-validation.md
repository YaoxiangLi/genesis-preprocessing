# Reference provenance validation

Original baseline: `4468c712e4c171b573e2ec2806fdc5327b5379e9`. Combined validation HEAD before these edits: `65e522bb1f273d8c9145421fc40e63473aace7ad`; exact dirty source hashes, commands and full logs are retained under `results/incremental-prs/`. This change does not replace the original observations in audit/04.

Implemented: reject reference-ID collisions; record SHA256 provenance for chromosome sizes and all five bwa-mem2 index products; revalidate content and generator identity on every invocation. Stop on unverified caches and preserve their contents. Stage the checked-out validator in the existing pinned tools container. No dependency manifest, lock, alignment parameter, duplicate policy or peak parameter changed.

| Verification | Result | Evidence |
| --- | --- | --- |
| Collision regression before fix | Expected failure: ambiguous names accepted | collision-red |
| Collision focused and full checks | PASS | collision-green, collision-checks |
| Cache helper adversarial fixtures | PASS: changed content with same size/mtime, missing/damaged/extra products, mode, recipe, image, manifest mismatch | reference-focused, reference-final-checks |
| Full `pixi run checks` | PASS, 83.35 s | reference-final-checks |
| Full `pixi run validate-docker --keep` | PASS, 329.81 s | reference-final-docker |
| Real Docker negative cases | PASS: changed FASTA, absent provenance, damaged index, colliding reference IDs rejected before DOWNLOAD | reference-final-docker |
| Stable resume | PASS; validator reruns intentionally, downstream computation cached | retained Docker trace-stable-resume.tsv |
| Independent biological-output comparison | PASS on deterministic synthetic fixtures | results/completion/reference-final-scientific-comparison.json |

Retained final run: `repo/tests/.runs/docker-15u301c1`. Complete stdout/stderr, exit statuses, wall time and GNU time maximum RSS are in each evidence directory; RSS measures the launcher/process tree, not an independently sampled container peak. The retained fixture and all source/input hashes are the reproducibility record. Exact dependency/container versions are in audit/02 and FastQC/MultiQC reports; reference generation uses the unchanged digest-pinned alignment image. A tools-image build experiment succeeded locally but is not required by this implementation and was not pushed.

Output comparison checks raw FASTQ payloads, every published scientific output, and BAM headers/records/bytes. Gzip header and PDF creation/modification timestamps are reported separately from byte identity. The initial comparison invocation used a nonexistent Python path and exited 127; the corrected command uses the project's existing `genesis_tools/.venv/bin/python`. The initial check run found formatting errors, which were fixed using the project's format configuration; failed logs remain preserved.

Limits: no real Sorghum reference was touched; no assembly substitution occurred. Biological validity is unresolved on synthetic data. Large-reference hashing cost, concurrent reference mutation and Conda/Apptainer execution remain unmeasured. See design/adr-reference-identity.md for the explicit legacy-cache compatibility boundary.
