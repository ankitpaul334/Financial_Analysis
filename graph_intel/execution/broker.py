"""I8 — isolated execution: signed auth, paper broker, audit log. No research imports."""
from __future__ import annotations
import hashlib
import hmac
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS executions (
  idempotency_key TEXT PRIMARY KEY, signal_id TEXT NOT NULL, asset TEXT NOT NULL,
  action TEXT NOT NULL, qty REAL NOT NULL, status TEXT NOT NULL, ts TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, kind TEXT NOT NULL, detail TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS positions (
  asset TEXT PRIMARY KEY, qty REAL NOT NULL, max_qty REAL NOT NULL);
"""

@dataclass
class Auth:
    signal_id: str
    asset: str
    action: str
    qty: float
    max_loss: float
    expires_at: datetime
    risk_approved: bool
    signature: str = ""

    def sign(self, secret: str) -> str:
        msg = f"{self.signal_id}|{self.asset}|{self.action}|{self.qty}|{self.expires_at.isoformat()}"
        self.signature = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
        return self.signature

    def verify(self, secret: str) -> bool:
        msg = f"{self.signal_id}|{self.asset}|{self.action}|{self.qty}|{self.expires_at.isoformat()}"
        expect = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expect, self.signature)

class PaperBroker:
    def __init__(self, path: str = ":memory:", kill_switch: bool = False):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.kill_switch = kill_switch

    def _audit(self, kind: str, detail: str):
        self.db.execute("INSERT INTO audit_log (ts, kind, detail) VALUES (?,?,?)",
                        (datetime.now(timezone.utc).isoformat(), kind, detail))
        self.db.commit()

    def set_limit(self, asset: str, max_qty: float):
        self.db.execute(
            "INSERT INTO positions (asset, qty, max_qty) VALUES (?,?,?)"
            " ON CONFLICT(asset) DO UPDATE SET max_qty=excluded.max_qty", (asset, 0.0, max_qty))
        self.db.commit()

    def execute(self, auth: Auth, secret: str, user_authorized: bool,
                market_open: bool, idempotency_key: str) -> Dict[str, Any]:
        deny = lambda r: {"executed": False, "reason": r}
        if self.kill_switch:
            return deny("kill_switch")
        if not auth.verify(secret):
            self._audit("deny", "bad_signature")
            return deny("bad_signature")
        if auth.expires_at <= datetime.now(timezone.utc):
            self._audit("deny", "expired")
            return deny("expired")
        if not (auth.risk_approved and user_authorized and market_open):
            self._audit("deny", "not_approved")
            return deny("not_approved")
        if self.db.execute("SELECT 1 FROM executions WHERE idempotency_key=?",
                           (idempotency_key,)).fetchone():
            return deny("duplicate")
        pos = self.db.execute("SELECT qty, max_qty FROM positions WHERE asset=?",
                              (auth.asset,)).fetchone()
        cur, lim = (pos["qty"], pos["max_qty"]) if pos else (0.0, float("inf"))
        if abs(cur + auth.qty) > lim:
            self._audit("deny", "position_limit")
            return deny("position_limit")
        self.db.execute(
            "INSERT INTO executions (idempotency_key, signal_id, asset, action, qty, status, ts)"
            " VALUES (?,?,?,?,?,?,?)",
            (idempotency_key, auth.signal_id, auth.asset, auth.action, auth.qty, "filled",
             datetime.now(timezone.utc).isoformat()))
        if pos:
            self.db.execute("UPDATE positions SET qty=qty+? WHERE asset=?", (auth.qty, auth.asset))
        else:
            self.db.execute("INSERT INTO positions (asset, qty, max_qty) VALUES (?,?,?)",
                            (auth.asset, auth.qty, float("inf")))
        self.db.commit()
        self._audit("fill", f"{auth.asset}x{auth.qty}")
        return {"executed": True, "idempotency_key": idempotency_key}

    def audit(self) -> List[Dict[str, Any]]:
        return [dict(r) for r in self.db.execute("SELECT * FROM audit_log ORDER BY id")]
