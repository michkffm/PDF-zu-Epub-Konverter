#!/usr/bin/env bash
# Check prerequisites and install the locked Python project. No remote installer is executed.
set -euo pipefail
cd "$(dirname "$0")"
for command in python3 poetry; do
    if ! command -v "$command" >/dev/null 2>&1; then
        echo "Missing $command. See README.md for installation instructions." >&2
        exit 1
    fi
done
poetry install
if command -v tesseract >/dev/null 2>&1; then
    tesseract --list-langs
else
    echo "Tesseract is optional; install it and the required language data for OCR."
fi
echo "Ready. Launch with ./run_gui.sh"
