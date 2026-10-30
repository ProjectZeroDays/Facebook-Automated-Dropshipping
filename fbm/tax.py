"""
fbm/tax.py — monthly P&L export + 1099-K tracker.
"""
from __future__ import annotations
import argparse, csv
from datetime import datetime
from fbm import core as C
from fbm import config as Config

FEE_RATE = 0.10


def monthly(month=None, tenant_id=C.DEFAULT_TENANT_ID):
    month = month or datetime.now().strftime("%Y-%m")
    with C.db() as c:
        rows = c.execute("SELECT * FROM orders WHERE strftime('%Y-%m',created_at)=? AND tenant_id=?",
                         (month, tenant_id)).fetchall()
        skus = {r["sku"]: r for r in c.execute("SELECT * FROM skus WHERE tenant_id=?",
                                               (tenant_id,)).fetchall()}
    revenue = sum(float(r["price"] or 0) for r in rows)
    cogs = sum(float((skus.get(r["sku"]) or {}).get("cost") or 0) for r in rows)
    refunds = sum(float(r["price"] or 0) for r in rows if r["status"] == "REFUNDED")
    fee_rate = Config.fee_rate()
    fees = revenue * fee_rate
    net = revenue - fees - cogs - refunds
    with C.db() as c:
        c.execute("INSERT INTO pnl(month,revenue,fees,cogs,refunds,net,orders,tenant_id) VALUES(?,?,?,?,?,?,?,?)",
                  (month, revenue, fees, cogs, refunds, net, len(rows), tenant_id))
    return dict(month=month, orders=len(rows), revenue=round(revenue, 2), fees=round(fees, 2),
                cogs=round(cogs, 2), refunds=round(refunds, 2), net=round(net, 2))


def export(month=None):
    d = monthly(month)
    path = f"pnl_{d['month']}.csv"
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(d)); w.writeheader(); w.writerow(d)
    print(d, "\n->", path)
    return d


def ytd_1099k(tenant_id=C.DEFAULT_TENANT_ID):
    with C.db() as c:
        r = c.execute("SELECT COALESCE(SUM(price),0) gross, COUNT(*) n FROM orders "
                      "WHERE status!='REFUNDED' AND tenant_id=?", (tenant_id,)).fetchone()
    gross, n = float(r["gross"]), r["n"]
    prof = Config.tax()
    print(f"YTD gross ${gross:,.2f} / {n} orders")
    print(f"1099-K: federal threshold $20,000 AND 200 txns (2026). State floor ${prof['k1099_threshold']:,}.")
    print(f"Business reg: {prof['business_registration']}")
    print("-> likely 1099-K" if (gross >= 20000 or n >= 200) else "-> below federal threshold (still taxable)")
    return gross, n


if __name__ == "__main__":
    C.load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", action="store_true"); ap.add_argument("--month")
    a = ap.parse_args()
    export(a.month) if a.export else ytd_1099k()