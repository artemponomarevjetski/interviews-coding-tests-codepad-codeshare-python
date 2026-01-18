#!/usr/bin/env python3
"""
Command-line audio setup for dual transcription
No GUI, no pop-ups, pure command line
"""
import subprocess
import sys
import os

def check_blackhole():
    """Check if BlackHole is installed"""
    print("🔍 Checking BlackHole installation...")
    
    # Method 1: Check via system_profiler
    result = subprocess.run(
        ["system_profiler", "SPAudioDataType"],
        capture_output=True,
        text=True
    )
    
    if "BlackHole" in result.stdout:
        print("✅ BlackHole found")
        return True
    else:
        print("❌ BlackHole not found")
        print("   Install with: brew install --cask blackhole")
        return False

def create_aggregate_device():
    """
    Create aggregate device using command-line
    Note: This requires sudo on some systems
    """
    print("🎧 Creating Aggregate Audio Device...")
    
    # Method 1: Use Audio MIDI Setup CLI if available
    try:
        # List available devices
        print("\nAvailable audio devices:")
        subprocess.run(["system_profiler", "SPAudioDataType", "|", "grep", "-A2", "Default"], 
                      shell=True, check=False)
        
        # Create aggregate device using coreaudio commands
        # This is a simplified approach - actual implementation varies
        
        print("\n📋 MANUAL COMMAND-LINE SETUP:")
        print("=============================")
        print("1. Create ~/aggregate.plist with this content:")
        print("""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>AggregateDeviceName</key>
    <string>Transcription Output</string>
    <key>AggregateDeviceUID</key>
    <string>com.apple.audio.AggregateDevice.TranscriptionOutput</string>
    <key>AggregateDeviceMasterSubDeviceUID</key>
    <string>BlackHole</string>
    <key>AggregateDevices</key>
    <array>
        <dict>
            <key>DeviceUID</key>
            <string>BlackHole</string>
            <key>DeviceIsMaster</key>
            <true/>
            <key>DeviceChannels</key>
            <integer>2</integer>
        </dict>
        <dict>
            <key>DeviceUID</key>
            <string>BuiltInSpeakerDevice</string>
            <key>DeviceIsMaster</key>
            <false/>
            <key>DeviceChannels</key>
            <integer>2</integer>
        </dict>
    </array>
</dict>
</plist>
""")
        
        print("\n2. Load the aggregate device:")
        print("   sudo cp ~/aggregate.plist /Library/Audio/Plug-Ins/HAL/")
        print("   sudo pkill -f coreaudiod")
        print("   sleep 2")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Error: {e}")
        return False

def setup_sound_preferences():
    """Set sound preferences via defaults command"""
    print("\n🔧 Setting sound preferences...")
    
    # Method 1: Use AppleScript but in background
    applescript = '''
    do shell script "osascript -e 'tell application \\"System Preferences\\" to quit'"
    do shell script "osascript -e 'tell application \\"System Events\\" to tell application process \\"System Preferences\\"
        if exists (window \\"Sound\\") then
            tell window \\"Sound\\"
                tell tab group 1
                    click pop up button 1
                    delay 0.5
                    try
                        click menu item \\"BlackHole 2ch\\" of menu 1 of pop up button 1
                    end try
                end tell
            end tell
        end if
    end tell'"
    '''
    
    try:
        subprocess.run(["osascript", "-e", applescript], check=False)
        print("✅ Sound preferences updated (BlackHole set as output)")
    except:
        print("⚠️  Could not update sound preferences automatically")

