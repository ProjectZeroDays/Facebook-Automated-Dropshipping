"""fbm/common.py — shared helpers for the FB Marketplace toolset.

Env vars:
  FBM_PROFILE   browser profile dir   (default: fb_profile)
  FBM_DB        sqlite path           (default: fbm.sqlite)
  ALERT_WEBHOOK Slack/Discord/Telegram webhook for alerts (optional)
"""
from __future__ import annotations
import os, random, sqlite3, time
import requests
from playwright.sync_api import TimeoutError as PWTimeout

from fbm import core as C

PROFILE_DIR = os.getenv("FBM_PROFILE", "fb_profile")
DB_PATH = os.getenv("FBM_DB", "fbm.sqlite")
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def pause(a=0.6, b=1.8):
    """Human-like delay."""
    time.sleep(random.uniform(a, b))


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    C.init_db()


def notify(msg, level="info"):
    hook = os.getenv("ALERT_WEBHOOK")
    if hook:
        try:
            requests.post(hook, json={"text": f"[fbm/{level}] {msg}"}, timeout=10)
        except Exception:
            pass


def launch(p, headless=False):
    """Persistent context so you stay logged in across runs."""
    ctx = p.chromium.launch_persistent_context(
        PROFILE_DIR, headless=headless,
        viewport={"width": 1366, "height": 900},
        user_agent=USER_AGENT,
        args=["--disable-blink-features=AutomationControlled"])
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    return ctx, page


def first_visible(page, selectors, timeout=8000):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            loc.wait_for(state="visible", timeout=timeout)
            return loc
        except PWTimeout:
            continue
    raise PWTimeout(f"no match: {selectors}")


def ensure_logged_in(page):
    C.ensure_logged_in(page)


def dismiss_modals(page):
    C.dismiss_modals(page)