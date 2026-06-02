#!/bin/bash

BASE_DIR="$(dirname "$(realpath "$0")")"

PYTHON="$BASE_DIR/venv/bin/python3"
SHOW_FILE="$BASE_DIR/NullSuite.show"
SCRIPT="$BASE_DIR/NullSuite.py"

if pgrep -x "NullSuite" > /dev/null; then
    echo "NULLMOJI" > "$SHOW_FILE"
    exit 0
fi