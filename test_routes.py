import os
os.chdir(r"C:\Projects\FB Dropshipper")
from app import app
client = app.test_client()

get_routes = [
    "/", "/onboarding", "/design", "/signup", "/login",
    "/auth/reset", "/auth/login", "/auth/totp", "/billing",
    "/refer", "/vendors", "/help", "/settings/account",
    "/settings/security", "/settings/integrations",
    "/settings/notifications", "/settings/data",
    "/products", "/orders", "/reports", "/bot",
    "/admin/index", "/admin/webhooks", "/admin/scorecard",
    "/admin/interventions",
]

print("=== GET Routes ===")
all_ok = True
for route in get_routes:
    resp = client.get(route)
    ok = resp.status_code == 200
    if not ok:
        all_ok = False
    print(f"  GET {route:35s} -> {resp.status_code} {'OK' if ok else 'FAIL'}")

print()
print("=== POST Routes (expect 200 or 403 CSRF) ===")
post_routes = ["/chat/send", "/command", "/agent", "/workflow"]
for route in post_routes:
    resp = client.post(route, data={})
    ok = resp.status_code in (200, 403)
    print(f"  POST {route:35s} -> {resp.status_code} {'OK' if ok else 'FAIL'}")

print()
print("ALL GET ROUTES 200:", all_ok)