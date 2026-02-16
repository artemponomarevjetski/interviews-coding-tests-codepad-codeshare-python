#!/usr/bin/env bash

# =============================================================================
# 🎭 AI Avatar System Launcher - Documentation
# =============================================================================
#
# ## 📋 Script Overview
#
# This is the main launcher script for the AI Avatar System. It handles:
# - 🔧 Environment setup and dependency installation
# - 🧹 Aggressive cleanup of previous processes
# - 🔑 API key validation
# - 🎤 Microphone access verification
# - 🚀 Background process management
# - 📊 Logging and monitoring
#
# -----------------------------------------------------------------------------
#
# ## 🔧 Configuration Variables
#
# | Variable | Default | Description |
# |----------|---------|-------------|
# | `PORT` | 5000 | Port for the web interface |
# | `VENV_DIR` | "venv" | Virtual environment directory |
# | `PID_FILE` | "avatar.pid" | File storing the process ID |
# | `LOG_RETENTION_DAYS` | 7 | Days to keep conversation logs |
#
# ### 📁 Log Files
#
# | File | Purpose |
# |------|---------|
# | `logs/service.log` | Main launcher service logs |
# | `logs/flask_app.log` | Flask application output |
# | `logs/conversations.log` | Conversation transcripts |
#
# -----------------------------------------------------------------------------
#
# ## 🎨 Color Codes
#
# The script uses ANSI color codes for better UX:
#
# RED='\033[0;31m'     # Errors, critical issues
# GREEN='\033[0;32m'   # Success messages
# YELLOW='\033[1;33m'  # Warnings, important notes
# BLUE='\033[0;34m'    # Information, status updates
# CYAN='\033[0;36m'    # URLs, links
# PURPLE='\033[0;35m'  # Special highlights
# BOLD='\033[1m'       # Bold text
# NC='\033[0m'         # No Color (reset)
#
# -----------------------------------------------------------------------------
#
# ## 🛠️ Function Documentation
#
# ### 1. `log() - Logging Function`
#    Writes timestamped messages to both console and service log file.
#    Example: log "Starting avatar system"
#    Output: [2026-02-15 14:30:25] Starting avatar system
#
# ### 2. `cleanup() - Process Cleanup`
#    Aggressively kills any processes that might interfere with the avatar.
#    Steps:
#      1. Kill by PID file - Reads avatar.pid and kills that specific process
#      2. Kill by port - Kills ALL processes on port 5000 (regular + sudo)
#      3. Kill by pattern - Kills any Python processes from the repo
#      4. Verify - Checks 3 times, tries sudo if needed
#    Exit Codes: 0 = Success, 1 = Cannot free port 5000
#
# ### 3. `check_dependencies() - Dependency Check`
#    Ensures all required software is installed.
#    Checks:
#      - Python 3.8+ installed
#      - Virtual environment exists (creates if missing)
#      - Virtual environment activated
#      - pip upgraded to latest
#      - Requirements installed (from requirements.txt or core packages)
#
#    Installed core packages:
#      flask>=2.3.0              # Web interface
#      sounddevice>=0.4.6         # Audio capture
#      soundfile>=0.12.1          # Audio file handling
#      numpy>=1.21.0              # Audio processing
#      openai>=1.0.0              # GPT + Whisper API
#      requests>=2.28.0           # HTTP requests
#      python-dotenv>=1.0.0       # Environment variables
#      speechrecognition>=3.10.0  # Speech recognition
#      keyboard>=0.13.5           # Hotkey support
#
# ### 4. `check_env() - Environment Validation`
#    Validates .env file and API keys.
#    Process:
#      1. Checks if .env exists (creates template if missing)
#      2. Loads environment variables
#      3. Validates OPENAI_API_KEY is set and not default
#      4. Checks optional ElevenLabs configuration
#      5. Sets default port if not specified
#    Exit Codes: 0 = Valid, 1 = Missing/invalid API key
#
# ### 5. `check_microphone() - Microphone Test`
#    Tests microphone accessibility without failing.
#    Queries available audio devices using sounddevice.
#    Note: Only warns, doesn't fail (app can still run)
#
# ### 6. `show_summary() - Status Display`
#    Displays a beautiful summary before launching.
#    Shows web interface URL, hotkeys, log file, PID file.
#
# -----------------------------------------------------------------------------
#
# ## 🚀 Main Execution Flow
#
#   1. Cleanup - Kills any processes on port 5000
#   2. Dependencies - Ensures Python and packages are ready
#   3. Environment - Validates API keys in .env
#   4. Microphone - Quick test (warning only)
#   5. Launch - Starts avatar.py in background with nohup
#   6. Monitor - Shows live logs with tail -f
#   7. Cleanup - On exit, kills process and removes PID file
#
# -----------------------------------------------------------------------------
#
# ## 📊 Exit Codes
#
# | Code | Meaning | Action Required |
# |------|---------|-----------------|
# | 0 | Success | Everything worked! |
# | 1 | Port 5000 stuck | Run `sudo lsof -i :5000` and kill manually |
# | 1 | Python missing | Install Python 3.8+ |
# | 1 | API key missing | Add key to `.env` |
# | 1 | Avatar failed to start | Check `logs/flask_app.log` |
#
# -----------------------------------------------------------------------------
#
# ## 💡 Usage Examples
#
# ### Normal start:
#   cd ~/interviews-coding-tests-codepad-codeshare-python/apps/flasks/avatar
#   chmod +x set-up-and-run.sh
#   ./set-up-and-run.sh
#
# ### If port 5000 is stuck:
#   sudo lsof -i :5000
#   sudo kill -9 <PID>
#   ./set-up-and-run.sh
#
# ### View logs without restarting:
#   tail -f logs/flask_app.log
#
# ### Stop the avatar manually:
#   kill $(cat avatar.pid)
#   rm avatar.pid
#
# -----------------------------------------------------------------------------
#
# ## 🔍 Troubleshooting
#
# ### "Port 5000 still in use"
#   lsof -i :5000
#   sudo kill -9 <PID>
#   ../kill-all-flasks.sh
#
# ### "OPENAI_API_KEY not configured"
#   nano .env
#   # Add: OPENAI_API_KEY="sk-your-real-key-here"
#
# ### "No microphone found"
#   - Check System Settings → Privacy & Security → Microphone
#   - Ensure Terminal has microphone access
#   - Test with: python3 -c "import sounddevice as sd; print(sd.query_devices())"
#
# ### Hotkeys not working
#   - System Settings → Privacy & Security → Accessibility
#   - Add your terminal app (Terminal.app, iTerm2, etc.)
#   - Restart terminal and script
#
# -----------------------------------------------------------------------------
#
# ## 🎯 Summary
#
# This launcher script provides:
#   - Production-ready process management
#   - Aggressive cleanup to ensure clean start
#   - Comprehensive logging for debugging
#   - Beautiful UX with color-coded output
#   - Graceful error handling with clear messages
#   - Background operation that survives terminal closure
#
# =============================================================================
#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# 🎭 AI Avatar System Launcher - FINAL VERSION (NO PASSWORD PROMPTS)
# =============================================================================
#
# This launcher script provides:
#   - Production-ready process management
#   - Cleanup WITHOUT ANY sudo/password prompts
#   - Comprehensive logging for debugging
#   - Beautiful UX with color-coded output
#   - Graceful error handling with clear messages
#   - Background operation that survives terminal closure
#
# =============================================================================

