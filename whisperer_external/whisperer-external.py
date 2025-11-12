#!/usr/bin/env python3
"""
DUAL AUDIO TRANSCRIPTION: External Microphone + System Audio
Transcribes both what you say (external mic) and what you hear (system audio)
"""

import os
import threading
import queue
import numpy as np
import sounddevice as sd
import whisper
from flask import Flask, render_template_string
from datetime import datetime, timedelta
import time
import sys
import traceback

# === CRASH PROTECTION ===
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    print("💥 CRASH DETECTED:")
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    print("\n🔧 Troubleshooting:")
    print("1. Check System Settings > Security & Privacy > Microphone")
    print("2. Ensure Terminal has microphone access")
    print("3. Install BlackHole 2ch: https://existential.audio/blackhole/")
    print("4. Restart computer if audio issues persist")
    print("5. Try: python -c 'import sounddevice as sd; print(sd.query_devices())'")

sys.excepthook = handle_exception

# === CONFIGURATION ===
SAMPLE_RATE = 16000
CHUNK_DURATION = 3  # Process 3-second chunks
SILENCE_THRESHOLD = 0.01  # Adjust based on your microphone sensitivity
MODEL_SIZE = "base"  # "tiny", "base", "small", "medium", "large"

# Global storage for transcriptions
transcription_history = []
transcription_lock = threading.Lock()

# === SAFE AUDIO DEVICE DETECTION ===
def get_audio_devices():
    """Find both microphone input and headphone output devices - SAFE VERSION"""
    try:
        devices = sd.query_devices()
        print(f"🔍 Found {len(devices)} audio devices")
        
        # SAFE device selection with bounds checking
        mic_device = None
        headphone_device = None
        
        # Try to find external microphone first
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                print(f"  Input {i}: {dev['name']} (channels: {dev['max_input_channels']})")
                if 'external' in dev['name'].lower():
                    mic_device = i
                    print(f"🎤 Using external microphone: {dev['name']} (ID: {i})")
                    break
        
        # If no external mic found, use first available input
        if mic_device is None:
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    mic_device = i
                    print(f"🎤 Using fallback microphone: {dev['name']} (ID: {i})")
                    break
        
        # Use BlackHole for system audio capture (device 0 typically)
        if len(devices) > 0 and devices[0]['max_input_channels'] > 0:
            headphone_device = 0
            print(f"🎧 Capturing system audio via: {devices[0]['name']} (ID: 0)")
        else:
            # Try to find any BlackHole device
            for i, dev in enumerate(devices):
                if 'blackhole' in dev['name'].lower() and dev['max_input_channels'] > 0:
                    headphone_device = i
                    print(f"🎧 Capturing system audio via: {dev['name']} (ID: {i})")
                    break
        
        if mic_device is None:
            print("❌ No microphone device found")
            return None, None
            
        if headphone_device is None:
            print("❌ No system audio capture device found (install BlackHole 2ch)")
            return None, None
        
        print("⚠️  IMPORTANT: Set System Audio Output to BlackHole 2ch to capture YouTube/computer audio")
        return mic_device, headphone_device
        
    except Exception as e:
        print(f"❌ Audio device detection error: {e}")
        print("💡 Try: python -c 'import sounddevice as sd; print(sd.query_devices())'")
        return None, None

# === AUDIO PROCESSING ===
def audio_capture_loop(device_id, audio_type, audio_queue):
    """Capture audio from specified device and add to queue"""
    print(f"🎯 Starting {audio_type} capture on device {device_id}")
    
    def audio_callback(indata, frames, time_info, status):
        if status:
            print(f"Audio status: {status}")
        
        # Convert to mono and appropriate format
        audio_data = indata[:, 0] if indata.ndim > 1 else indata
        audio_data = audio_data.astype(np.float32)
        
        # Only process if there's significant audio (not silence)
        rms = np.sqrt(np.mean(audio_data**2))
        if rms > SILENCE_THRESHOLD:
            audio_queue.put((audio_data.copy(), audio_type))
    
    try:
        with sd.InputStream(
            device=device_id,
            samplerate=SAMPLE_RATE,
            channels=1,
            callback=audio_callback,
            blocksize=int(SAMPLE_RATE * CHUNK_DURATION)
        ):
            print(f"✅ {audio_type} capture active - monitoring for audio...")
            while True:
                sd.sleep(1000)
    except Exception as e:
        print(f"❌ {audio_type} capture error: {e}")

def transcribe_audio_loop(model, audio_queue):
    """Transcribe audio chunks from queue"""
    print("🧠 Transcription engine ready - processing audio...")
    
    while True:
        try:
            audio_data, audio_type = audio_queue.get(timeout=10)
            
            # Transcribe using Whisper
            result = model.transcribe(audio_data, fp16=False)
            text = result["text"].strip()
            
            if text and len(text) > 2:  # Only store meaningful transcriptions
                timestamp = datetime.now()
                
                with transcription_lock:
                    transcription_history.append({
                        'text': text,
                        'type': audio_type,
                        'time': timestamp
                    })
                    
                    # Keep only last 50 entries
                    if len(transcription_history) > 50:
                        transcription_history.pop(0)
                
                print(f"[{timestamp.strftime('%H:%M:%S')}] {audio_type.upper()}: {text}")
                
        except queue.Empty:
            continue
        except Exception as e:
            print(f"❌ Transcription error: {e}")

