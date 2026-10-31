"""Thin page routes for the marketing surface, billing, referrals, help,
vendor directory, design system and admin tenant console.

Register in app.py:   from .web_pages import bp as pages_bp; app.register_blueprint(pages_bp)
Assumes base.html defines blocks: title, body_class, page_actions, content, scripts
and injects: current_user, tenant, csrf_token, theme, plans, year.
"""
from __future__ import annotations

import csv
import io
import time

from flask import (Blueprint, abort, current_app, g, jsonify, redirect, render_template,
                   request, send_file, session, url_for)

from .core import db

bp = Blueprint("pages", __name__)

PLANS = [
    dict(key="starter", name="Starter", price=49, featured=False,
         blurb="Bring your own API key. Full engine, 1 profile.",
         lines=["1 Facebook profile", "Up to 150 live listings", "BYO LLM API key",
                "Tracking intake", "Email support"],
         cta="Start with Starter"),
    dict(key="pro", name="Pro", price=99, featured=True,
         blurb="Bundled local model. The tier most people land on.",
         lines=["3 profiles", "Up to 800 live listings", "Bundled local model",
                "Competitor re-pricing", "Supplier failover", "Priority support"],
         cta="Start with Pro"),
    dict(key="agency", name="Agency", price=199, featured=False,
         blurb="Client workspaces, white-label reports, seats.",
         lines=["10 profiles", "Unlimited listings", "Client sub-accounts",
                "White-label reports", "API access", "Named support"],
         cta="Start with Agency"),
]

FEATURES = [
    dict(tag="reliability", tone="success", title="Self-healing selectors",
         body="18 fields are probed every run. When Facebook moves the DOM the registry rewrites itself instead of failing silently."),
    dict(tag="rate limits", tone="warn", title="Adaptive throttle",
         body="Token bucket with persisted state and backoff. Stays under the ~10/hour safe publish cadence."),
    dict(tag="orders", tone="accent", title="Plus-address tracking intake",
         body="The order ID lives in the recipient address, so a tracking number never has to be fuzzy-matched."),
    dict(tag="suppliers", tone="info", title="Primary / backup failover",
         body="If the primary supplier runs dry the SKU reroutes to the backup with the same RMA lookup path."),
    dict(tag="copy", tone="accent", title="LLM copy with a validator",
         body="A second pass rejects claims the listing doesn't support, so titles stop lying about specs."),
    dict(tag="trust", tone="success", title="Money paths verified",
         body="Raw-body webhook signatures, insert-before-dispatch dedupe, and a retry sweeper with admin replay."),
]


@bp.get("/")
def index():
    from fbm import auth, core
    try:
        core.init_db()
        with core.db() as c:
            row = c.execute("SELECT id FROM admins LIMIT 1").fetchone()
            if not row:
                return redirect(url_for("pages.setup_wizard"))
    except Exception:
        pass
    return render_template("index.html", plans=PLANS, features=FEATURES,
                           year=time.gmtime().tm_year)


@bp.get("/onboarding")
def onboarding():
    return render_template("onboarding.html")


@bp.get("/design")
def design():
    return render_template("design.html")


@bp.get("/signup")
def signup():
    return render_template("auth/signup.html", plans=PLANS,
                           invite=request.args.get("ref") or request.args.get("invite"),
                           form={}, error=None)


@bp.post("/signup")
def signup_post():
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    if not email or "@" not in email:
        return render_template("auth/signup.html", plans=PLANS, invite=None,
                               form=request.form, error="That email doesn't look right."), 400
    if len(password) < 12:
        return render_template("auth/signup.html", plans=PLANS, invite=None,
                               form=request.form, error="Use at least 12 characters."), 400
    return redirect(url_for("pages.index"))


@bp.get("/login")
def login():
    return render_template("auth/login.html")


@bp.get("/auth/reset")
def auth_reset():
    return render_template("auth/reset.html")


@bp.get("/auth/login")
def auth_login():
    return render_template("auth/login.html")


@bp.get("/auth/totp")
def auth_totp():
    return render_template("auth/totp.html")


@bp.get("/billing")
def billing():
    return render_template(
        "billing.html",
        sub=dict(plan_name="Pro", state="active", price=99, renew_date="2026-11-27",
                 charge_date="2026-11-27", trial=False, days_left=0),
        credit=dict(balance=25, lifetime=75,
                    entries=[("2026-10-12", "referral", 25, "inv_1042")]),
        invoices=[],
        card=dict(brand="visa", last4="4242", exp="04/29", zip="38103"),
        usage=dict(listings=128, listings_cap=800, publishes=41,
                   publishes_cap=500, ai_msgs=220, ai_msgs_cap=1000),
        gmv=dict(total="1,842", orders=41),
        tax=dict(entity="Sole proprietor", state="TN", tin_masked="•••-••-8817", risk="low"),
    )


