"""I2 — edge confidence calculus: weighted evidence + depth decay."""
from __future__ import annotations
import math
from typing import Any, Dict

GAMMA = 0.85
WEIGHTS = {"source": 0.25, "z": 0.30, "stability": 0.20, "strength": 0.25}
TIER_SCORE = {1: 1.0, 2: 0.95, 3: 0.9, 4: 0.85, 5: 0.8, 6: 0.6, 7: 0.5, 8: 0.2}

def _clamp(x: float) -> float:
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        return 0.0
    return max(0.0, min(1.0, x))

def _is_bad(x: Any) -> bool:
    return isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x)

def score(source_tier: int = 6, zscore: float = 0.0, stability: float = 0.5,
          strength: float = 0.5, depth: int = 0) -> Dict[str, Any]:
    if _is_bad(zscore) or _is_bad(stability) or _is_bad(strength):
        parts = {"source": 0.0, "z": 0.0, "stability": 0.0, "strength": 0.0}
        return {"confidence": 0.0, "base": 0.0, "depth": depth,
                "components": parts, "invalid_input": True}
    z_norm = _clamp(abs(zscore) / 3.0)
    parts = {
        "source": TIER_SCORE.get(source_tier, 0.6),
        "z": z_norm,
        "stability": _clamp(stability),
        "strength": _clamp(strength),
    }
    base = sum(parts[k] * WEIGHTS[k] for k in WEIGHTS)
    final = round(_clamp(base) * (GAMMA ** depth), 3)
    return {"confidence": final, "base": round(base, 3), "depth": depth, "components": parts}
