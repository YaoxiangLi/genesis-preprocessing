"""Real pinned-container acceptance test for fragment-derived signal and peaks."""

from __future__ import annotations

import argparse
from pathlib import Path

from genesis_tools.contracts.records import canonical, dump, load
from genesis_tools.scatac import ingest, products, pseudobulk
from genesis_tools.scatac.common import digest
from verify_scatac_fragments import inputs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--numeric-chromosomes", action="store_true")
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    fixture, manifests = inputs(root)
    config = load(manifests[0])
    library = config["library"]
    chromosomes = ("1", "2", "3") if args.numeric_chromosomes else ("chr1", "chr2", "chr3")
    fasta = root / "reference.fa"
    fasta.write_text("".join(f">{c}\n" + "ACGT" * 12500 + "\n" for c in chromosomes))
    config["reference"].update(
        fasta={"path": str(fasta), "sha256": digest(fasta)},
        contigs={c: 50000 for c in chromosomes},
    )
    library["reference_fasta_sha256"] = digest(fasta)
    cells = [c for c in fixture["cells"] if c["library_id"] == library["library_id"]]
    cell = cells[0]
    fragments = root / "input.tsv"
    # 300 distinct molecules at each locus. Support is deliberately >1.
    fragments.write_text(
        "".join(
            f"{chrom}\t{10000 + i}\t{10200 + i}\t{cell['barcode']}\t3\n"
            for chrom in chromosomes
            for i in range(300)
        )
    )
    config["fragments"] = {"path": str(fragments), "sha256": digest(fragments)}
    dump(root / "input.json", config)
    (root / "cells.jsonl").write_text(canonical(cell) + "\n")
    dump(
        root / "policy.json",
        {
            "schema_version": 1,
            "version": "real-tools-fixture-v1",
            "signal_convention": "chrombpnet-atac-v1",
            "organellar": "retain",
            "boundary_cuts": "error",
            "independent_library_merges": [],
            "peak_calling": {
                "qvalue": 0.05,
                "effective_genome_sizes": {library["reference_id"]: 150000},
            },
        },
    )
    original = digest(fragments)
    ingest.run(root / "input.json", root / "ingested")
    pseudobulk.aggregate(
        [root / "ingested"], root / "cells.jsonl", root / "policy.json", root / "groups"
    )
    groups = load(root / "groups/complete.json")["data"]["groups"]
    assert len(groups) == 1
    group_id = next(iter(groups))
    result = products.run(root / "groups" / group_id, root / "products")
    data = result["manifest"]["data"]
    assert data["group"]["unique_fragments"] == 900
    assert data["group"]["total_support"] == 2700
    assert data["group"]["cut_count"] == 1800
    assert data["qc"]["peak_count"] == 3
    assert data["qc"]["frip"] == 1.0
    assert products.run(root / "groups" / group_id, root / "products", resume=True)["cached"]
    repeat = products.run(root / "groups" / group_id, root / "products-repeat")
    assert result["manifest"]["outputs"] == repeat["manifest"]["outputs"]
    assert digest(fragments) == original
    print("PASS: real bigWig counts, three peaks, exact FRiP, resume and byte-identical outputs")


if __name__ == "__main__":
    main()
