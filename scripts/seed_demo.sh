#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python bootstrap.py
echo "seeded"