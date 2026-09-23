"""Shared temporal knowledge graph — single source of truth for all agents."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

VALID_NODE_TYPES = {
    "Event","NewsArticle","Source","Country","Region","Exchange","Market",
    "Asset","Stock","ETF","ADR","Future","Commodity","Currency","Bond",
    "Sector","Company","Industry","SupplyChainEntity","CentralBank",
    "Government","EconomicIndicator","TimeWindow","TradingSession",
    "HistoricalObservation","Signal","Decision","Execution","RiskFactor",
}

VALID_EDGE_TYPES = {
    "EVENT_REPORTED_BY","EVENT_AFFECTS","EVENT_ORIGINATED_IN","EVENT_OCCURS_AT",
    "NEWS_SUPPORTS","NEWS_CONTRADICTS","ASSET_EXPOSED_TO","COMPANY_BELONGS_TO",
    "COMPANY_SUPPLIES","COMPANY_DEPENDS_ON","ASSET_TRACKS","ASSET_CORRELATES_WITH",
    "ASSET_LEADS","ASSET_LAGS","ASSET_HEDGES","MARKET_TRADES_ON",
    "MARKET_CLOSED_DURING","MARKET_OPEN_DURING","ASSET_PRICED_BY",
    "EVENT_TRANSMITS_TO","EVENT_IMPACTS","SIGNAL_DERIVED_FROM",
    "SIGNAL_CONTRADICTED_BY","SIGNAL_VALIDATED_BY","SIGNAL_REJECTED_BY",
    "DECISION_BASED_ON","EXECUTION_FOR",
}

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass
class Node:
    id: str
    type: str
    props: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utcnow)

    def __post_init__(self):
        if self.type not in VALID_NODE_TYPES:
            raise ValueError(f"invalid node type: {self.type}")

@dataclass
class Edge:
    id: str
    type: str
    frm: str
    to: str
    props: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utcnow)

    def __post_init__(self):
        if self.type not in VALID_EDGE_TYPES:
            raise ValueError(f"invalid edge type: {self.type}")

class TemporalGraph:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, Edge] = {}
        self.by_type: Dict[str, set] = {}

    def add_node(self, type: str, id: Optional[str] = None, **props) -> Node:
        nid = id or f"{type.lower()}_{uuid.uuid4().hex[:8]}"
        if nid in self.nodes:
            return self.nodes[nid]
        n = Node(id=nid, type=type, props=props)
        self.nodes[nid] = n
        self.by_type.setdefault(type, set()).add(nid)
        return n

    def add_edge(self, type: str, frm: str, to: str, **props) -> Edge:
        if frm not in self.nodes or to not in self.nodes:
            raise KeyError(f"edge endpoints missing: {frm} -> {to}")
        props.setdefault("confidence", 0.5)
        props.setdefault("created_at", _utcnow())
        eid = f"e_{uuid.uuid4().hex[:8]}"
        e = Edge(id=eid, type=type, frm=frm, to=to, props=props)
        self.edges[eid] = e
        return e

    def neighbours(self, nid: str, edge_types: Optional[set] = None, depth: int = 1) -> Dict[str, List[Edge]]:
        if nid not in self.nodes:
            raise KeyError(f"unknown node: {nid}")
        try:
            depth = int(depth)
        except (TypeError, ValueError):
            raise ValueError("depth must be an integer")
        if depth < 1 or depth > 6:
            raise ValueError("depth must be 1..6")
        out: Dict[str, List[Edge]] = {}
        frontier = {nid}
        seen = {nid}
        adj: Dict[str, List[Edge]] = {}
        for e in self.edges.values():
            adj.setdefault(e.frm, []).append(e)
            adj.setdefault(e.to, []).append(e)
        for _ in range(depth):
            nxt = set()
            for n in frontier:
                for e in adj.get(n, []):
                    if edge_types and e.type not in edge_types:
                        continue
                    nb = e.to if e.frm == n else e.frm
                    if nb not in seen:
                        out.setdefault(nb, []).append(e)
                        nxt.add(nb)
            seen |= nxt
            frontier = nxt
            if not frontier:
                break
        return out

    def subgraph(self, node_ids: List[str]) -> Dict[str, Any]:
        keep = set(node_ids)
        return {
            "nodes": [asdict(self.nodes[i]) for i in keep if i in self.nodes],
            "edges": [asdict(e) for e in self.edges.values() if e.frm in keep and e.to in keep],
        }

    def snapshot(self) -> Dict[str, Any]:
        return {"nodes": len(self.nodes), "edges": len(self.edges), "taken_at": _utcnow()}

    def find_events_without_us_pricing(self) -> List[str]:
        return [nid for nid in self.by_type.get("Event", [])]
