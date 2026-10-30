# ============================================================================
# FBM Ops - Build Standalone .exe (Windows PowerShell)
# Creates a single-file executable for local self-hosting
# ============================================================================

$ErrorActionPreference = "Stop"
$SCRIPT_DIR = Split-Path $MyInvocation.MyCommand.Path -Parent
Set-Location $SCRIPT_DIR

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  FBM Ops - Build Standalone .exe" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# -----------------------------------------------------------
# Step 1: Check PyInstaller
# -----------------------------------------------------------
Write-Host "[1/4] Checking PyInstaller..." -ForegroundColor Yellow
try {
    & python -m PyInstaller --version 2>$null
    Write-Host "  PyInstaller available" -ForegroundColor Green
} catch {
    Write-Host "  Installing PyInstaller..." -ForegroundColor Yellow
    pip install pyinstaller
}

# -----------------------------------------------------------
# Step 2: Install dependencies
# -----------------------------------------------------------
Write-Host "[2/4] Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
python -m playwright install --with-deps chromium
Write-Host "  Dependencies installed" -ForegroundColor Green

# -----------------------------------------------------------
# Step 3: Build the .exe
# -----------------------------------------------------------
Write-Host "[3/4] Building standalone .exe (this may take several minutes)..." -ForegroundColor Yellow
& python -m PyInstaller fbm_ops.spec --clean --noconfirm
if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "  Build complete" -ForegroundColor Green

# -----------------------------------------------------------
# Step 4: Verify output
# -----------------------------------------------------------
$exePath = Join-Path $SCRIPT_DIR "dist\fbm-ops.exe"
Write-Host "[4/4] Verifying output..." -ForegroundColor Yellow
if (Test-Path $exePath) {
    $size = (Get-Item $exePath).Length
    $sizeMB = [math]::Round($size / 1MB, 2)
    Write-Host "  Executable: $exePath" -ForegroundColor Green
    Write-Host "  Size: $sizeMB MB" -ForegroundColor Green
    Write-Host ""
    Write-Host "To run standalone: .\dist\fbm-ops.exe" -ForegroundColor Yellow
    Write-Host "To run as daemon:  .\dist\fbm-ops.exe -m fbm.daemon start" -ForegroundColor Yellow
} else {
    Write-Host "Build output not found at $exePath" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  BUILD COMPLETE" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan