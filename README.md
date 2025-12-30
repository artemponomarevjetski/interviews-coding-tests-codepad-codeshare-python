# 🚀 Python Development Portfolio

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3%2B-green)](https://flask.palletsprojects.com/)
[![Bash](https://img.shields.io/badge/Bash-Scripting-4EAA25)](https://www.gnu.org/software/bash/)
[![Production-Ready](https://img.shields.io/badge/Production--Ready-Yes-success)]()
[![License](https://img.shields.io/badge/License-MIT-yellow)]()

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
│   │   │   ├── whisperer_internal/ # Internal audio transcription
│   │   │   ├── whisperer_external/ # External audio transcription
│   │   │   ├── avatar/             # Voice cloning systems
│   │   │   └── image-to-gpt/       # Visual analysis tools
│   │   ├── keylogger/        # Keylogger analysis and visualization tools
│   │   ├── overlay/          # Browser overlay and transparency tools
│   │   ├── chatterbox/       # Chat/communication applications
│   │   └── assesments/       # Assessment and testing tools
│   │
│   ├── whisperer_external/   # Dual audio transcription (mic + system audio)
│   ├── whisperer_internal/   # Internal audio transcription systems
│   └── lidar/                # LiDAR data processing applications
│
├── 🔧 Development Tools
│   ├── sync_by_rules.py      # Intelligent file synchronization tool
│   ├── dedupe_suffixes.py    # File deduplication with suffix management
│   ├── move_up.sh           # File organization automation
│   ├── compare_folders.sh   # Folder comparison utilities
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
# • whisperer_internal/ - Internal audio transcription
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
├── whisperer_internal/ # Internal audio processing
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

# Test assets (tracked):
test-snapshot/     # Tracked test images and assets
demo/              # Demonstration files
examples/          # Example data and configurations

# Best Practices:
# 1. Use 'test-snapshot/' for test images you want to track
# 2. Use 'temp/' for runtime files you don't want in git
# 3. Keep production code separate from test/demo code
```

### **Audio Processing Pipeline**

```python
# whisperer_external/whisperer-external.py
def get_audio_devices():
    """Intelligent device detection for dual audio capture"""
    # Auto-detects external microphone
    # Auto-detects BlackHole for system audio
    # Fallback mechanisms for robustness

def start_dual_transcription():
    """Multi-threaded audio processing"""
    # Thread 1: Microphone capture
    # Thread 2: System audio capture  
    # Thread 3: Whisper AI transcription
    # Thread 4: Web interface updates
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
cd whisperer_external && ./launch-flask-on5000-whisperer-external.sh
# OR test Flask demo:
cd apps/flasks/flask-test && python app.py
# OR
cd apps/overlay && python browser-overlay.py
# OR
cd apps/keylogger && python web_dashboard.py
```

### **System Requirements**

- **Python 3.8+** with virtual environment support
- **macOS** (optimized, but cross-platform compatible)
- **Audio devices** for transcription applications
- **BlackHole 2ch** (for system audio capture - optional)
- **Homebrew** (for package management on macOS)

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

# Code quality standards
# • PEP 8 compliance
# • Comprehensive error handling
# • Logging and monitoring
# • Documentation coverage
```

## 🎓 Learning Resources

This repository also serves as a learning portfolio:

- **Coding Challenges** - Interview preparation exercises
- **Algorithm Implementations** - Common patterns and solutions
- **Project Documentation** - Real-world application examples
- **Development Workflows** - Professional practices demonstrated

## 📈 Performance Characteristics

| Application | Resource Usage | Real-time Capable | Production Ready |
|-------------|----------------|-------------------|------------------|
| Whisperer | Medium CPU, Low RAM | ✅ Yes | ✅ Yes |
| Browser Overlay | Low CPU/GPU | ✅ Yes | ✅ Yes |
| Keylogger Tools | Low CPU/RAM | ✅ Real-time | ✅ Yes |
| Sync Tools | Low CPU, Variable I/O | ❌ Batch | ✅ Yes |