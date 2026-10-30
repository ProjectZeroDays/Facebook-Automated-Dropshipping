"""
fbm/dashboard.py — one-screen ops console + static export.
"""
from __future__ import annotations
from datetime import datetime
from flask import Flask, render_template_string, request, Response
from fbm import core as C
from fbm import metrics as Metrics

app = Flask(__name__); C.init_db()

CSS = """
:root{--bg:#f6f7f9;--panel:#fff;--fg:#0f172a;--muted:#64748b;--border:#e2e8f0;--good:#15803d;--ok:#b45309;--bad:#b91c1c;--accent:#2563eb;--chip:#f1f5f9}
html[data-theme="dark"]{--bg:#0e1014;--panel:#161a21;--fg:#e6e8eb;--muted:#98a2b3;--border:#262c37;--good:#22c55e;--ok:#f59e0b;--bad:#ef4444;--accent:#60a5fa;--chip:#1c212b}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 Inter,system-ui,sans-serif;padding:22px}
.wrap{max-width:1180px;margin:0 auto}h1{font-size:20px;margin:0 0 2px;font-weight:600}
.sub{color:var(--muted);font-size:12px;margin-bottom:16px}
nav{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}
nav a{padding:7px 12px;border:1px solid var(--border);border-radius:9px;color:var(--fg);text-decoration:none;font-size:12.5px}
nav a.on{background:var(--accent);color:#fff;border-color:var(--accent)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:16px}
.kpi{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:12px 14px}
.kpi .l{font-size:11px;color:var(--muted);text-transform:uppercase}.kpi .v{font-size:21px;font-weight:600;margin-top:3px}
table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--border);border-radius:12px;overflow:hidden;font-size:12.5px}
th{text-align:left;font-size:11px;text-transform:uppercase;color:var(--muted);padding:9px 8px;border-bottom:1px solid var(--border);background:var(--chip)}
td{padding:8px;border-bottom:1px solid var(--border)}tr:last-child td{border-bottom:none}
td.n{text-align:right;font-variant-numeric:tabular-nums}
.good{color:var(--good);font-weight:600}.ok{color:var(--ok);font-weight:600}.bad{color:var(--bad);font-weight:600}
.badge{font-size:11px;padding:2px 7px;border-radius:999px;border:1px solid var(--border)}
.card{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:14px;margin-bottom:16px}
"""

def _tenant_id():
    from flask import request
    return request.args.get("tenant_id", C.DEFAULT_TENANT_ID)


def q(sql, args=(), tenant_id=None):
    if tenant_id is None:
        tenant_id = _tenant_id()
    # Auto-append tenant_id filter for tenant-scoped tables
    tenant_tables = ("skus", "orders", "samples", "listings", "comps", "events", "threads", "drafts", "pnl")
    # Only modify SELECT statements on tenant tables that don't already have tenant_id
    import re as _re
    if _re.match(r'\s*SELECT', sql, _re.I):
        for t in tenant_tables:
            if _re.search(r'\bFROM\s+' + t + r'\b', sql, _re.I) and 'tenant_id' not in sql:
                sql = sql.rstrip().rstrip(';')
                if ' WHERE ' in sql.upper():
                    sql += f" AND tenant_id=?"
                else:
                    sql += f" WHERE tenant_id=?"
                args = args + (tenant_id,)
                break
    with C.db() as c: return c.execute(sql, args).fetchall()


def shell(active, body):
    nav = "".join(f'<a class="{{"on" if k==active else ""}}" href="{h}">{k}</a>'
                  for k, h in [("overview", "/"), ("comps", "/comps"), ("listings", "/listings"),
                               ("orders", "/orders"), ("skus", "/skus"), ("pnl", "/pnl"),
                               ("events", "/events"), ("export", "/export")])
    return render_template_string(
        "<!doctype html><html data-theme=dark><head><meta charset=utf-8>"
        "<meta name=viewport content='width=device-width,initial-scale=1'><title>FBM Ops</title>"
        "<style>{{css}}</style></head><body><div class=wrap><h1>FBM ops console</h1>"
        "<div class=sub>{{ts}}</div><nav>{{nav|safe}}</nav>{{body|safe}}</div></body></html>",
        css=CSS, nav=nav, body=body, ts=datetime.now().strftime("%Y-%m-%d %H:%M"))


