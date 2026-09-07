#!/bin/sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
CACHE_PATH=${VIBEBT_KITE_CACHE:-"$PROJECT_ROOT/../kite-futures-cache"}
PYTHON_BIN=${VIBEBT_PYTHON:-"$CACHE_PATH/.venv/bin/python"}

if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN=${PYTHON_BIN_FALLBACK:-python3}
fi

exec env VIBEBT_KITE_CACHE="$CACHE_PATH" "$PYTHON_BIN" "$@"
