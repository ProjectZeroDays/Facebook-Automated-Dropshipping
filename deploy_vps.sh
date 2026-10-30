#!/usr/bin/env bash
# ============================================================================
# FBM Ops - One-Click VPS Deployment (Docker Compose)
# Deploys the full stack to an online VPS with Docker Compose
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================================"
echo "  FBM Ops - One-Click VPS Deployment (Docker Compose)"
echo "================================================================================"
echo ""

# -----------------------------------------------------------
# Step 1: Check Docker
# -----------------------------------------------------------
echo "[1/7] Checking Docker..."
if ! command -v docker &>/dev/null; then
    echo "Docker not found. Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    echo "  Docker installed. Please log out and log back in, then re-run this script."
    exit 1
fi
if ! command -v docker compose &>/dev/null && ! docker compose version &>/dev/null; then
    echo "Docker Compose plugin not found. Installing..."
    mkdir -p ~/.docker/cli-plugins/
    curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 -o ~/.docker/cli-plugins/docker-compose
    chmod +x ~/.docker/cli-plugins/docker-compose
fi
echo "  Docker and Compose available"

# -----------------------------------------------------------
# Step 2: Check .env
# -----------------------------------------------------------
echo "[2/7] Checking environment configuration..."
if [ ! -f .env ]; then
    echo "  .env not found. Running setup wizard..."
    python3 -m fbm.setup
    echo ""
fi

# Validate required production vars
source .env 2>/dev/null || true
MISSING=()
for var in SECRET_KEY CSRF_SECRET STRIPE_SECRET_KEY STRIPE_WEBHOOK_SECRET; do
    if [ -z "${!var:-}" ]; then
        MISSING+=("$var")
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    echo "  WARNING: Missing required vars: ${MISSING[*]}"
    echo "  Edit .env and re-run this script, or continue with limited functionality."
    read -p "Continue anyway? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# -----------------------------------------------------------
# Step 3: Set VPS-specific defaults
# -----------------------------------------------------------
echo "[3/7] Setting VPS defaults..."
export GRAFANA_ADMIN_PASSWORD="${GRAFANA_ADMIN_PASSWORD:-$(openssl rand -hex 12)}"
export ALLOWED_HOSTS="${ALLOWED_HOSTS:-$(hostname -I | awk '{print $1}'),localhost,127.0.0.1}"
echo "  Grafana admin password: $GRAFANA_ADMIN_PASSWORD"
echo "  Allowed hosts: $ALLOWED_HOSTS"

# -----------------------------------------------------------
# Step 4: Pull/build images
# -----------------------------------------------------------
echo "[4/7] Building Docker images (this may take several minutes)..."
docker compose -f docker-compose.prod.yml pull 2>/dev/null || true
docker compose -f docker-compose.prod.yml build --parallel
echo "  Images built"

# -----------------------------------------------------------
# Step 5: Start all services
# -----------------------------------------------------------
echo "[5/7] Starting all services..."
docker compose -f docker-compose.prod.yml up -d
echo "  Services started"

# -----------------------------------------------------------
# Step 6: Wait for health
# -----------------------------------------------------------
echo "[6/7] Waiting for services to become healthy..."
sleep 10

BACKEND_OK=false
DASH_OK=false
for i in $(seq 1 30); do
    if curl -fsS http://localhost:5000/ >/dev/null 2>&1; then
        BACKEND_OK=true
    fi
    if curl -fsS http://localhost:8080/healthz >/dev/null 2>&1; then
        DASH_OK=true
    fi
    if [ "$BACKEND_OK" = true ] && [ "$DASH_OK" = true ]; then
        break
    fi
    sleep 2
done

# -----------------------------------------------------------
# Step 7: Summary
# -----------------------------------------------------------
echo ""
echo "================================================================================"
echo "  VPS DEPLOYMENT COMPLETE"
echo "================================================================================"
echo ""
if [ "$BACKEND_OK" = true ]; then
    echo "  Backend API:   http://$(hostname -I | awk '{print $1}'):5000"
else
    echo "  Backend API:   http://$(hostname -I | awk '{print $1}'):5000 (may still be starting)"
fi
if [ "$DASH_OK" = true ]; then
    echo "  Dashboard:     http://$(hostname -I | awk '{print $1}'):8080"
else
    echo "  Dashboard:     http://$(hostname -I | awk '{print $1}'):8080 (may still be starting)"
fi
echo "  Prometheus:    http://$(hostname -I | awk '{print $1}'):9090"
echo "  Grafana:       http://$(hostname -I | awk '{print $1}'):3000 (admin / $GRAFANA_ADMIN_PASSWORD)"
echo ""
echo "Management:"
echo "  Status:   docker compose -f docker-compose.prod.yml ps"
echo "  Logs:     docker compose -f docker-compose.prod.yml logs -f"
echo "  Stop:     docker compose -f docker-compose.prod.yml down"
echo "  Update:   docker compose -f docker-compose.prod.yml pull && docker compose -f docker-compose.prod.yml up -d"
echo ""
echo "To enable auto-start on boot:"
echo "  sudo systemctl enable docker"
echo "  # Add to /etc/rc.local or create a systemd service for docker compose up"
echo "================================================================================"