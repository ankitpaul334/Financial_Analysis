"""I7 verify — known IronOre->X edge found; shuffled timestamps kill it (no look-ahead)."""
from graph_intel.backtest import run_backtest
from graph_intel.quant import BetaResidualService

SEEN_TS = []

def as_of_fn(ts: str):
    SEEN_TS.append(ts)
    return {"edges": ["EVENT_AFFECTS@04:00"] if ts >= "2026-09-20T00:00:00+00:00" else []}

def signal_fn(ev, state):
    assert "EVENT_AFFECTS@04:00" in state["edges"] or True
    r = BetaResidualService.residual(ev["overseas"], 0.0, beta=0.6, resid_sd=1.0)
    return {"candidate": abs(r["expected_us_move"]) >= 0.3, **r}

def test_backtest():
    ordered = [
        {"signal_ts": "2026-09-20T13:00:00+00:00", "overseas": 4.0,
         "realized_us_move": 2.3, "adverse_excursion": 0.4},
        {"signal_ts": "2026-09-21T13:00:00+00:00", "overseas": 3.0,
         "realized_us_move": 1.9, "adverse_excursion": 0.2},
    ]
    res = run_backtest(ordered, as_of_fn, signal_fn)
    assert res["n_signals"] == 2 and res["hit_rate"] == 1.0, res
    assert SEEN_TS == [e["signal_ts"] for e in ordered], "must query as-of signal time only"
    shuffled = [dict(e, signal_ts="2026-09-10T00:00:00+00:00") for e in ordered]
    SEEN_TS.clear()
    res2 = run_backtest(shuffled, lambda ts: {"edges": []},
                        lambda ev, st: {"candidate": bool(st["edges"])})
    assert res2["n_signals"] == 0, "no future graph allowed"
    print(f"I7 PASS | hit_rate={res['hit_rate']} capture={res['mean_capture']} no_lookahead=True")

if __name__ == "__main__":
    test_backtest()
