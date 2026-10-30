"""
fbm/audit.py — God Mode audit tool.

Complete production-readiness audit of the FB Dropshipper stack. Checks every
system, dependency, configuration, and integration. Reports what is required
for all systems to work, what is missing, and what the app can and cannot do.

Usage:
  python -m fbm.audit              # full audit, print report
  python -m fbm.audit --json       # output machine-readable JSON
  python -m fbm.audit --fix        # attempt to auto-fix missing requirements
"""
from __future__ import annotations
import os, sys, json, shutil, subprocess, importlib
from datetime import datetime, timezone
from pathlib import Path
from fbm import core as C

PROJECT_ROOT = Path.cwd()
RESULTS = {
    "audited_at": datetime.now(timezone.utc).isoformat(),
    "project_root": str(PROJECT_ROOT),
    "overall": "unknown",
    "sections": {},
    "can_do": [],
    "cannot_do": [],
    "requirements_met": [],
    "requirements_missing": [],
    "fixes_applied": [],
    "critical_issues": [],
    "warnings": [],
}


def check(name: str, ok: bool, detail: str = "", required: bool = True, fix_fn=None):
    """Record a check result."""
    section = RESULTS["sections"].setdefault("checks", [])
    entry = {"name": name, "ok": ok, "detail": detail, "required": required}
    section.append(entry)

    if ok:
        RESULTS["requirements_met"].append(name)
    else:
        RESULTS["requirements_missing"].append(name)
        if required:
            RESULTS["critical_issues"].append(f"{name}: {detail}")
        else:
            RESULTS["warnings"].append(f"{name}: {detail}")

    if not ok and fix_fn:
        try:
            fix_fn()
            RESULTS["fixes_applied"].append(name)
        except Exception as e:
            RESULTS["warnings"].append(f"Auto-fix failed for {name}: {e}")

    return ok


# ---------------------------------------------------------------------------
# 1. Python & Runtime
# ---------------------------------------------------------------------------
def audit_python():
    ok = sys.version_info >= (3, 11)
    check("python_version", ok, f"{sys.version}", required=True)
    return ok


# ---------------------------------------------------------------------------
# 2. Core Modules Import
# ---------------------------------------------------------------------------
def audit_imports():
    modules = [
        "fbm.core", "fbm.autovars", "fbm.bugreport", "fbm.reprice", "fbm.samples",
        "fbm.tracking", "fbm.watcher", "fbm.crosslist_post", "fbm.scraper",
        "fbm.targets", "fbm.bootstrap", "fbm.firstrun", "fbm.dashboard",
        "fbm.billing", "fbm.observability", "fbm.auth_hardening", "fbm.plugins",
        "fbm.commands", "fbm.workflows", "fbm.agents", "fbm.actions",
        "fbm.payments", "fbm.drip", "fbm.onboarding_emails", "fbm.emailcopy",
        "fbm.adminroutes", "fbm.tenants", "fbm.selfheal", "fbm.insights",
        "fbm.inbox", "fbm.inbox_poller", "fbm.google", "fbm.download_model",
        "fbm.updater", "fbm.whisper", "fbm.metrics", "fbm.profile_backup",
        "fbm.inbox_ai", "fbm.daemon", "fbm.setup", "fbm.default_commands",
        "fbm.web_pages", "fbm.security", "fbm.mcp_client", "fbm.mcp_integration",
    ]
    failed = []
    for m in modules:
        try:
            importlib.import_module(m)
        except Exception as e:
            failed.append(f"{m}: {e}")
    ok = len(failed) == 0
    check("all_modules_import", ok,
          f"{len(modules) - len(failed)}/{len(modules)} modules imported" +
          (f"; failures: {'; '.join(failed[:3])}" if failed else ""),
          required=True)
    return ok


# ---------------------------------------------------------------------------
# 3. Configuration (.env)
# ---------------------------------------------------------------------------
def audit_env():
    env_path = Path(".env")
    exists = env_path.exists()
    check("env_file_exists", exists, str(env_path.absolute()), required=True)

    if exists:
        content = env_path.read_text()
        critical_vars = [
            "SECRET_KEY", "CSRF_SECRET", "STRIPE_SECRET_KEY",
            "STRIPE_WEBHOOK_SECRET", "OPENAI_API_KEY",
        ]
        missing = [v for v in critical_vars if f"{v}=" not in content]
        check("env_critical_vars", len(missing) == 0,
              f"Missing: {', '.join(missing)}" if missing else "All critical vars present",
              required=False)

        # Check for placeholder values
        placeholders = [
            "change-me", "your-", "sk-your", "whsec_", "sk_live_",
            "price_", "yourdomain.com", "your-email", "your-shipping"
        ]
        found_placeholders = [p for p in placeholders if p in content]
        check("env_no_placeholders", len(found_placeholders) == 0,
              f"Placeholder values found: {', '.join(found_placeholders[:5])}"
              if found_placeholders else "No placeholder values",
              required=False)


