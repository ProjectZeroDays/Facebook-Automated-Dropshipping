"""
fbm/watcher.py — poll Marketplace orders, POST new ones to n8n.

Usage:
  python -m fbm.watcher --once
  python -m fbm.watcher --interval 300 --webhook http://localhost:5678/webhook/fbm-new-sale
  python -m fbm.watcher --url "https://www.facebook.com/marketplace/you/selling"
"""
from __future__ import annotations
import argparse, hashlib, json, re, time
import requests
from playwright.sync_api import sync_playwright

from fbm import core as C
from fbm import common as cm

DEFAULT_URL = "https://www.facebook.com/marketplace/you/selling"
PRICE_RE = re.compile(r"\$([\d,]+(?:\.\d{2})?)")
ORDER_HINTS = ("Order", "Sold", "Shipped", "Preparing", "Delivered", "To ship")


def scan_orders(page, url):
    page.goto(url, wait_until="domcontentloaded"); cm.pause(2, 3); cm.dismiss_modals(page)
    for tab in ("Orders", "Shipping"):
        try:
            page.get_by_text(tab, exact=True).first.click(timeout=1500); cm.pause(1.2, 2.0); break
        except Exception:
            pass
    for _ in range(3):
        page.mouse.wheel(0, 2000); cm.pause(0.8, 1.5)

    found = {}
    els = page.locator("a, div[role='button']")
    for i in range(min(els.count(), 500)):
        try:
            t = (els.nth(i).inner_text() or "").strip()
        except Exception:
            continue
        if "$" not in t or not any(h in t for h in ORDER_HINTS):
            continue
        norm = " ".join(t.split())
        if not (12 <= len(norm) <= 400):
            continue
        fp = hashlib.sha1(norm.encode()).hexdigest()[:16]
        found[fp] = norm
    return found


def parse_order(raw):
    pm = PRICE_RE.search(raw)
    price = float(pm.group(1).replace(",", "")) if pm else None
    lines = [l.strip() for l in raw.split("  ") if l.strip()] or [raw]
    return {"title": lines[0][:120], "price": price, "raw": raw}


def is_new(fp, tenant_id=C.DEFAULT_TENANT_ID):
    with C.db() as c:
        return c.execute("SELECT 1 FROM orders WHERE fingerprint=? AND tenant_id=?",
                         (fp, tenant_id)).fetchone() is None


def mark(fp, payload, tenant_id=C.DEFAULT_TENANT_ID):
    with C.db() as c:
        c.execute("INSERT OR REPLACE INTO orders(fingerprint,payload,tenant_id) VALUES(?,?,?)",
                  (fp, json.dumps(payload), tenant_id))


def push(webhook, payload):
    r = requests.post(webhook, json=payload, timeout=15)
    r.raise_for_status()


def sweep(page, url, webhook, dry=False):
    new = 0
    for fp, raw in scan_orders(page, url).items():
        if not is_new(fp):
            continue
        payload = {"fingerprint": fp, **parse_order(raw)}
        if dry:
            print("NEW:", payload["title"], payload["price"])
        else:
            try:
                push(webhook, payload)
                print("pushed:", payload["title"], payload["price"])
            except Exception as e:
                C.notify(f"sale_watcher push failed: {e}", "error")
                print("push failed:", e); continue
        mark(fp, payload); new += 1
    if new == 0:
        print("no new orders")
    return new


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--webhook", default="http://localhost:5678/webhook/fbm-new-sale")
    ap.add_argument("--interval", type=int, default=300)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    C.init_db()
    with sync_playwright() as p:
        ctx, page = cm.launch(p)
        C.ensure_logged_in(page)
        while True:
            try:
                sweep(page, args.url, args.webhook, dry=args.dry)
                C.notify("sale_watcher ok")
            except Exception as e:
                print("sweep failed:", e); C.notify(f"sale_watcher failed: {e}", "error")
            if args.once:
                break
            time.sleep(args.interval)
        ctx.close()


if __name__ == "__main__":
    main()