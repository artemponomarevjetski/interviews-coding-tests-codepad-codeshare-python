import sounddevice as sd
import numpy as np

# List available devices
print("Available input devices:")
for i, dev in enumerate(sd.query_devices()):
    if dev['max_input_channels'] > 0:
        print(f"{i}: {dev['name']}")

# Use built-in mic (typically device 1 on Mac)
device_id = 1  
duration = 5  # seconds

print(f"\nTesting device {device_id} for {duration} seconds...")
print("SPEAK NOW - You should see amplitude > 0.1")
recording = sd.rec(int(duration * 16000), 
                  samplerate=16000, 
                  channels=1, 
                  device=device_id)
sd.wait()

max_amp = np.max(np.abs(recording))
print(f"\nMax amplitude recorded: {max_amp:.4f}")
print("(Values > 0.1 mean mic is working)")