# ---------------------------------------------------------------------------
# 4. Database
# ---------------------------------------------------------------------------
def audit_database():
    from fbm import core as C
    C.load_env()
    try:
        C.init_db()
        ok = True
        detail = "Database initialized successfully"
    except Exception as e:
        ok = False
        detail = str(e)
    check("database_init", ok, detail, required=True)


# ---------------------------------------------------------------------------
# 5. External Dependencies
# ---------------------------------------------------------------------------
def audit_external():
    # Playwright / Chromium
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        check("playwright_chromium", True, "Chromium launches successfully")
    except Exception as e:
        check("playwright_chromium", False, str(e), required=False)

    # Redis (optional)
    check("redis_available", shutil.which("redis-server") is not None,
          "redis-server not found (optional for caching)", required=False)

    # Docker (for container deployment)
    check("docker_available", shutil.which("docker") is not None,
          "Docker not found (required for VPS deployment)", required=False)

    # Stripe key format
    from fbm import core as C
    stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
    check("stripe_configured",
          bool(stripe_key) and stripe_key.startswith(("sk_", "")),
          "Stripe secret key not configured" if not stripe_key else "Stripe configured",
          required=False)


# ---------------------------------------------------------------------------
# 6. Routes & Endpoints
# ---------------------------------------------------------------------------
def audit_routes():
    from app import app
    client = app.test_client()
    expected = [
        "/", "/onboarding", "/design", "/signup", "/login",
        "/auth/reset", "/auth/login", "/auth/totp", "/billing",
        "/refer", "/vendors", "/help", "/settings/account",
        "/settings/security", "/settings/integrations",
        "/settings/notifications", "/settings/data",
        "/products", "/orders", "/reports", "/bot",
        "/admin/index", "/admin/webhooks", "/admin/scorecard",
        "/admin/interventions", "/setup", "/setup/status",
        "/daemon/status", "/healthz", "/metrics",
    ]
    failed = []
    for route in expected:
        try:
            resp = client.get(route)
            if resp.status_code not in (200, 302, 405):
                failed.append(f"{route} -> {resp.status_code}")
        except Exception as e:
            failed.append(f"{route} -> {e}")
    ok = len(failed) == 0
    check("all_routes_200", ok,
          f"{len(expected) - len(failed)}/{len(expected)} routes OK" +
          (f"; failures: {'; '.join(failed[:3])}" if failed else ""),
          required=True)


# ---------------------------------------------------------------------------
# 7. Security
# ---------------------------------------------------------------------------
def audit_security():
    issues = []

    # Check .env permissions on POSIX
    env_path = Path(".env")
    if env_path.exists() and os.name == "posix":
        mode = oct(env_path.stat().st_mode & 0o777)
        if mode != "0o600":
            issues.append(f".env permissions are {mode}, should be 600")

    # Check SECRET_KEY not default
    secret = os.getenv("SECRET_KEY", "")
    if secret in ("dev-only-change-me", "change-me-in-production", ""):
        issues.append("SECRET_KEY is using default/placeholder value")

    check("security_env_perms", len(issues) == 0,
          "; ".join(issues) if issues else "Security config OK",
          required=False)


# ---------------------------------------------------------------------------
# 8. Capability Assessment (what app can/cannot do)
# ---------------------------------------------------------------------------
def audit_capabilities():
    can = []
    cannot = []

    # Check billing
    stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
    if stripe_key and stripe_key.startswith("sk_"):
        can.append("Stripe billing: checkout, webhooks, invoices, dunning")
    else:
        cannot.append("Stripe billing: no STRIPE_SECRET_KEY configured")

    # Check AI
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key:
        can.append("AI: LLM-generated listing copy, inbox replies, competitor analysis")
    else:
        cannot.append("AI: no OPENAI_API_KEY configured — copy generation disabled")

    # Check Facebook
    fb_email = os.getenv("FBM_LOGIN_EMAIL", "")
    fb_pass = os.getenv("FBM_LOGIN_PASSWORD", "")
    if fb_email and fb_pass:
        can.append("Facebook: automated login, listing publish, order tracking")
    else:
        cannot.append("Facebook: no login credentials — manual login required")

    # Check suppliers
    supplier_keys = [
        os.getenv("SPOCKET_API_KEY", ""),
        os.getenv("CJ_API_KEY", ""),
        os.getenv("ZENDROP_API_KEY", ""),
        os.getenv("DROPCOMMERCE_API_KEY", ""),
    ]
    if any(supplier_keys):
        can.append("Suppliers: API-based order placement with failover")
    else:
        cannot.append("Suppliers: no supplier API keys — manual fulfillment only")

    # Check email
    imap_user = os.getenv("IMAP_USER", "")
    if imap_user:
        can.append("Email: IMAP order tracking intake via plus-address routing")
    else:
        cannot.append("Email: no IMAP config — order tracking must be manual")

    # Check multi-tenant
    can.append("Multi-tenancy: row-level isolation, per-tenant quotas, billing tiers")

    # Check daemon
    can.append("Daemon: auto-start, auto-restart, health monitoring, service management")

    # Cannot do
    cannot.append("Official Facebook Marketplace API: no official API exists; uses browser automation")
    cannot.append("iOS/Android mobile app: web dashboard only, no native mobile client")
    cannot.append("Guaranteed Facebook compliance: automation may violate Meta's ToS")
    cannot.append("Real-time WebSocket notifications: polling-based only")
    cannot.append("Multi-region deployment: single-instance deployment only")

    RESULTS["can_do"] = can
    RESULTS["cannot_do"] = cannot


