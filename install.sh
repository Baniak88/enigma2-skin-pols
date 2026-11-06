#!/bin/sh
# Installer manualny nie zmienia ustawień ani nie uruchamia ponownie GUI.
set -eu
SOURCE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$SOURCE/scripts/install_payload.py" "$SOURCE"

