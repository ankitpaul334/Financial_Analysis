"""Agents 9-12 — quant, counterfactual, falsification, risk."""
from __future__ import annotations
from typing import Any, Dict, List
from graph_intel.confidence import score as conf_score
from .base import BaseAgent, AgentResult

class QuantAgent(BaseAgent):
    name = "quant"
    def run(self, graph, payload: Dict[str, Any]) -> AgentResult:
        from graph_intel.quant import beta_from_history, BetaResidualService
        x, y = payload.get("series_x", []), payload.get("series_y", [])
        cur_x = float(payload.get("current_x", 0))
        cur_y = float(payload.get("current_y", 0))
        if len(x) < 3:
            return AgentResult(ok=False, data={}, errors=["insufficient history"])
        stats = beta_from_history(x, y)
        r = BetaResidualService.residual(cur_x, cur_y, stats["beta"], stats["resid_sd"])
        return AgentResult(ok=True, data={"beta": r["beta"], "correlation": round(stats["correlation"], 3),
                           "residual": r["residual"], "zscore": r["zscore"],
                           "significant": r["significant"]})

class CounterfactualAgent(BaseAgent):
    name = "counterfactual"
    def run(self, graph, payload: Dict[str, Any]) -> AgentResult:
        from graph_intel.quant import BetaResidualService
        drivers = payload.get("market_drivers", [])
        observed = float(payload.get("observed_us_move", 0))
        betas = payload.get("betas", {})
        baseline = round(sum(float(d.get("move", 0)) * float(betas.get(d.get("name", ""), 0.3)) for d in drivers), 3)
        beta = float(payload.get("beta", 1.0))
        r = BetaResidualService.residual(baseline, observed, beta, float(payload.get("resid_sd", 1.0)))
        return AgentResult(ok=True, data={"expected_us_move": r["expected_us_move"],
                           "observed_us_move": observed, "residual": r["residual"],
                           "zscore": r["zscore"], "significant": r["significant"]})

class FalsificationAgent(BaseAgent):
    name = "falsification"
    def run(self, graph, payload: Dict[str, Any]) -> AgentResult:
        alts = payload.get("alternative_paths", [])
        explained = sum(float(a.get("explains_pct", 0)) for a in alts)
        kill = explained >= 80 or any(a.get("decisive") for a in alts)
        sig = payload.get("signal_id")
        conf = conf_score(zscore=float(payload.get("zscore", 0.0)),
                          stability=float(payload.get("stability", 0.5)),
                          strength=1.0 - min(1.0, explained / 100.0), depth=2)
        if sig and sig in graph.nodes:
            graph.add_edge("SIGNAL_CONTRADICTED_BY" if kill else "SIGNAL_VALIDATED_BY",
                           sig, payload.get("event_id", sig),
                           confidence=conf["confidence"], confidence_parts=conf["components"])
        return AgentResult(ok=True, data={"explained_pct": explained, "rejected": kill,
                           "n_alternatives": len(alts), "confidence": conf})

class RiskAgent(BaseAgent):
    name = "risk"
    def run(self, graph, payload: Dict[str, Any]) -> AgentResult:
        gross = float(payload.get("gross_edge_bps", 0))
        costs = float(payload.get("spread_bps", 0)) + float(payload.get("slippage_bps", 0))
        risk_pen = float(payload.get("volatility_bps", 0)) * 0.5 + float(payload.get("gap_bps", 0))
        net = round(gross - costs - risk_pen, 1)
        approved = net >= float(payload.get("min_net_bps", 10)) and not payload.get("hard_block")
        if payload.get("signal_id") and payload["signal_id"] in graph.nodes:
            graph.add_node("RiskFactor", signal=payload["signal_id"], net_edge_bps=net, approved=approved)
        return AgentResult(ok=True, data={"gross": gross, "costs": costs,
                           "risk_penalty": risk_pen, "net_edge_bps": net, "approved": approved})
