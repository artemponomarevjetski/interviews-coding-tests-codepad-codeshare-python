# Interview Coding Tests & Development Toolkit

A comprehensive collection of coding tests, interview assignments, and practical development tools for technical interviews and daily programming tasks.

## 📁 Project Structure

### 📝 Core Interview Materials
- **Coding Tests** - Python solutions for technical interviews
- **SQL & Python Questions** - Database and programming challenges  
- **Algorithm Problems** - Data structures and algorithms
- **Web Scraping** - Data extraction and processing scripts

### 🛠️ Development Tools

#### 🔄 File Synchronization Toolkit
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

#### 📊 Analysis & Utilities
- `compare_folders.sh` - Folder comparison tools
- `folder-sizes.sh` - Disk usage analysis
- `dedupe_suffixes.py` - File deduplication
- `move_up.sh` - File organization utilities

### 🗂️ Key Directories

- `assesments/` - Coding assessment solutions
- `flask/` - Web application projects
- `overlay/` - Browser overlay utilities
- `whisperer_external/` & `whisperer_internal/` - AI integration projects
- `chatterbox/` - Chat application prototypes
- `png/` - Documentation screenshots

### 🚀 Quick Start

1. **Environment Setup:**
   ```bash
   ./env-setup.sh
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run Tests:**
   ```bash
   python ex1.py  # Example test execution
   python brackets.py  # Algorithm challenges
   ```

3. **Use Sync Toolkit:**
   ```bash
   make dry-run    # Preview changes
   make apply      # Apply synchronization
   ```

### 📋 Featured Code Samples

- **Data Structures:** `cdll.py` (Circular Doubly Linked List)
- **Algorithms:** `tree.py`, `atoi.ipynb`
- **Web Development:** `app.py`, `desklog.py`
- **Data Analysis:** `lidar-test.py`, `heart.csv` processing

### 🔧 Requirements

- Python 3.8+
- Bash shell
- Common Unix utilities