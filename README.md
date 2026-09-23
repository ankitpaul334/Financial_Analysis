# Global Cross-Market Graph Intelligence

Multi-agent financial intelligence system over a shared **temporal knowledge graph**.
See `AGENTS.md` for the full architecture spec (source of truth).

## Layout

```text
graph_intel/
  graph.py              # TemporalGraph: typed nodes/edges, traversal, subgraphs
  agents/
    base.py             # BaseAgent / AgentResult interface
    ingestion.py        # Agent 1 — normalize news + market ticks (dedup, no reasoning)
    entity_resolution.py# Agent 2 — alias to canonical node mapping
    event_extraction.py # Agent 3 — headline/body to structured event (rule-based v1)
    expansion.py        # Agent 4 — ranked 2nd/3rd-order exposure subgraph
    observers.py        # Agent 5 — parallel regional observers (JP/EU/AU/ME/US)
    reasoner.py         # Agent 6 — cross-market snapshot: overseas vs US residual
    price_discovery.py  # Agent 7 — temporal repricing chain
    dislocation.py      # Agent 8 — 5-gate candidate filter
    validation.py       # Agents 9-12 — quant, counterfactual, falsification, risk
    decision.py         # Agents 13-15 — decision, execution gate, outcome learning
tests/
  test_pipeline.py      # end-to-end pipeline test (all 15 agents)
```

## Run

```powershell
python -m tests.test_pipeline
```

Expected: `ALL 15 AGENTS PASS`.

## Session 2026-09-23

- Built: shared graph + all 15 agent specs (19 runtime with regional observers).
- Fixes: ingestion dedup + source tiers (v2), entity canonical merge
  (`NASDAQ:NVDA` now maps to `company_nvidia`), pipeline test syntax fix.
- Remaining: rule-based extraction only (LLM extractor next), no
  timezone/session logic, no live feeds, toy quant series, no
  persistence/scheduler/signal expiry.
- Next: Agent 3 LLM-backed extraction + timezone-aware temporal layer.
