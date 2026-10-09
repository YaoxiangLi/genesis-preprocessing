"""Transactional SQLite storage and immutable scientific evidence."""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import os
import sqlite3
import time
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ..contracts.records import canonical, fingerprint, identity, loads, now, record, validate

SCHEMA_VERSION = 2
MIGRATIONS = {
    1: [
        "CREATE TABLE meta (key TEXT PRIMARY KEY,value TEXT NOT NULL)",
        (
            "CREATE TABLE records (kind TEXT,id TEXT,version TEXT,body TEXT "
            "NOT NULL,created TEXT NOT NULL,PRIMARY KEY(kind,id,version))"
        ),
        (
            "CREATE TRIGGER immutable_records_update BEFORE UPDATE ON records "
            "BEGIN SELECT RAISE(ABORT,'immutable record'); END"
        ),
        (
            "CREATE TRIGGER immutable_records_delete BEFORE DELETE ON records "
            "BEGIN SELECT RAISE(ABORT,'immutable record'); END"
        ),
        (
            "CREATE TABLE entities (id TEXT PRIMARY KEY,kind TEXT NOT "
            "NULL,source TEXT NOT NULL,original TEXT NOT NULL,study TEXT)"
        ),
        (
            "CREATE TABLE relations (parent TEXT REFERENCES "
            "entities(id),child TEXT REFERENCES entities(id),relation "
            "TEXT,PRIMARY KEY(parent,child,relation))"
        ),
        "CREATE TABLE workers (id TEXT PRIMARY KEY,configuration TEXT NOT NULL)",
        (
            "CREATE TABLE datasets (id TEXT PRIMARY KEY REFERENCES "
            "entities(id),name TEXT,assay TEXT,species TEXT,study "
            "TEXT,reference_id TEXT,worker TEXT REFERENCES "
            "workers(id),manifest TEXT NOT NULL,validation TEXT,metadata TEXT "
            "NOT NULL,assessment TEXT)"
        ),
        (
            "CREATE TABLE links (dataset TEXT REFERENCES datasets(id),kind "
            "TEXT,id TEXT,version TEXT,PRIMARY "
            "KEY(dataset,kind,id,version),FOREIGN KEY(kind,id,version) "
            "REFERENCES records(kind,id,version))"
        ),
        (
            "CREATE TABLE locations (dataset TEXT REFERENCES "
            "datasets(id),artifact TEXT,manifest TEXT,worker TEXT REFERENCES "
            "workers(id),path TEXT,sha256 TEXT,availability TEXT,role "
            "TEXT,PRIMARY KEY(dataset,artifact,manifest))"
        ),
        "CREATE INDEX locations_worker_path ON locations(worker,path)",
        "CREATE INDEX locations_digest ON locations(sha256)",
        "CREATE INDEX datasets_filters ON datasets(assay,species,study,reference_id)",
        (
            "CREATE TABLE imports (kind TEXT,id TEXT,version TEXT,imported "
            "TEXT,PRIMARY KEY(kind,id,version))"
        ),
        "CREATE TABLE campaigns (id TEXT PRIMARY KEY,body TEXT NOT NULL)",
        (
            "CREATE TABLE attempts (campaign TEXT REFERENCES "
            "campaigns(id),job TEXT,attempt INTEGER,worker TEXT,state "
            "TEXT,payload_hash TEXT,observed TEXT,PRIMARY "
            "KEY(campaign,job,attempt,observed))"
        ),
    ],
    2: [
        (
            "CREATE TABLE decisions (sequence INTEGER PRIMARY KEY "
            "AUTOINCREMENT,dataset TEXT REFERENCES datasets(id),category "
            "TEXT,action TEXT,version TEXT UNIQUE,body TEXT NOT NULL)"
        ),
        "CREATE INDEX decisions_target ON decisions(dataset,category,sequence DESC)",
        (
            "CREATE TRIGGER immutable_decisions_update BEFORE UPDATE ON "
            "decisions BEGIN SELECT RAISE(ABORT,'immutable decision'); END"
        ),
        (
            "CREATE TRIGGER immutable_decisions_delete BEFORE DELETE ON "
            "decisions BEGIN SELECT RAISE(ABORT,'immutable decision'); END"
        ),
    ],
}


