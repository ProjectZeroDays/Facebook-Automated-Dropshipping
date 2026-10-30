"""
fbm/settings.py — business profile, product CSV import, presets.
"""
from __future__ import annotations
import csv, io, json
from pathlib import Path
from fbm import core as C
from fbm import config


CANON = ["sku","title","price","cost","category","condition","description",
         "photos","image_urls","link","source","backup_source","tags"]

ALIASES = {
  "name":"title","product":"title","item":"title","product name":"title",
  "sell price":"price","retail":"price","price usd":"price",
  "wholesale":"cost","supplier cost":"cost","buy price":"cost",
  "desc":"description","details":"description","info":"description",
  "img":"photos","images":"photos","pics":"photos","picture":"photos","photo":"photos",
  "url":"link","product url":"link","vendor":"source","supplier":"source","brand":"tags",
}


def import_csv(tenant_id, raw: bytes):
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    out, problems = [], []
    for i, r in enumerate(rows, 2):
        m = {}
        for k, v in r.items():
            if k is None: continue
            key = ALIASES.get(k.strip().lower(), k.strip().lower())
            if key in CANON: m[key] = (v or "").strip()
        if not m.get("title"): problems.append((i, "missing title")); continue
        try: m["price"] = float(str(m.get("price","0")).replace("$","").replace(",",""))
        except ValueError: problems.append((i, f"bad price '{m.get('price')}'")); continue
        m["cost"] = float(str(m.get("cost","0")).replace("$","").replace(",","") or 0)
        if not m.get("sku"): m["sku"] = f"CSV-{i:04d}"
        out.append(m)
    hints = []
    if any(not r.get("photos") and not r.get("image_urls") for r in out):
        hints.append("Some rows have no photos — listings need ≥1 image.")
    if any(r["price"] < r["cost"] for r in out):
        hints.append("Some rows sell below cost.")
    return {"accepted": out, "problems": problems, "hints": hints, "columns": CANON}


def save_business(tenant_id, **kw):
    cols = ["name","phone","email","city","state","hours","policies","return_days",
            "returns_allowed","shipping_payer","free_shipping_over","handling_days","logo"]
    data = {k: kw[k] for k in cols if k in kw}
    with C.db() as c:
        cols_str = ",".join(data.keys())
        placeholders = ",".join("?" * len(data))
        c.execute(f"INSERT INTO business(tenant_id,{cols_str}) VALUES(?,{placeholders}) "
                  f"ON CONFLICT(tenant_id) DO UPDATE SET " +
                  ",".join(f"{k}=excluded.{k}" for k in data),
                  (tenant_id, *data.values()))
    return data


def shipping_line(tenant_id):
    with C.db() as c:
        b = c.execute("SELECT * FROM business WHERE tenant_id=?", (tenant_id,)).fetchone()
    if not b: return {"payer": "fb"}
    if b["shipping_payer"] == "supplier":
        return {"payer": "supplier", "note": "Use the dropshipper's live shipping estimate at checkout."}
    return {"payer": "fb", "note": f"Meta's shipping pricing applies. Free over ${b['free_shipping_over'] or 0}."}


def draft_policies(answers):
    return f"""Returns: {answers.get('returns','30 days')} policy.
Shipping payer: {answers.get('shipping_payer','Meta/FB pricing')}.
Support: {answers.get('phone','')}
Hours: {answers.get('hours','')}
"""