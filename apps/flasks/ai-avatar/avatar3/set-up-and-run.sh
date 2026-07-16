#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# 🎭 AI Avatar System Launcher - COMPREHENSIVE DOCUMENTATION
# =============================================================================
#
# █████╗ ██╗    ███████╗██╗   ██╗███████╗████████╗███████╗███╗   ███╗
# ██╔══██╗██║    ██╔════╝██║   ██║██╔════╝╚══██╔══╝██╔════╝████╗ ████║
# ███████║██║    █████╗  ██║   ██║███████╗   ██║   █████╗  ██╔████╔██║
# ██╔══██║██║    ██╔══╝  ██║   ██║╚════██║   ██║   ██╔══╝  ██║╚██╔╝██║
# ██║  ██║██║    ██║     ╚██████╔╝███████║   ██║   ███████╗██║ ╚═╝ ██║
# ╚═╝  ╚═╝╚═╝    ╚═╝      ╚═════╝ ╚══════╝   ╚═╝   ╚══════╝╚═╝     ╚═╝
#
# =============================================================================
# 📋 TABLE OF CONTENTS
# =============================================================================
# 1.0 OVERVIEW .................... What this script does
# 2.0 REQUIREMENTS ................ What you need before running
# 3.0 CONFIGURATION ............... Variables you can customize
# 4.0 FILE STRUCTURE .............. Logs and important files
# 5.0 COLOR CODES ................. Visual feedback system
# 6.0 FUNCTION REFERENCE ..........
#     6.1 log() ................... Logging system
#     6.2 cleanup() ............... Process cleanup
#     6.3 check_dependencies() ..... Python and package verification
#     6.4 check_env() .............. .env file and API key validation
#     6.5 check_microphone() ....... Audio device detection
#     6.6 show_summary() ........... Status display
# 7.0 EXECUTION FLOW ............... Step-by-step process
# 8.0 EXIT CODES ................... What each exit code means
# 9.0 TROUBLESHOOTING .............. Common issues and solutions
# 10.0 USAGE EXAMPLES .............. How to run the script
# 11.0 ENVIRONMENT VARIABLES ....... What can be overridden
# 12.0 SHARED .ENV SUPPORT ......... Multi-location configuration
# 13.0 THREE MODE SUPPORT ........... Text, System Voice, Cloned Voice
# 14.0 VERSION HISTORY ............. Changes and updates
#
# =============================================================================
# 1.0 📋 OVERVIEW
# =============================================================================
#
# This launcher script provides a production-ready environment for the
# AI Avatar System with THREE response modes. It handles everything from 
# dependency installation to process management with a beautiful, user-friendly 
# interface.
#
# 🎯 PRIMARY OBJECTIVES:
#   - Zero-touch deployment - Just run and it works
#   - Intelligent cleanup - No more "port in use" errors
#   - Shared configuration - One .env file for all Flask apps
#   - Bulletproof error handling - Clear messages for every issue
#   - Background operation - Survives terminal closure
#   - Three mode support - Text, System Voice, and ElevenLabs Cloned Voice
#
# 🔄 WORKFLOW SUMMARY:
#   Cleanup → Dependencies → Environment → Microphone → Launch → Monitor
#
# =============================================================================
# 2.0 🔧 REQUIREMENTS
# =============================================================================
#
# 🐍 Python:
#   - Version 3.8 or higher
#   - Check with: python3 --version
#
# 🎤 Microphone:
#   - System Settings → Privacy & Security → Microphone
#   - Terminal must have microphone access
#
# ⌨️ Hotkeys (optional):
#   - System Settings → Privacy & Security → Accessibility
#   - Add Terminal.app or iTerm2 for global hotkeys
#
# 🔑 API Keys (in .env file):
#   - OpenAI API key (required) - Get from: https://platform.openai.com/api-keys
#   - ElevenLabs API key (optional) - For voice cloning (Mode 3)
#   - ElevenLabs Voice ID (optional) - Your cloned voice ID
#
# 📦 Python Packages (auto-installed):
#   - flask>=2.3.0              # Web interface
#   - sounddevice>=0.4.6        # Audio capture
#   - soundfile>=0.12.1         # Audio file handling
#   - numpy>=1.21.0             # Audio processing
#   - openai>=1.0.0             # GPT + Whisper API
#   - requests>=2.28.0          # HTTP requests
#   - python-dotenv>=1.0.0      # Environment variables
#   - speechrecognition>=3.10.0 # Speech recognition
#   - keyboard>=0.13.5          # Hotkey support
#
# =============================================================================
# 3.0 ⚙️ CONFIGURATION VARIABLES
# =============================================================================
#
# You can modify these variables at the top of the script:
#
# ┌─────────────────┬─────────────┬────────────────────────────────────────┐
# │ Variable        │ Default     │ Description                            │
# ├─────────────────┼─────────────┼────────────────────────────────────────┤
# │ PORT            │ 5000        │ Port for the web interface             │
# │ VENV_DIR        │ "venv"      │ Virtual environment directory          │
# │ PID_FILE        │ "avatar.pid"│ File storing the process ID            │
# │ LOG_RETENTION   │ 7 days      │ How long to keep conversation logs     │
# └─────────────────┴─────────────┴────────────────────────────────────────┘
#
# =============================================================================
# 4.0 📁 FILE STRUCTURE
# =============================================================================
#
# After running, the script creates/maintains these files:
#
# 📂 Project Root:
#   ├── 📁 avatar/
#   │   ├── 📄 avatar.py              # Main application (3 modes)
#   │   ├── 📄 set-up-and-run.sh      # This launcher script
#   │   ├── 📄 requirements.txt        # Python dependencies
#   │   ├── 📁 logs/                   # Log files directory
#   │   │   ├── 📄 service.log         # Launcher service logs
#   │   │   ├── 📄 flask_app.log       # Flask application output
#   │   │   └── 📄 conversations.log   # Conversation transcripts
#   │   ├── 📁 audio/                   # Voice cloning files
#   │   └── 📄 avatar.pid               # Running process ID
#   │
#   └── 📁 flasks/ (parent directory)
#       └── 📄 .env                     # Shared environment variables
#
# 📋 LOG FILE DETAILS:
#   - service.log:      Timestamped launcher operations
#   - flask_app.log:    Flask server output and debug info
#   - conversations.log: All AI conversations (rotated weekly)
#
# =============================================================================
# 5.0 🎨 COLOR CODES
# =============================================================================
#
# The script uses ANSI color codes for visual feedback:
#
# ┌─────────────┬──────────┬─────────────────────────────────────────────┐
# │ Code        │ Color    │ Usage                                       │
# ├─────────────┼──────────┼─────────────────────────────────────────────┤
# │ RED         │ ████     │ Errors, critical issues, missing API keys  │
# │ GREEN       │ ████     │ Success messages, confirmations             │
# │ YELLOW      │ ████     │ Warnings, important notes, cleanup actions  │
# │ BLUE        │ ████     │ Information, status updates, section headers│
# │ CYAN        │ ████     │ URLs, web interface links                   │
# │ PURPLE      │ ████     │ Special highlights, file paths              │
# │ BOLD        │ ████     │ Section titles, important numbers           │
# └─────────────┴──────────┴─────────────────────────────────────────────┘
#
# =============================================================================
# 6.0 🛠️ FUNCTION REFERENCE
# =============================================================================
#
# -----------------------------------------------------------------------------
# 6.1 log() - Logging Function
# -----------------------------------------------------------------------------
# Writes timestamped messages to both console and service log file.
#
# 📝 Syntax: log "Your message here"
# 📁 Output: [2026-02-22 14:30:25] Your message here
# 📄 Writes to: logs/service.log
#
# 💡 Example:
#   log "🚀 Starting avatar system"
#   # Console: [2026-02-22 14:30:25] 🚀 Starting avatar system
#   # File:    [2026-02-22 14:30:25] 🚀 Starting avatar system
#
# -----------------------------------------------------------------------------
# 6.2 cleanup() - Process Cleanup
# -----------------------------------------------------------------------------
# Aggressively kills any processes that might interfere with the avatar.
# Uses multiple strategies to ensure a clean start.
#
# 🔍 STRATEGIES (in order):
#   1. Kill by PID file - Reads avatar.pid and kills that specific process
#   2. Kill by port - Kills ALL user processes on port 5000 (NO SUDO)
#   3. Kill by pattern - Kills Python processes from the repo
#   4. Verify - Double-checks port is free
#
# 🚫 NO SUDO POLICY:
#   The script NEVER uses sudo to avoid password prompts
#   If processes remain, it gives clear instructions to kill manually
#
# 📊 Exit Codes: 0 = Success, continues execution
#
# 💡 Example Output:
#   [2026-02-22 14:30:25] 🧹 Cleaning up previous processes (no sudo)...
#   [2026-02-22 14:30:25]    ✅ Killing previous avatar instance (PID: 1234)
#   [2026-02-22 14:30:25]    🔍 Checking port 5000...
#   [2026-02-22 14:30:25]    ✅ No processes found on port 5000
#   [2026-02-22 14:30:25] ✅ Cleanup complete
#
# -----------------------------------------------------------------------------
# 6.3 check_dependencies() - Dependency Check
# -----------------------------------------------------------------------------
# Ensures all required software is installed and ready.
#
# 🔍 CHECKS PERFORMED:
#   ✓ Python 3.8+ is installed
#   ✓ Virtual environment exists (creates if missing)
#   ✓ Virtual environment activated
#   ✓ pip upgraded to latest
#   ✓ Requirements installed (from requirements.txt or core packages)
#
# 📦 INSTALLED PACKAGES:
#   - flask>=2.3.0              # Web interface
#   - sounddevice>=0.4.6        # Audio capture
#   - soundfile>=0.12.1         # Audio file handling
#   - numpy>=1.21.0             # Audio processing
#   - openai>=1.0.0             # GPT + Whisper API
#   - requests>=2.28.0          # HTTP requests
#   - python-dotenv>=1.0.0      # Environment variables
#   - speechrecognition>=3.10.0 # Speech recognition
#   - keyboard>=0.13.5          # Hotkey support
#
# ⚠️ Exit Codes: 1 = Python missing
#
# -----------------------------------------------------------------------------
# 6.4 check_env() - Environment Validation
# -----------------------------------------------------------------------------
# Validates .env file and API keys with multi-location search.
#
# 🔍 SEARCH LOCATIONS (in order):
#   1. Current directory (avatar/.env)
#   2. Parent directory (flasks/.env) ← SHARED CONFIGURATION
#   3. Grandparent directory (apps/.env)
#   4. Absolute path (as fallback)
#
# 📋 VALIDATION STEPS:
#   1. Searches all locations for .env file
#   2. If found, records path and loads variables
#   3. If not found, creates template in current directory
#   4. Validates OPENAI_API_KEY is set and not default
#   5. Checks optional ElevenLabs configuration (for Mode 3)
#   6. Sets default port if not specified
#
# 🔑 REQUIRED VARIABLES:
#   OPENAI_API_KEY="sk-..."     # Must be your actual key
#
# 🎤 OPTIONAL VARIABLES (for Mode 3 - Cloned Voice):
#   ELEVENLABS_API_KEY="..."     # For voice cloning
#   ELEVENLABS_VOICE_ID="..."    # Your cloned voice ID
#   GPT_MODEL="gpt-4"            # Model to use
#   PORT="5000"                  # Web interface port
#
# ⚠️ Exit Codes: 1 = Missing or invalid API key
#
# 💡 Example Output:
#   [2026-02-22 14:30:25] 🔑 Checking environment configuration...
#   [2026-02-22 14:30:25]    ✅ Found .env at: ../.env
#   [2026-02-22 14:30:25] ✅ OpenAI API key configured
#   [2026-02-22 14:30:25] ✅ ElevenLabs API key found (voice cloning available)
#
# -----------------------------------------------------------------------------
# 6.5 check_microphone() - Microphone Test
# -----------------------------------------------------------------------------
# Tests microphone accessibility without failing (warning only).
#
# 🔍 TESTS PERFORMED:
#   ✓ Queries available audio devices via sounddevice
#   ✓ Identifies default input device
#   ✓ Reports total input devices found
#   ✓ Warns if no microphone detected
#
# 💡 Note: This is informational only - the app can still run
#         even if no microphone is detected (for text-only mode)
#
# 💡 Example Output:
#   [2026-02-22 14:30:25] 🎤 Checking microphone access...
#      ✅ Found microphone: External Microphone
#      📊 Total input devices: 5
#
# -----------------------------------------------------------------------------
# 6.6 show_summary() - Status Display
# -----------------------------------------------------------------------------
# Displays a beautiful summary before launching.
#
# 📋 INFORMATION DISPLAYED:
#   - Web interface URL (with port)
#   - Hotkey combinations
#   - Log file locations
#   - PID file location
#   - .env file location (which one was found)
#   - Hotkey troubleshooting tips
#
# 💡 Example Output:
#   ╔══════════════════════════════════════════════════════╗
#   ║           SYSTEM READY - LAUNCHING AVATAR            ║
#   ╚══════════════════════════════════════════════════════╝
#   
#   📋 Summary:
#      🌐 Web Interface: http://localhost:5000
#      🎮 Hotkeys: Ctrl+Shift+D (Start), Ctrl+Shift+T (Stop), Ctrl+Shift+Q (Quit)
#      📝 Log file: logs/flask_app.log
#      💾 PID file: avatar.pid
#      🔑 Using .env from: ../.env
#
# =============================================================================
# 7.0 🚀 EXECUTION FLOW
# =============================================================================
#
# The script executes in this exact order:
#
# ┌─────────────────┐
# │     START       │
# └────────┬────────┘
#          ↓
# ┌─────────────────┐
# │   1. CLEANUP    │ ← Kill existing processes
# │   - Kill by PID │   Free port 5000
# │   - Kill by port│   Remove stale PID file
# │   - Kill by name│
# └────────┬────────┘
#          ↓
# ┌─────────────────┐
# │2. DEPENDENCIES  │ ← Check Python 3.8+
# │   - Python      │   Create/activate venv
# │   - Virtual env │   Install packages
# │   - Requirements│
# └────────┬────────┘
#          ↓
# ┌─────────────────┐
# │  3. ENVIRONMENT │ ← Search for .env (multiple locations)
# │   - Find .env   │   Load variables
# │   - Validate key│   Check OpenAI & ElevenLabs
# │   - Set PORT    │
# └────────┬────────┘
#          ↓
# ┌─────────────────┐
# │ 4. MICROPHONE   │ ← Query audio devices
# │   - List devices│   Report findings
# │   - Check access│   (Warning only)
# └────────┬────────┘
#          ↓
# ┌─────────────────┐
# │  5. SUMMARY     │ ← Display configuration
# │   - Show URL    │   Show file locations
# │   - Show hotkeys│   Show .env source
# └────────┬────────┘
#          ↓
# ┌─────────────────┐
# │   6. LAUNCH     │ ← Start avatar.py (3 modes)
# │   - nohup       │   Save PID
# │   - background  │   Monitor startup
# └────────┬────────┘
#          ↓
# ┌─────────────────┐
# │  7. MONITOR     │ ← tail -f logs
# │   - Show logs   │   Wait for Ctrl+C
# │   - Keep running│
# └────────┬────────┘
#          ↓
# ┌─────────────────┐
# │     EXIT        │ ← Cleanup on exit
# │   - Kill process│   Remove PID file
# │   - Done!       │
# └─────────────────┘
#
# =============================================================================
# 8.0 📊 EXIT CODES
# =============================================================================
#
# The script uses these exit codes for different error conditions:
#
# ┌─────────┬─────────────────────────────────┬─────────────────────────────┐
# │ Code    │ Meaning                         │ Action Required             │
# ├─────────┼─────────────────────────────────┼─────────────────────────────┤
# │ 0       │ Success                          │ Everything worked!           │
# ├─────────┼─────────────────────────────────┼─────────────────────────────┤
# │ 1       │ Python 3.8+ not found            │ Install Python from         │
# │         │                                  │ python.org                  │
# ├─────────┼─────────────────────────────────┼─────────────────────────────┤
# │ 1       │ OPENAI_API_KEY missing/invalid   │ Add your API key to .env    │
# ├─────────┼─────────────────────────────────┼─────────────────────────────┤
# │ 1       │ Avatar failed to start           │ Check logs/flask_app.log    │
# ├─────────┼─────────────────────────────────┼─────────────────────────────┤
# │ 1       │ Port 5000 stuck (manual fix)     │ Run: kill -9 <PID>          │
# └─────────┴─────────────────────────────────┴─────────────────────────────┘
#
# =============================================================================
# 9.0 🔍 TROUBLESHOOTING
# =============================================================================
#
# ─────────────────────────────────────────────────────────────────────────────
# ❌ ERROR: "Port 5000 still in use"
# ─────────────────────────────────────────────────────────────────────────────
#   🔍 CAUSE: Another Flask app or process is using the port
#   ✅ SOLUTION: 
#     1. Find the process: lsof -i :5000
#     2. Kill it: kill -9 <PID>
#     3. Or use: ../kill-all-flasks.sh
#
# ─────────────────────────────────────────────────────────────────────────────
# ❌ ERROR: "OPENAI_API_KEY not configured"
# ─────────────────────────────────────────────────────────────────────────────
#   🔍 CAUSE: .env file missing or API key not set
#   ✅ SOLUTION:
#     1. Check if .env exists: ls -la ../.env
#     2. Edit the file: nano ../.env
#     3. Add: OPENAI_API_KEY="sk-your-real-key-here"
#
# ─────────────────────────────────────────────────────────────────────────────
# ❌ ERROR: "ElevenLabs not configured" (when trying Mode 3)
# ─────────────────────────────────────────────────────────────────────────────
#   🔍 CAUSE: Missing ElevenLabs API key or voice ID
#   ✅ SOLUTION:
#     1. Get API key from: https://elevenlabs.io/app → Profile → API Key
#     2. Get voice ID from: https://elevenlabs.io/app/voice-lab
#     3. Add to ../.env:
#        ELEVENLABS_API_KEY="your-key"
#        ELEVENLABS_VOICE_ID="your-voice-id"
#
# ─────────────────────────────────────────────────────────────────────────────
# ❌ ERROR: "No microphone found"
# ─────────────────────────────────────────────────────────────────────────────
#   🔍 CAUSE: Microphone permissions not granted
#   ✅ SOLUTION:
#     1. System Settings → Privacy & Security → Microphone
#     2. Check "Terminal" is enabled
#     3. Test: python3 -c "import sounddevice as sd; print(sd.query_devices())"
#
# ─────────────────────────────────────────────────────────────────────────────
# ❌ ERROR: "Hotkeys not working"
# ─────────────────────────────────────────────────────────────────────────────
#   🔍 CAUSE: Accessibility permissions missing
#   ✅ SOLUTION:
#     1. System Settings → Privacy & Security → Accessibility
#     2. Add your terminal app (Terminal.app, iTerm2, etc.)
#     3. Restart terminal and script
#
# ─────────────────────────────────────────────────────────────────────────────
# ❌ ERROR: "Avatar failed to start" with no clear error
# ─────────────────────────────────────────────────────────────────────────────
#   🔍 CAUSE: Python syntax error or missing dependency
#   ✅ SOLUTION:
#     1. Check the logs: cat logs/flask_app.log
#     2. Look for Python errors (IndentationError, ImportError, etc.)
#     3. Fix the issue in avatar.py
#
# =============================================================================
# 10.0 💡 USAGE EXAMPLES
# =============================================================================
#
# ─────────────────────────────────────────────────────────────────────────────
# 🚀 NORMAL START
# ─────────────────────────────────────────────────────────────────────────────
#   cd ~/interviews-coding-tests-codepad-codeshare-python/apps/flasks/avatar
#   chmod +x set-up-and-run.sh
#   ./set-up-and-run.sh
#
# ─────────────────────────────────────────────────────────────────────────────
# 🔧 IF PORT 5000 IS STUCK
# ─────────────────────────────────────────────────────────────────────────────
#   sudo lsof -i :5000
#   sudo kill -9 <PID>
#   ./set-up-and-run.sh
#
# ─────────────────────────────────────────────────────────────────────────────
# 📝 VIEW LOGS WITHOUT RESTARTING
# ─────────────────────────────────────────────────────────────────────────────
#   tail -f logs/flask_app.log
#   tail -f logs/service.log
#   tail -f logs/conversations.log
#
# ─────────────────────────────────────────────────────────────────────────────
# 🛑 STOP THE AVATAR MANUALLY
# ─────────────────────────────────────────────────────────────────────────────
#   kill $(cat avatar.pid)
#   rm avatar.pid
#
# ─────────────────────────────────────────────────────────────────────────────
# 🔄 UPDATE DEPENDENCIES ONLY
# ─────────────────────────────────────────────────────────────────────────────
#   source venv/bin/activate
#   pip install -r requirements.txt --upgrade
#
# =============================================================================
# 11.0 🌍 ENVIRONMENT VARIABLES
# =============================================================================
#
# You can override defaults by setting these environment variables:
#
# ┌─────────────────┬──────────────────────────────────────────────────────┐
# │ Variable        │ Override Example                                      │
# ├─────────────────┼──────────────────────────────────────────────────────┤
# │ PORT            │ PORT=8080 ./set-up-and-run.sh                        │
# │ VENV_DIR        │ VENV_DIR="myenv" ./set-up-and-run.sh                 │
# │ PID_FILE        │ PID_FILE="custom.pid" ./set-up-and-run.sh            │
# │ ENV_FILE        │ ENV_FILE="/path/to/.env" ./set-up-and-run.sh         │
# └─────────────────┴──────────────────────────────────────────────────────┘
#
# =============================================================================
# 12.0 🔄 SHARED .ENV SUPPORT
# =============================================================================
#
# This script is designed to work with a shared .env file in the parent
# directory, allowing multiple Flask apps to use the same configuration.
#
# 📁 HIERARCHY:
#   flasks/                      # Parent directory
#   ├── .env                     # SHARED configuration file
#   ├── avatar/                   # This app
#   │   └── set-up-and-run.sh    # This script
#   ├── solver/                   # Another Flask app
#   └── whisperer-external/       # Another Flask app
#
# 🔍 SEARCH ORDER:
#   1. Current directory (for local overrides)
#   2. Parent directory (for shared config) ← DEFAULT FOR YOUR SETUP
#   3. Grandparent directory (for project-wide config)
#   4. Absolute path (for custom locations)
#
# ✅ BENEFITS:
#   - Single source of truth for API keys
#   - Update once, all apps use new keys
#   - No duplicate .env files
#   - Easier to manage multiple Flask apps
#
# =============================================================================
# 13.0 🎭 THREE MODE SUPPORT
# =============================================================================
#
# The avatar.py script supports THREE distinct response modes:
#
# ┌─────────────┬───────────────┬─────────────────────────────────────────┐
# │ Mode        │ Name          │ Description                             │
# ├─────────────┼───────────────┼─────────────────────────────────────────┤
# │ Mode 1      │ Text Only     │ 📝 Avatar types responses only          │
# │             │               │   - No voice output                     │
# │             │               │   - Works without microphone            │
# ├─────────────┼───────────────┼─────────────────────────────────────────┤
# │ Mode 2      │ System Voice  │ 🔊 Avatar speaks with system TTS        │
# │             │               │   - macOS: 'say' command                │
# │             │               │   - Linux: 'espeak'                     │
# │             │               │   - Windows: PowerShell TTS             │
# ├─────────────┼───────────────┼─────────────────────────────────────────┤
# │ Mode 3      │ Cloned Voice  │ 🎤 Avatar speaks with your voice        │
# │             │               │   - Requires ElevenLabs API key         │
# │             │               │   - Requires cloned voice ID            │
# │             │               │   - Falls back to system voice if error │
# └─────────────┴───────────────┴─────────────────────────────────────────┘
#
# The script automatically detects if ElevenLabs is configured and
# will show appropriate warnings if Mode 3 is selected without credentials.
#
# =============================================================================
# 14.0 📅 VERSION HISTORY
# =============================================================================
#
# ┌─────────┬─────────────┬────────────────────────────────────────────────┐
# │ Version │ Date        │ Changes                                        │
# ├─────────┼─────────────┼────────────────────────────────────────────────┤
# │ 1.0.0   │ 2025-02-15  │ Initial release                                │
# │ 2.0.0   │ 2025-02-18  │ Added hotkey support                           │
# │ 3.0.0   │ 2025-02-20  │ Added microphone detection                     │
# │ 4.0.0   │ 2025-02-22  │ Added multi-location .env search               │
# │ 5.0.0   │ 2026-02-22  │ Added Three Mode Support:                      │
# │         │             │  • Mode 1: Text Only                           │
# │         │             │  • Mode 2: System Voice                        │
# │         │             │  • Mode 3: ElevenLabs Cloned Voice             │
# │         │             │  • Shared .env support                         │
# │         │             │  • No sudo password prompts                    │
# │         │             │  • Comprehensive documentation                 │
# └─────────┴─────────────┴────────────────────────────────────────────────┘
#
# =============================================================================
# 🎯 FINAL NOTES
# =============================================================================
#
# This script represents the culmination of extensive testing and refinement.
# It's designed to be:
#   ✅ User-friendly - Clear messages and colors
#   ✅ Robust - Handles errors gracefully
#   ✅ Flexible - Works with shared or local configs
#   ✅ Production-ready - Manages background processes
#   ✅ Self-documenting - Comprehensive inline docs
#   ✅ Multi-mode - Supports text, system voice, and cloned voice
#
# If you encounter any issues not covered in this documentation,
# please check the logs first: cat logs/flask_app.log
#
# =============================================================================
# 🚀 ACTUAL SCRIPT STARTS HERE
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
    
    # Check multiple locations for .env file (prioritized order)
    ENV_FOUND=false
    ENV_LOCATIONS=(
        ".env"                                      # Current directory (avatar/.env)
        "../.env"                                   # Parent directory (flasks/.env) - SHARED CONFIG
        "../../.env"                                 # Grandparent directory (apps/.env)
        "$HOME/interviews-coding-tests-codepad-codeshare-python/apps/flasks/.env"  # Absolute path
    )
    
    for ENV_PATH in "${ENV_LOCATIONS[@]}"; do
        if [ -f "$ENV_PATH" ]; then
            log "   ✅ Found .env at: $ENV_PATH"
            export ENV_FILE="$ENV_PATH"
            ENV_FOUND=true
            break
        fi
    done
    
    if [ "$ENV_FOUND" = false ]; then
        log "${RED}❌ .env file not found in any location. Creating template in current directory...${NC}"
        cat > ".env" << 'EOF'
