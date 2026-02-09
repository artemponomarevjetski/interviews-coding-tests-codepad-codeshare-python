#!/usr/bin/env bash
#
# Launch the screen-OCR Flask dashboard on port 5000 with proper environment setup
# Supports both GPT and no-GPT modes (default: no-gpt)
# RUNS IN BACKGROUND AUTOMATICALLY - you can close terminal!
# Usage: ./launch-flask-on5000.sh [no-gpt|gpt]
# ------------------------------------------------------------------------------

set -Eeuo pipefail

# Configuration
BASE_DIR="${BASE_DIR:-$HOME/interviews-coding-tests-codepad-codeshare-python/apps/flasks/solver}"
FLASK_DIR="$BASE_DIR"
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
sleep 1
lsof -ti :5000 | xargs -r kill -9 2>/dev/null || true
sleep 1

# ---------------------------------------------------------------------------
# macOS Screen Recording Permission Check
# ---------------------------------------------------------------------------
if [[ "$OSTYPE" == "darwin"* ]]; then
  echo -e "\n\033[1;34m🔍 Checking screen-capture permission...\033[0m"
  TEST_PNG="$TEMP_DIR/screencap_$$.png"
  
  # Check if we can actually capture
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
  
  # Verify the screenshot was created
  if [[ ! -s "$TEST_PNG" ]]; then
    echo -e "\033[1;31m❌ Screenshot created but empty. Permission issue?\033[0m"
    rm -f "$TEST_PNG"
    exit 1
  fi
  
  rm -f "$TEST_PNG"
  echo -e "\033[1;32m✅ Screen capture permission confirmed\033[0m"
fi

# ---------------------------------------------------------------------------
# Python Environment Setup - SIMPLIFIED
# ---------------------------------------------------------------------------
echo -e "\n\033[1;34m🐍 Preparing Python environment...\033[0m"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "\033[1;31m❌ Python3 not found. Install Python 3.8+ first.\033[0m"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [[ ! -d "$VENVDIR" ]]; then
  echo "Creating virtual environment..."
  python3 -m venv "$VENVDIR"
  if [[ $? -ne 0 ]]; then
    echo -e "\033[1;31m❌ Failed to create virtual environment\033[0m"
    exit 1
  fi
fi

# Clean approach: Just use the venv Python binary directly
VENV_PYTHON="$VENVDIR/bin/python3"
VENV_PIP="$VENVDIR/bin/pip"

if [[ ! -f "$VENV_PYTHON" ]]; then
    echo -e "\033[1;31m❌ Virtual environment Python not found at: $VENV_PYTHON\033[0m"
    exit 1
fi

echo "✅ Using virtual environment Python: $VENV_PYTHON"

# Install/upgrade dependencies
if [[ ! -f "$REQUIREMENTS" ]]; then
    echo -e "\033[1;31m❌ requirements.txt not found at: $REQUIREMENTS\033[0m"
    exit 1
fi

echo "Upgrading pip and installing dependencies..."
"$VENV_PIP" install --upgrade pip

# Install dependencies using the venv pip
"$VENV_PIP" install Flask==2.3.2 Pillow==11.3.0 pytesseract==0.3.13 requests==2.31.0 psutil==7.2.2

if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Installing macOS dependencies..."
    "$VENV_PIP" install pyobjc-framework-Quartz==9.2
fi

