"""
fbm/flags.py — global + per-tenant feature flags. Admin-only mutation.
"""
from __future__ import annotations
import json
from fbm import core as C

GLOBAL = "GLOBAL"

DEFAULTS = {
  "trial_enabled": True,
  "trial_days": 7,
  "signups_open": True,
  "reward_mode": "credit",
  "referral_reward_usd": 25.0,
  "referral_two_sided": True,
  "gmv_fee_enabled": False,
  "maintenance_mode": False,
  "readonly_mode": False,
  "modules": {"publish": True, "crosslist": True, "tracking": True,
              "inbox_ai": True, "insights": True, "groups": True},
}


def _row(scope):
    with C.db() as c:
        r = c.execute("SELECT json FROM flags WHERE scope=?", (scope,)).fetchone()
    return json.loads(r["json"]) if r else {}


def get(tenant_id=None):
    merged = {**DEFAULTS, **_row(GLOBAL)}
    if tenant_id:
        t = _row(tenant_id)
        merged = {**merged, **{k: v for k, v in t.items() if k != "modules"}}
        merged["modules"] = {**merged["modules"], **t.get("modules", {})}
    return merged


def set_flag(patch, scope=GLOBAL, actor="admin"):
    data = {**_row(scope), **patch}
    # The event is owned by the tenant whose flags changed (scope), or the
    # default tenant for global flag changes.
    flag_tenant = scope if scope != GLOBAL else C.DEFAULT_TENANT_ID
    with C.db() as c:
        c.execute("INSERT INTO flags(scope,json,updated_at) VALUES(?,?,datetime('now')) "
                  "ON CONFLICT(scope) DO UPDATE SET json=excluded.json, updated_at=excluded.updated_at",
                  (scope, json.dumps(data)))
        c.execute("INSERT INTO events(kind,ref,detail,tenant_id) VALUES('flag_change',?,?,?)",
                  (scope, json.dumps(patch), flag_tenant))
    return data


def module_on(name, tenant_id=None):
    f = get(tenant_id)
    return f["modules"].get(name, False) and not f["maintenance_mode"]