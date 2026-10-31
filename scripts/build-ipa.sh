#!/bin/bash
# Build .ipa wrapper for iOS (Electron/Cordova web wrapper — web app only)
VERSION=${VERSION:-1.3.0}
echo "NOTE: FBM Ops is a server-side Flask application. .ipa packaging targets the Electron/iOS web wrapper (launcher app), not a native mobile marketplace automation."
mkdir -p ios-wrapper
cp electron/main.js ios-wrapper/
cp electron/package.json ios-wrapper/
sed -i.bak "s/\"version\": \".*\"/\"version\": \"${VERSION}\"/" ios-wrapper/package.json
echo "IPA wrapper prepared: ios-wrapper/ (version ${VERSION})"
echo "To build .ipa: open ios-wrapper in Xcode / Capacitor → Product → Archive → Distribute"
