#!/bin/bash

# Activate virtual environment if present
[ -d "venv" ] && source venv/bin/activate

# Silently install dependencies
pip install -r requirements.txt >/dev/null 2>&1

# Kill existing snapshot.py, tesseract, and other Python processes quietly
pkill -f "snapshot.py" 2>/dev/null
pkill -f "tesseract" 2>/dev/null
pgrep -f "python" | grep -v "$$" | xargs -r kill -9 2>/dev/null

# Free port 5000 quietly
lsof -ti :5000 | xargs -r kill -9 2>/dev/null

# Ensure log directory exists
mkdir -p "$HOME/log"

# Launch snapshot.py in the background, consolidate output to logfile
nohup python snapshot.py >> "$HOME/log/snapshot.log" 2>&1 &
disown

# Brief pause to ensure the application has launched properly
sleep 1

# User notification
echo "✅ snapshot.py launched and disowned. Check ~/log/snapshot.log for output."
