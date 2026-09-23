"""Agent 1 v2 — Ingestion: normalize feeds, dedup, no reasoning leakage."""
from __future__ import annotations
import hashlib
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from .base import BaseAgent, AgentResult

SOURCE_TIERS = {
    "government": 1, "central_bank": 2, "exchange": 3, "filing": 4,
    "data_provider": 5, "financial_news": 6, "specialist": 7, "social": 8,
}

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def _norm_src(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
    return f"src_{s[:48]}" or "src_unknown"

def _hash(*parts: str) -> str:
    h = hashlib.sha256("|".join(p.strip().lower() for p in parts).encode()).hexdigest()[:12]
    return h

def _norm_news(item: Dict[str, Any]) -> Dict[str, Any]:
    if not item.get("source") or not item.get("headline"):
        raise ValueError(f"news missing source/headline: {item}")
    headline = item["headline"].strip()
    art_id = f"art_{_hash(item['source'], headline)}"
    return {
        "article_id": art_id,
        "dedup_key": _hash(headline),
        "timestamp": item.get("published_at") or item.get("timestamp") or _utcnow(),
        "publication_time": item.get("published_at") or item.get("timestamp") or _utcnow(),
        "event_time": item.get("event_time"),
        "source": item["source"].strip(),
        "source_tier": item.get("source_tier", "financial_news"),
        "entities": item.get("entities", []),
        "raw_claims": [headline, item.get("body", "")],
        "timezone": item.get("timezone", "UTC"),
    }

def _norm_tick(t: Dict[str, Any]) -> Dict[str, Any]:
    if t.get("symbol") is None or t.get("price") is None:
        raise ValueError(f"tick missing symbol/price: {t}")
    return {
        "symbol": str(t["symbol"]).strip().upper(),
        "price": float(t["price"]),
        "timestamp": t.get("timestamp") or _utcnow(),
        "region": t.get("region", "unknown"),
        "volume_change": float(t.get("volume_change", 0.0)),
    }

class IngestionAgent(BaseAgent):
    name = "ingestion"
    def run(self, graph, payload: Dict[str, Any]) -> AgentResult:
        errors: List[str] = []
        events: List[Dict[str, Any]] = []
        seen_articles: set = set()
        for n in payload.get("raw_news", []):
            try:
                ev = _norm_news(n)
                if ev["article_id"] in seen_articles:
                    continue
                seen_articles.add(ev["article_id"])
                if ev["event_time"] is None:
                    ev["event_time"] = ev["publication_time"]
                events.append(ev)
                src = graph.add_node("Source", id=_norm_src(ev["source"]),
                                     name=ev["source"], tier=SOURCE_TIERS.get(ev["source_tier"], 6))
                if ev["article_id"] not in graph.nodes:
                    art = graph.add_node("NewsArticle", id=ev["article_id"],
                                         headline=ev["raw_claims"][0], source=ev["source"],
                                         publication_time=ev["publication_time"],
                                         timezone=ev["timezone"])
                    graph.add_edge("EVENT_REPORTED_BY", art.id, src.id, confidence=0.6)
            except Exception as ex:
                errors.append(str(ex))
        ticks: List[Dict[str, Any]] = []
        for t in payload.get("market_ticks", []):
            try:
                ticks.append(_norm_tick(t))
            except Exception as ex:
                errors.append(str(ex))
        return AgentResult(ok=bool(events or ticks) and not errors,
                           data={"events": events, "ticks": ticks}, errors=errors)
