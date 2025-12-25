#!/usr/bin/env bash
#
# Launch the screen-OCR Flask dashboard on port 5000 with proper environment setup
# Supports both GPT and no-GPT modes (default: no-gpt)
# Usage: ./launch-flask-on5000.sh [no-gpt|gpt]
# ------------------------------------------------------------------------------

set -Eeuo pipefail

# Configuration
BASE_DIR="${BASE_DIR:-$HOME/interviews-coding-tests-codepad-codeshare-python}"
FLASK_DIR="$BASE_DIR/flask"
LOG_DIR="$FLASK_DIR/log"
TEMP_DIR="$FLASK_DIR/temp"
VENVDIR="$BASE_DIR/venv"
REQUIREMENTS="$FLASK_DIR/requirements.txt"

# Mode selection (default: no-gpt mode)
MODE="${1:-no-gpt}"
if [[ "$MODE" != "gpt" && "$MODE" != "no-gpt" ]]; then
    echo "Usage: $0 [no-gpt|gpt]"
    echo "  no-gpt: Disable GPT-4, OCR-only mode (default)"
    echo "  gpt:    Enable GPT-4 analysis"
    exit 1
fi

# Initialize directories
mkdir -p "$LOG_DIR" "$TEMP_DIR"
touch "$LOG_DIR/flask.log"

# Cleanup previous instances
echo -e "\n\033[1;34m🛑 Killing any previous instance...\033[0m"
pkill -f "python.*snapshot\.py" 2>/dev/null || true
lsof -ti :5000 | xargs -r kill -9 2>/dev/null || true

# ---------------------------------------------------------------------------
# macOS Screen Recording Permission Check
# ---------------------------------------------------------------------------
if [[ "$OSTYPE" == "darwin"* ]]; then
  echo -e "\n\033[1;34m🔍 Checking screen-capture permission...\033[0m"
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
fi

# ---------------------------------------------------------------------------
# Python Environment Setup
# ---------------------------------------------------------------------------
echo -e "\n\033[1;34m🐍 Preparing Python environment...\033[0m"
if [[ ! -d "$VENVDIR" ]]; then
  python3 -m venv "$VENVDIR"
fi
source "$VENVDIR/bin/activate"

pip install --upgrade pip
pip install -r "$REQUIREMENTS"

# ---------------------------------------------------------------------------
# Flask Application Launch
# ---------------------------------------------------------------------------
cd "$FLASK_DIR"  # Ensure we're in the correct directory

IP=$(ipconfig getifaddr en0 || ipconfig getifaddr en1 || echo "127.0.0.1")
echo -e "\n\033[1;34m🌐 Dashboard will be on: http://$IP:5000\033[0m"

echo -e "\n\033[1;34m🚀 Starting Flask application in $MODE mode...\033[0m"
export GPT_MODE="$MODE"
nohup python -u snapshot.py >"$LOG_DIR/flask.log" 2>&1 &
FLASK_PID=$!
disown "$FLASK_PID"

# Health check with timeout
TIMEOUT=5
INTERVAL=1
ATTEMPTS=$((TIMEOUT/INTERVAL))

for ((i=1; i<=ATTEMPTS; i++)); do
  if curl -fs "http://localhost:5000" >/dev/null; then
    echo -e "\n\033[1;32m✅ System is operational!\033[0m"
    echo -e "🔍 View logs with: tail -f \"$LOG_DIR/flask.log\""
    echo -e "🖥️  Access at: http://$IP:5000"
    echo -e "📝 Mode: $MODE"
    exit 0
  fi
  sleep "$INTERVAL"
done

echo -e "\n\033[1;31m❌ Startup failed; last 20 log lines:\033[0m"
tail -n 20 "$LOG_DIR/flask.log"
exit 1