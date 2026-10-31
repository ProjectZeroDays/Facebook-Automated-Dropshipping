#!/bin/bash
# Build .dmg for macOS local deployment
set -euo pipefail
VERSION=${VERSION:-1.3.0}
APP="dist/FBM Ops.app"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp -r . "$APP/Contents/Resources/app/" || true
cp build_exe.sh "$APP/Contents/MacOS/FBM-Ops-Launch" || true
chmod +x "$APP/Contents/MacOS/FBM-Ops-Launch"
cat > "$APP/Contents/Info.plist" <<EOF
<?xml version="1.0"?><plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>com.projectzerodays.fbm</string>
<key>CFBundleName</key><string>FBM Ops</string>
<key>CFBundleVersion</key><string>${VERSION}</string>
</dict></plist>
EOF
# Create DMG via hdiutil if available
if command -v hdiutil &>/dev/null; then
    hdiutil create -volname "FBM Ops ${VERSION}" -srcfolder "$APP" -ov -format UDZO "dist/FBM-Ops-${VERSION}.dmg"
    echo "DMG: dist/FBM-Ops-${VERSION}.dmg"
else
    echo "WARNING: hdiutil not available — .app bundle ready at $APP (build .dmg on macOS)"
fi
