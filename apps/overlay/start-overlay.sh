#!/bin/bash
echo "Starting browser overlay..."
source overlay-venv/bin/activate
nohup python browser-overlay.py > /dev/null 2>&1 &
disown
echo "✅ Browser overlay started"
echo "Check for semi-transparent window on screen"
