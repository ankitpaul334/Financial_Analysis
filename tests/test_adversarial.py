"""Adversarial regression: NaN/inf, malformed inputs, traversal abuse, look-ahead."""
import math
from graph_intel.confidence import score
from graph_intel.quant import BetaResidualService, beta_from_history
from graph_intel.benchmark import evaluate
from graph_intel.graph import TemporalGraph
from graph_intel.store import TemporalStore
from graph_intel.schemas import Article
from graph_intel.agents.entity_resolution import EntityResolutionAgent
from graph_intel.agents.expansion import GraphExpansionAgent
from graph_intel.agents.price_discovery import PriceDiscoveryAgent

def test_nan_inf_never_confident():
    assert score(zscore=float("nan"), stability=float("nan"), strength=float("inf"))["confidence"] == 0.0
    r = BetaResidualService.residual(float("nan"), 1.0, 0.6, 1.0)
    assert r["significant"] is False and r.get("invalid_input") is True
    r2 = BetaResidualService.residual(float("inf"), 1.0, 0.6, 1.0)
    assert r2["significant"] is False
    assert beta_from_history([1.0, float("nan"), 2.0], [1.0, 2.0, 3.0])["correlation"] == 0.0
    d = evaluate(overseas_move=float("nan"), residual=float("inf"), zscore=float("nan"),
                 hit_rate=0.9, stability=0.9, net_edge_bps=999, novelty=1.0,
                 exposure=1.0, is_new=True)
    assert d.passes is False and d.decision == "NO_ACTION"
    print("regression nan/inf OK")

def test_malformed_inputs_rejected():
    g = TemporalGraph()
    r = EntityResolutionAgent().run(g, {"entities": ["NVDA", None, 123, "  "]})
    assert r.ok is False and len(r.errors) == 3 and len(r.data["resolved"]) == 1
    r2 = GraphExpansionAgent().run(g, {"event_id": "evt_x", "max_depth": "abc"})
    assert r2.ok is False
    r3 = GraphExpansionAgent().run(g, {"event_id": "evt_x", "max_depth": 99})
    assert r3.ok is False
    e = g.add_node("Event", id="evt_t")
    try:
        g.neighbours("ghost")
        assert False, "must raise"
    except KeyError:
        pass
    try:
        g.neighbours(e.id, depth=999)
        assert False, "must raise"
    except ValueError:
        pass
    print("regression malformed OK")

def test_zero_originator_no_blowup():
    g = TemporalGraph()
    r = PriceDiscoveryAgent().run(g, {"chain": [
        {"asset": "A", "move_pct": 0.0, "timestamp": "2026-09-23T01:00:00+00:00"},
        {"asset": "B", "move_pct": 5.0, "timestamp": "2026-09-23T02:00:00+00:00"}]})
    assert r.data["legs"][0]["transmission"] is None
    print("regression zero-move OK")

def test_naive_datetime_defaults_utc():
    a = Article(source="X", headline="Y", published_at="2026-11-01T01:30:00")
    assert str(a.published_at.tzinfo) == "UTC", a.published_at
    print("regression tz OK")

def test_as_of_never_leaks_future():
    s = TemporalStore()
    e = s.add_node("Event", id="evt_l")
    a = s.add_node("Asset", id="a_l")
    s.add_edge("EVENT_AFFECTS", e.id, a.id, confidence=0.9,
               valid_from="2026-09-24T00:00:00+00:00", txn_time="2026-09-24T00:00:00+00:00")
    assert s.as_of("2026-09-23T00:00:00+00:00")["edges"] == []
    s.close()
    print("regression no-look-ahead OK")
