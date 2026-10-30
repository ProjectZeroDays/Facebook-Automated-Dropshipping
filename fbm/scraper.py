"""
fbm/scraper.py — pull local Marketplace comps and flag over/under-pricing.

Usage:
  python -m fbm.scraper --city memphis --queries "slow feeder dog bowl,posture corrector" --scrolls 6
  python -m fbm.scraper --city memphis --queries "cat bed" --targets targets.csv
  python -m fbm.scraper --report          # stats from everything already stored

targets.csv (optional):  query,my_price
"""
from __future__ import annotations
import argparse, csv, re, statistics
from datetime import datetime
from urllib.parse import quote
from playwright.sync_api import sync_playwright

from fbm import core as C
from fbm import common as cm

PRICE_RE = re.compile(r"\$([\d,]+(?:\.\d{2})?)")
ITEM_RE = re.compile(r"/marketplace/item/(\d+)")


def search_url(city, query):
    return f"https://www.facebook.com/marketplace/{city}/search?query={quote(query)}"


def scrape_query(page, city, query, scrolls):
    page.goto(search_url(city, query), wait_until="domcontentloaded")
    cm.pause(2, 3); cm.dismiss_modals(page)
    for _ in range(scrolls):
        page.mouse.wheel(0, 2200); cm.pause(1.0, 1.8)

    seen = {}
    cards = page.locator("a[href*='/marketplace/item/']")
    for i in range(min(cards.count(), 150)):
        try:
            el = cards.nth(i)
            href = el.get_attribute("href") or ""
            m = ITEM_RE.search(href)
            if not m:
                continue
            lid = m.group(1)
            if lid in seen:
                continue
            lines = [l.strip() for l in (el.inner_text() or "").split("\n") if l.strip()]
            price = None
            for l in lines:
                pm = PRICE_RE.search(l)
                if pm:
                    price = float(pm.group(1).replace(",", ""))
                    break
            if price is None or price <= 0:
                continue
            title = next((l for l in lines if not PRICE_RE.search(l)),
                         lines[0] if lines else "")
            loc = lines[-1] if len(lines) > 1 else ""
            url = f"https://www.facebook.com{href}" if href.startswith("/") else href
            seen[lid] = dict(id=lid, query=query, title=title, price=price,
                             location=loc, url=url)
        except Exception:
            continue
    return list(seen.values())


def save(rows, tenant_id=C.DEFAULT_TENANT_ID):
    if not rows:
        return
    with C.db() as c:
        for r in rows:
            r["tenant_id"] = tenant_id
        c.executemany(
            "INSERT OR REPLACE INTO listings(id,query,title,price,location,url,tenant_id) "
            "VALUES(:id,:query,:title,:price,:location,:url,:tenant_id)", rows)


def load_targets(path):
    t = {}
    try:
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                t[r["query"].strip()] = float(r["my_price"])
    except FileNotFoundError:
        pass
    return t


def report(targets, tenant_id=C.DEFAULT_TENANT_ID):
    with C.db() as c:
        rows = c.execute("SELECT query, price FROM listings WHERE tenant_id=?", (tenant_id,)).fetchall()
    by_q = {}
    for r in rows:
        by_q.setdefault(r["query"], []).append(r["price"])
    print(f"\n{'query':38} {'n':>4} {'min':>8} {'p25':>8} {'median':>8} {'p75':>8} {'max':>8}  verdict")
    print("-" * 108)
    for q, prices in sorted(by_q.items()):
        prices.sort(); n = len(prices)
        med = statistics.median(prices)
        p25 = prices[int(n * 0.25)] if n else 0
        p75 = prices[min(n - 1, int(n * 0.75))] if n else 0
        my = targets.get(q)
        verdict = ""
        if my:
            if my > med * 1.15:
                verdict = f"REPRICE DOWN (you {my:.2f} vs median {med:.2f})"
            elif my < med * 0.85:
                verdict = f"ROOM TO RAISE (you {my:.2f} vs median {med:.2f})"
            else:
                verdict = "competitive"
        print(f"{q[:38]:38} {n:>4} {prices[0]:>8.2f} {p25:>8.2f} {med:>8.2f} {p75:>8.2f} {prices[-1]:>8.2f}  {verdict}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="memphis")
    ap.add_argument("--queries", default="")
    ap.add_argument("--scrolls", type=int, default=6)
    ap.add_argument("--targets", default="targets.csv")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    C.init_db()
    targets = load_targets(args.targets)

    if args.queries and not args.report:
        queries = [q.strip() for q in args.queries.split(",") if q.strip()]
        all_rows = []
        with sync_playwright() as p:
            ctx, page = cm.launch(p)
            C.ensure_logged_in(page)
            for q in queries:
                try:
                    rows = scrape_query(page, args.city, q, args.scrolls)
                    print(f"{q}: {len(rows)} comps")
                    all_rows += rows
                except Exception as e:
                    print(f"{q}: FAILED {e}"); C.notify(f"scraper failed on {q}: {e}", "error")
                cm.pause(3, 6)
            ctx.close()
        save(all_rows)
        out = args.out or f"comps_{datetime.now():%Y%m%d_%H%M}.csv"
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["id", "query", "title", "price", "location", "url"])
            w.writeheader(); w.writerows(all_rows)
        print(f"wrote {out}")

    report(targets)


if __name__ == "__main__":
    main()