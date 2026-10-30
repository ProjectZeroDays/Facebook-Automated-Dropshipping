"""
fbm/authroutes.py — all auth endpoints.
"""
from __future__ import annotations
from flask import Blueprint, request, jsonify


bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods=["POST"])
def login():
    return {"ok": True}


@bp.route("/reset", methods=["POST"])
def reset():
    return {"ok": True}


@bp.route("/register", methods=["POST"])
def register():
    return {"ok": True}


def register_routes(app):
    app.register_blueprint(bp)
    return app