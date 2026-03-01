#!/usr/bin/env python3
"""
🎭 AI AVATAR SYSTEM - COMPLETE DOCUMENTATION v6.5.0 (Microsoft Teams Mode)
=======================================================================================

A real-time AI avatar that joins your Microsoft Teams meetings! Listens to your Teams
calls through BlackHole and makes spontaneous comments in YOUR cloned voice. 
Like having a colleague who never misses a meeting.

┌─────────────────────────────────────────────────────────────────────────────┐
│                           TABLE OF CONTENTS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1.0 OVERVIEW .................... What this system does                     │
│     1.1 Four Modes Explained ..... Text, System, Cloned, Teams Mode        │
│     1.2 How Teams Mode Works ..... BlackHole audio routing                 │
│     1.3 Architecture .............. Component diagram                       │
│                                                                             │
│ 2.0 QUICK START ................... Get running in 2 minutes               │
│     2.1 Prerequisites ............. What you need installed                │
│     2.2 Installation .............. One-line setup                         │
│     2.3 First Run ................. Launch the avatar                      │
│                                                                             │
│ 3.0 TEAMS MODE .................... The main attraction                    │
│     3.1 Setup BlackHole ............ Configure virtual audio device        │
│     3.2 Start Listening ............. Ctrl+Shift+L                         │
│     3.3 Spontaneous Comments ........ Every 20 seconds                     │
│     3.4 Talk Back ................... Ctrl+Shift+D                         │
│     3.5 Force Comment ............... Ctrl+Shift+C                         │
│     3.6 Meeting Summary ............. Ctrl+Shift+S                         │
│     3.7 Action Items ............... Auto-detected from conversation       │
│                                                                             │
│ 4.0 VOICE CLONING (Mode 3) ......... Make it sound like YOU               │
│     4.1 ElevenLabs Setup ............ Get API key and voice ID            │
│     4.2 Voice Settings .............. Stability, similarity, style         │
│     4.3 Fallback Behavior ........... System voice on error               │
│                                                                             │
│ 5.0 AUDIO SYSTEM ................... How it hears everything              │
│     5.1 BlackHole Detection ......... Finding the virtual device          │
│     5.2 Microphone Selection ........ Your voice vs. Teams audio          │
│     5.3 Silence Detection ........... Optimized for meetings              │
│     5.4 Buffer Management ........... Rolling transcript window           │
│     5.5 Teams Audio Format .......... 48kHz for better clarity            │
│                                                                             │
│ 6.0 AI ENGINE ...................... The brain behind the avatar          │
│     6.1 Whisper Transcription ....... Speech-to-text                      │
│     6.2 GPT-4 Response Generation ... Professional comments               │
│     6.3 Context Window .............. Remembers last 4 exchanges          │
│     6.4 Personality Profile ......... Helpful, laconic colleague "Art"    │
│     6.5 Action Item Detection ....... Keywords: todo, deadline, assign    │
│                                                                             │
│ 7.0 WEB INTERFACE .................. Control panel                        │
│     7.1 Status Display .............. Teams listening indicator           │
│     7.2 Control Buttons ............. Start/stop/comment/summary          │
│     7.3 Live Transcript ............. See what's being said in Teams      │
│     7.4 Meeting Summary ............. Key points and action items         │
│     7.5 Auto-refresh ................ Updates every 2 seconds             │
│                                                                             │
│ 8.0 HOTKEYS ........................ Global keyboard shortcuts           │
│     8.1 Ctrl+Shift+L ................ Toggle Teams listening              │
│     8.2 Ctrl+Shift+C ................ Force a comment now                 │
│     8.3 Ctrl+Shift+D ................ Talk to avatar                      │
│     8.4 Ctrl+Shift+S ................ Get meeting summary                 │
│     8.5 Ctrl+Shift+Q ................ Quit system                         │
│     8.6 Permissions .................. macOS Accessibility setup          │
│                                                                             │
│ 9.0 FILE STRUCTURE ................. What gets created                    │
│     9.1 Logs ......................... Service, Flask, conversations      │
│     9.2 Teams Transcript ............. Full meeting transcript            │
│     9.3 Action Items ................. Auto-detected tasks                │
│     9.4 PID File ..................... Running process ID                 │
│     9.5 Virtual Environment ........... Isolated Python packages          │
│                                                                             │
│10.0 TROUBLESHOOTING ................. Common issues and fixes             │
│    10.1 "BlackHole not found" ......... Install virtual audio device      │
│    10.2 Hotkeys not working ........... Accessibility permissions         │
│    10.3 No microphone ................. Privacy settings                  │
│    10.4 Avatar not commenting .......... Check logs, API keys             │
│    10.5 Voice not cloning .............. ElevenLabs configuration         │
│    10.6 Teams audio not captured ....... Multi-Output Device setup        │
│                                                                             │
│11.0 COST ANALYSIS ................... What this costs to run              │
│    11.1 Whisper Transcription ......... $0.006/minute                     │
│    11.2 GPT-4 Comments ................ $0.03 per comment                 │
│    11.3 ElevenLabs TTS ................ $0.30/1000 chars                  │
│    11.4 1-hour Meeting Cost ........... ~$5-10 depending on activity      │
│                                                                             │
│12.0 ADVANCED CONFIGURATION .......... Tweaking the system                 │
│    12.1 Environment Variables ......... .env file options                 │
│    12.2 Comment Frequency ............. Adjust teams_comment_interval     │
│    12.3 Voice Settings ................ ElevenLabs parameters             │
│    12.4 Model Selection ............... GPT-4 vs GPT-3.5                  │
│    12.5 Sample Rate ................... 48kHz for Teams clarity           │
│                                                                             │
│13.0 EXAMPLES ......................... What to ask                       │
│    13.1 Project Meeting ............... "When's the deadline?"            │
│    13.2 Brainstorming ................. "Good idea, I like that."         │
│    13.3 Status Update ................. "What's blocking progress?"       │
│    13.4 Action Items .................. "I'll take care of that."         │
│                                                                             │
│14.0 VERSION HISTORY .................. What's new                         │
│    14.1 v6.0.0 ....................... Base voice system                 │
│    14.2 v6.1.0 ....................... Art personality                   │
│    14.3 v6.2.0 ....................... YouTube download mode             │
│    14.4 v6.4.0 ....................... TV Watching Mode                  │
│    14.5 v6.5.0 ....................... Microsoft Teams Mode (current)    │
└─────────────────────────────────────────────────────────────────────────────┘

AUTHOR: Artem Ponomarev
VERSION: 6.5.0 (Microsoft Teams Mode)
LICENSE: MIT

=======================================================================================
1.0 OVERVIEW
=======================================================================================

1.1 FOUR MODES EXPLAINED
------------------------
┌─────────────┬───────────────────┬────────────────────────────────────────────────┐
│ Mode        │ Name              │ Description                                    │
├─────────────┼───────────────────┼────────────────────────────────────────────────┤
│ Mode 1      │ Text Only         │ 📝 Avatar types responses only                 │
│             │                   │   - No voice output                            │
│             │                   │   - Works without microphone                   │
│             │                   │   - Best for testing or quiet environments     │
├─────────────┼───────────────────┼────────────────────────────────────────────────┤
│ Mode 2      │ System Voice      │ 🔊 Avatar speaks with system TTS               │
│             │                   │   - macOS: 'say' command (natural voices)      │
│             │                   │   - Linux: 'espeak' (synthetic)                │
│             │                   │   - Windows: PowerShell SAPI                   │
│             │                   │   - Low cost, always available                 │
├─────────────┼───────────────────┼────────────────────────────────────────────────┤
│ Mode 3      │ Cloned Voice      │ 🎤 Avatar speaks with YOUR voice               │
│             │                   │   - ElevenLabs voice cloning                   │
│             │                   │   - Requires API key + voice ID                │
│             │                   │   - ~$0.30 per 1000 characters                 │
│             │                   │   - Falls back to system voice on error        │
├─────────────┼───────────────────┼────────────────────────────────────────────────┤
│ Mode 4      │ Teams Mode        │ 💼 Avatar joins Microsoft Teams meetings       │
│             │                   │   - Listens to Teams audio through BlackHole   │
│             │                   │   - Makes spontaneous comments                 │
│             │                   │   - Detects action items automatically         │
│             │                   │   - Generates meeting summaries                │
│             │                   │   - Uses YOUR cloned voice                     │
│             │                   │   - Perfect for remote work                    │
└─────────────┴───────────────────┴────────────────────────────────────────────────┘

1.2 HOW TEAMS MODE WORKS
------------------------
┌─────────────────────────────────────────────────────────────────────────────┐
│                           YOUR COMPUTER                                      │
│                                                                              │
│  ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐     │
│  │   Microsoft    │      │   BlackHole     │      │    AI Avatar    │     │
│  │   Teams App    │─────▶│  Virtual Audio  │─────▶│   Listens to    │     │
│  │   (Audio Out)  │      │     Device      │      │   Teams Chat    │     │
│  └─────────────────┘      └─────────────────┘      └────────┬────────┘     │
│                           ┌─────────────────┐               │               │
│                           │   Your Speakers │◀──────────────┘               │
│                           │   (You hear it) │    Makes comments in          │
│                           └─────────────────┘    YOUR cloned voice          │
│                                                                              │
│                           ┌─────────────────┐                              │
│                           │  Meeting Notes  │←──────────────────────────────│
│                           │  • Action items │    Auto-generates summary    │
│                           │  • Key decisions│    and tracks action items   │
│                           └─────────────────┘                              │
└─────────────────────────────────────────────────────────────────────────────┘

=======================================================================================
2.0 QUICK START
=======================================================================================

2.1 PREREQUISITES
-----------------
🐍 Python 3.8 or higher:
   python3 --version

🎤 Microphone access (for talking back):
   System Settings → Privacy & Security → Microphone → Check Terminal

⌨️ Hotkey access (optional but recommended):
   System Settings → Privacy & Security → Accessibility → Add Terminal

🎧 BlackHole (virtual audio device):
   Already installed (seen in your logs: [0] BlackHole 2ch)

💻 Microsoft Teams:
   Installed and configured

2.2 INSTALLATION
----------------
# Clone/enter the directory
cd ~/interviews-coding-tests-codepad-codeshare-python/apps/flasks/avatar

# Make launcher executable
chmod +x set-up-and-run.sh

# Run the system (handles everything)
./set-up-and-run.sh

2.3 FIRST RUN
-------------
# Open web interface
open http://localhost:5000

# In the web interface, click "Mode 4: Teams Mode"
# OR press Ctrl+Shift+L to start listening immediately
"""