def connect(directory: Path, *, readonly: bool = True) -> sqlite3.Connection:
    path = directory.resolve() / "registry.sqlite"
    db = sqlite3.connect(
        path.as_uri() + ("?mode=ro" if readonly else "?mode=rw"), uri=True, timeout=30
    )
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    version = db.execute("PRAGMA user_version").fetchone()[0]
    if version > SCHEMA_VERSION or version < 1:
        db.close()
        raise ValueError("Unsupported registry schema; use init to initialize/migrate")
    if readonly:
        db.execute("PRAGMA query_only=ON")
    return db


@contextlib.contextmanager
def lock(directory: Path) -> Iterator[None]:
    with (directory / "writer.lock").open("a") as stream:
        deadline = time.monotonic() + 30
        while True:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise ValueError(
                        "Registry writer is busy; retry after the current writer finishes"
                    ) from None
                time.sleep(0.05)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


@contextlib.contextmanager
def write(directory: Path) -> Iterator[sqlite3.Connection]:
    with lock(directory), contextlib.closing(connect(directory, readonly=False)) as db:
        if db.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION:
            raise ValueError("Run registry init to migrate before writing")
        with db:
            db.execute("BEGIN IMMEDIATE")
            yield db


def initialize(directory: Path) -> dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=True)
    with lock(directory), contextlib.closing(sqlite3.connect(directory / "registry.sqlite")) as db:
        db.execute("PRAGMA foreign_keys=ON")
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if version > SCHEMA_VERSION:
            raise ValueError("Registry was created by a newer Genesis")
        if version and version < SCHEMA_VERSION:
            backup_path = (
                directory / f"before-v{version}-to-v{SCHEMA_VERSION}-{time.time_ns()}.sqlite"
            )
            with contextlib.closing(sqlite3.connect(backup_path)) as destination:
                db.backup(destination)
        db.execute("PRAGMA journal_mode=WAL")
        with db:
            db.execute("BEGIN IMMEDIATE")
            for target in range(version + 1, SCHEMA_VERSION + 1):
                for sql in MIGRATIONS[target]:
                    db.execute(sql)
                db.execute(f"PRAGMA user_version={target}")
            db.execute("INSERT OR IGNORE INTO meta VALUES('registry_id',?)", (str(uuid.uuid4()),))
            try:
                db.execute(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS search_text USING fts5(id UNINDEXED,body)"
                )
                db.execute("INSERT OR REPLACE INTO meta VALUES('fts5','true')")
            except sqlite3.OperationalError:
                db.execute("INSERT OR REPLACE INTO meta VALUES('fts5','false')")
        registry_id = db.execute("SELECT value FROM meta WHERE key='registry_id'").fetchone()[0]
    return {
        "registry_id": registry_id,
        "schema_version": SCHEMA_VERSION,
        "directory": str(directory),
    }


def put(db: sqlite3.Connection, value: dict[str, Any], dataset: str | None = None) -> None:
    validate(value)
    db.execute(
        "INSERT OR IGNORE INTO records VALUES(?,?,?,?,?)",
        (value["kind"], value["id"], value["version"], canonical(value), now()),
    )
    if dataset:
        db.execute(
            "INSERT OR IGNORE INTO links VALUES(?,?,?,?)",
            (dataset, value["kind"], value["id"], value["version"]),
        )


def get(db: sqlite3.Connection, kind: str, version: str) -> dict[str, Any]:
    row = db.execute(
        "SELECT body FROM records WHERE kind=? AND version=?", (kind, version)
    ).fetchone()
    if not row:
        raise ValueError(f"Missing {kind} revision: {version}")
    return loads(row[0])


def current(db: sqlite3.Connection, dataset: str) -> dict[str, Any]:
    row = db.execute("SELECT * FROM datasets WHERE id=?", (dataset,)).fetchone()
    if not row:
        raise ValueError("Unknown dataset ID")
    return dict(row)


