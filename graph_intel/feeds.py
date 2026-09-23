"""I3 — free feed adapters: GDELT, RSS, STOOQ/yfinance. Parsing only; callers handle HTTP."""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List

GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
CENTRAL_BANK_FEEDS = {
    "fed": "https://www.federalreserve.gov/feeds/press_all.xml",
    "ecb": "https://www.ecb.europa.eu/rss/press.html",
    "boj": "https://www.boj.or.jp/en/rss/whatsnew.xml",
    "rba": "https://www.rba.gov.au/rss/rss.xml",
}

def parse_gdelt_articles(payload: Dict[str, Any], source_tier: str = "data_provider") -> List[Dict[str, Any]]:
    out = []
    for a in payload.get("articles", []):
        if not a.get("title") or not a.get("url"):
            continue
        out.append({
            "source": a.get("sourceCommonName") or a.get("domain", "gdelt"),
            "headline": a["title"].strip(),
            "body": a.get("excerpt", ""),
            "published_at": a.get("seendate") or datetime.now().astimezone().isoformat(),
            "source_tier": source_tier,
            "entities": a.get("entities", []),
        })
    return out

def _entry_get(e: Any, key: str, default: str = "") -> str:
    if isinstance(e, dict):
        return e.get(key, default) or default
    return getattr(e, key, default) or default

def parse_rss_entries(feed: Any, source: str, source_tier: str = "central_bank") -> List[Dict[str, Any]]:
    entries = getattr(feed, "entries", None)
    if entries is None:
        entries = feed if isinstance(feed, list) else [feed]
    out = []
    for e in entries or []:
        title = _entry_get(e, "title")
        link = _entry_get(e, "link")
        if not title:
            continue
        pub = None
        try:
            import time as _t
            from datetime import timezone
            pl = getattr(e, "published_parsed", None) if not isinstance(e, dict) else None
            pub = datetime.fromtimestamp(_t.mktime(pl), tz=timezone.utc).isoformat() if pl else None
        except Exception:
            pub = None
        out.append({
            "source": source,
            "headline": title.strip(),
            "body": _entry_get(e, "summary") + f" {link}",
            "published_at": pub or datetime.now().astimezone().isoformat(),
            "source_tier": source_tier,
        })
    return out

def parse_stooq_csv(text: str, symbol: str, region: str = "unknown") -> List[Dict[str, Any]]:
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    if len(lines) < 2:
        return []
    header = [h.strip().lower() for h in lines[0].split(",")]
    try:
        di, ci = header.index("date"), header.index("close")
    except ValueError:
        return []
    out = []
    for ln in lines[1:]:
        parts = ln.split(",")
        try:
            out.append({"symbol": symbol, "price": float(parts[ci]),
                        "timestamp": datetime.fromisoformat(parts[di]).isoformat(),
                        "region": region})
        except Exception:
            continue
    return out
