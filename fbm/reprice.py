"""
fbm/reprice.py — auto-reprice listings that drift above local comps.

Your highest-ROI loop: if a listing sits >15% above the local median, reprice toward
it but never below the margin floor.
"""
from __future__ import annotations
import argparse
from fbm import targets as Targets
from fbm import core as C


def comps_median(query, tenant_id=C.DEFAULT_TENANT_ID):
    with C.db() as c:
        rows = c.execute("SELECT price FROM comps WHERE query=? AND tenant_id=?", (query, tenant_id)).fetchall()
    prices = [r["price"] for r in rows if r["price"]]
    if len(prices) < 3:
        return None, len(prices)
    return Targets.robust_median(prices)[0], len(prices)


def run(threshold=0.15, step=0.03, tenant_id=C.DEFAULT_TENANT_ID):
    changed = []
    with C.db() as c:
        skus = c.execute("SELECT * FROM skus WHERE active=1 AND tenant_id=?", (tenant_id,)).fetchall()
    for s in skus:
        med, n = comps_median(s["title"], tenant_id)
        if med is None:
            continue
        cur = float(s["price"] or 0)
        floor = Targets.margin_floor(float(s["cost"] or 0))
        if cur > med * (1 + threshold):
            new = max(floor, med * (1 - step))
            if new < cur - 0.50:
                with C.db() as c:
                    c.execute("UPDATE skus SET price=? WHERE sku=?", (round(new, 2), s["sku"]))
                    c.execute("INSERT INTO events(kind,ref,detail) VALUES('reprice',?,?)",
                              (s["sku"], f"{cur:.2f} -> {new:.2f} (median {med:.2f}, n={n})"))
                changed.append((s["sku"], cur, round(new, 2)))
                print(f"reprice {s['sku']}: {cur:.2f} -> {new:.2f}")
    return changed


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.15)
    ap.add_argument("--step", type=float, default=0.03)
    a = ap.parse_args()
    C.load_env()
    run(a.threshold, a.step)