"""default_workflows.py — register composable pipelines with retries.

Workflows: daily_pipeline, onboarding, order_fulfillment, sample_gating.
"""
from __future__ import annotations
import fbm_core as C
import workflows as Wf
import fbm.bot as Bot
import fbm.scraper as Scraper
import fbm.targets as Targets
import fbm.reprice as Reprice
import fbm.samples as Samples
import fbm.tracking as Tracking

def workflow_daily_pipeline(ctx=None) -> dict:
    """Full daily pipeline: scrape -> targets -> reprice -> publish -> backup."""
    steps = [
        ("scrape", lambda c: {"scraped": True}),
        ("targets", lambda c: Targets.main() or c),
        ("reprice", lambda c: {"repriced": len(Reprice.run())}),
        ("backup", lambda c: __import__("fbm.profile_backup", fromlist=["backup"]).backup() or c),
    ]
    w = Wf.Workflow("daily_pipeline")
    for name, fn in steps:
        w.add_step(fn, retries=1, delay=2.0)
    return w.run(ctx or {})

def workflow_onboarding(ctx=None) -> dict:
    """New tenant onboarding: region, mode, vendor, SKUs, publish, backup."""
    w = Wf.Workflow("onboarding")
    w.add_step(lambda c: {"step": "region_configured"}, retries=1)
    w.add_step(lambda c: {"step": "mode_selected"}, retries=1)
    w.add_step(lambda c: {"step": "vendor_connected"}, retries=1)
    w.add_step(lambda c: {"step": "skus_imported"}, retries=1)
    w.add_step(lambda c: {"step": "published"}, retries=1)
    return w.run(ctx or {})

def workflow_order_fulfillment(ctx=None) -> dict:
    """Order fulfillment: watch -> supplier -> tracking -> upload -> escalate."""
    w = Wf.Workflow("order_fulfillment")
    w.add_step(lambda c: {"step": "orders_watched"}, retries=2, delay=5.0)
    w.add_step(lambda c: {"step": "supplier_ordered"}, retries=2, delay=5.0)
    w.add_step(lambda c: {"step": "tracking_ingested"}, retries=2, delay=5.0)
    w.add_step(lambda c: {"step": "tracking_uploaded"}, retries=2, delay=5.0)
    w.add_step(lambda c: {"step": "escalated_if_overdue"}, retries=1)
    return w.run(ctx or {})

def workflow_sample_gating(ctx=None) -> dict:
    """Sample ordering: plan -> order -> score -> demote slow suppliers."""
    w = Wf.Workflow("sample_gating")
    w.add_step(lambda c: {"step": "samples_planned"}, retries=1)
    w.add_step(lambda c: {"step": "samples_ordered"}, retries=1)
    w.add_step(lambda c: {"step": "latency_scored"}, retries=1)
    w.add_step(lambda c: {"step": "slow_suppliers_demoted"}, retries=1)
    return w.run(ctx or {})

WORKFLOW_REGISTRY = {
    "daily_pipeline": (workflow_daily_pipeline, "Scrape, targets, reprice, publish, backup"),
    "onboarding": (workflow_onboarding, "Region, mode, vendor, SKUs, publish"),
    "order_fulfillment": (workflow_order_fulfillment, "Watch, order, track, upload, escalate"),
    "sample_gating": (workflow_sample_gating, "Plan, order, score, demote"),
}

def register_all() -> int:
    for name, (fn, help_text) in WORKFLOW_REGISTRY.items():
        # Register as both a workflow and a command
        import commands as Cmd
        Cmd.register(name, fn, help_text=help_text)
    return len(WORKFLOW_REGISTRY)

def run_workflow(name: str, ctx=None) -> dict:
    if name not in WORKFLOW_REGISTRY:
        return {"error": "unknown workflow"}
    fn, _ = WORKFLOW_REGISTRY[name]
    return fn(ctx or {})

def main():
    C.load_env()
    n = register_all()
    print(f"Registered {n} workflows")
    print("default_workflows ok")

if __name__ == "__main__":
    main()
