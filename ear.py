import sounddevice as sd
import numpy as np
import whisper
import queue
import soundfile as sf
from datetime import datetime
import os
import sys
import subprocess

# Configuration
SAMPLE_RATE = 16000  # Whisper's preferred sample rate
CHANNELS = 1         # Mono audio
DTYPE = 'float32'    # Better compatibility with Whisper
BUFFER_SECONDS = 30  # Process chunks of 30 seconds
LOG_FILE = "conversation_log.txt"
MODEL_SIZE = "base"  # Can be "tiny", "base", "small", "medium", "large"

# For macOS system audio capture
BLACKHOLE_DEVICE = "BlackHole"  # Needs to be installed

class AudioTranscriber:
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.model = whisper.load_model(MODEL_SIZE)
        self.setup_audio_device()
        
    def setup_audio_device(self):
        """Configure audio input device, prioritizing BlackHole on macOS"""
        devices = sd.query_devices()
        input_device = None
        
        # Try to find BlackHole for system audio capture
        for i, device in enumerate(devices):
            if BLACKHOLE_DEVICE in device['name'] and device['max_input_channels'] > 0:
                input_device = i
                print(f"Using audio device: {device['name']}")
                break
        
        if input_device is None:
            print("BlackHole not found, using default input device")
            input_device = sd.default.device[0]
        
        return input_device

    def audio_callback(self, indata, frames, time, status):
        """Callback for each audio block"""
        if status:
            print(f"Audio status: {status}", file=sys.stderr)
        self.audio_queue.put(indata.copy())

    def transcribe_audio(self, audio_data):
        """Transcribe audio using Whisper"""
        try:
            # Normalize audio to [-1, 1] range if needed
            if np.max(np.abs(audio_data)) > 1:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            # Whisper expects float32
            audio_data = audio_data.astype(np.float32)
            
            # Transcribe directly without temp file
            result = self.model.transcribe(audio_data.flatten(), 
                                         sample_rate=SAMPLE_RATE)
            return result["text"]
        except Exception as e:
            print(f"Transcription error: {e}")
            return "[Transcription failed]"

    def process_audio_chunks(self):
        """Process accumulated audio chunks"""
        buffer = []
        chunk_size = None
        
        while True:
            audio_chunk = self.audio_queue.get()
            
            if chunk_size is None:
                chunk_size = len(audio_chunk)
            
            buffer.append(audio_chunk)
            
            # Process when we have enough audio
            if len(buffer) >= BUFFER_SECONDS * (SAMPLE_RATE / chunk_size):
                audio_data = np.concatenate(buffer)
                buffer = []
                
                text = self.transcribe_audio(audio_data)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_entry = f"[{timestamp}] {text}\n"
                
                # Output and log
                print(log_entry, end='')
                with open(LOG_FILE, "a", encoding='utf-8') as f:
                    f.write(log_entry)

    def run(self):
        """Main execution loop"""
        input_device = self.setup_audio_device()
        
        print(f"Starting transcription (model: {MODEL_SIZE})... Press Ctrl+C to stop.")
        print(f"Logging to: {os.path.abspath(LOG_FILE)}")
        
        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                device=input_device,
                callback=self.audio_callback
            ):
                self.process_audio_chunks()
                
        except KeyboardInterrupt:
            print("\nStopping transcription...")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            print("Transcription stopped.")

if __name__ == "__main__":
    # Check for BlackHole installation on macOS
    if sys.platform == 'darwin':
        try:
            subprocess.run(["which", "BlackHole"], check=True)
        except subprocess.CalledProcessError:
            print("\nWARNING: BlackHole not found. System audio capture won't work.")
            print("Install it with: brew install blackhole-2ch")
            print("Then configure it in Audio MIDI Setup\n")
    
    transcriber = AudioTranscriber()
    transcriber.run()
