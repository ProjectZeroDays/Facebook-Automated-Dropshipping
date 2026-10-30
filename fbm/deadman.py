"""
fbm/deadman.py — healthchecks.io pings + two-strike escalation.
"""
from __future__ import annotations
import os
import requests
from fbm import core as C
from fbm.observability import get_logger

log = get_logger("deadman")


def ping(kind="success"):
    base = os.getenv("HEALTHCHECK_URL")
    if base:
        try:
            requests.get(f"{base}/{kind}", timeout=10)
            log.info("deadman ping sent", extra={"event": "deadman.ping", "kind": kind})
        except Exception:
            log.warning("deadman ping failed",
                        extra={"event": "deadman.ping_failed", "kind": kind})


def strike(reason="", tenant_id=C.DEFAULT_TENANT_ID):
    with C.db() as c:
        c.execute("INSERT INTO events(kind,ref,detail,tenant_id) VALUES('miss',?,?,?)",
                  ("run", reason, tenant_id))
        misses = c.execute("SELECT COUNT(*) n FROM events WHERE kind='miss' "
                           "AND created_at > datetime('now','-1 day') AND tenant_id=?",
                           (tenant_id,)).fetchone()["n"]
    if misses >= 2:
        C.notify(f"DEAD-MAN: {misses} missed runs in 24h ({reason})", "error")
        log.error("deadman escalation",
                  extra={"event": "deadman.escalation", "misses": misses, "reason": reason})
    else:
        log.info("deadman strike recorded",
                 extra={"event": "deadman.strike", "misses": misses, "reason": reason})
    return misses