import os
import sys
import json
import threading
import queue
import time
import tempfile
import subprocess
import platform
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

# Third-party imports
try:
    import sounddevice as sd
    import soundfile as sf
    import numpy as np
    from openai import OpenAI
    import requests
    import keyboard
    from flask import Flask, render_template_string, jsonify, request
    import speech_recognition as sr
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("📦 Install with: pip install sounddevice soundfile numpy openai requests keyboard flask speechrecognition python-dotenv")
    sys.exit(1)

# Load environment variables
load_dotenv()
parent_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(parent_env):
    load_dotenv(dotenv_path=parent_env)
    print(f"✅ Loaded .env from: {parent_env}")

class ConversationState(Enum):
    HUMAN_LEAD = "human_lead"        # You're talking
    AVATAR_LISTENING = "avatar_listening"  # Avatar listening to Teams
    AVATAR_COMMENTING = "avatar_commenting"  # Avatar making a comment
    TRANSITIONING = "transitioning"

class ResponseMode(Enum):
    TEXT_ONLY = "text"        # Mode 1: Text only
    SYSTEM_VOICE = "system"    # Mode 2: System TTS
    CLONED_VOICE = "cloned"    # Mode 3: ElevenLabs cloned voice
    TEAMS_MODE = "teams"       # Mode 4: Microsoft Teams Mode

