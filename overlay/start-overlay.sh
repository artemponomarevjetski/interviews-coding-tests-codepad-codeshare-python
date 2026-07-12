#!/bin/bash
pkill -f browser-overlay.py
echo "Starting browser overlay..."
mkdir -p data
nohup ./overlay-venv/bin/python browser-overlay.py > data/overlay.log 2>&1 &
disown
echo "✅ Browser overlay started (logs → data/overlay.log)"
echo "Check for semi-transparent window on screen"
# Close the current Terminal window (macOS only)
osascript -e 'tell application "Terminal" to close (first window whose frontmost is true)' &
exit 0
