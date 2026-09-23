# AGENTS.md — Global Cross-Market Graph Intelligence System

## 1. Mission

Build a continuously running multi-agent financial intelligence system that models global news, markets, assets, companies, sectors, commodities, currencies, macro events, and timezones as a **dynamic temporal knowledge graph**.

The system should not process each news article independently.

Instead, it should:

1. ingest many news and market observations simultaneously,
2. convert them into graph entities and relationships,
3. connect new events to affected assets and markets,
4. propagate information through the graph,
5. compare overseas price discovery with U.S. pricing,
6. detect statistically meaningful cross-market dislocations,
7. challenge the hypothesis with independent agents,
8. produce a decision,
9. optionally execute an approved action through a separate execution layer.

The central idea is:

> **Use the graph as the shared state of the world, and use agents to reason over different subgraphs of that state.**

---

# 2. Core Hypothesis

Global markets operate asynchronously.

An event may be discovered and priced in Japan, Australia, Europe, or the Middle East before the U.S. cash market opens.

However, do NOT assume:

`Overseas move → U.S. opportunity`

Instead test:

`New event → overseas repricing → connected asset graph → U.S. exposure → existing U.S. pricing → residual discrepancy → validation → action`

A candidate is only valid when the graph and quantitative evidence support the existence of a meaningful discrepancy after accounting for:

- U.S. futures
- ADRs
- ETFs
- FX
- commodities
- bonds
- market hours
- liquidity
- spreads
- slippage
- existing U.S. news
- security-specific exposure
- historical relationship stability.

---

# 3. Graph-First Architecture

The graph is the system's shared memory.

## Primary node types

```text
Event
NewsArticle
Source
Country
Region
Exchange
Market
Asset
Stock
ETF
ADR
Future
Commodity
Currency
Bond
Sector
Company
Industry
SupplyChainEntity
CentralBank
Government
EconomicIndicator
TimeWindow
TradingSession
HistoricalObservation
Signal
Decision
Execution
RiskFactor
```

## Important edge types

```text
EVENT_REPORTED_BY
EVENT_AFFECTS
EVENT_ORIGINATED_IN
EVENT_OCCURS_AT
NEWS_SUPPORTS
NEWS_CONTRADICTS
ASSET_EXPOSED_TO
COMPANY_BELONGS_TO
COMPANY_SUPPLIES
COMPANY_DEPENDS_ON
ASSET_TRACKS
ASSET_CORRELATES_WITH
ASSET_LEADS
ASSET_LAGS
ASSET_HEDGES
MARKET_TRADES_ON
MARKET_CLOSED_DURING
MARKET_OPEN_DURING
ASSET_PRICED_BY
EVENT_TRANSMITS_TO
EVENT_IMPACTS
SIGNAL_DERIVED_FROM
SIGNAL_CONTRADICTED_BY
SIGNAL_VALIDATED_BY
SIGNAL_REJECTED_BY
DECISION_BASED_ON
EXECUTION_FOR
```

Every relationship should support temporal metadata where possible:

```text
start_time
end_time
confidence
source
strength
observation_window
```

---

# 4. Temporal Graph

Time is a first-class dimension.

Represent:

- UTC timestamp
- local market timestamp
- timezone
- market session
- pre-market
- regular session
- after-hours
- holiday
- daylight-saving status.

Never reason only from publication time.

Track three timestamps separately:

```text
event_time
publication_time
market_reaction_time
```

This allows the system to determine whether an apparent information gap actually existed.

---

# 5. Agent Architecture

## Agent 1 — Ingestion Agent

Continuously ingest:

- global news
- exchange data
- index data
- stock prices
- futures
- FX
- commodities
- bonds
- economic releases
- company announcements
- central-bank announcements.

Normalize all data into a common event format.

Do not perform final reasoning here.

Output:

```json
{
  "event_id": "...",
  "timestamp": "...",
  "source": "...",
  "entities": [],
  "raw_claims": [],
  "market_observations": []
}
```

---

# 6. Agent 2 — Entity Resolution Agent

Resolve entities across sources.

Example:

```text
NVIDIA
NVDA
Nvidia Corp.
NASDAQ:NVDA
```

must map to the same canonical Company/Asset nodes.

Resolve:

- companies
- tickers
- exchanges
- commodities
- currencies
- countries
- sectors
- indices.

Never create duplicate graph nodes when an existing canonical entity can be identified.

