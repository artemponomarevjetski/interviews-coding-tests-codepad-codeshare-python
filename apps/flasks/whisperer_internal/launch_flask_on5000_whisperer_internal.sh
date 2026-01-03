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

  # Clean & recreate venv
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
  
  # CRITICAL FIX: Handle LLVM version conflicts for llvmlite
  echo "Handling LLVM version for llvmlite compatibility..."
  
  # Check and uninstall LLVM 21 if it exists (this is the key fix)
  if brew list --versions llvm >/dev/null 2>&1; then
    LLVM_VERSION=$(brew info llvm | grep -o '^llvm: .*' | cut -d' ' -f2 | head -1)
    if [[ "$LLVM_VERSION" == 21* ]]; then
      echo "Found LLVM $LLVM_VERSION - uninstalling to avoid conflicts with llvmlite..."
      brew uninstall llvm
    fi
  fi
  
  # Ensure LLVM 20 is installed
  if ! brew list --versions llvm@20 >/dev/null 2>&1; then
    echo "Installing LLVM 20 (required for llvmlite)..."
    brew install llvm@20
  fi
  
  # CRITICAL: Set environment variables BEFORE installing llvmlite
  # This ensures CMake finds the right LLVM version
  export LLVM_CONFIG="/usr/local/opt/llvm@20/bin/llvm-config"
  export PATH="/usr/local/opt/llvm@20/bin:$PATH"
  export LDFLAGS="-L/usr/local/opt/llvm@20/lib"
  export CPPFLAGS="-I/usr/local/opt/llvm@20/include"
  
  # Clear any existing CMake cache variables that might point to wrong LLVM
  unset CMAKE_PREFIX_PATH
  unset LLVM_DIR
  
  # Install llvmlite with explicit LLVM_CONFIG (this was the key that worked)
  echo "Installing llvmlite with LLVM 20..."
  LLVM_CONFIG=/usr/local/opt/llvm@20/bin/llvm-config pip install llvmlite==0.46.0
  
  # Install numba (requires llvmlite)
  echo "Installing numba..."
  pip install numba==0.63.1
  
  # Now install Flask and audio dependencies
  echo "Installing Flask and audio dependencies..."
  pip install Flask==2.3.2 numpy==1.26.4 sounddevice==0.4.6
  
  # Install whisper without pulling in its dependencies (we already have them)
  echo "Installing whisper..."
  pip install --no-deps openai-whisper==20231117
  
  # Install whisper's additional dependencies
  echo "Installing whisper dependencies..."
  pip install tiktoken regex tqdm more-itertools

  # Fallback option: if llvmlite installation fails, use faster-whisper
  if ! python -c "import llvmlite" 2>/dev/null; then
    echo "Warning: llvmlite installation may have failed, trying faster-whisper fallback..."
    pip uninstall -y openai-whisper numba llvmlite 2>/dev/null || true
    pip install faster-whisper
    echo "Using faster-whisper instead of openai-whisper"
  fi

  # Comprehensive smoke test
  echo "Running comprehensive smoke test..."
  
  # Test basic imports
  if python -c "import flask, torch; print('✅ Flask and torch imports successful')"; then
    # Test whisper import (original or faster-whisper)
    if python -c "import whisper" 2>/dev/null; then
      echo "✅ Original whisper import successful"
      # Test actual model loading
      if python -c "import whisper; model = whisper.load_model('base'); print('✅ Whisper model loaded successfully')"; then
        echo "✅ Whisper setup complete"
      else
        echo "⚠️  Whisper model loading failed, but imports work"
      fi
    elif python -c "from faster_whisper import WhisperModel" 2>/dev/null; then
      echo "✅ Faster-whisper import successful"
      if python -c "from faster_whisper import WhisperModel; model = WhisperModel('base', device='cpu', compute_type='int8'); print('✅ Faster-whisper model loaded successfully')"; then
        echo "✅ Faster-whisper setup complete"
      else
        echo "⚠️  Faster-whisper model loading failed, but imports work"
      fi
    else
      echo "⚠️  Could not import any whisper package"
      echo "⚠️  Transcription may not work, but web server will run"
    fi
  else
    echo "❌ Critical setup failed - Flask or torch not installed"
    exit 1
  fi

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
  echo
  echo "✅ Setup complete! Open http://localhost:${PORT} in your browser"
  echo "💡 Speak numbers like 'one two three' to test transcription"
} 2>&1 | tee -a "$SERVICE_LOG"