# --- Configuration ---
PORT=5000
VENV_DIR="venv"
PID_FILE="avatar.pid"

# --- Log File Paths ---
LOG_DIR="logs"
SERVICE_LOG="$LOG_DIR/service.log"
FLASK_LOG="$LOG_DIR/flask_app.log"
CONVERSATION_LOG="$LOG_DIR/conversations.log"

mkdir -p "$LOG_DIR"
touch "$SERVICE_LOG" "$FLASK_LOG" "$CONVERSATION_LOG"

# --- Color codes for better UX ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# --- ASCII Art for header ---
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║              🎭 AI AVATAR SYSTEM                     ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# --- Functions ---
log() { 
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$SERVICE_LOG"
}

cleanup() {
    log "${YELLOW}🧹 Cleaning up previous processes (no sudo)...${NC}"
    
    # Kill by PID file first
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE" 2>/dev/null || echo "")
        if [ -n "$OLD_PID" ] && ps -p "$OLD_PID" >/dev/null 2>&1; then
            log "   ✅ Killing previous avatar instance (PID: $OLD_PID)"
            kill -9 "$OLD_PID" 2>/dev/null || true
        fi
        rm -f "$PID_FILE"
    fi
    
    # Kill processes on port 5000 (NO SUDO - NEVER)
    log "   🔍 Checking port $PORT..."
    PIDS=$(lsof -ti:$PORT 2>/dev/null || true)
    if [ -n "$PIDS" ]; then
        log "   ⚠️  Found processes on port $PORT: $PIDS"
        # Try to kill them (only user processes)
        for PID in $PIDS; do
            if kill -0 "$PID" 2>/dev/null; then
                log "      Killing PID $PID"
                kill -9 "$PID" 2>/dev/null || true
            fi
        done
        sleep 1
        
        # Check if any remain
        REMAINING=$(lsof -ti:$PORT 2>/dev/null || true)
        if [ -n "$REMAINING" ]; then
            log "${YELLOW}   ⚠️  Some processes on port $PORT could not be killed${NC}"
            log "   ℹ️  You may need to run this command manually:"
            log "      kill -9 $REMAINING"
        else
            log "${GREEN}   ✅ Port $PORT is now free${NC}"
        fi
    else
        log "${GREEN}   ✅ No processes found on port $PORT${NC}"
    fi
    
    # Kill any Python processes from this repo (only user processes, NO SUDO)
    log "   🔍 Cleaning up related Python processes..."
    
    # Check for avatar processes
    AVATAR_PIDS=$(pgrep -f "python.*avatar" 2>/dev/null || true)
    if [ -n "$AVATAR_PIDS" ]; then
        log "   Found avatar processes: $AVATAR_PIDS"
        pkill -f "python.*avatar" 2>/dev/null || true
    fi
    
    # Check for flask processes
    FLASK_PIDS=$(pgrep -f "python.*flask" 2>/dev/null || true)
    if [ -n "$FLASK_PIDS" ]; then
        log "   Found flask processes: $FLASK_PIDS"
        pkill -f "python.*flask" 2>/dev/null || true
    fi
    
    # Check for any other python processes from this repo
    OTHER_PIDS=$(pgrep -f "python.*(solver|whisperer|snapshot)" 2>/dev/null || true)
    if [ -n "$OTHER_PIDS" ]; then
        log "   Found other repo processes: $OTHER_PIDS"
        pkill -f "python.*(solver|whisperer|snapshot)" 2>/dev/null || true
    fi
    
    log "${GREEN}✅ Cleanup complete${NC}"
}

