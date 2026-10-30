"""
fbm/targets.py — turn scraped comps into defensible price targets.

  python -m fbm.targets --strategy undercut --undercut 0.05
  python -m fbm.targets --strategy match --inventory inventory.csv
  python -m fbm.targets --apply            # write new prices into inventory.csv
"""
from __future__ import annotations
import argparse, csv, difflib, statistics
from fbm import core as C


def load_comps(tenant_id=C.DEFAULT_TENANT_ID):
    C.load_env()
    with C.db() as c:
        rows = c.execute("SELECT query, price FROM listings WHERE tenant_id=?", (tenant_id,)).fetchall()
    out = {}
    for r in rows:
        out.setdefault(r["query"], []).append(float(r["price"]))
    return out


def robust_median(prices):
    """IQR outlier removal, then median. Returns (median, n_kept, n_dropped)."""
    prices = sorted(prices)
    if len(prices) < 4:
        return (statistics.median(prices), len(prices), 0)
    q1 = prices[len(prices) // 4]
    q3 = prices[(3 * len(prices)) // 4]
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    kept = [p for p in prices if lo <= p <= hi] or prices
    return (statistics.median(kept), len(kept), len(prices) - len(kept))


def margin_floor(cost, fee=0.10, reserve=0.03, target_margin=0.15):
    denom = 1 - fee - reserve - target_margin
    return cost / denom if denom > 0 else cost * 2


def load_inventory(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def match_cost(query, inv):
    titles = [r["title"] for r in inv]
    m = difflib.get_close_matches(query, titles, n=1, cutoff=0.3)
    if m:
        for r in inv:
            if r["title"] == m[0]:
                return float(r.get("cost") or 0), r
    return 0.0, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", default="inventory.csv")
    ap.add_argument("--out", default="targets.csv")
    ap.add_argument("--strategy", choices=["match", "undercut", "premium"], default="undercut")
    ap.add_argument("--undercut", type=float, default=0.05)
    ap.add_argument("--premium", type=float, default=0.10)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    comps = load_comps()
    inv = load_inventory(args.inventory)
    rows, updates = [], {}

    for q, prices in comps.items():
        med, kept, dropped = robust_median(prices)
        if args.strategy == "undercut":
            sug = med * (1 - args.undercut)
        elif args.strategy == "premium":
            sug = med * (1 + args.premium)
        else:
            sug = med
        cost, invrow = match_cost(q, inv)
        floor = margin_floor(cost) if cost else 0
        final = max(sug, floor)
        action = "floor-protected" if floor and sug < floor else args.strategy
        rows.append({"query": q, "n": kept, "dropped": dropped, "median": round(med, 2),
                     "suggested": round(final, 2), "floor": round(floor, 2), "action": action})
        if invrow:
            updates[invrow["sku"]] = round(final, 2)
        print(f"{q[:34]:34} n={kept:>3} med={med:>8.2f} -> {final:>8.2f}  ({action})")

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["query", "n", "dropped", "median", "suggested",
                                          "floor", "action"])
        w.writeheader(); w.writerows(rows)
    print(f"wrote {args.out}")

    if args.apply and updates:
        for r in inv:
            if r["sku"] in updates:
                r["price"] = f"{updates[r['sku']]:.2f}"
        cols = list(inv[0].keys())
        with open(args.inventory, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(inv)
        print(f"applied {len(updates)} price updates to {args.inventory}")


if __name__ == "__main__":
    main()