"""I1 — SQLite temporal graph store with bitemporal edges + time-travel."""
from __future__ import annotations
import json
import sqlite3
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from .graph import TemporalGraph, Node, Edge, VALID_NODE_TYPES, VALID_EDGE_TYPES

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS nodes (
  id TEXT PRIMARY KEY, type TEXT NOT NULL, props TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS edges (
  id TEXT PRIMARY KEY, type TEXT NOT NULL, "frm" TEXT NOT NULL, "to" TEXT NOT NULL,
  props TEXT NOT NULL, valid_from TEXT NOT NULL, valid_to TEXT,
  txn_time TEXT NOT NULL,
  FOREIGN KEY("frm") REFERENCES nodes(id), FOREIGN KEY("to") REFERENCES nodes(id));
CREATE INDEX IF NOT EXISTS idx_edges_endpoints ON edges("frm", "to", valid_to);
CREATE TABLE IF NOT EXISTS graph_versions (
  version INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, note TEXT);
"""

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

class TemporalStore(TemporalGraph):
    def __init__(self, path: str | Path = ":memory:"):
        super().__init__()
        self.db = sqlite3.connect(str(path))
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def _log_version(self, note: str) -> int:
        cur = self.db.execute("INSERT INTO graph_versions (ts, note) VALUES (?,?)", (_utcnow(), note))
        self.db.commit()
        return cur.lastrowid

    def add_node(self, type: str, id: Optional[str] = None, **props) -> Node:
        n = super().add_node(type, id, **props)
        self.db.execute(
            "INSERT OR IGNORE INTO nodes (id, type, props, created_at) VALUES (?,?,?,?)",
            (n.id, n.type, json.dumps(n.props), n.created_at))
        self.db.commit()
        return n

    def add_edge(self, type: str, frm: str, to: str, valid_from: Optional[str] = None,
                 txn_time: Optional[str] = None, **props) -> Edge:
        e = super().add_edge(type, frm, to, **props)
        vf = valid_from or e.props.get("valid_from") or _utcnow()
        self.db.execute(
            "INSERT INTO edges (id, type, \"frm\", \"to\", props, valid_from, valid_to, txn_time)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (e.id, e.type, e.frm, e.to, json.dumps(e.props), vf, None, txn_time or _utcnow()))
        self.db.commit()
        return e

    def supersede_edge(self, type: str, frm: str, to: str, valid_from: Optional[str] = None,
                       at: Optional[str] = None, **props) -> Edge:
        ts = at or _utcnow()
        self.db.execute(
            "UPDATE edges SET valid_to=? WHERE type=? AND \"frm\"=? AND \"to\"=? AND valid_to IS NULL",
            (ts, type, frm, to))
        return self.add_edge(type, frm, to, valid_from=valid_from or ts, txn_time=ts, **props)

    def as_of(self, ts: str) -> Dict[str, Any]:
        nodes = [dict(r) for r in self.db.execute("SELECT * FROM nodes WHERE created_at <= ?", (ts,))]
        edges = [dict(r) for r in self.db.execute(
            "SELECT * FROM edges WHERE valid_from <= ? AND (valid_to IS NULL OR valid_to > ?)"
            " AND txn_time <= ?", (ts, ts, ts))]
        return {"as_of": ts, "nodes": nodes, "edges": edges}

    def edge_history(self, frm: str, to: str, type: Optional[str] = None) -> List[Dict[str, Any]]:
        q = "SELECT * FROM edges WHERE \"frm\"=? AND \"to\"=?"
        args: list = [frm, to]
        if type:
            q += " AND type=?"
            args.append(type)
        return [dict(r) for r in self.db.execute(q + " ORDER BY txn_time", args)]

    def snapshot_version(self, note: str = "") -> Dict[str, Any]:
        v = self._log_version(note)
        return {"version": v, "ts": _utcnow(), **super().snapshot()}

    def close(self):
        self.db.close()
