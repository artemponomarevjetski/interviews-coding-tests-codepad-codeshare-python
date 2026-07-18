#!/usr/bin/env bash
#
# +----------------------------------------------------------+
# |                                                          |
# |     WHISPERER-INTERNAL  –  MICROPHONE TRANSCRIPTION      |
# |                                                          |
# |  • Uses faster-whisper – no llvmlite/numba headaches     |
# |  • Listens to your built-in microphone                   |
# |  • Shows real-time transcriptions on the web interface   |
# |  • Kills all previous instances before starting          |
# |  • Runs in background, survives terminal closure         |
# |  • Includes a troubleshooter script for audio diagnostics|
# +----------------------------------------------------------+

set -Eeuo pipefail

# --- Configuration ------------------------------------------------------------
PORT=5000
VENV_DIR="venv"
PID_FILE="whisperer.pid"
LOG_RETENTION_DAYS=7
APP_PY="whisperer-internal.py"

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

cleanup_previous_instances() {
    log "${YELLOW}🧹 Cleaning up previous instances...${NC}"

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
    log "   Checking port $PORT..."
    PIDS=$(lsof -ti :"$PORT" 2>/dev/null || true)
    if [[ -n "$PIDS" ]]; then
        log "   Found processes on port $PORT: $PIDS"
        for PID in $PIDS; do
            if kill -0 "$PID" 2>/dev/null; then
                kill -9 "$PID" 2>/dev/null || true
            fi
        done
        sleep 1
        # Verify port is free
        if lsof -ti :"$PORT" >/dev/null 2>&1; then
            log "${YELLOW}⚠️  Could not free port $PORT. Please kill manually.${NC}"
            return 1
        else
            log "${GREEN}✅ Port $PORT is free.${NC}"
        fi
    else
        log "${GREEN}✅ Port $PORT is already free.${NC}"
    fi

    # Kill any Python processes matching "whisperer" (previous instances)
    pkill -f "python.*whisperer" 2>/dev/null || true
    pkill -f "python.*$APP_PY" 2>/dev/null || true

    log "${GREEN}✅ Cleanup complete.${NC}"
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

echo -e "${CYAN}"
echo "+----------------------------------------------------------+"
echo "|                                                          |"
echo "|     WHISPERER-INTERNAL  –  MICROPHONE TRANSCRIPTION      |"
echo "|                                                          |"
echo "|  • Uses faster-whisper – no llvmlite/numba headaches     |"
echo "|  • Listens to your built-in microphone                   |"
echo "|  • Shows real-time transcriptions on the web interface   |"
echo "|  • Kills all previous instances before starting          |"
echo "|  • Runs in background, survives terminal closure         |"
echo "|  • Includes a troubleshooter script for audio diagnostics|"
echo "+----------------------------------------------------------+"
echo -e "${NC}"
log "Starting Whisperer‑INTERNAL Launcher"

# -----------------------------------------------------------------------------
# 1. Cleanup previous instances
# -----------------------------------------------------------------------------
cleanup_previous_instances || {
    log "${RED}❌ Cleanup failed. Exiting.${NC}"
    exit 1
}

# -----------------------------------------------------------------------------
# 2. Ensure Homebrew and required system packages
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
# 3. Virtual environment setup
# -----------------------------------------------------------------------------
log "Creating virtual environment…"
rm -rf "$VENV_DIR"
"$PY311" -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

log "Upgrading pip and setuptools…"
python -m pip install --upgrade pip setuptools wheel

# -----------------------------------------------------------------------------
# 4. Install dependencies (with faster‑whisper)
# -----------------------------------------------------------------------------
log "Installing core dependencies (Flask, numpy, sounddevice)…"
pip install Flask==2.3.2 numpy==1.26.4 sounddevice==0.4.6

log "Installing faster‑whisper (no llvmlite/numba needed)…"
pip install faster-whisper

# -----------------------------------------------------------------------------
# 5. Smoke test – verify imports
# -----------------------------------------------------------------------------
log "Running smoke test…"
if python -c "import flask, numpy, sounddevice; print('✅ Core imports OK')"; then
    if python -c "from faster_whisper import WhisperModel; print('✅ faster-whisper import OK')"; then
        log "${GREEN}✅ All dependencies installed successfully.${NC}"
    else
        log "${RED}❌ faster-whisper import failed.${NC}"
        exit 1
    fi
else
    log "${RED}❌ Core dependency import failed.${NC}"
    exit 1
fi

# -----------------------------------------------------------------------------
# 6. Purge old transcripts (log rotation)
# -----------------------------------------------------------------------------
purge_old_transcripts

# -----------------------------------------------------------------------------
# 7. Launch the app in the background
# -----------------------------------------------------------------------------
log "Starting Whisperer service on http://localhost:${PORT} …"
nohup bash -lc "source venv/bin/activate && python -u $APP_PY" \
    >> "$FLASK_LOG" 2>&1 &

APP_PID=$!
echo "$APP_PID" > "$PID_FILE"

sleep 2
if ps -p "$APP_PID" >/dev/null 2>&1; then
    log "${GREEN}✅ Whisperer started (PID $APP_PID)${NC}"
    echo -e "\n${GREEN}🎤✅ Setup complete! Open http://localhost:${PORT} in your browser${NC}"
    echo -e "   Speak numbers like 'one two three' to test transcription."
    echo -e "   📝 Logs: tail -f $FLASK_LOG"
    echo -e "   🛑 Stop: pkill -f $APP_PY"
    echo -e "   🔧 Troubleshoot: python troubleshooter.py"
else
    log "${RED}❌ Whisperer failed to start. Check $FLASK_LOG${NC}"
    exit 1
fi

log "Launcher finished."
exit 0
