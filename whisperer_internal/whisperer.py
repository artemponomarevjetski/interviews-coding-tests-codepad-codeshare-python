import os
from datetime import datetime, timedelta
from collections import deque
import logging
from flask import Flask, render_template_string
import sounddevice as sd
import numpy as np
import whisper

# Initialize Flask app
app = Flask(__name__)

# Audio configuration optimized for MacBook Pro
sampling_rate = 16000
chunk_size = 4096  # Larger buffer to prevent overflow
silence_threshold = 0.02
min_audio_length = 1.0  # Minimum seconds of audio to process

# Load Whisper model
model = whisper.load_model("base")

# Configure logging
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

transcriptions = deque(maxlen=20)

def get_microphone():
    """Find the built-in microphone"""
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        if 'MacBook Pro Microphone' in dev['name'] and dev['max_input_channels'] > 0:
            return i
    return None

def transcribe_audio():
    try:
        device_id = get_microphone()
        if device_id is None:
            raise RuntimeError("MacBook microphone not found!")
            
        logging.info(f"Using microphone: {sd.query_devices()[device_id]['name']}")

        with sd.InputStream(
            samplerate=sampling_rate,
            channels=1,
            dtype='float32',
            device=device_id,
            blocksize=chunk_size,
            latency='high'
        ) as stream:
            logging.info("Audio stream active - speak naturally...")
            
            audio_buffer = np.array([], dtype=np.float32)
            last_active = datetime.now()
            
            while True:
                audio_chunk, overflowed = stream.read(chunk_size)
                if overflowed:
                    logging.debug("Buffer overflow occurred")
                
                audio_chunk = audio_chunk.squeeze()
                amplitude = np.max(np.abs(audio_chunk))
                
                # Buffer audio when speaking
                if amplitude > silence_threshold:
                    audio_buffer = np.concatenate((audio_buffer, audio_chunk))
                    last_active = datetime.now()
                elif len(audio_buffer) > 0:
                    # Process when silence detected after speech
                    silence_duration = (datetime.now() - last_active).total_seconds()
                    if silence_duration > 0.5 and len(audio_buffer) > sampling_rate * min_audio_length:
                        try:
                            # Normalize volume
                            audio_buffer = audio_buffer * (1.0 / np.max(np.abs(audio_buffer)))
                            result = model.transcribe(audio_buffer, fp16=False, language='en')
                            text = result["text"].strip().lower()
                            
                            if text:
                                entry = {
                                    'time': datetime.now(),
                                    'text': text
                                }
                                transcriptions.append(entry)
                                print(f"\n>> TRANSCRIPTION: {text} <<\n")
                                logging.info(f"TRANSCRIPTION: {text}")
                        except Exception as e:
                            logging.error(f"Transcription error: {str(e)}")
                        finally:
                            audio_buffer = np.array([], dtype=np.float32)
                
    except Exception as e:
        logging.error(f"Fatal audio error: {str(e)}", exc_info=True)
        raise

@app.route('/')
def index():
    one_minute_ago = datetime.now() - timedelta(minutes=1)
    recent_transcriptions = [
        f"{entry['time'].strftime('%H:%M:%S')} - {entry['text']}"
        for entry in transcriptions
        if entry['time'] > one_minute_ago
    ]
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Live Number Transcription</title>
        <meta http-equiv="refresh" content="2">
        <style>
            body { font-family: -apple-system, sans-serif; padding: 20px; }
            #transcriptions div { 
                padding: 10px; 
                border-bottom: 1px solid #e1e1e1;
                font-size: 1.2em;
            }
            h1 { color: #333; }
        </style>
    </head>
    <body>
        <h1>Live Number Transcription Test</h1>
        <div id="transcriptions">
            {% for text in recent_transcriptions %}
                <div>{{ text }}</div>
            {% else %}
                <div>Speak numbers like "one two three" to test...</div>
            {% endfor %}
        </div>
    </body>
    </html>
    """, recent_transcriptions=recent_transcriptions or [])

if __name__ == '__main__':
    from threading import Thread
    
    print("\n=== NUMBER TRANSCRIPTION TEST ===")
    print("Please speak clearly: 'one two three four five'")
    print("We should see these exact numbers appear below\n")
    
    audio_thread = Thread(target=transcribe_audio, daemon=True)
    audio_thread.start()
    
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
