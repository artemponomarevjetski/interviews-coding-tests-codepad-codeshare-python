#!/bin/bash
# Clean up any existing Xvfb
pkill -f "Xvfb :99"

# Start Xvfb with proper options
Xvfb :99 -screen 0 1024x768x24 -ac +extension GLX +render -noreset &

# Wait for initialization
sleep 2

# Main loop
export DISPLAY=:99
while true; do
    python stealth.py
    echo "Browser crashed - restarting in 5 seconds..."
    sleep 5
done
