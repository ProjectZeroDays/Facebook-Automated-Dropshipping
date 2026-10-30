"""
fbm/samples.py — autonomous sample ordering + supplier quality gating.

  python -m fbm.samples --plan         # what would be ordered
  python -m fbm.samples --order        # place them (budget-governed)
  python -m fbm.samples --score        # latency-based supplier scoring
"""
from __future__ import annotations
import argparse, os
from datetime import datetime
from fbm import core as C
from fbm import suppliers as Suppliers
# lowercase alias for test compatibility
suppliers = Suppliers


def alias_for(sku):
    dom = os.getenv("ORDER_ALIAS_DOMAIN", "yourdomain.com")
    return f"samples+{sku}@{dom}"


def pending(tenant_id=C.DEFAULT_TENANT_ID):
    with C.db() as c:
        return c.execute("SELECT s.* FROM skus s LEFT JOIN samples sm "
                         "ON sm.sku=s.sku AND sm.tenant_id=? "
                         "WHERE s.active=1 AND s.tenant_id=? AND sm.sku IS NULL",
                         (tenant_id, tenant_id)).fetchall()


def month_spend(tenant_id=C.DEFAULT_TENANT_ID):
    with C.db() as c:
        r = c.execute("SELECT COALESCE(SUM(cost),0) v FROM samples "
                      "WHERE strftime('%Y-%m', ordered_at)=strftime('%Y-%m','now') "
                      "AND tenant_id=?", (tenant_id,)).fetchone()
    return float(r["v"])


def order(dry=False, tenant_id=C.DEFAULT_TENANT_ID):
    budget = float(os.getenv("SAMPLE_BUDGET_MONTH", "150"))
    cap = float(os.getenv("SAMPLE_MAX_COST", "30"))
    addr = os.getenv("SAMPLE_ADDRESS", "")
    spend = month_spend(tenant_id); placed = []
    for s in pending(tenant_id):
        cost = float(s["cost"] or 0)
        if cost > cap or spend + cost > budget:
            print(f"skip {s['sku']} (cost {cost}, spend {spend:.2f}/{budget})"); continue
        if dry:
            print(f"would order {s['sku']} via {s['source']}"); continue
        try:
            used = Suppliers.place_order(dict(s), {"fingerprint": f"SAMPLE-{s['sku']}",
                                                   "buyer": "SAMPLE", "address": addr,
                                                   "title": s["title"], "account": "sample"})
            with C.db() as c:
                c.execute("INSERT OR REPLACE INTO samples(sku,supplier,ordered_at,cost,verdict,tenant_id) "
                          "VALUES(?,?,datetime('now'),?,'ordered',?)",
                          (s["sku"], used, cost, tenant_id))
            spend += cost; placed.append(s["sku"]); print(f"ordered sample {s['sku']} via {used}")
        except Exception as e:
            C.notify(f"sample order failed {s['sku']}: {e}", "warn")
    return placed


def score(tenant_id=C.DEFAULT_TENANT_ID):
    """Latency = first tracking scan - order time. Demote slow suppliers."""
    with C.db() as c:
        rows = c.execute("SELECT s.sku, s.supplier, s.ordered_at, o.created_at scan_at "
                         "FROM samples s JOIN orders o ON o.sku=s.sku AND o.tenant_id=? "
                         "WHERE o.tracking IS NOT NULL AND s.verdict='ordered' AND s.tenant_id=?",
                         (tenant_id, tenant_id)).fetchall()
    limit = float(os.getenv("SAMPLE_LATENCY_LIMIT_DAYS", "2"))
    for r in rows:
        days = (datetime.fromisoformat(r["scan_at"]) - datetime.fromisoformat(r["ordered_at"])).days
        verdict = "pass" if days <= limit else "fail"
        with C.db() as c:
            c.execute("UPDATE samples SET verdict=?, latency_days=? WHERE sku=? AND tenant_id=?",
                      (verdict, days, r["sku"], tenant_id))
            if verdict == "fail":
                c.execute("UPDATE skus SET active=0 WHERE sku=? AND backup_source IS NULL AND tenant_id=?",
                          (r["sku"], tenant_id))
                c.execute("INSERT INTO events(kind,ref,detail,tenant_id) VALUES('sample_fail',?,?,?)",
                          (r["sku"], f"{r['supplier']} took {days}d (>{limit})", tenant_id))
        if verdict == "fail":
            C.notify(f"SAMPLE FAIL {r['sku']}: {r['supplier']} {days}d - SKU demoted", "warn")
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--plan", action="store_true")
    ap.add_argument("--order", action="store_true"); ap.add_argument("--score", action="store_true")
    a = ap.parse_args(); C.load_env(); C.init_db()
    if a.score: score()
    else: order(dry=a.plan)