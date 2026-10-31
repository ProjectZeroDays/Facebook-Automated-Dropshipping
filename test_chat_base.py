from app import app
client = app.test_client()
r = client.get("/")
html = r.data.decode("utf-8", errors="ignore")
print("index uses base:", "base.html" in html or "sidebar" in html)
print("chat-widget:", "id=\"chat-widget\"" in html)
print("legal-banner:", "id=\"legal-banner\"" in html)
print("menu btn:", "☰" in html)
# Force delete admin to test redirect
from fbm import core
with core.db() as c:
    c.execute("DELETE FROM admins")
r2 = client.get("/")
print("after admin delete / status:", r2.status_code, "loc:", r2.headers.get("Location"))
