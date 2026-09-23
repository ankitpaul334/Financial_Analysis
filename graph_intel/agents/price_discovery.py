"""Agent 7 — Price Discovery: ordered temporal repricing chain."""
from __future__ import annotations
from typing import Any, Dict, List
from .base import BaseAgent, AgentResult

class PriceDiscoveryAgent(BaseAgent):
    name = "price_discovery"
    def run(self, graph, payload: Dict[str, Any]) -> AgentResult:
        chain: List[Dict[str, Any]] = payload.get("chain", [])
        if len(chain) < 2:
            return AgentResult(ok=False, data={}, errors=["need >=2 assets in chain"])
        legs = []
        for a, b in zip(chain, chain[1:]):
            ta, tb = a.get("timestamp", ""), b.get("timestamp", "")
            lead_lag = 0
            try:
                from datetime import datetime
                lead_lag = (datetime.fromisoformat(tb) - datetime.fromisoformat(ta)).total_seconds() / 60
            except Exception:
                pass
            legs.append({"from": a.get("asset"), "to": b.get("asset"),
                         "lag_min": round(lead_lag, 1),
                         "transmission": round(float(b.get("move_pct", 0)) / (abs(float(a.get("move_pct", 0))) + 1e-9), 3)})
        unreacted = [c["asset"] for c in chain if abs(float(c.get("move_pct", 0))) < 0.05]
        return AgentResult(ok=True, data={"legs": legs, "originator": chain[0]["asset"],
                           "terminal": chain[-1]["asset"], "unreacted": unreacted})
