"""I3 verify — schemas validate/dedup; feed parsers work on fixtures (no network)."""
from graph_intel.schemas import Article, Tick, dedup_key
from graph_intel.feeds import parse_gdelt_articles, parse_rss_entries, parse_stooq_csv
from types import SimpleNamespace

def test_feeds():
    a1 = Article(source="RBA", headline="Iron ore halted", published_at="2026-09-23T02:00:00+00:00")
    a2 = Article(source="rba ", headline="  iron ore HALTED ", published_at="2026-09-23T02:01:00+00:00")
    assert a1.key == a2.key == dedup_key("RBA", "Iron ore halted")
    assert a1.published_at.tzinfo is not None
    t = Tick(symbol="nikkei", price="39000", timestamp="2026-09-23T00:00:00+00:00", region="japan")
    assert t.symbol == "NIKKEI" and t.price == 39000.0
    g = parse_gdelt_articles({"articles": [
        {"title": "BOJ holds rates", "url": "http://x", "sourceCommonName": "BOJ", "seendate": "2026-09-23T01:00:00+00:00"},
        {"title": "", "url": "http://bad"}]})
    assert len(g) == 1 and g[0]["source"] == "BOJ"
    feed = SimpleNamespace(entries=[SimpleNamespace(title="Fed holds", link="http://f", summary="rates", published_parsed=None)])
    r = parse_rss_entries(feed, "fed")
    assert len(r) == 1 and r[0]["source"] == "fed"
    csv = "Date,Open,High,Low,Close,Volume\n2026-09-22,100,101,99,100.5,1000\nbad,row\n2026-09-23,100.5,102,100,101.0,1200"
    p = parse_stooq_csv(csv, "^SPX", region="us")
    assert len(p) == 2 and p[0]["price"] == 100.5
    print(f"I3 PASS | dedup={a1.key} gdelt=1 rss=1 ticks=2")

if __name__ == "__main__":
    test_feeds()
