#!/usr/bin/env bash
#
# Launch the screen‑OCR Flask dashboard on port 5000, creating the venv if
# necessary, checking macOS screen‑recording permission and tailing logs.
# ---------------------------------------------------------------------------

set -Eeuo pipefail

BASE_DIR="${BASE_DIR:-$HOME/interviews-coding-tests-codepad-codeshare-python}"
cd "$BASE_DIR"

LOG_DIR="$BASE_DIR/log"
TEMP_DIR="$BASE_DIR/temp"
VENVDIR="$BASE_DIR/venv"

mkdir -p "$LOG_DIR" "$TEMP_DIR"
touch   "$LOG_DIR/flask.log"

echo -e "\n\033[1;34m🛑 Killing any previous instance...\033[0m"
pkill -f "python.*snapshot\.py" 2>/dev/null || true
lsof -ti :5000 | xargs -r kill -9 2>/dev/null || true

# ---------------------------------------------------------------------------
# macOS: verify the terminal has Screen‑Recording entitlement
# ---------------------------------------------------------------------------
echo -e "\n\033[1;34m🔍 Checking screen‑capture permission...\033[0m"
TEST_PNG="$TEMP_DIR/screencap_$$.png"
if ! timeout 5 screencapture -x -o "$TEST_PNG" 2>/dev/null || [[ ! -s "$TEST_PNG" ]]; then
  cat <<'EOF' >&2
❌ Screen capture denied.

FIX:
  1. System Settings → Privacy & Security → Screen Recording
  2. Remove your terminal app, press the ↻ button, then add it back
  3. Quit & reopen the terminal

EOF
  exit 1
fi
rm -f "$TEST_PNG"

# ---------------------------------------------------------------------------
# Python environment
# ---------------------------------------------------------------------------
echo -e "\n\033[1;34m🐍 Preparing Python environment...\033[0m"
if [[ ! -d "$VENVDIR" ]]; then
  python3 -m venv "$VENVDIR"
fi
# shellcheck source=/dev/null
source "$VENVDIR/bin/activate"

pip install --upgrade pip
pip install -r requirements.txt

# ---------------------------------------------------------------------------
# Launch the Flask app
# ---------------------------------------------------------------------------
IP=$(ipconfig getifaddr en0 || ipconfig getifaddr en1 || echo "127.0.0.1")
echo -e "\n\033[1;34m🌐 Dashboard will be on: http://$IP:5000\033[0m"

echo -e "\n\033[1;34m🚀 Starting Flask application...\033[0m"
nohup python -u snapshot.py >"$LOG_DIR/flask.log" 2>&1 &
FLASK_PID=$!
disown "$FLASK_PID"

# Health check (max 5 s)
for i in {1..5}; do
  if curl -fs "http://localhost:5000" >/dev/null; then
    echo -e "\n\033[1;32m✅ System is operational!\033[0m"
    echo    "🔍  tail -f \"$LOG_DIR/flask.log\""
    exit 0
  fi
  sleep 1
done

echo -e "\n\033[1;31m❌ Startup failed; see last 20 log lines:\033[0m"
tail -n 20 "$LOG_DIR/flask.log"
exit 1
