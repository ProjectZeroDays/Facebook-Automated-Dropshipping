# Release v1.3.0 — Packaging + Cloud Deploy Automation

- Standalone EXE build pipeline (`build_exe.yml`) — Windows PyInstaller
- Package scripts: `.deb`, `.dmg`, `.ipa` (iOS wrapper), `.snap`, `.flatpak`
- Automated deploy pipeline (`deploy-cloud.yml`) — VPS SSH + Render webhook
- `DEPLOYMENT.md` with deploy instructions
- `RELEASE_NOTES.md` updated
- `v1.2.0` tag preserved; `v1.3.0` tagged for packaging release

Usage:
```bash
# Local EXE
.\build_exe.ps1

# Packages (requires fpm / snapcraft / flatpak / hdiutil / Xcode)
bash scripts/build-deb.sh
bash scripts/build-dmg.sh
bash scripts/build-snap.sh
bash scripts/build-flatpak.sh
bash scripts/build-ipa.sh

# Deploy
# Trigger .github/workflows/deploy-cloud.yml manually (requires secrets)
```

Tags: `v1.2.0`, `v1.3.0`
