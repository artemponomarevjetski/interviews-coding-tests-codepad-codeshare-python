#!/bin/bash

# Kill the process using port 5000
pid=$(lsof -ti:5000)
if [ -n "$pid" ]; then
  echo "Killing process on port 5000 (PID: $pid)"
  kill -9 $pid
fi

# Activate the virtual environment
source venv/bin/activate

# Run the Python script in the background using nohup and disown
nohup python3 snapshot.py & disown

echo "Flask app running in the background"