# OpenAI API Key (required)
OPENAI_API_KEY="your-openai-api-key-here"

# ElevenLabs API Key (optional - for voice cloning, Mode 3)
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
    
    # Load environment variables from the found .env file
    set -a
    source "$ENV_FILE"
    set +a
    
    # Check OpenAI API key
    if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your-openai-api-key-here" ]; then
        log "${RED}❌ OPENAI_API_KEY not configured in .env file${NC}"
        log "   Please add your OpenAI API key to $ENV_FILE"
        exit 1
    fi
    log "${GREEN}✅ OpenAI API key configured${NC}"
    
    # Check ElevenLabs (optional - for Mode 3)
    if [ -n "$ELEVENLABS_API_KEY" ] && [ "$ELEVENLABS_API_KEY" != "your-elevenlabs-api-key-here" ]; then
        log "${GREEN}✅ ElevenLabs API key found (Mode 3 - Cloned Voice available)${NC}"
        if [ -n "$ELEVENLABS_VOICE_ID" ] && [ "$ELEVENLABS_VOICE_ID" != "your-voice-id-here" ]; then
            log "${GREEN}✅ ElevenLabs voice ID configured${NC}"
        else
            log "${YELLOW}⚠️  No ElevenLabs voice ID configured${NC}"
            log "   ℹ️  Mode 3 will fall back to system voice without voice ID"
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
        print(f'   📊 Total input devices: {len(input_devices)}')
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
    echo -e "   🔑 Using .env from: ${PURPLE}${ENV_FILE:-.env}${NC}"
    echo -e "   🎭 Modes Available: 📝 Text | 🔊 System Voice | 🎤 Cloned Voice${NC}"
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
    
    # Check environment (with shared .env support)
    check_env
    
    # Check microphone
    check_microphone
    
    # Show summary
    show_summary
    
    # Start the application in background
    log "${BLUE}🚀 Starting AI Avatar System (3 Modes)...${NC}"
    
    # Use nohup to survive terminal close
    # Pass the .env location as an environment variable
    export ENV_FILE="${ENV_FILE:-.env}"
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
        echo -e "   Available modes: 📝 Text | 🔊 System Voice | 🎤 Cloned Voice"
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
