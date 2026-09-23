"""Agent 8 — Dislocation Detector: 5-gate candidate filter."""
from __future__ import annotations
from typing import Any, Dict, List
from .base import BaseAgent, AgentResult

class DislocationDetector(BaseAgent):
    name = "dislocation_detector"
    def run(self, graph, payload: Dict[str, Any]) -> AgentResult:
        gates = {
            "new_information": bool(payload.get("is_new")) and float(payload.get("novelty", 0)) > 0.3,
            "overseas_repricing": abs(float(payload.get("overseas_move", 0))) >= float(payload.get("min_overseas", 0.5)),
            "us_exposure": bool(payload.get("us_asset")) and float(payload.get("exposure", 0)) > 0.2,
            "us_gap": abs(float(payload.get("residual", 0))) >= float(payload.get("min_residual", 0.3)),
            "historical_support": float(payload.get("hit_rate", 0)) >= 0.5 and float(payload.get("stability", 0)) >= 0.5,
        }
        rejects = []
        for k in ("futures_moved", "adr_adjusted", "fx_explains", "commodity_transmitted", "illiquid", "unstable"):
            if payload.get(k):
                rejects.append(k)
        passed = all(gates.values()) and not rejects
        sig = None
        if passed:
            sig = graph.add_node("Signal", event=payload.get("event_id"),
                                 us_asset=payload.get("us_asset"),
                                 residual=payload.get("residual"))
            graph.add_edge("SIGNAL_DERIVED_FROM", sig.id, payload["event_id"], confidence=0.6)
        return AgentResult(ok=True, data={"gates": gates, "rejects": rejects,
                           "candidate": passed, "signal_id": sig.id if sig else None})