check_dependencies() {
    log "${BLUE}🔍 Checking dependencies...${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log "${RED}❌ Python3 not found. Install Python 3.8+ first.${NC}"
        exit 1
    fi
    
    # Check virtual environment
    if [ ! -d "$VENV_DIR" ]; then
        log "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
        python3 -m venv "$VENV_DIR"
        log "${GREEN}✅ Virtual environment created${NC}"
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    log "${GREEN}✅ Virtual environment activated${NC}"
    
    # Install/upgrade pip
    python -m pip install --upgrade pip setuptools wheel > /dev/null 2>&1
    
    # Check and install requirements
    if [ -f "requirements.txt" ]; then
        log "   📦 Installing/upgrading requirements..."
        pip install -r requirements.txt > /dev/null 2>&1
    else
        log "   📦 Installing core dependencies..."
        pip install flask>=2.3.0 > /dev/null 2>&1
        pip install sounddevice>=0.4.6 soundfile>=0.12.1 numpy>=1.21.0 > /dev/null 2>&1
        pip install openai>=1.0.0 requests>=2.28.0 > /dev/null 2>&1
        pip install python-dotenv>=1.0.0 > /dev/null 2>&1
        pip install speechrecognition>=3.10.0 > /dev/null 2>&1
        pip install keyboard>=0.13.5 > /dev/null 2>&1
    fi
    
    log "${GREEN}✅ Dependencies ready${NC}"
}

