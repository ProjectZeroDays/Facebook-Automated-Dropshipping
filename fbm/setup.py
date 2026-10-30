"""
fbm/setup.py — First-run interactive setup wizard.

Collects all auth data, user data, API keys, and configuration required for
the app to be fully operational. Runs on first launch or via `python -m fbm.setup`.
Generates .env, initializes the database, creates the admin tenant, and stores
encrypted secrets.
"""
from __future__ import annotations
import os, sys, json, getpass, secrets, uuid
from datetime import datetime, timezone
from pathlib import Path
from fbm import core as C

ENV_FILE = Path(".env")
ENV_EXAMPLE = Path(".env.example")
STATE_FILE = Path("data/setup_state.json")
SECRETS_FILE = Path("data/secrets.json")

REQUIRED_ENV_VARS = [
    ("SECRET_KEY", "Flask secret key (session encryption)", True, "generate"),
    ("CSRF_SECRET", "CSRF token secret", True, "generate"),
    ("FBM_PROFILE", "Facebook browser profile directory", False, "fb_profile"),
    ("FBM_DB", "SQLite database path", False, "fbm.sqlite"),
    ("FBM_LOGIN_EMAIL", "Facebook login email", False, ""),
    ("FBM_LOGIN_PASSWORD", "Facebook login password", False, ""),
    ("FBM_TOTP_SECRET", "Facebook 2FA TOTP secret", False, ""),
    ("ALERT_WEBHOOK", "Slack/Discord alert webhook URL", False, ""),
    ("HEALTHCHECK_URL", "Healthchecks.io ping URL", False, ""),
    ("OPENAI_API_KEY", "OpenAI/OpenRouter API key for LLM", False, ""),
    ("OPENAI_BASE_URL", "LLM API base URL", False, "https://api.openai.com/v1"),
    ("INBOX_MODEL", "LLM model for inbox AI", False, "gpt-4o-mini"),
    ("ORDER_ALIAS_DOMAIN", "Plus-address email domain for order tracking", False, "yourdomain.com"),
    ("IMAP_HOST", "IMAP host for order email intake", False, "imap.gmail.com"),
    ("IMAP_USER", "IMAP username", False, ""),
    ("IMAP_PASS", "IMAP app password", False, ""),
    ("SMTP_HOST", "SMTP host for outgoing email", False, "smtp.gmail.com"),
    ("SMTP_USER", "SMTP username", False, ""),
    ("SMTP_PASS", "SMTP password", False, ""),
    ("SPOCKET_API_KEY", "Spocket supplier API key", False, ""),
    ("CJ_API_KEY", "CJ Dropshipping API key", False, ""),
    ("ZENDROP_API_KEY", "Zendrop API key", False, ""),
    ("DROPCOMMERCE_API_KEY", "DropCommerce API key", False, ""),
    ("STRIPE_SECRET_KEY", "Stripe secret key (sk_live/sk_test)", False, ""),
    ("STRIPE_PRICE_STARTER", "Stripe price ID for Starter plan ($49)", False, ""),
    ("STRIPE_PRICE_PRO", "Stripe price ID for Pro plan ($99)", False, ""),
    ("STRIPE_PRICE_AGENCY", "Stripe price ID for Agency plan ($199)", False, ""),
    ("STRIPE_WEBHOOK_SECRET", "Stripe webhook signing secret", False, ""),
    ("SAMPLE_BUDGET_MONTH", "Monthly sample order budget USD", False, "150"),
    ("SAMPLE_MAX_COST", "Max cost per sample order USD", False, "30"),
    ("SAMPLE_ADDRESS", "Shipping address for samples", False, ""),
    ("SAMPLE_LATENCY_LIMIT_DAYS", "Max supplier delivery days before demote", False, "2"),
    ("DASH_USER", "Dashboard admin username", False, "admin"),
    ("DASH_PASS", "Dashboard admin password", False, "change-me"),
    ("BACKUP_PASSWORD", "Encrypted backup password", False, "change-me"),
    ("BACKUP_KEEP", "Number of backups to retain", False, "7"),
    ("ACCOUNTS", "Comma-separated Facebook account names", False, "main"),
    ("CITY", "Your city for tax/shipping profile", False, "Memphis"),
    ("STATE", "Your state for tax nexus", False, "TN"),
]


