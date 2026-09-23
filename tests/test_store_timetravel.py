"""I1 verify — time-travel: as_of(t1) differs from as_of(t2), no look-ahead."""
from graph_intel.store import TemporalStore

def test_store_timetravel():
    s = TemporalStore()
    e = s.add_node("Event", id="evt_t")
    oil = s.add_node("Commodity", id="commodity_brent")
    x = s.add_node("Asset", id="asset_x")
    s.add_edge("EVENT_AFFECTS", e.id, oil.id, confidence=0.5, strength=0.5,
                 valid_from="2026-09-23T04:00:00+00:00", txn_time="2026-09-23T04:00:00+00:00")
    s.add_edge("EVENT_TRANSMITS_TO", oil.id, x.id, confidence=0.4,
               strength=0.4, valid_from="2026-09-23T05:00:00+00:00",
               txn_time="2026-09-23T05:00:00+00:00")
    s.supersede_edge("EVENT_AFFECTS", e.id, oil.id, confidence=0.9, strength=0.9,
                     valid_from="2026-09-23T07:00:00+00:00", at="2026-09-23T07:00:00+00:00")
    early = s.as_of("2026-09-23T06:30:00+00:00")
    late = s.as_of("2026-09-23T08:00:00+00:00")
    early_confs = [e2["type"] for e2 in early["edges"]]
    assert "EVENT_AFFECTS" in early_confs and "EVENT_TRANSMITS_TO" in early_confs
    late_aff = [e2 for e2 in late["edges"] if e2["type"] == "EVENT_AFFECTS"]
    assert len(late_aff) == 1, "superseded edge must close old version"
    hist = s.edge_history(e.id, oil.id, "EVENT_AFFECTS")
    assert len(hist) == 2 and hist[0]["valid_to"] is not None
    v = s.snapshot_version("i1-check")
    assert v["version"] == 1
    s.close()
    print(f"I1 PASS | early_edges={len(early['edges'])} late_edges={len(late['edges'])} hist={len(hist)}")

if __name__ == "__main__":
    test_store_timetravel()