def entity(
    db: sqlite3.Connection, key: str, kind: str, source: str, original: str, study: str | None
) -> None:
    previous = db.execute("SELECT kind,source,original FROM entities WHERE id=?", (key,)).fetchone()
    if previous and tuple(previous) != (kind, source, original):
        raise ValueError("Entity ID collision across scientific sources or scopes")
    db.execute(
        "INSERT OR IGNORE INTO entities VALUES(?,?,?,?,?)", (key, kind, source, original, study)
    )


def import_bundle(directory: Path, value: dict[str, Any]) -> dict[str, int]:
    validate(value, "bundle")
    pairs = {
        (v["data"]["dataset_id"], v["data"]["manifest_version"]): v
        for v in value["data"]["validations"]
    }
    manifests = value["data"]["manifests"]
    if len({m["id"] for m in manifests}) != len(manifests):
        raise ValueError("An import bundle must contain one revision per dataset")
    if any(key not in {(m["id"], m["version"]) for m in manifests} for key in pairs):
        raise ValueError("Validation refers to a manifest outside this bundle")
    added = 0
    with write(directory) as db:
        if db.execute(
            "SELECT 1 FROM imports WHERE kind=? AND id=? AND version=?",
            (value["kind"], value["id"], value["version"]),
        ).fetchone():
            return {"imported": 0, "unchanged": len(manifests)}
        for manifest in manifests:
            data, dataset = manifest["data"], manifest["id"]
            if data["dataset_id"] != dataset:
                raise ValueError("Dataset identity differs from manifest identity")
            entity(db, dataset, "library", data["source_id"], data["library"], data["study"])
            for kind, raw in (
                ("study", data["study"]),
                ("biosample", data["biosample"]),
                ("reference", data["reference"]["id"]),
            ):
                if raw is not None:
                    key = identity(kind, data["source_id"], raw)
                    entity(db, key, kind, data["source_id"], raw, data["study"])
                    db.execute(
                        "INSERT OR IGNORE INTO relations VALUES(?,?,?)", (key, dataset, kind)
                    )
            for lane in data["lanes"]:
                key = identity("lane", dataset, str(lane.get("lane_id", fingerprint(lane))))
                entity(db, key, "lane", data["source_id"], canonical(lane), data["study"])
                db.execute("INSERT OR IGNORE INTO relations VALUES(?,?,'lane')", (dataset, key))
            db.execute("INSERT OR IGNORE INTO workers VALUES(?, '{}')", (data["worker"],))
            existing = db.execute("SELECT manifest FROM datasets WHERE id=?", (dataset,)).fetchone()
            validation = pairs.get((dataset, manifest["version"]))
            if not existing:
                db.execute(
                    "INSERT INTO datasets VALUES(?,?,?,?,?,?,?,?,?,?,NULL)",
                    (
                        dataset,
                        data["name"],
                        data["assay"],
                        data["species"],
                        data["study"],
                        data["reference"]["id"],
                        data["worker"],
                        manifest["version"],
                        validation["version"] if validation else None,
                        canonical(data["metadata"]),
                    ),
                )
            elif existing[0] != manifest["version"]:
                # Previously imported history must not roll the current dataset back.
                historical = db.execute(
                    "SELECT 1 FROM records WHERE kind='manifest' AND id=? AND version=?",
                    (dataset, manifest["version"]),
                ).fetchone()
                if historical:
                    raise ValueError(
                        "Historical revision import cannot replace the current manifest"
                    )
                db.execute(
                    (
                        "UPDATE datasets SET "
                        "name=?,assay=?,species=?,study=?,reference_id=?,worker=?,manifest"
                        "=?,validation=?,metadata=?,assessment=NULL WHERE id=?"
                    ),
                    (
                        data["name"],
                        data["assay"],
                        data["species"],
                        data["study"],
                        data["reference"]["id"],
                        data["worker"],
                        manifest["version"],
                        validation["version"] if validation else None,
                        canonical(data["metadata"]),
                        dataset,
                    ),
                )
            elif validation:
                db.execute(
                    "UPDATE datasets SET validation=? WHERE id=?", (validation["version"], dataset)
                )
            put(db, manifest, dataset)
            if validation:
                put(db, validation, dataset)
                for finding in validation["data"]["findings"]:
                    put(db, finding, dataset)
            for child in data["sources"] + data["measurements"]:
                put(db, child, dataset)
            for item in data["artifacts"]:
                db.execute("INSERT OR IGNORE INTO workers VALUES(?, '{}')", (item["worker"],))
                db.execute(
                    "INSERT OR IGNORE INTO locations VALUES(?,?,?,?,?,?,?,?)",
                    (
                        dataset,
                        item["id"],
                        manifest["version"],
                        item["worker"],
                        item["path"],
                        item["sha256"],
                        item["availability"],
                        item["role"],
                    ),
                )
            if db.execute("SELECT value FROM meta WHERE key='fts5'").fetchone()[0] == "true":
                db.execute("DELETE FROM search_text WHERE id=?", (dataset,))
                db.execute(
                    "INSERT INTO search_text VALUES(?,?)",
                    (dataset, canonical(data["metadata"]) + " " + data["name"]),
                )
            added += 1
        put(db, value)
        db.execute(
            "INSERT INTO imports VALUES(?,?,?,?)",
            (value["kind"], value["id"], value["version"], now()),
        )
    return {"imported": added, "unchanged": 0}


