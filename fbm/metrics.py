"""
fbm/metrics.py — Prometheus exporter for the FBM stack.
"""
from __future__ import annotations
from prometheus_client import Gauge, Counter, generate_latest, CONTENT_TYPE_LATEST
from fbm import core as C
from fbm.observability import get_logger

log = get_logger("metrics")

g_active = Gauge("fbm_listings_active", "active listings")
g_new = Gauge("fbm_orders_new", "orders needing action")
g_overdue = Gauge("fbm_orders_overdue", "orders past ship deadline")
g_comps = Gauge("fbm_comps_rows", "scraped comps rows")
g_skus = Gauge("fbm_skus_active", "active SKUs")
g_last = Gauge("fbm_last_run_timestamp", "last successful run (unix)")
c_actions = Counter("fbm_actions_total", "actions taken", ["kind"])


def refresh(tenant_id=C.DEFAULT_TENANT_ID):
    with C.db() as c:
        counts = {
            "active": c.execute("SELECT COUNT(*) n FROM listings WHERE status='active' AND tenant_id=?",
                                (tenant_id,)).fetchone()["n"],
            "new": c.execute("SELECT COUNT(*) n FROM orders WHERE status='NEW' AND tenant_id=?",
                             (tenant_id,)).fetchone()["n"],
            "overdue": c.execute("SELECT COUNT(*) n FROM orders WHERE status IN ('NEW','ORDERED') "
                                 "AND created_at < datetime('now','-2 day') AND tenant_id=?",
                                 (tenant_id,)).fetchone()["n"],
            "comps": c.execute("SELECT COUNT(*) n FROM comps WHERE tenant_id=?",
                               (tenant_id,)).fetchone()["n"],
            "skus": c.execute("SELECT COUNT(*) n FROM skus WHERE active=1 AND tenant_id=?",
                              (tenant_id,)).fetchone()["n"],
        }
    g_active.set(counts["active"])
    g_new.set(counts["new"])
    g_overdue.set(counts["overdue"])
    g_comps.set(counts["comps"])
    g_skus.set(counts["skus"])
    log.info("metrics refreshed", extra={"event": "metrics.refresh", "component": "metrics", **counts})


def render():
    refresh()
    return generate_latest(), CONTENT_TYPE_LATEST