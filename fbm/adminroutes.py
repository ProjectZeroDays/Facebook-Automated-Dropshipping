"""
fbm/adminroutes.py — admin routes registration.

Registers admin console routes on a Flask app: /admin/index, /admin/webhooks,
/admin/scorecard, /admin/interventions, /admin/tenants/<tenant_id>.
"""
from __future__ import annotations
from flask import Blueprint, render_template, jsonify, request
from fbm import core as C

bp = Blueprint("admin", __name__)


@bp.get("/admin/index")
def admin_index():
    return render_template("admin/index.html")


@bp.get("/admin/webhooks")
def admin_webhooks():
    return jsonify({"webhooks": []})


@bp.get("/admin/scorecard")
def admin_scorecard():
    return jsonify({"scorecard": {}})


@bp.get("/admin/interventions")
def admin_interventions():
    return jsonify({"interventions": []})


@bp.get("/admin/tenants/<tenant_id>")
def admin_tenant(tenant_id: str):
    return jsonify({"tenant_id": tenant_id})


def register(app):
    """Register admin blueprint on *app*. Returns the app."""
    app.register_blueprint(bp)
    C.notify("adminroutes: admin blueprint registered", "info")
    return app


def main():
    print("adminroutes ok")


if __name__ == "__main__":
    main()