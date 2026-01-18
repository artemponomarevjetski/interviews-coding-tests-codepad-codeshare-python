#!/usr/bin/env python3
"""
DUAL AUDIO TRANSCRIPTION: External Microphone + System Audio
Transcribes both what you say (external mic) and what you hear (system audio)
ENHANCED VERSION: Optimized for YouTube/system audio with better device detection
FIXED VERSION: Resolved dtype mismatch errors (float32 vs float64)
"""

import os
import threading
import queue
import numpy as np
import sounddevice as sd
import whisper
from flask import Flask, render_template_string, request, redirect
from datetime import datetime, timedelta
import time
import sys
import traceback
import warnings
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")

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
YOUTUBE_VOLUME_BOOST = 1.5  # Boost YouTube audio by 50%

# Global storage for transcriptions
transcription_history = []
transcription_lock = threading.Lock()
youtube_url_log = []

# === ENHANCED AUDIO DEVICE DETECTION ===
def get_audio_devices():
    """Find both microphone input and system audio devices - ENHANCED VERSION"""
    try:
        devices = sd.query_devices()
        print(f"🔍 Found {len(devices)} audio devices")
        
        mic_device = None
        system_audio_device = None
        
        # Print all devices for debugging
        print("\n📋 Available Audio Devices:")
        for i, dev in enumerate(devices):
            input_ch = dev['max_input_channels']
            output_ch = dev['max_output_channels']
            name = dev['name']
            print(f"  [{i}] {name}")
            print(f"     Input: {input_ch} channels | Output: {output_ch} channels")
        
        # === MICROPHONE DETECTION ===
        print("\n🎤 Looking for microphone...")
        
        # Strategy 1: Look for external USB microphones first
        for i, dev in enumerate(devices):
            name_lower = dev['name'].lower()
            if (dev['max_input_channels'] > 0 and 
                'blackhole' not in name_lower and
                any(keyword in name_lower for keyword in ['usb', 'external', 'blue', 'shure', 'rode', 'focusrite'])):
                mic_device = i
                print(f"✅ Found external microphone: {dev['name']} (ID: {i})")
                break
        
        # Strategy 2: Look for built-in microphone
        if mic_device is None:
            for i, dev in enumerate(devices):
                name_lower = dev['name'].lower()
                if (dev['max_input_channels'] > 0 and 
                    'blackhole' not in name_lower and
                    any(keyword in name_lower for keyword in ['macbook', 'built-in', 'internal', 'pro microphone'])):
                    mic_device = i
                    print(f"✅ Found built-in microphone: {dev['name']} (ID: {i})")
                    break
        
        # Strategy 3: Fallback to any non-BlackHole input device
        if mic_device is None:
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0 and 'blackhole' not in dev['name'].lower():
                    mic_device = i
                    print(f"⚠️  Using fallback microphone: {dev['name']} (ID: {i})")
                    break
        
        # === SYSTEM AUDIO DEVICE DETECTION ===
        print("\n🎧 Looking for system audio capture device...")
        
        # Strategy 1: Look for BlackHole (preferred for YouTube)
        for i, dev in enumerate(devices):
            name_lower = dev['name'].lower()
            if (dev['max_input_channels'] > 0 and 
                any(keyword in name_lower for keyword in ['blackhole', 'black hole', 'black_hole', 'loopback'])):
                system_audio_device = i
                print(f"✅ Found system audio device: {dev['name']} (ID: {i}) - Perfect for YouTube!")
                break
        
        # Strategy 2: Look for aggregate/multi-output devices
        if system_audio_device is None:
            for i, dev in enumerate(devices):
                name_lower = dev['name'].lower()
                if (dev['max_input_channels'] > 0 and 
                    any(keyword in name_lower for keyword in ['aggregate', 'multi-output', 'combined', 'mix'])):
                    system_audio_device = i
                    print(f"✅ Found aggregate device: {dev['name']} (ID: {i})")
                    break
        
        # Strategy 3: Look for any output device that can also capture input
        if system_audio_device is None:
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0 and dev['max_output_channels'] > 0:
                    system_audio_device = i
                    print(f"⚠️  Using output device for system audio: {dev['name']} (ID: {i})")
                    break
        
        # Strategy 4: Last resort - use device 0 if it has input
        if system_audio_device is None and len(devices) > 0 and devices[0]['max_input_channels'] > 0:
            system_audio_device = 0
            print(f"⚠️  Using device 0 for system audio: {devices[0]['name']} (ID: 0)")
        
        # === VALIDATION ===
        if mic_device is None:
            print("❌ No microphone device found")
            print("💡 Check if microphone is connected and permissions are granted")
            return None, None
            
        if system_audio_device is None:
            print("❌ No system audio capture device found")
            print("💡 For YouTube transcription, install BlackHole 2ch:")
            print("   Download: https://existential.audio/blackhole/")
            print("   Then set System Audio Output to BlackHole 2ch")
            return None, None
        
        print(f"\n✅ Device Selection Complete:")
        print(f"   🎤 Microphone: Device {mic_device} - {devices[mic_device]['name']}")
        print(f"   🎧 System Audio: Device {system_audio_device} - {devices[system_audio_device]['name']}")
        
        # Quick device test
        print("\n🔧 Quick device test...")
        try:
            # Test microphone
            test_rec = sd.rec(int(0.5 * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                            channels=1, device=mic_device, dtype='float32')
            sd.wait()
            mic_level = float(np.max(np.abs(test_rec)))
            print(f"   Microphone test: {'✅ Good level' if mic_level > 0.02 else '⚠️  Low level'} ({mic_level:.4f})")
            
            # Test system audio device
            test_rec = sd.rec(int(0.5 * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                            channels=1, device=system_audio_device, dtype='float32')
            sd.wait()
            sys_level = float(np.max(np.abs(test_rec)))
            print(f"   System audio test: {'✅ Good level' if sys_level > 0.01 else '⚠️  Low level'} ({sys_level:.4f})")
            
        except Exception as e:
            print(f"⚠️  Device test warning: {e}")
            print("   Will continue anyway - test in web interface")
        
        return mic_device, system_audio_device
        
    except Exception as e:
        print(f"❌ Audio device detection error: {e}")
        print("💡 Try running: python -c 'import sounddevice as sd; print(sd.query_devices())'")
        return None, None

# === FIXED AUDIO PROCESSING ===
def ensure_float32(audio_data):
    """Ensure audio data is float32 - FIX for dtype mismatch"""
    if audio_data.dtype != np.float32:
        return audio_data.astype(np.float32)
    return audio_data

def enhance_youtube_audio(audio_data, audio_type):
    """Apply processing specific to YouTube/system audio - FIXED VERSION"""
    if audio_type != 'system_audio':
        return audio_data
    
    # Ensure float32 dtype (CRITICAL FIX for whisper compatibility)
    audio_data = ensure_float32(audio_data)
    
    # Boost volume for YouTube audio
    audio_data = audio_data * YOUTUBE_VOLUME_BOOST
    
    # Clip to prevent distortion
    audio_data = np.clip(audio_data, -0.99, 0.99)
    
    # Simple noise gate for system audio
    threshold = SILENCE_THRESHOLD * 2
    audio_data[np.abs(audio_data) < threshold] = 0
    
    # Normalize
    max_val = np.max(np.abs(audio_data))
    if max_val > 0.1:
        audio_data = audio_data / max_val * 0.9
    
    # Final dtype check
    return ensure_float32(audio_data)

def enhance_microphone_audio(audio_data):
    """Apply processing for microphone audio - FIXED VERSION"""
    # Ensure float32 dtype (CRITICAL FIX for whisper compatibility)
    audio_data = ensure_float32(audio_data)
    
    # Light noise reduction for microphone
    if len(audio_data) > 100:
        # Simple rolling mean with float32 kernel
        kernel_size = 3
        kernel = np.ones(kernel_size, dtype=np.float32) / kernel_size
        audio_data = np.convolve(audio_data, kernel, mode='same')
    
    # Final dtype check
    return ensure_float32(audio_data)

def audio_capture_loop(device_id, audio_type, audio_queue):
    """Capture audio from specified device and add to queue - ENHANCED"""
    print(f"🎯 Starting {audio_type} capture on device {device_id}")
    
    def audio_callback(indata, frames, time_info, status):
        if status:
            print(f"⚠️  Audio status ({audio_type}): {status}")
        
        # Convert to mono and ensure float32
        audio_data = indata[:, 0] if indata.ndim > 1 else indata
        audio_data = audio_data.astype(np.float32).copy()
        
        # Apply type-specific processing
        if audio_type == 'system_audio':
            audio_data = enhance_youtube_audio(audio_data, audio_type)
        else:
            audio_data = enhance_microphone_audio(audio_data)
        
        # Calculate RMS and check threshold
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
        traceback.print_exc()

# === ENHANCED TRANSCRIPTION ===
def transcribe_audio_loop(model, audio_queue):
    """Transcribe audio chunks from queue - OPTIMIZED FOR YOUTUBE"""
    print("🧠 Transcription engine ready - processing audio...")
    
    # Cache for duplicate detection
    last_texts = []
    
    while True:
        try:
            audio_data, audio_type = audio_queue.get(timeout=15)
            
            # Skip if audio is too short
            if len(audio_data) < SAMPLE_RATE * 0.5:  # Less than 0.5 seconds
                continue
            
            # Final dtype check before transcription
            if audio_data.dtype != np.float32:
                print(f"⚠️  Converting {audio_data.dtype} to float32 before transcription")
                audio_data = audio_data.astype(np.float32)
            
            # Use different parameters for YouTube vs microphone
            if audio_type == 'system_audio':
                # Optimized for clear YouTube/system audio
                result = model.transcribe(
                    audio_data,
                    fp16=False,
                    language="en",
                    task="transcribe",
                    temperature=0.0,  # More deterministic
                    best_of=1,
                    beam_size=1,
                    suppress_tokens=[-1],  # Suppress common unnecessary tokens
                    without_timestamps=True
                )
            else:
                # Standard for microphone
                result = model.transcribe(
                    audio_data,
                    fp16=False,
                    language="en",
                    temperature=0.0
                )
            
            text = result["text"].strip()
            
            # Filter out meaningless transcriptions
            if (len(text) > 3 and 
                not text.lower().startswith('thank you for watching') and
                not text.lower().startswith('like and subscribe') and
                not all(c in ['.', ',', '!', '?', ' '] for c in text)):
                
                # Check for duplicates (prevent same text within 10 seconds)
                is_duplicate = False
                current_time = datetime.now()
                cutoff = current_time - timedelta(seconds=10)
                
                with transcription_lock:
                    # Check recent transcriptions for duplicates
                    for entry in transcription_history[-5:]:
                        if (entry['text'] == text and 
                            entry['type'] == audio_type and
                            entry['time'] > cutoff):
                            is_duplicate = True
                            break
                
                if not is_duplicate:
                    timestamp = datetime.now()
                    
                    with transcription_lock:
                        transcription_history.append({
                            'text': text,
                            'type': audio_type,
                            'time': timestamp
                        })
                        
                        # Keep only last 100 entries
                        if len(transcription_history) > 100:
                            transcription_history.pop(0)
                    
                    # Add context for YouTube
                    display_type = "🎬 YOUTUBE" if audio_type == 'system_audio' else "🎤 YOU"
                    print(f"[{timestamp.strftime('%H:%M:%S')}] {display_type}: {text}")
                
        except queue.Empty:
            continue
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            if "expected m1 and m2 to have the same dtype" in str(e):
                print("💡 Dtype mismatch detected - trying to fix...")
                # Try to recover by forcing float32
                try:
                    if 'audio_data' in locals():
                        audio_data = audio_data.astype(np.float32)
                except:
                    pass
            elif "cuda" in str(e).lower():
                print("💡 Running on CPU - using fp16=False")

# === ENHANCED FLASK WEB INTERFACE ===
app = Flask(__name__)

@app.route('/')
def index():
    """Web interface showing real-time transcriptions"""
    with transcription_lock:
        # Get recent transcriptions (last 15 minutes)
        cutoff_time = datetime.now() - timedelta(minutes=15)
        all_recent = [t for t in transcription_history if t['time'] > cutoff_time]
        all_recent.sort(key=lambda x: x['time'], reverse=True)  # Newest first
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dual Audio Transcription - YouTube Optimized</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            :root {
                --mic-color: #007aff;
                --youtube-color: #ff0000;
                --system-color: #34c759;
                --bg-color: #f5f5f7;
                --card-bg: #ffffff;
                --text-color: #1d1d1f;
                --text-secondary: #86868b;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: var(--bg-color);
                color: var(--text-color);
                line-height: 1.6;
            }
            
            .container {
                max-width: 900px;
                margin: 0 auto;
                background: var(--card-bg);
                border-radius: 16px;
                padding: 30px;
                box-shadow: 0 8px 30px rgba(0,0,0,0.08);
            }
            
            header {
                text-align: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 1px solid #e5e5e7;
            }
            
            h1 {
                color: var(--text-color);
                margin: 0 0 8px 0;
                font-size: 32px;
            }
            
            .subtitle {
                color: var(--text-secondary);
                font-size: 18px;
                margin-bottom: 20px;
            }
            
            .status-bar {
                display: flex;
                gap: 15px;
                margin-bottom: 30px;
            }
            
            .status-item {
                flex: 1;
                padding: 12px 16px;
                border-radius: 10px;
                font-weight: 600;
                text-align: center;
            }
            
            .status-mic {
                background: linear-gradient(135deg, #007aff22, #007aff11);
                border: 2px solid var(--mic-color);
                color: var(--mic-color);
            }
            
            .status-youtube {
                background: linear-gradient(135deg, #ff000022, #ff000011);
                border: 2px solid var(--youtube-color);
                color: var(--youtube-color);
            }
            
            .transcription {
                padding: 18px;
                margin: 20px 0;
                border-radius: 12px;
                border-left: 5px solid;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            
            .transcription:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(0,0,0,0.08);
            }
            
            .microphone {
                border-left-color: var(--mic-color);
                background: linear-gradient(135deg, #007aff08, #007aff04);
            }
            
            .system_audio {
                border-left-color: var(--youtube-color);
                background: linear-gradient(135deg, #ff000008, #ff000004);
            }
            
            .type-badge {
                font-weight: 700;
                font-size: 13px;
                padding: 6px 12px;
                border-radius: 20px;
                margin-right: 10px;
                display: inline-block;
                letter-spacing: 0.5px;
            }
            
            .mic-badge {
                background: var(--mic-color);
                color: white;
            }
            
            .youtube-badge {
                background: var(--youtube-color);
                color: white;
            }
            
            .time {
                color: var(--text-secondary);
                font-size: 14px;
                margin-left: 10px;
            }
            
            .transcription-text {
                margin: 12px 0 0 0;
                font-size: 16px;
                line-height: 1.5;
            }
            
            .empty-state {
                text-align: center;
                padding: 60px 40px;
                color: var(--text-secondary);
            }
            
            .setup-guide {
                background: linear-gradient(135deg, #fff3e0, #fff8e1);
                border-left: 4px solid #ff9800;
                padding: 25px;
                margin: 30px 0;
                border-radius: 12px;
            }
            
            .setup-guide h3 {
                margin-top: 0;
                color: #e65100;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .youtube-steps {
                background: linear-gradient(135deg, #ffeaea, #fff0f0);
                border-left: 4px solid #ff4444;
                padding: 25px;
                margin: 30px 0;
                border-radius: 12px;
            }
            
            .youtube-steps h3 {
                margin-top: 0;
                color: #d32f2f;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            ol {
                padding-left: 20px;
                margin-bottom: 0;
            }
            
            li {
                margin-bottom: 10px;
            }
            
            strong {
                color: var(--text-color);
            }
            
            a {
                color: var(--mic-color);
                text-decoration: none;
                font-weight: 600;
            }
            
            a:hover {
                text-decoration: underline;
            }
            
            .controls {
                display: flex;
                gap: 15px;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e5e5e7;
            }
            
            .refresh-btn {
                background: var(--mic-color);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                transition: background 0.2s;
            }
            
            .refresh-btn:hover {
                background: #0056cc;
            }
            
            @media (max-width: 768px) {
                .container {
                    padding: 20px;
                }
                
                .status-bar {
                    flex-direction: column;
                }
                
                h1 {
                    font-size: 26px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🎤🎬 Dual Audio Transcription</h1>
                <div class="subtitle">Transcribing your voice + YouTube/system audio in real-time</div>
            </header>
            
            <div class="status-bar">
                <div class="status-item status-mic">
                    🎤 MICROPHONE: ACTIVE
                </div>
                <div class="status-item status-youtube">
                    🎬 YOUTUBE: ACTIVE
                </div>
            </div>
            
            {% if all_recent %}
                <div id="transcriptions">
                    {% for entry in all_recent %}
                        <div class="transcription {{ entry.type }}">
                            <div>
                                <span class="type-badge {{ 'mic-badge' if entry.type == 'microphone' else 'youtube-badge' }}">
                                    {{ '🎤 YOU SAID' if entry.type == 'microphone' else '🎬 YOUTUBE' }}
                                </span>
                                <span class="time">{{ entry.time.strftime('%H:%M:%S') }}</span>
                            </div>
                            <p class="transcription-text">{{ entry.text }}</p>
                        </div>
                    {% endfor %}
                </div>
            {% else %}
                <div class="empty-state">
                    <h3>🎯 No transcriptions yet</h3>
                    <p>Start speaking or play a YouTube video to see real-time transcriptions...</p>
                    
                    <div class="setup-guide">
                        <h3>📋 Microphone Setup</h3>
                        <ol>
                            <li><strong>Grant Microphone Permission:</strong><br>
                                System Settings → Privacy & Security → Microphone<br>
                                Ensure Terminal has microphone access</li>
                            <li><strong>Test Your Microphone:</strong><br>
                                Speak clearly - you should see "🎤 YOU SAID" transcriptions appear</li>
                        </ol>
                    </div>
                    
                    <div class="youtube-steps">
                        <h3>🎬 YouTube/System Audio Setup</h3>
                        <ol>
                            <li><strong>Install BlackHole 2ch:</strong><br>
                                <a href="https://existential.audio/blackhole/" target="_blank">Download BlackHole 2ch</a> (free)</li>
                            <li><strong>Set System Output:</strong><br>
                                System Settings → Sound → Output → BlackHole 2ch</li>
                            <li><strong>Play YouTube:</strong><br>
                                Play any YouTube video - audio will be captured automatically</li>
                            <li><strong>Multi-Output (Optional):</strong><br>
                                Use Audio MIDI Setup to create Multi-Output device<br>
                                Combine BlackHole + your speakers to hear audio</li>
                        </ol>
                    </div>
                    
                    <p><small>💡 Tip: Adjust microphone placement and volume for best results</small></p>
                </div>
            {% endif %}
            
            <div class="controls">
                <button class="refresh-btn" onclick="window.location.reload()">
                    🔄 Refresh Now
                </button>
                <div style="flex: 1; text-align: right; color: var(--text-secondary); font-size: 14px;">
                    Auto-refreshes every 5 seconds
                </div>
            </div>
        </div>
        
        <script>
            // Auto-refresh every 5 seconds
            setTimeout(() => { window.location.reload(); }, 5000);
            
            // Smooth scroll to new transcriptions
            document.addEventListener('DOMContentLoaded', function() {
                if (window.location.hash !== '#bottom') {
                    window.scrollTo(0, 0);
                }
            });
        </script>
    </body>
    </html>
    """, all_recent=all_recent)

@app.route('/log-youtube', methods=['POST'])
def log_youtube_url():
    """Log a YouTube URL for reference"""
    url = request.form.get('youtube_url', '').strip()
    if url and 'youtube.com' in url or 'youtu.be' in url:
        youtube_url_log.append({
            'url': url,
            'time': datetime.now()
        })
        # Keep only last 10 URLs
        if len(youtube_url_log) > 10:
            youtube_url_log.pop(0)
    return redirect('/')

# === MAIN STARTUP ===
def start_dual_transcription():
    """Start both audio capture threads - ENHANCED"""
    print("\n" + "="*70)
    print("🎤🎬 ENHANCED DUAL AUDIO TRANSCRIPTION (YouTube Optimized)")
    print("="*70)
    
    # Get audio devices
    mic_device, system_audio_device = get_audio_devices()
    
    if mic_device is None or system_audio_device is None:
        print("\n❌ Cannot start - audio devices not available")
        print("💡 For YouTube transcription, you NEED BlackHole 2ch installed")
        print("   Download from: https://existential.audio/blackhole/")
        print("💡 Then set System Audio Output to BlackHole 2ch")
        print("💡 Also check microphone permissions in System Settings")
        return
    
    # Load Whisper model
    print(f"\n📦 Loading Whisper model ({MODEL_SIZE})...")
    try:
        model = whisper.load_model(MODEL_SIZE)
        print(f"✅ Model loaded successfully")
        print(f"   Sample rate: {SAMPLE_RATE} Hz")
        print(f"   Chunk duration: {CHUNK_DURATION} seconds")
    except Exception as e:
        print(f"❌ Failed to load Whisper model: {e}")
        print("💡 Try reinstalling whisper: pip install --upgrade openai-whisper")
        print("💡 Or try faster-whisper: pip install faster-whisper")
        return
    
    # Create audio queue
    audio_queue = queue.Queue()
    
    # Start capture threads
    mic_thread = threading.Thread(
        target=audio_capture_loop, 
        args=(mic_device, 'microphone', audio_queue),
        daemon=True
    )
    
    system_thread = threading.Thread(
        target=audio_capture_loop, 
        args=(system_audio_device, 'system_audio', audio_queue),
        daemon=True
    )
    
    # Start transcription thread
    transcribe_thread = threading.Thread(
        target=transcribe_audio_loop,
        args=(model, audio_queue),
        daemon=True
    )
    
    mic_thread.start()
    system_thread.start() 
    transcribe_thread.start()
    
    print("\n✅ All systems ready! Starting transcription...")
    print("\n📊 MONITORING:")
    print("  🎤 Microphone - What you're saying")
    print("  🎬 YouTube/System Audio - What you're hearing (via BlackHole)")
    
    print("\n🎯 QUICK START:")
    print("  1. Speak into your microphone → Look for '🎤 YOU SAID'")
    print("  2. Play YouTube video → Look for '🎬 YOUTUBE'")
    print("  3. Open http://localhost:5000 in your browser")
    
    print("\n⚙️  TIPS FOR BEST YOUTUBE TRANSCRIPTION:")
    print("  • Keep YouTube volume at 70-100% for best results")
    print("  • Ensure System Audio Output is set to BlackHole 2ch")
    print("  • Videos with clear speech work best")
    print("  • Non-English videos: Change MODEL_SIZE to 'large' in code")
    
    print("\n" + "="*70)

if __name__ == '__main__':
    # Start both transcription threads
    start_dual_transcription()
    
    # Run Flask app
    try:
        print("\n🌐 Starting web server at http://localhost:5000")
        print("   Press Ctrl+C to stop\n")
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True)
    except Exception as e:
        print(f"❌ Flask app failed to start: {e}")
        print("\n💡 Common solutions:")
        print("   1. Port 5000 is busy: Run 'lsof -i :5000' and kill processes")
        print("   2. Run the kill script: ./kill-all-flasks.sh")
        print("   3. Try a different port: Change 'port=5000' in the code")