---

# 7. Agent 3 — Event Extraction Agent

Convert unstructured news into structured events.

Extract:

```text
what happened
who/what is affected
where
when
why
expected economic mechanism
surprise component
confidence
```

Example:

```text
Event:
Australian iron ore export disruption

Nodes:
Australia
Iron Ore
Mining
Steel
Australian producers
Global commodity prices
U.S. industrial companies

Edges:
EVENT_AFFECTS
EVENT_TRANSMITS_TO
SUPPLY_CHAIN_DEPENDENCY
```

---

# 8. Agent 4 — Graph Expansion Agent

Starting from a new event, traverse the graph to discover second- and third-order exposures.

Example:

```text
Middle East geopolitical event
        ↓
Oil supply
        ↓
Brent
        ↓
WTI
        ↓
U.S. energy producers
        ↓
Airlines
        ↓
Transportation
        ↓
Inflation expectations
        ↓
Treasury yields
        ↓
Growth stocks
        ↓
Nasdaq
```

Do not blindly traverse every relationship.

Prioritize edges using:

```text
economic relevance
historical relationship strength
recency
confidence
materiality
```

Return a ranked event subgraph.

---

# 9. Agent 5 — Parallel Market Observer Agents

Run market observers concurrently by region.

## Japan Agent

Observe:

- Nikkei
- TOPIX
- sectors
- major stocks
- FX
- rates
- relevant commodities.

## Europe Agent

Observe:

- major European indexes
- sectors
- major companies
- EUR/GBP/CHF
- bonds
- commodities.

## Australia Agent

Observe:

- ASX
- mining
- banks
- AUD
- commodities.

## Middle East Agent

Observe:

- regional equity indexes
- oil
- gas
- FX
- sovereign markets
- geopolitical assets.

## U.S. Agent

Observe:

- S&P futures
- Nasdaq futures
- Dow futures
- sector ETFs
- stocks
- ADRs
- Treasury yields
- USD
- commodities
- volatility.

All regional agents write observations into the same graph.

---

# 10. Agent 6 — Simultaneous Cross-Market Reasoner

This is the core graph agent.

Do not ask:

> "What happened in Japan?"

Ask:

> "What changed across the connected global graph during the same information window?"

Construct a temporal snapshot:

```text
GLOBAL GRAPH STATE(t)
```

Compare:

```text
Event intensity
+
Overseas price response
+
Connected asset response
+
U.S. current pricing
+
Historical expected transmission
```

The agent should reason across multiple subgraphs simultaneously.

---

# 11. Agent 7 — Price Discovery Agent

For every event determine:

```text
Where was the information first reflected?
Which asset moved first?
Which connected asset moved second?
Which markets have not reacted?
```

Build a directed temporal chain:

```text
Event
 ↓
Originating asset
 ↓
Regional asset
 ↓
Global proxy
 ↓
U.S. proxy
 ↓
U.S. security
```

Estimate:

```text
lead_time
lag_time
transmission_strength
historical_consistency
```

---

# 12. Agent 8 — Dislocation Detector

Search the graph for:

```text
Observed overseas move
        vs
Expected U.S. move
```

A candidate requires:

```text
NEW INFORMATION
+
MEANINGFUL OVERSEAS REPRICING
+
CONNECTED U.S. EXPOSURE
+
U.S. PRICING DISCREPANCY
+
HISTORICAL SUPPORT
```

Reject when:

```text
U.S. futures already moved
OR
ADR already adjusted
OR
FX explains the difference
OR
commodity market already transmitted the information
OR
relationship is historically unstable
OR
liquidity is insufficient.
```

---

# 13. Agent 9 — Quantitative Graph Analytics Agent

Run quantitative analysis over graph relationships.

Useful measurements include:

- rolling correlation
- beta
- lead-lag correlation
- residual
- z-score
- volatility-adjusted move
- event-study abnormal return
- conditional response
- historical hit rate
- transmission delay
- regime-specific behavior.

Use graph structure to choose the relevant comparison assets rather than manually hardcoding every pair.

Example:

```text
Event
→ Commodity
→ Sector
→ Company
```

can generate a candidate relationship automatically.

---

# 14. Agent 10 — Counterfactual Agent

Ask:

> "If this overseas event had not happened, what would we expect the U.S. asset to do?"

Estimate a baseline using:

