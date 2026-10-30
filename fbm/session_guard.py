"""
fbm/session_guard.py — keep the FB session alive with no human.

Detects the login wall, auto-fills credentials, answers TOTP 2FA from the
shared secret, and only alerts (with a screenshot) if it truly can't get in.

Env: FBM_LOGIN_EMAIL, FBM_LOGIN_PASSWORD, FBM_TOTP_SECRET (optional)
"""
from __future__ import annotations
import os, sys
from fbm import core as C

LOGIN_HINTS = ("Log in to Facebook", "Log into Facebook", "email")


def logged_out(page):
    return page.locator("input[name='email']").count() > 0 or \
           any(h in (page.inner_text("body")[:2000] if page.locator("body").count() else "")
               for h in LOGIN_HINTS)


def _totp():
    secret = os.getenv("FBM_TOTP_SECRET")
    if not secret:
        return None
    try:
        import pyotp
        return pyotp.TOTP(secret).now()
    except Exception:
        return None


def auto_login(page):
    email, pw = os.getenv("FBM_LOGIN_EMAIL"), os.getenv("FBM_LOGIN_PASSWORD")
    if not (email and pw):
        return False
    try:
        page.fill("input[name='email']", email); C.pause(0.4, 0.8)
        page.fill("input[name='pass']", pw); C.pause(0.4, 0.8)
        page.get_by_role("button", name="Log in").first.click(); C.pause(2.5, 4.0)
    except Exception as e:
        C.notify(f"auto-login fill failed: {e}", "warn"); return False

    if page.locator("input[name='approvals_code']").count() > 0:
        code = _totp()
        if code:
            page.fill("input[name='approvals_code']", code); C.pause(0.4, 0.8)
            try: page.get_by_role("button", name="Continue").first.click()
            except Exception: page.keyboard.press("Enter")
            C.pause(2, 3)
        else:
            C.notify("2FA prompt: set FBM_TOTP_SECRET or enter the code once", "warn")
            print(">>> enter 2FA code in the window, then Enter"); input()

    for label in ("Save browser", "Continue", "Not now", "OK"):
        try: page.get_by_text(label, exact=False).first.click(timeout=1500); C.pause(0.6, 1.2)
        except Exception: pass

    ok = not logged_out(page)
    if ok:
        C.notify("session auto-restored")
    else:
        try: page.screenshot(path="data/login_wall.png", full_page=True)
        except Exception: pass
        C.notify("AUTO-LOGIN FAILED - screenshot at data/login_wall.png", "error")
    return ok


def guard():
    C.load_env()
    from playwright.sync_api import sync_playwright
    with C.profile_lock():
        with sync_playwright() as p:
            ctx = p.chromium.launch_persistent_context(
                C.PROFILE_DIR, headless=False, viewport={"width": 1366, "height": 900},
                user_agent=C.USER_AGENT, args=["--disable-blink-features=AutomationControlled"])
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto("https://www.facebook.com/", wait_until="domcontentloaded"); C.pause(2, 3)
            if not logged_out(page):
                print("session OK"); ctx.close(); return True
            print("logged out -> attempting auto-login")
            ok = auto_login(page)
            ctx.close(); return ok


if __name__ == "__main__":
    sys.exit(0 if guard() else 1)