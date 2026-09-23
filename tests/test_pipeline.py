"""End-to-end pipeline test across all agents."""
from graph_intel.graph import TemporalGraph
from graph_intel.agents.ingestion import IngestionAgent
from graph_intel.agents.entity_resolution import EntityResolutionAgent
from graph_intel.agents.event_extraction import EventExtractionAgent
from graph_intel.agents.expansion import GraphExpansionAgent
from graph_intel.agents.observers import run_all_regions
from graph_intel.agents.reasoner import CrossMarketReasoner
from graph_intel.agents.price_discovery import PriceDiscoveryAgent
from graph_intel.agents.dislocation import DislocationDetector
from graph_intel.agents.validation import QuantAgent, CounterfactualAgent, FalsificationAgent, RiskAgent
from graph_intel.agents.decision import DecisionAgent, ExecutionAgent, LearningAgent

def test_full_pipeline():
    g = TemporalGraph()
    r1 = IngestionAgent().run(g, {
        "raw_news": [{"source": "RBA", "headline": "Australia iron ore exports halted on cyclone, supply shock",
                       "body": "Major Pilbara iron ore terminals shut after a severe cyclone. Shipments halted, surprising commodity markets and pushing futures sharply higher with follow through across Asia and into US steel makers.",
                       "source_tier": "government", "entities": ["Iron Ore", "Australia", "BHP"]}],
        "market_ticks": [
            {"symbol": "IronOre", "price": 142.0, "region": "australia", "volume_change": 3.1,
             "timestamp": "2026-09-23T02:00:00+00:00"},
            {"symbol": "X", "price": 58.0, "region": "us", "volume_change": 0.1,
             "timestamp": "2026-09-23T13:00:00+00:00"},
        ]})
    assert len(r1.data["events"]) == 1, r1.errors
    ev_article = r1.data["events"][0]

    r2 = EntityResolutionAgent().run(g, {"entities": ev_article["entities"]})
    assert any(x["confidence"] == 1.0 for x in r2.data["resolved"])

    r3 = EventExtractionAgent().run(g, {"articles": [{
        "article_id": list(g.by_type.get("NewsArticle", []))[0],
        "headline": ev_article["raw_claims"][0], "body": ev_article["raw_claims"][1]}]})
    eid = r3.data["events"][0]["event_id"]
    assert r3.data["events"][0]["mechanism"] == "supply-shock transmission"

    for nid in ["commodity_iron_ore", "etf_xle", "asset_us_steel"]:
        try:
            g.add_node("Commodity" if "commodity" in nid else ("ETF" if "etf" in nid else "Asset"), id=nid)
        except Exception:
            pass
    g.add_edge("EVENT_AFFECTS", eid, "commodity_iron_ore", confidence=0.9, strength=0.9,
               economic_relevance=0.9, materiality=0.9)
    g.add_edge("EVENT_TRANSMITS_TO", "commodity_iron_ore", "asset_us_steel",
               confidence=0.7, strength=0.7, economic_relevance=0.7, materiality=0.6)
    r4 = GraphExpansionAgent().run(g, {"event_id": eid})
    assert r4.data["ranked_nodes"][0]["node_id"] == "commodity_iron_ore"

    robs = run_all_regions(g, r1.data["ticks"])
    assert robs["australia"].data["coverage_ratio"] > 0

    r6 = CrossMarketReasoner().run(g, {"event_id": eid,
        "overseas_moves": [{"asset": "IronOre", "move_pct": 4.0}], "us_moves": {"move_pct": 0.2}})
    assert r6.data["residual"] < 0

    r7 = PriceDiscoveryAgent().run(g, {"chain": [
        {"asset": "IronOre", "move_pct": 4.0, "timestamp": "2026-09-23T02:00:00+00:00"},
        {"asset": "X", "move_pct": 0.2, "timestamp": "2026-09-23T13:00:00+00:00"}]})
    assert r7.data["originator"] == "IronOre"

    r8 = DislocationDetector().run(g, {"event_id": eid, "is_new": True, "novelty": 0.9,
        "overseas_move": 4.0, "us_asset": "X", "exposure": 0.8, "residual": -2.2,
        "hit_rate": 0.65, "stability": 0.7})
    assert r8.data["candidate"] and r8.data["signal_id"]
    sig = r8.data["signal_id"]

    r9 = QuantAgent().run(g, {"series_x": [1, 2, 3, 4, 5, 4, 3, 5, 6, 7],
                              "series_y": [0.6, 1.2, 1.8, 2.4, 3.0, 2.4, 1.8, 3.0, 3.6, 4.2],
                              "current_x": 4.0, "current_y": 0.2})
    assert r9.data["significant"]

    r10 = CounterfactualAgent().run(g, {"observed_us_move": 0.2,
        "market_drivers": [{"name": "SPX", "move": 0.3}], "betas": {"SPX": 1.0}})
    r11 = FalsificationAgent().run(g, {"signal_id": sig, "event_id": eid, "alternative_paths": []})
    assert not r11.data["rejected"]
    r12 = RiskAgent().run(g, {"signal_id": sig, "gross_edge_bps": 220,
                              "spread_bps": 5, "slippage_bps": 10, "volatility_bps": 60})
    assert r12.data["approved"]

    r13 = DecisionAgent().run(g, {"signal_id": sig, "residual": -2.2,
        "quant": r9.data, "falsification": r11.data, "risk": r12.data})
    assert r13.data["decision"] == "ACTION_CANDIDATE", r13.data

    r14 = ExecutionAgent().run(g, {"auth": {"signal_id": sig, "asset": "X",
        "risk_approved": True, "max_loss": 1000, "expires_at": "2999-01-01T00:00:00+00:00"},
        "market_open": True, "user_authorized": True})
    assert r14.data["executed"]

    r15 = LearningAgent().run(g, {"signal_id": sig, "realized_move": 2.0, "expected_move": 2.2})
    assert r15.data["hit"]
    print(f"ALL 15 AGENTS PASS | nodes={g.snapshot()['nodes']} edges={g.snapshot()['edges']}")

if __name__ == "__main__":
    test_full_pipeline()
