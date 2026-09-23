"""Agent 6 — Cross-Market Reasoner: delegates math to BetaResidualService."""
from __future__ import annotations
from typing import Any, Dict, List
from graph_intel.quant import beta_from_history, BetaResidualService
from .base import BaseAgent, AgentResult

class CrossMarketReasoner(BaseAgent):
    name = "cross_market_reasoner"
    def run(self, graph, payload: Dict[str, Any]) -> AgentResult:
        event_id = payload.get("event_id")
        overseas = payload.get("overseas_moves", [])
        us = payload.get("us_moves", {})
        if not event_id or event_id not in graph.nodes:
            return AgentResult(ok=False, data={}, errors=["event missing"])
        o_mag = sum(abs(float(m.get("move_pct", 0))) for m in overseas) / max(len(overseas), 1)
        us_move = float(us.get("move_pct", 0.0))
        if payload.get("series_x") and payload.get("series_y"):
            stats = beta_from_history(payload["series_x"], payload["series_y"])
            beta, sd = stats["beta"], stats["resid_sd"]
        else:
            beta, sd = float(payload.get("expected_beta", 0.6)), float(payload.get("resid_sd", 1.0))
        r = BetaResidualService.residual(o_mag, us_move, beta, sd)
        return AgentResult(ok=True, data={
            "event_id": event_id,
            "overseas_magnitude": round(o_mag, 3),
            "expected_us_move": r["expected_us_move"],
            "observed_us_move": us_move,
            "residual": r["residual"],
            "zscore": r["zscore"],
            "significant": r["significant"],
            "beta": r["beta"],
            "graph_snapshot": graph.snapshot(),
            "n_overseas": len(overseas),
        })
