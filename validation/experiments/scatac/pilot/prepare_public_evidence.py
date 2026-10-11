"""Normalize publication TSV syntax while proving that every field is unchanged."""
from pathlib import Path
import csv
import datetime
import hashlib
import io
import json
import shutil

root = Path(__file__).resolve().parents[2]
base = root / "results/scatac-completion"
public = root / "repo/validation/evidence/scatac-completion"
originals = base / "publication/original-tsv"
originals.mkdir(parents=True, exist_ok=False)
records = []
for path in sorted(public.rglob("*.tsv")):
    original = path.read_bytes()
    rows = list(csv.reader(io.StringIO(original.decode(), newline=""), delimiter="\t"))
    destination = originals / path.relative_to(public)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(original)
    with path.open("w", newline="") as stream:
        csv.writer(stream, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_ALL).writerows(rows)
    published = path.read_bytes()
    assert list(csv.reader(io.StringIO(published.decode(), newline=""), delimiter="\t")) == rows
    records.append({"path": str(path.relative_to(public)), "records_including_header": len(rows),
                    "original_sha256": hashlib.sha256(original).hexdigest(),
                    "published_sha256": hashlib.sha256(published).hexdigest(),
                    "parsed_fields_unchanged": True})
result = {"status": "PASS", "captured_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
          "change": "Public copies use LF records and explicit field quoting. Raw results, release artifacts and all field values are unchanged.",
          "files": records}
path = base / "publication/tsv-normalization.json"
assert not path.exists()
path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
shutil.copyfile(path, public / "provenance/tsv-normalization.json")
shutil.copyfile(base / "publication/initial-whitespace-check.json",
                public / "provenance/publication-whitespace-observation.json")
print(json.dumps({"status": "PASS", "tables": len(records), "field_values_changed": 0}))
