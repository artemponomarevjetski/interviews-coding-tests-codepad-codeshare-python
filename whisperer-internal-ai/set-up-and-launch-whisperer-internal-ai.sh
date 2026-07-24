#!/usr/bin/env bash
#
# +----------------------------------------------------------+
# |                                                          |
# |     WHISPERER-INTERNAL  –  MICROPHONE TRANSCRIPTION      |
# |                                                          |
# |  • Uses faster-whisper – no llvmlite/numba headaches     |
# |  • Listens to your built-in microphone                   |
# |  • Shows real-time transcriptions on the web interface   |
# |  • Kills previous instances only if you say Yes          |
# |  • If you say No, it checks port availability           |
# |  • Runs in background, survives terminal closure         |
# |  • Includes a troubleshooter script for audio diagnostics|
# |  • Bundles transcribed text and sends to OpenAI async    |
# |  • Continues transcription while waiting for OpenAI      |
# |  • Injects API responses into the webpage on the fly     |
# +----------------------------------------------------------+

set -Eeuo pipefail

# --- ASCII HEADER (WHISPERER) ------------------------------------------------
echo -e "\033[1;36m"
cat << "EOF"
 ██╗    ██╗██╗  ██╗██╗███████╗██████╗ ███████╗██████╗ 
 ██║    ██║██║  ██║██║██╔════╝██╔══██╗██╔════╝██╔══██╗
 ██║ █╗ ██║███████║██║███████╗██████╔╝█████╗  ██████╔╝
 ██║███╗██║██╔══██║██║╚════██║██╔══██╗██╔══╝  ██╔══██╗
 ╚███╔███╔╝██║  ██║██║███████║██║  ██║███████╗██║  ██║
  ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
EOF
echo -e "\033[0m"
echo -e "\033[1;34m  🎤  Whisperer‑Internal  –  Microphone Transcription  🎤\033[0m"
echo -e "\033[1;36m        Real‑time speech‑to‑text + Async OpenAI AI\033[0m"
echo ""

# --- Configuration ------------------------------------------------------------
PORT=5000
VENV_DIR="venv"
PID_FILE="whisperer.pid"
LOG_RETENTION_DAYS=7
APP_PY="whisperer-internal-ai.py"   # asynchronous prompt responder

# --- Log File Paths -----------------------------------------------------------
LOG_DIR="logs"
SERVICE_LOG="$LOG_DIR/service.log"
FLASK_LOG="$LOG_DIR/flask_app.log"
TRANSCRIPT_LOG="$LOG_DIR/transcriptions.log"
RECENT_TRANSCRIPT_LOG="$LOG_DIR/recent_transcriptions.log"

mkdir -p "$LOG_DIR"
touch "$SERVICE_LOG" "$FLASK_LOG" "$TRANSCRIPT_LOG" "$RECENT_TRANSCRIPT_LOG"

# --- Colour codes for better UX ----------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Colour

# --- Functions ----------------------------------------------------------------
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$SERVICE_LOG"
}

# ---------------------------------------------------------------------------
# 1. Cleanup previous instances – WITH USER CONFIRMATION
# ---------------------------------------------------------------------------
# Global flag: 1 if we killed, 0 if we skipped or no instance found
KILLED=0

