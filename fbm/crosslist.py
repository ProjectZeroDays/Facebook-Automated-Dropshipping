"""
fbm/crosslist.py — mirror catalog to eBay / OfferUp / Nextdoor with fee-aware pricing.
"""
from __future__ import annotations
import csv, json
from pathlib import Path

PLATFORMS = {
  "ebay":     {"fee": 0.136, "fixed": 0.40, "mode": "shipped", "mult": 1.18},
  "offerup":  {"fee": 0.0,   "fixed": 0.0,  "mode": "local",   "mult": 0.95},
  "nextdoor": {"fee": 0.0,   "fixed": 0.0,  "mode": "local",   "mult": 0.95},
}


def build_queue(inventory="inventory.csv", out="crosslist_queue.json"):
    rows = list(csv.DictReader(open(inventory, newline="", encoding="utf-8")))
    queue = []
    for r in rows:
        base, cost = float(r["price"]), float(r.get("cost") or 0)
        for plat, cfg in PLATFORMS.items():
            price = round(base * cfg["mult"], 2)
            fee = round(price * cfg["fee"] + cfg["fixed"], 2)
            queue.append({"sku": r["sku"], "platform": plat, "title": r["title"],
                          "price": price, "mode": cfg["mode"], "fee": fee,
                          "net": round(price - fee - cost, 2),
                          "photos": r.get("photos", ""), "description": r.get("description", "")})
    Path(out).write_text(json.dumps(queue, indent=2))
    print(f"wrote {out} ({len(queue)} rows)")
    return queue


def report(queue):
    from collections import defaultdict
    agg = defaultdict(lambda: [0, 0.0])
    for q in queue:
        agg[q["platform"]][0] += 1; agg[q["platform"]][1] += q["net"]
    for p, (n, net) in sorted(agg.items()):
        print(f"{p:10} listings={n:3}  net_if_all_sell=${net:,.2f}")


if __name__ == "__main__":
    report(build_queue())