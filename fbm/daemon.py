"""
fbm/daemon.py — Background daemon manager for FBM Ops.

Starts, stops, and monitors all services: backend API, dashboard frontend,
worker cron, watcher, rate limiter, health monitor, and auto-restart.
Runs as a standalone service manager for local self-hosting and Docker.
"""
from __future__ import annotations
import os, sys, json, time, signal, subprocess, socket, threading
from datetime import datetime, timezone
from pathlib import Path
from fbm import core as C

DAEMON_DIR = Path("data/daemon")
PID_FILE = DAEMON_DIR / "daemon.pid"
STATE_FILE = DAEMON_DIR / "state.json"
LOG_DIR = DAEMON_DIR / "logs"
SERVICES_FILE = DAEMON_DIR / "services.json"

# Service definitions: name -> (command, cwd, env_prefix, port, health_path)
SERVICES = {
    "backend": {
        "cmd": [sys.executable, "app.py"],
        "port": 5000,
        "health": "/",
        "critical": True,
        "auto_restart": True,
    },
    "dashboard": {
        "cmd": [sys.executable, "dashboard.py"],
        "port": 8080,
        "health": "/healthz",
        "critical": True,
        "auto_restart": True,
    },
    "watcher": {
        "cmd": [sys.executable, "sale_watcher.py", "--once"],
        "port": None,
        "health": None,
        "critical": False,
        "auto_restart": False,
    },
    "reprice": {
        "cmd": [sys.executable, "reprice.py"],
        "port": None,
        "health": None,
        "critical": False,
        "auto_restart": False,
    },
}

class DaemonState:
    """Persisted daemon state: running services, PIDs, start times, restarts."""

    def __init__(self):
        DAEMON_DIR.mkdir(parents=True, exist_ok=True)
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        self._state = self._load()

    def _load(self) -> dict:
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text())
            except Exception:
                pass
        return {"services": {}, "started_at": None, "version": "0.2.0"}

    def save(self):
        STATE_FILE.write_text(json.dumps(self._state, indent=2, default=str))

    def set_service(self, name: str, info: dict):
        self._state.setdefault("services", {})[name] = info
        self.save()

    def remove_service(self, name: str):
        self._state.setdefault("services", {}).pop(name, None)
        self.save()

    def get_service(self, name: str) -> dict | None:
        return self._state.get("services", {}).get(name)

    def list_services(self) -> dict:
        return self._state.get("services", {})

    def set_started(self):
        self._state["started_at"] = datetime.now(timezone.utc).isoformat()
        self.save()


state = DaemonState()


