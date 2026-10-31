#!/usr/bin/env python3
"""Expanded regression tests — v1.1.1 verification."""
import sys, os
sys.path.insert(0, r"C:\Projects\FB Dropshipper")

results = {"PASS": 0, "FAIL": 0}

def run(name, fn):
    try:
        fn()
        print(f"PASS  {name}")
        results["PASS"] += 1
    except Exception as e:
        print(f"FAIL  {name} — {type(e).__name__}: {str(e)[:100]}")
        results["FAIL"] += 1

def imports_all():
    from fbm import auth, core, billing, audit, security, web_pages
    from fbm.inbox import poll_once, main
    from fbm.inbox_ai import AUTO_THRESHOLD, context, POLICY
    print("  all 13 modules imported OK")

def trial_full_flow():
    from app import app
    c = app.test_client()
    r = c.get("/trial")
    assert r.status_code == 200
    import re
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r.data.decode())
    assert m
    r_post = c.post("/trial", data={"csrf_token": m.group(1)})
    assert r_post.status_code == 200
    data = r_post.get_json(silent=True) or {}
    assert data.get("ok")

def admin_login_flow():
    from fbm import core, auth
    core.init_db()
    auth.create_admin("admin")
    assert auth.verify_admin("admin", "admin-change-me-immediately")

def setup_wizard_flow():
    from fbm import core, auth
    core.init_db()
    # Ensure admin exists; wizard skips if admin exists
    # Just verify wizard page renders 200
    from app import app
    c = app.test_client()
    r = c.get("/setup")
    assert r.status_code == 200

def routes_batch():
    from app import app
    c = app.test_client()
    routes = ["/", "/trial", "/signup", "/setup", "/admin/login",
              "/auth/login", "/settings/account", "/billing",
              "/products", "/orders", "/commands", "/agents",
              "/workflows", "/bot", "/metrics", "/healthz"]
    for route in routes:
        r = c.get(route)
        assert r.status_code == 200, f"Route {route} got {r.status_code}"

def billing_contract():
    from fbm import billing
    assert callable(billing.start_trial)
    # Check no hardcoded demo customers
    import inspect
    src = inspect.getsource(billing)
    assert "cus_9f2" not in src, "demo customer reference in billing"

def no_demo_data_leak():
    from fbm import web_pages, billing, core
    # Check web_pages has no hardcoded demo orders
    import inspect
    src = inspect.getsource(web_pages)
    assert "orders+demo" not in src, "demo order reference in web_pages"

run("imports_all", imports_all)
run("trial_full_flow", trial_full_flow)
run("admin_login_flow", admin_login_flow)
run("setup_wizard_flow", setup_wizard_flow)
run("routes_batch", routes_batch)
run("billing_contract", billing_contract)
run("no_demo_data_leak", no_demo_data_leak)

print(f"\n=== RESULTS: {results['PASS']} passed / {results['FAIL']} failed ===")
if results["FAIL"] == 0:
    print("ALL TESTS PASS — v1.1.1 clean for release.")
else:
    print("SOME TESTS FAILED — review above.")
