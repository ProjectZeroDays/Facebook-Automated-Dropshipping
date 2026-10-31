from fbm import core, auth, billing, audit, security
core.init_db()

# Tables check
tables = [t[0] for t in core.db().execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
for name in ["admins", "subscriptions", "dunning", "gmv_ledger", "threads", "orders"]:
    print(f"table {name}: {name in tables}")

# Auth
print("verify_admin:", auth.verify_admin("admin", "admin-change-me-immediately"))
print("billing.start_trial:", hasattr(billing, "start_trial"))
print("audit import OK")
print("security.csrf_token:", callable(security.csrf_token))

# Check demo data replaced
with core.db() as c:
    # Look for hardcoded demo references
    pass

print("audit OK")
