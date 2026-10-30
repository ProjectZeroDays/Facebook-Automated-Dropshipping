"""
fbm/billing.py — Stripe billing integration (checkout, webhooks, invoices, dunning).

Implements 3-tier subscription billing with Stripe:
- Starter: $49/month, 1 profile, 150 listings
- Pro: $99/month, 3 profiles, 800 listings
- Agency: $199/month, 10 profiles, unlimited

Includes proration, dunning management, and invoice generation.
Degrades gracefully when Stripe is not configured.
"""
from __future__ import annotations
import os, json, uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fbm import core as C

PLANS = {
    "starter": {"price": 49, "profiles": 1, "listings": 150,
                "features": ["1_profile", "150_listings", "email_support"]},
    "pro":     {"price": 99, "profiles": 3, "listings": 800,
                "features": ["3_profiles", "800_listings", "reprice",
                             "supplier_failover", "priority_support"]},
    "agency":  {"price": 199, "profiles": 10, "listings": None,
                "features": ["10_profiles", "unlimited_listings",
                             "api_access", "white_label", "named_support"]},
}

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_STARTER = os.getenv("STRIPE_PRICE_STARTER", "")
STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO", "")
STRIPE_PRICE_AGENCY = os.getenv("STRIPE_PRICE_AGENCY", "")

PRICE_IDS = {
    "starter": STRIPE_PRICE_STARTER,
    "pro": STRIPE_PRICE_PRO,
    "agency": STRIPE_PRICE_AGENCY,
}

DUNNING_MAX_RETRIES = 3
DUNNING_INTERVALS_HOURS = [1, 6, 24, 72]


def _stripe():
    if not STRIPE_SECRET_KEY:
        return None
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        return stripe
    except ImportError:
        C.notify("billing: stripe library not installed", "warn")
        return None


def _stripe_configured() -> bool:
    return bool(STRIPE_SECRET_KEY)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================
# Plans
# ============================================================

def list_plans() -> dict:
    return dict(PLANS)


def get_plan(name: str) -> dict | None:
    return PLANS.get(name)


# ============================================================
# Checkout
# ============================================================

def checkout(tenant_id: str, plan: str, email: str = "") -> dict:
    plan_obj = get_plan(plan)
    if not plan_obj:
        return {"ok": False, "error": f"unknown plan: {plan}"}

    if not _stripe_configured():
        return {"ok": True, "degraded": True, "url": None,
                "plan": plan, "amount": plan_obj["price"]}

    stripe = _stripe()
    if not stripe:
        return {"ok": False, "error": "stripe library not available"}

    try:
        session = stripe.checkout.Session.create(
            customer_email=email,
            payment_method_types=["card"],
            line_items=[{"price": PRICE_IDS.get(plan, ""),
                         "quantity": 1}],
            mode="subscription",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            metadata={"tenant_id": tenant_id, "plan": plan},
        )
        return {"ok": True, "degraded": False, "session_id": session.id,
                "customer_id": session.customer, "url": session.url,
                "plan": plan, "amount": plan_obj["price"]}
    except Exception as e:
        C.log_error(e, {"context": "billing.checkout",
                        "tenant_id": tenant_id, "plan": plan})
        return {"ok": False, "error": str(e)}


# ============================================================
# Invoices
# ============================================================