def import_campaign(directory: Path, campaign: Path) -> dict[str, Any]:
    """Read a consistent source snapshot, then release it before the registry transaction."""
    from ..contracts.records import load

    plan = load(campaign / "campaign.json")
    if plan.get("schema_version") != 1:
        raise ValueError("Unsupported campaign version")
    campaign_id = fingerprint(plan)
    with contextlib.closing(
        sqlite3.connect((campaign / "state.sqlite").resolve().as_uri() + "?mode=ro", uri=True)
    ) as source:
        source.row_factory = sqlite3.Row
        source.execute("BEGIN")
        jobs = [dict(row) for row in source.execute("SELECT * FROM jobs ORDER BY id")]
        events = [dict(row) for row in source.execute("SELECT * FROM events ORDER BY time")]
    snapshot_id = fingerprint({"plan": plan, "jobs": jobs, "events": events})
    with write(directory) as db:
        if db.execute(
            "SELECT 1 FROM imports WHERE kind='campaign' AND version=?", (snapshot_id,)
        ).fetchone():
            return {"imported": 0, "campaign_id": campaign_id}
        db.execute("INSERT OR IGNORE INTO campaigns VALUES(?,?)", (campaign_id, canonical(plan)))
        for key, worker in plan["workers"].items():
            old = db.execute("SELECT configuration FROM workers WHERE id=?", (key,)).fetchone()
            if old and old[0] not in {"{}", canonical(worker)}:
                raise ValueError("Worker identity reused for a different configuration")
            db.execute(
                (
                    "INSERT INTO workers VALUES(?,?) ON CONFLICT(id) DO UPDATE SET "
                    "configuration=excluded.configuration"
                ),
                (key, canonical(worker)),
            )
        for job in jobs:
            # Older attempts are not reconstructed from a current-state row.
            db.execute(
                "INSERT INTO attempts VALUES(?,?,?,?,?,?,?)",
                (
                    campaign_id,
                    job["id"],
                    job["attempt"],
                    job["worker"],
                    job["state"],
                    fingerprint(loads(job["payload"])),
                    now(),
                ),
            )
        db.execute(
            "INSERT INTO imports VALUES('campaign',?,?,?)", (campaign_id, snapshot_id, now())
        )
        evidence = record(
            "source",
            {
                "location": str(campaign.resolve()),
                "worker": "controller",
                "sha256": hashlib.sha256(
                    canonical({"jobs": jobs, "events": events}).encode()
                ).hexdigest(),
                "snapshot": canonical({"jobs": jobs, "events": events}),
                "media_type": "application/json",
            },
            identity("campaign-snapshot", campaign_id, snapshot_id),
        )
        put(db, evidence)
    return {"imported": len(jobs), "campaign_id": campaign_id}


