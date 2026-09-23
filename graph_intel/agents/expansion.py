"""Agent 4 — Graph Expansion: ranked 2nd/3rd-order exposure subgraph."""
from __future__ import annotations
from typing import Any, Dict, List
from .base import BaseAgent, AgentResult

def _score(e) -> float:
    p = e.props
    return (
        float(p.get("economic_relevance", 0.5)) * 0.3
        + float(p.get("strength", 0.5)) * 0.25
        + float(p.get("confidence", 0.5)) * 0.25
        + float(p.get("materiality", 0.5)) * 0.2
    )

class GraphExpansionAgent(BaseAgent):
    name = "graph_expansion"
    def run(self, graph, payload: Dict[str, Any]) -> AgentResult:
        start = payload.get("event_id")
        if not start or start not in graph.nodes:
            return AgentResult(ok=False, data={}, errors=[f"event not in graph: {start}"])
        try:
            depth = int(payload.get("max_depth", 3))
        except (TypeError, ValueError):
            return AgentResult(ok=False, data={}, errors=["max_depth must be an integer"])
        if depth < 1 or depth > 6:
            return AgentResult(ok=False, data={}, errors=["max_depth must be 1..6"])
        try:
            top_k = int(payload.get("top_k", 15))
        except (TypeError, ValueError):
            return AgentResult(ok=False, data={}, errors=["top_k must be an integer"])
        top_k = max(1, min(top_k, 100))
        scored: Dict[str, float] = {start: 1.0}
        frontier = {start}
        seen = {start}
        for _ in range(depth):
            nxt: Dict[str, float] = {}
            for e in graph.edges.values():
                nb = None
                if e.frm in frontier and e.to not in seen:
                    nb = e.to
                elif e.to in frontier and e.frm not in seen:
                    nb = e.frm
                if nb:
                    s = _score(e) * max(scored.get(e.frm, 0.5), scored.get(e.to, 0.5))
                    nxt[nb] = max(nxt.get(nb, 0), s)
            if not nxt:
                break
            for k, v in nxt.items():
                scored[k] = v
            seen |= set(nxt)
            frontier = set(nxt)
        ranked = sorted(((k, v) for k, v in scored.items() if k != start),
                        key=lambda x: -x[1])[:top_k]
        return AgentResult(ok=True, data={
            "event_id": start,
            "ranked_nodes": [{"node_id": k, "score": round(v, 3),
                              "type": graph.nodes[k].type} for k, v in ranked],
            "subgraph": graph.subgraph([start] + [k for k, _ in ranked]),
        })
