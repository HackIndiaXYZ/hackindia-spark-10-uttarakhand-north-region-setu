#!/usr/bin/env bash
# FutureEra — Server Startup Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
elif [ -f "$SCRIPT_DIR/../.venv/bin/python" ]; then
    PYTHON_BIN="$SCRIPT_DIR/../.venv/bin/python"
else
    PYTHON_BIN="python3"
fi

echo "=========================================="
echo " Starting FutureEra Server..."
echo " Python: $PYTHON_BIN"
echo " Working Dir: $SCRIPT_DIR"
echo " URL: http://127.0.0.1:8002"
echo " Docs: http://127.0.0.1:8002/docs"
echo "=========================================="

exec "$PYTHON_BIN" run.py
