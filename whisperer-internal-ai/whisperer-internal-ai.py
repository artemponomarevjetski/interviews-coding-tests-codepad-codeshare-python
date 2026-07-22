#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║  🎤  WHISPERER‑INTERNAL  –  Async OpenAI Voice Assistant           ║
║                                                                      ║
║  • Uses faster‑whisper (no llvmlite build issues)                   ║
║  • Listens to your built‑in microphone                              ║
║  • Bundles transcribed text and sends to OpenAI asynchronously      ║
║  • Continues transcription while waiting for OpenAI                 ║
║  • Injects API responses into the webpage on the fly                ║
║  • Attaches context.md instructions to every user prompt            ║
║  • Dynamically switches between code‑only and conversational mode   ║
║                                                                      ║
║  Usage:                                                              ║
║    python whisperer-internal-ai.py                                  ║
║                                                                      ║
║  Then open http://localhost:5000 in your browser.                    ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import re
from datetime import datetime, timedelta
from collections import deque
import logging
from flask import Flask, render_template_string
import sounddevice as sd
import numpy as np
import threading
from dotenv import load_dotenv
from openai import OpenAI

# ----------------------------------------------------------------------
#  Load environment variables from home directory (~/.env)
# ----------------------------------------------------------------------
home_env = os.path.expanduser("~/.env")
if os.path.exists(home_env):
    load_dotenv(dotenv_path=home_env, override=True)
else:
    print("❌ ERROR: ~/.env not found.")
    print("   Please create ~/.env with your OPENAI_API_KEY.")
    sys.exit(1)

# Check that the API key is actually set
api_key = os.getenv("OPENAI_API_KEY")
if not api_key or api_key == "your-openai-api-key-here":
    print("❌ ERROR: OPENAI_API_KEY not set or invalid.")
    print("   Please add a valid key to ~/.env")
    sys.exit(1)

# ----------------------------------------------------------------------
#  OpenAI client
# ----------------------------------------------------------------------
client = OpenAI(api_key=api_key)

# ----------------------------------------------------------------------
#  faster‑whisper – no compilation headaches
# ----------------------------------------------------------------------
from faster_whisper import WhisperModel

# ----------------------------------------------------------------------
#  Configuration
# ----------------------------------------------------------------------
SAMPLING_RATE = 16000
CHUNK_SIZE = 4096
SILENCE_THRESHOLD = 0.025
MIN_AUDIO_LENGTH = 0.8
MODEL_SIZE = "small.en"
COMPUTE_TYPE = "int8"

# ----------------------------------------------------------------------
#  Load the model (CPU only)
# ----------------------------------------------------------------------
model = WhisperModel(MODEL_SIZE, device="cpu", compute_type=COMPUTE_TYPE)

# ----------------------------------------------------------------------
#  Load instructions from context.md (attached to every user prompt)
# ----------------------------------------------------------------------
INSTRUCTIONS_PATH = os.path.join(os.path.dirname(__file__), "context.md")
INSTRUCTIONS_CACHE = None

def get_instructions():
    global INSTRUCTIONS_CACHE
    if INSTRUCTIONS_CACHE is not None:
        return INSTRUCTIONS_CACHE

    if os.path.exists(INSTRUCTIONS_PATH):
        with open(INSTRUCTIONS_PATH, 'r', encoding='utf-8') as f:
            INSTRUCTIONS_CACHE = f.read().strip()
        logging.info(f"✅ Loaded instructions from {INSTRUCTIONS_PATH}")
    else:
        # Create a default file with basic rules
        default = (
            "# Assistant Instructions\n\n"
            "You are a helpful assistant. Answer clearly and concisely.\n"
            "For coding questions, provide raw code (no markdown). "
            "For general chat, speak naturally."
        )
        with open(INSTRUCTIONS_PATH, 'w', encoding='utf-8') as f:
            f.write(default)
        INSTRUCTIONS_CACHE = default
        logging.info(f"📄 Created default instructions at {INSTRUCTIONS_PATH}")

    return INSTRUCTIONS_CACHE

# ----------------------------------------------------------------------
#  Flask app setup
# ----------------------------------------------------------------------
app = Flask(__name__)

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/flask_app.log'),
        logging.StreamHandler()
    ],
    datefmt='%Y-%m-%d %H:%M:%S'
)