def margin_cls(m): return "good" if m >= 50 else ("ok" if m >= 35 else "bad")


@app.route("/")
def overview(tenant_id=C.DEFAULT_TENANT_ID):
    active = q("SELECT COUNT(*) n FROM listings WHERE status='active' AND tenant_id=?",
               (tenant_id,))[0]["n"]
    neword = q("SELECT COUNT(*) n FROM orders WHERE status='NEW' AND tenant_id=?",
               (tenant_id,))[0]["n"]
    comps_n = q("SELECT COUNT(*) n FROM comps WHERE tenant_id=?", (tenant_id,))[0]["n"]
    skus = q("SELECT price,cost FROM skus WHERE active=1 AND tenant_id=?", (tenant_id,))
    avg_m = sum(((float(s["price"]) - float(s["cost"] or 0) - float(s["price"]) * 0.13) / float(s["price"]) * 100)
                for s in skus if s["price"]) / len(skus) if skus else 0
    body = f"""<div class=kpis>
      <div class=kpi><div class=l>Active listings</div><div class=v>{active}</div></div>
      <div class=kpi><div class=l>New orders</div><div class="v {'bad' if neword else 'good'}">{neword}</div></div>
      <div class=kpi><div class=l>Avg margin</div><div class=v>{avg_m:.1f}%</div></div>
      <div class=kpi><div class=l>Comps rows</div><div class=v>{comps}</div></div>
      <div class=kpi><div class=l>SKUs</div><div class=v>{len(skus)}</div></div>
    </div><div class=card><b>Recent events</b>{events_table(8)}</div>"""
    return shell("overview", body)


def events_table(n=50):
    rows = q("SELECT created_at,kind,ref,detail FROM events ORDER BY id DESC LIMIT ?", (n,))
    tr = "".join(f"<tr><td>{r['created_at']}</td><td>{r['kind']}</td><td>{r['ref'] or ''}</td>"
                 f"<td>{r['detail'] or ''}</td></tr>" for r in rows)
    return f"<table><thead><tr><th>time</th><th>kind</th><th>ref</th><th>detail</th></tr></thead><tbody>{tr}</tbody></table>"


@app.route("/comps")
def comps():
    rows = q("SELECT query,title,price,location FROM comps ORDER BY id DESC LIMIT 300")
    tr = "".join(f"<tr><td>{r['query']}</td><td>{r['title']}</td><td class=n>${r['price']:.2f}</td>"
                 f"<td>{r['location'] or ''}</td></tr>" for r in rows)
    return shell("comps", f"<table><thead><tr><th>query</th><th>title</th><th class=n>price</th>"
                          f"<th>location</th></tr></thead><tbody>{tr}</tbody></table>")


@app.route("/listings")
def listings():
    rows = q("SELECT id,account,sku,title,price,renewed,status FROM listings ORDER BY seen_at DESC LIMIT 300")
    tr = "".join(f"<tr><td>{r['account'] or ''}</td><td>{r['sku'] or ''}</td><td>{r['title']}</td>"
                 f"<td class=n>${(r['price'] or 0):.2f}</td><td>{r['renewed']}</td>"
                 f"<td><span class=badge>{r['status']}</span></td></tr>" for r in rows)
    return shell("listings", f"<table><thead><tr><th>acct</th><th>sku</th><th>title</th>"
                             f"<th class=n>price</th><th>renews</th><th>status</th></tr></thead><tbody>{tr}</tbody></table>")