def ensure_tables():
    with C.db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS processed_events(
            event_id TEXT PRIMARY KEY, kind TEXT,
            processed_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS webhook_events(
            event_id TEXT PRIMARY KEY, event_type TEXT,
            processed_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS invoices(
            invoice_id TEXT PRIMARY KEY, tenant_id TEXT, amount REAL,
            status TEXT DEFAULT 'open', stripe_invoice_id TEXT,
            due_date TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS payment_failures(
            id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id TEXT,
            failure_count INTEGER DEFAULT 0,
            last_failure TEXT, next_retry TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS gmv_ledger(
            id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id TEXT,
            order_fp TEXT, amount REAL, fee REAL, period TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS dunning(
            id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id TEXT,
            attempt INTEGER DEFAULT 1, next_retry TEXT,
            status TEXT DEFAULT 'active',
            last_failure TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")


def generate_invoice(tenant_id: str, period: str,
                     plan: str | None = None) -> dict:
    ensure_tables()
    sub = get_subscription(tenant_id)
    plan_name = plan or (sub["plan"] if sub else "starter")
    amount = get_plan(plan_name)["price"] if get_plan(plan_name) else 0

    # Add GMV fees
    gmv_fee = 0.0
    with C.db() as c:
        row = c.execute(
            "SELECT COALESCE(SUM(fee),0) FROM gmv_ledger "
            "WHERE tenant_id=? AND period=?",
            (tenant_id, period)).fetchone()
        if row:
            gmv_fee = row[0] or 0

    total = amount + gmv_fee
    invoice_id = f"inv_{tenant_id}_{period}"

    with C.db() as c:
        c.execute(
            "INSERT OR REPLACE INTO invoices "
            "(invoice_id,tenant_id,amount,status,plan,gmv_fee,created_at) "
            "VALUES(?,?,?,'open',?,?,datetime('now'))",
            (invoice_id, tenant_id, total, plan_name, gmv_fee))

    return {"invoice_id": invoice_id, "tenant_id": tenant_id,
            "amount": total, "status": "open", "plan": plan_name,
            "gmv_fee": gmv_fee}


def get_invoice(invoice_id: str) -> dict | None:
    with C.db() as c:
        row = c.execute(
            "SELECT * FROM invoices WHERE invoice_id=?",
            (invoice_id,)).fetchone()
        return dict(row) if row else None


def list_invoices(tenant_id: str) -> list:
    with C.db() as c:
        rows = c.execute(
            "SELECT * FROM invoices WHERE tenant_id=? "
            "ORDER BY created_at DESC", (tenant_id,)).fetchall()
        return [dict(r) for r in rows]


def mark_invoice_paid(invoice_id: str,
                      stripe_invoice_id: str = None) -> dict:
    with C.db() as c:
        c.execute(
            "UPDATE invoices SET status='paid', "
            "stripe_invoice_id=COALESCE(?,stripe_invoice_id) "
            "WHERE invoice_id=?",
            (stripe_invoice_id, invoice_id))
        row = c.execute(
            "SELECT tenant_id FROM invoices WHERE invoice_id=?",
            (invoice_id,)).fetchone()
        if row:
            clear_dunning(row["tenant_id"])
    return {"invoice_id": invoice_id, "status": "paid"}


# ============================================================
# Dunning
# ============================================================

def record_payment_failure(tenant_id: str) -> dict:
    with C.db() as c:
        row = c.execute(
            "SELECT attempt FROM dunning WHERE tenant_id=? AND status='active'",
            (tenant_id,)).fetchone()
        if row:
            attempt = row[0] + 1
            c.execute(
                "UPDATE dunning SET attempt=?, last_failure=datetime('now') "
                "WHERE tenant_id=? AND status='active'",
                (attempt, tenant_id))
        else:
            attempt = 1
            c.execute(
                "INSERT INTO dunning(tenant_id,attempt,next_retry,"
                "status,last_failure,created_at) "
                "VALUES(?,1,datetime('now'),'active',datetime('now'),"
                "datetime('now'))",
                (tenant_id,))

        if attempt >= DUNNING_MAX_RETRIES:
            status = "exhausted"
            next_retry = None
        else:
            status = "active"
            hours = DUNNING_INTERVALS_HOURS[
                min(attempt - 1, len(DUNNING_INTERVALS_HOURS) - 1)]
            next_retry = (_now() + timedelta(hours=hours)).isoformat()

        c.execute(
            "UPDATE dunning SET next_retry=?, status=? "
            "WHERE tenant_id=? AND status='active'",
            (next_retry, status, tenant_id))

    return {"attempt": attempt, "status": status, "next_retry": next_retry}


def get_dunning_status(tenant_id: str) -> dict:
    with C.db() as c:
        row = c.execute(
            "SELECT * FROM dunning WHERE tenant_id=? AND status='active' "
            "ORDER BY attempt DESC LIMIT 1",
            (tenant_id,)).fetchone()
        if not row:
            return {"status": "none", "attempt": 0,
                    "next_retry": None}
        return {"status": row[5], "attempt": row[2],
                "next_retry": row[3]}


def clear_dunning(tenant_id: str):
    with C.db() as c:
        c.execute(
            "UPDATE dunning SET status='cleared' "
            "WHERE tenant_id=? AND status='active'", (tenant_id,))


def process_dunning() -> list:
    results = []
    with C.db() as c:
        rows = c.execute(
            "SELECT tenant_id, attempt, next_retry FROM dunning "
            "WHERE status='active' AND next_retry <= datetime('now')"
        ).fetchall()
        for row in rows:
            tenant_id = row[0]
            attempt = row[1] + 1
            if attempt >= DUNNING_MAX_RETRIES:
                c.execute(
                    "UPDATE dunning SET status='exhausted', "
                    "next_retry=NULL WHERE tenant_id=?",
                    (tenant_id,))
                results.append({"tenant_id": tenant_id,
                                "attempt": attempt,
                                "result": "exhausted"})
            else:
                hours = DUNNING_INTERVALS_HOURS[
                    min(attempt - 1,
                        len(DUNNING_INTERVALS_HOURS) - 1)]
                next_retry = (_now() + timedelta(hours=hours)).isoformat()
                c.execute(
                    "UPDATE dunning SET attempt=?, next_retry=? "
                    "WHERE tenant_id=?",
                    (attempt, next_retry, tenant_id))
                results.append({"tenant_id": tenant_id,
                                "attempt": attempt,
                                "result": "retry_scheduled",
                                "next_retry": next_retry})
    return results


# ============================================================
# Proration
# ============================================================

def calculate_proration(tenant_id: str, new_plan: str) -> dict:
    sub = get_subscription(tenant_id)
    current_plan = sub["plan"] if sub else "starter"

    if current_plan == new_plan:
        return {"current_plan": current_plan, "new_plan": new_plan,
                "proration": 0.0, "reason": "same plan"}

    current_price = get_plan(current_plan)["price"] if get_plan(
        current_plan) else 0
    new_price = get_plan(new_plan)["price"] if get_plan(new_plan) else 0

    # Prorate for remaining days in period (30-day month assumption)
    period_end = sub["period_end"] if sub else None
    if period_end:
        try:
            end_dt = datetime.fromisoformat(period_end)
            days_left = max((end_dt - _now()).days, 1)
            days_total = 30
            ratio = days_left / days_total
        except Exception:
            ratio = 0.5
    else:
        ratio = 0.5

    proration = (new_price - current_price) * ratio
    return {"current_plan": current_plan, "new_plan": new_plan,
            "proration": round(proration, 2),
            "reason": "upgrade" if proration > 0 else "downgrade"}


# ============================================================
# Plan changes
# ============================================================

def change_plan(tenant_id: str, new_plan: str) -> dict:
    if not get_plan(new_plan):
        return {"ok": False, "error": f"unknown plan: {new_plan}"}

    with C.db() as c:
        c.execute(
            "UPDATE subscriptions SET plan=? WHERE tenant_id=?",
            (new_plan, tenant_id))
        c.execute(
            "UPDATE tenants SET plan=? WHERE id=?",
            (new_plan, tenant_id))
    return {"ok": True, "new_plan": new_plan}


# ============================================================
# Feature enforcement
# ============================================================

def enforce_feature(tenant_id: str, feature: str) -> tuple[bool, str | None]:
    sub = get_subscription(tenant_id)
    if not sub:
        return False, "no active subscription"

    plan_name = sub["plan"]
    plan_obj = get_plan(plan_name)
    if not plan_obj:
        return False, "unknown plan"

    # Check status
    if sub.get("status") == "past_due":
        if feature in ("billing", "update_payment", "view_invoices"):
            return True, None
        return False, "account past_due"

    features = plan_obj.get("features", [])
    if feature in features:
        return True, None
    return False, f"{feature} not available on {plan_name} plan"


# ============================================================
# Trial
# ============================================================

def start_trial(tenant_id: str) -> dict:
    trial_ends = (_now() + timedelta(days=7)).isoformat()
    with C.db() as c:
        c.execute(
            "UPDATE tenants SET status='trialing', trial_ends=? WHERE id=?",
            (trial_ends, tenant_id))
    return {"ok": True, "tenant_id": tenant_id,
            "status": "trialing", "trial_ends": trial_ends}


# ============================================================
# GMV / invoice delta
# ============================================================

def invoice_delta(tenant_id: str, period: str) -> dict:
    with C.db() as c:
        row = c.execute(
            "SELECT COALESCE(SUM(fee),0) FROM gmv_ledger "
            "WHERE tenant_id=? AND period=?",
            (tenant_id, period)).fetchone()
        gmv_fee = row[0] or 0

    sub = get_subscription(tenant_id)
    sub_price = get_plan(sub["plan"])["price"] if sub else 0
    charge = max(gmv_fee, sub_price)
    return {"gmv_fee": gmv_fee, "subscription": sub_price,
            "charge": charge}


# ============================================================
# Compatibility wrappers for webhooks.py
# ============================================================

def create_checkout_session(tenant_id: str, plan: str,
                            success_url: str, cancel_url: str) -> dict:
    return checkout(tenant_id, plan)


def handle_webhook(payload: bytes, sig_header: str) -> dict:
    ensure_tables()
    stripe = _stripe()
    if not stripe:
        # Dev mode - parse as JSON without signature verification
        try:
            event = json.loads(payload)
        except Exception:
            return {"error": "invalid payload"}
    else:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET)
        except Exception as e:
            return {"error": f"webhook signature invalid: {e}"}

    event_id = event.get("id")
    event_type = event.get("type")

    # Idempotency
    with C.db() as c:
        existing = c.execute(
            "SELECT id FROM processed_events WHERE event_id=?",
            (event_id,)).fetchone()
        if existing:
            return {"status": "already_processed", "event_id": event_id}
        c.execute(
            "INSERT INTO processed_events(event_id,kind,processed_at) "
            "VALUES(?,?,datetime('now'))",
            (event_id, event_type))

    data = event.get("data", {}).get("object", {})
    tenant_id = (data.get("metadata") or {}).get("tenant_id")

    if event_type == "checkout.session.completed":
        if tenant_id:
            plan = (data.get("metadata") or {}).get("plan", "starter")
            change_plan(tenant_id, plan)
            c = C.db()
            c.execute(
                "UPDATE tenants SET status='active' WHERE id=?",
                (tenant_id,))
    elif event_type == "invoice.payment_succeeded":
        if tenant_id:
            clear_dunning(tenant_id)
    elif event_type == "invoice.payment_failed":
        if tenant_id:
            record_payment_failure(tenant_id)

    return {"status": "processed", "event_id": event_id,
            "type": event_type}


def run_dunning() -> int:
    results = process_dunning()
    return len(results)


def get_subscription(tenant_id: str) -> dict | None:
    with C.db() as c:
        row = c.execute(
            "SELECT * FROM subscriptions WHERE tenant_id=? "
            "AND status IN ('active','trialing')",
            (tenant_id,)).fetchone()
        return dict(row) if row else None


def check_quota(tenant_id: str, resource: str,
                current_usage: int) -> dict:
    sub = get_subscription(tenant_id)
    if not sub:
        return {"allowed": False, "reason": "no active subscription"}

    plan = sub["plan"]
    plan_limits = PLANS.get(plan, {})

    if resource == "profiles":
        limit = plan_limits.get("profiles", 1)
    elif resource == "listings":
        limit = plan_limits.get("listings", 150)
    else:
        return {"allowed": True, "limit": None}

    return {
        "allowed": current_usage < limit if limit is not None else True,
        "limit": limit,
        "current": current_usage,
        "plan": plan,
    }


def main():
    C.load_env()
    print(f"billing: {len(PLANS)} plans configured")
    for name, p in PLANS.items():
        print(f"  {name}: ${p['price']}/mo, {p['profiles']} profiles, "
              f"{p['listings']} listings")
    print("billing ok")


if __name__ == "__main__":
    main()