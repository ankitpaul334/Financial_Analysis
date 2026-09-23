"""Agent 5 — Parallel Regional Market Observers (Japan/Europe/Australia/MiddleEast/US)."""
from __future__ import annotations
import concurrent.futures
from typing import Any, Dict, List
from .base import BaseAgent, AgentResult

REGIONS = {
    "japan": ["Nikkei", "TOPIX", "JPY", "JGB"],
    "europe": ["STOXX", "DAX", "FTSE", "EUR", "GBP", "Bund"],
    "australia": ["ASX", "AUD", "IronOre", "Banks-AU"],
    "middle_east": ["Brent", "NatGas", "TASI", "AED"],
    "us": ["SPX-FUT", "NDX-FUT", "DJI-FUT", "XLE", "TLT", "VIX", "USD"],
}

class RegionalObserver(BaseAgent):
    def __init__(self, region: str):
        self.name = f"observer_{region}"
        self.region = region

    def run(self, graph, payload: Dict[str, Any]) -> AgentResult:
        ticks = [t for t in payload.get("market_ticks", [])
                 if t.get("region", "").lower() == self.region]
        obs_ids = []
        for t in ticks:
            a = graph.add_node("Asset", id=f"asset_{t['symbol']}", symbol=t["symbol"])
            h = graph.add_node("HistoricalObservation", symbol=t["symbol"],
                               price=t["price"], timestamp=t["timestamp"],
                               region=self.region, volume_change=t.get("volume_change", 0))
            graph.add_edge("ASSET_PRICED_BY", a.id, h.id, confidence=0.9,
                           observation_window=t["timestamp"])
            obs_ids.append(h.id)
        coverage = [s for s in REGIONS[self.region]
                    if any(s.lower() in t["symbol"].lower() for t in ticks)]
        return AgentResult(ok=True, data={"region": self.region, "observations": obs_ids,
                           "coverage": coverage,
                           "coverage_ratio": round(len(coverage) / len(REGIONS[self.region]), 2)})

def run_all_regions(graph, ticks: List[Dict[str, Any]]) -> Dict[str, AgentResult]:
    out: Dict[str, AgentResult] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        futs = {ex.submit(RegionalObserver(r).run, graph, {"market_ticks": ticks}): r
                for r in REGIONS}
        for f in concurrent.futures.as_completed(futs):
            out[futs[f]] = f.result()
    return out
