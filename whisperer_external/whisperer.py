#!/usr/bin/env python3
"""
Dual Audio Transcription - Microphone Input & Headphone Output
Transcribes both sides of a conversation: what you say and what you hear
"""

import os
from datetime import datetime, timedelta
from collections import deque
import logging
from flask import Flask, render_template_string
import sounddevice as sd
import numpy as np
import whisper
import threading

# Initialize Flask app
app = Flask(__name__)

# Audio configuration
sampling_rate = 16000
chunk_size = 4096
silence_threshold = 0.015
min_audio_length = 1.0

# Load Whisper model
model = whisper.load_model("base")

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/dual_transcription.log'),
        logging.StreamHandler()
    ],
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Separate deques for microphone and headphone transcriptions
mic_transcriptions = deque(maxlen=20)
headphone_transcriptions = deque(maxlen=20)

def get_audio_devices():
    """Find both microphone input and headphone output devices - FIXED VERSION"""
    devices = sd.query_devices()
    
    mic_device = None
    headphone_device = None
    
    # Patterns for microphone input (what you're saying)
    mic_patterns = [
        "external microphone",
        "headphones",
        "earpods", 
        "airpods",
        "headset",
        "macbook pro microphone",
        "built-in microphone",
        "default input"
    ]
    
    # Patterns for headphone output (what you're hearing)
    headphone_patterns = [
        "external headphone",
        "headphones",
        "earpods",
        "airpods", 
        "headset",
        "built-in output",
        "default output"
    ]
    
    # Find microphone input device
    for pattern in mic_patterns:
        for i, dev in enumerate(devices):
            if (dev['max_input_channels'] > 0 and 
                pattern.lower() in dev['name'].lower()):
                mic_device = i
                logging.info(f"Found microphone device: {dev['name']} (ID: {i})")
                break
        if mic_device is not None:
            break
    
    # Find headphone output device (for loopback)
    for pattern in headphone_patterns:
        for i, dev in enumerate(devices):
            if (dev['max_output_channels'] > 0 and 
                pattern.lower() in dev['name'].lower()):
                headphone_device = i
                logging.info(f"Found headphone device: {dev['name']} (ID: {i})")
                break
        if headphone_device is not None:
            break
    
    # Fallbacks - FIXED: No more len() on sd.default.device
    if mic_device is None:
        # Get default input device safely
        default_input = sd.default.device[0] if sd.default.device else None
        if default_input is not None:
            mic_device = default_input
            logging.info(f"Using default input device for microphone: {devices[mic_device]['name']}")
        else:
            # Find first available input device
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    mic_device = i
                    logging.info(f"Using first available input device: {dev['name']} (ID: {i})")
                    break
    
    # FIXED: Handle headphone device selection without using len()
    if headphone_device is None:
        # Get default output device safely
        default_output = None
        if sd.default.device:
            # Safe way to get output device without using len()
            try:
                # Try to access by index directly
                default_output = sd.default.device[1]
            except (IndexError, TypeError):
                # Fallback to input device if output not available
                default_output = sd.default.device[0]
        
        if default_output is not None:
            headphone_device = default_output
            logging.info(f"Using default output device for headphones: {devices[headphone_device]['name']}")
        else:
            # Find first available output device
            for i, dev in enumerate(devices):
                if dev['max_output_channels'] > 0:
                    headphone_device = i
                    logging.info(f"Using first available output device: {dev['name']} (ID: {i})")
                    break
    
    return mic_device, headphone_device

def list_audio_devices():
    """List all available audio devices for debugging"""
    devices = sd.query_devices()
    print("\n=== Available Audio Devices ===")
    print("INPUT DEVICES:")
    for i, dev in enumerate(devices):
        if dev['max_input_channels'] > 0:
            # FIXED: Safe default device checking
            default_input = sd.default.device[0] if sd.default.device else None
            default_indicator = " (DEFAULT INPUT)" if i == default_input else ""
            print(f"  {i}: {dev['name']}{default_indicator}")
    
    print("\nOUTPUT DEVICES:")
    for i, dev in enumerate(devices):
        if dev['max_output_channels'] > 0:
            # FIXED: Safe default device checking
            default_output = sd.default.device[1] if sd.default.device else None
            default_indicator = " (DEFAULT OUTPUT)" if i == default_output else ""
            print(f"  {i}: {dev['name']}{default_indicator}")
    print("=====================================\n")