def search(
    db: sqlite3.Connection,
    *,
    filters: dict[str, str] | None = None,
    text: str | None = None,
    after: str = "",
    limit: int = 100,
) -> list[dict[str, Any]]:
    if not 1 <= limit <= 1000:
        raise ValueError("Limit must be 1–1000")
    where, parameters = ["d.id > ?"], [after]
    for key, value in (filters or {}).items():
        if key in {"species", "assay", "study", "reference_id", "worker"}:
            where.append(f"d.{key}=?")
        elif key == "availability":
            where.append(
                "EXISTS(SELECT 1 FROM locations l WHERE l.dataset=d.id AND "
                "l.manifest=d.manifest AND l.availability=?)"
            )
        elif key == "biological_context":
            where.append("d.metadata LIKE ? ESCAPE '\\'")
            value = "%" + value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        else:
            raise ValueError(f"Unsupported filter: {key}")
        parameters.append(value)
    if text:
        if db.execute("SELECT value FROM meta WHERE key='fts5'").fetchone()[0] == "true":
            where.append("d.id IN (SELECT id FROM search_text WHERE search_text MATCH ?)")
            parameters.append('"' + text.replace('"', '""') + '"')
        else:
            where.append("(d.name || ' ' || d.metadata) LIKE ? ESCAPE '\\'")
            parameters.append(
                "%" + text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
            )
    return [
        dict(row)
        for row in db.execute(
            "SELECT d.* FROM datasets d WHERE " + " AND ".join(where) + " ORDER BY d.id LIMIT ?",
            [*parameters, limit],
        )
    ]


def history(
    db: sqlite3.Connection, dataset: str, *, limit: int = 100, after: int = 0
) -> list[dict[str, Any]]:
    if not 1 <= limit <= 1000 or after < 0:
        raise ValueError("Invalid history pagination")
    return [
        loads(row[0])
        for row in db.execute(
            (
                "SELECT r.body FROM records r JOIN links l USING(kind,id,version) "
                "WHERE l.dataset=? ORDER BY r.created,r.kind,r.id,r.version LIMIT "
                "? OFFSET ?"
            ),
            (dataset, limit, after),
        )
    ]


def export_bundle(db: sqlite3.Connection, datasets: list[str]) -> dict[str, Any]:
    manifests, validations = [], []
    for dataset in sorted(set(datasets)):
        row = current(db, dataset)
        manifests.append(get(db, "manifest", row["manifest"]))
        if row["validation"]:
            validations.append(get(db, "validation", row["validation"]))
    data = {"manifests": manifests, "validations": validations}
    return record("bundle", data, identity("bundle", fingerprint(data)))


def backup(directory: Path, destination: Path) -> None:
    if destination.exists():
        raise ValueError("Backup destination already exists")
    temporary = destination.with_name(destination.name + ".partial-" + uuid.uuid4().hex)
    try:
        with (
            contextlib.closing(connect(directory)) as source,
            contextlib.closing(sqlite3.connect(temporary)) as target,
        ):
            source.backup(target)
            if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Backup integrity check failed")
        os.link(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def restore(source: Path, directory: Path) -> None:
    if directory.exists():
        raise ValueError("Restore requires a new destination directory")
    with contextlib.closing(
        sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)
    ) as db:
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if (
            not 1 <= version <= SCHEMA_VERSION
            or db.execute("PRAGMA integrity_check").fetchone()[0] != "ok"
            or db.execute("PRAGMA foreign_key_check").fetchall()
        ):
            raise ValueError("Backup has an unsupported schema or failed integrity checks")
        directory.mkdir(parents=True)
        with contextlib.closing(sqlite3.connect(directory / "registry.sqlite")) as target:
            db.backup(target)