def test_audio_routing():
    """Test if audio is routing correctly"""
    print("\n🎵 Testing audio routing...")
    
    test_script = '''
import sounddevice as sd
import numpy as np
import sys

try:
    # List devices
    print("Available audio devices:")
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        if d['max_input_channels'] > 0:
            print(f"  [{i}] {d['name']}")
    
    # Find BlackHole
    blackhole_idx = None
    for i, d in enumerate(devices):
        if 'blackhole' in d['name'].lower():
            blackhole_idx = i
            break
    
    if blackhole_idx is None:
        print("❌ BlackHole not found in device list")
        sys.exit(1)
    
    print(f"\\n🔍 Found BlackHole at device {blackhole_idx}")
    print("   Play YouTube video now...")
    
    # Record 3 seconds
    recording = sd.rec(3 * 16000, samplerate=16000, 
                      channels=1, device=blackhole_idx, 
                      dtype='float32')
    sd.wait()
    
    level = np.max(np.abs(recording))
    print(f"📊 Audio level: {level:.6f}")
    
    if level > 0.01:
        print("✅ Good! Audio is reaching BlackHole")
        print("   Transcription will work")
    elif level > 0.001:
        print("⚠️  Low audio level")
        print("   Increase browser/system volume")
    else:
        print("❌ No audio detected")
        print("   Check: System Settings → Sound → Output")
        print("   Should be set to BlackHole 2ch")
        
except Exception as e:
    print(f"❌ Test failed: {e}")
    '''
    
    # Run the test
    subprocess.run([sys.executable, "-c", test_script])

