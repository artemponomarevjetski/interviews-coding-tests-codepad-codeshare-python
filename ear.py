import sounddevice as sd
import numpy as np
import whisper
import queue
import soundfile as sf
from datetime import datetime
import os
import sys
import subprocess
import time
from pprint import pprint

# Configuration
SAMPLE_RATE = 16000  # Whisper's preferred sample rate
LOG_DIR = "log"
LOG_FILE = os.path.join(LOG_DIR, "conversation_log.txt")
MODEL_SIZE = "small"  # More accurate than base but still reasonably fast
BUFFER_SECONDS = 5    # Process chunks of 5 seconds
DEBUG_MODE = True     # Enable additional logging and audio saving
TEMP_DIR = "temp"     # Directory for temporary audio files

class AudioTranscriber:
    def __init__(self):
        # Create necessary directories
        os.makedirs(TEMP_DIR, exist_ok=True)
        os.makedirs(LOG_DIR, exist_ok=True)
        
        self.audio_queue = queue.Queue()
        self.model = whisper.load_model(MODEL_SIZE)
        self.input_device, self.channels = self.setup_audio_device()
        self.last_audio_peak = 0
        
    def setup_audio_device(self):
        """Configure audio input device with comprehensive checks"""
        print("\n=== Audio Device Setup ===")
        devices = sd.query_devices()
        pprint([f"{i}: {d['name']} (in:{d['max_input_channels']}, out:{d['max_output_channels']})" 
               for i, d in enumerate(devices)])
        
        input_device = sd.default.device[0]
        channels = 1  # Default to mono
        
        # Try to find BlackHole or alternative
        for i, device in enumerate(devices):
            if "blackhole" in device['name'].lower():
                if device['max_input_channels'] >= 2:
                    input_device = i
                    channels = 2
                    print(f"\n✅ Selected BlackHole device: {device['name']} (Stereo)")
                    break
        
        if channels == 1:
            print(f"\nℹ️ Using default input device: {devices[input_device]['name']} (Mono)")
        
        # Configure audio routing on macOS
        if sys.platform == 'darwin':
            self.configure_macos_audio_routing()
        
        return input_device, channels
    
    def configure_macos_audio_routing(self):
        """Configure macOS audio routing programmatically"""
        try:
            print("\n=== Configuring Audio Routing ===")
            
            # Force BlackHole as input
            subprocess.run(["switchaudio-osx", "-s", "BlackHole 2ch", "-t", "input"], check=True)
            print("✅ Forced BlackHole as input device")
            
            # Create multi-output device if needed
            devices = subprocess.run(["switchaudio-osx", "-a"], capture_output=True, text=True).stdout
            if "Multi-Output" not in devices:
                subprocess.run([
                    "osascript", "-e",
                    'tell application "Audio MIDI Setup" to activate\n'
                    'tell application "System Events" to tell process "Audio MIDI Setup"\n'
                    'click menu item "Create Multi-Output Device" of menu "File" of menu bar 1\n'
                    'delay 1\n'
                    'set value of checkbox "BlackHole 2ch" of window 1 to true\n'
                    'set value of checkbox "Built-in Output" of window 1 to true\n'
                    'set current name of window 1 to "Multi-Output"\n'
                    'end tell'
                ], check=True)
                print("✅ Created Multi-Output device")
            
            # Set multi-output as system output
            subprocess.run(["switchaudio-osx", "-s", "Multi-Output", "-t", "output"], check=True)
            print("✅ Set Multi-Output as system output")
            
            # Verify routing
            print("\nCurrent Routing:")
            input_dev = subprocess.run(
                ["switchaudio-osx", "-c", "-t", "input"],
                capture_output=True, text=True
            ).stdout.strip()
            print(f"Input: {input_dev}")
            
            output_dev = subprocess.run(
                ["switchaudio-osx", "-c", "-t", "output"],
                capture_output=True, text=True
            ).stdout.strip()
            print(f"Output: {output_dev}")
            
        except Exception as e:
            print(f"⚠️ Audio routing error: {e}")
            print("Please configure manually in Audio MIDI Setup")

    def audio_callback(self, indata, frames, time, status):
        """Callback for each audio block with volume monitoring"""
        if status:
            print(f"Audio status: {status}", file=sys.stderr)
        
        current_peak = np.max(np.abs(indata))
        self.last_audio_peak = current_peak
        
        if DEBUG_MODE and current_peak > 0.01:  # Only log when there's sound
            print(f"Audio level: {current_peak:.4f}", end='\r')
        
        self.audio_queue.put(indata.copy())

    def transcribe_audio(self, audio_data):
        """Transcribe audio using Whisper with enhanced debugging"""
        try:
            # Convert stereo to mono if needed
            if audio_data.ndim > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            # Audio quality checks
            peak = np.max(np.abs(audio_data))
            rms = np.sqrt(np.mean(audio_data**2))
            
            print(f"\nAudio Stats - Peak: {peak:.4f}, RMS: {rms:.4f}")
            
            if peak < 0.01:  # Very quiet audio
                print("⚠️ Audio too quiet - applying 20x amplification")
                audio_data = audio_data * 20
                peak = np.max(np.abs(audio_data))
            
            # Save the audio for debugging
            if DEBUG_MODE:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                debug_file = os.path.join(TEMP_DIR, f"debug_audio_{timestamp}.wav")
                sf.write(debug_file, audio_data, SAMPLE_RATE)
                print(f"Saved audio to {debug_file}")
            
            # Transcribe with progress updates
            result = self.model.transcribe(
                audio_data.astype(np.float32),
                language='en',
                fp16=False,  # FP32 is better for CPU
                verbose=True if DEBUG_MODE else None
            )
            
            return result["text"].strip()
        except Exception as e:
            print(f"❌ Transcription error: {str(e)}")
            return "[Transcription failed]"

    def run(self):
        """Main execution loop with enhanced monitoring"""
        print(f"\n=== Starting Transcription (model: {MODEL_SIZE}) ===")
        print(f"Logging to: {os.path.abspath(LOG_FILE)}")
        print("Press Ctrl+C to stop\n")
        
        # Verify audio pipeline
        self.verify_audio_pipeline()
        
        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=self.channels,
                dtype='float32',
                device=self.input_device,
                callback=self.audio_callback
            ):
                self.process_audio_chunks()
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping transcription...")
        except Exception as e:
            print(f"❌ Fatal error: {e}")
        finally:
            print("Transcription stopped.")

    def verify_audio_pipeline(self):
        """Verify the audio pipeline is working before starting"""
        if not DEBUG_MODE:
            return
            
        print("\n🔊 Verifying audio pipeline...")
        try:
            test_file = os.path.join(TEMP_DIR, "pipeline_test.wav")
            subprocess.run(["sox", "-d", "-t", "coreaudio", "BlackHole 2ch", test_file, "trim", "0", "3"], timeout=5)
            
            if os.path.exists(test_file):
                data, _ = sf.read(test_file)
                peak = np.max(np.abs(data))
                print(f"Test recording - Peak: {peak:.4f}")
                
                if peak < 0.001:
                    print("❌ No audio detected in test recording")
                    print("Please check:")
                    print("1. Audio MIDI Setup has Multi-Output device with BlackHole+Built-in Output")
                    print("2. System Preferences > Sound has Multi-Output selected")
                    print("3. System Preferences > Security has microphone access granted")
                else:
                    print("✅ Audio pipeline verified!")
        except Exception as e:
            print(f"⚠️ Pipeline verification failed: {e}")

    def process_audio_chunks(self):
        """Process accumulated audio chunks with activity monitoring"""
        buffer = []
        last_activity_check = time.time()
        
        print("Listening... Speak now (waiting for audio input)")
        
        while True:
            try:
                # Check audio activity periodically
                if time.time() - last_activity_check > 2:
                    if self.last_audio_peak < 0.001:
                        print("🔇 No audio detected - check your input source")
                    last_activity_check = time.time()
                
                audio_chunk = self.audio_queue.get()
                buffer.append(audio_chunk)
                
                # Process when we have enough audio
                if len(buffer) >= (SAMPLE_RATE * BUFFER_SECONDS) // len(audio_chunk):
                    audio_data = np.concatenate(buffer)
                    buffer = []  # Reset buffer
                    
                    text = self.transcribe_audio(audio_data)
                    if text and text != "[Transcription failed]":
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        log_entry = f"[{timestamp}] {text}\n"
                        print(f"\nTranscription: {text}")
                        with open(LOG_FILE, "a", encoding='utf-8') as f:
                            f.write(log_entry)
                            
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"⚠️ Processing error: {e}")

