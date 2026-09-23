"""I6 — centralized dislocation benchmark: one gate set, composite score."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List

THRESHOLDS = {
    "min_overseas": 0.5, "min_residual": 0.3, "min_z": 2.0,
    "min_hit_rate": 0.55, "min_stability": 0.5, "min_net_bps": 10.0,
    "min_novelty": 0.3, "min_exposure": 0.2,
}
WEIGHTS = {"z": 0.30, "residual": 0.25, "hit": 0.20, "novelty": 0.15, "liquidity": 0.10}
HARD_REJECTS = ("futures_moved", "adr_adjusted", "fx_explains", "commodity_transmitted",
                "illiquid", "unstable")

@dataclass
class DislocationScore:
    passes: bool
    score: float
    gates: Dict[str, bool] = field(default_factory=dict)
    rejects: List[str] = field(default_factory=list)
    decision: str = "NO_ACTION"

def evaluate(overseas_move: float = 0.0, residual: float = 0.0, zscore: float = 0.0,
             hit_rate: float = 0.0, stability: float = 0.0, net_edge_bps: float = 0.0,
             novelty: float = 0.0, exposure: float = 0.0, is_new: bool = False,
             **flags) -> DislocationScore:
    gates = {
        "new_information": bool(is_new) and novelty > THRESHOLDS["min_novelty"],
        "overseas_repricing": abs(overseas_move) >= THRESHOLDS["min_overseas"],
        "us_exposure": exposure > THRESHOLDS["min_exposure"],
        "us_gap": abs(residual) >= THRESHOLDS["min_residual"],
        "statistical": abs(zscore) >= THRESHOLDS["min_z"],
        "historical": hit_rate >= THRESHOLDS["min_hit_rate"] and stability >= THRESHOLDS["min_stability"],
        "economic": net_edge_bps >= THRESHOLDS["min_net_bps"],
    }
    rejects = [k for k in HARD_REJECTS if flags.get(k)]
    z_n = min(1.0, abs(zscore) / 3.0)
    r_n = min(1.0, abs(residual) / 2.0)
    score = round(WEIGHTS["z"] * z_n + WEIGHTS["residual"] * r_n
                  + WEIGHTS["hit"] * hit_rate + WEIGHTS["novelty"] * novelty
                  + WEIGHTS["liquidity"] * (0.0 if flags.get("illiquid") else 1.0), 3)
    passes = all(gates.values()) and not rejects
    decision = "ACTION_CANDIDATE" if passes else (
        "WATCH" if gates["overseas_repricing"] and gates["us_gap"] and not rejects else "NO_ACTION")
    return DislocationScore(passes=passes, score=score, gates=gates,
                            rejects=rejects, decision=decision)
