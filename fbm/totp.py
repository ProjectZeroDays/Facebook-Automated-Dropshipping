"""
fbm/totp.py — secret, QR, recovery codes.
"""
from __future__ import annotations


def new_secret():
    import pyotp
    return pyotp.TOTP(pyotp.random_base32()).secret


def provisioning_uri(email, secret):
    import pyotp
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name="FBM Ops")


def verify(secret, code):
    import pyotp
    return pyotp.TOTP(secret).verify(code)


def new_recovery_codes():
    import secrets
    return [secrets.token_hex(4) for _ in range(8)]


def hash_code(code):
    import hashlib
    return hashlib.sha256(code.encode()).hexdigest()


def qr_svg(uri):
    import qrcode
    import qrcode.image.svg as svg
    img = qrcode.make(uri, image_factory=svg.SvgPathImage)
    import io as _io
    buf = _io.BytesIO()
    img.save(buf)
    return buf.getvalue().decode()