#!/bin/bash
# Clean up previous instances
pkill -f "Xvfb :99" 2>/dev/null

# Start virtual display
Xvfb :99 -screen 0 1024x768x24 -ac +extension GLX +render -noreset &
sleep 2

# Main loop with crash recovery
export DISPLAY=:99
while true; do
    /usr/bin/python3 stealth.py
    echo "$(date): Browser crashed - restarting in 5 seconds..."
    sleep 5
done
