#!/usr/bin/env python3
"""
🎭 AI Avatar System - Final Version with Mode Selection and Enhanced Microphone Support
=======================================================================================

A real-time AI avatar that can temporarily take over conversations on your behalf.
This version features a mode selector for text-only or voice responses and prioritizes
external/headset microphones for optimal audio quality.

WORKFLOW:
---------
1. 👤 You begin a conversation naturally
2. 🎭 Activate the avatar to handle the discussion (Ctrl+Shift+D or web button)
3. 🤖 The AI responds (text only or text+voice based on selected mode)
4. 👤 Seamlessly take back control when ready (Ctrl+Shift+T)

MODES:
------
📝 Mode 1 (Text Only):
   - Avatar transcribes your speech
   - Sends to GPT API
   - Displays response as text only
   - No voice output

🎤 Mode 2 (Text + Voice):
   - Avatar transcribes your speech
   - Sends to GPT API
   - Displays response as text
   - Speaks response through your earphones (system TTS placeholder)
   - Ready for ElevenLabs voice cloning integration

MICROPHONE PRIORITY:
-------------------
The system automatically selects the best available microphone in this order:
1. 🎧 External USB microphones (Blue, Shure, Rode, Focusrite, etc.)
2. 🎧 Headset microphones
3. 🎧 Built-in MacBook microphone (fallback)

CORE CAPABILITIES:
-----------------
• 🎤 Real-time speech recognition via optimized microphone selection (OpenAI Whisper)
• 🧠 Intelligent conversation handling using GPT-4
• 🔊 System text-to-speech fallback (macOS 'say', Linux 'espeak', Windows SAPI)
• 🎯 Optional voice cloning through ElevenLabs API (if configured)
• 🌐 Web-based monitoring and control interface (Flask)
• ⌨️ Global hotkey support for delegation/takeover
• 🔄 Real-time transcription display showing what the avatar "heard"
• 🎮 Mode selector radio buttons for text-only or voice responses
• 📜 Conversation display with 10-minute history and 1000-line limit (newest at top)

TECHNICAL ARCHITECTURE:
----------------------
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Microphone  │────▶│    Whisper   │────▶│     GPT-4    │
│   (Priority  │     │     (STT)    │     │  (Reasoning) │
│    External) │     └──────────────┘     └───────┬──────┘
└──────────────┘                                   ▼
              ┌─────────────────────────────┐
              │     Conversation Display    │
              │  ┌───────────────────────┐  │
              │  │ Newest at TOP         │  │
              │  │ 👤 You (blue)         │  │
              │  │ 🎭 Avatar (purple)    │  │
              │  │ 10-min history        │  │
              │  │ 1000-line limit       │  │
              │  └───────────────────────┘  │
              └─────────────────────────────┘
                           │
                           ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Speaker    │◀────│  System TTS  │◀────│   Response   │
│   Output     │     │   (Fallback) │     │  Generation  │
└──────────────┘     └──────────────┘     └──────────────┘
                    (ElevenLabs if configured)
                           │
                           ▼
              ┌───────────────────────┐
              │   Mode Selector       │
              │  ┌─────────────────┐  │
              │  │ 📝 Mode 1: Text │  │
              │  │ 🎤 Mode 2: Voice│  │
              │  └─────────────────┘  │
              └───────────────────────┘

REQUIREMENTS:
------------
• Python 3.8+
• OpenAI API key (required for Whisper + GPT)
• Microphone access (System Settings → Privacy → Microphone)
• For hotkeys: Accessibility permissions (System Settings → Privacy → Accessibility)

QUICK START:
-----------
1. Create .env file with:
   OPENAI_API_KEY="sk-your-key-here"
   PORT=5000
   GPT_MODEL=gpt-4

2. Install dependencies:
   pip install -r requirements.txt

3. Run the launcher:
   ./set-up-and-run.sh

4. Open http://localhost:5000 in your browser
5. Select your preferred mode (Text Only or Text + Voice)
6. Click "Start Voice Conversation" or press Ctrl+Shift+D
7. Start speaking!

HOTKEYS:
--------
• Ctrl+Shift+D - Delegate conversation to avatar
• Ctrl+Shift+T - Take back control from avatar
• Ctrl+Shift+Q - Quit the entire system

TROUBLESHOOTING:
----------------
• No microphone detected: Check System Settings → Privacy → Microphone
• Hotkeys not working: Add Terminal to Accessibility permissions
• Slow responses: Check internet connection or try gpt-3.5-turbo
• No audio output: Check system volume and output device
• Transcription not showing: Check microphone levels and permissions
• Wrong microphone selected: Check System Settings → Sound → Input

FILE STRUCTURE:
--------------
• avatar.py           - Main application (this file) with mode selector
• set-up-and-run.sh   - Launcher script with cleanup
• requirements.txt    - Python dependencies
• .env               - API keys configuration
• voice-clone.py     - Optional ElevenLabs voice cloning setup
• logs/              - Application logs directory

MODE DETAILS:
------------
Mode 1 (Text Only):
   - Perfect for quiet environments
   - No voice output, just text responses
   - Saves API costs (no TTS)

Mode 2 (Text + Voice):
   - Full conversational experience
   - Avatar speaks responses through your earphones
   - Uses system TTS as placeholder (macOS 'say' command)
   - Ready for ElevenLabs voice cloning integration

CONVERSATION DISPLAY FEATURES:
-----------------------------
• ⏱️ 10-minute cutoff - Only shows recent conversation
• 📊 1000-line limit - Maintains performance
• 📅 Date separators - Shows when conversation spans multiple days
• 🎯 Message alignment - User right, avatar left
• 🔝 Newest messages at top - Easy to see latest exchange first
• 📍 Conversation appears right below Quick Tips

AUTHOR: Artem Ponomarev
VERSION: 5.0.0 (Final - Newest at Top)
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

# Load environment variables
load_dotenv()

class ConversationState(Enum):
    HUMAN_LEAD = "human_lead"
    AVATAR_ACTIVE = "avatar_active"
    TRANSITIONING = "transitioning"

class ConversationDelegator:
    def __init__(self):
        self.state = ConversationState.HUMAN_LEAD
        self.is_running = True
        self.avatar_active = False
        
        # Mode selection (default: text-only)
        self.mode = 'text'  # 'text' or 'voice'
        
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
        """Setup Flask web interface with mode switching"""
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
            """API endpoint to switch between text and voice modes"""
            data = request.get_json()
            if data and 'mode' in data:
                self.mode = data['mode']
                self.log(f"🔄 Mode changed to: {self.mode}")
                return jsonify({"success": True, "mode": self.mode})
            return jsonify({"success": False}), 400
    
    def get_system_state(self):
        """Get current system state including mode"""
        return {
            "state": self.state.value,
            "transcriptions": self.transcriptions[-10:],
            "responses": self.responses[-10:],
            "conversation_length": len(self.conversation_history),
            "hotkeys_enabled": self.hotkeys_enabled,
            "mode": self.mode,
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
            
            # Announce delegation only in voice mode
            if self.mode == 'voice':
                self.system_tts("I'll take it from here")
            
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
            
            # Announce takeover only in voice mode
            if self.mode == 'voice':
                self.system_tts("I'll take over now")
            
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
        """Generate AI response using GPT"""
        if not self.config["openai_api_key"]:
            return "AI system unavailable"
        
        try:
            # Build system prompt
            system_prompt = """
            You are an AI avatar having a voice conversation with a user.
            
            CONVERSATION RULES:
            - Keep responses natural and conversational
            - Be helpful, friendly, and engaging
            - Responses should be concise (1-3 sentences) for smooth voice delivery
            - Ask follow-up questions to keep the conversation flowing
            - If you don't understand something, ask for clarification
            
            Remember: This is a voice conversation, so keep responses natural and easy to speak.
            """
            
            messages = [
                {"role": "system", "content": system_prompt},
                *self.conversation_history[-6:],  # Last 3 exchanges
                {"role": "user", "content": user_input}
            ]
            
            response = self.openai_client.chat.completions.create(
                model=self.config["gpt_model"],
                messages=messages,
                max_tokens=150,
                temperature=0.7
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
            return "I apologize, but I'm having trouble responding right now."
    
    def text_to_speech(self, text):
        """Convert text to speech using ElevenLabs (if configured)"""
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
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.4,
                    "similarity_boost": 0.8
                }
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.content
            else:
                self.log(f"❌ ElevenLabs API error: {response.status_code}")
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
                subprocess.run(['say', text], check=True)
            elif system == "Linux":
                subprocess.run(['espeak', text], check=True)
            elif system == "Windows":
                ps_script = f'''
                Add-Type -AssemblyName System.Speech
                $speech = New-Object System.Speech.Synthesis.SpeechSynthesizer
                $speech.Speak("{text.replace('"', '""')}")
                '''
                subprocess.run(['powershell', '-Command', ps_script], check=True)
            return True
        except Exception as e:
            self.log(f"❌ System TTS error: {e}")
            return False
    
    def speak_message(self, text, use_cloned_voice=True):
        """Speak a message aloud only if in voice mode"""
        if not text.strip() or self.mode != 'voice':
            # In text mode, just log that we're not speaking
            if self.mode == 'text':
                self.log(f"📝 (text mode) Response: {text}")
            return True
        
        # Try ElevenLabs if configured
        if use_cloned_voice and self.config["elevenlabs_api_key"] and self.config["elevenlabs_voice_id"]:
            audio_data = self.text_to_speech(text)
            if audio_data:
                return self.play_audio_data(audio_data)
        
        # Fallback to system TTS
        return self.system_tts(text)
    
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
                                    
                                    # Speak response (respects mode setting)
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
        """Web interface with conversation displayed below tips (newest at top)"""
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
    <title>🎭 AI Avatar System</title>
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
        
        /* Mode selector */
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
        
        /* Conversation display - simple stacking, no scroll window */
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
        .mode-voice {
            background: #9f7aea;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎭 AI Avatar</h1>
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
        
        <!-- Mode Selector -->
        <div class="mode-selector">
            <label class="mode-option {% if mode == 'text' %}active{% else %}inactive{% endif %}">
                <input type="radio" name="mode" value="text" {% if mode == 'text' %}checked{% endif %} onchange="changeMode('text')">
                📝 Mode 1: Text Only
                <span class="mode-badge">No voice</span>
            </label>
            <label class="mode-option {% if mode == 'voice' %}active{% else %}inactive{% endif %}">
                <input type="radio" name="mode" value="voice" {% if mode == 'voice' %}checked{% endif %} onchange="changeMode('voice')">
                🎤 Mode 2: Text + Voice
                <span class="mode-badge">Speaks back</span>
            </label>
        </div>
        
        <div style="text-align: center;">
            <div class="status-badge" style="background-color: {{ status_color }};">
                {{ status_text }}
                <span class="mode-indicator {% if mode == 'text' %}mode-text-only{% else %}mode-voice{% endif %}">
                    {% if mode == 'text' %}📝 Text Only{% else %}🎤 Voice Mode{% endif %}
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
                <li><strong>Mode 2 (Text + Voice):</strong> Avatar types AND speaks responses (placeholder voice)</li>
                <li>Speak naturally - the avatar will respond after you pause</li>
                <li>Each conversation turn takes 2-3 seconds</li>
                <li>Click "Stop Conversation" anytime to end</li>
                <li>Showing last 10 minutes of conversation (newest at top)</li>
            </ul>
        </div>
        
        <!-- Conversation - appended right below tips, newest at top -->
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
        mode=self.mode,
        hotkey_delegate=self.config["hotkey_delegate"].upper(),
        hotkey_takeover=self.config["hotkey_takeover"].upper(),
        hotkey_quit=self.config["hotkey_quit"].upper(),
        hotkeys_enabled=self.hotkeys_enabled
        )
    
    def run(self):
        """Main system loop"""
        self.log("\n" + "="*60)
        self.log("🎭 AI AVATAR SYSTEM")
        self.log("="*60)
        self.log("📋 Workflow: Select Mode → Click Start → Speak → Avatar responds")
        self.log(f"🎮 Current Mode: {self.mode.upper()}")
        
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
    print("🎭 AI AVATAR SYSTEM")
    print("="*60)
    print("Version: 5.0.0 (Final - Newest at Top)")
    print("="*60)
    
    # Check for required API keys
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY not found in .env file!")
        print("💡 Create a .env file with:")
        print('   OPENAI_API_KEY="sk-your-key-here"')
        print("   PORT=5000")
        print("   GPT_MODEL=gpt-4")
        return
    
    print("✅ OpenAI API key found")
    print("🚀 Starting avatar system...\n")
    
    # Create and run the system
    delegator = ConversationDelegator()
    delegator.run()

if __name__ == "__main__":
    main()
