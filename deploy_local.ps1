# ============================================================================
# FBM Ops - One-Click Local Deployment (Windows PowerShell)
# Installs dependencies, runs setup, starts all services as a background daemon
# ============================================================================

$ErrorActionPreference = "Stop"
$SCRIPT_DIR = Split-Path $MyInvocation.MyCommand.Path -Parent
Set-Location $SCRIPT_DIR

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  FBM Ops - One-Click Local Deployment" -ForegroundColor Cyan
Write-Host "  Autonomous Facebook Marketplace Dropshipping Operations" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# -----------------------------------------------------------
# Step 1: Check Python
# -----------------------------------------------------------
Write-Host "[1/6] Checking Python..." -ForegroundColor Yellow
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "Python not found. Please install Python 3.11+ from https://python.org" -ForegroundColor Red
    exit 1
}
Write-Host "  Found: $($python.Version)" -ForegroundColor Green

# -----------------------------------------------------------
# Step 2: Install dependencies
# -----------------------------------------------------------
Write-Host "[2/6] Installing Python dependencies..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install --with-deps chromium
Write-Host "  Dependencies installed" -ForegroundColor Green

# -----------------------------------------------------------
# Step 3: Check if setup is needed
# -----------------------------------------------------------
Write-Host "[3/6] Checking setup status..." -ForegroundColor Yellow
$setupNeeded = $true
if (Test-Path ".env") {
    $result = python -c "from fbm.setup import is_first_run; import sys; sys.exit(0 if not is_first_run() else 1)" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $setupNeeded = $false
        Write-Host "  Setup already complete" -ForegroundColor Green
    }
}

if ($setupNeeded) {
    Write-Host "  First-run setup required" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Launching interactive setup wizard..." -ForegroundColor Cyan
    python -m fbm.setup
    Write-Host ""
}

# -----------------------------------------------------------
# Step 4: Initialize database
# -----------------------------------------------------------
Write-Host "[4/6] Initializing database..." -ForegroundColor Yellow
python -c "from fbm import core as C; C.load_env(); C.init_db(); print('Database ready')"
Write-Host "  Database initialized" -ForegroundColor Green

# -----------------------------------------------------------
# Step 5: Start all services as daemon
# -----------------------------------------------------------
Write-Host "[5/6] Starting all services..." -ForegroundColor Yellow
# Kill any existing FBM processes
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Modules.ModuleName -contains "app.py" -or $_.Modules.ModuleName -contains "dashboard.py" } | Stop-Process -Force 2>$null | Out-Null

# Start daemon in background
Start-Process python -ArgumentList "-m", "fbm.daemon", "start" -WorkingDirectory $SCRIPT_DIR -WindowStyle Hidden
Start-Sleep -Seconds 5

# Verify backend is up
$backendUp = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:5000/" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $backendUp = $true
            break
        }
    } catch {}
    Start-Sleep -Seconds 1
}

if ($backendUp) {
    Write-Host "  Backend API running on http://127.0.0.1:5000" -ForegroundColor Green
} else {
    Write-Host "  WARNING: Backend may still be starting. Check data/daemon/logs/" -ForegroundColor Yellow
}

# Verify dashboard is up
$dashUp = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8080/healthz" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $dashUp = $true
            break
        }
    } catch {}
    Start-Sleep -Seconds 1
}

if ($dashUp) {
    Write-Host "  Dashboard running on http://127.0.0.1:8080" -ForegroundColor Green
} else {
    Write-Host "  WARNING: Dashboard may still be starting" -ForegroundColor Yellow
}

# -----------------------------------------------------------
# Step 6: Summary
# -----------------------------------------------------------
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  DEPLOYMENT COMPLETE" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Services:" -ForegroundColor Yellow
Write-Host "  Backend API:  http://127.0.0.1:5000" -ForegroundColor White
Write-Host "  Dashboard:    http://127.0.0.1:8080" -ForegroundColor White
Write-Host ""
Write-Host "Management:" -ForegroundColor Yellow
Write-Host "  Check status:  python -m fbm.daemon status" -ForegroundColor White
Write-Host "  Restart all:   python -m fbm.daemon restart" -ForegroundColor White
Write-Host "  Stop all:      python -m fbm.daemon stop" -ForegroundColor White
Write-Host "  View logs:     Get-Content data/daemon/logs/*.log -Tail 50 -Wait" -ForegroundColor White
Write-Host ""
Write-Host "To run as a Windows service, use NSSM or register with sc.exe" -ForegroundColor Gray
Write-Host "================================================================================" -ForegroundColor Cyan