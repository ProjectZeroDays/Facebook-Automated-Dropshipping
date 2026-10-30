"""
fbm/auth.py — passkeys, passwords, resets, step-up, audit.
"""
from __future__ import annotations
import base64, hashlib, hmac, json, os, secrets, time, uuid
from datetime import datetime, timedelta
from fbm import core as C
from fbm import vault


def _b64(b): return base64.urlsafe_b64encode(b).decode().rstrip("=")


def _unb64(s): return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def hash_password(pw: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.scrypt(pw.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt${_b64(salt)}${_b64(dk)}"


def verify_password(pw: str, stored: str) -> bool:
    try:
        _, salt, dk = stored.split("$")
        calc = hashlib.scrypt(pw.encode(), salt=_unb64(salt), n=2**14, r=8, p=1, dklen=32)
        return hmac.compare_digest(calc, _unb64(dk))
    except Exception:
        return False


def set_password(user_id, pw):
    _w("UPDATE users SET password_hash=? WHERE id=?", (hash_password(pw), user_id))


def has_password(user_id):
    return bool(_q("SELECT password_hash FROM users WHERE id=?", (user_id,))[0]["password_hash"])


def _q(sql, args=()):
    with C.db() as c:
        return c.execute(sql, args).fetchall()


def _w(sql, args=()):
    with C.db() as c:
        c.execute(sql, args)