cleanup_previous_instances() {
    log "${YELLOW}🧹 Checking for previous Whisperer instances...${NC}"

    # Check for PID file
    local old_pid=""
    if [[ -f "$PID_FILE" ]]; then
        old_pid=$(cat "$PID_FILE" 2>/dev/null || echo "")
    fi

    # Check for processes using the port
    local port_pids=$(lsof -ti :"$PORT" 2>/dev/null || true)

    # Check for any running whisperer python processes
    local whisperer_pids=$(pgrep -f "python.*whisperer" 2>/dev/null || true)
    local app_pids=$(pgrep -f "python.*$APP_PY" 2>/dev/null || true)

    # Combine all found processes
    local all_pids="$old_pid $port_pids $whisperer_pids $app_pids"
    # Remove duplicates and empty
    all_pids=$(echo "$all_pids" | tr ' ' '\n' | sort -u | grep -v '^$' | tr '\n' ' ')

    if [[ -n "$all_pids" ]]; then
        echo -e "${YELLOW}⚠️  Found a running Whisperer app:${NC}"
        if [[ -n "$old_pid" ]]; then
            echo "   PID file: $PID_FILE -> PID $old_pid"
        fi
        if [[ -n "$port_pids" ]]; then
            echo "   Port $PORT in use by PIDs: $port_pids"
        fi
        if [[ -n "$whisperer_pids" ]]; then
            echo "   Whisperer processes: $whisperer_pids"
        fi
        if [[ -n "$app_pids" ]]; then
            echo "   $APP_PY processes: $app_pids"
        fi

        read -p "Do you want to kill the previous Whisperer app and restart? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}🔄 Killing previous instances...${NC}"
            # Kill by PID file
            if [[ -f "$PID_FILE" ]]; then
                OLD_PID=$(cat "$PID_FILE" 2>/dev/null || echo "")
                if [[ -n "$OLD_PID" ]] && ps -p "$OLD_PID" >/dev/null 2>&1; then
                    log "   Killing previous whisperer (PID $OLD_PID)"
                    kill -9 "$OLD_PID" 2>/dev/null || true
                fi
                rm -f "$PID_FILE"
            fi

            # Kill any process using the port
            if [[ -n "$port_pids" ]]; then
                log "   Killing processes on port $PORT: $port_pids"
                kill -9 $port_pids 2>/dev/null || true
            fi

            # Kill any Python processes matching "whisperer"
            pkill -f "python.*whisperer" 2>/dev/null || true
            pkill -f "python.*$APP_PY" 2>/dev/null || true

            sleep 1
            log "${GREEN}✅ Cleanup complete.${NC}"
            KILLED=1
        else
            echo -e "${YELLOW}⏭️  Skipping kill. Will check if port $PORT is free.${NC}"
            KILLED=0
        fi
    else
        echo -e "${GREEN}✅ No previous Whisperer instance found.${NC}"
        KILLED=0
    fi
    return 0
}

purge_old_transcripts() {
    if [[ -s "$TRANSCRIPT_LOG" ]]; then
        log "Purging transcript logs older than $LOG_RETENTION_DAYS days..."
        temp_file=$(mktemp)
        cutoff_date=$(date -v-"${LOG_RETENTION_DAYS}"d +%s)

        while IFS= read -r line; do
            if [[ "$line" =~ ^\[(.*)\].* ]]; then
                log_date=$(date -j -f "%Y-%m-%d %H:%M:%S" "${BASH_REMATCH[1]}" +%s 2>/dev/null)
                if [[ -n "$log_date" ]] && [[ "$log_date" -gt "$cutoff_date" ]]; then
                    echo "$line"
                fi
            fi
        done < "$TRANSCRIPT_LOG" > "$temp_file"

        mv "$temp_file" "$TRANSCRIPT_LOG"
        log "Transcript log cleaned."
    else
        log "No existing transcript log entries to purge."
    fi
}

# =============================================================================
#  MAIN
# =============================================================================

log "Starting Whisperer‑INTERNAL Launcher"

# -----------------------------------------------------------------------------
# 1. Cleanup previous instances (with confirmation – may skip)
# -----------------------------------------------------------------------------
cleanup_previous_instances || {
    # This should never happen because we always return 0, but keep for safety
    log "${RED}❌ Cleanup encountered an unexpected error. Exiting.${NC}"
    exit 1
}