- historical market behavior
- sector movement
- broader index movement
- FX
- commodity prices
- volatility
- contemporaneous U.S. news.

Then compare:

```text
Expected U.S. move
vs
Observed U.S. move
```

The difference is the candidate residual.

---

# 15. Agent 11 — Falsification Agent

Its only goal is to disprove the signal.

Search the graph for contradictory paths.

Example:

```text
News Event
 ↓
Oil ↑
 ↓
Energy stocks ↑

BUT

U.S. inflation data
 ↓
Treasury yields ↑
 ↓
Energy sector relative move explained
```

If an alternative causal path explains the discrepancy, downgrade or reject the signal.

Never allow the system to become an opportunity-confirmation machine.

---

# 16. Agent 12 — Risk Agent

Evaluate:

- liquidity
- spread
- slippage
- volatility
- gap risk
- market opening risk
- event risk
- correlation breakdown
- execution delay
- short availability
- position concentration.

Calculate:

```text
Expected Gross Edge
-
Transaction Costs
-
Execution Risk
-
Model Uncertainty
=
Estimated Net Edge
```

If net edge is not sufficiently supported:

```text
REJECT
```

---

# 17. Agent 13 — Decision Agent

The decision agent receives only validated graph evidence.

Possible outputs:

```text
NO ACTION
WATCH
RESEARCH SIGNAL
ACTION CANDIDATE
```

It must provide:

```text
event
graph path
supporting evidence
contradicting evidence
price discrepancy
historical evidence
risk
confidence
reason for decision
```

Do not convert confidence into guaranteed probability of profit.

---

# 18. Agent 14 — Execution Agent

Execution must be separated from research.

The research system may produce:

```text
ACTION_CANDIDATE
```

The execution layer independently verifies:

- current price
- current spread
- market status
- position limits
- risk limits
- stale-signal timeout
- user authorization.

Only then may an execution tool/API be called.

Never let an LLM directly execute an order solely from free-form reasoning.

Require structured machine-readable authorization:

```json
{
  "signal_id": "...",
  "asset": "...",
  "action": "...",
  "max_position": "...",
  "max_loss": "...",
  "expires_at": "...",
  "risk_approved": true
}
```

---

# 19. Agent 15 — Outcome Learning Agent

After the U.S. market reacts, attach the outcome to the original graph.

Record:

```text
signal_time
opening_price
30m_price
1h_price
close
expected_move
realized_move
transaction_cost_assumption
signal_status
```

Create feedback edges:

```text
SIGNAL
 ↓
OUTCOME
 ↓
MODEL_PERFORMANCE
```

Use this to identify:

- successful graph patterns
- false positives
- unstable relationships
- regime changes
- unreliable sources
- excessive latency.

Do not automatically retrain a strategy from a single outcome.

---

# 20. Shared Graph Memory

Agents should not communicate primarily through long text.

Use structured graph state.

Example:

```json
{
  "event_id": "evt_123",
  "nodes": ["oil", "middle_east", "brent", "xle", "airlines"],
  "edges": [
    {
      "type": "EVENT_AFFECTS",
      "from": "evt_123",
      "to": "brent",
      "confidence": 0.92
    }
  ],
  "observations": [],
  "signals": [],
  "contradictions": []
}
```

LLM messages should contain reasoning summaries and references to graph objects, not duplicated market data.

---

# 21. Graph Query Strategy

Prefer targeted subgraph queries.

Example:

```text
Find all U.S. assets within 3 economically meaningful hops
from an event occurring in Australia
where:

overseas_return > threshold
AND
historical_lead_lag_strength > threshold
AND
current_US_residual > threshold.
```

Another:

```text
Find events where:

event → foreign_asset
foreign_asset → sector
sector → US_asset

and

foreign_asset has already repriced
but US_asset has not.
```

---

# 22. Confidence Model

Do not use a single LLM confidence score.

Build confidence from independent evidence:

```text
Source Reliability
+
Event Confidence
+
Market Reaction Strength
+
Graph Relationship Strength
+
Historical Stability
+
Statistical Significance
+
U.S. Pricing Gap
-
Contradictory Evidence
-
Execution Friction
```

Every component should remain inspectable.

---

# 23. Source Hierarchy

Prefer:

1. official government sources
2. central banks
3. exchanges
4. company filings / investor relations
5. established financial data providers
6. reputable financial news
7. specialist publications
8. social media

