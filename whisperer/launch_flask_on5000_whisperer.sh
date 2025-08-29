#!/usr/bin/env bash
set -euo pipefail

# --- Configuration ---
PORT=5000
VENV_DIR="venv"
PID_FILE="whisperer.pid"
LOG_RETENTION_DAYS=7

# --- Log File Paths ---
LOG_DIR="logs"
SERVICE_LOG="$LOG_DIR/service.log"
FLASK_LOG="$LOG_DIR/flask_app.log"
TRANSCRIPT_LOG="$LOG_DIR/transcriptions.log"
RECENT_TRANSCRIPT_LOG="$LOG_DIR/recent_transcriptions.log"

mkdir -p "$LOG_DIR"
touch "$SERVICE_LOG" "$FLASK_LOG" "$TRANSCRIPT_LOG" "$RECENT_TRANSCRIPT_LOG"

# --- Functions ---
purge_old_transcripts() {
  if [ -s "$TRANSCRIPT_LOG" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Purging transcript logs older than $LOG_RETENTION_DAYS days" >> "$SERVICE_LOG"
    temp_file=$(mktemp)
    cutoff_date=$(date -v-"${LOG_RETENTION_DAYS}"d +%s)

    while IFS= read -r line; do
      if [[ "$line" =~ ^\[(.*)\].* ]]; then
        log_date=$(date -j -f "%Y-%m-%d %H:%M:%S" "${BASH_REMATCH[1]}" +%s 2>/dev/null)
        if [ -n "$log_date" ] && [ "$log_date" -gt "$cutoff_date" ]; then
          echo "$line"
        fi
      fi
    done < "$TRANSCRIPT_LOG" > "$temp_file"

    mv "$temp_file" "$TRANSCRIPT_LOG"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Transcript log cleaned" >> "$SERVICE_LOG"
  else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] No existing transcript log entries to purge" >> "$SERVICE_LOG"
  fi
}

free_port() {
  echo -e "\n[$(date '+%Y-%m-%d %H:%M:%S')] Attempting to free port $PORT..." >> "$SERVICE_LOG"
  local pids
  pids=$(lsof -ti :$PORT || true)
  if [ -n "${pids}" ]; then
    echo "Found processes using port $PORT: $pids" >> "$SERVICE_LOG"
    kill -9 $pids || true
    sleep 1
    if lsof -ti :$PORT >/dev/null 2>&1; then
      echo "Failed to free port $PORT" >> "$SERVICE_LOG"
      return 1
    else
      echo "Successfully freed port $PORT" >> "$SERVICE_LOG"
      return 0
    fi
  else
    echo "No processes found using port $PORT" >> "$SERVICE_LOG"
    return 0
  fi
}

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$SERVICE_LOG" ; }

# --- Main ---
{
  echo
  log "Starting Whisper Service Launcher"
  echo "=============================================="

  # Ensure Homebrew + deps
  if ! command -v brew >/dev/null 2>&1; then
    log "Homebrew not found. Install from https://brew.sh and rerun."
    exit 1
  fi
  brew list --versions python@3.11 >/dev/null 2>&1 || brew install python@3.11
  brew list --versions portaudio   >/dev/null 2>&1 || brew install portaudio

  PY311="$(brew --prefix)/bin/python3.11"
  if [ ! -x "$PY311" ]; then
    log "python3.11 not found at $PY311"
    exit 1
  fi

  # Port handling
  echo
  echo "Checking port $PORT..."
  if lsof -i :$PORT >/dev/null 2>&1; then
    echo "Port $PORT is in use - attempting to free it..."
    if ! free_port; then
      echo "Could not free port $PORT. Please close it manually."
      exit 1
    fi
  fi

  # Stop previous instance by PID if present
  if [ -f "$PID_FILE" ]; then
    if ps -p "$(cat "$PID_FILE")" >/dev/null 2>&1; then
      echo "Stopping prior whisperer (PID $(cat "$PID_FILE"))..."
      kill -9 "$(cat "$PID_FILE")" || true
    fi
    rm -f "$PID_FILE"
  fi

  # Clean & recreate venv (per your request)
  echo
  echo "Recreating virtual environment…"
  rm -rf "$VENV_DIR"
  "$PY311" -m venv "$VENV_DIR"
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"

  # Toolchain + pins
  python -m pip install --upgrade pip setuptools wheel

  # Requirements as requested
  printf "Flask==2.3.2\nnumpy==1.26.4\nsounddevice==0.4.6\nopenai-whisper==20231117\n" > requirements.txt

  # Install Torch CPU first, then the rest
  pip install torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu
  pip install -r requirements.txt

  # Smoke test
  python -c "import flask, torch, whisper; print('ok')"

  # Purge old transcripts
  purge_old_transcripts

  # Launch app in the background (survives terminal close)
  echo
  echo "Starting Whisperer service on http://localhost:${PORT} …"
  nohup bash -lc 'source venv/bin/activate; python -u whisperer.py' \
      >> "$FLASK_LOG" 2>&1 &

  echo $! > "$PID_FILE"
  echo "PID $(cat "$PID_FILE")"
  echo "Logs: tail -f $FLASK_LOG"
} 2>&1 | tee -a "$SERVICE_LOG"
