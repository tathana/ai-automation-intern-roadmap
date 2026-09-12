"""Educational SQLite job store showing idempotent enqueue and atomic claim."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sqlite3
import time


def canonical(value: dict) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


class PayloadConflict(ValueError):
    pass


class JobStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs(
                  id INTEGER PRIMARY KEY,
                  event_id TEXT NOT NULL UNIQUE,
                  payload_hash TEXT NOT NULL,
                  payload TEXT NOT NULL,
                  state TEXT NOT NULL DEFAULT 'queued',
                  created REAL NOT NULL,
                  claimed REAL
                );
                CREATE TABLE IF NOT EXISTS audit(
                  id INTEGER PRIMARY KEY,
                  job_id INTEGER NOT NULL REFERENCES jobs(id),
                  action TEXT NOT NULL,
                  at REAL NOT NULL
                );
                """
            )

    @contextmanager
    def connection(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def enqueue(self, event_id: str, payload: dict, now: float | None = None) -> tuple[int, bool]:
        raw = canonical(payload)
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        timestamp = time.time() if now is None else now
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            old = connection.execute("SELECT id,payload_hash FROM jobs WHERE event_id=?", (event_id,)).fetchone()
            if old:
                if old["payload_hash"] != digest:
                    raise PayloadConflict("same_event_different_payload")
                return old["id"], True
            job_id = connection.execute(
                "INSERT INTO jobs(event_id,payload_hash,payload,created) VALUES (?,?,?,?)",
                (event_id, digest, raw, timestamp),
            ).lastrowid
            connection.execute("INSERT INTO audit(job_id,action,at) VALUES (?,?,?)", (job_id, "enqueued", timestamp))
            return int(job_id), False

    def claim(self, now: float | None = None) -> dict | None:
        timestamp = time.time() if now is None else now
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM jobs WHERE state='queued' ORDER BY id LIMIT 1").fetchone()
            if row is None:
                return None
            changed = connection.execute(
                "UPDATE jobs SET state='processing',claimed=? WHERE id=? AND state='queued'", (timestamp, row["id"])
            ).rowcount
            if changed != 1:
                return None
            connection.execute("INSERT INTO audit(job_id,action,at) VALUES (?,?,?)", (row["id"], "claimed", timestamp))
            return {**dict(row), "payload": json.loads(row["payload"]), "state": "processing", "claimed": timestamp}

    def list_jobs(self) -> list[dict]:
        with self.connection() as connection:
            return [dict(row) for row in connection.execute("SELECT id,event_id,state,created,claimed FROM jobs ORDER BY id")]


def main() -> int:
    parser = argparse.ArgumentParser(description="Educational local SQLite job store")
    parser.add_argument("--db", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    enqueue = sub.add_parser("enqueue")
    enqueue.add_argument("event_id")
    sub.add_parser("claim")
    sub.add_parser("list")
    args = parser.parse_args()
    store = JobStore(args.db)
    try:
        result = store.enqueue(args.event_id, {"event_id": args.event_id}) if args.command == "enqueue" else store.claim() if args.command == "claim" else store.list_jobs()
    except PayloadConflict as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2
    print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
