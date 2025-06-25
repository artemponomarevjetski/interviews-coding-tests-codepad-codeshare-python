#!/bin/bash

# ==============================================
# ULTIMATE FLASK LAUNCHER WITH PERMISSION CHECKS
# ==============================================

# --- Initialization ---
set -euo pipefail  # Enable strict error handling

# Activate virtual environment if exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# --- Cleanup ---
echo -e "\n\033[1;34m🛑 Killing existing processes...\033[0m"
pkill -f "python.*snapshot\.py" 2>/dev/null || true
lsof -ti :5000 | xargs -r kill -9 2>/dev/null || true

# --- Directories Setup ---
BASE_DIR=~/interviews-coding-tests-codepad-codeshare-python
LOG_DIR="$BASE_DIR/log"
TEMP_DIR="$BASE_DIR/temp"

mkdir -p "$LOG_DIR" "$TEMP_DIR"
touch "$LOG_DIR/flask.log"

# --- Permission Check with Fallbacks ---
echo -e "\n\033[1;34m🔍 Checking screen capture permissions...\033[0m"
TEST_FILE="$TEMP_DIR/screencapture_test_$(date +%s).png"
PERMISSION_FIXED=0

# Try multiple capture methods with timeout
for method in "-l" "" "-m"; do
    timeout 5 screencapture -x $method -o "$TEST_FILE" 2>/dev/null && \
    [ -s "$TEST_FILE" ] && \
    PERMISSION_FIXED=1 && \
    rm "$TEST_FILE" && \
    break
done

if [ "$PERMISSION_FIXED" -eq 0 ]; then
    echo -e "\n\033[1;31m❌ SCREEN CAPTURE FAILED\033[0m"
    echo -e "\n\033[1;33m🔧 REQUIRED FIX:\033[0m"
    echo "1. Open System Settings → Privacy & Security → Screen Recording"
    echo "2. REMOVE Terminal/iTerm from the list"
    echo "3. Click the 🔄 button in the bottom right corner"
    echo "4. RE-ADD your terminal app"
    echo "5. RESTART the terminal completely"
    echo -e "\n\033[1;36m💡 TIP: Try right-clicking your terminal app and selecting 'Open' if using a non-App Store version.\033[0m"
    exit 1
fi

# --- Python Environment Setup ---
echo -e "\n\033[1;34m🐍 Setting up Python environment...\033[0m"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install pillow pytesseract flask pyobjc-framework-Quartz
else
    source venv/bin/activate
    pip install -r requirements.txt 2>/dev/null || true
fi

# --- Network Configuration ---
IP=$(ipconfig getifaddr en0 || ipconfig getifaddr en1 || echo "127.0.0.1")
echo -e "\n\033[1;34m🌐 Network configuration:\033[0m"
echo "Local IP: $IP"
echo "Port: 5000"

# --- Application Launch ---
echo -e "\n\033[1;34m🚀 Launching Flask application...\033[0m"
nohup python3 -u snapshot.py --fallback > "$LOG_DIR/flask.log" 2>&1 &
FLASK_PID=$!
disown $FLASK_PID

# --- Startup Verification ---
echo -e "\n\033[1;34m🔍 Verifying startup...\033[0m"
for i in {1..5}; do
    if curl -s "http://localhost:5000" >/dev/null; then
        break
    fi
    sleep 1
done

if ! curl -s "http://localhost:5000" >/dev/null; then
    echo -e "\n\033[1;31m❌ Startup failed! Last 20 log lines:\033[0m"
    tail -n 20 "$LOG_DIR/flask.log"
    echo -e "\n\033[1;33m🔄 Attempting to restart...\033[0m"
    kill $FLASK_PID 2>/dev/null || true
    nohup python3 -u snapshot.py --fallback > "$LOG_DIR/flask.log" 2>&1 &
    disown
    sleep 2
    if ! curl -s "http://localhost:5000" >/dev/null; then
        exit 1
    fi
fi

# --- Final Status ---
echo -e "\n\033[1;32m✅ System is operational!\033[0m"
echo -e "\033[1;36m🔍 Monitor with:\033[0m tail -f \"$LOG_DIR/flask.log\""
echo -e "\033[1;36m🌐 Dashboard:\033[0m http://$IP:5000"
echo -e "\033[1;36m🛑 To stop:\033[0m pkill -f \"python.*snapshot\.py\""

exit 0
