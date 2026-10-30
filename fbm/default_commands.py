"""default_commands.py — register slash commands for the CLI and chatbot.

Commands: /publish, /renew, /recycle, /scrape, /reprice, /status, /backup,
/restore, /agents, /mcp, /workflow, /help, /setup, /daemon, /audit
"""
from __future__ import annotations
from fbm import core as C
from fbm import commands as Cmd
import fbm.bot as Bot
import fbm.scraper as Scraper
import fbm.targets as Targets
import fbm.deadman as Deadman
import fbm.profile_backup as PB
import fbm.setup as Setup
import fbm.daemon as Daemon

def cmd_publish(args: str = "") -> dict:
    limit = int(args) if args.strip().isdigit() else 5
    Bot.main() if False else None
    from fbm.bot import main as bot_main
    import sys
    old = sys.argv
    sys.argv = ["bot", "--mode", "list", "--limit", str(limit)]
    try:
        bot_main()
    except SystemExit:
        pass
    finally:
        sys.argv = old
    return {"status": "published", "limit": limit}

def cmd_renew(args: str = "") -> dict:
    limit = int(args) if args.strip().isdigit() else 10
    import sys
    old = sys.argv
    sys.argv = ["bot", "--mode", "renew", "--limit", str(limit)]
    try:
        from fbm.bot import main as bot_main
        bot_main()
    except SystemExit:
        pass
    finally:
        sys.argv = old
    return {"status": "renewed", "limit": limit}

def cmd_recycle(args: str = "") -> dict:
    limit = int(args) if args.strip().isdigit() else 10
    import sys
    old = sys.argv
    sys.argv = ["bot", "--mode", "recycle", "--limit", str(limit)]
    try:
        from fbm.bot import main as bot_main
        bot_main()
    except SystemExit:
        pass
    finally:
        sys.argv = old
    return {"status": "recycled", "limit": limit}

def cmd_scrape(args: str = "") -> dict:
    queries = args.strip() or "memphis"
    from fbm.scraper import main as scrape_main
    import sys
    old = sys.argv
    sys.argv = ["scraper", "--city", "memphis", "--queries", queries]
    try:
        scrape_main()
    except SystemExit:
        pass
    finally:
        sys.argv = old
    return {"status": "scraped", "queries": queries}

def cmd_reprice(args: str = "") -> dict:
    from fbm.reprice import run as reprice_run
    changed = reprice_run()
    return {"status": "repriced", "changed": len(changed)}

def cmd_status(args: str = "", tenant_id=C.DEFAULT_TENANT_ID) -> dict:
    with C.db() as c:
        active = c.execute("SELECT COUNT(*) n FROM listings WHERE status='active' AND tenant_id=?",
                           (tenant_id,)).fetchone()["n"]
        new_orders = c.execute("SELECT COUNT(*) n FROM orders WHERE status='NEW' AND tenant_id=?",
                               (tenant_id,)).fetchone()["n"]
        skus = c.execute("SELECT COUNT(*) n FROM skus WHERE active=1 AND tenant_id=?",
                         (tenant_id,)).fetchone()["n"]
    return {"active_listings": active, "new_orders": new_orders, "active_skus": skus}

def cmd_backup(args: str = "") -> dict:
    PB.backup()
    return {"status": "backup_created"}

def cmd_restore(args: str = "") -> dict:
    PB.restore(args.strip() or None)
    return {"status": "restored"}

def cmd_agents(args: str = "") -> dict:
    import fbm.agents as Ag
    return {"agents": Ag.list_agents()}

def cmd_mcp(args: str = "") -> dict:
    import fbm.mcp_integration as MI
    return {"mcp_tools": MI.list_mcp_tools()}

def cmd_workflow(args: str = "") -> dict:
    import fbm.workflows as Wf
    return {"workflow_modules": ["workflows", "actions", "commands"]}

def cmd_help(args: str = "") -> dict:
    cmds = Cmd.list_commands()
    return {"commands": [c["name"] for c in cmds], "help": {c["name"]: c["help"] for c in cmds}}

def cmd_setup(args: str = "") -> dict:
    """Run first-run setup wizard."""
    if Setup.is_first_run():
        return {"status": "setup_required", "message": "Run python -m fbm.setup to configure"}
    return {"status": "setup_complete"}


def cmd_daemon(args: str = "") -> dict:
    """Manage the background daemon."""
    parts = args.strip().split()
    action = parts[0] if parts else "status"
    service = parts[1] if len(parts) > 1 else None

    if action == "start":
        if service:
            cfg = Daemon.SERVICES.get(service)
            if not cfg:
                return {"error": f"Unknown service: {service}"}
            info = Daemon.start_service(service, cfg)
            return {"status": "started", "service": service, "detail": info}
        else:
            results = Daemon.start_all()
            return {"status": "started_all", "services": {k: v["status"] if v else "failed" for k, v in results.items()}}
    elif action == "stop":
        if service:
            Daemon.stop_service(service)
            return {"status": "stopped", "service": service}
        else:
            Daemon.stop_all()
            return {"status": "stopped_all"}
    elif action == "restart":
        if service:
            cfg = Daemon.SERVICES.get(service)
            if not cfg:
                return {"error": f"Unknown service: {service}"}
            info = Daemon.restart_service(service, cfg)
            return {"status": "restarted", "service": service, "detail": info}
        else:
            Daemon.stop_all()
            Daemon.start_all()
            return {"status": "restarted_all"}
    else:
        return Daemon.status()


COMMAND_REGISTRY = {
    "publish": (cmd_publish, "Publish inventory to Marketplace"),
    "renew": (cmd_renew, "Renew active listings"),
    "recycle": (cmd_recycle, "Delete + relist oldest items"),
    "scrape": (cmd_scrape, "Scrape competitor prices"),
    "reprice": (cmd_reprice, "Auto-reprice listings above median"),
    "status": (cmd_status, "Show shop status KPIs"),
    "backup": (cmd_backup, "Create encrypted profile + DB backup"),
    "restore": (cmd_restore, "Restore from latest backup"),
    "agents": (cmd_agents, "List available agents"),
    "mcp": (cmd_mcp, "List MCP tools"),
    "workflow": (cmd_workflow, "Workflow engine info"),
    "help": (cmd_help, "List all commands"),
    "setup": (cmd_setup, "Run first-run setup wizard"),
    "daemon": (cmd_daemon, "Manage background daemon services"),
}

def register_all() -> int:
    for name, (fn, help_text) in COMMAND_REGISTRY.items():
        Cmd.register(name, fn, help_text=help_text)
    return len(COMMAND_REGISTRY)

def run_command(name: str, args: str = "") -> dict:
    return Cmd.run(name, args)

def main():
    C.load_env()
    n = register_all()
    print(f"Registered {n} commands")
    print("default_commands ok")

if __name__ == "__main__":
    main()
