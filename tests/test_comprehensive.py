#!/usr/bin/env python3
"""Comprehensive regression test for FB Dropshipper v1.1.1."""
from __future__ import annotations
import sys, traceback

def test(name, fn):
    try:
        fn()
        print("PASS  ", name)
        return True
    except Exception as e:
        print("FAIL  ", name, "-", type(e).__name__, "-", str(e)[:120])
        traceback.print_exc()
        return False

def imports():
    from fbm import auth, core, billing, web_pages, chatbot, security
    from fbm.inbox_ai import context, AUTO_THRESHOLD
    # Verify auth functions
    core.init_db()
    auth.create_admin("testadmin")
    assert auth.verify_admin("testadmin", "admin-change-me-immediately")

def trial_route():
    from app import app
    c = app.test_client()
    # GET
    r = c.get("/trial")
    assert r.status_code == 200
    html = r.data.decode("utf-8", errors="ignore")
    assert "csrf_token" in html
    assert "Start Trial" in html or "Trial" in html
    # POST with CSRF
    import re
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    assert m, "CSRF token missing in trial.html"
    r = c.post("/trial", data={"csrf_token": m.group(1)})
    assert r.status_code == 200, f"POST /trial got {r.status_code}"
    data = r.get_json(silent=True) or {}
    assert data.get("ok") is True, f"Unexpected POST response: {data}"

def admin_first():
    from fbm import auth, core
    core.init_db()
    # Should make admin if not exists
    res = auth.create_admin("admin")
    # Verify
    assert auth.verify_admin("admin", "admin-change-me-immediately")

def routes_get():
    from app import app
    c = app.test_client()
    ok = 0; fail = 0
    routes = ["/", "/trial", "/signup", "/setup", "/admin/login",
              "/auth/login", "/settings/account", "/healthz", "/metrics",
              "/billing", "/products", "/orders", "/bot"]
    for r in routes:
        status = c.get(r).status_code
        if status == 200:
            ok += 1
        else:
            fail += 1
            print("  route", r, "=", status)
    assert fail == 0, f"Failed routes: {fail}"

if __name__ == "__main__":
    passed = sum(TESTS := [
        test("imports", imports),
        test("trial_route", trial_route),
        test("admin_first", admin_first),
        test("routes_get", routes_get),
    ])
    print(f"\nRESULT: {passed}/{len(TESTS)} passed")
    sys.exit(0 if passed == len(TESTS) else 1)
