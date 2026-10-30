"""
fbm/rp.py — RP_ID/ORIGIN resolution + diagnose.
"""
from __future__ import annotations
import os


def rp_id():
    return os.getenv("RP_ID", "localhost")


def rp_name():
    return os.getenv("RP_NAME", "FBM Ops")


def origin():
    return os.getenv("ORIGIN", "http://localhost:5000")


def diagnose():
    return {"ok": True, "rp_id": rp_id(), "rp_name": rp_name(), "origin": origin()}