# 🪟 Browser Overlay

A semi‑transparent, always‑on‑top browser window – perfect for ChatGPT, dashboards, or any reference material you need to keep visible while working.

---

## ✨ Features

- **Frameless, 70% transparent** window – stays out of your way.
- **Always on top** – never gets buried under other windows.
- **Persistent session** – cookies and local storage are saved in `data/`.  
  Log in once, and you stay logged in across restarts.
- **Toggle visibility** – press `Ctrl+Shift+H` to show/hide the window instantly.
- **Graceful shutdown** – `Ctrl+C` in foreground mode exits cleanly.
- **Runs in background** – use `./start-overlay.sh` and close the terminal.
- **Logging** – background logs are written to `data/overlay.log`.

---

## 🚀 Quick Start

```bash
# 1. Activate the virtual environment (first time only)
source overlay-venv/bin/activate

# 2. Run in foreground (debug mode – logs go to terminal)
python browser-overlay.py

# 3. Run in background (logs to data/overlay.log, detach from terminal)
./start-overlay.sh

# 4. Stop the background process
./stop-overlay.sh

# 5. Check if it's running
pgrep -fl "python.*browser-overlay"
