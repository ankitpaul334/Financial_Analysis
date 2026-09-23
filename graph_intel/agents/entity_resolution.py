"""Agent 2 — Entity Resolution: map aliases to canonical nodes, no duplicates."""
from __future__ import annotations
import re
from typing import Any, Dict, List, Tuple
from .base import BaseAgent, AgentResult

ALIAS_SEED = {
    "nvidia": ("Company", "company_nvidia"),
    "nvda": ("Company", "company_nvidia"),
    "nvidia corp": ("Company", "company_nvidia"),
    "nasdaq:nvda": ("Company", "company_nvidia"),
    "nvda us": ("Company", "company_nvidia"),
    "brent": ("Commodity", "commodity_brent"),
    "brent crude": ("Commodity", "commodity_brent"),
    "wti": ("Commodity", "commodity_wti"),
    "iron ore": ("Commodity", "commodity_iron_ore"),
    "jpy": ("Currency", "currency_jpy"),
    "usd": ("Currency", "currency_usd"),
    "aud": ("Currency", "currency_aud"),
    "nikkei": ("Market", "market_nikkei"),
    "nikkei 225": ("Market", "market_nikkei"),
    "asx": ("Exchange", "exchange_asx"),
    "nasdaq": ("Exchange", "exchange_nasdaq"),
    "japan": ("Country", "country_japan"),
    "australia": ("Country", "country_australia"),
    "us": ("Country", "country_usa"),
    "usa": ("Country", "country_usa"),
}

def _norm(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s*\.\s*", " ", s)
    s = re.sub(r"[^a-z0-9: ]+", "", s)
    return re.sub(r"\s+", " ", s).strip()

class EntityResolutionAgent(BaseAgent):
    name = "entity_resolution"
    def __init__(self):
        self.aliases: Dict[str, Tuple[str, str]] = dict(ALIAS_SEED)

    def resolve(self, graph, raw: str) -> Tuple[str, str, float]:
        key = _norm(raw)
        if key in self.aliases:
            return (*self.aliases[key], 1.0)
        for alias, (ntype, nid) in self.aliases.items():
            if key == alias or key.startswith(alias + " ") or key.endswith(" " + alias):
                return ntype, nid, 0.7
        kind = "Company" if re.match(r"^[A-Z]{1,5}(\.[A-Z])?$", raw.strip()) else "SupplyChainEntity"
        nid = f"{kind.lower()}_{re.sub(r'[^a-z0-9]+', '_', key)[:32]}"
        return kind, nid, 0.4

    def run(self, graph, payload: Dict[str, Any]) -> AgentResult:
        resolved: List[Dict[str, Any]] = []
        unresolved: List[str] = []
        errors: List[str] = []
        for raw in payload.get("entities", []):
            if not isinstance(raw, str) or not raw.strip():
                errors.append(f"invalid entity: {raw!r}")
                continue
            ntype, nid, conf = self.resolve(graph, raw)
            node = graph.add_node(ntype, id=nid, canonical_name=nid, aliases=[raw])
            if raw not in node.props.get("aliases", []):
                node.props.setdefault("aliases", []).append(raw)
            resolved.append({"raw": raw, "node_id": nid, "type": ntype, "confidence": conf})
            if conf < 0.5:
                unresolved.append(raw)
        return AgentResult(ok=not errors, data={"resolved": resolved, "unresolved": unresolved},
                           errors=errors)
