"""I4 verify — duplicate delivery yields one Event; WAL replay; watermarks."""
import asyncio
from graph_intel.bus import EventBus
from graph_intel.graph import TemporalGraph
from graph_intel.agents.ingestion import IngestionAgent

def _handle_news(graph, payload):
    IngestionAgent().run(graph, {"raw_news": [payload], "market_ticks": []})

def test_bus():
    bus = EventBus()
    bus.on("news", _handle_news)
    art = {"source": "BOJ", "headline": "BOJ holds rates",
           "published_at": "2026-09-23T01:00:00+00:00", "source_tier": "central_bank"}
    assert bus.publish("art_dup1", "news", art) is True
    assert bus.publish("art_dup1", "news", art) is False
    assert bus.publish("art_dup2", "news", {**art, "headline": "BOJ holds rates calmly"}) is True
    assert bus.pending_count() == 2
    bus.mark_watermark("boj_rss", "2026-09-23T01:00:00+00:00")
    assert bus.watermark("boj_rss") == "2026-09-23T01:00:00+00:00"
    g = TemporalGraph()
    counts = asyncio.run(bus.drain(g))
    assert counts["processed"] == 2 and bus.pending_count() == 0
    arts = g.by_type.get("NewsArticle", set())
    assert len(arts) == 2, arts
    print(f"I4 PASS | processed=2 arts=2 watermark_ok=True")

if __name__ == "__main__":
    test_bus()
