import pyaudio
import numpy as np
import time

p = pyaudio.PyAudio()
blackhole = None
for i in range(p.get_device_count()):
    if "BlackHole" in p.get_device_info_by_index(i)['name']:
        blackhole = i
        print(f"✅ Found BlackHole at index {i}")

CHUNK = 4096
RATE = 44100
stream = p.open(format=pyaudio.paInt16, channels=2, rate=RATE,
                input=True, input_device_index=blackhole,
                frames_per_buffer=CHUNK)

print("\n🎧 Monitoring audio levels... PLAY YOUR AUDIOBOOK NOW")
print("Volume bars will appear if audio reaches BlackHole:\n")

try:
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        audio_data = np.frombuffer(data, dtype=np.int16)
        volume = np.abs(audio_data).mean()
        
        # Show volume level
        bars = int(min(volume / 100, 50))
        print(f"\rVolume: {'█' * bars}{'░' * (50 - bars)} {volume:.0f}", end='')
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n\n✅ Test stopped")
finally:
    stream.close()
    p.terminate()
