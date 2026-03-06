#!/bin/bash

# 📋 PASTE SAVER - Complete Launch Script
# Checks port, frees it, sets up venv, installs requirements, launches app

echo "📋 PASTE SAVER - Launch Script"
echo "================================"

# Get the directory where this script is located
cd "$(dirname "$0")"
echo "📍 Working directory: $(pwd)"

# Function to kill process on port 5000
kill_port_5000() {
    echo "🔍 Checking port 5000..."
    local pid=$(lsof -ti:5000)
    if [ ! -z "$pid" ]; then
        echo "⚠️  Port 5000 is in use by PID $pid"
        echo "🔴 Killing process..."
        kill -9 $pid 2>/dev/null
        sleep 1
        if lsof -ti:5000 >/dev/null; then
            echo "❌ Failed to kill process on port 5000"
            return 1
        else
            echo "✅ Port 5000 is now free"
        fi
    else
        echo "✅ Port 5000 is already free"
    fi
    return 0
}

# Kill any process on port 5000
kill_port_5000
if [ $? -ne 0 ]; then
    echo "❌ Could not free port 5000. Exiting."
    exit 1
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
else
    echo "✅ Python $(python3 --version) found"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi
echo "✅ Virtual environment activated"

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✅ Pip upgraded"

# Install requirements
echo "📦 Installing requirements..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install requirements"
        exit 1
    fi
    echo "✅ Requirements installed from requirements.txt"
else
    echo "⚠️  requirements.txt not found. Creating default..."
    echo "Flask==3.1.3" > requirements.txt
    echo "Werkzeug==3.1.6" >> requirements.txt
    pip install -r requirements.txt
    echo "✅ Default requirements installed"
fi

# Create logs directory if it doesn't exist (though app does this too)
mkdir -p logs/excerpts logs/images
echo "📁 Log directories ready"

# Clear any Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
echo "🧹 Cache cleared"

# Display launch information
echo ""
echo "🚀 Launching Paste Saver..."
echo "================================"
echo ""

# Run the app
python app.py

# This part runs if the app exits
echo ""
echo "👋 Paste Saver has stopped."
echo "📁 Your saved files are in: $(pwd)/logs/"