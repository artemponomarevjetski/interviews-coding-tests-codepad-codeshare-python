#!/usr/bin/env bash
#
# +----------------------------------------------------------+
# |                                                          |
# |     SOLVER – Screen OCR + GPT Dashboard                  |
# |                                                          |
# |  • Captures your screen and extracts text with OCR      |
# |  • Sends the extracted text to the most powerful GPT    |
#  • Shows results on a live web dashboard               |
# |  • Runs in background – close the terminal safely      |
# |                                                          |
# |  Usage:                                                  |
# |    ./set-up-and-launch-solver-app.sh                    |
# |                                                          |
# |  Then open http://localhost:5001 in your browser.       |
# +----------------------------------------------------------+

set -Eeuo pipefail

# === ASCII HEADER ===
echo -e "\033[1;36m"
cat << "EOF"
  ███████╗ ██████╗ ██╗     ██╗   ██╗███████╗██████╗ 
  ██╔════╝██╔═══██╗██║     ██║   ██║██╔════╝██╔══██╗
  ███████╗██║   ██║██║     ██║   ██║█████╗  ██████╔╝
  ╚════██║██║   ██║██║     ╚██╗ ██╔╝██╔══╝  ██╔══██╗
  ███████║╚██████╔╝███████╗ ╚████╔╝ ███████╗██║  ██║
  ╚══════╝ ╚═════╝ ╚══════╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝
EOF
echo -e "\033[0m"
echo -e "\033[1;34m  Screen OCR + GPT Dashboard – Launcher\033[0m"
echo ""

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_DIR="${BASE_DIR:-$HOME/interviews-coding-tests-codepad-codeshare-python/solver}"
FLASK_DIR="$BASE_DIR"
LOG_DIR="$FLASK_DIR/log"
TEMP_DIR="$FLASK_DIR/temp"
VENVDIR="$BASE_DIR/venv"
REQUIREMENTS="$FLASK_DIR/requirements.txt"
PORT=5001

# Stop any previous overlay (if present)
"$BASE_DIR/../overlay/stop-overlay.sh" 2>/dev/null || true

# ALWAYS use the most powerful accessible model
MODEL="gpt-4-turbo"
MODE="gpt"
export OPENAI_MODEL="$MODEL"

mkdir -p "$LOG_DIR" "$TEMP_DIR"
touch "$LOG_DIR/flask.log"

# ---------------------------------------------------------------------------
# 1. Cleanup previous instances – WITH USER CONFIRMATION
# ---------------------------------------------------------------------------
# Global flag: 1 if we killed, 0 if we skipped or no instance found
KILLED=0

echo -e "\033[1;33m🧹 Checking for previous Solver instances...\033[0m"

OLD_PID=$(pgrep -f "python.*snapshot\.py" 2>/dev/null || true)
OLD_PORT_PID=$(lsof -ti :$PORT 2>/dev/null || true)

