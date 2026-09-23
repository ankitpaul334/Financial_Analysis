"""I3 — Pydantic schemas for the data layer."""
from __future__ import annotations
import hashlib
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

def dedup_key(source: str, headline: str) -> str:
    return hashlib.sha256(f"{source.strip().lower()}|{headline.strip().lower()}".encode()).hexdigest()[:12]

class Article(BaseModel):
    source: str
    headline: str
    body: str = ""
    published_at: datetime
    event_time: Optional[datetime] = None
    source_tier: str = "financial_news"
    entities: List[str] = Field(default_factory=list)
    timezone: str = "UTC"

    @field_validator("published_at", "event_time", mode="before")
    @classmethod
    def _tz(cls, v):
        if v is None:
            return v
        if isinstance(v, datetime):
            return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
        dt = datetime.fromisoformat(str(v))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    @property
    def key(self) -> str:
        return dedup_key(self.source, self.headline)

    @property
    def article_id(self) -> str:
        return f"art_{self.key}"

class Tick(BaseModel):
    symbol: str
    price: float
    timestamp: datetime
    region: str = "unknown"
    volume_change: float = 0.0

    @field_validator("symbol", mode="before")
    @classmethod
    def _sym(cls, v):
        return str(v).strip().upper()

class Event(BaseModel):
    event_id: str
    what: str
    mechanism: str
    surprise: float = Field(ge=0.0, le=1.0, default=0.3)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    article_ids: List[str] = Field(default_factory=list)