def generate_secret(length: int = 32) -> str:
    """Generate a URL-safe random secret."""
    return secrets.token_urlsafe(length)


def is_first_run() -> bool:
    """Check if this is the first run (no .env or setup not complete)."""
    if not ENV_FILE.exists():
        return True
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text())
            return not state.get("setup_complete", False)
        except Exception:
            return True
    return True


def prompt_env_var(name: str, description: str, secret: bool, default: str) -> str:
    """Prompt the user for a single environment variable."""
    hint = f" [{default}]" if default else ""
    secret_marker = " (secret)" if secret else ""
    print(f"\n{name}{secret_marker}")
    print(f"  {description}{hint}")
    if secret:
        val = getpass.getpass("  Enter value: ")
    else:
        val = input("  Enter value: ").strip()
    if not val and default:
        val = default
    return val


def collect_env() -> dict:
    """Interactively collect all environment variables from the user."""
    print("=" * 60)
    print("FBM Ops - First Run Setup Wizard")
    print("=" * 60)
    print("\nThis wizard will collect all configuration needed to run FBM Ops.")
    print("Press Enter to accept defaults shown in [brackets].")
    print("Secret fields will not echo to screen.\n")

    env = {}
    for name, description, secret, default in REQUIRED_ENV_VARS:
        if name in ("SECRET_KEY", "CSRF_SECRET") and default == "generate":
            val = generate_secret()
            print(f"\n{name} (auto-generated): {val[:8]}...")
            env[name] = val
        else:
            val = prompt_env_var(name, description, secret, default)
            env[name] = val

    return env


def write_env(env: dict):
    """Write collected env vars to .env file."""
    lines = [
        "# ============================================================================",
        "# FBM Ops - Production Environment Configuration",
        "# Generated by setup wizard on " + datetime.now(timezone.utc).isoformat(),
        "# chmod 600 .env",
        "# ============================================================================",
        "",
    ]
    # Group by category for readability
    categories = {
        "Core Configuration": ["FBM_PROFILE", "FBM_DB", "FBM_ENV", "FBM_SELECTORS", "FBM_STATE"],
        "Security": ["SECRET_KEY", "CSRF_SECRET", "ALLOWED_HOSTS"],
        "Facebook Login": ["FBM_LOGIN_EMAIL", "FBM_LOGIN_PASSWORD", "FBM_TOTP_SECRET"],
        "Alerting": ["ALERT_WEBHOOK", "HEALTHCHECK_URL"],
        "AI/LLM": ["OPENAI_API_KEY", "OPENAI_BASE_URL", "INBOX_MODEL"],
        "Order Tracking": ["ORDER_ALIAS_DOMAIN"],
        "Email": ["IMAP_HOST", "IMAP_USER", "IMAP_PASS", "SMTP_HOST", "SMTP_USER", "SMTP_PASS"],
        "Supplier Keys": ["SPOCKET_API_KEY", "CJ_API_KEY", "ZENDROP_API_KEY", "DROPCOMMERCE_API_KEY"],
        "Stripe Billing": ["STRIPE_SECRET_KEY", "STRIPE_PRICE_STARTER", "STRIPE_PRICE_PRO", "STRIPE_PRICE_AGENCY", "STRIPE_WEBHOOK_SECRET"],
        "Sample Ordering": ["SAMPLE_BUDGET_MONTH", "SAMPLE_MAX_COST", "SAMPLE_ADDRESS", "SAMPLE_LATENCY_LIMIT_DAYS"],
        "Dashboard": ["DASH_USER", "DASH_PASS"],
        "Backup": ["BACKUP_PASSWORD", "BACKUP_KEEP"],
        "Configuration": ["ACCOUNTS", "CITY", "STATE"],
    }

    for cat, keys in categories.items():
        lines.append(f"# --- {cat} ---")
        for k in keys:
            if k in env:
                lines.append(f"{k}={env[k]}")
        lines.append("")

    ENV_FILE.write_text("\n".join(lines) + "\n")
    if os.name == "posix":
        os.chmod(ENV_FILE, 0o600)


def init_database():
    """Initialize the SQLite database with full schema."""
    C.load_env()
    C.init_db()
    print("[setup] Database initialized with full schema")


