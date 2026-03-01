#!/usr/bin/env python3
"""
🎧 BlackHole Audio Transcriber - Fixed version with overflow handling
"""

import pyaudio
import speech_recognition as sr
from datetime import datetime
import time

# Find BlackHole
p = pyaudio.PyAudio()
blackhole = None
for i in range(p.get_device_count()):
    if "BlackHole" in p.get_device_info_by_index(i)['name']:
        blackhole = i
        print(f"✅ Using BlackHole (index {i})")
        break

if blackhole is None:
    print("❌ BlackHole not found! Install from: https://github.com/ExistentialAudio/BlackHole")
    exit()

# Audio settings - larger buffer and overflow handling
CHUNK = 4096  # Increased buffer size
RATE = 44100
stream = p.open(format=pyaudio.paInt16, channels=2, rate=RATE,
                input=True, input_device_index=blackhole,
                frames_per_buffer=CHUNK)

r = sr.Recognizer()
print("\n🎧 Listening to BlackHole... Press Ctrl+C to stop\n")

try:
    while True:
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio = sr.AudioData(data, RATE, 2)

            try:
                text = r.recognize_google(audio)
                if text:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] {text}")
            except sr.UnknownValueError:
                pass  # No speech detected
            except sr.RequestError as e:
                print(f"⚠️  API Error: {e}")

        except OSError as e:
            # Handle overflow by continuing
            time.sleep(0.01)
            continue

except KeyboardInterrupt:
    print("\n\n✅ Stopped")
finally:
    stream.close()
    p.terminate()
