#!/usr/bin/env python3
"""
Whisperer Troubleshooter
- Verifies Python + packages
- Checks PortAudio/sounddevice and lists input devices
- Records a short sample and reports amplitude
- Optionally checks if Whisper can import and run a tiny transcribe on silence
- Optionally checks if a port (e.g., 5000) is occupied

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
from contextlib import closing

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

        print("\nAvailable input devices:")
        for idx, dev in enumerate(devices):
            if dev.get('max_input_channels', 0) > 0:
                print(f"  {idx}: {dev['name']}")

        add_result(True, "Enumerate audio devices", f"{len(inputable)} input device(s)")
        return devices
    except Exception as e:
        add_result(False, "Enumerate audio devices", str(e))
        return []

def resolve_device_id(preferred: str | int, devices):
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
        import numpy as np
        import sounddevice as sd

        print(f"\nRecording test: {seconds:.1f}s @ {rate} Hz, ch={channels}, device={device}")
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

def whisper_sanity(seconds: float = 0.5, rate: int = 16000, device=None):
    """Very quick whisper pass on a short silence buffer + mic chunk."""
    try:
        import numpy as np
        import sounddevice as sd
        import whisper

        print("\nWhisper sanity check (this may download a model the first time)…")
        model = whisper.load_model("base")  # small enough for CPU
        # Record a very short snippet
        buf = sd.rec(int(seconds * rate), samplerate=rate, channels=1, device=device, dtype='float32')
        sd.wait()

        audio = buf.squeeze()
        if audio.size == 0:
            add_result(False, "Whisper sanity", "No audio recorded")
            return False

        # Normalize to avoid near-zero energies
        peak = float(np.max(np.abs(audio)))
        if peak > 0:
            audio = audio / peak

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
    # PortAudio presence hint
    try:
        # Not a definitive check, but gives a hint
        out = os.popen("brew list --versions portaudio 2>/dev/null").read().strip()
        if out:
            add_result(True, "PortAudio (brew)", out)
        else:
            add_result(False, "PortAudio (brew)", "Not installed — try: brew install portaudio")
    except Exception:
        add_result(False, "PortAudio (brew)", "Check manually: brew list --versions portaudio")

def main():
    parser = argparse.ArgumentParser(description="Troubleshoot Whisperer audio & environment.")
    parser.add_argument("--seconds", type=float, default=5.0, help="Seconds to record for the mic test (default 5.0)")
    parser.add_argument("--rate", type=int, default=16000, help="Sample rate (default 16000)")
    parser.add_argument("--channels", type=int, default=1, help="Input channels (default 1)")
    parser.add_argument("--device", default="auto", help='Device id or name substring (default "auto")')
    parser.add_argument("--port", type=int, default=5000, help="Check if this port is free (default 5000)")
    parser.add_argument("--check-whisper", action="store_true", help="Also test whisper import and a quick transcribe()")
    args = parser.parse_args()

    print("\n=== Whisperer Troubleshooter ===\n")
    check_python()
    check_imports(args.check_whisper)
    check_homebrew_and_portaudio()

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

    ok_whisper = True
    if args.check_whisper:
        ok_whisper = whisper_sanity(seconds=0.5, rate=args.rate, device=dev_id)

    print("\n=== Summary ===")
    hard_fail = False
    for ok, line in RESULTS:
        print(line)
        if not ok and ("Import" in line or "Microphone capture" in line or "Select input device" in line):
            hard_fail = True

    if hard_fail or not ok_record:
        print("\nResult: ❌ Issues detected. See FAIL lines and tips above.")
        sys.exit(1)

    if not port_free:
        print("\nResult: ⚠️  Mic path OK, but target port appears busy.")
        sys.exit(0)

    if args.check_whisper and not ok_whisper:
        print("\nResult: ⚠️  Mic path OK, whisper check failed—see tip above.")
        sys.exit(0)

    print("\nResult: ✅ All core checks passed.")

if __name__ == "__main__":
    # Small delay so terminal prints in order when run inside scripts
    time.sleep(0.05)
    main()