# ------------------------------------------------------------
#  ROLLING CONVERSATION BUNDLE (last 10 exchanges = 20 messages)
# ------------------------------------------------------------
history = deque(maxlen=20)          # stores {"role": "user"/"assistant", "content": ...}
history_lock = threading.Lock()

conversations = []                  # display list (for the web UI)
conversations_lock = threading.Lock()
MAX_CONVERSATIONS = 20

# ----------------------------------------------------------------------
#  Microphone selection
# ----------------------------------------------------------------------
def get_microphone():
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        if 'MacBook Pro Microphone' in dev['name'] and dev['max_input_channels'] > 0:
            return i
    for i, dev in enumerate(devices):
        if dev['max_input_channels'] > 0 and 'blackhole' not in dev['name'].lower():
            return i
    return None

# ----------------------------------------------------------------------
#  Async OpenAI caller – with dynamic mode and context.md attachment
# ----------------------------------------------------------------------
def get_ai_reply(history_snapshot, entry):
    try:
        # 1) Load the persistent instructions
        instructions = get_instructions()

        # 2) Modify the last user message by appending instructions
        modified_history = list(history_snapshot)
        if modified_history and modified_history[-1]["role"] == "user":
            original = modified_history[-1]["content"]
            modified_history[-1] = {
                "role": "user",
                "content": f"{original}\n\n---\n\n{instructions}"   # attached at the bottom
            }

        # 3) Detect if it's a coding query (for dynamic system prompt)
        user_query = modified_history[-1]["content"] if modified_history else ""
        is_coding_query = any(kw in user_query.lower() for kw in
                              ["code", "python", "function", "class", "algorithm",
                               "write", "implement", "solve", "bug", "error"])

        if is_coding_query:
            system_prompt = (
                "You are a senior engineer. Provide only the raw code solution. "
                "Do not use Markdown, no backticks, no code fences, no explanations, no comments. "
                "Output just the plain code – nothing else."
            )
        else:
            system_prompt = (
                "You are a helpful, friendly assistant. Answer conversationally, "
                "with clear explanations, and use Markdown formatting for readability "
                "when appropriate (but not for code unless specifically asked)."
            )

        messages = [
            {"role": "system", "content": system_prompt}
        ] + modified_history   # ← the user prompt now includes the .md rules

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1200,
            temperature=0.2,
        )
        reply = response.choices[0].message.content.strip()

        # If coding query, strip markdown fences just in case
        if is_coding_query:
            reply = re.sub(r'^```\w*\n?', '', reply)
            reply = re.sub(r'\n?```$', '', reply)

    except Exception as e:
        logging.error(f"OpenAI error: {e}")
        reply = f"[Error: {e}]"

    # Append assistant reply to rolling history
    with history_lock:
        history.append({"role": "assistant", "content": reply})

    # Update display entry
    with conversations_lock:
        entry['reply'] = reply
        entry['time'] = datetime.now()

    logging.info(f"AI reply: {reply}")
    print(f"\n>> AI: {reply}")

