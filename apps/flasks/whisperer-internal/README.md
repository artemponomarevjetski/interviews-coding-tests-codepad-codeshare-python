# 🎤 Whisperer‑Internal – Microphone Transcription

> Real‑time speech‑to‑text using **faster‑whisper** – no compilation headaches, no `llvmlite` nightmares.

---

## 📖 What It Does

- Listens to your **built‑in microphone** (or any input device)
- Transcribes what you say in real‑time using OpenAI's Whisper model (via faster‑whisper)
- Displays transcriptions on a live web dashboard
- Runs in the background, survives terminal closure
- Includes a **troubleshooter** script to diagnose audio issues

---

## 🚀 Quick Start

```bash
cd apps/flasks/whisperer-internal
chmod +x set-up-and-launch-whisperer-internal.sh
./set-up-and-launch-whisperer-internal.sh
```

Then open `http://localhost:5000` in your browser.

Speak clearly – you'll see transcriptions appear.

---

## 🧠 How It Works

1. The launcher script:
   - Kills any previous instance of the app
   - Sets up a fresh Python virtual environment
   - Installs `faster‑whisper` (no `llvmlite`/`numba` build issues)
   - Starts the Flask web server in the background

2. The app captures audio from your default microphone, buffers speech, and sends it to `faster‑whisper` for transcription.

3. Transcriptions are displayed on the web interface and logged to `logs/flask_app.log`.

---

## 🛠️ Troubleshooter

If something isn't working, run:

```bash
python troubleshooter.py
```

This tool checks:

- Python and package availability
- Microphone access and permissions
- Audio device listing
- Recording levels
- Port availability (5000)
- (Optional) BlackHole routing for system audio

For deeper checks:

```bash
python troubleshooter.py --check-whisper --check-browser
```

---

## 📁 File Structure

```
whisperer-internal/
├── set-up-and-launch-whisperer-internal.sh   # Launcher (kills old, sets up venv, starts app)
├── whisperer-internal.py                     # Main Flask application (faster‑whisper)
├── troubleshooter.py                          # Audio diagnostic tool
├── requirements.txt                           # Python dependencies (faster‑whisper)
├── README.md                                  # This file
├── logs/                                     # Runtime logs
│   ├── service.log                           # Launcher logs
│   ├── flask_app.log                         # Application logs
│   └── transcriptions.log                    # All transcriptions (rotated)
└── venv/                                     # Virtual environment (auto‑created)
```

---

## 🔧 Dependencies

The launcher installs the following automatically:

- `Flask==2.3.2`
- `numpy==1.26.4`
- `sounddevice==0.4.6`
- `faster-whisper`

No `llvmlite` or `numba` are required – **no build errors**.

---

## 🎯 Usage Scenarios

- **Test your microphone** – speak and see if transcription works.
- **Develop voice‑enabled apps** – use the transcription output.
- **Quick dictation** – capture spoken notes without saving files.

---

## ⚙️ Configuration

You can customise the launcher by editing the variables at the top of the script:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 5000 | Web interface port |
| `VENV_DIR` | `venv` | Virtual environment directory |
| `PID_FILE` | `whisperer.pid` | File storing the process ID |
| `LOG_RETENTION_DAYS` | 7 | How many days of transcript logs to keep |

---

## 📦 Environment Variables (Optional)

If you need to override the port or other settings, you can set them before running:

```bash
PORT=5001 ./set-up-and-launch-whisperer-internal.sh
```

---

## ❓ Troubleshooting Common Issues

| Problem | Solution |
|---------|----------|
| **No microphone detected** | Check System Settings → Privacy & Security → Microphone → enable Terminal. |
| **Port 5000 already in use** | Run `../kill-all-flasks.sh` or manually kill the process. |
| **Transcription not appearing** | Speak clearly; check the log file `logs/flask_app.log` for errors. |
| **Build errors** | The script uses `faster‑whisper` – if you still see `llvmlite` errors, ensure you have the latest script. |
| **Hotkeys not working** | This app doesn't use hotkeys – it's purely web‑based. |

---

## 🖥️ Web Interface

The dashboard updates every 2 seconds. It shows the last 20 transcriptions from the past minute.

---

## 📝 Logs

- `logs/flask_app.log` – all application output (including transcription events).
- `logs/service.log` – launcher script logs.
- `logs/transcriptions.log` – a rotating log of all transcriptions.

You can monitor the app in real‑time:

```bash
tail -f logs/flask_app.log
```

---

## 🛑 Stopping the App

```bash
pkill -f whisperer-internal.py
# or
kill $(cat whisperer.pid)
```

---

## 🧪 Test It

1. Run the launcher.
2. Open `http://localhost:5000`.
3. Speak clearly: *"one two three four five"*.
4. You should see the words appear within seconds.

---

## 📄 License

MIT – free to use, modify, and distribute.

---

```
╔══════════════════════════════════════════════════════════════════════╗
║   🎤  Whisperer‑Internal  –  Built by Artem Ponomarev              ║
║   Say it, see it – no build hassles.                               ║
╚══════════════════════════════════════════════════════════════════════╝
```
