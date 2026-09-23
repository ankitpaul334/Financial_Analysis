"""Agent 6 — Cross-Market Reasoner: compare connected graph state in one window."""
from __future__ import annotations
from typing import Any, Dict, List
from .base import BaseAgent, AgentResult

class CrossMarketReasoner(BaseAgent):
    name = "cross_market_reasoner"
    def run(self, graph, payload: Dict[str, Any]) -> AgentResult:
        event_id = payload.get("event_id")
        overseas = payload.get("overseas_moves", [])
        us = payload.get("us_moves", {})
        expected_beta = float(payload.get("expected_beta", 0.6))
        if not event_id or event_id not in graph.nodes:
            return AgentResult(ok=False, data={}, errors=["event missing"])
        o_mag = sum(abs(float(m.get("move_pct", 0))) for m in overseas) / max(len(overseas), 1)
        us_move = float(us.get("move_pct", 0.0))
        expected_us = round(o_mag * expected_beta, 3)
        residual = round(us_move - expected_us, 3)
        snapshot = graph.snapshot()
        return AgentResult(ok=True, data={
            "event_id": event_id,
            "overseas_magnitude": round(o_mag, 3),
            "expected_us_move": expected_us,
            "observed_us_move": us_move,
            "residual": residual,
            "graph_snapshot": snapshot,
            "n_overseas": len(overseas),
        })
