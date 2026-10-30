"""
fbm/suppliers.py — supplier registry with primary/backup failover + RMA info.
"""
from __future__ import annotations
import json, os
from pathlib import Path
import requests
from fbm import core as C

REG = Path("suppliers.json")
DEFAULT = {
  "spocket":     {"kind":"api","url":"","key_env":"SPOCKET_API_KEY","rma":"email support@spocket.co with order id"},
  "zendrop":     {"kind":"api","url":"","key_env":"ZENDROP_API_KEY","rma":"dashboard RMA within 30d"},
  "cj":          {"kind":"api","url":"","key_env":"CJ_API_KEY","rma":"RMA via dashboard"},
  "dropcommerce":{"kind":"api","url":"","key_env":"DROPCOMMERCE_API_KEY","rma":"email"},
  "manual":      {"kind":"manual","rma":"email supplier with order + photo"},
}


def registry():
    return json.loads(REG.read_text()) if REG.exists() else DEFAULT


def _log(kind, ref, detail, account=None, tenant_id=C.DEFAULT_TENANT_ID):
    with C.db() as c:
        c.execute("INSERT INTO events(kind,ref,detail,account,tenant_id) VALUES(?,?,?,?,?)",
                  (kind, ref, detail, account, tenant_id))


def place_order(sku_row, order, tenant_id=C.DEFAULT_TENANT_ID):
    """Try primary, then backup. Never let a stockout become a cancellation."""
    for supplier in [s for s in (sku_row.get("source"), sku_row.get("backup_source")) if s]:
        try:
            cfg = registry().get(supplier, {})
            if cfg.get("kind") == "manual" or not cfg.get("url"):
                C.notify(f"MANUAL order: {sku_row['sku']} -> {order.get('title')}")
            else:
                r = requests.post(cfg["url"],
                    headers={"Authorization": f"Bearer {os.getenv(cfg.get('key_env',''),'')}"},
                    json={"sku": sku_row["sku"], "ship_to": order.get("buyer"),
                          "address": order.get("address"), "blind_ship": True}, timeout=20)
                r.raise_for_status()
            _log("order_placed", order.get("fingerprint"), supplier, order.get("account"),
                 tenant_id=tenant_id)
            return supplier
        except Exception as e:
            _log("order_fail", order.get("fingerprint"), f"{supplier}: {e}", order.get("account"),
                 tenant_id=tenant_id)
    raise RuntimeError(f"all suppliers failed for {sku_row.get('sku')}")


def rma_info(sku_row):
    return registry().get(sku_row.get("source") or "manual", {}).get("rma", "contact supplier")