class ConversationDelegator:
    """Main controller class for the AI Avatar Microsoft Teams system."""
    
    def __init__(self):
        """Initialize the avatar system with all components."""
        self.state = ConversationState.HUMAN_LEAD
        self.is_running = True
        self.avatar_active = False

        # Response mode (default: text-only)
        self.mode = ResponseMode.TEXT_ONLY

        # Configuration
        self.config = self.load_config()
        
        # Initialize logging FIRST - create logs directory and set up log file
        os.makedirs("logs", exist_ok=True)
        self.log_file = "logs/delegator.log"
        self.log("🔧 Initializing AI Avatar Microsoft Teams System...")

        # Audio configuration - OPTIMIZED FOR TEAMS (48kHz)
        self.sample_rate = 48000  # Teams uses 48kHz
        self.chunk_size = 2048    # Larger chunks for better capture
        self.silence_threshold = 0.01  # More sensitive for voices
        self.silence_duration = 1.2    # Slightly shorter for meetings

        # Teams Mode settings
        self.teams_listening = False
        self.last_teams_comment_time = datetime.now()
        self.teams_comment_interval = 20  # More frequent comments in meetings
        self.teams_audio_buffer = np.array([], dtype=np.float32)
        self.teams_transcript_buffer = []  # Store recent Teams transcripts
        self.last_teams_transcript = ""
        
        # Meeting intelligence
        self.meeting_transcript = []  # Full meeting transcript
        self.action_items = []        # Detected action items
        self.key_decisions = []       # Key decisions made
        self.meeting_start_time = None

        # Conversation management
        self.conversation_history = []
        self.transcriptions = []
        self.responses = []

        # Thread control
        self.avatar_thread = None
        self.teams_listener_thread = None
        self._stop_avatar_loop = threading.Event()
        self._stop_teams_listener = threading.Event()

        # Hotkey status
        self.hotkeys_enabled = False

        # Initialize components
        self.setup_apis()
        self.setup_audio()
        self.setup_hotkeys()
        self.setup_flask()
        
        self.log("✅ Avatar system initialized successfully")

    def load_config(self):
        """Load configuration from environment variables."""
        config = {
            "openai_api_key": os.getenv('OPENAI_API_KEY'),
            "elevenlabs_api_key": os.getenv('ELEVENLABS_API_KEY'),
            "elevenlabs_voice_id": os.getenv('ELEVENLABS_VOICE_ID'),
            "gpt_model": os.getenv('GPT_MODEL', 'gpt-4'),
            "port": int(os.getenv('PORT', 5000)),
            "hotkey_listen": "ctrl+shift+l",      # Start listening to Teams
            "hotkey_comment": "ctrl+shift+c",      # Force a comment
            "hotkey_talk": "ctrl+shift+d",         # Talk to avatar
            "hotkey_summary": "ctrl+shift+s",      # Get meeting summary
            "hotkey_quit": "ctrl+shift+q",
            "avatar_name": "AI Avatar"
        }
        return config

    def log(self, message):
        """Log message with timestamp to both console and file."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')

    def setup_apis(self):
        """Initialize API clients for OpenAI and speech recognition."""
        if self.config["openai_api_key"]:
            self.openai_client = OpenAI(api_key=self.config["openai_api_key"])
            self.log("✅ OpenAI API configured")
        else:
            self.log("❌ OpenAI API key missing - please add to .env file")

        # Setup speech recognition for user's voice
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            self.log("✅ Speech recognition ready")

    def setup_audio(self):
        """Query and log available audio devices - OPTIMIZED FOR TEAMS."""
        try:
            devices = sd.query_devices()
            self.log("✅ Audio system ready")
            self.log("📋 Available input devices:")
            
            # Find and highlight BlackHole and Teams devices
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    device_name = dev['name'].lower()
                    if 'blackhole' in device_name:
                        self.log(f"   [{i}] {dev['name']} ← 🎧 USE THIS FOR TEAMS AUDIO")
                    elif 'microsoft teams' in device_name:
                        self.log(f"   [{i}] {dev['name']} ← 💻 TEAMS DEVICE")
                    else:
                        self.log(f"   [{i}] {dev['name']}")
                        
        except Exception as e:
            self.log(f"❌ Audio setup error: {e}")

    def setup_hotkeys(self):
        """Register global hotkey listeners."""
        try:
            keyboard.add_hotkey(self.config["hotkey_listen"], self.toggle_teams_listening)
            keyboard.add_hotkey(self.config["hotkey_comment"], self.force_comment)
            keyboard.add_hotkey(self.config["hotkey_talk"], self.start_talking_to_avatar)
            keyboard.add_hotkey(self.config["hotkey_summary"], self.get_meeting_summary)
            keyboard.add_hotkey(self.config["hotkey_quit"], self.shutdown)
            self.hotkeys_enabled = True
            self.log(f"✅ Hotkeys registered: {self.config['hotkey_listen']} / {self.config['hotkey_comment']} / {self.config['hotkey_talk']} / {self.config['hotkey_summary']}")
        except Exception as e:
            self.hotkeys_enabled = False
            self.log(f"⚠️ Hotkeys unavailable: {e}")
            self.log("💡 On macOS: System Settings → Privacy & Security → Accessibility → Add your terminal app")

    def setup_flask(self):
        """Configure Flask web server with all routes."""
        self.app = Flask(__name__)

        @self.app.route('/')
        def index():
            return self.web_interface()

        @self.app.route('/api/state')
        def api_state():
            return jsonify(self.get_system_state())

        @self.app.route('/api/set_mode', methods=['POST'])
        def api_set_mode():
            data = request.get_json()
            if data and 'mode' in data:
                mode_str = data['mode']
                if mode_str == 'text':
                    self.mode = ResponseMode.TEXT_ONLY
                    self.log("🔄 Mode changed to: 📝 Text Only")
                elif mode_str == 'system':
                    self.mode = ResponseMode.SYSTEM_VOICE
                    self.log("🔄 Mode changed to: 🔊 System Voice")
                elif mode_str == 'cloned':
                    if self.config["elevenlabs_api_key"] and self.config["elevenlabs_voice_id"]:
                        self.mode = ResponseMode.CLONED_VOICE
                        self.log("🔄 Mode changed to: 🎤 Cloned Voice")
                    else:
                        self.log("⚠️ ElevenLabs not configured")
                        return jsonify({"success": False}), 400
                elif mode_str == 'teams':
                    self.mode = ResponseMode.TEAMS_MODE
                    self.log("🔄 Mode changed to: 💼 Microsoft Teams Mode")
                return jsonify({"success": True, "mode": self.mode.value})
            return jsonify({"success": False}), 400

        @self.app.route('/api/teams/listen', methods=['POST'])
        def api_teams_listen():
            self.toggle_teams_listening()
            return jsonify({"success": True, "listening": self.teams_listening})

        @self.app.route('/api/teams/comment', methods=['POST'])
        def api_teams_comment():
            self.force_comment()
            return jsonify({"success": True})
            
        @self.app.route('/api/teams/summary', methods=['GET'])
        def api_teams_summary():
            summary = self.generate_meeting_summary()
            return jsonify({"success": True, "summary": summary})

    def get_system_state(self):
        """Return current system state for API."""
        meeting_duration = 0
        if self.meeting_start_time and self.teams_listening:
            meeting_duration = int((datetime.now() - self.meeting_start_time).total_seconds() / 60)
            
        return {
            "state": self.state.value,
            "transcriptions": self.transcriptions[-10:],
            "responses": self.responses[-10:],
            "mode": self.mode.value,
            "teams_listening": self.teams_listening,
            "last_teams_heard": self.last_teams_transcript[-100:] if self.last_teams_transcript else "",
            "meeting_duration": meeting_duration,
            "action_items": len(self.action_items),
            "elevenlabs_configured": bool(self.config["elevenlabs_api_key"] and self.config["elevenlabs_voice_id"]),
            "timestamp": datetime.now().isoformat()
        }

    def get_blackhole_device(self):
        """Find BlackHole audio device for Teams audio capture."""
        try:
            devices = sd.query_devices()
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0 and 'blackhole' in dev['name'].lower():
                    self.log(f"🎧 Found BlackHole device: {dev['name']} (ID: {i})")
                    return i
            self.log("⚠️ BlackHole not found - install from https://github.com/ExistentialAudio/BlackHole")
            return None
        except Exception as e:
            self.log(f"❌ BlackHole detection error: {e}")
            return None

    def toggle_teams_listening(self):
        """Start or stop listening to Teams audio."""
        if not self.teams_listening:
            self.start_teams_listening()
        else:
            self.stop_teams_listening()

    def start_teams_listening(self):
        """Start avatar listening to Microsoft Teams."""
        if self.teams_listening:
            return

        blackhole_id = self.get_blackhole_device()
        if blackhole_id is None:
            self.speak_message("BlackHole not installed. Can't listen to Teams.")
            return

        self.teams_listening = True
        self.state = ConversationState.AVATAR_LISTENING
        self._stop_teams_listener.clear()
        self.meeting_start_time = datetime.now()
        
        self.speak_message("Okay, I'm listening to your Teams meeting.")
        
        # Start Teams listener thread
        self.teams_listener_thread = threading.Thread(
            target=self.teams_listening_loop,
            args=(blackhole_id,),
            daemon=True
        )
        self.teams_listener_thread.start()
        
        self.log("💼 Started listening to Microsoft Teams")

    def stop_teams_listening(self):
        """Stop listening to Teams."""
        if not self.teams_listening:
            return
            
        self.teams_listening = False
        self._stop_teams_listener.set()
        self.state = ConversationState.HUMAN_LEAD
        
        # Generate meeting summary
        if len(self.meeting_transcript) > 0:
            summary = self.generate_meeting_summary()
            self.speak_message("Here's your meeting summary.")
            self.log(f"📋 Meeting summary generated")
        else:
            self.speak_message("Stopped listening to Teams.")
        
        self.log("⏹️ Stopped Teams listening")

    def teams_listening_loop(self, device_id):
        """
        Listen to Microsoft Teams audio through BlackHole.
        Optimized for 48kHz sample rate and voice recognition.
        """
        self.log("🔄 Teams listening loop started")
        
        audio_buffer = np.array([], dtype=np.float32)
        last_activity = datetime.now()
        
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                device=device_id,
                blocksize=self.chunk_size
            ) as stream:
                
                while self.teams_listening and not self._stop_teams_listener.is_set():
                    try:
                        # Read audio from system (Teams)
                        audio_chunk, overflowed = stream.read(self.chunk_size)
                        audio_chunk = audio_chunk.squeeze()
                        
                        # Check if there's audio playing
                        amplitude = np.max(np.abs(audio_chunk)) if len(audio_chunk) > 0 else 0
                        
                        if amplitude > self.silence_threshold:
                            # Someone is talking in Teams
                            audio_buffer = np.concatenate((audio_buffer, audio_chunk))
                            last_activity = datetime.now()
                        elif len(audio_buffer) > 0:
                            # Silence detected - process what was said
                            silence_time = (datetime.now() - last_activity).total_seconds()
                            
                            if silence_time > 1.5 and len(audio_buffer) > self.sample_rate * 1.5:
                                # Process a chunk of Teams audio (at least 1.5 seconds)
                                self.process_teams_audio(audio_buffer)
                                audio_buffer = np.array([], dtype=np.float32)
                        
                        # Make spontaneous comments every ~20 seconds during meeting
                        if (datetime.now() - self.last_teams_comment_time).total_seconds() > self.teams_comment_interval:
                            if len(self.teams_transcript_buffer) > 0:
                                self.make_teams_comment()
                                self.last_teams_comment_time = datetime.now()
                        
                        time.sleep(0.1)
                        
                    except Exception as e:
                        self.log(f"❌ Teams loop error: {e}")
                        time.sleep(0.5)
                        
        except Exception as e:
            self.log(f"❌ Teams stream error: {e}")
        
        self.log("🔄 Teams listening loop ended")

    def process_teams_audio(self, audio_chunk):
        """Transcribe Teams audio and store it."""
        try:
            # Transcribe what was just said in Teams
            transcript = self.transcribe_with_whisper(audio_chunk)
            
            if transcript and len(transcript) > 10:
                self.last_teams_transcript = transcript
                
                # Save to full meeting transcript
                self.meeting_transcript.append({
                    'time': datetime.now(),
                    'text': transcript
                })
                
                # Store in rolling buffer (keep last 5 for context)
                self.teams_transcript_buffer.append({
                    'time': datetime.now(),
                    'text': transcript
                })
                if len(self.teams_transcript_buffer) > 5:
                    self.teams_transcript_buffer.pop(0)
                
                # Check for action items
                self.detect_action_items(transcript)
                
                self.log(f"💼 Teams: {transcript[:100]}...")
                
                # Save to dedicated Teams log
                with open("logs/teams_transcript.log", "a") as f:
                    f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {transcript}\n")
                
        except Exception as e:
            self.log(f"❌ Teams audio processing error: {e}")

    def detect_action_items(self, transcript):
        """Detect potential action items from meeting conversation."""
        action_keywords = [
            'todo', 'to do', 'action item', 'need to', 'have to', 
            'must', 'should', 'will', 'going to', 'assign', 'deadline',
            'due by', 'remind me', 'follow up', 'send', 'email', 'schedule',
            'book', 'create', 'make', 'do', 'finish', 'complete'
        ]
        
        transcript_lower = transcript.lower()
        for keyword in action_keywords:
            if keyword in transcript_lower:
                self.action_items.append({
                    'time': datetime.now(),
                    'text': transcript,
                    'keyword': keyword
                })
                self.log(f"📋 Potential action item detected: {transcript[:50]}...")
                break

    def make_teams_comment(self):
        """Avatar makes a spontaneous comment about the Teams meeting."""
        if not self.teams_transcript_buffer or self.state == ConversationState.AVATAR_COMMENTING:
            return
        
        # Combine recent transcripts for context
        recent_content = " ".join([t['text'] for t in self.teams_transcript_buffer])
        
        try:
            prompt = f"""
            You're listening to a Microsoft Teams meeting. You just heard:
            
            "{recent_content}"
            
            Make a quick, professional comment about what was said. Be laconic, like Art.
            Just 1-2 sentences. Could be agreement, clarification, or observation.
            You're like a helpful colleague listening in.
            
            Examples:
            - "Good point about the deadline."
            - "Makes sense, we should do that."
            - "I can help with that task."
            - "When's that due exactly?"
            - "Makes sense to me."
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.config["gpt_model"],
                messages=[
                    {"role": "system", "content": "You're Art - laconic, direct, helpful. Make short, relevant comments about the Teams meeting."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=40,
                temperature=0.6
            )
            
            comment = response.choices[0].message.content.strip()
            
            # Store and speak the comment
            self.state = ConversationState.AVATAR_COMMENTING
            
            self.responses.append({
                'time': datetime.now(),
                'text': f"💼 (Teams comment): {comment}",
                'type': 'response'
            })
            
            self.speak_message(comment)
            
            self.state = ConversationState.AVATAR_LISTENING
            self.log(f"💬 Teams comment: {comment}")
            
        except Exception as e:
            self.log(f"❌ Comment generation error: {e}")

    def generate_meeting_summary(self):
        """Generate a summary of the entire Teams meeting."""
        if not self.meeting_transcript:
            return "No meeting transcript available."
        
        try:
            # Combine last 30 exchanges for summary
            recent_transcript = " ".join([t['text'] for t in self.meeting_transcript[-30:]])
            
            action_items_text = ""
            if self.action_items:
                action_items_text = "\nAction Items Detected:\n"
                for i, item in enumerate(self.action_items[-10:], 1):
                    action_items_text += f"{i}. {item['text'][:100]}...\n"
            
            prompt = f"""
            Summarize this Microsoft Teams meeting conversation:
            
            "{recent_transcript}"
            
            {action_items_text}
            
            Provide:
            1. Key discussion points (2-3 bullet points)
            2. Action items (who needs to do what)
            3. Decisions made
            4. Follow-up needed
            
            Be concise, professional, like Art.
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.config["gpt_model"],
                messages=[
                    {"role": "system", "content": "You're Art - laconic, direct. Summarize the meeting key points professionally."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.3
            )
            
            summary = response.choices[0].message.content.strip()
            
            self.responses.append({
                'time': datetime.now(),
                'text': f"📋 Meeting Summary:\n{summary}",
                'type': 'response'
            })
            
            # Save summary to file
            with open("logs/meeting_summaries.log", "a") as f:
                f.write(f"\n--- Meeting Summary {datetime.now().strftime('%Y-%m-%d %H:%M')} ---\n")
                f.write(summary)
                f.write("\n" + "="*50 + "\n")
            
            return summary
            
        except Exception as e:
            self.log(f"❌ Summary generation error: {e}")
            return "Couldn't generate summary."

    def force_comment(self):
        """Force the avatar to make a comment right now."""
        self.make_teams_comment()

    def get_meeting_summary(self):
        """Hotkey handler to get meeting summary."""
        summary = self.generate_meeting_summary()
        self.speak_message("Here's the meeting summary so far.")
        return summary

    def start_talking_to_avatar(self):
        """Start a conversation with the avatar (overlay on Teams mode)."""
        if not self.avatar_active:
            self.avatar_active = True
            self._stop_avatar_loop.clear()
            
            # Start conversation thread (listens to YOU, not Teams)
            self.avatar_thread = threading.Thread(
                target=self.avatar_conversation_loop,
                daemon=True
            )
            self.avatar_thread.start()
            
            self.speak_message("Yeah?")
            self.log("🎭 Avatar ready to talk")

    def avatar_conversation_loop(self):
        """Listen to user's voice and respond (overlay on Teams mode)."""
        self.log("🔄 Conversation loop started")
        
        device_id = self.get_microphone_device()
        if device_id is None:
            self.log("❌ No microphone found")
            return
        
        audio_buffer = np.array([], dtype=np.float32)
        last_activity = datetime.now()
        
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                device=device_id,
                blocksize=self.chunk_size
            ) as stream:
                
                while self.avatar_active and not self._stop_avatar_loop.is_set():
                    try:
                        audio_chunk, overflowed = stream.read(self.chunk_size)
                        audio_chunk = audio_chunk.squeeze()
                        
                        amplitude = np.max(np.abs(audio_chunk)) if len(audio_chunk) > 0 else 0
                        
                        if amplitude > self.silence_threshold:
                            # You're talking
                            audio_buffer = np.concatenate((audio_buffer, audio_chunk))
                            last_activity = datetime.now()
                        elif len(audio_buffer) > 0:
                            # Silence after you spoke
                            silence_time = (datetime.now() - last_activity).total_seconds()
                            
                            if silence_time > self.silence_duration and len(audio_buffer) > self.sample_rate:
                                # Process your speech
                                user_speech = self.transcribe_with_whisper(audio_buffer)
                                
                                if user_speech and len(user_speech) > 2:
                                    self.log(f"🎤 You said: {user_speech}")
                                    
                                    self.transcriptions.append({
                                        'time': datetime.now(),
                                        'text': user_speech,
                                        'type': 'input'
                                    })
                                    
                                    # Generate response (with Teams context)
                                    ai_response = self.generate_response(user_speech)
                                    
                                    self.responses.append({
                                        'time': datetime.now(),
                                        'text': ai_response,
                                        'type': 'response'
                                    })
                                    
                                    self.speak_message(ai_response)
                                
                                audio_buffer = np.array([], dtype=np.float32)
                                
                    except Exception as e:
                        self.log(f"❌ Conversation loop error: {e}")
                        time.sleep(0.1)
                        
        except Exception as e:
            self.log(f"❌ Audio stream error: {e}")
        
        self.log("🔄 Conversation loop ended")

    def generate_response(self, user_input):
        """Generate response with context of the Teams meeting."""
        try:
            # Add Teams context if available
            teams_context = ""
            if self.teams_transcript_buffer:
                recent_teams = " ".join([t['text'] for t in self.teams_transcript_buffer[-2:]])
                teams_context = f"\nThe Teams meeting was discussing: \"{recent_teams}\""
            
            system_prompt = f"""
            You're Art. Laconic, direct, helpful. You're listening to a Teams meeting with me.
            {teams_context}
            
            Respond naturally to what I say. Short sentences. Like a helpful colleague.
            """
            
            messages = [
                {"role": "system", "content": system_prompt},
                *self.conversation_history[-4:],
                {"role": "user", "content": user_input}
            ]
            
            response = self.openai_client.chat.completions.create(
                model=self.config["gpt_model"],
                messages=messages,
                max_tokens=60,
                temperature=0.5
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            
            # Keep history manageable
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            return ai_response
            
        except Exception as e:
            self.log(f"❌ GPT error: {e}")
            return "Huh?"

    def get_microphone_device(self):
        """Find microphone for user's voice (skip BlackHole)."""
        try:
            devices = sd.query_devices()
            # Skip BlackHole for user voice - we want actual mic
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    name = dev['name'].lower()
                    if 'blackhole' not in name:
                        if 'macbook' in name or 'built-in' in name:
                            self.log(f"🎤 Using microphone: {dev['name']}")
                            return i
            # Fallback to first non-BlackHole device
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0 and 'blackhole' not in dev['name'].lower():
                    self.log(f"🎤 Using fallback microphone: {dev['name']}")
                    return i
            return 0
        except Exception as e:
            self.log(f"❌ Microphone detection error: {e}")
            return 0

    def transcribe_with_whisper(self, audio_data):
        """Transcribe audio using OpenAI Whisper."""
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                sf.write(tmp_file.name, audio_data, self.sample_rate)
                with open(tmp_file.name, 'rb') as f:
                    transcript = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=f,
                        response_format="text"
                    )
                os.unlink(tmp_file.name)
                return transcript.strip()
        except Exception as e:
            self.log(f"❌ Whisper transcription error: {e}")
            return ""

    def text_to_speech(self, text):
        """ElevenLabs TTS - YOUR cloned voice."""
        if not self.config["elevenlabs_api_key"] or not self.config["elevenlabs_voice_id"]:
            return None
            
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.config['elevenlabs_voice_id']}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.config['elevenlabs_api_key']
            }
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            response = requests.post(url, json=data, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.content
            self.log(f"⚠️ ElevenLabs API error: {response.status_code}")
            return None
        except Exception as e:
            self.log(f"❌ ElevenLabs TTS error: {e}")
            return None

    def play_audio_data(self, audio_data):
        """Play audio data using system audio player."""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
                f.write(audio_data)
                f.flush()
                subprocess.run(['afplay', f.name], check=True)
                os.unlink(f.name)
                return True
        except Exception as e:
            self.log(f"❌ Audio playback error: {e}")
            return False

    def system_tts(self, text):
        """Use macOS 'say' command for TTS fallback."""
        try:
            os.system(f'say "{text}"')
            return True
        except Exception as e:
            self.log(f"❌ System TTS error: {e}")
            return False

    def speak_message(self, text):
        """Speak a message using the selected mode."""
        if not text.strip():
            return False
            
        if self.mode == ResponseMode.TEXT_ONLY:
            self.log(f"📝 {text}")
            return True
        elif self.mode == ResponseMode.SYSTEM_VOICE:
            return self.system_tts(text)
        elif self.mode in [ResponseMode.CLONED_VOICE, ResponseMode.TEAMS_MODE]:
            audio = self.text_to_speech(text)
            if audio:
                return self.play_audio_data(audio)
            return self.system_tts(text)
        return False

    def web_interface(self):
        """Render the web interface for Teams mode."""
        cutoff_time = datetime.now() - timedelta(minutes=10)
        recent = [t for t in self.transcriptions if t['time'] > cutoff_time] + \
                 [r for r in self.responses if r['time'] > cutoff_time]
        recent.sort(key=lambda x: x['time'], reverse=True)
        
        # Get recent Teams transcripts
        teams_transcripts = self.teams_transcript_buffer[::-1] if self.teams_transcript_buffer else []
        
        status_info = {
            ConversationState.HUMAN_LEAD: {"text": "👤 READY", "color": "#27ae60"},
            ConversationState.AVATAR_LISTENING: {"text": "💼 LISTENING TO TEAMS", "color": "#0078d4"},
            ConversationState.AVATAR_COMMENTING: {"text": "💬 COMMENTING", "color": "#f39c12"},
            ConversationState.TRANSITIONING: {"text": "🔄 TRANSITIONING", "color": "#f39c12"}
        }
        current = status_info.get(self.state, status_info[ConversationState.HUMAN_LEAD])
        
        return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>🎭 AI Avatar - Microsoft Teams Mode</title>
    <meta http-equiv="refresh" content="2">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #2d3748;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .teams-header {
            background: #0078d4;
            color: white;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
            text-align: center;
        }
        .teams-header h1 {
            margin: 0;
            font-size: 2em;
        }
        .teams-header p {
            margin: 10px 0 0;
            opacity: 0.9;
        }
        .status-badge {
            display: inline-block;
            padding: 15px 30px;
            border-radius: 50px;
            font-weight: bold;
            color: white;
            font-size: 1.2em;
            margin: 20px 0;
            background-color: {{ status_color }};
        }
        .hotkey-panel {
            background: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        .hotkey-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }
        .hotkey-item {
            background: #34495e;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
        }
        .hotkey-key {
            background: #f1c40f;
            color: #2c3e50;
            padding: 5px 10px;
            border-radius: 5px;
            font-weight: bold;
            display: inline-block;
            margin-bottom: 5px;
        }
        .teams-controls {
            display: flex;
            gap: 10px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        .teams-button {
            flex: 1;
            min-width: 150px;
            padding: 15px;
            border: none;
            border-radius: 10px;
            font-weight: bold;
            cursor: pointer;
            font-size: 1.1em;
        }
        .teams-button.start {
            background: #0078d4;
            color: white;
        }
        .teams-button.stop {
            background: #f56565;
            color: white;
        }
        .teams-button.comment {
            background: #9f7aea;
            color: white;
        }
        .teams-button.summary {
            background: #48bb78;
            color: white;
        }
        
        .transcript-panel {
            background: #1a202c;
            color: #a0aec0;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            font-family: 'Courier New', monospace;
            border: 2px solid #0078d4;
        }
        .transcript-panel h3 {
            color: #fbbf24;
            margin-top: 0;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .transcript-panel h3 .live-badge {
            background: #ef4444;
            color: white;
            font-size: 0.7em;
            padding: 3px 8px;
            border-radius: 20px;
            animation: pulse 1.5s infinite;
        }
        .transcript-entry {
            padding: 10px;
            margin: 8px 0;
            background: #2d3748;
            border-radius: 8px;
            border-left: 4px solid #0078d4;
            color: #e2e8f0;
            font-size: 1.1em;
            word-wrap: break-word;
        }
        .transcript-entry .timestamp {
            color: #9f7aea;
            font-size: 0.8em;
            margin-right: 10px;
        }
        .transcript-entry .speaker {
            color: #fbbf24;
            font-weight: bold;
            margin-right: 10px;
        }
        .transcript-entry .text {
            color: #e2e8f0;
        }
        .transcript-empty {
            color: #718096;
            font-style: italic;
            text-align: center;
            padding: 20px;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .meeting-info {
            display: flex;
            gap: 20px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        .info-card {
            background: #edf2f7;
            padding: 15px;
            border-radius: 10px;
            flex: 1;
            min-width: 120px;
            text-align: center;
        }
        .info-card .label {
            font-size: 0.9em;
            color: #4a5568;
        }
        .info-card .value {
            font-size: 1.5em;
            font-weight: bold;
            color: #0078d4;
        }
        
        .now-watching {
            background: #edf2f7;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            font-style: italic;
            border-left: 4px solid #0078d4;
        }
        .conversation {
            margin-top: 20px;
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 15px;
        }
        .message {
            margin: 15px 0;
            padding: 15px;
            border-radius: 15px;
        }
        .user-message {
            background: #e3f2fd;
            margin-left: 20%;
        }
        .avatar-message {
            background: #f3e5f5;
            margin-right: 20%;
        }
        .teams-message {
            background: #e6f2ff;
            margin: 10px 0;
            border-left: 4px solid #0078d4;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="teams-header">
            <h1>💼 AI Avatar - Microsoft Teams Mode</h1>
            <p>Avatar listens to your Teams meetings and comments in YOUR voice</p>
        </div>
        
        <div style="text-align: center;">
            <div class="status-badge" style="background-color: {{ status_color }};">
                {{ status_text }}
            </div>
        </div>
        
        <div class="meeting-info">
            <div class="info-card">
                <div class="label">Meeting Duration</div>
                <div class="value">{{ meeting_duration }} min</div>
            </div>
            <div class="info-card">
                <div class="label">Action Items</div>
                <div class="value">{{ action_items }}</div>
            </div>
            <div class="info-card">
                <div class="label">Status</div>
                <div class="value">{% if teams_listening %}🎤 Active{% else %}⏸️ Paused{% endif %}</div>
            </div>
        </div>
        
        <div class="hotkey-panel">
            <h3>🎮 Hotkeys (works globally)</h3>
            <div class="hotkey-grid">
                <div class="hotkey-item">
                    <div class="hotkey-key">Ctrl+Shift+L</div>
                    <div>Start/Stop Teams Listening</div>
                </div>
                <div class="hotkey-item">
                    <div class="hotkey-key">Ctrl+Shift+C</div>
                    <div>Force Comment Now</div>
                </div>
                <div class="hotkey-item">
                    <div class="hotkey-key">Ctrl+Shift+D</div>
                    <div>Talk to Avatar</div>
                </div>
                <div class="hotkey-item">
                    <div class="hotkey-key">Ctrl+Shift+S</div>
                    <div>Get Meeting Summary</div>
                </div>
                <div class="hotkey-item">
                    <div class="hotkey-key">Ctrl+Shift+Q</div>
                    <div>Quit</div>
                </div>
            </div>
        </div>
        
        <div class="teams-controls">
            {% if not teams_listening %}
                <button class="teams-button start" onclick="startListening()">💼 Start Teams Listening</button>
            {% else %}
                <button class="teams-button stop" onclick="stopListening()">⏹️ Stop Listening</button>
                <button class="teams-button comment" onclick="forceComment()">💬 Make Comment Now</button>
                <button class="teams-button summary" onclick="getSummary()">📋 Meeting Summary</button>
            {% endif %}
        </div>
        
        <!-- Live Transcription Panel -->
        <div class="transcript-panel">
            <h3>
                🎤 LIVE: What's Being Said in Teams 
                <span class="live-badge">LIVE</span>
            </h3>
            {% if teams_transcripts %}
                {% for transcript in teams_transcripts %}
                    <div class="transcript-entry">
                        <span class="timestamp">{{ transcript.time.strftime('%H:%M:%S') }}</span>
                        <span class="speaker">💼 Teams:</span>
                        <span class="text">"{{ transcript.text }}"</span>
                    </div>
                {% endfor %}
            {% else %}
                <div class="transcript-empty">
                    🔇 No Teams audio detected. Make sure BlackHole is routing audio from Teams.
                </div>
            {% endif %}
        </div>
        
        {% if last_teams_heard %}
        <div class="now-watching">
            <strong>💼 Just Heard in Teams:</strong> "{{ last_teams_heard }}"
        </div>
        {% endif %}
        
        <h3>📝 Conversation</h3>
        <div class="conversation">
            {% if recent %}
                {% for entry in recent %}
                    <div class="message 
                        {% if entry.type == 'input' %}user-message
                        {% elif 'Teams comment' in entry.text %}teams-message
                        {% else %}avatar-message{% endif %}">
                        <div class="message-header">
                            <span>
                                {% if entry.type == 'input' %}👤 You
                                {% elif 'Teams comment' in entry.text %}💼 Avatar (in Teams)
                                {% else %}🎭 Avatar{% endif %}
                            </span>
                            <span>{{ entry.time.strftime('%H:%M:%S') }}</span>
                        </div>
                        <div class="message-content">{{ entry.text }}</div>
                    </div>
                {% endfor %}
            {% else %}
                <p style="text-align: center; color: #999; padding: 40px;">
                    Join a Teams meeting and start listening. Your avatar will comment in YOUR voice!
                </p>
            {% endif %}
        </div>
    </div>
    
    <script>
        function startListening() {
            fetch('/api/teams/listen', { method: 'POST' })
                .then(() => location.reload());
        }
        function stopListening() {
            fetch('/api/teams/listen', { method: 'POST' })
                .then(() => location.reload());
        }
        function forceComment() {
            fetch('/api/teams/comment', { method: 'POST' })
                .then(() => setTimeout(() => location.reload(), 2000));
        }
        function getSummary() {
            fetch('/api/teams/summary')
                .then(response => response.json())
                .then(data => {
                    alert('Meeting Summary:\n\n' + data.summary);
                    location.reload();
                });
        }
    </script>
</body>
</html>
        """,
        status_text=current["text"],
        status_color=current["color"],
        state=self.state.value,
        recent=recent,
        teams_listening=self.teams_listening,
        last_teams_heard=self.last_teams_transcript[:200] if self.last_teams_transcript else "",
        teams_transcripts=teams_transcripts,
        meeting_duration=self.get_system_state().get('meeting_duration', 0),
        action_items=len(self.action_items),
        mode=self.mode.value
        )

    def run(self):
        """Main loop - start the Flask server."""
        self.log("\n" + "="*60)
        self.log("🎭 AI AVATAR - MICROSOFT TEAMS MODE (v6.5.0)")
        self.log("="*60)
        self.log("HOW TO USE:")
        self.log("1. Join a Microsoft Teams meeting")
        self.log("2. Press Ctrl+Shift+L to start avatar listening")
        self.log("3. Avatar makes comments every ~20 seconds in YOUR voice")
        self.log("4. Press Ctrl+Shift+D to talk back")
        self.log("5. Press Ctrl+Shift+C for instant comment")
        self.log("6. Press Ctrl+Shift+S for meeting summary")
        self.log("="*60)
        self.log(f"🌐 Web Interface: http://localhost:{self.config['port']}")
        self.log("="*60)
        
        if not self.config["openai_api_key"]:
            self.log("❌ CRITICAL: OpenAI API key not configured")
            self.log("   Please add OPENAI_API_KEY to your .env file")
            return

        if self.config["elevenlabs_api_key"] and self.config["elevenlabs_voice_id"]:
            self.log("✅ ElevenLabs configured - Teams Mode will use YOUR voice")
            self.log(f"🎤 Voice ID: {self.config['elevenlabs_voice_id']}")
        else:
            self.log("ℹ️ ElevenLabs not configured - Teams Mode will use system voice")
        
        self.log("\n📋 Audio Setup Required:")
        self.log("   1. Open Audio MIDI Setup")
        self.log("   2. Create Multi-Output Device with:")
        self.log("      - BlackHole 2ch (for avatar)")
        self.log("      - Your speakers/headphones (for you)")
        self.log("   3. Set as default output device")
        self.log("\n💡 Teams will now route audio to both you AND the avatar!\n")
        
        try:
            self.app.run(host='0.0.0.0', port=self.config["port"], debug=False, use_reloader=False)
        except KeyboardInterrupt:
            self.shutdown()
        except Exception as e:
            self.log(f"❌ System error: {e}")
            self.shutdown()

    def shutdown(self):
        """Clean shutdown of all threads and processes."""
        self.log("🛑 Shutting down system...")
        self.is_running = False
        self.teams_listening = False
        self.avatar_active = False
        self._stop_teams_listener.set()
        self._stop_avatar_loop.set()
        
        # Generate final meeting summary if there was a meeting
        if len(self.meeting_transcript) > 5:
            self.log("📋 Generating final meeting summary...")
            self.generate_meeting_summary()
        
        # Wait for threads to finish
        if self.avatar_thread and self.avatar_thread.is_alive():
            self.avatar_thread.join(timeout=2.0)
        if self.teams_listener_thread and self.teams_listener_thread.is_alive():
            self.teams_listener_thread.join(timeout=2.0)
        
        self.log("✅ System shutdown complete")


def main():
    """Main entry point."""
    print("\n" + "="*60)
    print("🎭 AI AVATAR - MICROSOFT TEAMS MODE v6.5.0")
    print("="*60)
    print("This mode lets your avatar:")
    print("  💼 Listen to your Microsoft Teams meetings")
    print("  💬 Make spontaneous comments in YOUR voice")
    print("  🗣️  Talk back during the meeting")
    print("  📋 Auto-detect action items")
    print("  📊 Generate meeting summaries")
    print("="*60)
    print("REQUIRED: BlackHole (already installed)")
    print("Setup: https://github.com/ExistentialAudio/BlackHole")
    print("\nAUDIO SETUP:")
    print("1. Open Audio MIDI Setup")
    print("2. Create Multi-Output Device")
    print("3. Check: ✅ BlackHole 2ch + ✅ Your Headphones")
    print("4. Set as default output")
    print("="*60)
    
    # Check for required API keys
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY not found in .env file!")
        print("💡 Create a .env file in the parent directory with:")
        print('   OPENAI_API_KEY="sk-your-key-here"')
        print("   PORT=5000")
        return

    print("✅ OpenAI API key found")
    
    if os.getenv('ELEVENLABS_API_KEY') and os.getenv('ELEVENLABS_VOICE_ID'):
        print("✅ ElevenLabs configured - will use YOUR cloned voice")
        print(f"🎤 Voice ID: {os.getenv('ELEVENLABS_VOICE_ID')}")
    else:
        print("ℹ️ ElevenLabs not configured - using system voice")
    
    print("🚀 Starting avatar system...\n")
    
    delegator = ConversationDelegator()
    delegator.run()

if __name__ == "__main__":
    main()
