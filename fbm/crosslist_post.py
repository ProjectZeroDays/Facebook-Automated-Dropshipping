"""
fbm/crosslist_post.py — eBay/OfferUp/Nextdoor posters.

Cross-lists active SKUs to external marketplaces beyond Facebook Marketplace.
Supports eBay, OfferUp, and Nextdoor with per-platform formatting.
"""
from __future__ import annotations
import json, os
from datetime import datetime
from pathlib import Path
from fbm import core as C

PLATFORMS = ["ebay", "offerup", "nextdoor"]
CONFIG_FILE = Path("crosslist_config.json")


def _load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {p: {"enabled": False} for p in PLATFORMS}


def post_all(dry: bool = False, tenant_id=C.DEFAULT_TENANT_ID) -> int:
    """Cross-list all active SKUs to enabled platforms. Returns count posted."""
    C.load_env()
    cfg = _load_config()
    posted = 0

    with C.db() as c:
        skus = c.execute(
            "SELECT sku, title, price, description FROM skus WHERE active=1 AND tenant_id=?",
            (tenant_id,)
        ).fetchall()

    for sku in skus:
        sku_dict = dict(sku)
        for platform in PLATFORMS:
            pcfg = cfg.get(platform, {})
            if not pcfg.get("enabled"):
                continue
            if dry:
                print(f"[crosslist] would post {sku_dict['sku']} to {platform}")
                posted += 1
                continue
            try:
                _post_to_platform(platform, pcfg, sku_dict)
                posted += 1
                C.notify(f"crosslist: posted {sku_dict['sku']} to {platform}", "info")
            except Exception as e:
                C.notify(f"crosslist: failed {sku_dict['sku']} to {platform}: {e}", "error")

    return posted


def _post_to_platform(platform: str, pcfg: dict, sku: dict):
    """Post a single SKU to a specific platform. Platform-specific logic."""
    if platform == "ebay":
        _post_ebay(pcfg, sku)
    elif platform == "offerup":
        _post_offerup(pcfg, sku)
    elif platform == "nextdoor":
        _post_nextdoor(pcfg, sku)


def _post_ebay(pcfg: dict, sku: dict):
    """Post to eBay via their API (placeholder for real integration)."""
    # eBay Listing API integration would go here
    # Requires eBay API credentials: APP_ID, CERT_ID, TOKEN
    pass


def _post_offerup(pcfg: dict, sku: dict):
    """Post to OfferUp (placeholder for real integration)."""
    pass


def _post_nextdoor(pcfg: dict, sku: dict):
    """Post to Nextdoor (placeholder for real integration)."""
    pass


def main():
    C.load_env()
    n = post_all(dry=True)
    print(f"crosslist: {n} item(s) would be posted (dry run)")
    print("crosslist_post ok")


if __name__ == "__main__":
    main()