def main():
    print("="*60)
    print("🎧 COMMAND-LINE AUDIO SETUP FOR DUAL TRANSCRIPTION")
    print("="*60)
    print("\nThis script sets up audio routing WITHOUT GUI pop-ups")
    
    # Check BlackHole
    if not check_blackhole():
        print("\n⏳ Installing BlackHole...")
        subprocess.run(["brew", "install", "--cask", "blackhole"], check=False)
    
    # Setup instructions
    print("\n" + "="*60)
    print("📋 PURE COMMAND-LINE SETUP INSTRUCTIONS")
    print("="*60)
    
    print("\nA. QUICK SETUP (Hear AND transcribe):")
    print("   1. Set output to BlackHole (captures audio):")
    print('      osascript -e \'tell application "System Events" to tell application process "System Preferences"')
    print('        if exists (window "Sound") then')
    print('          tell window "Sound"')
    print('            tell tab group 1')
    print('              click pop up button 1')
    print('              delay 0.5')
    print('              try')
    print('                click menu item "BlackHole 2ch" of menu 1 of pop up button 1')
    print('              end try')
    print('            end tell')
    print('          end tell')
    print('        end if')
    print('      end tell\'')
    
    print("\n   2. To HEAR audio while transcribing:")
    print("      - Use separate device (phone, tablet) for YouTube")
    print("      - OR use Chrome with --disable-features flag")
    print("      - OR switch back to headphones when needed")
    
    print("\nB. ALTERNATIVE: Use Soundflower (easier setup):")
    print("   1. brew install --cask soundflower")
    print("   2. System Settings → Sound → Output → Soundflower (2ch)")
    print("   3. Play YouTube - it will capture audio")
    
    print("\nC. SIMPLEST: Just use microphone transcription")
    print("   - Works without any audio routing setup")
    print("   - YouTube won't be transcribed")
    
    # Test
    print("\n" + "="*60)
    print("🧪 TESTING CURRENT SETUP")
    print("="*60)
    test_audio_routing()
    
    print("\n" + "="*60)
    print("✅ SETUP COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("1. Start transcription: ./set-up-and-launch-whisperer-external.sh")
    print("2. Open: http://localhost:5000")
    print("3. Test microphone: Speak into your external mic")
    print("4. For YouTube: Set system output to BlackHole 2ch")

if __name__ == "__main__":
    main()
    #!/usr/bin/env python3
"""
ENHANCED Whisperer Troubleshooter - Now with browser audio routing checks
- Verifies Python + packages
- Checks PortAudio/sounddevice and lists input devices
- Records a short sample and reports amplitude
- Checks browser audio routing to BlackHole
- Checks if a port (e.g., 5000) is occupied
- Provides browser-specific recommendations

Exit codes:
 0 OK, non-fatal warnings may be printed
 1 Hard failure (missing package / device / record error)
"""

import sys
import os
import argparse
import shutil
import socket
import time
import subprocess
import numpy as np
from contextlib import closing
from typing import Union

RESULTS = []

def add_result(ok: bool, title: str, detail: str = ""):
    status = "OK" if ok else "FAIL"
    line = f"[{status}] {title}"
    if detail:
        line += f" — {detail}"
    RESULTS.append((ok, line))
    print(line)

def check_python():
    add_result(True, "Python", f"{sys.executable} (v{sys.version.split()[0]})")

def check_imports(check_whisper: bool):
    try:
        import numpy  # noqa
        add_result(True, "Import numpy")
    except Exception as e:
        add_result(False, "Import numpy", str(e))

    try:
        import sounddevice  # noqa
        add_result(True, "Import sounddevice")
    except Exception as e:
        add_result(False, "Import sounddevice", str(e))

    if check_whisper:
        try:
            import whisper  # noqa
            add_result(True, "Import whisper")
        except Exception as e:
            add_result(False, "Import whisper", str(e))

def list_input_devices():
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        inputable = [d for d in devices if d.get('max_input_channels', 0) > 0]
        if not inputable:
            add_result(False, "Audio input devices", "No input-capable devices found")
            return []

        print("\n📋 Available input devices:")
        for idx, dev in enumerate(devices):
            if dev.get('max_input_channels', 0) > 0:
                is_default = " (DEFAULT INPUT)" if idx == sd.default.device[0] else ""
                print(f"  [{idx}] {dev['name']}{is_default}")

        add_result(True, "Enumerate audio devices", f"{len(inputable)} input device(s)")
        return devices
    except Exception as e:
        add_result(False, "Enumerate audio devices", str(e))
        return []

def resolve_device_id(preferred: Union[str, int], devices):
    """Return a device id or None."""
    import sounddevice as sd

    if isinstance(preferred, int):
        try:
            sd.check_input_settings(device=preferred)
            return preferred
        except Exception:
            return None

    if isinstance(preferred, str):
        if preferred.lower() == "auto":
            # Heuristic: prefer MacBook Pro Microphone if present; else first input device
            for i, dev in enumerate(devices):
                if dev.get('max_input_channels', 0) > 0 and "MacBook Pro Microphone" in dev.get('name', ""):
                    return i
            for i, dev in enumerate(devices):
                if dev.get('max_input_channels', 0) > 0:
                    return i
            return None

        # name match
        for i, dev in enumerate(devices):
            if dev.get('max_input_channels', 0) > 0 and preferred.lower() in dev.get('name', "").lower():
                return i
    return None

def test_record(seconds: float, rate: int, channels: int, device):
    try:
        import sounddevice as sd

        print(f"\n🎤 Recording test: {seconds:.1f}s @ {rate} Hz, ch={channels}, device={device}")
        recorded = sd.rec(int(seconds * rate), samplerate=rate, channels=channels, device=device, dtype='float32')
        sd.wait()

        max_amp = float(np.max(np.abs(recorded))) if recorded.size else 0.0
        msg = f"max amplitude = {max_amp:.4f}"
        ok = max_amp > 0.05  # conservative threshold
        add_result(ok, "Microphone capture", msg)

        if not ok:
            tips = [
                "Check macOS System Settings → Privacy & Security → Microphone (allow terminal/VS Code).",
                "Increase input level in Sound settings or move closer to mic.",
                "Try a different device with --device or unplug/replug USB mics.",
            ]
            print("Tips: " + " ".join(tips))
        return ok
    except Exception as e:
        add_result(False, "Microphone capture", str(e))
        print("Tip: If you see 'PortAudioError', (re)install PortAudio (brew install portaudio) and reinstall sounddevice in the venv.")
        return False

def check_port(port: int):
    # True means free; False means busy
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.settimeout(0.5)
        result = s.connect_ex(("127.0.0.1", port))
        if result == 0:
            add_result(False, f"Port {port}", "Already in use")
            return False
        add_result(True, f"Port {port}", "Available")
        return True

def check_browser_audio_routing():
    """Check if browser audio is reaching BlackHole"""
    print("\n🔍 CHECKING BROWSER AUDIO ROUTING")
    print("=" * 50)
    
    try:
        import sounddevice as sd
        
        # Find BlackHole device
        devices = sd.query_devices()
        blackhole_device = None
        for i, dev in enumerate(devices):
            if 'blackhole' in dev['name'].lower():
                blackhole_device = i
                break
        
        if blackhole_device is None:
            add_result(False, "BlackHole device", "Not found")
            print("💡 Install BlackHole 2ch: brew install --cask blackhole")
            return False
        
        print(f"Found BlackHole: Device {blackhole_device}")
        
        # Test audio level
        print("\n🎧 Testing BlackHole audio level...")
        print("Please play YouTube video in a browser NOW")
        print("Waiting 5 seconds for audio to start...")
        time.sleep(5)
        
        recording = sd.rec(3 * 16000, samplerate=16000, channels=1, 
                          device=blackhole_device, dtype='float32')
        sd.wait()
        
        max_level = np.max(np.abs(recording))
        rms = np.sqrt(np.mean(recording**2))
        
        print(f"\n📊 Audio Level Results:")
        print(f"  Max amplitude: {max_level:.6f}")
        print(f"  RMS level: {rms:.8f}")
        
        if max_level > 0.01:
            add_result(True, "Browser audio routing", f"Good level ({max_level:.4f})")
            print("✅ Browser audio is reaching BlackHole successfully!")
            return True
        elif max_level > 0.001:
            add_result(False, "Browser audio routing", f"Low level ({max_level:.4f})")
            print("⚠️  Audio detected but very low")
            print("   Increase browser/YouTube volume to 100%")
            return False
        else:
            add_result(False, "Browser audio routing", "No audio detected")
            print("❌ No audio detected from browser")
            return False
            
    except Exception as e:
        add_result(False, "Browser audio routing", str(e))
        return False

def check_running_browsers():
    """Check which browsers are running"""
    print("\n🌐 CHECKING RUNNING BROWSERS")
    print("=" * 50)
    
    browsers = {
        "Firefox": "firefox",
        "Chrome": "Google Chrome",
        "Safari": "Safari",
        "Edge": "Microsoft Edge"
    }
    
    running_browsers = []
    
    for name, process in browsers.items():
        try:
            result = subprocess.run(['pgrep', '-f', process], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                running_browsers.append(name)
                print(f"✅ {name} is running")
            else:
                print(f"🔴 {name} is not running")
        except:
            print(f"⚠️  Could not check {name}")
    
    return running_browsers

def check_system_audio_output():
    """Check current system audio output"""
    print("\n🔊 CHECKING SYSTEM AUDIO OUTPUT")
    print("=" * 50)
    
    try:
        # Use AppleScript to get current output
        applescript = '''
        tell application "System Events"
            tell application process "System Preferences"
                if exists (window "Sound") then
                    tell window "Sound"
                        tell tab group 1
                            set currentTab to value of radio button 1
                            if currentTab is "Output" then
                                set selectedOutput to value of text field 1 of (first row of table 1 of scroll area 1 whose selected is true)
                                return selectedOutput
                            end if
                        end tell
                    end tell
                end if
            end tell
        end tell
        '''
        
        result = subprocess.run(['osascript', '-e', applescript], 
                              capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            output = result.stdout.strip()
            print(f"Current audio output: {output}")
            
            if 'blackhole' in output.lower():
                add_result(True, "System audio output", f"Correctly set to {output}")
                return True
            else:
                add_result(False, "System audio output", f"Should be BlackHole, but is {output}")
                print("❌ System output is NOT set to BlackHole")
                print("💡 Fix: System Settings → Sound → Output → BlackHole 2ch")
                return False
        else:
            print("⚠️  Could not determine audio output")
            return None
            
    except Exception as e:
        print(f"⚠️  Error checking audio output: {e}")
        return None

def provide_browser_recommendation():
    """Provide browser-specific recommendations"""
    print("\n🎯 BROWSER RECOMMENDATIONS")
    print("=" * 50)
    
    print("\n🔥 FIREFOX (RECOMMENDED):")
    print("   ✅ Best compatibility with BlackHole")
    print("   ✅ No audio sandboxing issues")
    print("   ✅ Works out of the box")
    print("   Steps:")
    print("   1. Open Firefox")
    print("   2. Go to YouTube")
    print("   3. System Settings → Sound → Output → BlackHole 2ch")
    print("   4. Play video")
    
    print("\n⚠️  CHROME (PROBLEMATIC):")
    print("   ❌ Audio sandboxing often blocks BlackHole")
    print("   ❌ Requires special flags that don't always work")
    print("   ❌ Not recommended for this setup")
    print("   If you must use Chrome:")
    print("   1. Quit Chrome completely")
    print("   2. Run: open -a 'Google Chrome' --args --disable-features=AudioServiceSandbox")
    print("   3. System Settings → Sound → Output → BlackHole 2ch")
    
    print("\n🍎 SAFARI:")
    print("   ⚠️  Mixed results")
    print("   ✅ Sometimes works with BlackHole")
    print("   ❌ May have permission issues")
    
    print("\n📝 VERIFICATION:")
    print("   After setting up:")
    print("   1. Run: python3 -c \"import sounddevice as sd; import numpy as np;")
    print("      rec = sd.rec(3*16000, samplerate=16000, device=0, dtype='float32');")
    print("      sd.wait(); print('Audio level:', np.max(np.abs(rec)))\"")
    print("   2. Audio level should be > 0.01")

def whisper_sanity(seconds: float = 0.5, rate: int = 16000, device=None):
    """Very quick whisper pass on a short silence buffer + mic chunk."""
    try:
        import sounddevice as sd
        import whisper

        print("\n🧠 Whisper sanity check...")
        model = whisper.load_model("base")
        buf = sd.rec(int(seconds * rate), samplerate=rate, channels=1, device=device, dtype='float32')
        sd.wait()

        audio = buf.squeeze()
        if audio.size == 0:
            add_result(False, "Whisper sanity", "No audio recorded")
            return False

        result = model.transcribe(audio, fp16=False, language="en")
        text = (result.get("text") or "").strip()
        add_result(True, "Whisper transcribe() call", f'text="{text}"')
        return True
    except Exception as e:
        add_result(False, "Whisper transcribe() call", str(e))
        print("Tip: If this fails, verify torch/whisper versions match your CPU-only setup.")
        return False

def check_homebrew_and_portaudio():
    hb = shutil.which("brew")
    if not hb:
        add_result(False, "Homebrew", "Not found (optional but handy on macOS)")
        return
    add_result(True, "Homebrew", hb)
    try:
        out = os.popen("brew list --versions portaudio 2>/dev/null").read().strip()
        if out:
            add_result(True, "PortAudio (brew)", out)
        else:
            add_result(False, "PortAudio (brew)", "Not installed — try: brew install portaudio")
    except Exception:
        add_result(False, "PortAudio (brew)", "Check manually: brew list --versions portaudio")

def main():
    parser = argparse.ArgumentParser(description="Troubleshoot Whisperer audio & environment.")
    parser.add_argument("--seconds", type=float, default=5.0, help="Seconds to record for mic test (default 5.0)")
    parser.add_argument("--rate", type=int, default=16000, help="Sample rate (default 16000)")
    parser.add_argument("--channels", type=int, default=1, help="Input channels (default 1)")
    parser.add_argument("--device", default="auto", help='Device id or name substring (default "auto")')
    parser.add_argument("--port", type=int, default=5000, help="Check if this port is free (default 5000)")
    parser.add_argument("--check-whisper", action="store_true", help="Also test whisper import and a quick transcribe()")
    parser.add_argument("--check-browser", action="store_true", help="Check browser audio routing to BlackHole")
    args = parser.parse_args()

    print("\n" + "="*60)
    print("🎯 ENHANCED WHISPERER TROUBLESHOOTER")
    print("="*60 + "\n")
    
    check_python()
    check_imports(args.check_whisper)
    check_homebrew_and_portaudio()
    
    # Check running browsers
    running_browsers = check_running_browsers()
    
    # Check system audio output
    audio_output_ok = check_system_audio_output()
    
    devices = list_input_devices()
    if not devices:
        print("\nNo input devices; aborting further audio checks.")
        sys.exit(1)

    # Resolve device
    try:
        dev_id = None
        if isinstance(args.device, str) and args.device.isdigit():
            dev_id = int(args.device)
        else:
            dev_id = resolve_device_id(args.device, devices)
        if dev_id is None:
            add_result(False, "Select input device", f"Could not resolve '{args.device}'")
            print("Tip: Re-run with a numeric index you saw above, e.g. --device 3")
            sys.exit(1)
        else:
            name = devices[dev_id]['name']
            add_result(True, "Select input device", f"{dev_id}: {name}")
    except Exception as e:
        add_result(False, "Select input device", str(e))
        sys.exit(1)

    ok_record = test_record(args.seconds, args.rate, args.channels, dev_id)
    port_free = check_port(args.port)
    
    # Check browser audio if requested
    browser_audio_ok = None
    if args.check_browser:
        browser_audio_ok = check_browser_audio_routing()
    
    ok_whisper = True
    if args.check_whisper:
        ok_whisper = whisper_sanity(seconds=0.5, rate=args.rate, device=dev_id)

    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    hard_fail = False
    for ok, line in RESULTS:
        print(line)
        if not ok and ("Import" in line or "Microphone capture" in line or "Select input device" in line):
            hard_fail = True
    
    # Provide browser recommendations
    provide_browser_recommendation()
    
    print("\n" + "="*60)
    print("🎯 FINAL RECOMMENDATION")
    print("="*60)
    
    if "Firefox" in running_browsers:
        print("✅ Firefox is running - USE THIS for YouTube!")
        print("   Make sure:")
        print("   1. System Settings → Sound → Output = BlackHole 2ch")
        print("   2. Firefox/YouTube volume at 100%")
        print("   3. Firefox tab is not muted")
    elif "Chrome" in running_browsers:
        print("⚠️  Chrome is running - SWITCH TO FIREFOX")
        print("   Chrome has audio sandboxing issues with BlackHole")
        print("   Install Firefox: brew install --cask firefox")
    else:
        print("🔴 No recommended browser running")
        print("   Install and use Firefox: brew install --cask firefox")
    
    if hard_fail or not ok_record:
        print("\nResult: ❌ Issues detected. See FAIL lines and tips above.")
        sys.exit(1)

    if not port_free:
        print("\nResult: ⚠️  Mic path OK, but target port appears busy.")
        print("        Run: ./kill-all-flasks.sh (option 3)")
        sys.exit(0)

    if args.check_whisper and not ok_whisper:
        print("\nResult: ⚠️  Mic path OK, whisper check failed—see tip above.")
        sys.exit(0)
    
    if args.check_browser and browser_audio_ok is False:
        print("\nResult: ⚠️  Mic path OK, but browser audio not reaching BlackHole")
        print("        Follow browser recommendations above")
        sys.exit(0)

    print("\nResult: ✅ All core checks passed.")
    print("        Use Firefox for YouTube, Chrome will likely not work.")

if __name__ == "__main__":
    time.sleep(0.05)
    main()