def is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    """Check if a TCP port is accepting connections."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def is_service_healthy(name: str, cfg: dict) -> bool:
    """Check if a service is healthy via its port or process."""
    info = state.get_service(name)
    if not info:
        return False
    pid = info.get("pid")
    if pid:
        try:
            os.kill(pid, 0)  # Check if process exists
        except OSError:
            return False
    if cfg["port"] and cfg["health"]:
        return is_port_open("127.0.0.1", cfg["port"])
    return pid is not None


def start_service(name: str, cfg: dict) -> dict | None:
    """Start a single service as a subprocess. Returns info dict or None."""
    if state.get_service(name) and is_service_healthy(name, cfg):
        return state.get_service(name)

    log_file = LOG_DIR / f"{name}.log"
    err_file = LOG_DIR / f"{name}.err"

    try:
        proc = subprocess.Popen(
            cfg["cmd"],
            cwd=os.getcwd(),
            env={**os.environ},
            stdout=open(log_file, "ab"),
            stderr=open(err_file, "ab"),
            stdin=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        )

        info = {
            "name": name,
            "pid": proc.pid,
            "cmd": " ".join(cfg["cmd"]),
            "port": cfg["port"],
            "started_at": datetime.now(timezone.utc).isoformat(),
            "restart_count": 0,
            "status": "starting",
            "log_file": str(log_file),
            "err_file": str(err_file),
        }

        # Brief wait for critical services to bind their port
        if cfg["port"]:
            for _ in range(30):
                time.sleep(0.25)
                if is_port_open("127.0.0.1", cfg["port"]):
                    info["status"] = "running"
                    break
            else:
                info["status"] = "port_timeout"
        else:
            info["status"] = "running"

        state.set_service(name, info)
        C.notify(f"daemon: started {name} (pid {proc.pid})", "info")
        return info

    except Exception as e:
        C.notify(f"daemon: failed to start {name}: {e}", "error")
        return None


def stop_service(name: str) -> bool:
    """Stop a running service by PID."""
    info = state.get_service(name)
    if not info:
        return True
    pid = info.get("pid")
    if pid:
        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                               capture_output=True)
            else:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
        except Exception:
            pass
    state.remove_service(name)
    C.notify(f"daemon: stopped {name}", "info")
    return True


def restart_service(name: str, cfg: dict) -> dict | None:
    """Stop and restart a service."""
    stop_service(name)
    time.sleep(1.0)
    return start_service(name, cfg)


def start_all() -> dict:
    """Start all enabled services. Returns dict of service -> info."""
    results = {}
    for name, cfg in SERVICES.items():
        if cfg["auto_restart"] or cfg["critical"]:
            results[name] = start_service(name, cfg)
        else:
            results[name] = state.get_service(name)
    state.set_started()
    return results


def stop_all():
    """Stop all running services."""
    for name in list(state.list_services().keys()):
        stop_service(name)


def monitor_loop(interval: int = 10):
    """Background monitor: auto-restart critical services that die."""
    C.notify("daemon: monitor loop started", "info")
    while True:
        try:
            for name, cfg in SERVICES.items():
                if not cfg["auto_restart"]:
                    continue
                info = state.get_service(name)
                if not info:
                    continue
                if not is_service_healthy(name, cfg):
                    restart_count = info.get("restart_count", 0) + 1
                    C.notify(f"daemon: {name} unhealthy, restart #{restart_count}", "warn")
                    info["restart_count"] = restart_count
                    info["status"] = "restarting"
                    state.set_service(name, info)
                    start_service(name, cfg)
        except Exception as e:
            C.notify(f"daemon: monitor error: {e}", "error")
        time.sleep(interval)


def status() -> dict:
    """Return current daemon status for all services."""
    result = {
        "daemon_running": is_port_open("127.0.0.1", 5000) or bool(state.list_services()),
        "started_at": state._state.get("started_at"),
        "services": {},
    }
    for name, cfg in SERVICES.items():
        info = state.get_service(name)
        result["services"][name] = {
            "running": is_service_healthy(name, cfg) if info else False,
            "pid": info.get("pid") if info else None,
            "status": info.get("status", "unknown") if info else "stopped",
            "port": cfg["port"],
            "restart_count": info.get("restart_count", 0) if info else 0,
        }
    return result


def daemonize(monitor: bool = True):
    """Run the daemon in the background (POSIX) or foreground (Windows)."""
    if os.name == "posix" and os.fork() != 0:
        return  # Parent exits, child continues

    # Start all services
    start_all()

    if monitor:
        monitor_loop()
    else:
        # Keep process alive
        while True:
            time.sleep(60)


def main():
    import argparse
    ap = argparse.ArgumentParser(description="FBM Ops daemon manager")
    ap.add_argument("action", choices=["start", "stop", "restart", "status", "monitor"])
    ap.add_argument("--service", help="Target service name (for start/stop/restart)")
    args = ap.parse_args()

    C.load_env()

    if args.action == "start":
        if args.service:
            cfg = SERVICES.get(args.service)
            if not cfg:
                print(f"Unknown service: {args.service}")
                sys.exit(1)
            info = start_service(args.service, cfg)
            print(f"{args.service}: {info['status'] if info else 'failed'}")
        else:
            results = start_all()
            for name, info in results.items():
                status = info["status"] if info else "unknown"
                print(f"{name}: {status}")
    elif args.action == "stop":
        if args.service:
            stop_service(args.service)
            print(f"{args.service}: stopped")
        else:
            stop_all()
            print("All services stopped")
    elif args.action == "restart":
        if args.service:
            cfg = SERVICES.get(args.service)
            if not cfg:
                print(f"Unknown service: {args.service}")
                sys.exit(1)
            info = restart_service(args.service, cfg)
            print(f"{args.service}: {info['status'] if info else 'failed'}")
        else:
            stop_all()
            start_all()
            print("All services restarted")
    elif args.action == "status":
        st = status()
        print(json.dumps(st, indent=2, default=str))
    elif args.action == "monitor":
        daemonize(monitor=True)


if __name__ == "__main__":
    main()