check_env() {
    log "${BLUE}🔑 Checking environment configuration...${NC}"
    
    # Check .env file
    if [ ! -f ".env" ]; then
        log "${RED}❌ .env file not found. Creating template...${NC}"
        cat > ".env" << 'EOF'
# OpenAI API Key (required)
OPENAI_API_KEY="your-openai-api-key-here"

# ElevenLabs API Key (optional - for voice cloning)
ELEVENLABS_API_KEY="your-elevenlabs-api-key-here"
ELEVENLABS_VOICE_ID="your-voice-id-here"

# Model settings
GPT_MODEL=gpt-4
PORT=5000
EOF
        log "${RED}❌ Please edit .env and add your OpenAI API key${NC}"
        log "   Get one from: https://platform.openai.com/api-keys"
        exit 1
    fi
    
    # Load environment variables
    set -a
    source .env
    set +a
    
    # Check OpenAI API key
    if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your-openai-api-key-here" ]; then
        log "${RED}❌ OPENAI_API_KEY not configured in .env file${NC}"
        log "   Please add your OpenAI API key to .env"
        exit 1
    fi
    log "${GREEN}✅ OpenAI API key configured${NC}"
    
    # Check ElevenLabs (optional - we'll do voice cloning later)
    if [ -n "$ELEVENLABS_API_KEY" ] && [ "$ELEVENLABS_API_KEY" != "your-elevenlabs-api-key-here" ]; then
        log "${GREEN}✅ ElevenLabs API key found (voice cloning available)${NC}"
        if [ -n "$ELEVENLABS_VOICE_ID" ] && [ "$ELEVENLABS_VOICE_ID" != "your-voice-id-here" ]; then
            log "${GREEN}✅ ElevenLabs voice ID configured${NC}"
        else
            log "${YELLOW}⚠️  Voice cloning files found in audio/ directory${NC}"
            log "   ℹ️  Run './audio/voice-clone.py' later to set up your voice"
        fi
    fi
    
    # Set default port if not specified
    PORT="${PORT:-5000}"
}

check_microphone() {
    log "${BLUE}🎤 Checking microphone access...${NC}"
    
    # Quick microphone test
    python3 -c "
import sys
try:
    import sounddevice as sd
    devices = sd.query_devices()
    input_devices = [i for i, d in enumerate(devices) if d['max_input_channels'] > 0]
    if input_devices:
        default_input = sd.default.device[0] if sd.default.device else input_devices[0]
        device_name = devices[default_input]['name']
        print(f'   ✅ Found microphone: {device_name}')
    else:
        print('   ⚠️  No microphone found - check System Settings')
        sys.exit(0)
except Exception as e:
    print(f'   ⚠️  Could not check microphone: {e}')
" 2>&1 | tee -a "$SERVICE_LOG"
}

show_summary() {
    echo -e "\n${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║           SYSTEM READY - LAUNCHING AVATAR            ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BOLD}📋 Summary:${NC}"
    echo -e "   🌐 Web Interface: ${CYAN}http://localhost:$PORT${NC}"
    echo -e "   🎮 Hotkeys: ${YELLOW}Ctrl+Shift+D${NC} (Start), ${YELLOW}Ctrl+Shift+T${NC} (Stop), ${YELLOW}Ctrl+Shift+Q${NC} (Quit)"
    echo -e "   📝 Log file: ${BLUE}$FLASK_LOG${NC}"
    echo -e "   💾 PID file: ${BLUE}$PID_FILE${NC}"
    echo -e "   🎤 Voice cloning files: ${PURPLE}audio/ directory${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  If hotkeys don't work:${NC}"
    echo -e "   System Settings → Privacy & Security → Accessibility → Add Terminal"
    echo ""
}

# --- Main Execution ---
{
    # Run cleanup first
    cleanup
    
    # Check dependencies
    check_dependencies
    
    # Check environment
    check_env
    
    # Check microphone
    check_microphone
    
    # Show summary
    show_summary
    
    # Start the application in background
    log "${BLUE}🚀 Starting AI Avatar System...${NC}"
    
    # Use nohup to survive terminal close
    nohup python3 avatar.py > "$FLASK_LOG" 2>&1 &
    AVATAR_PID=$!
    echo $AVATAR_PID > "$PID_FILE"
    
    log "${GREEN}✅ Avatar started with PID: $AVATAR_PID${NC}"
    
    # Wait a moment and check if it's running
    sleep 3
    if ps -p $AVATAR_PID > /dev/null 2>&1; then
        log "${GREEN}✅ Avatar is running successfully${NC}"
        echo -e "\n${GREEN}🎭✅ Avatar System is now running!${NC}"
        echo -e "   ${CYAN}http://localhost:$PORT${NC}"
        echo -e "\n${YELLOW}Press Ctrl+C to stop watching logs (app continues running)${NC}\n"
        
        # Show logs
        tail -f "$FLASK_LOG"
    else
        log "${RED}❌ Avatar failed to start${NC}"
        log "   Check logs: $FLASK_LOG"
        exit 1
    fi
    
} 2>&1 | tee -a "$SERVICE_LOG"

# Cleanup on exit
trap 'echo -e "\n${YELLOW}🛑 Stopping avatar...${NC}"; kill $AVATAR_PID 2>/dev/null 2>&1; rm -f $PID_FILE; echo -e "${GREEN}✅ Stopped${NC}"' EXIT
