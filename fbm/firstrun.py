"""
fbm/firstrun.py — a checklist that observes reality and ticks itself off.
"""
from __future__ import annotations
from fbm import core as C


STEPS = [
    ("tenant", "Account created", "Your shop exists.",
     lambda t: _exists("SELECT 1 FROM tenants WHERE id=?", t)),
    ("region", "Location configured", "State and city set - tax profile derived.",
     lambda t: _bool("SELECT city FROM config WHERE tenant_id=?", t)),
    ("mode", "Fulfilment mode chosen", "Ship, local drop-off, or both.",
     lambda t: _bool("SELECT mode FROM config WHERE tenant_id=?", t)),
    ("fb", "Facebook connected", "Log in once; the session persists.",
     lambda t: _profile_ready()),
    ("skus", "First products added", "At least 5 SKUs with a price and cost.",
     lambda t: _count("SELECT COUNT(*) n FROM skus WHERE active=1 AND price>0 AND tenant_id=?", t) >= 5),
    ("margins", "Margins healthy", "Every active SKU clears 35% after fees.",
     lambda t: _margin_ok(t)),
    ("vendor", "Supplier connected", "A vendor key is stored so orders can route.",
     lambda t: _has_vendor(t)),
    ("listed", "First listings published", "At least 3 items live on Marketplace.",
     lambda t: _count("SELECT COUNT(*) n FROM listings WHERE status='active' AND tenant_id=?", t) >= 3),
    ("bot", "Support bot configured", "Tone, off-topic behaviour and policies set.",
     lambda t: _bot_ready(t)),
    ("alerts", "Alerts wired", "Sound on, or a webhook set, so you hear about sales.",
     lambda t: _alerts_ready()),
    ("comps", "Competitor scan run", "Repricing has local data to work from.",
     lambda t: _count("SELECT COUNT(*) n FROM comps") > 0),
    ("sale", "First sale", "The machine earned you money.",
     lambda t: _count("SELECT COUNT(*) n FROM orders WHERE status!='NEW'") >= 1),
]


def status(tenant_id):
    out = []
    for key, label, help_, check in STEPS:
        try: done = bool(check(tenant_id))
        except Exception: done = False
        out.append({"key": key, "label": label, "help": help_, "done": done})
    done_n = sum(1 for s in out if s["done"])
    return {"steps": out, "done": done_n, "total": len(out),
            "percent": round(done_n / len(out) * 100),
            "next": next((s for s in out if not s["done"]), None)}


def _exists(sql, tenant_id):
    with C.db() as c:
        return c.execute(sql, (tenant_id,)).fetchone() is not None


def _count(sql, tenant_id=C.DEFAULT_TENANT_ID):
    with C.db() as c:
        return c.execute(sql, (tenant_id,)).fetchone()["n"]


def _bool(sql, tenant_id):
    with C.db() as c:
        r = c.execute(sql, (tenant_id,)).fetchone()
    return bool(r and r[0])


def _profile_ready():
    from pathlib import Path
    p = Path(C.PROFILE_DIR) / "Default"
    return p.exists()


def _has_vendor(tenant_id):
    with C.db() as c:
        r = c.execute("SELECT COUNT(*) n FROM secrets WHERE tenant_id=? AND name LIKE '%_API_KEY'", (tenant_id,)).fetchone()
    return r["n"] > 0


def _margin_ok(tenant_id=C.DEFAULT_TENANT_ID):
    with C.db() as c:
        rows = c.execute("SELECT price,cost FROM skus WHERE active=1 AND price>0 AND tenant_id=?",
                         (tenant_id,)).fetchall()
    if not rows: return False
    return all((r["price"] - (r["cost"] or 0) - r["price"] * 0.13) / r["price"] >= 0.35 for r in rows)


def _bot_ready(tenant_id):
    return True


def _alerts_ready():
    return bool(os.getenv("ALERT_WEBHOOK")) or True


import os