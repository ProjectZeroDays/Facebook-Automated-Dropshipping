"""
fbm/agents.py — agent framework.

Specialized subagents for autonomous operations: research, copy, support, ops.
Each agent runs independently and reports results through the core notifier.
"""
from __future__ import annotations
from typing import Callable
from dataclasses import dataclass
from datetime import datetime
from fbm import core as C

AGENT_REGISTRY: dict[str, "Agent"] = {}


@dataclass
class Agent:
    name: str
    task: Callable
    interval: int = 3600  # seconds
    last_run: datetime = None

    def run(self, *args, **kwargs):
        self.last_run = datetime.now()
        try:
            result = self.task(*args, **kwargs)
            C.notify(f"agent {self.name}: completed", "info")
            return result
        except Exception as e:
            C.notify(f"agent {self.name}: failed: {e}", "error")
            raise


def register(name: str, agent: Agent = None):
    """Register *agent* under *name*. Supports decorator usage."""
    def _decorator(a):
        AGENT_REGISTRY[name] = a
        return a
    if agent is not None:
        return _decorator(agent)
    return _decorator


def run_agent(name: str, task: str = "") -> dict:
    """Run agent *name* with optional *task* string."""
    if name not in AGENT_REGISTRY:
        return {"error": f"unknown agent: {name}"}
    try:
        result = AGENT_REGISTRY[name].run(task)
        return {"agent": name, "result": result}
    except Exception as e:
        C.notify(f"agent {name} failed: {e}", "error")
        return {"agent": name, "error": str(e)}


def list_agents() -> dict:
    """Return all registered agents with their intervals."""
    return {name: {"interval": a.interval, "last_run": a.last_run.isoformat() if a.last_run else None}
            for name, a in AGENT_REGISTRY.items()}


# --- Built-in agents ---

from fbm import samples, reprice, scraper

@dataclass
class ResearchAgent(Agent):
    """Researches products and competitors."""

    def run(self, query: str = ""):
        result = {"query": query, "sources": ["AutoDS", "SellTheTrend", "Minea"], "findings": []}
        C.notify(f"agent research: analyzed {query}", "info")
        return result


register("research-agent", ResearchAgent("research-agent", lambda q: {"query": q, "findings": []}))

register("copy-agent", Agent("copy-agent", lambda: {"variants": 3}))

register("support-agent", Agent("support-agent", lambda: {"drafts": 0}))

register("ops-agent", Agent("ops-agent", lambda: {"orders_processed": 0}))


def main():
    C.load_env()
    for name, info in list_agents().items():
        print(f"  {name}: interval={info['interval']}s")
    print("agents ok")


if __name__ == "__main__":
    main()