"""
tests/test_billing.py — tests for fbm billing (checkout, invoices, dunning,
proration, tier enforcement).

Stripe API calls are mocked; no live Stripe calls are ever made. Billing
functions degrade gracefully when STRIPE_SECRET_KEY is not configured.
"""
from __future__ import annotations

import fbm.billing as billing
import fbm.webhooks as webhooks


class FakeStripeObject(dict):
    def __init__(self, **kw):
        super().__init__(kw)
        self.__dict__.update(kw)


class FakeStripe:
    class Customer:
        @staticmethod
        def create(**kw):
            return FakeStripeObject(
                id="cus_test_123", email=kw.get("email"), metadata=kw.get("metadata"))

    class checkout:
        class Session:
            @staticmethod
            def create(**kw):
                return FakeStripeObject(
                    id="cs_test_123",
                    url="https://checkout.stripe.com/c/pay/cs_test_123",
                    subscription="sub_test_123",
                )

    class Invoice:
        @staticmethod
        def create(**kw):
            return FakeStripeObject(id="in_test_123")

    class Webhook:
        @staticmethod
        def construct_event(payload, sig_header, secret):
            return FakeStripeObject(
                id="evt_test_123",
                type="checkout.session.completed",
                data={"object": {"id": "cs_test_123",
                                 "metadata": {"tenant_id": "t_webhook"}}},
            )


def _seed_tenant(env, tenant_id="t_billing", plan="starter", status="active"):
    with env.db() as c:
        c.execute(
            "INSERT OR REPLACE INTO tenants(id,email,plan,status,created_at) "
            "VALUES(?,?,?,?,datetime('now'))",
            (tenant_id, f"{tenant_id}@example.com", plan, status),
        )
        c.execute(
            "INSERT OR REPLACE INTO subscriptions(tenant_id,plan,amount,status,"
            "period_end,stripe_customer,stripe_sub) VALUES(?,?,?,?,datetime('+30 days'),NULL,NULL)",
            (tenant_id, plan, billing.PLANS[plan]["price"], status),
        )


