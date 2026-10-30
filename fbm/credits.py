"""
fbm/credits.py — dollar credits. Two-sided referral, fraud-guarded.
"""
from __future__ import annotations
import os
from fbm import core as C


def grant(tenant_id, amount, reason, ref=None, expires_months=None):
    import flags
    exp = expires_months if expires_months is not None else flags.get()["credit_expiry_months"]
    with C.db() as c:
        c.execute("INSERT INTO credits(tenant_id,amount,reason,ref,expires_at) "
                  "VALUES(?,?,?,?, datetime('now', ?))",
                  (tenant_id, round(float(amount), 2), reason, ref, f"+{exp} months"))
    return available(tenant_id)


def available(tenant_id):
    with C.db() as c:
        r = c.execute("SELECT COALESCE(SUM(amount),0) g, COALESCE(SUM(applied),0) a "
                      "FROM credits WHERE tenant_id=? AND (expires_at IS NULL OR expires_at > datetime('now'))",
                      (tenant_id,)).fetchone()
    return round(float(r["g"]) - float(r["a"]), 2)


def apply_to_stripe(tenant_id):
    """Push available credit to the Stripe customer as a negative balance."""
    import stripe
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    amt = available(tenant_id)
    if amt <= 0: return 0
    with C.db() as c:
        s = c.execute("SELECT stripe_customer FROM subscriptions WHERE tenant_id=?", (tenant_id,)).fetchone()
    if not s: return 0
    stripe.Customer.create_balance_transaction(
        s["stripe_customer"], amount=-int(round(amt * 100)), currency="usd",
        description="referral credit")
    with C.db() as c:
        c.execute("INSERT INTO credits(tenant_id,applied,reason) VALUES(?,?, 'applied')",
                  (tenant_id, amt))
    return amt


def reward_flow(referred_tenant, referrer_tenant):
    """Two-sided: referee credited at signup, referrer credited on first paid invoice."""
    import flags
    f = flags.get()
    if f["reward_mode"] != "credit":
        return {"mode": "free_month"}
    amt = f["referral_reward_usd"]
    grant(referred_tenant, amt, "referral_referee")
    with C.db() as c:
        c.execute("UPDATE referrals SET status='awaiting_payment' WHERE referred_tenant=?", (referred_tenant,))
    return {"referee_credit": amt, "referrer_pending": amt if f["referral_two_sided"] else 0}


def credit_referrer_on_payment(referred_tenant):
    import flags
    with C.db() as c:
        r = c.execute("SELECT * FROM referrals WHERE referred_tenant=? AND status='awaiting_payment'",
                      (referred_tenant,)).fetchone()
    if not r: return None
    amt = flags.get()["referral_reward_usd"]
    grant(r["referrer_tenant"], amt, "referral_referrer", ref=referred_tenant)
    with C.db() as c:
        c.execute("UPDATE referrals SET status='credited', converted_at=datetime('now') WHERE id=?", (r["id"],))
    return {"referrer": r["referrer_tenant"], "credited": amt}


def lapse(referee_tenant):
    """Trial ended without payment — referrer earns nothing."""
    with C.db() as c:
        c.execute("UPDATE referrals SET status='lapsed' WHERE referred_tenant=? "
                  "AND referrer_credited_at IS NULL", (referee_tenant,))