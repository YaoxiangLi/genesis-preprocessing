# Reference identity and reuse

Status: accepted for the local validation branch; not merged upstream. Scientific reference files are immutable for the duration of a run.

The baseline experiment in `audit/04-reference-cache-experiment.md` reproduced silent reuse of derived products after a FASTA was replaced at the same path. Filename existence cannot establish assembly identity. Distinct accepted suffixes also allowed two filenames to collapse to one cache ID; this now fails sample validation.

| Strategy | Benefit | Limitation | Decision |
| --- | --- | --- | --- |
| Filename identity | Existing layout, inexpensive lookup | Cannot detect replacement or ambiguous assembly names | Reject as sufficient evidence |
| Versioned registry | Human-readable provider, assembly, annotation and provenance | Metadata alone can be wrong | Prototype schema and checksum validation |
| Content identity | Detects byte changes independently of filenames | Streaming read cost; equivalent reformatting changes hash | Adopt decompressed FASTA SHA256 with product checksums |

For each chromosome-size file and bwa-mem2 index, write an atomic provenance manifest after successful generation. Record decompressed and compressed FASTA hashes, product hashes, actual generator version, configured container identity and generator recipe hash. Gzip-header and mtime changes do not invalidate sequence identity. Recipe changes conservatively invalidate products, including nonsemantic recipe edits. Stub products cannot be reused in real runs.

Validate on every invocation, including resume, before downloads. Missing, damaged, mismatched or unrecorded products cause a hard stop with instructions to preserve the files and regenerate in a fresh reference directory. There is no automatic overwrite, migration or repair of legacy caches. This intentionally changes compatibility for old reference directories, not alignment or peak policy. Truly absent products may be generated. Source validation is staged explicitly into the pinned dependency container so the checked-out validator is the one executed.

This is launch-time verification, not a distributed locking protocol. Concurrent modification during execution is unsupported; keep references immutable during a run. The configured container identity and actual tool versions are both recorded; Docker was tested, Conda and Apptainer were not revalidated here. Hashing large references and indexes adds sequential I/O; fixture timings do not predict large-genome overhead.

The registry prototype in `reference-schema.yaml` adds assembly/provider/masking/annotation/TSS/organellar identity. Aliases point to a canonical identity rather than creating duplicate assembly records. Annotation identity is separate from genome sequence identity: a changed annotation creates a different reference bundle. Missing biological annotations and plant thresholds are explicit, never inferred from filenames. The prototype is not connected to production metadata ingestion.

`processing-provenance-schema.yaml` separates run provenance from reference identity. The fixture validates a real contract-check event and explicitly distinguishes non-Nextflow validation from a Nextflow run; missing required run identity is rejected. Production adoption of this schema remains a separate integration.
