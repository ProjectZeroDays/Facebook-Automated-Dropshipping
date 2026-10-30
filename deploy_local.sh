#!/usr/bin/env bash
# ============================================================================
# FBM Ops - One-Click Local Deployment (Linux/macOS bash)
# Installs dependencies, runs setup, starts all services as a background daemon
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================================"
echo "  FBM Ops - One-Click Local Deployment"
echo "  Autonomous Facebook Marketplace Dropshipping Operations"
echo "================================================================================"
echo ""

# -----------------------------------------------------------
# Step 1: Check Python
# -----------------------------------------------------------
echo "[1/6] Checking Python..."
if ! command -v python3 &>/dev/null; then
    echo "Python 3.11+ not found. Please install from https://python.org"
    exit 1
fi
PYTHON_VER=$(python3 --version 2>&1)
echo "  Found: $PYTHON_VER"

# -----------------------------------------------------------
# Step 2: Install dependencies
# -----------------------------------------------------------
echo "[2/6] Installing Python dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m playwright install --with-deps chromium
echo "  Dependencies installed"

# -----------------------------------------------------------
# Step 3: Check if setup is needed
# -----------------------------------------------------------
echo "[3/6] Checking setup status..."
SETUP_NEEDED=true
if [ -f .env ]; then
    if python3 -c "from fbm.setup import is_first_run; import sys; sys.exit(0 if not is_first_run() else 1)" 2>/dev/null; then
        SETUP_NEEDED=false
        echo "  Setup already complete"
    fi
fi

if [ "$SETUP_NEEDED" = true ]; then
    echo "  First-run setup required"
    echo ""
    echo "Launching interactive setup wizard..."
    python3 -m fbm.setup
    echo ""
fi

# -----------------------------------------------------------
# Step 4: Initialize database
# -----------------------------------------------------------
echo "[4/6] Initializing database..."
python3 -c "from fbm import core as C; C.load_env(); C.init_db(); print('Database ready')"
echo "  Database initialized"

# -----------------------------------------------------------
# Step 5: Start all services as daemon
# -----------------------------------------------------------
echo "[5/6] Starting all services..."
# Kill existing FBM processes
pkill -f "app.py" 2>/dev/null || true
pkill -f "dashboard.py" 2>/dev/null || true
pkill -f "fbm.daemon" 2>/dev/null || true
sleep 2

# Start daemon
python3 -m fbm.daemon start &
DAEMON_PID=$!
echo "  Daemon PID: $DAEMON_PID"

# Wait for backend
BACKEND_UP=false
for i in $(seq 1 30); do
    if curl -fsS http://127.0.0.1:5000/ >/dev/null 2>&1; then
        BACKEND_UP=true
        break
    fi
    sleep 1
done

if [ "$BACKEND_UP" = true ]; then
    echo "  Backend API running on http://127.0.0.1:5000"
else
    echo "  WARNING: Backend may still be starting. Check data/daemon/logs/"
fi

# Wait for dashboard
DASH_UP=false
for i in $(seq 1 30); do
    if curl -fsS http://127.0.0.1:8080/healthz >/dev/null 2>&1; then
        DASH_UP=true
        break
    fi
    sleep 1
done

if [ "$DASH_UP" = true ]; then
    echo "  Dashboard running on http://127.0.0.1:8080"
else
    echo "  WARNING: Dashboard may still be starting"
fi

# -----------------------------------------------------------
# Step 6: Summary
# -----------------------------------------------------------
echo ""
echo "================================================================================"
echo "  DEPLOYMENT COMPLETE"
echo "================================================================================"
echo ""
echo "Services:"
echo "  Backend API:  http://127.0.0.1:5000"
echo "  Dashboard:    http://127.0.0.1:8080"
echo ""
echo "Management:"
echo "  Check status:  python3 -m fbm.daemon status"
echo "  Restart all:   python3 -m fbm.daemon restart"
echo "  Stop all:      python3 -m fbm.daemon stop"
echo "  View logs:     tail -f data/daemon/logs/*.log"
echo ""
echo "To run as a systemd service, see deploy_vps.sh or create:"
echo "  sudo cp fbm-ops.service /etc/systemd/system/"
echo "  sudo systemctl enable --now fbm-ops"
echo "================================================================================"