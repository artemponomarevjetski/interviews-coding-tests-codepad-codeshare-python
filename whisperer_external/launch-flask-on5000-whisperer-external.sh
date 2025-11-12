#!/usr/bin/env bash
set -euo pipefail

# --- Configuration ---
PORT=5000
VENV_DIR="venv"
PID_FILE="whisperer.pid"
LOG_RETENTION_DAYS=7
MODE="EXTERNAL"

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

audio_device_check() {
  echo -e "\n[$(date '+%Y-%m-%d %H:%M:%S')] Running audio device checks..." >> "$SERVICE_LOG"
  
  if [ -f "$VENV_DIR/bin/python" ]; then
    echo "=== AUDIO DEVICE CHECK ===" | tee -a "$SERVICE_LOG"
    
    # List all audio devices
    "$VENV_DIR/bin/python" -c "
import sounddevice as sd
try:
    devices = sd.query_devices()
    print('INPUT DEVICES (for microphone):')
    input_count = 0
    for i, dev in enumerate(devices):
        if dev['max_input_channels'] > 0:
            input_count += 1
            default_input = sd.default.device[0] if sd.default.device else None
            default_indicator = ' (DEFAULT INPUT)' if i == default_input else ''
            print(f'  {i}: {dev[\"name\"]}{default_indicator}')
    
    print('\nOUTPUT DEVICES (for headphones):')
    output_count = 0
    for i, dev in enumerate(devices):
        if dev['max_output_channels'] > 0:
            output_count += 1
            default_output = sd.default.device[1] if sd.default.device else None
            default_indicator = ' (DEFAULT OUTPUT)' if i == default_output else ''
            print(f'  {i}: {dev[\"name\"]}{default_indicator}')
    
    print(f'\nSUMMARY: {input_count} input device(s), {output_count} output device(s)')
    
    # Check for BlackHole device
    blackhole_found = any('blackhole' in dev['name'].lower() for dev in devices)
    if blackhole_found:
        print('✅ BlackHole device found for system audio capture')
    else:
        print('❌ BlackHole device not found - install BlackHole 2ch')
        print('   Download from: https://existential.audio/blackhole/')
        
    # Check for external microphone
    external_mic_found = any('external' in dev['name'].lower() for dev in devices if dev['max_input_channels'] > 0)
    if external_mic_found:
        print('✅ External microphone detected')
    else:
        print('⚠️  No external microphone found - check connection')
        
except Exception as e:
    print(f'❌ Audio device check failed: {e}')
" 2>&1 | tee -a "$SERVICE_LOG"

    # Test microphone functionality
    echo -e "\nTesting microphone recording..." | tee -a "$SERVICE_LOG"
    "$VENV_DIR/bin/python" -c "
import sounddevice as sd
import numpy as np

try:
    # Find external microphone first, then fallback
    devices = sd.query_devices()
    input_devices = []
    
    for i, dev in enumerate(devices):
        if dev['max_input_channels'] > 0:
            if 'external' in dev['name'].lower():
                input_devices.insert(0, i)  # Prefer external mics
            else:
                input_devices.append(i)
    
    if not input_devices:
        print('❌ No input devices found!')
        print('   Microphone may not work in the app')
    else:
        device_id = input_devices[0]
        device_name = devices[device_id]['name']
        print(f'Testing microphone: {device_name} (ID: {device_id})')
        print('Recording 3 seconds... Speak into your microphone now!')
        
        # Record 3 seconds of audio
        duration = 3
        sample_rate = 16000
        recording = sd.rec(int(duration * sample_rate), 
                          samplerate=sample_rate, 
                          channels=1, 
                          device=device_id, 
                          dtype='float32')
        sd.wait()
        
        max_amplitude = float(np.max(np.abs(recording)))
        print(f'Max audio amplitude: {max_amplitude:.4f}')
        
        if max_amplitude > 0.02:
            print('✅ Microphone test PASSED - Good audio levels detected')
        elif max_amplitude > 0.005:
            print('⚠️  Microphone test WARNING - Low audio levels detected')
            print('   Speak louder or check microphone settings')
        else:
            print('❌ Microphone test FAILED - No audio detected')
            print('   Microphone may not work in the app')
            print('   Check: System Settings > Privacy & Security > Microphone')
            print('   Ensure Terminal has microphone access')
            
except Exception as e:
    print(f'❌ Microphone test error: {e}')
    print('   App will start anyway - test microphone in web interface')
" 2>&1 | tee -a "$SERVICE_LOG"
    
    # Always return success so the app starts anyway
    return 0
  else
    echo "Virtual environment not found - skipping audio checks" | tee -a "$SERVICE_LOG"
    return 0
  fi
}

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$SERVICE_LOG" ; }

# --- Main ---
{
  echo
  log "Starting DUAL AUDIO Transcription Service (External + System Audio)"
  echo "=================================================================="

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

  # Clean & recreate venv (only if needed)
  if [ ! -d "$VENV_DIR" ] || [ ! -f "$VENV_DIR/bin/python" ]; then
    echo
    echo "Setting up virtual environment…"
    rm -rf "$VENV_DIR"
    "$PY311" -m venv "$VENV_DIR"
  fi

  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"

  # Install dependencies if needed
  if ! "$VENV_DIR/bin/python" -c "import flask, torch, whisper, sounddevice" &>/dev/null; then
    echo "Installing dependencies..."
    python -m pip install --upgrade pip setuptools wheel

    # Requirements
    printf "Flask==2.3.2\nnumpy==1.26.4\nsounddevice==0.4.6\nopenai-whisper==20231117\n" > requirements.txt

    # Install Torch CPU first, then the rest
    pip install torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu
    pip install -r requirements.txt

    # Smoke test
    python -c "import flask, torch, whisper, sounddevice; print('✅ Dependencies installed successfully')"
  fi

  # Run comprehensive audio device checks (show warnings but don't exit)
  echo
  echo "Running comprehensive audio device checks..."
  audio_device_check
  echo "⚠️  Note: App will start regardless of audio check results"
  echo "   Test microphone and system audio directly in the web interface"

  # Purge old transcripts
  purge_old_transcripts

  # Launch app in the background (survives terminal close)
  echo
  echo "Starting DUAL AUDIO transcription service on http://localhost:${PORT} …"
  echo "MODE: External Microphone + System Audio via BlackHole"
  echo "App starting - check web interface for actual functionality"
  
  # FIXED: Using correct filename whisperer-external.py
  nohup bash -lc 'source venv/bin/activate; python -u whisperer-external.py' \
      >> "$FLASK_LOG" 2>&1 &

  echo $! > "$PID_FILE"
  echo "PID $(cat "$PID_FILE")"
  echo "Logs: tail -f $FLASK_LOG"
  echo
  echo "🎤🎧 DUAL AUDIO Transcription service started!"
  echo "   Web interface: http://localhost:5000"
  echo "   Monitoring: External Microphone + System Audio"
  echo "   Set System Audio Output to BlackHole 2ch for YouTube capture"
  echo "   If no transcriptions appear, check audio permissions and BlackHole setup"
} 2>&1 | tee -a "$SERVICE_LOG"