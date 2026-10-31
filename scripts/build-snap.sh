#!/bin/bash
# Build .snap for Ubuntu (snapcraft)
VERSION=${VERSION:-1.3.0}
cat > snap/snapcraft.yaml <<EOF
name: fbm-ops
base: core22
version: '${VERSION}'
summary: FB Dropshipper — automated Facebook Marketplace ops
license: Proprietary
contact: admin@example.com
issues: https://github.com/ProjectZeroDays/Facebook-Automated-Dropshipping/issues
grade: stable
confinement: strict

parts:
  fbm:
    source: .
    plugin: dump
    organize:
      deploy_local.sh: bin/fbm-start

apps:
  fbm-ops:
    command: bin/python -m fbm
    daemon: simple
    plugs: [network, home]
EOF
echo "SNAP manifest: snap/snapcraft.yaml (version ${VERSION})"
echo "Build: snapcraft pack (requires snapcraft)"
