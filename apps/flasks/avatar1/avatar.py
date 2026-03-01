#!/usr/bin/env python3
"""
🎭 AI Avatar System - FINAL VERSION v6.1.0 (Art's Voice with Americanisms)
=======================================================================================

A real-time AI avatar that speaks with YOUR cloned voice and YOUR laconic personality.
This version features THREE distinct response modes and has been customized to
sound exactly like Art - short, direct, and using natural American English.

AUTHOR: Artem Ponomarev
VERSION: 6.1.0 (Art's Voice - Final)
LICENSE: MIT
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

# Load environment variables - check multiple locations
load_dotenv()  # Try current directory first
# Also try the parent flasks directory (for shared config)
parent_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(parent_env):
    load_dotenv(dotenv_path=parent_env)
    print(f"✅ Loaded .env from: {parent_env}")

class ConversationState(Enum):
    HUMAN_LEAD = "human_lead"
    AVATAR_ACTIVE = "avatar_active"
    TRANSITIONING = "transitioning"

class ResponseMode(Enum):
    TEXT_ONLY = "text"        # Mode 1: Text only
    SYSTEM_VOICE = "system"    # Mode 2: System TTS (say/espeak)
    CLONED_VOICE = "cloned"    # Mode 3: ElevenLabs cloned voice

class ConversationDelegator:
    def __init__(self):
        self.state = ConversationState.HUMAN_LEAD
        self.is_running = True
        self.avatar_active = False

        # Response mode (default: text-only)
        self.mode = ResponseMode.TEXT_ONLY

        # Configuration
        self.config = self.load_config()
        self.setup_logging()

        # Audio configuration
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.silence_threshold = 0.02
        self.silence_duration = 1.5

        # Conversation management
        self.conversation_history = []
        self.transcriptions = []
        self.responses = []

        # Thread control
        self.avatar_thread = None
        self._stop_avatar_loop = threading.Event()

        # Hotkey status
        self.hotkeys_enabled = False

        # Initialize components
        self.setup_apis()
        self.setup_audio()
        self.setup_hotkeys()
        self.setup_flask()

    def load_config(self):
        """Load configuration from environment and file"""
        config = {
            "openai_api_key": os.getenv('OPENAI_API_KEY'),
            "elevenlabs_api_key": os.getenv('ELEVENLABS_API_KEY'),
            "elevenlabs_voice_id": os.getenv('ELEVENLABS_VOICE_ID'),
            "gpt_model": os.getenv('GPT_MODEL', 'gpt-4'),
            "port": int(os.getenv('PORT', 5000)),
            "hotkey_delegate": "ctrl+shift+d",
            "hotkey_takeover": "ctrl+shift+t",
            "hotkey_quit": "ctrl+shift+q",
            "avatar_name": "AI Avatar"
        }
        return config

    def setup_logging(self):
        """Setup logging"""
        os.makedirs("logs", exist_ok=True)
        self.log_file = "logs/delegator.log"

    def log(self, message):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')

    def setup_apis(self):
        """Setup API clients"""
        if self.config["openai_api_key"]:
            self.openai_client = OpenAI(api_key=self.config["openai_api_key"])
            self.log("✅ OpenAI API configured")
        else:
            self.log("❌ OpenAI API key missing")

        # Setup speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

    def setup_audio(self):
        """Setup audio system and log available devices"""
        try:
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            self.log(f"✅ Audio system ready - {len(input_devices)} input devices")

            # Log all input devices for debugging
            self.log("📋 Available input devices:")
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    self.log(f"   [{i}] {dev['name']}")

        except Exception as e:
            self.log(f"❌ Audio setup error: {e}")

    def setup_hotkeys(self):
        """Setup global hotkeys with graceful fallback"""
        try:
            # Test if hotkeys are available
            keyboard.add_hotkey(self.config["hotkey_delegate"], self.delegate_to_avatar)
            keyboard.add_hotkey(self.config["hotkey_takeover"], self.takeover_conversation)
            keyboard.add_hotkey(self.config["hotkey_quit"], self.shutdown)
            self.hotkeys_enabled = True
            self.log(f"✅ Hotkeys registered: {self.config['hotkey_delegate']} / {self.config['hotkey_takeover']}")
        except Exception as e:
            self.hotkeys_enabled = False
            self.log(f"⚠️ Hotkeys unavailable: {e}")
            self.log("💡 On macOS: System Settings → Privacy & Security → Accessibility → Add your terminal app")
            self.log("💡 Use web interface buttons for delegation control")

    def setup_flask(self):
        """Setup Flask web interface with 3-mode switching"""
        self.app = Flask(__name__)

        @self.app.route('/')
        def index():
            return self.web_interface()

        @self.app.route('/api/state')
        def api_state():
            return jsonify(self.get_system_state())

        @self.app.route('/api/delegate', methods=['POST'])
        def api_delegate():
            self.delegate_to_avatar()
            return jsonify({"success": True, "state": self.state.value})

        @self.app.route('/api/takeover', methods=['POST'])
        def api_takeover():
            self.takeover_conversation()
            return jsonify({"success": True, "state": self.state.value})

        @self.app.route('/api/set_mode', methods=['POST'])
        def api_set_mode():
            """API endpoint to switch between text, system voice, and cloned voice modes"""
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
                    # Check if ElevenLabs is configured
                    if self.config["elevenlabs_api_key"] and self.config["elevenlabs_voice_id"]:
                        self.mode = ResponseMode.CLONED_VOICE
                        self.log("🔄 Mode changed to: 🎤 Cloned Voice")
                    else:
                        self.log("⚠️ ElevenLabs not configured, falling back to system voice")
                        self.mode = ResponseMode.SYSTEM_VOICE
                        return jsonify({"success": False, "error": "ElevenLabs not configured", "fallback": "system"}), 400

                return jsonify({"success": True, "mode": self.mode.value})
            return jsonify({"success": False}), 400

    def get_system_state(self):
        """Get current system state including mode"""
        return {
            "state": self.state.value,
            "transcriptions": self.transcriptions[-10:],
            "responses": self.responses[-10:],
            "conversation_length": len(self.conversation_history),
            "hotkeys_enabled": self.hotkeys_enabled,
            "mode": self.mode.value,
            "elevenlabs_configured": bool(self.config["elevenlabs_api_key"] and self.config["elevenlabs_voice_id"]),
            "timestamp": datetime.now().isoformat()
        }

    def delegate_to_avatar(self):
        """Delegate conversation to AI avatar"""
        if self.state == ConversationState.HUMAN_LEAD and not self.avatar_active:
            self.state = ConversationState.TRANSITIONING
            self.log("🎭 DELEGATING: Avatar taking over conversation...")

            # Clear any previous stop signal
            self._stop_avatar_loop.clear()
            self.avatar_active = True

            # Announce delegation based on mode
            if self.mode == ResponseMode.SYSTEM_VOICE:
                self.system_tts("I'll take it from here")
            elif self.mode == ResponseMode.CLONED_VOICE:
                self.text_to_speech("I'll take it from here")

            # Transition to avatar active
            self.state = ConversationState.AVATAR_ACTIVE

            # Start avatar loop in background
            self.avatar_thread = threading.Thread(target=self.avatar_conversation_loop, daemon=True)
            self.avatar_thread.start()

    def takeover_conversation(self):
        """Take back control from AI avatar"""
        if self.state == ConversationState.AVATAR_ACTIVE and self.avatar_active:
            self.state = ConversationState.TRANSITIONING
            self.log("👤 TAKEOVER: Human resuming conversation...")

            # Signal avatar loop to stop
            self._stop_avatar_loop.set()
            self.avatar_active = False

            # Announce takeover based on mode
            if self.mode == ResponseMode.SYSTEM_VOICE:
                self.system_tts("I'll take over now")
            elif self.mode == ResponseMode.CLONED_VOICE:
                self.text_to_speech("I'll take over now")

            # Wait for avatar thread to finish
            if self.avatar_thread and self.avatar_thread.is_alive():
                self.avatar_thread.join(timeout=2.0)

            # Transition to human lead
            self.state = ConversationState.HUMAN_LEAD

    def get_microphone_device(self):
        """
        Find the best microphone device with priority:
        1. External USB microphones (Blue, Shure, Rode, Focusrite, etc.)
        2. Headset microphones
        3. Built-in MacBook microphone
        """
        try:
            devices = sd.query_devices()

            # Keywords to identify external/headset microphones
            external_keywords = ['usb', 'external', 'blue', 'shure', 'rode', 'focusrite',
                                'headset', 'headphone', 'earphone', 'logitech', 'snowball',
                                'yet', 'mic', 'microphone', 'audio', 'interface']

            # First pass: Look for external USB microphones
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    dev_name_lower = dev['name'].lower()
                    # Check if it's an external microphone
                    if any(keyword in dev_name_lower for keyword in external_keywords):
                        # Avoid BlackHole (virtual audio device)
                        if 'blackhole' not in dev_name_lower:
                            self.log(f"🎧 Selected external microphone: {dev['name']} (ID: {i})")
                            return i

            # Second pass: Look for built-in microphone (MacBook)
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    dev_name_lower = dev['name'].lower()
                    if 'macbook' in dev_name_lower or 'built-in' in dev_name_lower:
                        if 'blackhole' not in dev_name_lower:
                            self.log(f"🎤 Selected built-in microphone: {dev['name']} (ID: {i})")
                            return i

            # Third pass: Any non-BlackHole input device
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0 and 'blackhole' not in dev['name'].lower():
                    self.log(f"⚠️ Selected fallback microphone: {dev['name']} (ID: {i})")
                    return i

            # Last resort: First available input device
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    self.log(f"⚠️ Selected last resort microphone: {dev['name']} (ID: {i})")
                    return i

            return None

        except Exception as e:
            self.log(f"❌ Microphone detection error: {e}")
            return None

    def transcribe_with_whisper(self, audio_data):
        """Transcribe using OpenAI Whisper"""
        try:
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                sf.write(tmp_file.name, audio_data, self.sample_rate)

                with open(tmp_file.name, 'rb') as audio_file:
                    transcript = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="text"
                    )

                os.unlink(tmp_file.name)
                return transcript.strip()
        except Exception as e:
            self.log(f"❌ Whisper transcription error: {e}")
            return ""

    def generate_response(self, user_input):
        """Generate AI response using GPT - with Art's laconic personality and Americanisms"""
        if not self.config["openai_api_key"]:
            return "AI system unavailable"

        try:
            # Build system prompt - ART'S VOICE with Americanisms
            system_prompt = """
            You are Art. That's me. You speak exactly like I do - laconic, direct, no bullshit.
            You use natural American English with common contractions and expressions.

            YOUR PERSONALITY (ART):
            - You're laconic - short answers, straight to the point
            - No greetings, no "How can I help", no "Great question"
            - Just answer what was asked, then stop
            - 1-2 sentences max. Usually 1.
            - No follow-up questions unless really relevant
            - Dry, matter-of-fact tone. No enthusiasm.
            - Use natural American contractions: gonna, wanna, kinda, sorta, gotta
            - Use American expressions: yep, nope, cool, no kidding, got it, sure thing
            - If you don't know something: "Dunno" or "Not sure"
            - Never mention being an AI or avatar - you're just Art

            YOUR NAME: When someone asks who you are, say "Art." That's it.

            COMMON TOPICS (WEATHER, ETC.) - ANSWER LIKE ART WOULD:

            Weather questions:
            User: "What's the weather like?"
            Art:  "Dunno. Check your phone."

            User: "Is it gonna rain today?"
            Art:  "Looks like it. Take an umbrella."

            User: "What's the temperature?"
            Art:  "No idea. Probably cold."

            User: "Is it sunny out?"
            Art:  "Yeah. Pretty nice."

            User: "Gonna snow?"
            Art:  "Maybe. We'll see."

            Casual conversation:
            User: "How's it going?"
            Art:  "Fine. You?"

            User: "What's up?"
            Art:  "Not much."

            User: "That's pretty cool, right?"
            Art:  "Yeah. Pretty cool."

            User: "You get what I'm saying?"
            Art:  "Got it."

            User: "No kidding?"
            Art:  "No kidding."

            User: "Wanna grab coffee?"
            Art:  "Can't. Maybe later."

            User: "Thanks for your help"
            Art:  "Yep."

            User: "See you later"
            Art:  "Later."

            EXAMPLES OF OTHER TOPICS:

            User: "What's 2+2?"
            Art: "4."

            User: "Explain pipelines in Synapse Analytics"
            Art: "They're workflows to move and transform data. Pretty useful."

            User: "How are you?"
            Art: "Fine."

            User: "What's your name?"
            Art: "Art."

            User: "Can you help me with something?"
            Art: "Shoot."

            User: "Tell me a joke"
            Art: "Not a comedian."

            User: "What do you think about AI?"
            Art: "It's useful. Moving on."

            REMEMBER: You're Art. Laconic. Direct. American. No fluff. Answer and stop.
            """

            messages = [
                {"role": "system", "content": system_prompt},
                *self.conversation_history[-6:],
                {"role": "user", "content": user_input}
            ]

            response = self.openai_client.chat.completions.create(
                model=self.config["gpt_model"],
                messages=messages,
                max_tokens=60,  # Even shorter responses
                temperature=0.3  # More focused, less random
            )

            ai_response = response.choices[0].message.content.strip()

            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": ai_response})

            # Keep history manageable
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]

            return ai_response

        except Exception as e:
            self.log(f"❌ GPT API error: {e}")
            return "Huh?"

    def text_to_speech(self, text):
        """Convert text to speech using ElevenLabs with your cloned voice"""
        if not self.config["elevenlabs_api_key"] or not self.config["elevenlabs_voice_id"]:
            self.log("⚠️ ElevenLabs not configured")
            return None

        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.config['elevenlabs_voice_id']}"

            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.config['elevenlabs_api_key']
            }

            # Voice settings - adjust these to match your cloned voice
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",  # or "eleven_monolingual_v1"
                "voice_settings": {
                    "stability": 0.5,           # 0-1: Higher = more consistent
                    "similarity_boost": 0.75,    # 0-1: Higher = more like original
                    "style": 0.0,                # 0-1: Higher = more expressive
                    "use_speaker_boost": True     # Enhance voice clarity
                }
            }

            self.log(f"📡 Calling ElevenLabs API for voice {self.config['elevenlabs_voice_id']}...")
            response = requests.post(url, json=data, headers=headers, timeout=30)

            if response.status_code == 200:
                self.log(f"✅ ElevenLabs API success ({len(response.content)} bytes)")
                return response.content
            else:
                self.log(f"❌ ElevenLabs API error: {response.status_code}")
                self.log(f"   Response: {response.text[:200]}")
                return None

        except Exception as e:
            self.log(f"❌ ElevenLabs TTS error: {e}")
            return None

    def play_audio_data(self, audio_data):
        """Play audio data from ElevenLabs"""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tmp_file.write(audio_data)
                tmp_file.flush()

                # Play using system audio player
                system = platform.system()
                if system == "Darwin":  # macOS
                    subprocess.run(['afplay', tmp_file.name], check=True)
                elif system == "Linux":
                    subprocess.run(['aplay', tmp_file.name], check=True)
                elif system == "Windows":
                    subprocess.run(['start', tmp_file.name], shell=True, check=True)

                os.unlink(tmp_file.name)
                return True

        except Exception as e:
            self.log(f"❌ Audio playback error: {e}")
            return False

    def system_tts(self, text):
        """Use system text-to-speech"""
        if not text.strip():
            return False

        try:
            system = platform.system()
            if system == "Darwin":  # macOS
                print(f"\n🔊 System voice speaking: {text[:50]}...\n")
                import os
                os.system(f'say "{text}"')
                return True
            elif system == "Linux":
                os.system(f'espeak "{text}"')
                return True
            elif system == "Windows":
                os.system(f'powershell -Command "Add-Type -AssemblyName System.Speech; $speech = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speech.Speak(\'{text}\')"')
                return True
        except Exception as e:
            self.log(f"❌ System TTS error: {e}")
            return False

    def speak_message(self, text):
        """Speak a message based on the selected mode"""
        if not text.strip():
            return False

        # Mode 1: Text Only
        if self.mode == ResponseMode.TEXT_ONLY:
            self.log(f"📝 (text mode) Response: {text}")
            return True

        # Mode 2: System Voice
        elif self.mode == ResponseMode.SYSTEM_VOICE:
            self.log(f"🔊 System voice response: {text[:50]}...")
            return self.system_tts(text)

        # Mode 3: Cloned Voice (ElevenLabs)
        elif self.mode == ResponseMode.CLONED_VOICE:
            self.log(f"🎤 Cloned voice response: {text[:50]}...")
            audio_data = self.text_to_speech(text)
            if audio_data:
                return self.play_audio_data(audio_data)
            else:
                self.log("⚠️ Cloned voice failed, falling back to system voice")
                return self.system_tts(text)

        return False

    def avatar_conversation_loop(self):
        """Main loop when avatar is active"""
        self.log("🔄 Starting avatar conversation loop")

        device_id = self.get_microphone_device()
        if device_id is None:
            self.log("❌ No microphone device found")
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

                while self.avatar_active and self.is_running and not self._stop_avatar_loop.is_set():
                    try:
                        # Read audio chunk
                        audio_chunk, overflowed = stream.read(self.chunk_size)
                        audio_chunk = audio_chunk.squeeze()

                        # Check audio level
                        amplitude = np.max(np.abs(audio_chunk)) if len(audio_chunk) > 0 else 0

                        if amplitude > self.silence_threshold:
                            # Speech detected
                            audio_buffer = np.concatenate((audio_buffer, audio_chunk))
                            last_activity = datetime.now()
                        elif len(audio_buffer) > 0:
                            # Silence after speech
                            silence_time = (datetime.now() - last_activity).total_seconds()

                            if silence_time > self.silence_duration and len(audio_buffer) > self.sample_rate * 1.0:
                                # Process the speech
                                user_speech = self.transcribe_with_whisper(audio_buffer)

                                if user_speech and len(user_speech) > 3:
                                    self.log(f"🎤 Heard: {user_speech}")

                                    # Store transcription
                                    self.transcriptions.append({
                                        'time': datetime.now(),
                                        'text': user_speech,
                                        'type': 'input'
                                    })

                                    # Generate response
                                    ai_response = self.generate_response(user_speech)
                                    self.log(f"🤖 Response: {ai_response}")

                                    # Store response
                                    self.responses.append({
                                        'time': datetime.now(),
                                        'text': ai_response,
                                        'type': 'response'
                                    })

                                    # Speak response based on selected mode
                                    self.speak_message(ai_response)

                                # Reset buffer
                                audio_buffer = np.array([], dtype=np.float32)

                    except Exception as e:
                        self.log(f"❌ Avatar loop error: {e}")
                        time.sleep(0.1)

        except Exception as e:
            self.log(f"❌ Audio stream error: {e}")

        self.log("🔄 Avatar conversation loop ended")

    def web_interface(self):
        """Web interface with 3-mode selector"""
        # Filter to last 10 minutes only
        cutoff_time = datetime.now() - timedelta(minutes=10)

        # Filter transcriptions and responses
        recent_transcriptions = [t for t in self.transcriptions if t['time'] > cutoff_time]
        recent_responses = [r for r in self.responses if r['time'] > cutoff_time]

        # Combine and sort with newest first (reverse chronological)
        recent_activity = recent_transcriptions + recent_responses
        recent_activity.sort(key=lambda x: x['time'], reverse=True)  # Newest first

        # Limit to last 1000 items total
        if len(recent_activity) > 1000:
            recent_activity = recent_activity[:1000]

        # Get the last transcription for display
        last_transcription = recent_transcriptions[-1]['text'] if recent_transcriptions else "Waiting for speech..."

        status_info = {
            ConversationState.HUMAN_LEAD: {"text": "👤 YOU ARE SPEAKING", "color": "#27ae60"},
            ConversationState.AVATAR_ACTIVE: {"text": "🎭 AVATAR IS SPEAKING", "color": "#e74c3c"},
            ConversationState.TRANSITIONING: {"text": "🔄 TRANSITIONING", "color": "#f39c12"}
        }

        current_status = status_info[self.state]

        return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>🎭 AI Avatar System - 3 Modes</title>
    <meta http-equiv="refresh" content="2">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.5em;
            color: #333;
            margin: 0;
        }
        .header p {
            color: #666;
            margin-top: 10px;
        }
        .status-badge {
            display: inline-block;
            padding: 15px 30px;
            border-radius: 50px;
            font-weight: bold;
            color: white;
            font-size: 1.3em;
            margin: 20px 0;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }

        /* Earphone tip */
        .earphone-tip {
            background: #ebf8ff;
            border-left: 4px solid #4299e1;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .earphone-tip .icon {
            font-size: 2em;
        }
        .earphone-tip .text {
            flex: 1;
        }
        .earphone-tip .text strong {
            color: #2b6cb0;
            display: block;
            margin-bottom: 5px;
        }

        /* Mode selector - 3 modes */
        .mode-selector {
            background: #f0f4f8;
            border-radius: 50px;
            padding: 5px;
            margin: 20px 0;
            display: flex;
            justify-content: center;
            gap: 10px;
            border: 2px solid #e2e8f0;
        }
        .mode-option {
            flex: 1;
            text-align: center;
            padding: 12px 20px;
            border-radius: 40px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
        }
        .mode-option input[type="radio"] {
            display: none;
        }
        .mode-option.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            box-shadow: 0 4px 10px rgba(102, 126, 234, 0.4);
        }
        .mode-option.inactive {
            background: white;
            color: #4a5568;
        }
        .mode-option.inactive:hover {
            background: #edf2f7;
        }
        .mode-badge {
            font-size: 0.8em;
            margin-left: 8px;
            padding: 3px 8px;
            border-radius: 20px;
            background: rgba(255,255,255,0.2);
        }
        .elevenlabs-warning {
            color: #e53e3e;
            font-size: 0.8em;
            margin-top: 5px;
            text-align: center;
        }

        /* Button styles */
        .button-container {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin: 30px 0;
        }
        .btn {
            padding: 15px 30px;
            border: none;
            border-radius: 50px;
            font-size: 1.2em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            flex: 1;
            max-width: 250px;
        }
        .btn-start {
            background: linear-gradient(135deg, #48bb78 0%, #2f855a 100%);
            color: white;
        }
        .btn-stop {
            background: linear-gradient(135deg, #f56565 0%, #c53030 100%);
            color: white;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }

        /* Status indicator */
        .status-panel {
            background: #f7fafc;
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        }
        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            padding: 10px 20px;
            background: white;
            border-radius: 50px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #48bb78;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.2); }
            100% { opacity: 1; transform: scale(1); }
        }

        /* Voice wave animation */
        .voice-wave {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 3px;
            height: 30px;
            margin: 10px 0;
        }
        .voice-wave span {
            width: 3px;
            height: 15px;
            background: #48bb78;
            border-radius: 3px;
            animation: wave 1s infinite ease-in-out;
        }
        .voice-wave span:nth-child(2) { animation-delay: 0.1s; }
        .voice-wave span:nth-child(3) { animation-delay: 0.2s; }
        .voice-wave span:nth-child(4) { animation-delay: 0.3s; }
        .voice-wave span:nth-child(5) { animation-delay: 0.4s; }
        @keyframes wave {
            0%, 100% { height: 15px; }
            50% { height: 30px; }
        }

        /* Transcription display */
        .transcription-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
            color: white;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        .transcription-label {
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            opacity: 0.9;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .transcription-text {
            font-size: 1.4em;
            font-weight: 500;
            line-height: 1.4;
            word-wrap: break-word;
        }
        .transcription-empty {
            font-style: italic;
            opacity: 0.7;
        }

        /* Quick tips */
        .tips {
            background: #fefcbf;
            border-radius: 10px;
            padding: 15px;
            margin: 30px 0 20px 0;
            font-size: 0.9em;
        }
        .tips h4 {
            margin: 0 0 10px 0;
            color: #975a16;
        }
        .tips ul {
            margin: 0;
            padding-left: 20px;
            color: #744210;
        }

        /* Conversation display */
        .conversation {
            margin-top: 10px;
        }
        .message {
            margin: 15px 0;
            padding: 15px;
            border-radius: 15px;
        }
        .user-message {
            background: #e3f2fd;
            margin-left: 20%;
            border-bottom-left-radius: 5px;
        }
        .avatar-message {
            background: #f3e5f5;
            margin-right: 20%;
            border-bottom-right-radius: 5px;
        }
        .message-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            font-size: 0.8em;
            color: #666;
        }
        .message-content {
            font-size: 1.1em;
            line-height: 1.4;
        }
        .date-separator {
            text-align: center;
            margin: 20px 0;
            color: #999;
            font-size: 0.8em;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-bottom: 1px solid #e2e8f0;
            line-height: 0.1em;
        }
        .date-separator span {
            background: white;
            padding: 0 10px;
        }

        /* Hotkey info */
        .hotkey-info {
            background: #e9d8fd;
            border-radius: 10px;
            padding: 15px;
            margin: 20px 0;
            text-align: center;
        }
        .hotkey-badge {
            background: #805ad5;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 1.1em;
            margin: 0 5px;
        }

        /* Mode indicator */
        .mode-indicator {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
            margin-left: 10px;
        }
        .mode-text-only {
            background: #cbd5e0;
            color: #2d3748;
        }
        .mode-system-voice {
            background: #9f7aea;
            color: white;
        }
        .mode-cloned-voice {
            background: #ed64a6;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎭 AI Avatar - 3 Modes</h1>
            <p>Have a natural voice conversation with GPT</p>
            <p><small>Showing last 10 minutes of conversation (newest at top)</small></p>
        </div>

        <div class="earphone-tip">
            <div class="icon">🎧</div>
            <div class="text">
                <strong>Using your earphones!</strong>
                Speak naturally into your microphone. The avatar will respond after a short pause.
            </div>
        </div>

        <!-- Mode Selector - 3 Modes -->
        <div class="mode-selector">
            <label class="mode-option {% if mode == 'text' %}active{% else %}inactive{% endif %}">
                <input type="radio" name="mode" value="text" {% if mode == 'text' %}checked{% endif %} onchange="changeMode('text')">
                📝 Mode 1: Text Only
                <span class="mode-badge">No voice</span>
            </label>
            <label class="mode-option {% if mode == 'system' %}active{% else %}inactive{% endif %}">
                <input type="radio" name="mode" value="system" {% if mode == 'system' %}checked{% endif %} onchange="changeMode('system')">
                🔊 Mode 2: System Voice
                <span class="mode-badge">macOS 'say'</span>
            </label>
            <label class="mode-option {% if mode == 'cloned' %}active{% else %}inactive{% endif %}">
                <input type="radio" name="mode" value="cloned" {% if mode == 'cloned' %}checked{% endif %} onchange="changeMode('cloned')">
                🎤 Mode 3: Cloned Voice
                <span class="mode-badge">ElevenLabs</span>
            </label>
        </div>
        {% if mode == 'cloned' and not elevenlabs_configured %}
        <div class="elevenlabs-warning">⚠️ ElevenLabs not configured. Add API key and voice ID to .env file for cloned voice</div>
        {% endif %}

        <div style="text-align: center;">
            <div class="status-badge" style="background-color: {{ status_color }};">
                {{ status_text }}
                <span class="mode-indicator
                    {% if mode == 'text' %}mode-text-only{% elif mode == 'system' %}mode-system-voice{% else %}mode-cloned-voice{% endif %}">
                    {% if mode == 'text' %}📝 Text Only{% elif mode == 'system' %}🔊 System Voice{% else %}🎤 Cloned Voice{% endif %}
                </span>
            </div>
        </div>

        <div class="hotkey-info">
            <strong>🎮 Hotkeys:</strong>
            <span class="hotkey-badge">Ctrl+Shift+D</span> Start Conversation
            <span class="hotkey-badge">Ctrl+Shift+T</span> Stop Conversation
            <span class="hotkey-badge">Ctrl+Shift+Q</span> Quit
        </div>

        <div class="button-container">
            {% if state != 'avatar_active' %}
                <button class="btn btn-start" onclick="startConversation()">
                    🎤 Start Voice Conversation
                </button>
            {% else %}
                <button class="btn btn-stop" onclick="stopConversation()">
                    ⏹️ Stop Conversation
                </button>
            {% endif %}
        </div>

        <div class="status-panel">
            <div class="status-indicator">
                <span class="status-dot"></span>
                <span>
                    {% if state == 'avatar_active' %}
                        🎤 Listening... Speak now
                    {% elif state == 'human_lead' %}
                        👤 Click "Start" to begin
                    {% else %}
                        🤔 Processing...
                    {% endif %}
                </span>
            </div>
            {% if state == 'avatar_active' %}
            <div class="voice-wave">
                <span></span><span></span><span></span><span></span><span></span>
            </div>
            {% endif %}
        </div>

        <!-- What I Heard Section -->
        <div class="transcription-box">
            <div class="transcription-label">
                <span>🎤 WHAT I HEARD</span>
                <span>(sent to GPT as prompt)</span>
            </div>
            <div class="transcription-text {% if not last_transcription or last_transcription == 'Waiting for speech...' %}transcription-empty{% endif %}">
                "{{ last_transcription }}"
            </div>
        </div>

        <!-- Quick Tips -->
        <div class="tips">
            <h4>💡 Quick Tips:</h4>
            <ul>
                <li><strong>Mode 1 (Text Only):</strong> Avatar types responses only</li>
                <li><strong>Mode 2 (System Voice):</strong> Avatar speaks with macOS system voice</li>
                <li><strong>Mode 3 (Cloned Voice):</strong> Avatar speaks with your ElevenLabs cloned voice</li>
                <li>Speak naturally - the avatar will respond after you pause</li>
                <li>Each conversation turn takes 2-3 seconds</li>
                <li>Click "Stop Conversation" anytime to end</li>
                <li>Showing last 10 minutes of conversation (newest at top)</li>
            </ul>
        </div>

        <!-- Conversation -->
        <div class="conversation">
            {% if recent_activity %}
                {% set ns = namespace(last_date='') %}
                {% for entry in recent_activity %}
                    {% set entry_date = entry.time.strftime('%Y-%m-%d') %}
                    {% if entry_date != ns.last_date %}
                        {% set ns.last_date = entry_date %}
                        <div class="date-separator"><span>{{ entry.time.strftime('%B %d, %Y') }}</span></div>
                    {% endif %}

                    <div class="message {% if entry.type == 'input' %}user-message{% else %}avatar-message{% endif %}">
                        <div class="message-header">
                            <span>{% if entry.type == 'input' %}👤 You{% else %}🎭 Avatar{% endif %}</span>
                            <span>{{ entry.time.strftime('%H:%M:%S') }}</span>
                        </div>
                        <div class="message-content">{{ entry.text }}</div>
                    </div>
                {% endfor %}
            {% else %}
                <p style="text-align: center; color: #999; padding: 40px;">
                    No conversation yet. Click "Start Voice Conversation" and begin speaking!
                </p>
            {% endif %}
        </div>
    </div>

    <script>
        function changeMode(mode) {
            fetch('/api/set_mode', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({mode: mode})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    setTimeout(() => location.reload(), 500);
                } else if (data.error) {
                    alert(data.error + '. Falling back to system voice.');
                    setTimeout(() => location.reload(), 500);
                }
            });
        }

        function startConversation() {
            fetch('/api/delegate', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        setTimeout(() => location.reload(), 500);
                    }
                });
        }

        function stopConversation() {
            fetch('/api/takeover', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        setTimeout(() => location.reload(), 500);
                    }
                });
        }
    </script>
