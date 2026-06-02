#!/bin/bash

if [ -e /dev/uinput ]; then
    sudo /bin/chmod 666 /dev/uinput 2>/dev/null || true
fi


source venv/bin/activate

python3 NullSuite.py

read
