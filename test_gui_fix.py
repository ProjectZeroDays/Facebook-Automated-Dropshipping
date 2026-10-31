from app import app
client = app.test_client()
# Check index redirect
r = client.get("/", follow_redirects=False)
print("/ status:", r.status_code, "location:", r.headers.get("Location"))
# Check setup wizard
r2 = client.get("/setup")
print("/setup status:", r2.status_code)
# Check if admin exists in DB
from fbm import core, auth
core.init_db()
try:
    auth.create_admin("admin")
    print("admin created/exists")
except Exception as e:
    print("admin error:", e)
# Check rendered page for chat-widget
html = r2.data.decode("utf-8", errors="ignore")
print("chat-widget in HTML:", "id=\"chat-widget\"" in html)
print("legal-banner in HTML:", "id=\"legal-banner\"" in html)
print("minimize btn in HTML:", "Minimize chat" in html or "chat-restore" in html)
