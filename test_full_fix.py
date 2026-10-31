from app import app
from fbm import metrics as Metrics

c = app.test_client()
print("=== Health Check ===")
r = c.get('/healthz')
print("/healthz status:", r.status_code, "body:", r.data.decode('utf-8', errors='ignore')[:200])

print("\n=== Metrics ===")
r = c.get('/metrics')
print("/metrics status:", r.status_code)

print("\n=== 25 GET Routes Check ===")
routes = ['/', '/admin/dashboard', '/admin/login', '/admin/index', '/auth/login', '/signup', 
          '/trial', '/setup', '/setting/account', '/settings/account', '/healthz', '/metrics',
          '/billing', '/products', '/orders', '/refer', '/vendors', '/reports', 
          '/help', '/design', '/onboarding', '/chat/history', '/chat/search',
          '/bot', '/commands']

success = 0
fail = 0
for route in routes:
    r = c.get(route)
    if r.status_code == 200:
        success += 1
    else:
        fail += 1
    print(f"  {route}: {r.status_code}")

print(f"\nResult: {success} passed / {fail} failed out of {len(routes)} routes")

print("\n=== Admin Route Test ===")
from fbm import core, auth
core.init_db()
auth.create_admin("admin")
r = c.get('/')
html = r.data.decode('utf-8', errors='ignore')
print("/ route redirects to /setup when no admin:", 'setup' in html.lower() or 'admin' in html.lower())
# With admin
r = c.get('/')
print("/ route status after admin:", r.status_code)