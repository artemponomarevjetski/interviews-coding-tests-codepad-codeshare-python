# 🎭 AI Avatar System

A real-time AI assistant that can temporarily take over conversations using your cloned voice. Seamlessly delegate discussions to AI and take back control when needed.

## ✨ Features

- **🎙️ Voice Cloning** - Create a realistic voice clone using ElevenLabs API
- **🤖 Intelligent Conversations** - GPT-4 powered responses with conversation memory
- **🎮 Hotkey Control** - Delegate/takeover conversations with keyboard shortcuts
- **🌐 Web Dashboard** - Real-time monitoring interface at `localhost:5000`
- **🔊 Multi-platform Audio** - Works on macOS, Linux, and Windows
- **⚡ Real-time Processing** - Low-latency speech recognition and synthesis
- **🎯 Graceful Fallbacks** - System TTS when voice cloning unavailable

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key
- ElevenLabs API key (optional, for voice cloning)
- macOS/Linux/Windows with microphone

### Installation

```bash
# Clone and setup
git clone <repository-url>
cd avatar

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your API keys
```

### Voice Cloning Setup

```bash
# Place your voice samples in audio/ folder (3-5 samples, 10-30s each)
# Then run voice cloning setup
python3 voice-clone.py
```

### Launch the System

```bash
# Start the AI avatar
./launch-avatar.sh
# Access dashboard at http://localhost:5000
```

## 📁 Project Structure

```
avatar/
├── avatar.py              # Main AI system (29KB)
├── voice-clone.py         # Voice cloning utility (8KB)
├── launch-avatar.sh       # Launcher script (1.9KB)
├── requirements.txt       # Dependencies
├── .env                   # API configuration
├── audio/                 # Voice samples (~1MB)
│   ├── voice_preview_art.mp3
│   ├── original.m4a
│   └── clone.mp3
└── venv/                  # Virtual environment
```

## 🎮 Usage

### Conversation Flow
1. **Start Speaking** - Begin conversation naturally
2. **Delegate** - Press `Ctrl+Shift+D` to activate AI avatar
3. **Monitor** - Watch AI handle conversation with your cloned voice
4. **Take Over** - Press `Ctrl+Shift+T` to resume control anytime

### Web Interface
Access `http://localhost:5000` for:
- Real-time conversation monitoring
- Manual delegation controls
- Conversation history
- System status

### Hotkeys
- **Ctrl+Shift+D** - Delegate to AI avatar
- **Ctrl+Shift+T** - Take back control
- **Ctrl+Shift+Q** - Quit system

## 🔧 Configuration

### API Keys Required
Create a `.env` file with:
```bash
OPENAI_API_KEY=sk-your-openai-key
ELEVENLABS_API_KEY=your-elevenlabs-key  # Optional
ELEVENLABS_VOICE_ID=auto-generated
GPT_MODEL=gpt-4
PORT=5000
```

### Audio Requirements
For best voice cloning results:
- 3-5 audio samples, 10-30 seconds each
- Clear recordings with minimal background noise
- Various phrases and speaking styles
- Supported formats: MP3, WAV, M4A

## 🛠️ Technical Details

### Core Components
- **Speech Recognition**: OpenAI Whisper API
- **Language Model**: GPT-4 (configurable to GPT-3.5-turbo)
- **Voice Synthesis**: ElevenLabs API + system TTS fallback
- **Audio Processing**: Real-time streaming with silence detection
- **Web Server**: Flask with auto-refresh interface

### System Architecture
The system manages three conversation states:
- `HUMAN_LEAD` - Human controls conversation
- `AVATAR_ACTIVE` - AI responds with cloned voice
- `TRANSITIONING` - Smooth state transition

### Performance Metrics
- **Response Time**: <2 seconds for AI processing
- **Audio Latency**: Real-time streaming
- **Memory Usage**: Optimized for continuous operation
- **Error Handling**: Graceful fallbacks throughout

