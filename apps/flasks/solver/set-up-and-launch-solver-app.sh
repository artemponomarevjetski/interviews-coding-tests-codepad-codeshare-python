#!/usr/bin/env bash
#
# Launch the screen-OCR Flask dashboard on port 5000
# ALWAYS runs in GPT mode with the most powerful model
# RUNS IN BACKGROUND AUTOMATICALLY - you can close terminal!
# ------------------------------------------------------------------------------

set -Eeuo pipefail

# Configuration
BASE_DIR="${BASE_DIR:-$HOME/interviews-coding-tests-codepad-codeshare-python/apps/flasks/solver}"
FLASK_DIR="$BASE_DIR"
LOG_DIR="$FLASK_DIR/log"
TEMP_DIR="$FLASK_DIR/temp"
VENVDIR="$BASE_DIR/venv"
REQUIREMENTS="$FLASK_DIR/requirements.txt"

# ALWAYS use gpt-4-turbo (most powerful accessible model)
MODEL="gpt-4-turbo"
MODE="gpt"

export OPENAI_MODEL="$MODEL"

# Initialize directories
mkdir -p "$LOG_DIR" "$TEMP_DIR"
touch "$LOG_DIR/flask.log"

# Cleanup previous instances
echo -e "\n\033[1;34m🛑 Killing any previous instance...\033[0m"
pkill -f "python.*snapshot\.py" 2>/dev/null || true
sleep 1
lsof -ti :5000 | xargs -r kill -9 2>/dev/null || true
sleep 1

# ---------------------------------------------------------------------------
# macOS Screen Recording Permission Check
# ---------------------------------------------------------------------------
if [[ "$OSTYPE" == "darwin"* ]]; then
  echo -e "\n\033[1;34m🔍 Checking screen-capture permission...\033[0m"
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

TERMINAL APPS TO CHECK:
  - Terminal.app
  - iTerm2
  - Warp
  - Any other terminal you're using

After adding permission, restart terminal and run this script again.
EOF
    exit 1
  fi
  
  if [[ ! -s "$TEST_PNG" ]]; then
    echo -e "\033[1;31m❌ Screenshot created but empty. Permission issue?\033[0m"
    rm -f "$TEST_PNG"
    exit 1
  fi
  
  rm -f "$TEST_PNG"
  echo -e "\033[1;32m✅ Screen capture permission confirmed\033[0m"
fi

# ---------------------------------------------------------------------------
# Python Environment Setup
# ---------------------------------------------------------------------------
echo -e "\n\033[1;34m🐍 Preparing Python environment...\033[0m"

if ! command -v python3 &> /dev/null; then
    echo -e "\033[1;31m❌ Python3 not found. Install Python 3.8+ first.\033[0m"
    exit 1
fi

if [[ ! -d "$VENVDIR" ]]; then
  echo "Creating virtual environment..."
  python3 -m venv "$VENVDIR"
  if [[ $? -ne 0 ]]; then
    echo -e "\033[1;31m❌ Failed to create virtual environment\033[0m"
    exit 1
  fi
fi

VENV_PYTHON="$VENVDIR/bin/python3"
VENV_PIP="$VENVDIR/bin/pip"

if [[ ! -f "$VENV_PYTHON" ]]; then
    echo -e "\033[1;31m❌ Virtual environment Python not found at: $VENV_PYTHON\033[0m"
    exit 1
fi

echo "✅ Using virtual environment Python: $VENV_PYTHON"

if [[ ! -f "$REQUIREMENTS" ]]; then
    echo -e "\033[1;31m❌ requirements.txt not found at: $REQUIREMENTS\033[0m"
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
# ENV FILE HANDLING - Connect to root .env
# ---------------------------------------------------------------------------
echo -e "\n\033[1;34m🔑 Checking OpenAI API key...\033[0m"
ROOT_ENV="$HOME/interviews-coding-tests-codepad-codeshare-python/.env"
TARGET_ENV="$FLASK_DIR/.env"