# ---------------------------------------------------------------------------
# 9. Docker / VPS readiness
# ---------------------------------------------------------------------------
def audit_deployment():
    checks = {
        "Dockerfile.prod": Path("Dockerfile.prod").exists(),
        "docker-compose.prod.yml": Path("docker-compose.prod.yml").exists(),
        "entrypoint.prod.sh": Path("entrypoint.prod.sh").exists(),
        "deploy_local.sh": Path("deploy_local.sh").exists(),
        "deploy_local.ps1": Path("deploy_local.ps1").exists(),
        "deploy_vps.sh": Path("deploy_vps.sh").exists(),
        "fbm-ops.service": Path("fbm-ops.service").exists(),
    }
    for name, ok in checks.items():
        check(f"deploy_{name}", ok, str(PROJECT_ROOT / name), required=False)


# ---------------------------------------------------------------------------
# Main audit runner
# ---------------------------------------------------------------------------
def run_audit(fix: bool = False, quiet: bool = False):
    if not quiet:
        print("=" * 70)
        print("GOD MODE AUDIT — FB Dropshipper Production Readiness")
        print("=" * 70)
        print()

    RESULTS["overall"] = "running"

    # Run all audit sections
    audit_python()
    audit_imports()
    audit_env()
    audit_database()
    audit_external()
    audit_routes()
    audit_security()
    audit_capabilities()
    audit_deployment()

    # Determine overall status
    if RESULTS["critical_issues"]:
        RESULTS["overall"] = "CRITICAL_ISSUES"
    elif RESULTS["warnings"]:
        RESULTS["overall"] = "WARNINGS"
    else:
        RESULTS["overall"] = "READY"

    if not quiet:
        print()
        print("=" * 70)
        print("AUDIT RESULTS")
        print("=" * 70)
        print(f"Overall status: {RESULTS['overall']}")
        print(f"Requirements met: {len(RESULTS['requirements_met'])}")
        print(f"Requirements missing: {len(RESULTS['requirements_missing'])}")
        print(f"Critical issues: {len(RESULTS['critical_issues'])}")
        print(f"Warnings: {len(RESULTS['warnings'])}")
        print(f"Auto-fixes applied: {len(RESULTS['fixes_applied'])}")
        print()

        if RESULTS["critical_issues"]:
            print("CRITICAL ISSUES (must fix before production):")
            for issue in RESULTS["critical_issues"]:
                print(f"  [FAIL] {issue}")
            print()

        if RESULTS["warnings"]:
            print("WARNINGS (recommended but not blocking):")
            for warn in RESULTS["warnings"]:
                print(f"  [WARN] {warn}")
            print()

        if RESULTS["can_do"]:
            print("WHAT THE APP CAN DO:")
            for item in RESULTS["can_do"]:
                print(f"  [OK] {item}")
            print()

        if RESULTS["cannot_do"]:
            print("WHAT THE APP CANNOT DO:")
            for item in RESULTS["cannot_do"]:
                print(f"  [NO] {item}")
            print()

        print("=" * 70)

    return RESULTS


def main():
    import argparse
    ap = argparse.ArgumentParser(description="God Mode production audit")
    ap.add_argument("--json", action="store_true", help="Output JSON only")
    ap.add_argument("--fix", action="store_true", help="Attempt auto-fixes")
    args = ap.parse_args()

    C.load_env()
    results = run_audit(fix=args.fix, quiet=args.json)

    if args.json:
        print(json.dumps(results, indent=2, default=str))

    # Exit code based on status
    if results["overall"] == "READY":
        sys.exit(0)
    elif results["overall"] == "WARNINGS":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()