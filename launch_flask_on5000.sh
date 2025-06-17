#!/bin/bash

# ==============================================
# ULTIMATE FLASK LAUNCHER WITH PERMISSION CHECKS
# ==============================================

# --- Cleanup ---
echo "🛑 Killing existing processes..."
pkill -f "python.*snapshot\.py" 2>/dev/null
lsof -ti :5000 | xargs -r kill -9 2>/dev/null

# --- Directories ---
BASE_DIR=~/interviews-coding-tests-codepad-codeshare-python
mkdir -p $BASE_DIR/{temp,log}

# --- Permission Check with Fallbacks ---
TEST_FILE="/tmp/screencapture_test_$(date +%s).png"
PERMISSION_FIXED=0

# Try multiple capture methods
for method in "-l" "" "-m"; do
    screencapture -x $method -o "$TEST_FILE" 2>/dev/null
    if [ -s "$TEST_FILE" ]; then
        PERMISSION_FIXED=1
        rm "$TEST_FILE"
        break
    fi
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

# --- Python Setup ---
if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install pillow pytesseract flask pyobjc-framework-Quartz
else
    source venv/bin/activate
fi

# --- Launch with Quartz Fallback ---
IP=$(ipconfig getifaddr en0 || ipconfig getifaddr en1 || echo "127.0.0.1")
echo "🚀 Starting Flask app on http://$IP:5000"

# Run with enhanced error handling
nohup python3 -u snapshot.py --fallback > $BASE_DIR/log/flask.log 2>&1 &
disown

# Verify startup
sleep 2
if ! curl -s "http://localhost:5000" >/dev/null; then
    echo -e "\n\033[1;31m❌ Startup failed! Check logs:\033[0m"
    tail -n 20 $BASE_DIR/log/flask.log
    exit 1
fi

echo -e "\n\033[1;32m✅ System is operational!\033[0m"
echo "🔍 Monitor with: tail -f $BASE_DIR/log/flask.log"
echo "🌐 Dashboard: http://$IP:5000"
