"""
fbm/payments.py — Apple/Google/Venmo, Connect links.

Generates payment provider connect URLs for Apple Pay, Google Pay, and Venmo.
Each provider returns a connect URL that the user visits to complete auth.
"""
from __future__ import annotations
import os
from fbm import core as C

PROVIDERS = {
    "apple": "https://apple.com/pay/connect",
    "google": "https://pay.google.com/business/connect",
    "venmo": "https://venmo.com/business/connect",
}


def connect(provider: str) -> dict:
    """Return a connect dict for *provider* with URL and status."""
    provider = provider.lower()
    if provider not in PROVIDERS:
        return {"provider": provider, "url": "", "error": "unknown provider"}

    url = os.getenv(f"{provider.upper()}_CONNECT_URL", PROVIDERS[provider])
    api_key = os.getenv(f"{provider.upper()}_API_KEY", "")

    if not api_key:
        C.notify(f"payments: {provider} not configured (missing {provider.upper()}_API_KEY)", "warn")

    return {
        "provider": provider,
        "url": url,
        "configured": bool(api_key),
    }


def connect_all() -> dict:
    """Return connect dicts for all providers."""
    return {p: connect(p) for p in PROVIDERS}


def main():
    C.load_env()
    for p, info in connect_all().items():
        print(f"[payments] {p}: {info['url']} (configured={info['configured']})")
    print("payments ok")


if __name__ == "__main__":
    main()