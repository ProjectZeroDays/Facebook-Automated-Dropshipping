"""
fbm/autovars.py — reconcile automated variables.

Reconciles system-derived variables: active SKU count, listing health,
profile utilization, rate limit headroom, and other operational metrics.
"""
from __future__ import annotations
from fbm import core as C


def reconcile(tenant_id=C.DEFAULT_TENANT_ID) -> dict:
    """Return reconciled automated variables for *tenant_id*."""
    C.load_env()
    with C.db() as c:
        active_skus = c.execute("SELECT COUNT(*) n FROM skus WHERE active=1 AND tenant_id=?",
                                (tenant_id,)).fetchone()["n"]
        total_skus = c.execute("SELECT COUNT(*) n FROM skus WHERE tenant_id=?",
                               (tenant_id,)).fetchone()["n"]
        pending_orders = c.execute(
            "SELECT COUNT(*) n FROM orders WHERE status IN ('pending','unfulfilled') AND tenant_id=?",
            (tenant_id,),
        ).fetchone()["n"]
        overdue = c.execute(
            "SELECT COUNT(*) n FROM orders WHERE status='pending' "
            "AND created_at < datetime('now', '-2 days') AND tenant_id=?",
            (tenant_id,),
        ).fetchone()["n"]

    return {
        "tenant_id": tenant_id,
        "active_skus": active_skus,
        "total_skus": total_skus,
        "pending_orders": pending_orders,
        "overdue_orders": overdue,
        "listing_utilization": round(active_skus / max(total_skus, 1) * 100, 1),
    }


def main():
    C.load_env(); C.init_db()
    print(reconcile())
    print("autovars ok")


if __name__ == "__main__":
    main()