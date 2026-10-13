import json
from pathlib import Path

report = json.loads(Path("multiqc_data/multiqc_data.json").read_text())
raw = report["report_saved_raw_data"]
required = [
    "multiqc_fastqc",
    "multiqc_samtools_flagstat",
    "multiqc_samtools_stats",
    "multiqc_samtools_idxstats",
]
missing = [key for key in required if not raw.get(key)]
assert not missing, f"Missing expected MultiQC data: {missing}; present={list(raw)}"
assert len(raw["multiqc_fastqc"]) == 2
Path("required-modules.json").write_text(
    json.dumps(
        {"required": required, "sample_counts": {k: len(raw[k]) for k in required}}, indent=2
    )
    + "\n"
)
