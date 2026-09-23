"""I4 — async event bus with SQLite WAL outbox, idempotent delivery, watermarks."""
from __future__ import annotations
import asyncio
import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS events_inbox (
  dedup_key TEXT PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending', created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS feed_watermarks (
  feed TEXT PRIMARY KEY, last_seen_ts TEXT NOT NULL);
"""

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

class EventBus:
    def __init__(self, path: str = ":memory:"):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.queue: asyncio.Queue = asyncio.Queue()
        self.handlers: Dict[str, List[Callable]] = {}

    def publish(self, dedup_key: str, kind: str, payload: Dict[str, Any]) -> bool:
        try:
            self.db.execute(
                "INSERT INTO events_inbox (dedup_key, kind, payload, status, created_at)"
                " VALUES (?,?,?,?,?)",
                (dedup_key, kind, json.dumps(payload), "pending", _utcnow()))
            self.db.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def on(self, kind: str, handler: Callable):
        self.handlers.setdefault(kind, []).append(handler)

    def mark_watermark(self, feed: str, ts: str):
        self.db.execute(
            "INSERT INTO feed_watermarks (feed, last_seen_ts) VALUES (?,?)"
            " ON CONFLICT(feed) DO UPDATE SET last_seen_ts=excluded.last_seen_ts",
            (feed, ts))
        self.db.commit()

    def watermark(self, feed: str) -> str | None:
        r = self.db.execute("SELECT last_seen_ts FROM feed_watermarks WHERE feed=?", (feed,)).fetchone()
        return r["last_seen_ts"] if r else None

    async def drain(self, graph) -> Dict[str, int]:
        counts = {"processed": 0, "duplicate": 0}
        rows = self.db.execute("SELECT * FROM events_inbox WHERE status='pending'").fetchall()
        for r in rows:
            handlers = self.handlers.get(r["kind"], [])
            payload = json.loads(r["payload"])
            for h in handlers:
                res = h(graph, payload)
                if asyncio.iscoroutine(res):
                    await res
            self.db.execute("UPDATE events_inbox SET status='done' WHERE dedup_key=?", (r["dedup_key"],))
            counts["processed"] += 1
        self.db.commit()
        pending = self.db.execute("SELECT COUNT(*) c FROM events_inbox WHERE status='pending'").fetchone()["c"]
        assert pending == 0, "drain must clear pending (crash replay re-reads inbox)"
        return counts

    def pending_count(self) -> int:
        return self.db.execute("SELECT COUNT(*) c FROM events_inbox WHERE status='pending'").fetchone()["c"]