@bp.get("/billing/credits.csv")
def credits_csv():
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["date", "source", "amount", "applied_to"])
    return send_file(io.BytesIO(buf.getvalue().encode()), mimetype="text/csv",
                     as_attachment=True, download_name="credits.csv")


@bp.get("/refer")
def refer():
    code = "REF" + (g.get("tenant_id") or "demo")[:6]
    url = request.url_root.rstrip("/") + url_for("pages.signup") + f"?ref={code}"
    referrals = []
    stats = dict(sent=12, signed_up=4, conversion=33, earned=50, pending=2,
                 free_months=0.5, price=99, this_month=3, monthly_cap=10, next_tier=5)
    milestones = [dict(label=f"{n} conversions", reward=f"+${r} bonus",
                       done=stats["signed_up"] >= n,
                       current=stats["signed_up"] < n <= stats["signed_up"] + 2)
                  for n, r in ((1, 0), (3, 25), (5, 50), (10, 150))]
    try:
        import qrcode, io as _io
        import qrcode.image.svg as svg
        img = qrcode.make(url, image_factory=svg.SvgPathImage)
        buf = _io.BytesIO()
        img.save(buf)
        qr = buf.getvalue().decode()
    except Exception:
        qr = f'<svg viewBox="0 0 40 40" width="120" height="120"><text x="2" y="22" font-size="4">{url[:28]}</text></svg>'
    return render_template("refer.html", share=dict(url=url, code=code, qr_svg=qr),
                           stats=stats, referrals=referrals, milestones=milestones)


@bp.get("/vendors")
def vendors():
    from .vendors_data import CATEGORIES, VENDORS
    q = (request.args.get("q") or "").strip().lower()
    category = request.args.get("category") or ""
    sort = request.args.get("sort") or "rating"
    rows = [v for v in VENDORS
            if (not q or q in v["name"].lower() or q in v["summary"].lower())
            and (not category or v["category"] == category)]
    key = {"rating": lambda v: -v["rating"], "price": lambda v: v["price_rank"],
           "fb": lambda v: -v["fb_rank"]}.get(sort, lambda v: -v["rating"])
    rows.sort(key=key)
    return render_template("vendors.html", vendors=rows, q=q, category=category,
                           sort=sort, categories=CATEGORIES)


@bp.get("/help")
def help_page():
    q = (request.args.get("q") or "").strip()
    categories = [
        dict(key="setup", label="Setup", icon="\u2699", count=12),
        dict(key="publishing", label="Publishing", icon="\u2197", count=18),
        dict(key="orders", label="Orders", icon="[BOX]", count=14),
        dict(key="billing", label="Billing", icon="$", count=9),
    ]
    popular = [
        dict(title="Why are my listings under review?", slug="under-review", views=1240),
        dict(title="How renew + relist works", slug="renew-relist", views=980),
        dict(title="Tracking not matching orders", slug="tracking-match", views=860),
    ]
    changelog = [
        dict(title="Adaptive rate limiter", kind="feature", date="2026-10-20"),
        dict(title="Fixed 10% fee default", kind="fix", date="2026-10-18"),
    ]
    results = []
    if q:
        results = [dict(title="How renew + relist works", slug="renew-relist",
                        excerpt="Renew 5 times, then delete and relist.",
                        category="Publishing")]
    return render_template("help.html", q=q, results=results, categories=categories,
                           popular=popular, changelog=changelog)


@bp.get("/settings/account")
def settings_account():
    return render_template("settings/account.html",
        profile=dict(name="Memphis Reseller", email="mem***@example.com", phone="(901) 555-0123"),
        subscription=dict(plan_name="Pro", state="active", price=99, renew_date="2026-11-27",
                          payment_method="Visa •••• 4242"),
        credit=dict(balance=25, lifetime=75))


@bp.get("/settings/security")
def settings_security():
    return render_template("settings/security.html",
        profile=dict(state="healthy", connected=True),
        passkeys=[], totp_enabled=False,
        recovery_codes=["A1B2-C3D4", "E5F6-G7H8", "I9J0-K1L2", "M3N4-O5P6",
                      "Q7R8-S9T0", "U1V2-W3X4", "Y5Z6-A7B8", "C9D0-E1F2"])


