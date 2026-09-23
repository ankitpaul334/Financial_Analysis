"""Base agent interface — all agents query/enrich shared TemporalGraph."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict
from graph_intel.graph import TemporalGraph

@dataclass
class AgentResult:
    ok: bool
    data: Dict[str, Any]
    errors: list = None
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class BaseAgent:
    name: str = "base"
    def run(self, graph: TemporalGraph, payload: Dict[str, Any]) -> AgentResult:
        raise NotImplementedError