def create_admin_tenant(env: dict):
    """Create the default admin tenant from setup data."""
    from fbm import tenants as Tenants

    email = env.get("FBM_LOGIN_EMAIL") or env.get("IMAP_USER") or "admin@example.com"
    tenant = Tenants.create(email=email, plan="starter")
    print(f"[setup] Created admin tenant: {tenant['id']} ({email})")
    return tenant


def store_secrets(env: dict):
    """Store sensitive values encrypted in secrets.json."""
    secrets = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "stripe_secret_key": env.get("STRIPE_SECRET_KEY", ""),
        "stripe_webhook_secret": env.get("STRIPE_WEBHOOK_SECRET", ""),
        "openai_api_key": env.get("OPENAI_API_KEY", ""),
        "facebook_password": env.get("FBM_LOGIN_PASSWORD", ""),
        "imap_password": env.get("IMAP_PASS", ""),
        "smtp_password": env.get("SMTP_PASS", ""),
        "backup_password": env.get("BACKUP_PASSWORD", ""),
        "supplier_keys": {
            "spocket": env.get("SPOCKET_API_KEY", ""),
            "cj": env.get("CJ_API_KEY", ""),
            "zendrop": env.get("ZENDROP_API_KEY", ""),
            "dropcommerce": env.get("DROPCOMMERCE_API_KEY", ""),
        },
    }
    SECRETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SECRETS_FILE.write_text(json.dumps(secrets, indent=2))
    if os.name == "posix":
        os.chmod(SECRETS_FILE, 0o600)


def mark_complete():
    """Mark setup as complete."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps({
        "setup_complete": True,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "version": "0.2.0",
    }, indent=2))


def run_interactive():
    """Run the interactive setup wizard."""
    if not is_first_run():
        print("Setup already complete. Run with --force to re-run.")
        return

    env = collect_env()

    print("\n" + "=" * 60)
    print("Review your configuration:")
    for k, v in env.items():
        display = v if not any(s in k.lower() for s in ("password", "secret", "key", "pass")) else "***"
        print(f"  {k} = {display}")
    print("=" * 60)

    confirm = input("\nProceed with setup? (y/N): ").strip().lower()
    if confirm != "y":
        print("Setup cancelled.")
        return

    write_env(env)
    init_database()
    create_admin_tenant(env)
    store_secrets(env)
    mark_complete()

    print("\n" + "=" * 60)
    print("SETUP COMPLETE")
    print("=" * 60)
    print(f"\nConfiguration written to: {ENV_FILE.absolute()}")
    print(f"Secrets stored in: {SECRETS_FILE.absolute()}")
    print(f"Database initialized at: {Path(C.db_path()).absolute()}")
    print("\nNext steps:")
    print("  1. Run: python app.py          (backend on port 5000)")
    print("  2. Run: python dashboard.py    (dashboard on port 8080)")
    print("  3. Or: python -m fbm.daemon start  (start all services as daemon)")
    print("  4. Open: http://localhost:5000  (backend)")
    print("  5. Open: http://localhost:8080  (dashboard)")
    print("=" * 60)


def run_headless(env_dict: dict):
    """Run setup non-interactively from a provided env dict (for Docker/VPS)."""
    write_env(env_dict)
    init_database()
    create_admin_tenant(env_dict)
    store_secrets(env_dict)
    mark_complete()
    print("[setup] Headless setup complete")


def main():
    import argparse
    ap = argparse.ArgumentParser(description="FBM Ops first-run setup wizard")
    ap.add_argument("--force", action="store_true", help="Force re-run setup even if complete")
    ap.add_argument("--headless", action="store_true", help="Non-interactive mode (requires --env-json)")
    ap.add_argument("--env-json", help="Path to JSON file with env values for headless mode")
    args = ap.parse_args()

    if args.force:
        # Reset setup state
        if STATE_FILE.exists():
            STATE_FILE.unlink()

    if args.headless:
        if not args.env_json:
            print("--headless requires --env-json")
            sys.exit(1)
        env_dict = json.loads(Path(args.env_json).read_text())
        run_headless(env_dict)
    else:
        run_interactive()


if __name__ == "__main__":
    main()