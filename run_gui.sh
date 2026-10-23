#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v poetry >/dev/null 2>&1; then
    echo "Poetry is missing. See README.md." >&2
    exit 1
fi
exec poetry run python src/main.py
