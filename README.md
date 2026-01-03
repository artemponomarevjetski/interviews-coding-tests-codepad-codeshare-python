# 🚀 Python Development Portfolio

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3%2B-green)](https://flask.palletsprojects.com/)
[![Bash](https://img.shields.io/badge/Bash-Scripting-4EAA25)](https://www.gnu.org/software/bash/)
[![Production-Ready](https://img.shields.io/badge/Production--Ready-Yes-success)]()
[![License](https://img.shields.io/badge/License-MIT-yellow)]()
[![LLVM](https://img.shields.io/badge/LLVM-20.1.8-blueviolet)](https://llvm.org/)
[![Whisper](https://img.shields.io/badge/Whisper-AI-7B68EE)](https://openai.com/research/whisper)

A comprehensive collection of Python applications, scripts, and utilities demonstrating modern software development, automation, and full-stack capabilities.

## 📁 Project Structure

```
interviews-coding-tests-codepad-codeshare-python/
├── 📦 Production Applications
│   ├── apps/
│   │   ├── flasks/
│   │   │   ├── flask-exercise/     # Flask learning exercises and examples
│   │   │   ├── flask-test/         # Flask testing framework with demo app
│   │   │   ├── flask/              # Main Flask application (snapshot.py)
│   │   │   ├── whisperer_internal/ # ✅ Internal audio transcription with LLVM fix
│   │   │   ├── whisperer_external/ # External audio transcription
│   │   │   ├── avatar/             # Voice cloning systems
│   │   │   └── image-to-gpt/       # Visual analysis tools
│   │   ├── keylogger/        # Keylogger analysis and visualization tools
│   │   ├── overlay/          # Browser overlay and transparency tools
│   │   ├── chatterbox/       # Chat/communication applications
│   │   └── assesments/       # Assessment and testing tools
│   │
│   ├── whisperer_external/   # Dual audio transcription (mic + system audio)
│   ├── whisperer_internal/   # ✅ Fixed LLVM version compatibility issue
│   └── lidar/                # LiDAR data processing applications
│
├── 🔧 Development Tools
│   ├── sync_by_rules.py      # Intelligent file synchronization tool
│   ├── dedupe_suffixes.py    # File deduplication with suffix management
│   ├── move_up.sh           # File organization automation
│   ├── compare_folders.sh   # Folder comparison utilities
│   ├── launch_flask_on5000_whisperer_internal.sh  # ✅ Fixed deployment script
│   └── sync_toolkit.tar     # Complete synchronization toolkit
│
├── 📚 Learning & Practice
│   ├── coding challenges and interview preparation
│   ├── Python exercises and algorithm implementations
│   └── Notebook explorations (moved to external repository)
│
└── 🛠️ Infrastructure
    ├── env-setup.sh         # Environment setup automation
    ├── venv/                # Virtual environment
    ├── .gitignore          # Comprehensive git ignore rules
    └── requirements.txt     # Python dependencies
```

## 🎯 Featured Projects

### 🎤 **Internal Audio Transcription System** (`whisperer_internal/`) ✅ **RECENTLY FIXED**

**Real-time microphone transcription with LLVM compatibility fix**

```bash
# ✅ FIXED: LLVM 21 → 20 compatibility issue resolved
# Features:
# • MacBook Pro microphone optimization
# • Real-time Whisper AI transcription  
# • Automatic LLVM version management
# • Web dashboard with live updates
# • Fallback to faster-whisper if needed

# Launch the system (now with fixed LLVM):
cd whisperer_internal
./launch_flask_on5000_whisperer_internal.sh
# Open: http://localhost:5000
```

**Recent Fix - LLVM Compatibility:**
- **Problem**: llvmlite 0.46.0 only supports LLVM 20, but system had LLVM 21
- **Solution**: Automated LLVM version management in deployment script
- **Key Fix**: `brew uninstall llvm` (removes LLVM 21) + `brew install llvm@20`
- **Environment**: Sets `LLVM_CONFIG=/usr/local/opt/llvm@20/bin/llvm-config`
- **Fallback**: Automatically switches to `faster-whisper` if llvmlite fails

**Architecture:**
- **Optimized audio capture** for MacBook Pro microphones
- **Whisper AI** for real-time transcription
- **LLVM 20 compatibility** with automated version management
- **Flask web interface** with auto-refresh (2-second updates)
- **Graceful degradation** to faster-whisper if needed

### 🎤 **Dual Audio Transcription System** (`whisperer_external/`)

**Real-time microphone + YouTube audio transcription**

```bash
# Features:
# • External microphone capture
# • System audio capture via BlackHole
# • Real-time Whisper AI transcription
# • Web dashboard with live updates
# • Dual-stream processing (YOU + HEAR)

# Launch the system:
cd whisperer_external
./launch-flask-on5000-whisperer-external.sh
# Open: http://localhost:5000
```

**Architecture:**
- **Multi-threaded audio capture** (mic + system audio)
- **Whisper AI** for real-time transcription
- **Flask web interface** with auto-refresh
- **BlackHole audio routing** for system capture
- **Crash protection** and graceful recovery

### 🎭 **Browser Overlay System** (`apps/overlay/`)

**Semi-transparent, always-on-top browser windows**

```python
# Key Features:
# • Truly stealth window (no taskbar/dock icon)
# • Adjustable transparency (70% by default)
# • Bypasses window managers
# • Manual login capability
# • Hidden from screen sharing

# Setup:
cd apps/overlay
python -m venv venv
source venv/bin/activate
pip install PyQt6 PyQt6-WebEngine
python browser-overlay.py
```

**Use Cases:**
- Reference materials while coding
- Chat assistants overlay
- Documentation sidebars
- Learning tools transparency

### 🔑 **Keylogger Analysis Suite** (`apps/keylogger/`)

**Professional keyboard activity analysis and visualization**

```python
# Tools Included:
# • text_reconstructor.py - Reconstruct typed content from keylogs
# • web_dashboard.py - Real-time visualization interface
# • Pattern analysis and security auditing

# Sample usage:
cd apps/keylogger
python text_reconstructor.py path/to/keylog.jsonl
python web_dashboard.py  # Launches visualization interface
```

**Features:**
- Text reconstruction from raw key events
- Web-based visualization dashboard
- Pattern analysis for productivity
- Security auditing capabilities

### 🚀 **Flask Development Framework** (`apps/flasks/`)

**Comprehensive Flask development and testing environment**

```python
# Projects Included:
# • flask-exercise/ - Basic Flask learning exercises
# • flask-test/     - Testing framework with demo image server
# • flask/          - Production Flask application with GPT analysis
# • whisperer_internal/ - ✅ Fixed internal audio transcription
# • whisperer_external/ - External audio transcription
# • avatar/ - Voice cloning systems
# • image-to-gpt/ - Visual analysis tools

# Test the Flask demo server:
cd apps/flasks/flask-test
python app.py
# Open: http://localhost:5001
```

**Features:**
- **Demo Image Server** - Serves test images from `test-snapshot/` directory
- **Clean Separation** - Test vs production environments
- **Temporary Files Management** - `temp/` ignored globally via `.gitignore`
- **Structured Testing** - Organized test assets in `test-snapshot/`

## 🏗️ Technical Architecture

### **Modular Application Design**

```python
# apps/flasks/ - Example Flask application structure
flasks/
├── flask-exercise/     # Flask learning exercises
├── flask-test/         # Flask testing and demo applications
├── whisperer_internal/ # ✅ Fixed internal audio processing (LLVM 20)
├── whisperer_external/ # External audio processing
├── avatar/             # Voice cloning and avatar systems
└── image-to-gpt/       # Visual analysis tools
```

### **File Management Strategy**

```bash
# Temporary files (.gitignore):
temp/              # Ignored globally - for runtime temporary files
*.tmp              # Temporary file patterns
*.log              # Log files (kept local)
venv/              # Virtual environments
logs/              # Application logs

# Test assets (tracked):
test-snapshot/     # Tracked test images and assets
demo/              # Demonstration files
examples/          # Example data and configurations

# Best Practices:
# 1. Use 'test-snapshot/' for test images you want to track
# 2. Use 'temp/' for runtime files you don't want in git
# 3. Keep production code separate from test/demo code
# 4. Logs go to 'logs/' directory for each application
```

### **Audio Processing Pipeline** ✅ **IMPROVED**

```python
# whisperer_internal/whisperer.py - FIXED VERSION
def initialize_whisper_model():
    """
    Loads Whisper model with LLVM 20 compatibility
    Falls back to faster-whisper if llvmlite fails
    """
    try:
        # Try original whisper (requires llvmlite with LLVM 20)
        import whisper
        return whisper.load_model("base")
    except Exception:
        # Fallback to faster-whisper (no LLVM dependencies)
        from faster_whisper import WhisperModel
        return WhisperModel("base", device="cpu", compute_type="int8")
```

### **LLVM Compatibility Management** 🔧 **NEW SECTION**

```bash
# launch_flask_on5000_whisperer_internal.sh - Key Fixes:
# 1. Check for LLVM 21 and remove it
if brew list --versions llvm | grep -q "21"; then
    brew uninstall llvm
fi

# 2. Ensure LLVM 20 is installed
if ! brew list --versions llvm@20; then
    brew install llvm@20
fi

# 3. Set environment variables for LLVM 20
export LLVM_CONFIG="/usr/local/opt/llvm@20/bin/llvm-config"
export PATH="/usr/local/opt/llvm@20/bin:$PATH"

# 4. Install llvmlite with correct LLVM version
LLVM_CONFIG=/usr/local/opt/llvm@20/bin/llvm-config pip install llvmlite==0.46.0

# 5. Fallback mechanism
if ! python -c "import llvmlite"; then
    pip install faster-whisper  # Alternative without LLVM
fi
```

## 🚀 Getting Started

### **Quick Setup**

```bash
# 1. Clone the repository
git clone https://github.com/artemponomarevjetski/interviews-coding-tests-codepad-codeshare-python.git
cd interviews-coding-tests-codepad-codeshare-python

# 2. Setup environment
./env-setup.sh

# 3. Choose an application to run
cd whisperer_internal && ./launch_flask_on5000_whisperer_internal.sh  # ✅ FIXED
# OR test Flask demo:
cd apps/flasks/flask-test && python app.py
# OR test browser overlay:
cd apps/overlay && python browser-overlay.py
# OR test keylogger analysis:
cd apps/keylogger && python web_dashboard.py
```

### **System Requirements**

- **Python 3.8+** with virtual environment support
- **macOS** (optimized, but cross-platform compatible)
- **Audio devices** for transcription applications
- **LLVM 20** (for whisper transcription - automatically managed)
- **Homebrew** (for package management on macOS)
- **PortAudio** (for audio capture: `brew install portaudio`)

### **Installation Notes** 📝 **UPDATED**

```bash
# For whisperer_internal - Automated LLVM management
cd whisperer_internal
./launch_flask_on5000_whisperer_internal.sh
# Script will:
# 1. Check for LLVM 21 and remove it if present
# 2. Install LLVM 20 if not installed
# 3. Set proper environment variables
# 4. Install llvmlite with LLVM 20
# 5. Install whisper and dependencies
# 6. Launch Flask application on port 5000
```

## 🔧 Development Patterns

### **Production-Ready Scripting**

```bash
# compare_folders.sh - Professional folder comparison
#!/bin/bash
# Usage: ./compare_folders.sh /path/to/folder1 /path/to/folder2
# Features:
# • Recursive directory comparison
# • File size and timestamp analysis
# • Missing file detection
# • Summary reporting

# folder-sizes.sh - Disk usage analysis
# Visual breakdown of folder sizes
# Sort by size, date, or type
# Export to CSV for analysis

# launch_flask_on5000_whisperer_internal.sh - ✅ Improved deployment
# Features:
# • LLVM version management
# • Port conflict resolution
# • Virtual environment management
# • Log rotation and cleanup
# • PID management for graceful shutdown
```

### **Data Processing Utilities**

```python
# dedupe_suffixes.py - Intelligent file deduplication
def deduplicate_files(directory):
    """
    Removes duplicate files with different suffixes
    Preserves the most relevant version
    Maintains file relationships
    """
    
# heart.csv - Data analysis examples
# Sample datasets for analysis practice
# CSV manipulation patterns
# Statistical analysis examples
```

## 📊 Application Portfolio

### **Web Applications**
- **Flask Dashboards** - Real-time monitoring and visualization
- **Audio Transcription** - Live speech-to-text with dual inputs
- **Keylogger Analysis** - Typing pattern visualization
- **Screen OCR** - Screen capture with GPT analysis

### **Desktop Applications**
- **Browser Overlay** - Transparent, always-on-top browsers
- **Audio Tools** - System-level audio processing
- **File Management** - Intelligent synchronization and organization

### **Development Tools**
- **Sync Toolkit** - Rule-based file synchronization
- **Environment Setup** - Automated development environment configuration
- **Testing Utilities** - Interview preparation and coding challenges

## 🧪 Testing & Quality

```bash
# Comprehensive testing approach
python -m pytest apps/                  # Unit tests
./compare_folders.sh --test             # Script validation
python sync_by_rules.py --dry-run       # Safe execution testing

# LLVM compatibility testing (for whisper applications)
cd whisperer_internal
./launch_flask_on5000_whisperer_internal.sh --test
# Verifies LLVM 20 installation and whisper import

# Code quality standards
# • PEP 8 compliance
# • Comprehensive error handling
# • Logging and monitoring
# • Documentation coverage
# • LLVM version compatibility checks
```

## 📈 Performance Characteristics

| Application | Resource Usage | Real-time Capable | Production Ready | LLVM Compatibility |
|-------------|----------------|-------------------|------------------|-------------------|
| Whisperer Internal | Medium CPU, Low RAM | ✅ Yes | ✅ Yes | ✅ LLVM 20 |
| Whisperer External | Medium CPU, Medium RAM | ✅ Yes | ✅ Yes | ✅ LLVM 20 |
| Browser Overlay | Low CPU/GPU | ✅ Yes | ✅ Yes | ❌ Not required |
| Keylogger Tools | Low CPU/RAM | ✅ Real-time | ✅ Yes | ❌ Not required |
| Sync Tools | Low CPU, Variable I/O | ❌ Batch | ✅ Yes | ❌ Not required |

## 🎓 Learning Resources

This repository also serves as a learning portfolio:

- **Coding Challenges** - Interview preparation exercises
- **Algorithm Implementations** - Common patterns and solutions
- **Project Documentation** - Real-world application examples
- **Development Workflows** - Professional practices demonstrated
- **LLVM Compatibility** - System library version management

## 🔄 Recent Updates

### **✅ Fixed Issues:**
1. **LLVM 21 → 20 Compatibility** - Resolved llvmlite installation failures
2. **Deployment Script Improvements** - Added LLVM version management
3. **Fallback Mechanisms** - Automatic switch to faster-whisper if needed
4. **Environment Variable Handling** - Proper LLVM_CONFIG settings

### **🆕 New Features:**
1. **Automated LLVM Management** - Scripts handle LLVM version conflicts
2. **Enhanced Error Recovery** - Graceful degradation options
3. **Better Logging** - Structured log files in `logs/` directory
4. **PID Management** - Proper process tracking and cleanup

### **📋 Known Issues & Solutions:**
- **Issue**: `llvmlite` fails with LLVM 21
- **Solution**: Script automatically installs LLVM 20 and sets environment
- **Fallback**: Uses `faster-whisper` if llvmlite installation fails
- **Prevention**: Checks for LLVM 21 and removes it before installation

## 🤝 Contributing

This repository demonstrates real-world problem-solving:
- **System Compatibility** - Handling LLVM version conflicts
- **Production Deployment** - Robust installation scripts
- **Error Recovery** - Graceful degradation patterns
- **Documentation** - Clear troubleshooting guides

For issues or improvements, please reference the specific application directory and include:
1. System information (macOS version, Python version)
2. LLVM version (`llvm-config --version`)
3. Error messages from logs
4. Steps to reproduce

## 📜 License

MIT License - see LICENSE file for details.