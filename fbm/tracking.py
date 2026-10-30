"""
fbm/tracking.py — the tracking pipeline.

Sources: IMAP poller, Gmail API push, Zapier/Make/IFTTT webhook, supplier API, manual.
Matching: alias-first (exact), then buyer/SKU/time fuzzy.
Output: validated tracking on the order + queued FB upload + escalation.
"""
from __future__ import annotations
import re, json
from datetime import datetime
import os
from fbm import core as C

# ---- carrier detection + validation -------------------------------------
CARRIERS = {
    "ups":    re.compile(r"\b1Z[0-9A-Z]{16}\b"),
    "usps":   re.compile(r"\b(9[2-5]\d{20,24}|420\d{5,9}9[2-5]\d{20})\b"),
    "fedex":  re.compile(r"\b(\d{12}|\d{15}|\d{20}|\d{22})\b"),
    "dhl":    re.compile(r"\b(JJD\d{10,20}|JD\d{18}|\d{10})\b"),
    "amazon": re.compile(r"\bTBA\d{12,15}\b"),
}


def _luhn_ok(num):
    d = [int(x) for x in num if x.isdigit()][::-1]
    return sum(d[0::2]) + sum(sum(divmod(x * 2, 10)) for x in d[1::2]) % 10 == 0


def detect_carrier(text):
    for carrier, pat in CARRIERS.items():
        for m in pat.findall(text):
            t = m if isinstance(m, str) else m[0]
            if carrier == "usps" and not _luhn_ok(t[-22:] if len(t) > 22 else t):
                continue
            return carrier, t
    return None, None


def tracking_url(carrier, num):
    return {
        "ups":   f"https://www.ups.com/track?tracknum={num}",
        "usps":  f"https://tools.usps.com/go/TrackConfirmAction?tLabels={num}",
        "fedex": f"https://www.fedex.com/fedextrack/?trknbr={num}",
        "dhl":   f"https://www.dhl.com/us-en/home/tracking.html?tracking-id={num}",
    }.get(carrier, num)


# ---- alias routing ------------------------------------------------------
def alias_for(order):
    dom = os.getenv("ORDER_ALIAS_DOMAIN", "yourdomain.com")
    return f"orders+{order['fingerprint']}@{dom}"


def order_from_alias(to_addr, tenant_id=C.DEFAULT_TENANT_ID):
    m = re.search(r"orders\+([0-9a-f]{6,})@", to_addr or "")
    if not m:
        return None
    with C.db() as c:
        return c.execute("SELECT * FROM orders WHERE fingerprint LIKE ? AND tenant_id=?",
                         (m.group(1) + "%", tenant_id)).fetchone()


# ---- ingest -------------------------------------------------------------
def ingest(payload, tenant_id=C.DEFAULT_TENANT_ID):
    """payload: {to, subject, body, from} or {fingerprint, tracking, carrier}."""
    text = f"{payload.get('subject', '')}\n{payload.get('body', '')}"
    carrier, num = payload.get("carrier"), payload.get("tracking")
    if not num:
        carrier, num = detect_carrier(text)
    if not num:
        return False

    order = None
    if payload.get("fingerprint"):
        with C.db() as c:
            order = c.execute("SELECT * FROM orders WHERE fingerprint=? AND tenant_id=?",
                              (payload["fingerprint"], tenant_id)).fetchone()
    if order is None and payload.get("to"):
        order = order_from_alias(payload["to"], tenant_id)
    if order is None:
        order = _fuzzy_order(text, tenant_id)
    if order is None:
        _log("tracking_unmatched", num, f"carrier={carrier}", tenant_id)
        C.notify(f"unmatched tracking {num}", "warn")
        return False

    with C.db() as c:
        c.execute("UPDATE orders SET tracking=?, supplier=COALESCE(supplier,'?'), "
                  "status='SHIPPED', updated_at=datetime('now') WHERE fingerprint=? AND tenant_id=?",
                  (num, order["fingerprint"], tenant_id))
        c.execute("INSERT INTO events(kind,ref,detail,tenant_id) VALUES('tracking_ingested',?,?,?)",
                  (order["fingerprint"], f"{carrier} {num}", tenant_id))
    C.notify(f"tracking {carrier} {num} matched to {order['title']}")
    return True


def _fuzzy_order(text, tenant_id=C.DEFAULT_TENANT_ID):
    with C.db() as c:
        openo = c.execute("SELECT * FROM orders WHERE status IN ('NEW','ORDERED') AND tenant_id=?",
                          (tenant_id,)).fetchall()
    for o in openo:
        if o["sku"] and o["sku"].lower() in text.lower():
            return o
        if o["buyer"] and o["buyer"].split()[0].lower() in text.lower():
            return o
    return None


def _log(kind, ref, detail, tenant_id=C.DEFAULT_TENANT_ID):
    with C.db() as c:
        c.execute("INSERT INTO events(kind,ref,detail,tenant_id) VALUES(?,?,?,?)",
                  (kind, ref, detail, tenant_id))


# ---- push tracking to Facebook -----------------------------------------
def upload_to_fb(page, lim, order, tenant_id=C.DEFAULT_TENANT_ID):
    """Navigate the order and paste tracking. Selectors self-heal."""
    page.goto("https://www.facebook.com/marketplace/you/selling", wait_until="domcontentloaded")
    lim.wait(); C.dismiss_modals(page)
    try:
        C.find(page, "orders_tab").click()
    except Exception:
        pass
    card = page.get_by_text(order["title"][:40], exact=False).first
    card.click(); cm.pause()
    C.find(page, "add_tracking").click(); cm.pause()
    try:
        C.find(page, "carrier_select").click()
        page.get_by_text(order.get("carrier", "Other"), exact=False).first.click()
    except Exception:
        pass
    C.find(page, "tracking_input").fill(order["tracking"]); cm.pause()
    C.find(page, "confirm").click(); cm.pause()
    with C.db() as c:
        c.execute("UPDATE orders SET status='SHIPPED', updated_at=datetime('now') "
                  "WHERE fingerprint=? AND tenant_id=?",
                  (order["fingerprint"], tenant_id))
    C.notify(f"tracking uploaded to FB: {order['title']}")


def escalate(overdue_days=2, tenant_id=C.DEFAULT_TENANT_ID):
    with C.db() as c:
        rows = c.execute("SELECT * FROM orders WHERE status IN ('NEW','ORDERED') "
                         "AND created_at < datetime('now', ?) AND tenant_id=?",
                         (f"-{overdue_days} day", tenant_id)).fetchall()
    for r in rows:
        C.notify(f"OVERDUE: {r['title']} (created {r['created_at']})", "error")
    return len(rows)


# import cm lazily to avoid circular import at module load
from fbm import common as cm  # noqa: E402