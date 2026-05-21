#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$(basename "$SCRIPT_DIR")" == "code" ]]; then
  CAPSULE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
  PY_SRC="$CAPSULE_ROOT/code/src"
else
  CAPSULE_ROOT="$SCRIPT_DIR"
  PY_SRC="$CAPSULE_ROOT/src"
fi

cd "$CAPSULE_ROOT"
python3 "$PY_SRC/main_result_reproduction.py"
