#!/usr/bin/env bash
# Launches SolidworksMCP-python over stdio in MOCK mode (Linux / cloud sessions).
# First run bootstraps a pinned copy into .vendor/ (git-ignored); later runs just exec.
# stdout is the MCP JSON-RPC channel, so all bootstrap output goes to stderr.
set -euo pipefail

PIN=fdfe0168f5cc45f317f277f4f803831e1edb0a46   # upstream main as of 2026-10-19
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEST="$ROOT/.vendor/SolidworksMCP-python"
PY="$DEST/.venv/bin/python"

if [ ! -x "$PY" ] || [ "$(git -C "$DEST" rev-parse HEAD 2>/dev/null)" != "$PIN" ]; then
  {
    echo "[solidworks-mcp] bootstrapping $PIN into $DEST"
    rm -rf "$DEST" && mkdir -p "$DEST"
    git -C "$DEST" init -q
    git -C "$DEST" fetch -q --depth 1 https://github.com/andrewbartels1/SolidworksMCP-python.git "$PIN"
    git -C "$DEST" checkout -q FETCH_HEAD
    (cd "$DEST" && uv venv -q --python 3.13 .venv && uv pip install -q --python .venv/bin/python -e .)
  } >&2
fi

exec "$PY" -I "$DEST/src/utils/start_local_server_claude.py" --mock "$@"
