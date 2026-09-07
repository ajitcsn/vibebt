#!/bin/sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
CACHE_PATH=${VIBEBT_KITE_CACHE:-"$PROJECT_ROOT/../kite-futures-cache"}
PYTHON_BIN=${VIBEBT_PYTHON:-"$CACHE_PATH/.venv/bin/python"}

if [ ! -x "$PYTHON_BIN" ]; then
  echo "VibeBT could not find a Python environment at $PYTHON_BIN." >&2
  exit 1
fi

exec "$PYTHON_BIN" "$CACHE_PATH/fetch.py" "$@"
