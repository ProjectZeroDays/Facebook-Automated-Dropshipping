#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python dashboard.py &
python -m fbm.bot --mode renew --limit 5 &
wait