"""Agent 3 — Event Extraction: headline+body to structured event, rule-based v1."""
from __future__ import annotations
import re
import uuid
from typing import Any, Dict, List
from .base import BaseAgent, AgentResult

MECHANISMS = [
    (r"rate (hike|cut|hold)|central bank|boj|fed|ecb", "monetary-policy repricing"),
    (r"export|disruption|shortage|supply|mine|pipeline|opec", "supply-shock transmission"),
    (r"tariff|sanction|war|missile|geopolitic|tension", "geopolitical risk repricing"),
    (r"earnings|guidance|profit|revenue|chip|semiconductor", "earnings-expectation revision"),
    (r"inflation|cpi|jobs|gdp|retail|yields|bond", "macro-data repricing"),
]

WHAT_PATTERNS = [
    (r"(holds?|keeps?|leaves?) .* rates?", "rates unchanged"),
    (r"cuts? .* rates?", "rate cut"),
    (r"hikes?|raises? .* rates?", "rate hike"),
    (r"disruption|halt|strike|outage", "supply disruption"),
    (r"beats?|misses? .* (earnings|revenue|guidance)", "earnings surprise"),
    (r"tariff|sanction", "trade restriction"),
]

def _match(rules, text: str, default: str) -> str:
    for pat, label in rules:
        if re.search(pat, text, re.I):
            return label
    return default

def extract(headline: str, body: str = "") -> Dict[str, Any]:
    text = f"{headline} {body}"
    surprise = 0.6 if re.search(r"surprise|unexpected|shock|beats?|misses?", text, re.I) else 0.3
    confidence = 0.75 if len(body or "") > 80 else 0.5
    return {
        "what": _match(WHAT_PATTERNS, text, headline[:120]),
        "mechanism": _match(MECHANISMS, text, "general repricing"),
        "surprise": surprise,
        "confidence": confidence,
    }

class EventExtractionAgent(BaseAgent):
    name = "event_extraction"
    def run(self, graph, payload: Dict[str, Any]) -> AgentResult:
        out: List[Dict[str, Any]] = []
        errors: List[str] = []
        for art in payload.get("articles", []):
            try:
                headline = art.get("headline", "")
                if not headline:
                    raise ValueError("article missing headline")
                ex = extract(headline, art.get("body", ""))
                eid = art.get("event_id") or f"evt_{uuid.uuid4().hex[:8]}"
                ev = graph.add_node("Event", id=eid, what=ex["what"],
                                    mechanism=ex["mechanism"], surprise=ex["surprise"],
                                    confidence=ex["confidence"])
                if art.get("article_id") and art["article_id"] in graph.nodes:
                    graph.add_edge("NEWS_SUPPORTS", art["article_id"], ev.id,
                                   confidence=ex["confidence"])
                out.append({"event_id": ev.id, **ex})
            except Exception as ex2:
                errors.append(str(ex2))
        return AgentResult(ok=bool(out), data={"events": out}, errors=errors)
