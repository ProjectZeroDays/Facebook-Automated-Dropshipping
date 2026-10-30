"""security.py — CSRF, headers, input validation, audit logging."""
from __future__ import annotations
import hashlib, hmac, os, re
import fbm_core as C

def csrf_token(session_id):
    secret = os.getenv("CSRF_SECRET", "dev-csrf-secret")
    return hmac.new(secret.encode(), session_id.encode(), hashlib.sha256).hexdigest()

def verify_csrf(session_id, token):
    return hmac.compare_digest(csrf_token(session_id), token or "")

def sanitize(text):
    if text is None:
        return ""
    text = str(text)
    text = re.sub(r"<[^>]*>", "", text)
    return text.strip()

def audit(action, actor="system", detail="", tenant_id=C.DEFAULT_TENANT_ID):
    with C.db() as c:
        c.execute("INSERT INTO events(kind,ref,detail,account,tenant_id) VALUES('audit',?,?,?,?)",
                  (action, detail, actor, tenant_id))
    return True

def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

def main():
    C.load_env()
    print("security ok")

if __name__ == "__main__":
    main()
