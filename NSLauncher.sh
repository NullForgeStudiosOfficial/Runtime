#!/bin/bash

BASE_DIR="$(dirname "$(realpath "$0")")"

PYTHON="$BASE_DIR/venv/bin/python3"
SHOW_FILE="$BASE_DIR/NullSuite.show"
SCRIPT="$BASE_DIR/NullSuite.py"

if [ -e /dev/uinput ]; then
    sudo /bin/chmod 666 /dev/uinput 2>/dev/null || true
fi

# ==============================
# If already running → show + exit
# ==============================
if pgrep -x "NullSuite" > /dev/null; then
    echo "SHOW" > "$SHOW_FILE"
    exit 0
fi

# ==============================
# Watchdog loop
# ==============================

while true; do
    if ! pgrep -x "NullSuite" > /dev/null; then
        echo "launchingpy"
        nohup "$PYTHON" "$SCRIPT" > /dev/null 2>&1 &
        disown
        sleep 2
    fi

    sleep 5
done