Social media may provide early detection but must not automatically be treated as confirmed information.

---

# 24. Event Deduplication

Multiple articles about the same event should become:

```text
ONE EVENT NODE
```

with multiple:

```text
NEWS_ARTICLE
```

nodes attached to it.

This prevents the system from interpreting 30 articles about one event as 30 independent signals.

---

# 25. Graph Example

Example:

```text
                 [Geopolitical Event]
                         |
                  EVENT_AFFECTS
                         |
                       [Oil]
                    /          \
                 [Brent]      [WTI]
                    |            |
               [Europe]        [US]
                    |            |
              [Energy Sector] [Energy ETF]
                    \            /
                     \          /
                      [US Equity]
```

At the same time:

```text
[Event]
   |
[Oil]
   |
[Inflation]
   |
[US Treasury Yields]
   |
[Growth Stocks]
   |
[Nasdaq]
```

The system should compare both paths.

---

# 26. Multi-Agent Scheduling

Do not wake every agent for every article.

Use an event-driven activation model.

```text
LOW MATERIALITY
→ store only

MEDIUM MATERIALITY
→ activate event + market agents

HIGH MATERIALITY
→ activate full graph investigation

HIGH CONFIDENCE DISLOCATION
→ activate validation + risk + decision agents
```

This reduces compute and token usage.

---

# 27. Parallelism

Run independent agents concurrently.

For example:

```text
                 EVENT
                   |
       ┌───────────┼───────────┐
       ↓           ↓           ↓
   Japan Agent Europe Agent Australia Agent
       ↓           ↓           ↓
       └───────────┼───────────┘
                   ↓
            Graph Reasoner
                   ↓
          U.S. Transmission
                   ↓
         Quant Validation
            ↙           ↘
     Falsification     Risk
            \           /
             \         /
              Decision
```

Agents should converge on shared structured state rather than serially passing long prompts.

---

# 28. Final Decision Schema

Every candidate must produce:

```json
{
  "signal_id": "...",
  "event": "...",
  "timestamp": "...",

  "origin_market": "...",

  "graph_path": [],

  "overseas_reaction": {
    "asset": "...",
    "move": 0,
    "volume_change": 0
  },

  "us_exposure": {
    "asset": "...",
    "observed_move": 0,
    "expected_move": 0,
    "residual": 0
  },

  "already_priced_checks": [],

  "contradictions": [],

  "historical_validation": {},

  "execution_constraints": {},

  "decision": "NO_ACTION | WATCH | RESEARCH_SIGNAL | ACTION_CANDIDATE",

  "confidence": {},

  "expiry": "..."
}
```

---

# 29. Non-Negotiable Rules

1. Never equate news with price impact.
2. Never equate price impact with opportunity.
3. Never assume the U.S. market is unaware merely because its cash session is closed.
4. Always check futures, ADRs, ETFs, FX, commodities and bonds.
5. Use the graph to discover indirect exposure.
6. Treat time as part of the graph.
7. Separate event time from publication time.
8. Separate discovery from validation.
9. Separate research from execution.
10. Every signal must have a falsification path.
11. Every decision must be traceable to graph evidence.
12. Never fabricate missing market data.
13. Never use one source as confirmation of itself.
14. Deduplicate news about the same event.
15. Expire stale signals.
16. Store outcomes for evaluation.
17. Prefer fewer high-evidence signals over many speculative ones.
18. The system must be able to return `NO_ACTION`.
19. Never guarantee profit.
20. Human/user authorization is required before real-world execution unless an explicitly configured automated execution policy permits it.

---

# 30. System Objective

The final system should behave like a continuously updating global market graph:

```text
NEWS
  ↓
EVENTS
  ↓
ENTITIES
  ↓
RELATIONSHIPS
  ↓
GLOBAL MARKET STATE
  ↓
TEMPORAL GRAPH
  ↓
CROSS-MARKET PROPAGATION
  ↓
PRICE-DISCOVERY ANALYSIS
  ↓
DISLOCATION DETECTION
  ↓
FALSIFICATION
  ↓
RISK
  ↓
DECISION
  ↓
AUTHORIZED ACTION
  ↓
OUTCOME
  ↓
GRAPH LEARNING
```

The key architectural principle is:

> **Do not build a collection of agents that each read the world independently. Build one shared, temporal global market graph that many specialized agents query, enrich, challenge, and act upon.**
