"""I5 — single Beta/Residual service + LLM seam (deterministic default)."""
from __future__ import annotations
import math
import statistics
from typing import Any, Callable, Dict, List, Optional

def _finite(xs: List[float]) -> bool:
    return bool(xs) and all(isinstance(v, (int, float)) and not isinstance(v, bool)
                            and math.isfinite(v) for v in xs)

def beta_from_history(series_x: List[float], series_y: List[float]) -> Dict[str, float]:
    if len(series_x) < 3 or len(series_x) != len(series_y):
        return {"beta": 0.6, "correlation": 0.0, "resid_sd": 1.0}
    if not _finite(series_x) or not _finite(series_y):
        return {"beta": 0.6, "correlation": 0.0, "resid_sd": 1.0}
    mx, my = statistics.fmean(series_x), statistics.fmean(series_y)
    num = sum((x - mx) * (y - my) for x, y in zip(series_x, series_y))
    den = math.sqrt(sum((x - mx) ** 2 for x in series_x) * sum((y - my) ** 2 for y in series_y))
    corr = num / (den + 1e-9)
    beta = corr * (statistics.pstdev(series_y) / (statistics.pstdev(series_x) + 1e-9))
    sd = statistics.pstdev([yy - beta * xx for xx, yy in zip(series_x, series_y)]) + 1e-9
    return {"beta": beta, "correlation": corr, "resid_sd": sd}

class BetaResidualService:
    @staticmethod
    def residual(overseas_move: float, observed_us: float, beta: float,
                 resid_sd: float = 1.0) -> Dict[str, Any]:
        for v in (overseas_move, observed_us, beta, resid_sd):
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                return {"expected_us_move": 0.0, "residual": 0.0, "zscore": 0.0,
                        "significant": False, "beta": 0.0, "invalid_input": True}
        expected = overseas_move * beta
        resid = observed_us - expected
        z = resid / (resid_sd + 1e-9)
        return {"expected_us_move": round(expected, 3), "residual": round(resid, 3),
                "zscore": round(z, 3), "significant": abs(z) >= 2.0, "beta": round(beta, 3)}

_extract_fn: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
_explain_fn: Optional[Callable[[Dict[str, Any]], str]] = None

def register_llm(extract_fn=None, explain_fn=None):
    global _extract_fn, _explain_fn
    _extract_fn, _explain_fn = extract_fn, explain_fn

def extract_event(article: Dict[str, Any]) -> Dict[str, Any]:
    if _extract_fn is not None:
        return _extract_fn(article)
    from graph_intel.agents.event_extraction import extract as rule_extract
    return rule_extract(article.get("headline", ""), article.get("body", ""))

def explain_subgraph(subgraph: Dict[str, Any]) -> str:
    if _explain_fn is not None:
        return _explain_fn(subgraph)
    return f"{len(subgraph.get('nodes', []))} nodes, {len(subgraph.get('edges', []))} edges"
