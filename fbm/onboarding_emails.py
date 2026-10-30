"""
fbm/onboarding_emails.py — day 0-14 sequence.

Sends the onboarding email sequence: day 0 welcome, day 2 setup check,
day 3 first listing, day 4 pricing tips, day 5 first sale, day 10 review,
day 14 retention check.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from pathlib import Path
from fbm import core as C

ONBOARDING_LOG = Path("data/onboarding_log.json")

SEQUENCE = [
    (0, "welcome", "Welcome — here's how to get started"),
    (2, "setup_check", "Is your profile set up correctly?"),
    (3, "first_listing", "Time to publish your first listing"),
    (4, "pricing_tips", "Pricing strategies that sell"),
    (5, "first_sale", "Congrats on your first sale!"),
    (10, "review", "How are things going?"),
    (14, "retention", "Let's keep the momentum going"),
]


def _load_log() -> dict:
    if ONBOARDING_LOG.exists():
        import json
        return json.loads(ONBOARDING_LOG.read_text())
    return {}


def _save_log(log: dict):
    import json
    ONBOARDING_LOG.parent.mkdir(parents=True, exist_ok=True)
    ONBOARDING_LOG.write_text(json.dumps(log, indent=2))


def run() -> int:
    """Process pending onboarding emails. Returns count sent."""
    C.load_env()
    C.init_db()

    log = _load_log()
    sent = 0

    with C.db() as c:
        tenants = c.execute("SELECT id, email, created_at FROM tenants").fetchall()

    now = datetime.now()
    for t in tenants:
        tdict = dict(t)
        created = datetime.fromisoformat(tdict["created_at"])
        days = (now - created).days

        for day, kind, subject in SEQUENCE:
            key = f"day{day}"
            if days == day and key not in log.get(tdict["id"], []):
                _send_email(tdict, kind, subject)
                log.setdefault(tdict["id"], []).append(key)
                sent += 1

    _save_log(log)
    return sent


def _send_email(tenant: dict, kind: str, subject: str):
    """Send an onboarding email to a tenant."""
    email = tenant.get("email", "")
    if not email:
        return
    C.notify(f"onboarding: {kind} email to {email} — {subject}", "info")


def main():
    C.load_env(); C.init_db()
    n = run()
    print(f"onboarding_emails: {n} email(s) sent")
    print("onboarding_emails ok")


if __name__ == "__main__":
    main()