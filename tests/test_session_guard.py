import session_guard as SG
from fakes import FakePage

def test_detects_login_form():
    assert SG.logged_out(FakePage(email_inputs=1)) is True

def test_detects_login_wall_text():
    assert SG.logged_out(FakePage(email_inputs=0, body="Log into Facebook")) is True

def test_logged_in_returns_false():
    assert SG.logged_out(FakePage(email_inputs=0, body="Marketplace")) is False

def test_totp_is_six_digits_or_none(monkeypatch):
    monkeypatch.setenv("FBM_TOTP_SECRET", "JBSWY3DPEHPK3PXP")
    code = SG._totp()
    assert code is None or (code.isdigit() and len(code) == 6)