# ---------------------------------------------------------------------------
# Clean the .env file for GPT mode (WITHOUT BACKUP)
# ---------------------------------------------------------------------------
if [[ "$MODE" == "gpt" ]]; then
    echo -e "\n\033[1;34m🔑 Checking OpenAI API key...\033[0m"
    
    if [[ -f "$FLASK_DIR/.env" ]]; then
        echo "Checking .env file..."
        
        # Clean the file in-place WITHOUT creating backup
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # Save original modification time
            ORIG_MOD_TIME=$(stat -f "%m" "$FLASK_DIR/.env" 2>/dev/null || true)
            
            # Clean the file
            sed -i '' 's/%//g' "$FLASK_DIR/.env" 2>/dev/null
            sed -i '' 's/[[:space:]]*$//' "$FLASK_DIR/.env" 2>/dev/null
            
            # Restore original modification time if possible
            if [[ -n "$ORIG_MOD_TIME" ]]; then
                touch -m -t "$(date -r "$ORIG_MOD_TIME" +"%Y%m%d%H%M.%S" 2>/dev/null || echo "")" "$FLASK_DIR/.env" 2>/dev/null || true
            fi
        else
            # Linux version - clean without backup
            sed -i 's/%//g' "$FLASK_DIR/.env" 2>/dev/null
            sed -i 's/[[:space:]]*$//' "$FLASK_DIR/.env" 2>/dev/null
        fi
        
        # Check API key
        API_KEY=$(grep 'OPENAI_API_KEY=' "$FLASK_DIR/.env" | cut -d'=' -f2- | tr -d '[:space:]' | tr -d '"' | tr -d "'")
        if [[ -n "$API_KEY" ]]; then
            echo "✅ API key found: ${API_KEY:0:20}..."
            echo "   Key length: ${#API_KEY} characters"
            
            if [[ "$API_KEY" == "your-api-key-here" ]] || [[ ${#API_KEY} -lt 20 ]]; then
                echo -e "\033[1;31m❌ Please add a valid OpenAI API key to $FLASK_DIR/.env\033[0m"
                exit 1
            fi
        else
            echo -e "\033[1;31m❌ No API key found in .env file\033[0m"
            exit 1
        fi
    else
        echo -e "\033[1;33m⚠️  No .env file found\033[0m"
        echo "Creating .env template..."
        cat > "$FLASK_DIR/.env" << 'EOF'
# OpenAI API Key
# Get yours from: https://platform.openai.com/api-keys
OPENAI_API_KEY="your-api-key-here"
EOF
        echo -e "\033[1;31m❌ Please edit $FLASK_DIR/.env and add your OpenAI API key\033[0m"
        echo -e "\033[1;36m💡 Get API key: https://platform.openai.com/api-keys\033[0m"
        exit 1
    fi
fi

# ---------------------------------------------------------------------------
# Test Python environment
# ---------------------------------------------------------------------------
echo -e "\n\033[1;34m🧪 Testing Python environment...\033[0m"

"$VENV_PYTHON" -c "
import sys
print(f'✅ Python version: {sys.version}')
print(f'✅ Python executable: {sys.executable}')

# Test imports
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

# Test snapshot.py
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

# Get IP address
IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "127.0.0.1")
echo -e "\n\033[1;34m🌐 Dashboard will be on: http://$IP:5000\033[0m"

# Clear old log
> "$LOG_DIR/flask.log"

echo -e "\n\033[1;34m🚀 Starting Flask application in $MODE mode (background)...\033[0m"
export GPT_MODE="$MODE"

# Start Flask using venv Python IN BACKGROUND
echo "Starting Flask server in background..."
"$VENV_PYTHON" -u snapshot.py >"$LOG_DIR/flask.log" 2>&1 &
FLASK_PID=$!
sleep 3

# Check if process is running
if ! kill -0 "$FLASK_PID" 2>/dev/null; then
    echo -e "\n\033[1;31m❌ Flask process failed to start\033[0m"
    echo "Last 10 lines of log:"
    tail -n 10 "$LOG_DIR/flask.log"
    exit 1
fi

echo "✅ Process ID: $FLASK_PID"
echo "📄 Log file: $LOG_DIR/flask.log"

# Disown the process so it survives terminal closure
disown $FLASK_PID

# Health check with timeout
TIMEOUT=30
INTERVAL=2
ATTEMPTS=$((TIMEOUT/INTERVAL))

echo -e "\n\033[1;36m⏳ Waiting for Flask to start (max ${TIMEOUT}s)...\033[0m"
for ((i=1; i<=ATTEMPTS; i++)); do
  if curl -fs "http://localhost:5000" >/dev/null 2>&1; then
    echo -e "\n\033[1;32m✅ System is operational!\033[0m"
    echo -e "══════════════════════════════════════════════════════════════"
    echo -e "🖥️  Access at: http://$IP:5000"
    echo -e "📝 Mode: \033[1;33m$MODE\033[0m"
    echo -e "🐍 Python: $("$VENV_PYTHON" --version)"
    echo -e "📊 Screenshots: $TEMP_DIR/"
    echo -e "📋 Log file: $LOG_DIR/flask.log"
    echo -e "🔍 View logs: tail -f \"$LOG_DIR/flask.log\""
    echo -e "🛑 To stop: pkill -f \"python.*snapshot\.py\" or run 'ocr-stop'"
    echo -e "══════════════════════════════════════════════════════════════"
    echo -e "\033[1;36m✅ App running in background! You can close this terminal.\033[0m"
    echo ""
    
    # Don't tail logs - just exit so user can close terminal
    exit 0
  fi
  printf "."
  sleep "$INTERVAL"
done

echo -e "\n\033[1;31m❌ Startup failed after $TIMEOUT seconds\033[0m"
echo -e "\n\033[1;33m📋 Last 20 log lines:\033[0m"
tail -n 20 "$LOG_DIR/flask.log"

echo -e "\n\033[1;33m📋 Checking for common errors:\033[0m"

# Check for port conflict
echo "1. Checking port 5000..."
if lsof -ti :5000 | grep -v "^$FLASK_PID\$" >/dev/null; then
    echo "   ❌ Port 5000 in use by other process:"
    lsof -i :5000
fi

# Check Python process
echo "2. Checking Python process..."
if ps -p "$FLASK_PID" >/dev/null; then
    echo "   ✅ Process $FLASK_PID is running"
else
    echo "   ❌ Process $FLASK_PID died"
fi

# Check snapshot.py imports
echo "3. Testing snapshot.py imports..."
if ! "$VENV_PYTHON" -c "import sys; sys.path.insert(0, '$FLASK_DIR'); import snapshot; print('   ✅ snapshot.py imports OK')" 2>/dev/null; then
    echo "   ❌ snapshot.py import failed"
fi

echo -e "\n\033[1;36m💡 Manual troubleshooting:\033[0m"
echo "1. Run manually: cd \"$FLASK_DIR\" && \"$VENV_PYTHON\" snapshot.py"
echo "2. Check screen capture: screencapture test.png"
echo "3. Check venv: \"$VENV_PYTHON\" -c \"import flask; print('Flask OK')\""
echo "4. Kill all: pkill -f \"python.*snapshot\.py\" && lsof -ti :5000 | xargs -r kill -9"

# Kill the failed process
kill -9 "$FLASK_PID" 2>/dev/null || true
exit 1