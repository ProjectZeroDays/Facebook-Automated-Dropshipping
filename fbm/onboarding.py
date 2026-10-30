"""
fbm/onboarding.py — check FB standing, ask the questions, pre-configure everything.
"""
from __future__ import annotations
from fbm import core as C
from fbm import config, settings


QUESTIONS = [
    ("fulfilment", "How will you get items to buyers?", ["ship from supplier","drop off locally","both"]),
    ("dropoff_where", "If you drop off locally, where?", ["from home","public spot (store/parking)","both"]),
    ("address", "Your pickup address (for local mode)", "text"),
    ("hours", "When can buyers collect?", ["weekdays 9-5","evenings","weekends","flexible"]),
    ("radius", "How far will you deliver/serve?", ["10 mi","25 mi","40 mi","50+ mi"]),
    ("phone", "Support number for buyers", "text"),
    ("returns", "Accept returns?", ["yes 30 days","yes 14 days","no"]),
    ("shipping_payer", "Who pays shipping?", ["Meta/FB pricing","my supplier's estimate"]),
    ("tone", "How should the bot sound?", ["friendly-short","professional","casual"]),
]


def check_fb(page):
    page.goto("https://www.facebook.com/marketplace/you/selling", wait_until="domcontentloaded")
    body = page.inner_text("body")[:3000]
    if "Log in" in body: return {"status": "no_account"}
    if "access removed" in body or "restricted" in body: return {"status": "restricted"}
    return {"status": "ok"}


def apply_answers(tenant_id, answers):
    mode = {"ship from supplier":"ship","drop off locally":"local","both":"hybrid"}[answers["fulfilment"]]
    config.save(mode=mode)
    settings.save_business(tenant_id,
        phone=answers["phone"],
        returns_allowed=1 if answers["returns"].startswith("yes") else 0,
        return_days=int(answers["returns"].split()[1]) if answers["returns"].startswith("yes") else 0,
        shipping_payer="fb" if answers["shipping_payer"].startswith("Meta") else "supplier",
        hours=answers["hours"], policies=settings.draft_policies(answers))
    from fbm import bot_rules
    bot_rules.save_rules(tenant_id, {"tone": answers["tone"]})
    return {"mode": mode, "configured": True}