#!/bin/bash
pkill -f browser-overlay.py   # kills any existing instance
echo "Starting browser overlay..."
source overlay-venv/bin/activate
mkdir -p data                  # ensure data/ exists
nohup python browser-overlay.py > data/overlay.log 2>&1 &
disown
echo "✅ Browser overlay started (logs → data/overlay.log)"
echo "Check for semi-transparent window on screen"