# ----------------------------------------------------------------------
#  Transcription loop (non‑blocking)
# ----------------------------------------------------------------------
def transcribe_audio():
    try:
        device_id = get_microphone()
        if device_id is None:
            raise RuntimeError("No microphone found! Check permissions.")

        logging.info(f"Using microphone: {sd.query_devices()[device_id]['name']}")

        with sd.InputStream(
            samplerate=SAMPLING_RATE,
            channels=1,
            dtype='float32',
            device=device_id,
            blocksize=CHUNK_SIZE,
            latency='high'
        ) as stream:
            logging.info("Audio stream active – speak naturally...")
            audio_buffer = np.array([], dtype=np.float32)
            last_active = datetime.now()

            while True:
                audio_chunk, overflowed = stream.read(CHUNK_SIZE)
                if overflowed:
                    logging.debug("Buffer overflow occurred")

                audio_chunk = audio_chunk.squeeze()
                amplitude = np.max(np.abs(audio_chunk))

                if amplitude > SILENCE_THRESHOLD:
                    audio_buffer = np.concatenate((audio_buffer, audio_chunk))
                    last_active = datetime.now()
                elif len(audio_buffer) > 0:
                    silence_duration = (datetime.now() - last_active).total_seconds()
                    if silence_duration > 0.5 and len(audio_buffer) > SAMPLING_RATE * MIN_AUDIO_LENGTH:
                        try:
                            # Normalise volume to avoid clipping or low volume
                            max_amp = np.max(np.abs(audio_buffer))
                            if max_amp > 0:
                                audio_buffer = audio_buffer / max_amp

                            segments, _ = model.transcribe(
                                audio_buffer,
                                language="en",
                                vad_filter=True,
                                beam_size=5,
                                temperature=0.0,
                                condition_on_previous_text=False
                            )
                            user_text = " ".join(seg.text for seg in segments).strip().lower()

                            if user_text:
                                # Append user message to rolling history
                                with history_lock:
                                    history.append({"role": "user", "content": user_text})

                                # Create display entry
                                entry = {
                                    'time': datetime.now(),
                                    'user': user_text,
                                    'reply': None
                                }
                                with conversations_lock:
                                    conversations.append(entry)
                                    if len(conversations) > MAX_CONVERSATIONS:
                                        conversations.pop(0)

                                print(f"\n>> USER: {user_text}")
                                logging.info(f"USER: {user_text}")

                                # Snapshot history and spawn API call
                                history_snapshot = list(history)
                                threading.Thread(
                                    target=get_ai_reply,
                                    args=(history_snapshot, entry),
                                    daemon=True
                                ).start()

                        except Exception as e:
                            logging.error(f"Transcription error: {str(e)}")
                        finally:
                            audio_buffer = np.array([], dtype=np.float32)

    except Exception as e:
        logging.error(f"Fatal audio error: {str(e)}", exc_info=True)
        raise

# ----------------------------------------------------------------------
#  Flask route – with <pre> for code blocks
# ----------------------------------------------------------------------
@app.route('/')
def index():
    cutoff = datetime.now() - timedelta(minutes=5)
    with conversations_lock:
        recent = [
            {
                'time': entry['time'].strftime('%H:%M:%S'),
                'user': entry['user'],
                'reply': entry['reply'] if entry['reply'] is not None else "Thinking..."
            }
            for entry in conversations
            if entry['time'] > cutoff
        ]
    recent.reverse()

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Voice Assistant – Async OpenAI</title>
        <meta http-equiv="refresh" content="2">
        <style>
            body { font-family: -apple-system, sans-serif; padding: 20px; max-width: 800px; margin: 0 auto; }
            h1 { color: #333; }
            .conversation {
                background: #f9f9f9;
                border-radius: 8px;
                margin: 12px 0;
                padding: 16px;
                border-left: 4px solid #007aff;
            }
            .user { color: #007aff; font-weight: bold; }
            .ai { color: #34c759; font-weight: bold; margin-top: 6px; }
            .thinking { color: #999; font-style: italic; }
            .time { color: #888; font-size: 0.8em; }

            .code-block {
                background: #f4f4f4;
                border-radius: 4px;
                padding: 12px;
                overflow-x: auto;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                white-space: pre-wrap;
                word-break: break-word;
                border: 1px solid #ddd;
                margin: 8px 0;
            }
        </style>
    </head>
    <body>
        <h1>🗣️ Voice Assistant (Async)</h1>
        <p>Speak – your question appears immediately; reply arrives when ready.</p>
        <div id="conversations">
            {% for entry in recent %}
                <div class="conversation">
                    <div class="time">{{ entry.time }}</div>
                    <div class="user">🧑 You: {{ entry.user }}</div>
                    <div class="ai">
                        🤖 AI:
                        {% if entry.reply == "Thinking..." %}
                            <span class="thinking">{{ entry.reply }}</span>
                        {% else %}
                            <pre class="code-block">{{ entry.reply }}</pre>
                        {% endif %}
                    </div>
                </div>
            {% else %}
                <p>Speak to start a conversation...</p>
            {% endfor %}
        </div>
    </body>
    </html>
    """, recent=recent or [])

# ----------------------------------------------------------------------
#  Main entry point
# ----------------------------------------------------------------------
if __name__ == '__main__':
    from threading import Thread

    print("\n=== 🗣️ ASYNC VOICE ASSISTANT (OpenAI) ===")
    print("Speak – your speech is transcribed and sent to AI in the background.")
    print("You can keep talking while replies come in.")
    print("Open http://localhost:5000 to see the conversation.\n")

    audio_thread = Thread(target=transcribe_audio, daemon=True)
    audio_thread.start()

    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)