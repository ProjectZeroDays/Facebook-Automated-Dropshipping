# Cloud Deployment — FBM Ops

## Automated Deployments (GitHub Actions)

- `.github/workflows/deploy-cloud.yml` — deploy to VPS via SSH + Render via API
- `.github/workflows/build-exe.yml` — build standalone Windows `.exe` on tag push

### Triggering
- Push to `main` → deploy-cloud (manual approve on VPS, Render webhook on workflow_dispatch)
- Tag `vX.Y.Z` → build-exe creates artifact

### VPS Deploy
Requires secrets:
- `VPS_SSH_KEY`
- `VPS_USER`
- `VPS_HOST`

Script pulls repo, rebuilds Docker Compose prod stack (`docker-compose.prod.yml`), restarts service (`fbm-ops.service`).

### Render Deploy
Requires:
- `RENDER_API_KEY`
- `RENDER_SERVICE_ID`

### Docker Compose Production
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### Standalone EXE (Local)
```powershell
.\build_exe.ps1
# Output: dist\fbm-ops.exe
```

### Release Workflow
```bash
gh release create v1.1.1 --title "v1.1.1 — Admin Login, Trial Fix, GUI" \
  --notes-file RELEASE_NOTES.md
```
