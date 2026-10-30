#!/usr/bin/env bash
# ============================================================================
# FBM Ops - Build Standalone Executable (Linux/macOS)
# Creates a standalone executable for local self-hosting
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================================"
echo "  FBM Ops - Build Standalone Executable"
echo "================================================================================"
echo ""

# -----------------------------------------------------------
# Step 1: Check PyInstaller
# -----------------------------------------------------------
echo "[1/4] Checking PyInstaller..."
if ! python3 -m PyInstaller --version &>/dev/null; then
    echo "  Installing PyInstaller..."
    pip3 install pyinstaller
fi
echo "  PyInstaller available"

# -----------------------------------------------------------
# Step 2: Install dependencies
# -----------------------------------------------------------
echo "[2/4] Installing Python dependencies..."
pip3 install -r requirements.txt
python3 -m playwright install --with-deps chromium
echo "  Dependencies installed"

# -----------------------------------------------------------
# Step 3: Build the executable
# -----------------------------------------------------------
echo "[3/4] Building standalone executable (this may take several minutes)..."
python3 -m PyInstaller fbm_ops.spec --clean --noconfirm
echo "  Build complete"

# -----------------------------------------------------------
# Step 4: Verify output
# -----------------------------------------------------------
echo "[4/4] Verifying output..."
EXE_PATH="$SCRIPT_DIR/dist/fbm-ops"
if [ -f "$EXE_PATH" ]; then
    SIZE=$(du -h "$EXE_PATH" | cut -f1)
    echo "  Executable: $EXE_PATH"
    echo "  Size: $SIZE"
    echo ""
    echo "To run standalone: ./dist/fbm-ops"
    echo "To run as daemon:  ./dist/fbm-ops -m fbm.daemon start"
else
    echo "Build output not found at $EXE_PATH"
    exit 1
fi

echo ""
echo "================================================================================"
echo "  BUILD COMPLETE"
echo "================================================================================"