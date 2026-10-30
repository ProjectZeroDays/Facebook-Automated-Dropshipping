"""
fbm/wizard.py — 9-screen onboarding that pre-configures everything before payment.
"""
from __future__ import annotations
from flask import Blueprint, render_template, request, redirect, session
from fbm import config, regions, settings, flags, credits, onboarding, vault, integrations

bp = Blueprint("wizard", __name__)
STEPS = ["welcome","plan","region","mode","vendor","niches","review","facebook","bot"]


@bp.route("/wizard", methods=["GET","POST"])
def wizard():
    step = request.args.get("step", "welcome")
    if request.method == "POST":
        answers = session.setdefault("wizard", {})
        answers.update({k: v for k, v in request.form.items()})
        session["wizard"] = answers
        nxt = STEPS[min(STEPS.index(step) + 1, len(STEPS) - 1)]
        return redirect(f"/wizard?step={nxt}")
    ctx = {"step": step, "steps": STEPS, "answers": session.get("wizard", {}),
           "states": regions.list_all(), "tax": regions.profile(session.get("wizard",{}).get("state","TN")),
           "vendors": integrations.REGISTRY, "plans": __import__("billing").PLANS}
    return render_template(f"wizard/{step}.html", **ctx)


@bp.route("/wizard/finish", methods=["POST"])
def finish():
    a = session.get("wizard", {})
    tenant = a["tenant_id"]
    onboarding.apply_answers(tenant, a)
    config.save(state=a["state"], city=a["city"], mode=a["mode"])
    credits.attach_referral(tenant, a["ref"]) if a.get("ref") else None
    from fbm import bootstrap
    bootstrap.seed_from(a.get("niches", []))
    return redirect("/?first_run=1")