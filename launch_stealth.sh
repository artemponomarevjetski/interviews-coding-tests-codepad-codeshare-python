#!/bin/bash
# Clean up previous instances
pkill -f "python.*stealth.py" 2>/dev/null
pkill -f Xvfb 2>/dev/null

# Start virtual display (if needed)
Xvfb :99 -screen 0 1024x768x24 -ac +extension GLX +render -noreset 2>/dev/null &
export DISPLAY=:99
sleep 2

# Run with crash protection
while true; do
    nohup python stealth.py >> stealth.log 2>&1
    echo "[$(date)] Process crashed, restarting in 5 seconds..."
    sleep 5
done