# === FLASK WEB INTERFACE ===
app = Flask(__name__)

@app.route('/')
def index():
    """Web interface showing real-time transcriptions"""
    with transcription_lock:
        # Get recent transcriptions (last 10 minutes)
        cutoff_time = datetime.now() - timedelta(minutes=10)
        all_recent = [t for t in transcription_history if t['time'] > cutoff_time]
        all_recent.sort(key=lambda x: x['time'])
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dual Audio Transcription</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f5f5f7;
                color: #333;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                padding: 30px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            h1 {
                color: #1d1d1f;
                margin-bottom: 8px;
            }
            .subtitle {
                color: #86868b;
                margin-bottom: 30px;
                font-size: 17px;
            }
            .status {
                background: #34c759;
                color: white;
                padding: 10px 16px;
                border-radius: 8px;
                margin-bottom: 30px;
                font-weight: 600;
            }
            .transcription {
                padding: 16px;
                margin: 16px 0;
                border-radius: 10px;
                border-left: 4px solid;
            }
            .microphone {
                border-color: #007aff;
                background: #f0f7ff;
            }
            .headphone {
                border-color: #34c759;
                background: #f0fff4;
            }
            .type-badge {
                font-weight: 600;
                font-size: 14px;
                padding: 4px 8px;
                border-radius: 6px;
                margin-right: 8px;
            }
            .mic-badge {
                background: #007aff;
                color: white;
            }
            .headphone-badge {
                background: #34c759;
                color: white;
            }
            .time {
                color: #86868b;
                font-size: 14px;
            }
            .empty-state {
                text-align: center; 
                color: #86868b; 
                padding: 40px;
                font-style: italic;
                background: #f9f9fa;
                border-radius: 8px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎤🎧 Dual Audio Transcription</h1>
            <div class="subtitle">Transcribing both what you say and what you hear</div>
            <div class="status">● LIVE - Monitoring external microphone and system audio</div>
            
            <div id="transcriptions">
                {% for entry in all_recent %}
                    <div class="transcription {{ entry.type }}">
                        <span class="type-badge {{ 'mic-badge' if entry.type == 'microphone' else 'headphone-badge' }}">
                            {{ '🎤 YOU' if entry.type == 'microphone' else '🎧 HEAR' }}
                        </span>
                        <span class="time">{{ entry.time.strftime('%H:%M:%S') }}</span>
                        <div style="margin-top: 5px;">{{ entry.text }}</div>
                    </div>
                {% else %}
                    <div class="empty-state">
                        Speak into your microphone or play audio through speakers to see transcriptions...
                        <br><br>
                        <small>Make sure system audio output is set to BlackHole 2ch</small>
                    </div>
                {% endfor %}
            </div>
        </div>
        
        <script>
            // Auto-refresh every 3 seconds
            setTimeout(() => { window.location.reload(); }, 3000);
        </script>
    </body>
    </html>
    """, all_recent=all_recent)

def start_dual_transcription():
    """Start both audio capture threads"""
    # Get audio devices
    mic_device, headphone_device = get_audio_devices()
    
    if mic_device is None or headphone_device is None:
        print("❌ Cannot start - audio devices not available")
        return
    
    # Load Whisper model
    print(f"📦 Loading Whisper model ({MODEL_SIZE})...")
    model = whisper.load_model(MODEL_SIZE)
    print("✅ Model loaded")
    
    # Create audio queues
    audio_queue = queue.Queue()
    
    # Start capture threads
    mic_thread = threading.Thread(
        target=audio_capture_loop, 
        args=(mic_device, 'microphone', audio_queue),
        daemon=True
    )
    
    headphone_thread = threading.Thread(
        target=audio_capture_loop, 
        args=(headphone_device, 'headphone', audio_queue),
        daemon=True
    )
    
    # Start transcription thread
    transcribe_thread = threading.Thread(
        target=transcribe_audio_loop,
        args=(model, audio_queue),
        daemon=True
    )
    
    mic_thread.start()
    headphone_thread.start() 
    transcribe_thread.start()
    
    print("✅ All threads started - system ready")

if __name__ == '__main__':
    print("\n=== DUAL AUDIO TRANSCRIPTION ===")
    print("Mode: Transcribing external microphone + system audio")
    print("Monitoring:")
    print("  🎤 External Microphone - What you're saying")
    print("  🎧 System Audio - What you're hearing (via BlackHole)") 
    print("Web interface: http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    
    # Start both transcription threads
    start_dual_transcription()
    
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)