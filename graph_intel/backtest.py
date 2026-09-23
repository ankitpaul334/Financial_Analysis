"""I7 — event-study backtest over point-in-time graph state (no look-ahead)."""
from __future__ import annotations
import statistics
from typing import Any, Callable, Dict, List

def run_backtest(events: List[Dict[str, Any]],
                 as_of_fn: Callable[[str], Dict[str, Any]],
                 signal_fn: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]) -> Dict[str, Any]:
    hits, captures, excursions = 0, [], []
    for ev in events:
        state = as_of_fn(ev["signal_ts"])
        sig = signal_fn(ev, state)
        if not sig.get("candidate"):
            continue
        realized = float(ev.get("realized_us_move", 0.0))
        expected = float(sig.get("expected_us_move", 0.0))
        err = realized - expected
        captures.append(abs(realized) if abs(err) < abs(expected) + 1e-9 else 0.0)
        excursions.append(float(ev.get("adverse_excursion", 0.0)))
        if abs(err) < 0.3:
            hits += 1
    n = len(captures)
    return {
        "n_signals": n,
        "hit_rate": round(hits / n, 3) if n else 0.0,
        "mean_capture": round(statistics.fmean(captures), 3) if n else 0.0,
        "max_adverse": round(max(excursions), 3) if excursions else 0.0,
        "calibrated": n >= 5,
    }
