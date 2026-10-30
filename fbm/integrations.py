"""
fbm/integrations.py — registry, browser connect flow, per-integration settings.
"""
from __future__ import annotations
import json
from fbm import core as C
from fbm import vault, flags

REGISTRY = {
 "spocket": {
    "name":"Spocket","category":"supplier","auth":"api_key",
    "signup":"https://www.spocket.co/signup","login":"https://app.spocket.co/login",
    "key_page":"https://app.spocket.co/settings/api","key_name":"SPOCKET_API_KEY",
    "features":["catalog_import","stock_sync","order_fulfil","rma"],
    "settings":[
      {"key":"ship_from","label":"Preferred warehouse","type":"select",
       "options":["US","EU","auto"],"default":"US","help":"Where orders dispatch from."},
      {"key":"max_handling_days","label":"Max handling days","type":"number","default":2},
      {"key":"auto_import","label":"Auto-import new products","type":"bool","default":False}],
    "test": lambda k: bool(k)},
 "cj": {"name":"CJdropshipping","category":"supplier","auth":"api_key",
    "signup":"https://cjdropshipping.com/register.html","login":"https://cjdropshipping.com/login.html",
    "key_page":"https://cjdropshipping.com/my.html","key_name":"CJ_API_KEY",
    "features":["catalog_import","stock_sync","order_fulfil","branded_packaging"],
    "settings":[{"key":"warehouse","label":"Warehouse","type":"select","options":["US","CN"],"default":"US"}],
    "test": lambda k: bool(k)},
 "stripe": {"name":"Stripe","category":"billing","auth":"api_key",
    "signup":"https://dashboard.stripe.com/register","login":"https://dashboard.stripe.com/login",
    "key_page":"https://dashboard.stripe.com/apikeys","key_name":"STRIPE_SECRET_KEY",
    "features":["subscriptions","customer_balance","connect_payouts"],
    "settings":[{"key":"currency","label":"Currency","type":"select","options":["USD"],"default":"USD"}],
    "test": lambda k: str(k).startswith("sk_")},
 "ebay": {"name":"eBay","category":"marketplace","auth":"oauth",
    "signup":"https://www.ebay.com/signin","login":"https://www.ebay.com/signin",
    "features":["crosslist","orders","tracking"],
    "settings":[{"key":"default_category","label":"Default category","type":"text","default":"Home & Garden"},
               {"key":"listing_duration","label":"Duration","type":"select","options":["GTC","7 days"],"default":"GTC"}],
    "test": lambda k: bool(k)},
 "gmail": {"name":"Gmail (tracking ingest)","category":"email","auth":"oauth",
    "signup":"https://accounts.google.com/signup","login":"https://accounts.google.com/",
    "features":["tracking_ingest","order_email"],
    "settings":[{"key":"alias_domain","label":"Alias domain","type":"text","default":""},
               {"key":"poll_seconds","label":"Poll interval (s)","type":"number","default":120}],
    "test": lambda k: bool(k)},
 "twilio": {"name":"Twilio (SMS / WhatsApp)","category":"messaging","auth":"api_key",
    "signup":"https://www.twilio.com/try-twilio","login":"https://console.twilio.com/",
    "key_page":"https://console.twilio.com/","key_name":"TWILIO_AUTH_TOKEN",
    "features":["sms_reply","whatsapp_reply","alerts"],
    "settings":[{"key":"from_number","label":"From number","type":"text"},
               {"key":"channels","label":"Channels","type":"multi","options":["sms","whatsapp"],"default":["sms"]}],
    "test": lambda k: bool(k)},
 "openai": {"name":"OpenAI / OpenRouter / Anthropic","category":"ai","auth":"api_key",
    "signup":"https://platform.openai.com/signup","login":"https://platform.openai.com/login",
    "key_page":"https://platform.openai.com/api-keys","key_name":"OPENAI_API_KEY",
    "features":["ai_reply","ai_copy","ai_classify"],
    "settings":[{"key":"model","label":"Model","type":"text","default":"gpt-4o-mini"},
               {"key":"base_url","label":"Base URL","type":"text","default":"https://api.openai.com/v1"}],
    "test": lambda k: bool(k)},
 "slack": {"name":"Slack / Discord alerts","category":"alerts","auth":"webhook",
    "signup":"https://api.slack.com/apps","login":"https://slack.com/signin",
    "features":["alerts","digest"],
    "settings":[{"key":"channel","label":"Channel","type":"text","default":"#fbm"}],
    "test": lambda k: str(k).startswith("http")},
}


def _spec(iid): return REGISTRY[iid]


def status(tenant_id):
    connected = set(vault.names(tenant_id))
    out = {}
    for iid, s in REGISTRY.items():
        out[iid] = {"name": s["name"], "category": s["category"], "auth": s["auth"],
                    "features": s["features"], "settings": s["settings"],
                    "connected": s.get("key_name","") in connected or iid in connected,
                    "signup": s.get("signup"), "login": s.get("login")}
    return out


def features_available(tenant_id):
    avail = {"fb_publish", "fb_tracking", "local_pickup"}
    for iid, s in REGISTRY.items():
        if status(tenant_id)[iid]["connected"]:
            avail |= set(s["features"])
    return avail


def can(tenant_id, feature):
    return feature in features_available(tenant_id) and not flags.get(tenant_id)["maintenance_mode"]


def connect(tenant_id, iid, mode="signup", pasted_key=None):
    """Open a real browser at the vendor's signup/login; user returns and we finish."""
    s = _spec(iid)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            f"profiles/int_{iid}", headless=False, viewport={"width":1280,"height":860},
            user_agent=C.USER_AGENT, args=["--disable-blink-features=AutomationControlled"])
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(s.get(mode) or s["login"], wait_until="domcontentloaded")
        print(f">>> finish signing in to {s['name']}, then press Enter in the app")
        input()

        key = pasted_key or _harvest(page, s)
        ok = False
        if key:
            try: ok = s["test"](key)
            except Exception: ok = False
            if ok: vault.put(tenant_id, s["key_name"], key)
        if ok and s.get("settings"):
            vault.put(tenant_id, f"{iid}_settings", {x["key"]: x.get("default") for x in s["settings"]})
        ctx.close()
    with C.db() as c:
        c.execute("INSERT INTO events(kind,ref,detail,tenant_id) VALUES('integration',?,?,?)",
                  (iid, "connected" if ok else "failed", tenant_id))
    return {"connected": ok, "integration": iid,
            "features": s["features"] if ok else [],
            "message": f"{s['name']} connected." if ok else "Couldn't verify the key - paste it manually."}


def _harvest(page, spec):
    if not spec.get("key_page"): return None
    try:
        page.goto(spec["key_page"], wait_until="domcontentloaded"); C.pause(2, 3)
        for sel in ["input[readonly]", "code", "[data-testid*='key']"]:
            loc = page.locator(sel).first
            if loc.count():
                v = (loc.input_value() if sel.startswith("input") else loc.inner_text()).strip()
                if len(v) > 12: return v
    except Exception:
        pass
    return None


def save_settings(tenant_id, iid, values):
    vault.put(tenant_id, f"{iid}_settings", values)
    return values


def settings_for(tenant_id, iid):
    return vault.get(tenant_id, f"{iid}_settings") or {}