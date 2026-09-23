"""Agents 13-15 — decision, execution gate, outcome learning."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict
from graph_intel.confidence import score as conf_score
from .base import BaseAgent, AgentResult

class DecisionAgent(BaseAgent):
    name = "decision"
    def run(self, graph, payload: Dict[str, Any]) -> AgentResult:
        fals = payload.get("falsification", {})
        risk = payload.get("risk", {})
        quant = payload.get("quant", {})
        if fals.get("rejected") or not risk.get("approved"):
            d = "NO_ACTION"
        elif not quant.get("significant") and abs(float(payload.get("residual", 0))) < 0.5:
            d = "WATCH"
        elif risk.get("approved") and quant.get("significant"):
            d = "ACTION_CANDIDATE"
        else:
            d = "RESEARCH_SIGNAL"
        dec = graph.add_node("Decision", decision=d, signal=payload.get("signal_id"),
                             reason=f"fals={fals.get('rejected')},risk={risk.get('approved')},z={quant.get('zscore')}")
        conf = conf_score(zscore=float(quant.get("zscore", 0.0)),
                          stability=float(payload.get("stability", 0.5)),
                          strength=float(risk.get("net_edge_bps", 0)) / 100.0, depth=2)
        if payload.get("signal_id") and payload["signal_id"] in graph.nodes:
            graph.add_edge("DECISION_BASED_ON", dec.id, payload["signal_id"],
                           confidence=conf["confidence"], confidence_parts=conf["components"])
        return AgentResult(ok=True, data={"decision": d, "decision_id": dec.id,
                           "confidence_breakdown": conf})

class ExecutionAgent(BaseAgent):
    name = "execution"
    def run(self, graph, payload: Dict[str, Any]) -> AgentResult:
        auth = payload.get("auth", {})
        checks = {
            "risk_approved": bool(auth.get("risk_approved")),
            "not_expired": auth.get("expires_at", "9999") > datetime.now(timezone.utc).isoformat(),
            "within_limits": float(auth.get("max_loss", 0)) > 0,
            "market_open": bool(payload.get("market_open")),
            "user_authorized": bool(payload.get("user_authorized")),
        }
        ok = all(checks.values())
        if ok:
            ex = graph.add_node("Execution", signal=auth.get("signal_id"), asset=auth.get("asset"))
            graph.add_edge("EXECUTION_FOR", ex.id, auth.get("signal_id"), confidence=1.0)
            return AgentResult(ok=True, data={"executed": True, "execution_id": ex.id, "checks": checks})
        return AgentResult(ok=False, data={"executed": False, "checks": checks},
                           errors=[k for k, v in checks.items() if not v])

class LearningAgent(BaseAgent):
    name = "outcome_learning"
    def run(self, graph, payload: Dict[str, Any]) -> AgentResult:
        sig = payload.get("signal_id")
        if not sig or sig not in graph.nodes:
            return AgentResult(ok=False, data={}, errors=["signal missing"])
        realized = float(payload.get("realized_move", 0))
        expected = float(payload.get("expected_move", 0))
        err = round(realized - expected, 3)
        graph.nodes[sig].props.update({"realized": realized, "error": err,
                                       "status": "hit" if abs(err) < 0.3 else "miss"})
        return AgentResult(ok=True, data={"signal_id": sig, "error": err,
                           "hit": abs(err) < 0.3})