if __name__ == "__main__":
    # Check for required tools
    if sys.platform == 'darwin':
        print("=== System Requirements Check ===")
        try:
            subprocess.run(["which", "BlackHole"], check=True)
            print("✅ BlackHole is installed")
        except subprocess.CalledProcessError:
            print("\nℹ️ For system audio capture, install BlackHole:")
            print("brew install blackhole-2ch")
            print("Then configure it in Audio MIDI Setup\n")
        
        try:
            subprocess.run(["which", "switchaudio-osx"], check=True)
            print("✅ switchaudio-osx is installed")
        except subprocess.CalledProcessError:
            print("ℹ️ For audio routing control, install:")
            print("brew install switchaudio-osx")
        
        try:
            subprocess.run(["which", "sox"], check=True)
            print("✅ sox is installed")
        except subprocess.CalledProcessError:
            print("ℹ️ For audio verification, install:")
            print("brew install sox")
        
        # Check microphone permissions
        print("\n🔊 Checking microphone permissions...")
        try:
            subprocess.run([
                "osascript", "-e",
                'tell application "System Preferences" to activate\n'
                'tell application "System Events" to tell process "System Preferences"\n'
                'click menu item "Microphone" of menu "View" of menu bar 1\n'
                'end tell\n'
                'delay 2'
            ], check=True)
            print("Please ensure your terminal app has microphone access")
            input("Press Enter after verifying permissions...")
        except:
            print("Couldn't open permissions automatically - check manually in:")
            print("System Preferences > Security & Privacy > Microphone")
    
    # Run the transcriber
    transcriber = AudioTranscriber()
    transcriber.run()
