#!/usr/bin/env bash

echo "🔧 Automatically configuring Audio MIDI Setup for BlackHole..."

# Step 1: Check if BlackHole is installed
if ! system_profiler SPAudioDataType | grep -q "BlackHole"; then
    echo "❌ BlackHole not found! Install first:"
    echo "   brew install blackhole-2ch"
    exit 1
fi

# Step 2: Setup virtual environment
echo -e "\n📦 Setting up Python environment..."
[ ! -d "venv" ] && python3 -m venv venv
source venv/bin/activate
pip install -q pyaudio SpeechRecognition numpy
echo "✅ Dependencies installed"

# Step 3: Configure Audio MIDI with AppleScript (FIXED)
echo -e "\n🔧 Configuring Audio MIDI Setup..."
osascript <<EOF
tell application "Audio MIDI Setup"
    activate
end tell

delay 1

tell application "System Events"
    tell process "Audio MIDI Setup"
        -- Click + button to create new device
        click button 1 of window 1
        
        delay 0.5
        
        -- Select "Create Multi-Output Device"
        keystroke "Create Multi-Output Device"
        keystroke return
        
        delay 1
        
        -- Check both devices
        -- External Headphones (row 1)
        click checkbox 1 of row 1 of table 1 of scroll area 1 of window 1
        
        -- BlackHole 2ch (row 2)
        click checkbox 1 of row 2 of table 1 of scroll area 1 of window 1
        
        -- Enable Drift Correction for BlackHole
        click checkbox 1 of row 2 of table 1 of scroll area 1 of window 2
        
        delay 0.5
        
        -- Set as default output
        tell row 1 of table 1 of scroll area 1 of window 1
            perform action "AXShowMenu"
            keystroke "Use This Device For Sound Output"
            keystroke return
        end tell
    end tell
end tell
EOF

echo "✅ Audio MIDI configured"

# Step 4: Verify and set as default using SwitchAudioSource
if command -v SwitchAudioSource &> /dev/null; then
    echo "✅ Setting Multi-Output Device as default..."
    SwitchAudioSource -s "Multi-Output Device" -t output 2>/dev/null
else
    echo "⚠️  Install switchaudio-osx for better control:"
    echo "   brew install switchaudio-osx"
fi

# Step 5: Show current configuration
echo -e "\n🎧 Current audio setup:"
if command -v SwitchAudioSource &> /dev/null; then
    SwitchAudioSource -a -t output | while read device; do
        if [[ "$device" == *"Multi-Output"* ]]; then
            echo "   ✅ $device (DEFAULT)"
        else
            echo "   • $device"
        fi
    done
fi

# Step 6: Launch transcriber
echo -e "\n🚀 Launching transcriber (Press Ctrl+C to stop)\n"
python avatar.py
