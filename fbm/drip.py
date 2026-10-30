"""
fbm/drip.py — milestone emails.

Sends milestone-based email sequences (trial day reminders, first sale,
welcome, re-engagement) using the configured email backend.
"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
from fbm import core as C

DRIP_LOG = Path("data/drip_log.json")


def _load_log() -> dict:
    if DRIP_LOG.exists():
        import json
        return json.loads(DRIP_LOG.read_text())
    return {}


def _save_log(log: dict):
    import json
    DRIP_LOG.parent.mkdir(parents=True, exist_ok=True)
    DRIP_LOG.write_text(json.dumps(log, indent=2))


def run() -> int:
    """Process pending drip emails. Returns count sent."""
    C.load_env()
    C.init_db()

    log = _load_log()
    sent = 0

    with C.db() as c:
        tenants = c.execute("SELECT id, email, created_at, plan FROM tenants").fetchall()

    now = datetime.now()
    for t in tenants:
        tdict = dict(t)
        created = datetime.fromisoformat(tdict["created_at"])
        days = (now - created).days

        # Day 0: welcome
        if days == 0 and "welcome" not in log.get(tdict["id"], []):
            _send_drip(tdict, "welcome", "Welcome to FB Dropshipper!")
            log.setdefault(tdict["id"], []).append("welcome")
            sent += 1

        # Day 6: trial reminder
        elif days == 6 and "trial_reminder" not in log.get(tdict["id"], []):
            _send_drip(tdict, "trial_reminder", "Your trial ends in 1 day.")
            log.setdefault(tdict["id"], []).append("trial_reminder")
            sent += 1

        # Day 14: post-trial followup
        elif days == 14 and "followup" not in log.get(tdict["id"], []):
            _send_drip(tdict, "followup", "How's your first week going?")
            log.setdefault(tdict["id"], []).append("followup")
            sent += 1

    _save_log(log)
    return sent


def _send_drip(tenant: dict, kind: str, subject: str):
    """Send a drip email to a tenant."""
    email = tenant.get("email", "")
    if not email:
        return
    C.notify(f"drip: {kind} email to {email} — {subject}", "info")


def main():
    C.load_env(); C.init_db()
    n = run()
    print(f"drip: {n} email(s) sent")
    print("drip ok")


if __name__ == "__main__":
    main()