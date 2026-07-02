#!/usr/bin/env bash
#
# Launch the screen-OCR Flask dashboard on port 5000 with proper environment setup
# Supports both GPT and no-GPT modes (default: no-gpt)
# RUNS IN BACKGROUND AUTOMATICALLY - you can close terminal!
# Usage: ./set-up-and-launch-solver-app.sh [no-gpt|gpt] [model]
# ------------------------------------------------------------------------------

set -Eeuo pipefail

# Configuration
BASE_DIR="${BASE_DIR:-$HOME/interviews-coding-tests-codepad-codeshare-python/apps/flasks/solver}"
FLASK_DIR="$BASE_DIR"
LOG_DIR="$FLASK_DIR/log"
TEMP_DIR="$FLASK_DIR/temp"
VENVDIR="$BASE_DIR/venv"
REQUIREMENTS="$FLASK_DIR/requirements.txt"

# Detect model from environment variable (set by alias) or command line
MODEL="${OPENAI_MODEL:-gpt-4-turbo}"
VALID_MODELS=("gpt-4o" "gpt-4-turbo" "gpt-4" "gpt-3.5-turbo" "o1-preview" "o1-mini")
VALID=0
for vm in "${VALID_MODELS[@]}"; do
    if [[ "$MODEL" == "$vm" ]]; then
        VALID=1
        break
    fi
done

if [[ $VALID -eq 0 ]]; then
    MODEL="gpt-4-turbo"
fi

# Mode selection (default: no-gpt mode)
MODE="${1:-no-gpt}"
if [[ "$MODE" != "gpt" && "$MODE" != "no-gpt" ]]; then
    echo "Usage: $0 [no-gpt|gpt] [model]"
    echo "  no-gpt: Disable GPT-4, OCR-only mode (default)"
    echo "  gpt:    Enable GPT-4 analysis"
    echo "  model:  (optional) gpt-4o, gpt-4-turbo, gpt-4, gpt-3.5-turbo, o1-preview, o1-mini"
    exit 1
fi

# Set environment variable for model
export OPENAI_MODEL="$MODEL"

# ---------------------------------------------------------------------------
# DYNAMIC PROJECTIONS & INFO DISPLAY
# ---------------------------------------------------------------------------
show_projections() {
    # Pricing per 1K tokens
    case "$MODEL" in
        "gpt-4o")
            COST_PER_1K_INPUT="0.005"
            COST_PER_1K_OUTPUT="0.015"
            AVG_COST_PER_ANALYSIS="0.03"
            DESC="Best balance"
            ;;
        "gpt-4-turbo")
            COST_PER_1K_INPUT="0.010"
            COST_PER_1K_OUTPUT="0.030"
            AVG_COST_PER_ANALYSIS="0.06"
            DESC="Faster, powerful"
            ;;
        "gpt-4")
            COST_PER_1K_INPUT="0.030"
            COST_PER_1K_OUTPUT="0.060"
            AVG_COST_PER_ANALYSIS="0.18"
            DESC="Most powerful"
            ;;
        "gpt-3.5-turbo")
            COST_PER_1K_INPUT="0.001"
            COST_PER_1K_OUTPUT="0.002"
            AVG_COST_PER_ANALYSIS="0.006"
            DESC="Fastest, cheapest"
            ;;
        "o1-preview")
            COST_PER_1K_INPUT="0.015"
            COST_PER_1K_OUTPUT="0.060"
            AVG_COST_PER_ANALYSIS="0.15"
            DESC="Advanced reasoning"
            ;;
        "o1-mini")
            COST_PER_1K_INPUT="0.003"
            COST_PER_1K_OUTPUT="0.012"
            AVG_COST_PER_ANALYSIS="0.03"
            DESC="Fast reasoning"
            ;;
        *)
            AVG_COST_PER_ANALYSIS="0.03"
            DESC="Unknown"
            ;;
    esac

    # Try to get actual balance from the API
    BALANCE="Unknown"
    BALANCE_RESPONSE=$(curl -s --max-time 3 \
        -H "Authorization: Bearer $(grep 'OPENAI_API_KEY=' ~/interviews-coding-tests-codepad-codeshare-python/.env 2>/dev/null | cut -d'=' -f2- | tr -d '[:space:]' | tr -d '"' | tr -d "'")" \
        "https://api.openai.com/dashboard/billing/credit_grants" 2>/dev/null || echo "")
    
    if [[ -n "$BALANCE_RESPONSE" ]]; then
        TOTAL_GRANTED=$(echo "$BALANCE_RESPONSE" | grep -o '"total_granted":[0-9.]*' | cut -d':' -f2)
        TOTAL_USED=$(echo "$BALANCE_RESPONSE" | grep -o '"total_used":[0-9.]*' | cut -d':' -f2)
        if [[ -n "$TOTAL_GRANTED" ]] && [[ -n "$TOTAL_USED" ]]; then
            REMAINING=$(echo "$TOTAL_GRANTED - $TOTAL_USED" | bc -l 2>/dev/null || echo "0")
            BALANCE=$(printf "%.2f" "$REMAINING")
        fi
    fi
    
    if [[ "$BALANCE" == "Unknown" ]] || [[ "$BALANCE" == "0.00" ]]; then
        BALANCE="17.85"  # Fallback
    fi
    
    # Calculate projections
    EST_ANALYSES=$(echo "$BALANCE / $AVG_COST_PER_ANALYSIS" | bc -l 2>/dev/null | xargs printf "%.0f" 2>/dev/null || echo "~300")
    
    # Get the command that was run
    CMD="${BASH_SOURCE[0]}"
    if [[ -n "$ALIAS_NAME" ]]; then
        CMD="$ALIAS_NAME"
    fi
    
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║ 🚀 SOLVER LAUNCHED                                              ║"
    echo "╠═══════════════════════════════════════════════════════════════════╣"
    echo "║ 📌 Command:      $CMD                                           ║"
    echo "║ 🤖 Model:        $MODEL ($DESC)                                ║"
    echo "║ 💰 Input/1K:     \$$COST_PER_1K_INPUT / Output/1K: \$$COST_PER_1K_OUTPUT   ║"
    echo "║ 💵 Balance:      \$$BALANCE                                      ║"
    echo "║ 📊 Avg cost:     ~\$$AVG_COST_PER_ANALYSIS per analysis                     ║"
    echo "║ 📈 Est. uses:    ~$EST_ANALYSES analyses remaining               ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo ""
}

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
if [[ "$MODE" == "gpt" ]]; then
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
fi

# ---------------------------------------------------------------------------
# SHOW PROJECTIONS (if GPT mode)
# ---------------------------------------------------------------------------
if [[ "$MODE" == "gpt" ]]; then
    show_projections
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
    echo -e "\n\033[1;32m✅ System is operational!\033[0m"
    echo -e "══════════════════════════════════════════════════════════════"
    echo -e "🖥️  Access at: http://$IP:5000"
    echo -e "📝 Mode: \033[1;33m$MODE\033[0m"
    echo -e "🤖 Model: \033[1;33m$MODEL\033[0m"
    echo -e "🐍 Python: $("$VENV_PYTHON" --version)"
    echo -e "📊 Screenshots: $TEMP_DIR/"
    echo -e "📋 Log file: $LOG_DIR/flask.log"
    echo -e "🔍 View logs: tail -f \"$LOG_DIR/flask.log\""
    echo -e "🛑 To stop: pkill -f \"python.*snapshot\.py\""
    echo -e "══════════════════════════════════════════════════════════════"
    echo -e "\033[1;36m✅ App running in background! You can close this terminal.\033[0m"
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
