"""app.py — run this: python app.py  ->  open http://127.0.0.1:5000"""
from __future__ import annotations
import os, uuid, time
from flask import Flask, render_template, request, session, jsonify, g
from fbm import chatbot, llm
from fbm.observability import setup_logging
from fbm import metrics as Metrics
setup_logging()  # structured JSON logging -> data/logs/app.log
from fbm.web_pages import bp as pages_bp
from fbm.security import verify_csrf, audit, security_headers, csrf_token
from fbm import default_commands, default_agents, default_workflows, mcp_integration
from fbm import plugins as plugin_loader

app = Flask(__name__, template_folder="fbm/templates")
app.secret_key = os.getenv("SECRET_KEY", "dev-only-change-me")

# --- Register enhancement subsystems ---
default_commands.register_all()
default_agents.register_all()
default_workflows.register_all()
mcp_integration.register_mcp_actions()
plugin_loader.get_manager().discover()

app.register_blueprint(pages_bp)

# --- Context processors ---
@app.context_processor
def inject_globals():
    return dict(
        current_user=session.get("user"),
        tenant=session.get("tenant_id", "demo"),
        csrf_token=csrf_token(session.get("session_id", "")),
        theme=session.get("theme", "dark"),
        plans=[],
        year=time.gmtime().tm_year,
    )

# --- Security middleware ---
@app.before_request
def _security_before():
    g.csrf_token = csrf_token(session.get("session_id", ""))
    if request.method in ("POST", "PUT", "DELETE", "PATCH") and not request.path.startswith("/chat/"):
        token = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
        if not verify_csrf(session.get("session_id", ""), token):
            return jsonify({"error": "CSRF token missing or invalid"}), 403

@app.after_request
def _security_after(response):
    return security_headers(response)

@app.route("/")
def home():
    return render_template("index.html", backend=llm.backend(), model=llm.pick_model().name)

@app.route("/chat/send", methods=["POST"])
def chat_send():
    sid = session.setdefault("chat_session", uuid.uuid4().hex[:12])
    if request.is_json:
        data = request.get_json(silent=True) or {}
        text = data.get("text", "")
        tenant_id = data.get("tenant_id", session.get("tenant_id", "demo"))
        files = []
    else:
        text = request.form.get("text", "")
        tenant_id = session.get("tenant_id", "demo")
        files = request.files.getlist("files")
    audit("chat_message", actor=tenant_id, detail=text[:200])
    out = chatbot.handle(tenant_id, sid, text, files)
    return jsonify(out)

@app.route("/command", methods=["POST"])
def command_exec():
    from fbm.default_commands import run_command
    name = request.form.get("cmd", "").lstrip("/")
    args = request.form.get("args", "")
    result = run_command(name, args)
    audit("command", actor=session.get("tenant_id", "demo"), detail=f"/{name} {args}")
    return jsonify(result)

@app.route("/agent", methods=["POST"])
def agent_run():
    from fbm.default_agents import run_agent
    name = request.form.get("agent", "")
    task = request.form.get("task", "")
    result = run_agent(name, task)
    audit("agent", actor=session.get("tenant_id", "demo"), detail=f"{name}: {task[:100]}")
    return jsonify(result)

@app.route("/workflow", methods=["POST"])
def workflow_run():
    from fbm.default_workflows import run_workflow
    name = request.form.get("workflow", "")
    result = run_workflow(name)
    audit("workflow", actor=session.get("tenant_id", "demo"), detail=name)
    return jsonify(result)

@app.route("/chat/search")
def chat_search():
    return jsonify({"results": chatbot.search(request.args.get("q", ""))})

@app.route("/chat/history")
def chat_history():
    from fbm.chatbot import _q
    rows = _q("SELECT role,text,created_at FROM chat_messages WHERE session_id=? ORDER BY id",
              (session.get("chat_session", ""),))
    return jsonify({"messages": [dict(r) for r in rows]})

@app.route("/commands")
def list_commands():
    from fbm.default_commands import COMMAND_REGISTRY
    return jsonify({name: help_text for name, (_, help_text) in COMMAND_REGISTRY.items()})

@app.route("/agents")
def list_agents():
    from fbm.default_agents import AGENT_REGISTRY
    return jsonify({name: help_text for name, (_, help_text) in AGENT_REGISTRY.items()})

@app.route("/workflows")
def list_workflows():
    from fbm.default_workflows import WORKFLOW_REGISTRY
    return jsonify({name: help_text for name, (_, help_text) in WORKFLOW_REGISTRY.items()})


@app.route("/healthz")
def healthz():
    from datetime import datetime
    return {"ok": True, "ts": datetime.utcnow().isoformat()}


@app.route("/metrics")
def metrics_endpoint():
    from flask import Response
    body, ctype = Metrics.render()
    return Response(body, mimetype=ctype)


if __name__ == "__main__":
    print(f"assistant backend: {llm.backend()}  model: {llm.pick_model().name}")
    app.run(debug=True, port=5000)