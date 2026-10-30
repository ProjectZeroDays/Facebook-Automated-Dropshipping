"""default_agents.py — register specialized subagents.

Agents: research, copy, support, ops, pricing, inventory.
Each agent is a callable that takes a task description and returns a result.
"""
from __future__ import annotations
import fbm_core as C
import agents as Ag
import fbm.scraper as Scraper
import fbm.targets as Targets
import fbm.reprice as Reprice
import fbm.copygen as Copygen
import fbm.validate as Validate
import fbm.suppliers as Suppliers
import fbm.tracking as Tracking
import fbm.returns as Returns

def agent_research(task: str) -> dict:
    """Research agent: find products, validate niches, check competition."""
    from fbm.scraper import scrape_query
    from fbm_core import session
    result = {"agent": "research", "task": task, "findings": []}
    C.notify(f"agent research: {task}", "info")
    return result

def agent_copy(task: str) -> dict:
    """Copy agent: generate listing titles and descriptions."""
    from fbm.copygen import offline
    result = {"agent": "copy", "task": task, "variants": []}
    return result

def agent_support(task: str) -> dict:
    """Support agent: classify buyer intent, draft replies, handle returns."""
    from fbm.returns import classify, reply
    intent = classify(task)
    reply_text = reply(task) if intent else (None, None)
    return {"agent": "support", "intent": intent, "reply": reply_text[1] if reply_text else None}

def agent_ops(task: str) -> dict:
    """Ops agent: check status, backups, health, alerts."""
    from fbm.deadman import escalate
    overdue = escalate()
    return {"agent": "ops", "overdue_orders": overdue}

def agent_pricing(task: str) -> dict:
    """Pricing agent: scrape comps, suggest prices, apply repricing."""
    changed = Reprice.run()
    return {"agent": "pricing", "repriced": len(changed)}

def agent_inventory(task: str) -> dict:
    """Inventory agent: check SKUs, suppliers, reorder samples."""
    from fbm.samples import pending
    p = pending()
    return {"agent": "inventory", "pending_samples": len(p)}

AGENT_REGISTRY = {
    "research": (agent_research, "Product research and niche validation"),
    "copy": (agent_copy, "Generate listing copy and variants"),
    "support": (agent_support, "Buyer message classification and replies"),
    "ops": (agent_ops, "Operations health and alerts"),
    "pricing": (agent_pricing, "Competitor scraping and repricing"),
    "inventory": (agent_inventory, "SKU and supplier management"),
}

def register_all() -> int:
    for name, (fn, help_text) in AGENT_REGISTRY.items():
        Ag.register(name, fn)
    return len(AGENT_REGISTRY)

def run_agent(name: str, task: str) -> dict:
    return Ag.run(name, task)

def main():
    C.load_env()
    n = register_all()
    print(f"Registered {n} agents")
    print("default_agents ok")

if __name__ == "__main__":
    main()
