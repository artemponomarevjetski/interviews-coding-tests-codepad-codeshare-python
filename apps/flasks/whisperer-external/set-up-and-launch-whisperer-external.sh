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
setup_multi_output_device() {
  echo -e "\n[$(date '+%Y-%m-%d %H:%M:%S')] Setting up Multi-Output Audio Device..." >> "$SERVICE_LOG"
  
  echo "🎧 Setting up Multi-Output Device for simultaneous audio capture and playback..." | tee -a "$SERVICE_LOG"
  
  # First, ensure BlackHole is installed
  if ! brew list --cask | grep -q blackhole; then
    echo "Installing BlackHole 2ch..." | tee -a "$SERVICE_LOG"
    brew install --cask blackhole
  fi
  
  # Create Multi-Output Device using AppleScript
  echo "Creating Multi-Output Device..." | tee -a "$SERVICE_LOG"
  
  osascript <<'EOF' 2>&1 | tee -a "$SERVICE_LOG"
tell application "Audio MIDI Setup"
    activate
    delay 2
end tell

tell application "System Events"
    tell process "Audio MIDI Setup"
        -- Wait for window
        repeat until exists window 1
            delay 0.5
        end repeat
        
        -- Create Multi-Output Device
        click button 1 of window 1
        click menu item "Create Multi-Output Device" of menu 1 of button 1 of window 1
        delay 1
        
        -- Find and enable BlackHole
        set blackholeFound to false
        try
            repeat with i from 1 to 100
                try
                    set rowText to value of static text 1 of row i of outline 1 of scroll area 1 of window 1
                    if rowText contains "BlackHole" or rowText contains "2ch" then
                        set blackholeFound to true
                        if value of checkbox 1 of row i of outline 1 of scroll area 1 of window 1 is 0 then
                            click checkbox 1 of row i of outline 1 of scroll area 1 of window 1
                        end if
                        exit repeat
                    end if
                on error
                    exit repeat
                end try
            end repeat
        end try
        
        -- Find and enable Headphones/Speakers
        set headphonesFound to false
        try
            repeat with i from 1 to 100
                try
                    set rowText to value of static text 1 of row i of outline 1 of scroll area 1 of window 1
                    if rowText contains "Headphones" or rowText contains "External" or rowText contains "Speaker" then
                        set headphonesFound to true
                        if value of checkbox 1 of row i of outline 1 of scroll area 1 of window 1 is 0 then
                            click checkbox 1 of row i of outline 1 of scroll area 1 of window 1
                        end if
                        exit repeat
                    end if
                on error
                    exit repeat
                end try
            end repeat
        end try
        
        -- Rename the device
        delay 1
        set multiRow to first row of outline 1 of scroll area 1 of window 1 whose value of static text 1 starts with "Multi-Output"
        set value of text field 1 of multiRow to "Transcription Output"
        
        -- Set as default output
        tell multiRow
            perform action "AXShowMenu"
            delay 0.5
            click menu item "Use This Device For Sound Output" of menu 1
        end tell
        
        delay 2
        
        -- Close Audio MIDI Setup
        tell application "Audio MIDI Setup" to quit
        
        return "Multi-Output Device created with BlackHole and headphones"
    end tell
end tell
EOF
  
  # Verify setup in System Settings
  echo "Verifying audio output configuration..." | tee -a "$SERVICE_LOG"
  
  # Check current output device
  CURRENT_OUTPUT=$(osascript -e 'tell application "System Events" to tell application process "System Preferences"
    if exists (window "Sound") then
        tell window "Sound"
            tell tab group 1
                set currentOutput to value of pop up button 1
                return currentOutput
            end tell
        end tell
    end if
  end tell' 2>/dev/null || echo "unknown")
  
  echo "Current audio output: $CURRENT_OUTPUT" | tee -a "$SERVICE_LOG"
  
  if [[ "$CURRENT_OUTPUT" == *"Multi-Output"* ]] || [[ "$CURRENT_OUTPUT" == *"Transcription"* ]]; then
    echo "✅ Multi-Output Device is active!" | tee -a "$SERVICE_LOG"
    echo "   YouTube audio will be captured AND heard through headphones" | tee -a "$SERVICE_LOG"
    return 0
  else
    echo "⚠️  Multi-Output Device may not be set as default" | tee -a "$SERVICE_LOG"
    echo "   Manual setup may be required:" | tee -a "$SERVICE_LOG"
    echo "   1. System Settings → Sound → Output" | tee -a "$SERVICE_LOG"
    echo "   2. Select 'Transcription Output' or 'Multi-Output Device'" | tee -a "$SERVICE_LOG"
    return 1
  fi
}

setup_system_audio() {
  echo -e "\n[$(date '+%Y-%m-%d %H:%M:%S')] Configuring system audio for dual transcription..." >> "$SERVICE_LOG"
  
  echo "🔊 Configuring System Audio Settings..." | tee -a "$SERVICE_LOG"
  
  # Try to set system output to BlackHole first (for backward compatibility)
  echo "Option 1: Setting BlackHole 2ch as system output..." | tee -a "$SERVICE_LOG"
  
  osascript <<'EOF' 2>&1 | tee -a "$SERVICE_LOG"
try
    tell application "System Preferences"
        activate
        reveal anchor "output" of pane id "com.apple.preference.sound"
        delay 2
    end tell
    
    tell application "System Events"
        tell process "System Preferences"
            tell window "Sound"
                tell tab group 1
                    -- Try to select BlackHole
                    click pop up button 1
                    delay 0.5
                    
                    -- Look for BlackHole in the menu
                    try
                        click menu item "BlackHole 2ch" of menu 1 of pop up button 1
                        return "Set to BlackHole 2ch"
                    on error
                        -- If not found, look for Multi-Output device
                        try
                            click menu item "Transcription Output" of menu 1 of pop up button 1
                            return "Set to Transcription Output"
                        on error
                            try
                                click menu item where its name contains "Multi-Output"
                                return "Set to Multi-Output Device"
                            on error
                                return "Could not find audio devices - manual setup required"
                            end try
                        end try
                    end try
                end tell
            end tell
        end tell
    end tell
    
    delay 1
    tell application "System Preferences" to quit
    
on error
    return "⚠️  Could not configure audio automatically - please set manually"
end try
EOF
  
  # Test audio routing
  echo "Testing audio routing configuration..." | tee -a "$SERVICE_LOG"
  
  "$VENV_DIR/bin/python" -c "
import sounddevice as sd
import numpy as np

print('🔍 Testing BlackHole audio capture...')
print('Play YouTube video in browser to test')

try:
    # Find BlackHole device
    devices = sd.query_devices()
    blackhole_device = None
    for i, dev in enumerate(devices):
        if 'blackhole' in dev['name'].lower():
            blackhole_device = i
            break
    
    if blackhole_device is None:
        print('❌ BlackHole device not found')
        exit(1)
    
    print(f'Found BlackHole at device {blackhole_device}')
    print('Recording 5 seconds of system audio...')
    
    # Record from BlackHole
    recording = sd.rec(5 * 16000, samplerate=16000, channels=1, 
                      device=blackhole_device, dtype='float32')
    sd.wait()
    
    audio_level = np.max(np.abs(recording))
    print(f'📊 Max audio level: {audio_level:.6f}')
    
    if audio_level > 0.01:
        print('✅ Good audio level detected!')
        print('   Browser audio is reaching BlackHole')
    elif audio_level > 0.001:
        print('⚠️  Low audio level detected')
        print('   Increase browser/system volume')
    else:
        print('❌ No audio detected from browser')
        print('   Check: Browser volume, BlackHole as system output')
        
except Exception as e:
    print(f'⚠️  Audio test error: {e}')
" 2>&1 | tee -a "$SERVICE_LOG"
  
  echo "🎯 Audio Setup Instructions:" | tee -a "$SERVICE_LOG"
  echo "1. Open Firefox (recommended) or Safari" | tee -a "$SERVICE_LOG"
  echo "2. Go to YouTube.com" | tee -a "$SERVICE_LOG"
  echo "3. Play any video" | tee -a "$SERVICE_LOG"
  echo "4. Ensure system output is 'Transcription Output' or contains BlackHole" | tee -a "$SERVICE_LOG"
  echo "5. You should hear audio AND see transcriptions!" | tee -a "$SERVICE_LOG"
}

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

  # Setup Multi-Output Audio Device (NEW)
  echo
  echo "🎧 Setting up audio routing for simultaneous capture and playback..."
  setup_multi_output_device
  
  # Configure system audio settings
  setup_system_audio

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

  # Clean & recreate venv de novo
  echo
  echo "Recreating virtual environment from scratch…"
  rm -rf "$VENV_DIR"
  "$PY311" -m venv "$VENV_DIR"
  
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"

  # Install dependencies
  echo "Installing dependencies..."
  python -m pip install --upgrade pip setuptools wheel

  # Requirements
  printf "Flask==2.3.2\nnumpy==1.26.4\nsounddevice==0.4.6\nopenai-whisper==20231117\n" > requirements.txt

  # Install Torch CPU first
  echo "Installing PyTorch..."
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
  
  nohup bash -lc 'source venv/bin/activate; python -u whisperer-external.py' \
      >> "$FLASK_LOG" 2>&1 &

  echo $! > "$PID_FILE"
  echo "PID $(cat "$PID_FILE")"
  echo "Logs: tail -f $FLASK_LOG"
  echo
  echo "🎤🎧 DUAL AUDIO Transcription service started!"
  echo "   Web interface: http://localhost:5000"
  echo "   Monitoring: External Microphone + System Audio"
  echo "   Audio Output: 'Transcription Output' (Multi-Output Device)"
  echo "   You can now HEAR YouTube audio while it transcribes!"
  echo "   If no transcriptions appear, check audio permissions and volume"
} 2>&1 | tee -a "$SERVICE_LOG"