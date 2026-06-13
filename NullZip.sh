#!/bin/bash

FILE="$1"

if [ ! -f "$FILE" ]; then
    exit 1
fi

DIR="$(dirname "$FILE")"
FILENAME="$(basename "$FILE")"
NAME="${FILENAME%.*}"

TARGET="$DIR/$NAME"

mkdir -p "$TARGET"

case "${FILE,,}" in
    *.zip|*.7z)
        7z x "$FILE" -o"$TARGET"
        ;;
    *.rar)
        unrar x "$FILE" "$TARGET/"
        ;;
    *)
        echo "Unsupported archive type: $FILE"
        exit 1
        ;;
esac