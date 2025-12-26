#!/bin/bash

# 🎭 AI Avatar System Launcher - With Aggressive Cleanup

echo ""
echo "🎭 AI Avatar System"
echo "===================="
echo ""

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up previous processes..."
    
    # Kill port 5000 processes
    lsof -ti:5000 | xargs kill -9 2>/dev/null
    
    # Kill specific Python processes
    pkill -f "python3 avatar.py" 2>/dev/null
    pkill -f "flask" 2>/dev/null
    pkill -f "python.*avatar" 2>/dev/null
    
    # Small delay to ensure cleanup
    sleep 2
    
    # Double-check port 5000
    if lsof -ti:5000 > /dev/null; then
        echo "❌ Port 5000 still in use, forcing cleanup..."
        sudo lsof -ti:5000 | xargs sudo kill -9 2>/dev/null
    fi
}

# Run cleanup
cleanup

# Check virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found. Run setup first."
    exit 1
fi

# Check environment file
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it with your API keys."
    exit 1
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Check OpenAI API key
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "sk-your-openai-api-key-here" ]; then
    echo "❌ OPENAI_API_KEY not configured in .env file"
    exit 1
fi

echo "✅ OpenAI API key configured"

# Check ElevenLabs configuration
if [ -n "$ELEVENLABS_API_KEY" ] && [ "$ELEVENLABS_API_KEY" != "your-elevenlabs-api-key-here" ]; then
    echo "✅ ElevenLabs configured for cloned voice"
else
    echo "⚠️  Using system TTS (ElevenLabs not configured)"
fi

echo ""
echo "🚀 Starting AI Avatar System..."
echo "🌐 Web Interface: http://localhost:${PORT:-5000}"
echo "🎮 Hotkeys: Ctrl+Shift+D (Delegate), Ctrl+Shift+T (Takeover), Ctrl+Shift+Q (Quit)"
echo ""

# Start the application - CORRECTED FILENAME
python3 avatar.py

echo ""
echo "🎭 AI Avatar System stopped"
