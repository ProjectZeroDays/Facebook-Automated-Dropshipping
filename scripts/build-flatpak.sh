#!/bin/bash
# Build Flatpak manifest for FBM Ops
VERSION=${VERSION:-1.3.0}
mkdir -p flatpak
cat > flatpak/com.projectzerodays.fbm.json <<EOF
{
  "app-id": "com.projectzerodays.fbm",
  "runtime": "org.freedesktop.Platform",
  "runtime-version": "23.08",
  "sdk": "org.freedesktop.Sdk",
  "command": "python",
  "modules": [
    {
      "name": "fbm-ops",
      "buildsystem": "simple",
      "build-commands": [
        "cp -r . /app/share/fbm-ops",
        "mkdir -p /app/bin",
        "ln -sf /app/share/fbm-ops/deploy_local.sh /app/bin/fbm-start"
      ],
      "sources": [{"type":"dir", "path":"."}]
    }
  ],
  "finish-args": ["--share=network"]
}
EOF
echo "FLATPAK manifest: flatpak/com.projectzerodays.fbm.json (version ${VERSION})"
echo "Build: flatpak-builder --repo=repo build-dir flatpak/com.projectzerodays.fbm.json"
