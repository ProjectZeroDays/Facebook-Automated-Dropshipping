#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# FBM Ops Production Entrypoint
# Starts all required services: Xvfb, backend, dashboard, cron worker
# Supports: all (default), backend, dashboard, worker, once
###############################################################################

echo "[boot] FBM Ops starting $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Ensure data directories exist
mkdir -p /app/data /app/data/logs /app/data/backups \
         /app/data/imgs/variants /app/data/daemon /app/models

# Start virtual display for Playwright
if [ ! -f /tmp/.X99-lock ]; then
    Xvfb :99 -screen 0 1366x900x24 >/tmp/xvfb.log 2>&1 &
    export DISPLAY=:99
    sleep 2
    echo "[boot] Xvfb started on :99"
fi
export DISPLAY=:99

# Tighten .env permissions
[ -f /app/.env ] && chmod 600 /app/.env || true

# Load environment
set -a
[ -f /app/.env ] && . /app/.env
set +a

# Initialize database on first run
python3 -c "from fbm import core as C; C.load_env(); C.init_db(); print('[boot] DB initialized')" 2>&1 || true

# Run setup if .env is missing or incomplete
if [ ! -f /app/.env ] || ! python3 -c "from fbm.setup import is_first_run; import sys; sys.exit(0 if not is_first_run() else 1)" 2>/dev/null; then
    echo "[boot] .env missing or incomplete - setup required"
fi

case "${1:-all}" in
  all)
    echo "[boot] Starting all services..."

    # Start backend API (port 5000)
    python3 app.py &
    BACKEND_PID=$!
    echo "[boot] Backend API started (pid $BACKEND_PID, port 5000)"

    # Wait for backend to be ready
    for i in $(seq 1 30); do
        if curl -fsS http://127.0.0.1:5000/ >/dev/null 2>&1; then
            echo "[boot] Backend API ready"
            break
        fi
        sleep 1
    done

    # Start dashboard (port 8080)
    python3 dashboard.py &
    DASH_PID=$!
    echo "[boot] Dashboard started (pid $DASH_PID, port 8080)"

    # Start cron worker for scheduled tasks
    crontab /app/crontab 2>/dev/null || true
    cron -f &
    CRON_PID=$!
    echo "[boot] Cron worker started (pid $CRON_PID)"

    # Start daemon monitor (auto-restart critical services)
    python3 -m fbm.daemon monitor &
    DAEMON_PID=$!
    echo "[boot] Daemon monitor started (pid $DAEMON_PID)"

    # Wait for any process to exit (if one dies, we exit too)
    wait -n
    echo "[boot] A service exited, shutting down..."
    kill $BACKEND_PID $DASH_PID $CRON_PID $DAEMON_PID 2>/dev/null || true
    ;;
  backend)
    exec python3 app.py
    ;;
  dashboard)
    exec python3 dashboard.py
    ;;
  worker)
    crontab /app/crontab 2>/dev/null || true
    exec cron -f
    ;;
  once)
    exec python3 run_all.sh
    ;;
  *)
    exec "$@"
    ;;
esac