if [[ -n "$OLD_PID" || -n "$OLD_PORT_PID" ]]; then
    echo -e "\033[1;33m⚠️  Found a running Solver app:\033[0m"
    if [[ -n "$OLD_PID" ]]; then
        echo "   Process(es): $OLD_PID"
        ps -p $OLD_PID -o pid,cmd 2>/dev/null | tail -n +2
    fi
    if [[ -n "$OLD_PORT_PID" ]]; then
        echo "   Port $PORT is in use by PID: $OLD_PORT_PID"
    fi
    
    read -p "Do you want to kill the previous Solver app and restart? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "\033[1;33m🔄 Killing previous instances...\033[0m"
        pkill -f "python.*snapshot\.py" 2>/dev/null || true
        lsof -ti :$PORT | xargs -r kill -9 2>/dev/null || true
        sleep 1
        echo -e "\033[1;32m✅ Cleanup complete.\033[0m"
        KILLED=1
    else
        echo -e "\033[1;33m⏭️  Skipping kill. Will check if port $PORT is free.\033[0m"
        KILLED=0
    fi
else
    echo -e "\033[1;32m✅ No previous Solver instance found.\033[0m"
    KILLED=0
fi

# ---------------------------------------------------------------------------
# 2. Check port availability if we didn't kill
# ---------------------------------------------------------------------------
if [[ $KILLED -eq 0 ]] && lsof -ti :"$PORT" >/dev/null 2>&1; then
    echo -e "\033[1;31m❌ Port $PORT is still in use by another process.\033[0m"
    echo -e "\033[1;31m   You chose not to kill the previous instance, but the port is occupied.\033[0m"
    echo -e "\033[1;31m   Please stop the other process manually, or kill it and restart.\033[0m"
    exit 1
fi

# ---------------------------------------------------------------------------
# 3. macOS Screen Recording Permission Check
# ---------------------------------------------------------------------------
if [[ "$OSTYPE" == "darwin"* ]]; then
  echo -e "\033[1;34m🔍 Checking screen-capture permission...\033[0m"
  TEST_PNG="$TEMP_DIR/screencap_$$.png"
  
  if ! timeout 5 screencapture -x "$TEST_PNG" 2>/dev/null; then
    cat <<'EOF' >&2
❌ Screen capture failed.

FIX macOS PERMISSIONS:
  1. Open System Settings → Privacy & Security → Screen Recording
  2. Click the lock icon (enter password)
  3. Remove your terminal app from the list (if present)
  4. Click the "+" button and add your terminal app back
  5. Quit terminal completely and reopen

After adding permission, restart terminal and run this script again.
EOF
    exit 1
  fi
  
  if [[ ! -s "$TEST_PNG" ]]; then
    echo -e "\033[1;31m❌ Screenshot empty – permission issue?\033[0m"
    rm -f "$TEST_PNG"
    exit 1
  fi
  
  rm -f "$TEST_PNG"
  echo -e "\033[1;32m✅ Screen capture permission confirmed\033[0m"
fi

# ---------------------------------------------------------------------------
# 4. Python Environment Setup
# ---------------------------------------------------------------------------
echo -e "\n\033[1;34m🐍 Preparing Python environment...\033[0m"

if ! command -v python3 &> /dev/null; then
    echo -e "\033[1;31m❌ Python3 not found. Install Python 3.8+ first.\033[0m"
    exit 1
fi

if [[ ! -d "$VENVDIR" ]]; then
  echo "Creating virtual environment..."
  python3 -m venv "$VENVDIR" || {
    echo -e "\033[1;31m❌ Failed to create virtual environment\033[0m"
    exit 1
  }
fi

VENV_PYTHON="$VENVDIR/bin/python3"
VENV_PIP="$VENVDIR/bin/pip"

if [[ ! -f "$VENV_PYTHON" ]]; then
    echo -e "\033[1;31m❌ Virtual environment Python not found: $VENV_PYTHON\033[0m"
    exit 1
fi
echo "✅ Using virtual environment Python: $VENV_PYTHON"

if [[ ! -f "$REQUIREMENTS" ]]; then
    echo -e "\033[1;31m❌ requirements.txt not found: $REQUIREMENTS\033[0m"
    exit 1
fi

echo "Upgrading pip and installing dependencies..."
"$VENV_PIP" install --upgrade pip
"$VENV_PIP" install Flask==2.3.2 Pillow==11.3.0 pytesseract==0.3.13 requests==2.31.0 psutil==7.2.2

if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Installing macOS dependencies..."
    "$VENV_PIP" install pyobjc-framework-Quartz==9.2
fi

# ---------------------------------------------------------------------------
# 5. ENV FILE HANDLING – Use ~/.env directly
# ---------------------------------------------------------------------------
echo -e "\n\033[1;34m🔑 Checking OpenAI API key...\033[0m"
HOME_ENV="$HOME/.env"

if [[ ! -f "$HOME_ENV" ]]; then
    echo -e "\033[1;31m❌ ~/.env not found.\033[0m"
    echo "Please create ~/.env with your OPENAI_API_KEY."
    echo "Format: OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    exit 1
fi

# Load the API key from ~/.env
API_KEY=$(grep '^OPENAI_API_KEY=' "$HOME_ENV" | head -1 | cut -d'=' -f2- | tr -d '[:space:]' | tr -d '"' | tr -d "'")

if [[ -z "$API_KEY" ]]; then
    echo -e "\033[1;31m❌ OPENAI_API_KEY not found in ~/.env\033[0m"
    exit 1
fi

if [[ "$API_KEY" == "your-api-key-here" ]] || [[ ${#API_KEY} -lt 20 ]]; then
    echo -e "\033[1;31m❌ Invalid API key in ~/.env\033[0m"
    echo "Please replace with your actual key."
    exit 1
fi

echo -e "\033[1;32m✅ API key loaded from ~/.env (${API_KEY:0:20}...)\033[0m"

# Export the key for snapshot.py
export OPENAI_API_KEY="$API_KEY"

# Also create a local .env file for snapshot.py if it doesn't exist
if [[ ! -f "$FLASK_DIR/.env" ]]; then
    echo "OPENAI_API_KEY=$API_KEY" > "$FLASK_DIR/.env"
    echo -e "\033[1;32m✅ Created local .env file for snapshot.py\033[0m"
fi

# ---------------------------------------------------------------------------
# 6. Test Python environment
# ---------------------------------------------------------------------------
echo -e "\n\033[1;34m🧪 Testing Python environment...\033[0m"

"$VENV_PYTHON" -c "
import sys
print(f'✅ Python version: {sys.version}')
print(f'✅ Python executable: {sys.executable}')

imports_ok = True
try:
    import flask
    print(f'✅ Flask {flask.__version__}')
except ImportError as e:
    print(f'❌ Flask import failed: {e}')
    imports_ok = False

try:
    import PIL
    print(f'✅ Pillow {PIL.__version__}')
except ImportError as e:
    print(f'❌ PIL import failed: {e}')
    imports_ok = False

try:
    import pytesseract
    print(f'✅ pytesseract - Tesseract: {pytesseract.get_tesseract_version()}')
except ImportError as e:
    print(f'❌ pytesseract import failed: {e}')
    imports_ok = False

try:
    import psutil
    print(f'✅ psutil {psutil.__version__}')
except ImportError as e:
    print(f'❌ psutil import failed: {e}')
    imports_ok = False

try:
    sys.path.insert(0, '$FLASK_DIR')
    import snapshot
    print('✅ snapshot.py imports successfully')
except Exception as e:
    print(f'❌ snapshot.py import failed: {e}')
    imports_ok = False

if not imports_ok:
    print('❌ Some imports failed. Exiting.')
    sys.exit(1)
"

# ---------------------------------------------------------------------------
# 7. Start Flask Application IN BACKGROUND
# ---------------------------------------------------------------------------
cd "$FLASK_DIR"

IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "127.0.0.1")
echo -e "\n\033[1;34m🌐 Dashboard will be on: http://$IP:$PORT\033[0m"

> "$LOG_DIR/flask.log"

echo -e "\n\033[1;34m🚀 Starting Flask application in $MODE mode (background)...\033[0m"
export GPT_MODE="$MODE"

"$VENV_PYTHON" -u snapshot.py >"$LOG_DIR/flask.log" 2>&1 &
FLASK_PID=$!
sleep 3

if ! kill -0 "$FLASK_PID" 2>/dev/null; then
    echo -e "\n\033[1;31m❌ Flask process failed to start\033[0m"
    echo "Last 10 lines of log:"
    tail -n 10 "$LOG_DIR/flask.log"
    exit 1
fi

echo "✅ Process ID: $FLASK_PID"
echo "📄 Log file: $LOG_DIR/flask.log"

disown $FLASK_PID

TIMEOUT=30
INTERVAL=2
ATTEMPTS=$((TIMEOUT/INTERVAL))

echo -e "\n\033[1;36m⏳ Waiting for Flask to start (max ${TIMEOUT}s)...\033[0m"
for ((i=1; i<=ATTEMPTS; i++)); do
  if curl -fs "http://localhost:$PORT" >/dev/null 2>&1; then
    PY_VER=$("$VENV_PYTHON" --version 2>/dev/null | cut -d' ' -f2 | cut -d'.' -f1-2)
    
    echo -e "\n\033[1;32m"
    echo "┌────────────────────────────────────────────────────────────────────────────┐"
    echo "│ ✅ SYSTEM IS OPERATIONAL!                                                  │"
    echo "├────────────────────────────────────────────────────────────────────────────┤"
    printf "│ 🖥️  http://$IP:$PORT%*s │\n" $((60 - ${#IP} - ${#PORT} - 1)) ""
    printf "│ 🤖  %-*s │\n" 58 "$MODEL"
    printf "│ 📝  %-*s │\n" 58 "$MODE"
    printf "│ 🐍  Python %-*s │\n" 52 "$PY_VER"
    printf "│ 📊  Screenshots: %-*s │\n" 42 "$TEMP_DIR"
    printf "│ 📋  Log: %-*s │\n" 50 "$LOG_DIR/flask.log"
    printf "│ 🔍  View logs: tail -f %-*s │\n" 35 "\"$LOG_DIR/flask.log\""
    printf "│ 🛑  Stop: pkill -f %-*s │\n" 35 "\"python.*snapshot\.py\""
    echo "├────────────────────────────────────────────────────────────────────────────┤"
    echo "│ ✅ App running in background! You can close this terminal.                 │"
    echo "└────────────────────────────────────────────────────────────────────────────┘"
    echo -e "\033[0m"
    echo ""

    # Auto‑close terminal (macOS only) – only on success
    if [[ "$OSTYPE" == "darwin"* ]]; then
        osascript -e 'tell application "Terminal" to close (first window whose frontmost is true)' &
    fi
    exit 0
  fi
  printf "."
  sleep "$INTERVAL"
done

echo -e "\n\033[1;31m❌ Startup failed after $TIMEOUT seconds\033[0m"
echo -e "\n\033[1;33m📋 Last 20 log lines:\033[0m"
tail -n 20 "$LOG_DIR/flask.log"

kill -9 "$FLASK_PID" 2>/dev/null || true
exit 1