#!/usr/bin/env bash
set -euo pipefail

# virtual display
Xvfb :99 -screen 0 1366x900x24 >/tmp/xvfb.log 2>&1 &
export DISPLAY=:99
sleep 1

# secrets perms
[ -f /app/.env ] && chmod 600 /app/.env || true

case "${1:-worker}" in
  worker)
    if [ ! -d "$FBM_PROFILE/Default" ]; then
      echo "[boot] first run: opening browser for login..."
      python3 login_once.py || true
    fi
    crontab /app/crontab
    exec cron -f
    ;;
  dashboard)
    exec gunicorn -b 0.0.0.0:8080 -w 2 dashboard:app
    ;;
  once)
    exec python3 run_all.sh
    ;;
  *)
    exec "$@"
    ;;
esac