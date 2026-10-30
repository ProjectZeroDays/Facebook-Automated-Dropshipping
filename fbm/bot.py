"""
fbm/bot.py — Playwright bot for automated FB Marketplace
listing, renewing, and delete+relist cycling.

Pattern: persistent Chromium profile + CSV inventory. Selectors on Facebook
change often — each has a comment and a fallback. Run HEADFUL the first time
to log in manually; the profile dir keeps you logged in afterward.

Install:
    pip install playwright && playwright install chromium

Run:
    python -m fbm.bot --mode list      # publish inventory.csv
    python -m fbm.bot --mode renew     # renew active listings
    python -m fbm.bot --mode recycle   # delete + relist (feed the algo)
"""
from __future__ import annotations
import argparse, csv, logging, random, time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

from fbm import core as C
from fbm import common as cm

PROFILE_DIR = C.PROFILE_DIR
INVENTORY = "inventory.csv"
CREATE_URL = "https://www.facebook.com/marketplace/create/item"
SELLING_URL = "https://www.facebook.com/marketplace/you/selling"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("fbm")


def publish_listing(page, item):
    page.goto(CREATE_URL, wait_until="domcontentloaded")
    cm.pause(1.5, 2.5)

    C.find(page, "title").fill(item["title"])
    cm.pause()
    C.find(page, "price").fill(item["price"])
    cm.pause()

    for field, key in (("category", "category"), ("condition", "condition")):
        try:
            C.find(page, field).click(); cm.pause()
            page.get_by_text(item[key], exact=False).first.click(); cm.pause()
        except PWTimeout:
            log.warning("%s step skipped", field)

    C.find(page, "description").fill(item["description"])
    cm.pause()

    photos = [p.strip() for p in item.get("photos", "").split(";") if p.strip()]
    page.locator("input[type='file']").first.set_input_files(
        [str(Path(p)) for p in photos])
    log.info("uploaded %d photos", len(photos))
    cm.pause(3, 5)

    C.find(page, "next").click()
    cm.pause(1.5, 2.5)

    for label in ("Shipping", "Use your own shipping label", "Free shipping for buyers"):
        try:
            page.get_by_text(label, exact=False).first.click(); cm.pause()
        except PWTimeout:
            log.warning("could not set: %s", label)

    C.find(page, "publish").click()
    cm.pause(3, 5)
    log.info("published: %s", item["title"])


def record_listing(page, item, account, variant=0):
    url = page.url
    lid = url.rstrip("/").split("/")[-1]
    with C.db() as c:
        c.execute("INSERT OR REPLACE INTO listings(id,account,sku,title,price,url,status,variant,posted_at) "
                  "VALUES(?,?,?,?,?,?,'active',?,datetime('now'))",
                  (lid, account, item.get("sku"), item["title"], float(item["price"]), url, variant))
    return lid


def renew_all(page, limit=10):
    page.goto(SELLING_URL, wait_until="domcontentloaded"); cm.pause(2, 3)
    n = 0
    while n < limit:
        btn = page.get_by_text("Renew", exact=True)
        if btn.count() == 0:
            break
        btn.first.click(); cm.pause(1.2, 2.0); n += 1
        log.info("renewed #%d", n)
    return n


def delete_and_relist(page, item):
    page.goto(SELLING_URL, wait_until="domcontentloaded"); cm.pause(2, 3)
    card = page.get_by_text(item["title"], exact=False).first
    if card.count() == 0:
        return False
    card.click(); cm.pause()
    try:
        C.find(page, "more_options").click(); cm.pause()
        page.get_by_text("Delete listing", exact=False).first.click(); cm.pause()
        page.get_by_text("Delete", exact=True).first.click(); cm.pause(1.5, 2.5)
    except PWTimeout:
        log.warning("delete menu not found for %s", item["title"]); return False
    publish_listing(page, item)
    return True


def load_inventory(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["list", "renew", "recycle"], default="list")
    ap.add_argument("--limit", type=int, default=10, help="max actions/run (FB-safe)")
    ap.add_argument("--account", default="main", help="account name for multi-account")
    args = ap.parse_args()

    items = load_inventory(INVENTORY)
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            PROFILE_DIR, headless=False,
            viewport={"width": 1366, "height": 900},
            args=["--disable-blink-features=AutomationControlled"])
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        C.ensure_logged_in(page)

        if args.mode == "list":
            for it in items[:args.limit]:
                try:
                    publish_listing(page, it)
                    record_listing(page, it, args.account)
                except Exception as e:
                    log.error("failed %s: %s", it.get("title"), e)
                cm.pause(3, 6)
        elif args.mode == "renew":
            renew_all(page, args.limit)
        elif args.mode == "recycle":
            for it in items[:args.limit]:
                delete_and_relist(page, it); cm.pause(3, 6)
        ctx.close()


if __name__ == "__main__":
    main()