@app.route("/orders", methods=["GET", "POST"])
def orders():
    if request.method == "POST":
        fp = request.form["fp"]; status = request.form["status"]
        with C.db() as c:
            c.execute("UPDATE orders SET status=?, updated_at=datetime('now') WHERE fingerprint=?", (status, fp))
        return shell("orders", "<p>updated.</p>" + orders_table())
    return shell("orders", orders_table())


def orders_table():
    rows = q("SELECT fingerprint,title,price,buyer,status,tracking FROM orders ORDER BY created_at DESC LIMIT 300")
    opts = ["NEW", "ORDERED", "SHIPPED", "DELIVERED", "REFUNDED"]
    tr = ""
    for r in rows:
        sel = "".join(f'<option {{"selected" if o==r["status"] else ""}}>{o}</option>' for o in opts)
        tr += (f"<tr><td>{r['title']}</td><td class=n>${(r['price'] or 0):.2f}</td>"
               f"<td>{r['buyer'] or ''}</td><td>{r['tracking'] or ''}</td>"
               f"<td><form method=post style='display:flex;gap:6px'>"
               f"<input type=hidden name=fp value='{r['fingerprint']}'>"
               f"<select name=status>{sel}</select><button>save</button></form></td></tr>")
    return (f"<table><thead><tr><th>item</th><th class=n>price</th><th>buyer</th>"
            f"<th>tracking</th><th>status</th></tr></thead><tbody>{tr}</tbody></table>")


@app.route("/skus")
def skus():
    rows = q("SELECT sku,title,price,cost,source,backup_source FROM skus WHERE active=1")
    tr = ""
    for r in rows:
        p, c = float(r["price"] or 0), float(r["cost"] or 0)
        m = (p - c - p * 0.13) / p * 100 if p else 0
        tr += (f"<tr><td>{r['sku']}</td><td>{r['title']}</td><td class=n>${c:.2f}</td>"
               f"<td class=n>${p:.2f}</td><td class=n>{m:.1f}%</td>"
               f"<td class={margin_cls(m)}>{{'ok' if m >= 35 else 'thin'}}</td>"
               f"<td>{r['source'] or ''} / {r['backup_source'] or '—'}</td></tr>")
    return shell("skus", f"<table><thead><tr><th>sku</th><th>title</th><th class=n>cost</th>"
                         f"<th class=n>price</th><th class=n>margin</th><th></th><th>suppliers</th>"
                         f"</tr></thead><tbody>{tr}</tbody></table>")


@app.route("/pnl")
def pnl():
    rows = q("SELECT * FROM pnl ORDER BY month DESC LIMIT 24")
    tr = "".join(f"<tr><td>{r['month']}</td><td class=n>{r['orders']}</td>"
                 f"<td class=n>${r['revenue']:.2f}</td><td class=n>${r['fees']:.2f}</td>"
                 f"<td class=n>${r['cogs']:.2f}</td><td class=n>${r['refunds']:.2f}</td>"
                 f"<td class='n good'>${r['net']:.2f}</td></tr>" for r in rows)
    return shell("pnl", f"<table><thead><tr><th>month</th><th class=n>orders</th><th class=n>revenue</th>"
                        f"<th class=n>fees</th><th class=n>cogs</th><th class=n>refunds</th>"
                        f"<th class=n>net</th></tr></thead><tbody>{tr}</tbody></table>")


@app.route("/events")
def events(): return shell("events", events_table(200))


@app.route("/export")
def export():
    html = shell("overview", f"<div class=card>Snapshot {datetime.now():%Y-%m-%d %H:%M}</div>" + events_table(50))
    Path("data/dashboard.html").parent.mkdir(parents=True, exist_ok=True)
    Path("data/dashboard.html").write_text(html)
    return html


@app.route("/healthz")
def healthz(): return {"ok": True, "ts": datetime.now().isoformat()}


@app.route("/metrics")
def metrics_endpoint():
    body, ctype = Metrics.render()
    return Response(body, mimetype=ctype)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)