if [[ -f "$ROOT_ENV" ]]; then
    echo "✅ Found root .env at: $ROOT_ENV"
    
    if [[ ! -L "$TARGET_ENV" ]] || [[ ! -f "$TARGET_ENV" ]]; then
        echo "   🔗 Creating symlink: $TARGET_ENV -> $ROOT_ENV"
        ln -sf "$ROOT_ENV" "$TARGET_ENV"
    else
        echo "   🔗 Symlink already exists: $TARGET_ENV"
    fi
    
    if [[ ! -f "$TARGET_ENV" ]]; then
        echo -e "\033[1;31m❌ Symlink failed - $TARGET_ENV not accessible\033[0m"
        exit 1
    fi
    
    echo "   ✅ Connected to root .env"
else
    echo -e "\033[1;33m⚠️  Root .env not found at: $ROOT_ENV\033[0m"
    echo "Creating .env template..."
    cat > "$TARGET_ENV" << 'EOF'
# OpenAI API Key
# Get yours from: https://platform.openai.com/api-keys
OPENAI_API_KEY="your-api-key-here"
EOF
    echo -e "\033[1;31m❌ Please add a valid OpenAI API key to:\033[0m"
    echo -e "   $ROOT_ENV"
    echo -e "\033[1;36m💡 Get API key: https://platform.openai.com/api-keys\033[0m"
    exit 1
fi

if [[ -f "$TARGET_ENV" ]]; then
    echo "Checking API key in $TARGET_ENV..."
    API_KEY=$(grep 'OPENAI_API_KEY=' "$TARGET_ENV" | cut -d'=' -f2- | tr -d '[:space:]' | tr -d '"' | tr -d "'")
    
    if [[ -n "$API_KEY" ]]; then
        echo "✅ API key found: ${API_KEY:0:20}..."
        echo "   Key length: ${#API_KEY} characters"
        
        if [[ "$API_KEY" == "your-api-key-here" ]] || [[ ${#API_KEY} -lt 20 ]]; then
            echo -e "\033[1;31m❌ Invalid API key in $TARGET_ENV\033[0m"
            echo -e "\033[1;33m💡 Please add your actual OpenAI API key to:\033[0m"
            echo "   $ROOT_ENV"
            echo -e "\033[1;36m   Format: OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\033[0m"
            exit 1
        fi
        echo -e "\033[1;32m✅ API key validated successfully!\033[0m"
    else
        echo -e "\033[1;31m❌ No API key found in $TARGET_ENV\033[0m"
        echo -e "\033[1;33m💡 Add this line to $ROOT_ENV:\033[0m"
        echo "   OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        exit 1
    fi
else
    echo -e "\033[1;31m❌ .env file not found at $TARGET_ENV\033[0m"
    exit 1
fi

# ---------------------------------------------------------------------------
# Test Python environment
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
# Start Flask Application IN BACKGROUND
# ---------------------------------------------------------------------------
cd "$FLASK_DIR"

IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "127.0.0.1")
echo -e "\n\033[1;34m🌐 Dashboard will be on: http://$IP:5000\033[0m"

> "$LOG_DIR/flask.log"

echo -e "\n\033[1;34m🚀 Starting Flask application in $MODE mode (background)...\033[0m"
export GPT_MODE="$MODE"

echo "Starting Flask server in background..."
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
  if curl -fs "http://localhost:5000" >/dev/null 2>&1; then
    # Get Python version
    PY_VER=$("$VENV_PYTHON" --version 2>/dev/null | cut -d' ' -f2 | cut -d'.' -f1-2)
    
    echo -e "\n\033[1;32m"
    echo "┌────────────────────────────────────────────────────────────────────────────┐"
    echo "│ ✅ SYSTEM IS OPERATIONAL!                                                  │"
    echo "├────────────────────────────────────────────────────────────────────────────┤"
    printf "│ 🖥️  http://$IP:5000%*s │\n" $((60 - ${#IP} - 11)) ""
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