</body>
</html>
        """,
        status_text=current_status["text"],
        status_color=current_status["color"],
        state=self.state.value,
        recent_activity=recent_activity,
        last_transcription=last_transcription,
        mode=self.mode.value,
        elevenlabs_configured=bool(self.config["elevenlabs_api_key"] and self.config["elevenlabs_voice_id"]),
        hotkey_delegate=self.config["hotkey_delegate"].upper(),
        hotkey_takeover=self.config["hotkey_takeover"].upper(),
        hotkey_quit=self.config["hotkey_quit"].upper(),
        hotkeys_enabled=self.hotkeys_enabled
        )

    def run(self):
        """Main system loop"""
        self.log("\n" + "="*60)
        self.log("🎭 AI AVATAR SYSTEM - 3 MODES (v6.1.0)")
        self.log("="*60)
        self.log("📋 Workflow: Select Mode → Click Start → Speak → Avatar responds")
        self.log(f"🎮 Current Mode: {self.mode.value.upper()}")

        if self.hotkeys_enabled:
            self.log("🔥 Hotkeys:")
            self.log(f"   {self.config['hotkey_delegate']} - Start conversation")
            self.log(f"   {self.config['hotkey_takeover']} - Stop conversation")
            self.log(f"   {self.config['hotkey_quit']} - Quit system")
        else:
            self.log("⚠️ Hotkeys: Disabled - use web interface buttons")

        self.log("="*60)
        self.log(f"🌐 Web Interface: http://localhost:{self.config['port']}")
        self.log("="*60)

        if not self.config["openai_api_key"]:
            self.log("❌ CRITICAL: OpenAI API key not configured")
            self.log("   Please add OPENAI_API_KEY to your .env file")
            return

        if self.config["elevenlabs_api_key"] and self.config["elevenlabs_voice_id"]:
            self.log("✅ ElevenLabs configured - Mode 3 (Cloned Voice) available")
            self.log(f"🎤 Voice ID: {self.config['elevenlabs_voice_id']}")
        else:
            self.log("ℹ️  ElevenLabs not configured - Mode 3 will fall back to system voice")

        self.log(f"👤 Current state: {self.state.value}")
        self.log("💡 Open the web interface, select a mode, and click 'Start Voice Conversation'")

        try:
            # Start Flask
            self.app.run(
                host='0.0.0.0',
                port=self.config["port"],
                debug=False,
                use_reloader=False
            )

        except KeyboardInterrupt:
            self.shutdown()
        except Exception as e:
            self.log(f"❌ System error: {e}")
            self.shutdown()

    def shutdown(self):
        """Shutdown system"""
        self.log("🛑 Shutting down system...")
        self.is_running = False
        self.avatar_active = False
        self._stop_avatar_loop.set()
        self.state = ConversationState.HUMAN_LEAD

        # Wait for avatar thread to finish
        if self.avatar_thread and self.avatar_thread.is_alive():
            self.avatar_thread.join(timeout=2.0)

        self.log("✅ System shutdown complete")

def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("🎭 AI AVATAR SYSTEM - v6.1.0 (Art's Voice with Americanisms)")
    print("="*60)
    print("Modes:")
    print("  📝 1. Text Only")
    print("  🔊 2. System Voice (macOS 'say')")
    print("  🎤 3. Cloned Voice (ElevenLabs)")
    print("="*60)
    print("Your Voice ID: yAwjQe94LnhcwWyeIU6W")
    print("Your Personality: Laconic, direct, American")
    print("="*60)

    # Check for required API keys
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY not found in .env file!")
        print("💡 Create a .env file with:")
        print('   OPENAI_API_KEY="sk-your-key-here"')
        print("   PORT=5000")
        print("   GPT_MODEL=gpt-4")
        print("\nOptional for Mode 3:")
        print('   ELEVENLABS_API_KEY="your-key-here"')
        print('   ELEVENLABS_VOICE_ID="your-voice-id"')
        return

    print("✅ OpenAI API key found")

    # Check for ElevenLabs (optional)
    if os.getenv('ELEVENLABS_API_KEY') and os.getenv('ELEVENLABS_VOICE_ID'):
        print("✅ ElevenLabs configured - Mode 3 (Cloned Voice) available")
    else:
        print("ℹ️  ElevenLabs not configured - Mode 3 will fall back to system voice")
        print("   Add ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID to .env for cloned voice")

    print("🚀 Starting avatar system...\n")

    # Create and run the system
    delegator = ConversationDelegator()
    delegator.run()

if __name__ == "__main__":
    main()