## 🔍 Troubleshooting

### Common Issues

**Hotkeys Not Working (macOS)**
```bash
# Grant Accessibility permissions:
# System Settings → Privacy & Security → Accessibility
# Add your terminal application
```

**Port 5000 Already in Use**
```bash
# The launch script automatically cleans up ports
# Or manually: lsof -ti:5000 | xargs kill -9
```

**Missing Audio Libraries**
```bash
# macOS
brew install portaudio

# Ubuntu/Debian
sudo apt-get install portaudio19-dev python3-pyaudio
```

### API Errors
- Verify API keys in `.env` are valid
- Check billing/credits on OpenAI and ElevenLabs
- Ensure internet connection is stable

## 📚 Dependencies

```bash
# Core AI & APIs
openai>=1.0.0
elevenlabs>=0.2.28

# Audio Processing
sounddevice>=0.4.6
soundfile>=0.12.1
speechrecognition>=3.10.0

# Web Interface & Control
flask>=2.3.0
keyboard>=0.13.5
requests>=2.28.0

# Utilities
python-dotenv>=1.0.0
numpy>=1.21.0
```

## ⚠️ Important Notes

### Security
- Never commit `.env` file to version control
- Conversation data is not persisted long-term
- Audio processing happens locally before API calls

### Ethical Use
- Always inform others when using AI assistance
- Take responsibility for AI-generated content
- Use for productivity enhancement, not deception

### Limitations
- Requires stable internet connection for API calls
- Voice cloning quality depends on sample quality
- Real-time performance varies by system resources

---

# 🛠️ Development & Interview Toolkit

This repository is part of a larger collection of development tools and interview preparation materials.

## 📁 Project Structure

### 🎭 AI Avatar System (Current)
The primary system described above for conversational AI with voice cloning.

### 🔄 File Synchronization Toolkit
Intelligent file synchronization with conflict resolution and dry-run capabilities.

**Files:**
- `sync_by_rules.py` - Core synchronization logic (Python 3.8+)
- `sim_sync.sh` - Dry-run simulation wrapper
- `apply_sync.sh` - Apply changes wrapper
- `Makefile` - Convenience targets for common operations

**Usage:**
```bash
# Dry-run with defaults
./sim_sync.sh

# Apply changes safely
python3 sync_by_rules.py --apply

# Apply with conflict resolution
python3 sync_by_rules.py --apply --delete-older-source

# Recursive synchronization
python3 sync_by_rules.py --apply --recursive
```

### 📝 Interview & Coding Tests
- **Coding Tests** - Python solutions for technical interviews
- **SQL & Python Questions** - Database and programming challenges  
- **Algorithm Problems** - Data structures and algorithms
- **Web Scraping** - Data extraction and processing scripts

### 🗂️ Key Directories
- `assesments/` - Coding assessment solutions
- `flask/` - Web application projects
- `overlay/` - Browser overlay utilities
- `whisperer_external/` & `whisperer_internal/` - Speech-to-text AI projects
- `chatterbox/` - Chat application prototypes
- `png/` - Documentation screenshots

### 📊 Analysis & Utilities
- `compare_folders.sh` - Folder comparison tools
- `folder-sizes.sh` - Disk usage analysis
- `dedupe_suffixes.py` - File deduplication
- `move_up.sh` - File organization utilities

### 📋 Featured Code Samples
- **Data Structures:** `cdll.py` (Circular Doubly Linked List)
- **Algorithms:** `tree.py`, `atoi.ipynb`
- **Web Development:** `app.py`, `desklog.py`
- **Data Analysis:** `lidar-test.py`, `heart.csv` processing

### 🔧 Requirements
- Python 3.8+
- Bash shell
- Common Unix utilities

## 📄 License

MIT License - See LICENSE file for details.

---

**Ready to deploy your AI avatar? Run `./launch-avatar.sh` and start the conversation!**