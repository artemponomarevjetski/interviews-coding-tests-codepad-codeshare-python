import sounddevice as sd
import numpy as np
import time
import sys
import os

print("=" * 60)
print("🎭 AVATAR AUDIO DIAGNOSTIC TOOL")
print("=" * 60)

# Step 1: Check if avatar process is running
print("\n🔍 Step 1: Avatar Process Status")
print("-" * 40)
import subprocess
result = subprocess.run(['pgrep', '-f', 'python.*avatar'], capture_output=True, text=True)
if result.stdout:
    print(f"✅ Avatar is running (PID: {result.stdout.strip()})")
else:
    print("❌ Avatar is NOT running")

# Step 2: List all audio input devices
print("\n📋 Step 2: Available Audio Input Devices")
print("-" * 40)
devices = sd.query_devices()
blackhole_id = None
for i, dev in enumerate(devices):
    if dev['max_input_channels'] > 0:
        print(f"   [{i}] {dev['name']} (inputs: {dev['max_input_channels']})")
        if 'blackhole' in dev['name'].lower():
            blackhole_id = i
            print(f"      👆 THIS IS BLACKHOLE - ID: {i}")

if blackhole_id is None:
    print("\n❌ ERROR: BlackHole not found!")
    sys.exit(1)

# Step 3: Test BlackHole audio capture
print("\n🎧 Step 3: Testing BlackHole Audio Capture")
print("-" * 40)
print("🔊 PLAY TEAMS AUDIO NOW! (speak or have someone speak)")
print("Listening for 15 seconds...")

def callback(indata, frames, time, status):
    volume = np.linalg.norm(indata) * 10
    if volume > 0.1:
        print(f"🔊 AUDIO DETECTED! Level: {volume:.2f}", end='\r')
        global detected
        detected = True

detected = False
try:
    with sd.InputStream(device=blackhole_id, channels=1, callback=callback, samplerate=48000):
        time.sleep(15)
    print("\n")
    if detected:
        print("✅ SUCCESS: BlackHole IS receiving audio!")
        print("   The avatar SHOULD be able to hear Teams.")
    else:
        print("❌ FAILED: BlackHole is NOT receiving any audio")
        print("   Check your Multi-Output Device in Audio MIDI Setup")
except Exception as e:
    print(f"\n❌ ERROR testing BlackHole: {e}")

# Step 4: Check avatar's delegator log for Teams entries
print("\n📝 Step 4: Recent Avatar Logs (last 20 lines)")
print("-" * 40)
log_file = "logs/delegator.log"
if os.path.exists(log_file):
    with open(log_file, 'r') as f:
        lines = f.readlines()[-20:]
        for line in lines:
            if 'error' in line.lower() or 'exception' in line.lower():
                print(f"⚠️  {line.strip()}")
            elif 'teams heard' in line.lower():
                print(f"✅ {line.strip()}")
            elif 'comment' in line.lower():
                print(f"💬 {line.strip()}")
            else:
                print(f"   {line.strip()}")
else:
    print("   No delegator.log found")

# Step 5: Check flask_app.log for errors
print("\n🔍 Step 5: Flask App Errors (last 10 lines)")
print("-" * 40)
log_file = "logs/flask_app.log"
if os.path.exists(log_file):
    with open(log_file, 'r') as f:
        lines = f.readlines()[-10:]
        for line in lines:
            if 'error' in line.lower() or 'exception' in line.lower():
                print(f"⚠️  {line.strip()}")
            else:
                print(f"   {line.strip()}")
else:
    print("   No flask_app.log found")

print("\n" + "=" * 60)
print("📋 QUICK CHECKLIST:")
print("1. Audio MIDI Setup: Multi-Output Device has External Headphones + BlackHole CHECKED")
print("2. Teams Settings: Speaker = External Headphones, Microphone = External Microphone")
print("3. In web interface: Did you click 'Start Teams Listening'?")
print("4. Is Teams actually playing audio? (can you hear it?)")
print("=" * 60)