def transcribe_audio_stream(device_id, device_type, transcription_deque):
    """Transcribe audio from a specific device stream"""
    try:
        device_name = sd.query_devices()[device_id]['name']
        logging.info(f"Starting {device_type} transcription from: {device_name} (ID: {device_id})")

        # Get device info to handle channels properly
        device_info = sd.query_devices(device_id)
        channels = min(device_info['max_input_channels'], 1)  # Use mono for compatibility

        with sd.InputStream(
            samplerate=sampling_rate,
            channels=channels,
            dtype='float32',
            device=device_id,
            blocksize=chunk_size,
            latency='high'
        ) as stream:
            logging.info(f"{device_type.upper()} stream active - listening...")
            
            audio_buffer = np.array([], dtype=np.float32)
            last_active = datetime.now()
            
            while True:
                audio_chunk, overflowed = stream.read(chunk_size)
                if overflowed:
                    logging.debug(f"{device_type} buffer overflow occurred")
                
                audio_chunk = audio_chunk.squeeze()
                amplitude = np.max(np.abs(audio_chunk))
                
                # Buffer audio when sound detected
                if amplitude > silence_threshold:
                    audio_buffer = np.concatenate((audio_buffer, audio_chunk))
                    last_active = datetime.now()
                elif len(audio_buffer) > 0:
                    # Process when silence detected after speech
                    silence_duration = (datetime.now() - last_active).total_seconds()
                    if silence_duration > 0.5 and len(audio_buffer) > sampling_rate * min_audio_length:
                        try:
                            # Normalize volume for better transcription
                            max_amp = np.max(np.abs(audio_buffer))
                            if max_amp > 0:
                                audio_buffer = audio_buffer * (1.0 / max_amp)
                            
                            result = model.transcribe(audio_buffer, fp16=False, language='en')
                            text = result["text"].strip()
                            
                            if text:
                                entry = {
                                    'time': datetime.now(),
                                    'text': text,
                                    'type': device_type
                                }
                                transcription_deque.append(entry)
                                
                                # Color-coded console output
                                if device_type == "microphone":
                                    color_prefix = "\033[94m"  # Blue
                                    color_suffix = "\033[0m"
                                    log_prefix = "MIC"
                                else:
                                    color_prefix = "\033[92m"  # Green  
                                    color_suffix = "\033[0m"
                                    log_prefix = "HEADPHONES"
                                
                                print(f"\n{color_prefix}>> {log_prefix}: {text} <<{color_suffix}\n")
                                logging.info(f"{log_prefix}: {text}")
                        except Exception as e:
                            logging.error(f"{device_type} transcription error: {str(e)}")
                        finally:
                            audio_buffer = np.array([], dtype=np.float32)
                
    except Exception as e:
        logging.error(f"Fatal {device_type} audio error: {str(e)}", exc_info=True)
        raise

def start_dual_transcription():
    """Start both microphone and headphone transcription threads"""
    # List devices for debugging
    list_audio_devices()
    
    # Get both devices
    mic_device, headphone_device = get_audio_devices()
    
    if mic_device is None:
        logging.error("No microphone device found! Cannot start transcription.")
        return
        
    if headphone_device is None:
        logging.error("No headphone device found! Cannot start transcription.")
        return
    
    # Start microphone transcription (what you're saying)
    mic_thread = threading.Thread(
        target=transcribe_audio_stream, 
        args=(mic_device, "microphone", mic_transcriptions),
        daemon=True
    )
    mic_thread.start()
    
    # Start headphone transcription (what you're hearing)
    # Note: This requires stereo mix or loopback capability on your system
    headphone_thread = threading.Thread(
        target=transcribe_audio_stream, 
        args=(headphone_device, "headphones", headphone_transcriptions),
        daemon=True
    )
    headphone_thread.start()
    
    logging.info("Dual transcription started - monitoring both microphone and headphones")

@app.route('/')
def index():
    one_minute_ago = datetime.now() - timedelta(minutes=1)
    
    # Combine and sort recent transcriptions from both sources
    recent_mic = [
        {'time': entry['time'], 'text': entry['text'], 'type': 'microphone'}
        for entry in mic_transcriptions
        if entry['time'] > one_minute_ago
    ]
    
    recent_headphones = [
        {'time': entry['time'], 'text': entry['text'], 'type': 'headphones'}  
        for entry in headphone_transcriptions
        if entry['time'] > one_minute_ago
    ]
    
    all_recent = recent_mic + recent_headphones
    all_recent.sort(key=lambda x: x['time'])
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dual Audio Transcription</title>
        <meta http-equiv="refresh" content="2">
        <style>
            body { 
                font-family: -apple-system, sans-serif; 
                padding: 20px; 
                background: #f5f5f5;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 25px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 { 
                color: #333; 
                text-align: center;
                margin-bottom: 10px;
            }
            .subtitle {
                text-align: center;
                color: #666;
                margin-bottom: 20px;
                font-style: italic;
            }
            .transcription {
                padding: 12px; 
                border-bottom: 1px solid #e1e1e1;
                font-size: 1.1em;
                line-height: 1.4;
                margin-bottom: 8px;
                border-left: 4px solid #ddd;
                padding-left: 15px;
            }
            .microphone {
                border-left-color: #4285f4;
                background-color: #f8fbff;
            }
            .headphones {
                border-left-color: #34a853;
                background-color: #f8fff9;
            }
            .type-badge {
                display: inline-block;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 0.8em;
                font-weight: bold;
                margin-right: 8px;
            }
            .mic-badge {
                background: #4285f4;
                color: white;
            }
            .headphone-badge {
                background: #34a853;
                color: white;
            }
            .status {
                text-align: center;
                color: #4CAF50;
                font-weight: bold;
                margin-bottom: 20px;
            }
            .empty-state {
                text-align: center; 
                color: #999; 
                padding: 40px;
                font-style: italic;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎤🎧 Dual Audio Transcription</h1>
            <div class="subtitle">Transcribing both what you say and what you hear</div>
            <div class="status">● LIVE - Monitoring microphone and headphones</div>
            
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
                        Speak into your microphone or play audio through headphones to see transcriptions...
                    </div>
                {% endfor %}
            </div>
        </div>
    </body>
    </html>
    """, all_recent=all_recent)

if __name__ == '__main__':
    print("\n=== DUAL AUDIO TRANSCRIPTION ===")
    print("Mode: Transcribing both microphone input and headphone output")
    print("Monitoring:")
    print("  🎤 Microphone - What you're saying")
    print("  🎧 Headphones - What you're hearing") 
    print("Web interface: http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    
    # Start both transcription threads
    start_dual_transcription()
    
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)