def _enable_stripe(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_123")
    monkeypatch.setattr(billing, "_stripe_configured", lambda: True)
    monkeypatch.setattr(billing, "_stripe", FakeStripe)


# --------------------------------------------------------------------------- plans
def test_billing_module_imports():
    assert billing is not None


def test_top_level_reexport_works():
    import billing as top_billing
    assert top_billing.checkout is billing.checkout


def test_list_plans_returns_all_tiers():
    plans = billing.list_plans()
    assert set(plans) == {"starter", "pro", "agency"}
    assert plans["starter"]["price"] == 49
    assert plans["pro"]["price"] == 99
    assert plans["agency"]["price"] == 199


def test_get_plan_unknown_returns_none():
    assert billing.get_plan("notaplan") is None
    assert billing.get_plan("starter")["price"] == 49


# --------------------------------------------------------------------------- checkout
def test_checkout_degraded_without_stripe_key(env, monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    _seed_tenant(env)
    res = billing.checkout("t_billing", "pro", "user@example.com")
    assert res["ok"] is True
    assert res["degraded"] is True
    assert res["url"] is None
    assert res["plan"] == "pro"
    assert res["amount"] == 99


def test_checkout_unknown_plan_error(env):
    _seed_tenant(env)
    res = billing.checkout("t_billing", "bogus", "user@example.com")
    assert res["ok"] is False
    assert "unknown plan" in res["error"]


def test_checkout_with_mocked_stripe(env, monkeypatch):
    _enable_stripe(monkeypatch)
    _seed_tenant(env)
    res = billing.checkout("t_billing", "starter", "user@example.com")
    assert res["ok"] is True
    assert res["degraded"] is False
    assert res["session_id"] == "cs_test_123"
    assert res["customer_id"] == "cus_test_123"
    assert "checkout.stripe.com" in res["url"]


# --------------------------------------------------------------------------- invoices
def test_generate_invoice_creates_invoice(env):
    _seed_tenant(env, plan="pro", status="active")
    inv = billing.generate_invoice("t_billing", "2026-10")
    assert inv["status"] == "open"
    assert inv["amount"] == 99.0
    assert inv["plan"] == "pro"
    assert inv["invoice_id"].startswith("inv_t_billing_2026-10")

    got = billing.get_invoice(inv["invoice_id"])
    assert got is not None
    assert got["amount"] == 99.0


def test_generate_invoice_includes_gmv_fee(env):
    _seed_tenant(env, plan="starter", status="active")
    with env.db() as c:
        c.execute(
            "INSERT INTO gmv_ledger(tenant_id,order_fp,amount,fee,period) "
            "VALUES(?,?,?,?,'2026-10')",
            ("t_billing", "order_1", 100.0, 3.0),
        )
    inv = billing.generate_invoice("t_billing", "2026-10")
    assert inv["gmv_fee"] == 3.0
    assert inv["amount"] == 49.0 + 3.0


def test_list_invoices(env):
    _seed_tenant(env, plan="pro", status="active")
    billing.generate_invoice("t_billing", "2026-09")
    billing.generate_invoice("t_billing", "2026-10")
    invs = billing.list_invoices("t_billing")
    assert len(invs) == 2


def test_mark_invoice_paid_clears_dunning(env):
    _seed_tenant(env, plan="pro", status="active")
    inv = billing.generate_invoice("t_billing", "2026-10")
    billing.record_payment_failure("t_billing")
    updated = billing.mark_invoice_paid(inv["invoice_id"])
    assert updated["status"] == "paid"
    assert billing.get_dunning_status("t_billing")["status"] == "cleared"


def test_invoice_delta_backward_compat(env):
    _seed_tenant(env, plan="pro", status="active")
    with env.db() as c:
        c.execute(
            "INSERT INTO gmv_ledger(tenant_id,order_fp,amount,fee,period) "
            "VALUES(?,?,?,?,'2026-10')",
            ("t_billing", "order_2", 200.0, 6.0),
        )
    delta = billing.invoice_delta("t_billing", "2026-10")
    assert delta["gmv_fee"] == 6.0
    assert delta["subscription"] == 99.0
    assert delta["charge"] == 99.0  # max(6, 99)


# --------------------------------------------------------------------------- dunning
def test_record_payment_failure_schedules_retry(env):
    _seed_tenant(env)
    rec = billing.record_payment_failure("t_billing")
    assert rec["attempt"] == 1
    assert rec["status"] == "active"
    assert rec["next_retry"] is not None

    rec2 = billing.record_payment_failure("t_billing")
    assert rec2["attempt"] == 2
    assert rec2["next_retry"] != rec["next_retry"]


def test_record_payment_failure_exhausts_after_max(env):
    _seed_tenant(env)
    for _ in range(4):
        billing.record_payment_failure("t_billing")
    rec = billing.record_payment_failure("t_billing")
    assert rec["attempt"] == 5
    assert rec["status"] == "exhausted"
    assert rec["next_retry"] is None


def test_get_dunning_status_none_when_empty(env):
    _seed_tenant(env)
    assert billing.get_dunning_status("t_billing")["status"] == "none"


def test_process_dunning_schedules_retry_without_stripe(env, monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.setattr(billing, "_stripe_configured", lambda: False)
    _seed_tenant(env)
    with env.db() as c:
        c.execute(
            "INSERT INTO dunning(tenant_id,attempt,next_retry,status,last_failure) "
            "VALUES(?,1,?, 'active', datetime('now'))",
            ("t_billing", "2000-01-01 00:00:00"),
        )
    results = billing.process_dunning()
    assert len(results) == 1
    assert results[0]["result"] == "retry_scheduled"
    assert results[0]["attempt"] == 2


def test_process_dunning_recovers_with_mocked_stripe(env, monkeypatch):
    _enable_stripe(monkeypatch)
    _seed_tenant(env)
    with env.db() as c:
        c.execute(
            "UPDATE subscriptions SET stripe_customer='cus_test_123', stripe_sub='sub_test_123' "
            "WHERE tenant_id='t_billing'",
        )
        c.execute(
            "INSERT INTO dunning(tenant_id,attempt,next_retry,status,last_failure) "
            "VALUES(?,1,?, 'active', datetime('now'))",
            ("t_billing", "2000-01-01 00:00:00"),
        )
    results = billing.process_dunning()
    assert len(results) == 1
    assert results[0]["result"] == "recovered"


# --------------------------------------------------------------------------- proration
def test_calculate_proration_upgrade(env):
    _seed_tenant(env, plan="starter")
    with env.db() as c:
        c.execute(
            "UPDATE subscriptions SET period_end=? WHERE tenant_id='t_billing'",
            (billing._iso(billing._now() + __import__("datetime").timedelta(days=12)),),
        )
    pror = billing.calculate_proration("t_billing", "pro")
    assert pror["current_plan"] == "starter"
    assert pror["new_plan"] == "pro"
    assert pror["proration"] > 0  # upgrade costs more


def test_calculate_proration_downgrade(env):
    _seed_tenant(env, plan="pro")
    with env.db() as c:
        c.execute(
            "UPDATE subscriptions SET period_end=? WHERE tenant_id='t_billing'",
            (billing._iso(billing._now() + __import__("datetime").timedelta(days=12)),),
        )
    pror = billing.calculate_proration("t_billing", "starter")
    assert pror["proration"] < 0  # downgrade credits


def test_calculate_proration_same_plan(env):
    _seed_tenant(env, plan="starter")
    pror = billing.calculate_proration("t_billing", "starter")
    assert pror["proration"] == 0.0
    assert pror["reason"] == "same plan"


def test_change_plan_updates_subscription(env):
    _seed_tenant(env, plan="starter")
    res = billing.change_plan("t_billing", "agency")
    assert res["ok"] is True
    assert res["new_plan"] == "agency"
    with env.db() as c:
        row = c.execute("SELECT plan FROM subscriptions WHERE tenant_id='t_billing'").fetchone()
        assert row["plan"] == "agency"


# --------------------------------------------------------------------------- tier enforcement
def test_enforce_feature_allowed(env):
    _seed_tenant(env, plan="pro")
    allowed, reason = billing.enforce_feature("t_billing", "reprice")
    assert allowed is True
    assert reason is None


def test_enforce_feature_blocked_wrong_tier(env):
    _seed_tenant(env, plan="starter")
    allowed, reason = billing.enforce_feature("t_billing", "api_access")
    assert allowed is False
    assert "not available" in reason


def test_enforce_feature_blocked_when_past_due(env):
    _seed_tenant(env, plan="pro", status="past_due")
    allowed, reason = billing.enforce_feature("t_billing", "reprice")
    assert allowed is False
    assert "past_due" in reason

    allowed, reason = billing.enforce_feature("t_billing", "billing")
    assert allowed is True


def test_start_trial_sets_status(env):
    _seed_tenant(env, status="active")
    billing.start_trial("t_billing")
    with env.db() as c:
        row = c.execute("SELECT status, trial_ends FROM tenants WHERE id='t_billing'").fetchone()
    assert row["status"] == "trialing"
    assert row["trial_ends"] is not None


# --------------------------------------------------------------------------- webhooks
def test_webhooks_module_imports():
    assert webhooks is not None


def test_webhook_receive_dev_mode(env, monkeypatch):
    from flask import Flask
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    app = Flask(__name__)
    webhooks.register(app)
    client = app.test_client()
    payload = {"type": "checkout.session.completed", "id": "evt_dev_1",
               "data": {"object": {"id": "cs_dev_1", "metadata": {}}}}
    resp = client.post("/webhooks/", json=payload)
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True


def test_webhook_idempotency(env, monkeypatch):
    from flask import Flask
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    app = Flask(__name__)
    webhooks.register(app)
    client = app.test_client()
    payload = {"type": "invoice.payment_succeeded", "id": "evt_idem_1",
               "data": {"object": {"id": "in_idem_1", "amount_due": 9900, "customer": "cus_x"}}}
    first = client.post("/webhooks/", json=payload)
    assert first.get_json().get("duplicate") is not True
    second = client.post("/webhooks/", json=payload)
    assert second.get_json()["duplicate"] is True


def test_webhook_verify_signature_dev_mode_returns_parsed():
    import os
    old = os.environ.get("STRIPE_WEBHOOK_SECRET")
    os.environ.pop("STRIPE_WEBHOOK_SECRET", None)
    try:
        event, err = webhooks._verify_signature(b'{"type":"x","id":"e1"}', "")
        assert err is None
        assert event["type"] == "x"
    finally:
        if old is not None:
            os.environ["STRIPE_WEBHOOK_SECRET"] = old
        else:
            os.environ.pop("STRIPE_WEBHOOK_SECRET", None)
