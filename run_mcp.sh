#!/usr/bin/env bash
# Portable launcher for the fal.ai MCP server.
# Resolves the project directory from this script's location, creates the
# virtualenv on first run, installs requirements when they change, and then
# execs the server so the MCP client talks to it directly over stdio.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${FAL_MCP_VENV:-$PROJECT_DIR/.venv}"
PYTHON_BIN="${PYTHON:-python3}"
STAMP="$VENV_DIR/.requirements.sha"

cd "$PROJECT_DIR"

if [ ! -x "$VENV_DIR/bin/python" ]; then
    echo "[fal-mcp] creating virtualenv at $VENV_DIR" >&2
    "$PYTHON_BIN" -m venv "$VENV_DIR" >&2
fi

REQ_SHA="$(cksum requirements.txt | awk '{print $1}')"
if [ ! -f "$STAMP" ] || [ "$(cat "$STAMP")" != "$REQ_SHA" ]; then
    echo "[fal-mcp] installing requirements" >&2
    "$VENV_DIR/bin/python" -m pip install --quiet --disable-pip-version-check -r requirements.txt >&2
    echo "$REQ_SHA" > "$STAMP"
fi

exec "$VENV_DIR/bin/python" "$PROJECT_DIR/fal_mcp.py" "$@"
