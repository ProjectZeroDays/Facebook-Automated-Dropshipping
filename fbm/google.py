"""google.py — Gmail, Calendar, Voice integration stubs.

Provides OAuth-scoped helpers for Gmail (tracking intake), Calendar
(delivery reminders), and Voice (SMS alerts). Requires google-auth /
google-api-python-client and credentials JSON.
"""
from __future__ import annotations
import os
import fbm_core as C

SCOPES = {
    "gmail":  ["https://www.googleapis.com/auth/gmail.readonly"],
    "calendar": ["https://www.googleapis.com/auth/calendar"],
    "voice":  ["https://www.googleapis.com/auth/voice"],
}

def service(name: str):
    """Return an authenticated Google service object, or None if not configured."""
    creds_file = os.getenv("GOOGLE_CREDS", "credentials.json")
    if not os.path.exists(creds_file):
        C.notify(f"google: {creds_file} not found — {name} unavailable", "warn")
        return None
    try:
        from google.oauth2.service_account import Credentials
        creds = Credentials.from_service_account_file(creds_file, scopes=SCOPES.get(name, []))
        return creds
    except ImportError:
        C.notify("google: google-auth not installed", "warn")
        return None
    except Exception as e:
        C.notify(f"google: {name} init failed: {e}", "error")
        return None

def main():
    C.load_env()
    for name in SCOPES:
        svc = service(name)
        print(f"[google] {name}: {'ok' if svc else 'not configured'}")
    print("google ok")

if __name__ == "__main__":
    main()
