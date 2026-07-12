# 🪟 Browser Overlay

A semi‑transparent, always‑on‑top browser window for quick reference.

## What it does

- Opens a **frameless, 70% transparent** window.
- Loads `https://chat.openai.com` (or any URL you set).
- **Stays on top** of all other windows.
- Useful for ChatGPT, docs, dashboards, or any reference material.

## Quick Start

```bash
# Activate environment (first time only)
source overlay-venv/bin/activate

# Debug mode (foreground)
python browser-overlay.py

# Background start
./start-overlay.sh

# Stop
./stop-overlay.sh

# Check if running
pgrep -fl "python.*browser-overlay"
eof