@bp.get("/settings/integrations")
def integrations():
    return render_template(
        "settings/integrations.html",
        profile=dict(state="healthy", connected=True, label="memphis_reseller",
                     last_publish="4 min ago", selectors_ok=18, selectors_total=18,
                     rate_used=8, rate_cap=10),
        stripe=dict(connected=True, account="acct_1Nx\u2026", mode="live",
                    customer_id=os.getenv("STRIPE_CUSTOMER","n/a"), webhook_ok=os.getenv("STRIPE_WEBHOOK_OK","false").lower()=="true",
                    webhook_url=request.url_root.rstrip("/") + "/stripe/webhook"),
        intake=dict(connected=True,
                    address=os.getenv("IMAP_ALIAS","orders@example.com"),
                    imap_host="imap.gmail.com", last_poll="2 min ago",
                    parsed_today=7),
        suppliers=[
            dict(key="autods", name="AutoDS", role="primary", fill_rate="99.1", connected=True),
            dict(key="spocket", name="Spocket", role="backup", fill_rate="97.4", connected=True),
            dict(key="cj", name="CJ Dropshipping", role="tertiary", fill_rate="95.0", connected=False),
        ],
        ai=dict(tier="Pro", model="qwen3-1.7b", ctx=8192, ram_gb=8, window_min=10,
                byo_key_masked="sk-\u2026f92",
                available=[dict(key="gemma-3-1b", name="Gemma 3 1B", size="0.8 GB", ram=4),
                           dict(key="qwen3-1.7b", name="Qwen3 1.7B", size="1.2 GB", ram=6),
                           dict(key="llama-3.2-3b", name="Llama 3.2 3B", size="2.1 GB", ram=8)]),
        hooks=[],
        slack_hook="",
    )


@bp.get("/settings/notifications")
def settings_notifications():
    return render_template("settings/notifications.html")


@bp.get("/settings/data")
def settings_data():
    return render_template("settings/data.html")


@bp.get("/products")
def products():
    return render_template("products.html")


@bp.get("/orders")
def orders():
    return render_template("orders.html")


@bp.get("/reports")
def reports():
    return render_template("reports.html")


@bp.get("/bot")
def bot():
    return render_template("bot.html")


@bp.get("/admin/index")
def admin_index():
    return render_template("admin/index.html")


@bp.get("/admin/webhooks")
def admin_webhooks():
    return render_template("admin/webhooks.html")


@bp.get("/admin/scorecard")
def admin_scorecard():
    return render_template("admin/scorecard.html")


@bp.get("/admin/interventions")
def admin_interventions():
    return render_template("admin/interventions.html")


@bp.get("/admin/tenants/<tenant_id>")
def admin_tenant(tenant_id):
    return render_template(
        "admin/tenant.html",
        tenant=dict(id=tenant_id, name="Memphis reseller", email="mem***@example.com",
                    avatar=None, presence="online", joined="2026-09-14", region="Memphis, TN",
                    plan="Pro", state="active", mrr=99, tenure="43 days", days_left=0,
                    churn_score=82, churn_tone="success", listings_live=128,
                    listings_delta=12, orders_30d=41, gmv_30d="1,842",
                    last_login="2 hours ago", sessions=41, bot_msgs=220,
                    features_used=6, features_total=11,
                    activity=[3, 5, 4, 8, 7, 11, 10, 14, 12, 17],
                    stripe_customer=os.getenv("STRIPE_CUSTOMER","n/a"), hook_secret_age="live",
                    byo_key="set", passkeys=2, totp=True),
        hooks=[],
        interventions=[],
        modules=[
            dict(key="listing_engine", label="Listing engine", floor="Starter", enabled=True,
                 desc="Create, renew, relist.", usage="128 listings"),
            dict(key="competitor_pricing", label="Competitor re-pricing", floor="Pro", enabled=True,
                 desc="Scrape rivals and adjust within band.", usage="41 adjustments"),
            dict(key="supplier_failover", label="Supplier failover", floor="Pro", enabled=True,
                 desc="Primary to backup rerouting.", usage="3 reroutes"),
            dict(key="bot_actions", label="Bot can change settings", floor="Pro", enabled=True,
                 desc="Action registry from chat.", usage="12 actions"),
            dict(key="client_workspaces", label="Client workspaces", floor="Agency", enabled=False,
                 desc="Sub-accounts with own logins.", usage="\u2014"),
            dict(key="white_label", label="White-label reports", floor="Agency", enabled=False,
                 desc="Your logo on exports.", usage="\u2014"),
        ],
    )


# ============================================================================
# Setup Wizard Routes
# ============================================================================

@bp.get("/admin/login")
def admin_login():
    return render_template("auth/login.html", admin_mode=True, form={}, error=None)

