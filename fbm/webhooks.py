"""
fbm/webhooks.py — verify, dedupe, dispatch, replay, sweep.

Stripe webhook endpoint with signature verification, idempotent event handling,
and subscription/invoice/dunning dispatch. Degrades gracefully when Stripe is
not configured: signature verification is skipped in that case (dev mode).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from fbm import core as C
from fbm.billing import (
    _stripe_configured,
    generate_invoice,
    mark_invoice_paid,
    record_payment_failure,
    ensure_tables,
)

bp = Blueprint("webhooks", __name__, url_prefix="/webhooks")

# Stripe event types we handle and dispatch to billing side-effects.
HANDLED_EVENTS = (
    "checkout.session.completed",
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "invoice.created",
    "invoice.payment_succeeded",
    "invoice.payment_failed",
    "invoice.payment_action_required",
)

# Features a past-due account is still allowed to access.
PAST_DUE_ALLOWED = ("billing", "update_payment", "view_invoices")


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _event_processed(event_id):
    with C.db() as c:
        row = c.execute("SELECT 1 FROM processed_events WHERE event_id=?", (event_id,)).fetchone()
    return row is not None


def _mark_processed(event_id, kind):
    with C.db() as c:
        c.execute(
            "INSERT OR IGNORE INTO processed_events(event_id,kind) VALUES(?,?)",
            (event_id, kind),
        )


def _handle_event(kind, data):
    """Dispatch a Stripe event to the appropriate billing side-effect."""
    tenant_id = None
    try:
        obj = data.get("data", {}).get("object", {})
        tenant_id = (obj.get("metadata") or {}).get("tenant_id")

        if kind == "checkout.session.completed":
            _on_checkout_completed(obj)
        elif kind == "customer.subscription.created":
            _on_subscription_created(obj)
        elif kind == "customer.subscription.updated":
            _on_subscription_updated(obj)
        elif kind == "customer.subscription.deleted":
            _on_subscription_deleted(obj)
        elif kind == "invoice.created":
            _on_invoice_created(obj)
        elif kind == "invoice.payment_succeeded":
            _on_invoice_payment_succeeded(obj)
        elif kind == "invoice.payment_failed":
            _on_invoice_payment_failed(obj, tenant_id)
        elif kind == "invoice.payment_action_required":
            _on_invoice_payment_action_required(obj, tenant_id)
    except Exception as exc:  # pragma: no cover - defensive
        C.notify(f"webhooks: handler error for {kind}: {exc}", "warn")


def _on_checkout_completed(obj):
    tenant_id = (obj.get("metadata") or {}).get("tenant_id")
    sub = obj.get("subscription")
    customer = obj.get("customer")
    with C.db() as c:
        c.execute(
            "UPDATE subscriptions SET status='active', stripe_sub=COALESCE(?, stripe_sub), "
            "stripe_customer=COALESCE(?, stripe_customer) WHERE tenant_id=?",
            (sub, customer, tenant_id),
        )
        c.execute("UPDATE tenants SET status='active' WHERE id=?", (tenant_id,))
    C.notify(f"billing: checkout completed for tenant {tenant_id}", "info")


def _on_subscription_created(obj):
    tenant_id = (obj.get("metadata") or {}).get("tenant_id")
    if not tenant_id:
        return
    with C.db() as c:
        c.execute(
            "UPDATE subscriptions SET stripe_sub=?, status='active' WHERE tenant_id=?",
            (obj.get("id"), tenant_id),
        )


def _on_subscription_updated(obj):
    sub_id = obj.get("id")
    status = obj.get("status")
    with C.db() as c:
        c.execute("UPDATE subscriptions SET status=? WHERE stripe_sub=?", (status, sub_id))
        if status in ("canceled", "unpaid", "past_due"):
            c.execute(
                "UPDATE tenants SET status=? WHERE id IN "
                "(SELECT tenant_id FROM subscriptions WHERE stripe_sub=?)",
                (status, sub_id),
            )


def _on_subscription_deleted(obj):
    sub_id = obj.get("id")
    with C.db() as c:
        c.execute("UPDATE subscriptions SET status='canceled' WHERE stripe_sub=?", (sub_id,))


def _on_invoice_created(obj):
    customer = obj.get("customer")
    tenant_id = _tenant_for_customer(customer)
    if not tenant_id:
        return
    amount = obj.get("amount_due", 0) / 100.0
    with C.db() as c:
        exists = c.execute(
            "SELECT 1 FROM invoices WHERE stripe_invoice_id=?", (obj.get("id"),)
        ).fetchone()
    if not exists:
        due = None
        if obj.get("due_date"):
            due = _iso(datetime.fromtimestamp(obj.get("due_date")))
        with C.db() as c:
            c.execute(
                "INSERT INTO invoices(invoice_id,tenant_id,amount,status,stripe_invoice_id,due_date)"
                " VALUES(?,?,?,'open',?,?)",
                (f"inv_{tenant_id}_{obj.get('id')}", tenant_id, amount, obj.get("id"), due),
            )


def _on_invoice_payment_succeeded(obj):
    stripe_invoice_id = obj.get("id")
    customer = obj.get("customer")
    tenant_id = _tenant_for_customer(customer)
    if tenant_id:
        mark_invoice_paid(f"inv_{tenant_id}_{stripe_invoice_id}", stripe_invoice_id)
    C.notify(f"billing: invoice paid for tenant {tenant_id}", "info")


def _on_invoice_payment_failed(obj, tenant_id):
    if not tenant_id:
        tenant_id = _tenant_for_customer(obj.get("customer"))
    if tenant_id:
        record_payment_failure(tenant_id)
    C.notify(f"billing: invoice payment failed for tenant {tenant_id}", "warn")


def _on_invoice_payment_action_required(obj, tenant_id):
    if not tenant_id:
        tenant_id = _tenant_for_customer(obj.get("customer"))
    C.notify(f"billing: invoice action required for tenant {tenant_id}", "warn")


def _tenant_for_customer(customer):
    if not customer:
        return None
    with C.db() as c:
        row = c.execute(
            "SELECT tenant_id FROM subscriptions WHERE stripe_customer=?", (customer,)
        ).fetchone()
    return row["tenant_id"] if row else None


def _verify_signature(payload, sig_header):
    """Verify Stripe webhook signature. Returns (event, error).

    When Stripe is not configured or no webhook secret is set, the raw payload is
    parsed as JSON and returned without signature verification (dev mode).
    """
    secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not secret or not _stripe_configured():
        return json.loads(payload), None
    try:
        import stripe as stripe_mod
        event = stripe_mod.Webhook.construct_event(payload, sig_header, secret)
        return event, None
    except Exception as exc:  # pragma: no cover - stripe error
        return None, str(exc)


@bp.route("/", methods=["POST"])
def receive():
    """Stripe webhook endpoint: verify signature, dedupe, dispatch."""
    ensure_tables()
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature", "")

    event, err = _verify_signature(payload, sig_header)
    if err:
        C.notify(f"webhooks: signature verification failed: {err}", "warn")
        return jsonify({"error": "invalid signature"}), 400

    kind = event.get("type")
    event_id = event.get("id")

    # Idempotency: ignore events we have already processed.
    if event_id and _event_processed(event_id):
        return jsonify({"ok": True, "duplicate": True}), 200

    # Record the raw event for audit.
    with C.db() as c:
        c.execute(
            "INSERT INTO events(kind,ref,detail) VALUES('webhook',?,?)",
            (kind, json.dumps(event)),
        )
    if event_id:
        _mark_processed(event_id, kind)

    if kind in HANDLED_EVENTS:
        _handle_event(kind, event)

    return jsonify({"ok": True}), 200


def register(app):
    app.register_blueprint(bp)
    return app


def sweep():
    """Replay any unprocessed webhook events older than 24h (placeholder)."""
    pass


def main():
    print("webhooks ok")


if __name__ == "__main__":
    main()
