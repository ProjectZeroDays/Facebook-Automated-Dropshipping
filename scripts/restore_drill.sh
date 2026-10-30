#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m fbm.profile_backup restore
echo "restored"