# Execution snapshot, 13 October 2026

This directory records the local comparison at the time in
[snapshot.json](snapshot.json). It is a dated handoff record, not a live status
page. At that observation, 48 of 136 planned method cases had completed their
common assessment: synthetic DAP, synthetic ATAC and public SE DAP at one million
templates. PE DAP was still processing. The complete ATAC workflow comparison is
recorded separately in [whole-workflows](../whole-workflows/).

The `.py.txt` files preserve the exact local batch commands as evidence. Their
absolute paths, process ownership checks and deadlines belong to this server.
Use the [portable recipe](../../../../benchmarks/experiments/plant-methods-20261013/README.md)
to reproduce the study elsewhere. Copying these files or cloning Git does not
transfer active processes, original reads, environments or temporary BAMs.

The local queues run these steps in order:

1. Finish three technical repetitions of PE DAP and Arabidopsis ATAC at one million
   templates. Preserve the result tables, logs and figures before pruning work.
2. Run each non-maize cohort at the five-million-template cap, once per method.
   Evaluate the SE DAP motifs and archive each completed cohort.
3. Prepare maize inputs only after all four original FASTQs have passed their
   publisher checksum checks. Run mapping and processing groups separately, with
   the same baseline in each group, after the other depth experiments finish.
4. Compare completed native Arabidopsis ATAC baseline observations with the
   production workflow. The comparison's result is still pending in this snapshot.

The scripts stop on failures; queued work must not be counted as successful.
`PROCESSED` means alignment/selection/calling finished for a case, before its common
assessment. Completed counts in the snapshot require `COMPLETE` results.
The shell command receipts only include commands that had returned when copied.

The active measurement checkout keeps the scientific source from `f35a4f9`.
Documentation and evidence commits do not change those source hashes. Installed
package and reporting fixes were tested and published through a separate worktree.
Do not merge those source changes into the active measurement checkout while its
queues are running. New development on another server can start from lab `main`.

`download-budget-accounting.json` reserves known package/image payloads and an
explicit allowance for other transfers. It is a conservative planning record,
not a measurement of all network traffic. The acquisition ledger measures source
payload bytes across attempts. Partial files remain unverified; only the final
source lock establishes complete acquisition.

When collecting later results, use a new dated observation. Preserve this record,
earlier failures and each experiment's original source identity. Update the
[comparison report](../../../reports/pipeline-method-comparison.md) only with
completed measurements and keep unfinished or failed cases visible.