@bp.post("/admin/login")
def admin_login_post():
    from fbm import auth
    uid = (request.form.get("username") or "").strip()
    pw = request.form.get("password") or ""
    if not uid or not pw:
        return render_template("auth/login.html", admin_mode=True,
                               form=request.form, error="Both fields required."), 400
    if auth.verify_admin(uid, pw):
        session["admin"] = uid
        return redirect(url_for("pages.admin_dashboard"))
    return render_template("auth/login.html", admin_mode=True,
                           form=request.form, error="Invalid admin credentials."), 401

@bp.get("/admin/dashboard")
def admin_dashboard():
    from fbm import auth
    if session.get("admin") != "admin" and not auth.verify_admin(session.get("admin"), ""):
        return redirect(url_for("pages.admin_login"))
    return render_template("admin/dashboard.html")

@bp.get("/trial")
def trial_view():
    return render_template("trial.html")

@bp.post("/trial")
def trial_post():
    from fbm import billing
    tenant_id = session.get("tenant_id") or "default"
    res = billing.start_trial(tenant_id)
    return jsonify(res)

@bp.get("/setup")
def setup_wizard():
    """First-run setup wizard page."""
    from fbm.setup import is_first_run
    from fbm import auth
    if not is_first_run():
        return redirect(url_for("pages.index"))
    auth.create_admin("admin")
    return render_template("setup/wizard.html")


@bp.post("/setup")
def setup_wizard_post():
    """Process setup wizard form submission."""
    from fbm.setup import run_headless, write_env, init_database, create_admin_tenant, store_secrets, mark_complete
    import json

    data = request.get_json(silent=True) or {}
    env = {}

    # Map form fields to env vars
    field_map = {
        "secret_key": "SECRET_KEY",
        "csrf_secret": "CSRF_SECRET",
        "fbm_profile": "FBM_PROFILE",
        "fbm_db": "FBM_DB",
        "fb_email": "FBM_LOGIN_EMAIL",
        "fb_password": "FBM_LOGIN_PASSWORD",
        "fb_totp": "FBM_TOTP_SECRET",
        "alert_webhook": "ALERT_WEBHOOK",
        "healthcheck_url": "HEALTHCHECK_URL",
        "openai_key": "OPENAI_API_KEY",
        "openai_base": "OPENAI_BASE_URL",
        "inbox_model": "INBOX_MODEL",
        "alias_domain": "ORDER_ALIAS_DOMAIN",
        "imap_host": "IMAP_HOST",
        "imap_user": "IMAP_USER",
        "imap_pass": "IMAP_PASS",
        "smtp_host": "SMTP_HOST",
        "smtp_user": "SMTP_USER",
        "smtp_pass": "SMTP_PASS",
        "spocket_key": "SPOCKET_API_KEY",
        "cj_key": "CJ_API_KEY",
        "zendrop_key": "ZENDROP_API_KEY",
        "dropcommerce_key": "DROPCOMMERCE_API_KEY",
        "stripe_key": "STRIPE_SECRET_KEY",
        "stripe_price_starter": "STRIPE_PRICE_STARTER",
        "stripe_price_pro": "STRIPE_PRICE_PRO",
        "stripe_price_agency": "STRIPE_PRICE_AGENCY",
        "stripe_webhook": "STRIPE_WEBHOOK_SECRET",
        "sample_budget": "SAMPLE_BUDGET_MONTH",
        "sample_max_cost": "SAMPLE_MAX_COST",
        "sample_address": "SAMPLE_ADDRESS",
        "sample_latency": "SAMPLE_LATENCY_LIMIT_DAYS",
        "dash_user": "DASH_USER",
        "dash_pass": "DASH_PASS",
        "backup_pass": "BACKUP_PASSWORD",
        "backup_keep": "BACKUP_KEEP",
        "accounts": "ACCOUNTS",
        "city": "CITY",
        "state": "STATE",
    }

    for form_key, env_key in field_map.items():
        val = data.get(form_key, "")
        if val:
            env[env_key] = val

    # Generate secrets if not provided
    if not env.get("SECRET_KEY"):
        import secrets as _secrets
        env["SECRET_KEY"] = _secrets.token_urlsafe(32)
    if not env.get("CSRF_SECRET"):
        import secrets as _secrets
        env["CSRF_SECRET"] = _secrets.token_urlsafe(32)

    try:
        write_env(env)
        init_database()
        create_admin_tenant(env)
        store_secrets(env)
        mark_complete()
        return jsonify({"status": "success", "message": "Setup complete"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.get("/setup/status")
def setup_status():
    """Return setup completion status."""
    from fbm.setup import is_first_run
    return jsonify({"setup_required": is_first_run()})


@bp.get("/daemon/status")
def daemon_status():
    """Return daemon service status."""
    from fbm.daemon import status
    return jsonify(status())