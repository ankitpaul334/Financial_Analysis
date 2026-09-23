"""Agent 8 — Dislocation Detector: 5-gate candidate filter."""
from __future__ import annotations
from typing import Any, Dict, List
from graph_intel.confidence import score as conf_score
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
        conf = None
        if passed:
            sig = graph.add_node("Signal", event=payload.get("event_id"),
                                 us_asset=payload.get("us_asset"),
                                 residual=payload.get("residual"))
            conf = conf_score(source_tier=int(payload.get("source_tier", 6)),
                              zscore=float(payload.get("zscore", 0.0)),
                              stability=float(payload.get("stability", 0.5)),
                              strength=float(payload.get("exposure", 0.5)), depth=1)
            graph.add_edge("SIGNAL_DERIVED_FROM", sig.id, payload["event_id"],
                           confidence=conf["confidence"], confidence_parts=conf["components"])
        return AgentResult(ok=True, data={"gates": gates, "rejects": rejects,
                           "candidate": passed, "signal_id": sig.id if sig else None,
                           "confidence": conf})
