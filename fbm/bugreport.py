"""
fbm/bugreport.py — diagnostics bundle.

Collects system info, version, config, recent events, and errors into a
machine-readable diagnostic bundle for support and troubleshooting.
"""
from __future__ import annotations
import os, sys, json, platform
from datetime import datetime
from pathlib import Path
from fbm import core as C


def bundle(tenant_id=C.DEFAULT_TENANT_ID) -> dict:
    """Return a diagnostic bundle dict with system, version, config, events."""
    info = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "python": sys.version,
        },
        "app": {
            "version": getattr(C, "__version__", "0.2.0"),
            "cwd": os.getcwd(),
            "env_file": os.getenv("FBM_ENV", ".env"),
            "db": os.getenv("FBM_DB", "fbm.sqlite"),
            "profile": os.getenv("FBM_PROFILE", "fb_profile"),
        },
        "config": {},
        "recent_events": [],
        "active_skus": 0,
        "tenant_id": tenant_id,
        "errors": [],
    }

    # Load env vars (non-secret keys only)
    safe_keys = ["FBM_DB", "FBM_PROFILE", "FBM_ENV", "FBM_SELECTORS", "FBM_STATE"]
    for k in safe_keys:
        info["config"][k] = os.getenv(k, "")

    # Recent events from DB
    try:
        with C.db() as c:
            rows = c.execute(
                "SELECT kind, ref, detail, account, created_at "
                "FROM events WHERE tenant_id=? ORDER BY id DESC LIMIT 20",
                (tenant_id,),
            ).fetchall()
            info["recent_events"] = [dict(r) for r in rows]

            n = c.execute("SELECT COUNT(*) n FROM skus WHERE active=1 AND tenant_id=?",
                          (tenant_id,)).fetchone()["n"]
            info["active_skus"] = n
    except Exception as e:
        info["errors"].append(f"db query failed: {e}")

    return info


def main():
    C.load_env()
    b = bundle()
    print(json.dumps(b, indent=2, default=str))
    print("bugreport ok")


if __name__ == "__main__":
    main()