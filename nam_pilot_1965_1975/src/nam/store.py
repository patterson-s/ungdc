"""Flat-file substrate: each table from nam_discourse_plan.md S3 is a JSONL file under
substrate/. Append-only tables (decisions, annotations, grid_versions, codes,
temporal_signatures, batches, questions) are only ever appended to; "updating" a question's
status means rewriting the file with that one record's status field changed -- the record's
identity and history are preserved in `decisions` regardless.

IDs are simple incrementing integers, derived from the current file's line count plus any
ids already seen this process (so two writes in the same run don't collide).
"""
import json
import threading
from pathlib import Path

_LOCK = threading.Lock()


class Store:
    def __init__(self, substrate_dir: Path):
        self.dir = Path(substrate_dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, table: str) -> Path:
        return self.dir / f"{table}.jsonl"

    def next_id(self, table: str) -> int:
        path = self._path(table)
        if not path.exists():
            return 1
        with open(path, encoding="utf-8") as f:
            return sum(1 for _ in f) + 1

    def append(self, table: str, record: dict) -> dict:
        with _LOCK:
            path = self._path(table)
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    def scan(self, table: str):
        path = self._path(table)
        if not path.exists():
            return
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)

    def filter(self, table: str, **kwargs):
        for record in self.scan(table):
            if all(record.get(k) == v for k, v in kwargs.items()):
                yield record

    def get(self, table: str, id_field: str, id_value):
        for record in self.scan(table):
            if record.get(id_field) == id_value:
                return record
        return None

    def rewrite_one(self, table: str, id_field: str, id_value, update: dict) -> dict:
        """Rewrite a single record in place (used only for `questions.status` /
        `answered_at` -- the question's content and history stay in `decisions`)."""
        with _LOCK:
            path = self._path(table)
            records = list(self.scan(table)) if path.exists() else []
            updated = None
            for r in records:
                if r.get(id_field) == id_value:
                    r.update(update)
                    updated = r
                    break
            if updated is None:
                raise KeyError(f"{table}: no record with {id_field}={id_value}")
            with open(path, "w", encoding="utf-8") as f:
                for r in records:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            return updated


def load_speeches(path: Path) -> dict:
    """speech_id -> full speech record, loaded once and kept in memory for the run."""
    speeches = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            speeches[r["speech_id"]] = r
    return speeches
