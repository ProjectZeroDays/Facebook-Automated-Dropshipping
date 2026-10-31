#!/usr/bin/env powershell
# ==========================================================================
# FBM Ops - Release Standalone EXE for v1.1.x
# Packages: build_exe.ps1 -> .exe -> release asset upload
# ===========================================================================
$VERSION = "v1.1.1"
$REPO = "https://github.com/ProjectZeroDays/Facebook-Automated-Dropshipping"
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host "  FBM Ops — Release Standalone EXE (Windows)" -ForegroundColor Cyan
Write-Host "  Version: $VERSION" -ForegroundColor Cyan
Write-Host "  Repo: $REPO" -ForegroundColor Cyan
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check build artifacts
if (Test-Path "dist/fbm-ops.exe") {
    $hash = (Get-FileHash "dist/fbm-ops.exe").Hash.Substring(0, 16)
    Write-Host "  Build artifact verified (sha256: $hash)" -ForegroundColor Green
} else {
    Write-Host "  Build artifact missing. Running build_exe.ps1..." -ForegroundColor Yellow
    .\build_exe.ps1
}

# Step 2: Create release notes for EXE
$notes = @"
FBM Ops Standalone EXE — v1.1.1
-----------------------------------
- Single-file executable (Windows)
- Includes all modules: auth, core, billing, admin dashboard, setup wizard
- Restricted proprietary license enforced (see LICENSE)
- Runs locally without Docker
- Launch: .\dist\fbm-ops.exe
"@
$notes | Out-File "RELEASE_${VERSION}_STANDALONE.md" -Encoding utf8
Write-Host "  Release notes: RELEASE_${VERSION}_STANDALONE.md" -ForegroundColor Green

Write-Host ""
Write-Host "To upload to GitHub release:" -ForegroundColor Yellow
Write-Host "  gh release upload v1.1.1 'dist/*.exe#FBM Ops v1.1.1 Standalone EXE (Windows)'" -ForegroundColor White
