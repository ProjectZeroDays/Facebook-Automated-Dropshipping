#!/bin/bash
# Build .deb for FBM Ops (Debian/Ubuntu)
# Uses fpm if available, else dpkg-deb directly
set -euo pipefail
VERSION=${VERSION:-1.3.0}
NAME="fbm-ops"
BUILD_DIR="dist/${NAME}_${VERSION}_amd64"
mkdir -p "$BUILD_DIR/usr/share/fbm-ops" "$BUILD_DIR/usr/bin" "$BUILD_DIR/DEBIAN"

cp -r . "$BUILD_DIR/usr/share/fbm-ops/" || true
cp deploy_local.sh "$BUILD_DIR/usr/bin/fbm-ops-start" || true
chmod +x "$BUILD_DIR/usr/bin/fbm-ops-start"

cat > "$BUILD_DIR/DEBIAN/control" <<EOF
Package: ${NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: amd64
Maintainer: ProjectZeroDays <admin@example.com>
Description: FB Dropshipper — automated Facebook Marketplace ops
 Restricted proprietary software. Authorized use only.
EOF

dpkg-deb --build "$BUILD_DIR" "dist/${NAME}_${VERSION}_amd64.deb"
echo "DEB: dist/${NAME}_${VERSION}_amd64.deb"
