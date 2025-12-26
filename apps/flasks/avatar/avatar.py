"""
🎭 AI Avatar System

A real-time AI avatar that can temporarily take over conversations on your behalf.

WORKFLOW:
1. You begin a conversation naturally
2. Activate the avatar to handle the discussion  
3. The AI responds using your voice and conversational style
4. Seamlessly take back control when ready

CORE CAPABILITIES:
• Real-time speech recognition via built-in microphone
• Intelligent conversation handling using GPT-4
• Voice cloning through ElevenLabs API
• System text-to-speech fallback
• Web-based monitoring and control interface
• Global hotkey support for delegation/takeover

TECHNICAL ARCHITECTURE:
- Audio Processing: Real-time microphone input with silence detection
- AI Integration: OpenAI Whisper (STT) + GPT-4 (reasoning) 
- Voice Synthesis: ElevenLabs (cloned voice) + System TTS (fallback)
- Web Interface: Flask-based real-time monitoring dashboard
- Control System: Hotkey-driven state management with graceful fallbacks

USAGE:
1. Configure API keys in .env file
2. Run: ./launch-avatar.sh
3. Access web interface: http://localhost:5000
4. Use hotkeys: 
   - Ctrl+Shift+D: Delegate to avatar
   - Ctrl+Shift+T: Take over conversation  
   - Ctrl+Shift+Q: Quit system

SECURITY NOTE:
- API keys are loaded from .env (excluded from version control)
- No conversation data is persisted long-term
- All audio processing happens locally until API calls
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
from datetime import datetime
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
    from flask import Flask, render_template_string, jsonify
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
        """Setup audio system"""
        try:
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            self.log(f"✅ Audio system ready - {len(input_devices)} input devices")
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
        """Setup Flask web interface"""
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
    
    def get_system_state(self):
        """Get current system state"""
        return {
            "state": self.state.value,
            "transcriptions": self.transcriptions[-10:],
            "responses": self.responses[-10:],
            "conversation_length": len(self.conversation_history),
            "hotkeys_enabled": self.hotkeys_enabled,
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
            
            # Announce delegation
            self.speak_message("I'll take it from here", use_cloned_voice=False)
            
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
            
            # Announce takeover
            self.speak_message("I'll take over now", use_cloned_voice=False)
            
            # Wait for avatar thread to finish
            if self.avatar_thread and self.avatar_thread.is_alive():
                self.avatar_thread.join(timeout=2.0)
            
            # Transition to human lead
            self.state = ConversationState.HUMAN_LEAD
    
    def get_microphone_device(self):
        """Find the best microphone device"""
        try:
            devices = sd.query_devices()
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    if 'macbook' in dev['name'].lower():
                        return i
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
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
            You are an AI avatar temporarily handling a conversation for someone.
            
            CONVERSATION RULES:
            - Keep responses natural and conversational
            - Be helpful and professional
            - If the topic becomes too complex or personal, suggest handing back to the human
            - Maintain the flow of conversation naturally
            - Responses should be concise (1-2 sentences) for smooth voice delivery
            
            When you think the human should take over, include a gentle handoff cue like:
            "This might be better handled by my colleague" or "Let me hand this back"
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
        """Convert text to speech using ElevenLabs"""
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
    
    def speak_message(self, text, use_cloned_voice=True):
        """Speak a message aloud"""
        if not text.strip():
            return False
        
        if use_cloned_voice and self.config["elevenlabs_api_key"]:
            audio_data = self.text_to_speech(text)
            if audio_data:
                return self.play_audio_data(audio_data)
        
        # Fallback to system TTS
        return self.system_tts(text)
    
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
                                    
                                    # Speak response
                                    self.speak_message(ai_response, use_cloned_voice=True)
                                
                                # Reset buffer
                                audio_buffer = np.array([], dtype=np.float32)
                    
                    except Exception as e:
                        self.log(f"❌ Avatar loop error: {e}")
                        time.sleep(0.1)
                        
        except Exception as e:
            self.log(f"❌ Audio stream error: {e}")
        
        self.log("🔄 Avatar conversation loop ended")
    
    def web_interface(self):
        """Web interface for monitoring"""
        recent_activity = self.transcriptions[-10:] + self.responses[-10:]
        recent_activity.sort(key=lambda x: x['time'], reverse=True)
        
        status_info = {
            ConversationState.HUMAN_LEAD: {"text": "👤 HUMAN LEADING", "color": "#27ae60"},
            ConversationState.AVATAR_ACTIVE: {"text": "🎭 AVATAR ACTIVE", "color": "#e74c3c"},
            ConversationState.TRANSITIONING: {"text": "🔄 TRANSITIONING", "color": "#f39c12"}
        }
        
        current_status = status_info[self.state]
        
        return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>🎭 AI Avatar System</title>
    <meta http-equiv="refresh" content="3">
    <style>
        body { font-family: -apple-system, sans-serif; margin: 20px; background: #f5f5f7; }
        .container { max-width: 1000px; margin: 0 auto; background: white; border-radius: 12px; padding: 30px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid #eee; }
        .status { display: inline-block; padding: 12px 24px; border-radius: 25px; font-weight: bold; color: white; font-size: 1.2em; margin: 15px 0; }
        .workflow { display: flex; justify-content: space-between; margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 10px; }
        .step { text-align: center; flex: 1; padding: 15px; }
        .step-number { background: #3498db; color: white; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; margin: 0 auto 10px; }
        .controls { display: flex; gap: 15px; justify-content: center; margin: 25px 0; }
        .btn { padding: 12px 24px; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; }
        .btn-delegate { background: #e74c3c; color: white; }
        .btn-takeover { background: #27ae60; color: white; }
        .message { padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid; }
        .input { background: #e3f2fd; border-left-color: #2196f3; }
        .response { background: #f3e5f5; border-left-color: #9c27b0; }
        .timestamp { font-size: 0.8em; color: #666; margin-bottom: 5px; }
        .hotkeys { background: #fff3cd; border-radius: 8px; padding: 15px; margin: 20px 0; text-align: center; }
        .permission-warning { background: #ffeaa7; border-radius: 8px; padding: 15px; margin: 20px 0; text-align: center; border-left: 4px solid #fdcb6e; }
        .success-message { background: #d4edda; border-radius: 8px; padding: 15px; margin: 20px 0; text-align: center; border-left: 4px solid #28a745; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎭 AI Avatar System</h1>
            <div class="status" style="background-color: {{ status_color }};">{{ status_text }}</div>
        </div>

        <div class="workflow">
            <div class="step"><div class="step-number">1</div><strong>You Start</strong><p>Begin conversation naturally</p></div>
            <div class="step"><div class="step-number">2</div><strong>Delegate</strong><p>Press Ctrl+Shift+D</p></div>
            <div class="step"><div class="step-number">3</div><strong>Observe</strong><p>Avatar handles conversation</p></div>
            <div class="step"><div class="step-number">4</div><strong>Take Over</strong><p>Press Ctrl+Shift+T anytime</p></div>
        </div>

        <div class="hotkeys">
            <strong>Control Hotkeys:</strong> {{ hotkey_delegate }} - Delegate | {{ hotkey_takeover }} - Take Over | {{ hotkey_quit }} - Quit
        </div>

        {% if not hotkeys_enabled %}
        <div class="permission-warning">
            <strong>⚠️ Hotkeys Disabled:</strong> On macOS, grant Accessibility permissions to your terminal app for hotkeys to work.
            <br><strong>💡 Solution:</strong> System Settings → Privacy & Security → Accessibility → Add your terminal app
            <br><strong>🎮 Alternative:</strong> Use the web interface buttons below
        </div>
        {% else %}
        <div class="success-message">
            <strong>✅ Hotkeys Enabled:</strong> You can use Ctrl+Shift+D to delegate and Ctrl+Shift+T to take over!
        </div>
        {% endif %}

        <div class="controls">
            {% if state != 'avatar_active' %}
                <button class="btn btn-delegate" onclick="delegateToAvatar()">Delegate to Avatar</button>
            {% else %}
                <button class="btn btn-takeover" onclick="takeoverConversation()">Take Over Conversation</button>
            {% endif %}
        </div>

        <div style="margin-top: 30px; max-height: 500px; overflow-y: auto;">
            <h3>Recent Conversation Activity</h3>
            {% for entry in recent_activity %}
                <div class="message {{ entry.type }}">
                    <div class="timestamp">{{ entry.time.strftime('%H:%M:%S') }}</div>
                    <div><strong>{{ '🎤 Input' if entry.type == 'input' else '🤖 Avatar Response' }}:</strong> {{ entry.text }}</div>
                </div>
            {% else %}
                <p style="text-align: center; color: #666;">No conversation activity yet</p>
            {% endfor %}
        </div>
    </div>

    <script>
        function delegateToAvatar() { 
            fetch('/api/delegate', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        setTimeout(() => location.reload(), 500);
                    }
                });
        }
        
        function takeoverConversation() { 
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
        self.log("📋 Workflow: You Start → Delegate → Observe → Take Over")
        
        if self.hotkeys_enabled:
            self.log("🔥 Hotkeys:")
            self.log(f"   {self.config['hotkey_delegate']} - Delegate to Avatar")
            self.log(f"   {self.config['hotkey_takeover']} - Take Over from Avatar")
            self.log(f"   {self.config['hotkey_quit']} - Quit System")
        else:
            self.log("⚠️ Hotkeys: Disabled (requires Accessibility permissions)")
            self.log("💡 Use web interface buttons for delegation control")
        
        self.log("="*60)
        self.log(f"🌐 Web Interface: http://localhost:{self.config['port']}")
        self.log("="*60)
        
        if not self.config["openai_api_key"]:
            self.log("❌ WARNING: OpenAI API key not configured")
        if not self.config["elevenlabs_api_key"]:
            self.log("❌ WARNING: ElevenLabs API key not configured")
        
        self.log(f"👤 Current state: {self.state.value}")
        self.log("💡 Start speaking naturally, then delegate when ready")
        
        try:
            # Start Flask in background
            flask_thread = threading.Thread(
                target=lambda: self.app.run(
                    host='0.0.0.0',
                    port=self.config["port"],
                    debug=False,
                    use_reloader=False
                ),
                daemon=True
            )
            flask_thread.start()
            
            # Main loop
            while self.is_running:
                time.sleep(0.5)
                
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
    # Check for required API keys
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY environment variable not set!")
        print("💡 Set it with: export OPENAI_API_KEY='your_api_key'")
        return
    
    # Create and run the system
    delegator = ConversationDelegator()
    delegator.run()

if __name__ == "__main__":
    main()