# -----------------------------------------------------------------------------
# 2. Check port availability if we didn't kill
# -----------------------------------------------------------------------------
if [[ $KILLED -eq 0 ]] && lsof -ti :"$PORT" >/dev/null 2>&1; then
    echo -e "${RED}❌ Port $PORT is still in use by another process.${NC}"
    echo -e "${RED}   You chose not to kill the previous instance, but the port is occupied.${NC}"
    echo -e "${RED}   Please stop the other process manually, or kill it and restart.${NC}"
    log "${RED}❌ Port $PORT busy – aborting start.${NC}"
    exit 1
fi

# -----------------------------------------------------------------------------
# 3. Ensure Homebrew and required system packages
# -----------------------------------------------------------------------------
if ! command -v brew &> /dev/null; then
    log "${RED}❌ Homebrew not found. Install from https://brew.sh and rerun.${NC}"
    exit 1
fi

brew list --versions python@3.11 >/dev/null 2>&1 || brew install python@3.11
brew list --versions portaudio   >/dev/null 2>&1 || brew install portaudio

PY311="$(brew --prefix)/bin/python3.11"
if [[ ! -x "$PY311" ]]; then
    log "${RED}❌ python3.11 not found at $PY311${NC}"
    exit 1
fi

# -----------------------------------------------------------------------------
# 4. Virtual environment setup
# -----------------------------------------------------------------------------
log "Creating virtual environment…"
rm -rf "$VENV_DIR"
"$PY311" -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

log "Upgrading pip and setuptools…"
python -m pip install --upgrade pip setuptools wheel

# -----------------------------------------------------------------------------
# 5. Install dependencies from requirements.txt (includes openai & dotenv)
# -----------------------------------------------------------------------------
log "Installing dependencies from requirements.txt…"
pip install -r requirements.txt

# -----------------------------------------------------------------------------
# 6. Smoke test – verify imports (including openai and dotenv)
# -----------------------------------------------------------------------------
log "Running smoke test…"
if python -c "import flask, numpy, sounddevice, dotenv, openai; print('✅ Core + OpenAI imports OK')"; then
    if python -c "from faster_whisper import WhisperModel; print('✅ faster-whisper import OK')"; then
        log "${GREEN}✅ All dependencies installed successfully.${NC}"
    else
        log "${RED}❌ faster-whisper import failed.${NC}"
        exit 1
    fi
else
    log "${RED}❌ Core dependency import failed (missing openai or dotenv?).${NC}"
    exit 1
fi

# -----------------------------------------------------------------------------
# 7. Purge old transcripts (log rotation)
# -----------------------------------------------------------------------------
purge_old_transcripts

# -----------------------------------------------------------------------------
# 8. Launch the app in the background
# -----------------------------------------------------------------------------
log "Starting Whisperer service on http://localhost:${PORT} …"
nohup bash -lc "source venv/bin/activate && python -u $APP_PY" \
    >> "$FLASK_LOG" 2>&1 &

APP_PID=$!
echo "$APP_PID" > "$PID_FILE"

sleep 2
if ps -p "$APP_PID" >/dev/null 2>&1; then
    log "${GREEN}✅ Whisperer started (PID $APP_PID)${NC}"
    echo -e "\n${GREEN}🎤✅ Setup complete! Open http://localhost:${PORT} or http://192.168.1.167:5000 in your browser${NC}"
    echo -e "   Speak numbers like 'one two three' to test transcription."
    echo -e "   📝 Logs: tail -f $FLASK_LOG"
    echo -e "   🛑 Stop: pkill -f $APP_PY"
    echo -e "   🔧 Troubleshoot: python troubleshooter.py"

    # Auto-close terminal (macOS only) after successful launch
    if [[ "$OSTYPE" == "darwin"* ]]; then
        osascript -e 'tell application "Terminal" to close (first window whose frontmost is true)' &
    fi
    exit 0
else
    log "${RED}❌ Whisperer failed to start. Check $FLASK_LOG${NC}"
    exit 1
fi

log "Launcher finished."
exit 0