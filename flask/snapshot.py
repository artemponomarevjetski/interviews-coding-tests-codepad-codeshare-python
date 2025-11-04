#!/usr/bin/env python3
"""
Screen OCR + Content Analyzer
- Automatic snapshots with timestamps
- Manual refresh for immediate capture
- Aggregate conversation log
- Auto-GPT when content changes (in GPT mode)
- Manual prompts (in GPT mode)
- Auto-balance updates (in GPT mode)
"""

import os
import platform
import shutil
import socket
import subprocess
import time
import signal
import sys
import psutil
from datetime import datetime
from threading import Thread, Lock
import json

from flask import Flask, render_template_string, send_file, jsonify
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import requests

# Configuration
BASE = os.path.expanduser("~/interviews-coding-tests-codepad-codeshare-python")
CONFIG = {
    "save_dir": f"{BASE}/temp",
    "log_dir": f"{BASE}/log", 
    "log_file": "snapshot.log",
    "aggregate_log": "aggregate_conversation.txt",
    "latest": "snap_latest.png",
    "ocr_txt": "snapshot.txt",
    "gpt_analysis": "gpt_analysis.txt",
    "port": 5000,
    "interval": 10,
    "gpt_interval": 20,
    "balance_interval": 600,
    "retain": 50,
    "tesseract": None,
    "openai_model": "gpt-4o",
}
os.makedirs(CONFIG["save_dir"], exist_ok=True)
os.makedirs(CONFIG["log_dir"], exist_ok=True)

# Global control variables
worker_running = True
app_running = True
control_lock = Lock()
last_api_call_time = None
last_api_content_preview = ""
total_api_cost = 0.0
current_balance = None
api_key = None
last_text_hash = ""
conversation_history = []
last_manual_capture_time = 0

mode = os.environ.get('GPT_MODE', 'no-gpt').lower()
GPT_MODE = mode if mode in ['gpt', 'no-gpt'] else 'no-gpt'  # Validate like shell script

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    path = os.path.join(CONFIG["log_dir"], CONFIG["log_file"])
    with open(path, "a") as fh:
        fh.write(f"[{ts}] {msg}\n")
        fh.flush()
    print(f"[{ts}] {msg}")

def log_conversation(role: str, content: str, content_type: str = "text"):
    """Log to aggregate conversation file"""
    global conversation_history
    
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conversation_entry = {
        "timestamp": ts,
        "role": role,
        "content": content,
        "type": content_type
    }
    
    # Add to in-memory history (keep last 100 entries)
    conversation_history.append(conversation_entry)
    if len(conversation_history) > 100:
        conversation_history.pop(0)
    
    # Append to file
    aggregate_path = os.path.join(CONFIG["log_dir"], CONFIG["aggregate_log"])
    try:
        with open(aggregate_path, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"🕒 {ts} | {role.upper()} | {content_type.upper()}\n")
            f.write(f"{'='*80}\n")
            f.write(f"{content}\n")
    except Exception as e:
        log(f"❌ Error writing to aggregate log: {e}")

# Load API key - only if in GPT mode
def load_api_key_from_env_file():
    """Load OpenAI API key from .env file"""
    if GPT_MODE != 'gpt':
        return None
        
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(env_path):
        return None
    try:
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('OPENAI_API_KEY='):
                    key = line.split('=', 1)[1].strip().strip('"\'')
                    if key:
                        log(f"✅ API key loaded from .env file: {key[:10]}...{key[-5:]}")
                        return key
        return None
    except Exception as e:
        log(f"❌ Error reading .env: {e}")
        return None

# Initialize API key based on mode
api_key = load_api_key_from_env_file()
gpt_enabled = api_key is not None and GPT_MODE == 'gpt'

if GPT_MODE == 'gpt':
    if gpt_enabled:
        log("✅ GPT-4 features enabled")
    else:
        log("⚠️ GPT mode requested but no API key found")
else:
    log("📝 OCR-ONLY mode: GPT features disabled")

# Balance functions - only in GPT mode
def get_balance_from_api():
    """Get current OpenAI balance from API or use fallback"""
    global current_balance, api_key
    
    if not api_key or GPT_MODE != 'gpt':
        log("⚠️ No API key available or OCR-only mode, using fallback balance")
        return "$9.40"
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        # Try to get billing information
        response = requests.get(
            "https://api.openai.com/dashboard/billing/credit_grants",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            billing_data = response.json()
            total_granted = billing_data.get('total_granted', 0)
            total_used = billing_data.get('total_used', 0)
            remaining = total_granted - total_used
            new_balance = f"${remaining:.2f}"
            log(f"💰 Balance from billing API: {new_balance}")
            return new_balance
        else:
            log(f"⚠️ Could not fetch balance from API (Status: {response.status_code}), using fallback")
            return "$9.40"
                
    except Exception as e:
        log(f"⚠️ Balance API error: {e}, using fallback")
        return "$9.40"

def get_openai_balance():
    """Get current OpenAI balance - returns string value"""
    global current_balance
    return current_balance if GPT_MODE == 'gpt' else "N/A (OCR-only mode)"

def get_openai_pricing():
    """Get current OpenAI pricing information"""
    pricing = {
        "gpt-4o": {"input": 0.005, "output": 0.015},      # $5/$15 per 1M tokens
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},   # $10/$30 per 1M tokens
        "gpt-4": {"input": 0.03, "output": 0.06},         # $30/$60 per 1M tokens
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
    }
    return pricing.get(CONFIG["openai_model"], pricing["gpt-4o"])

def estimate_cost(text):
    """Estimate cost for processing text"""
    if GPT_MODE != 'gpt':
        return 0.0
    pricing = get_openai_pricing()
    estimated_tokens = len(text) / 4
    cost = (estimated_tokens / 1000) * pricing["input"]
    return max(0.01, cost)

def get_estimated_requests():
    """Calculate estimated remaining GPT-4 requests"""
    if GPT_MODE != 'gpt':
        return 0
    try:
        balance_clean = current_balance.replace('$', '').strip()
        balance_float = float(balance_clean)
        pricing = get_openai_pricing()
        avg_cost_per_call = 0.03
        estimated = int(balance_float / avg_cost_per_call)
        return max(0, estimated)
    except:
        return 300

def get_python_processes():
    """Get current Python processes in the system"""
    try:
        python_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
            try:
                if 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    memory_mb = proc.info['memory_info'].rss / 1024 / 1024 if proc.info['memory_info'] else 0
                    
                    python_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmdline': cmdline[:200] + '...' if len(cmdline) > 200 else cmdline,
                        'memory_mb': round(memory_mb, 1)
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        python_processes.sort(key=lambda x: x['memory_mb'], reverse=True)
        return python_processes
    except Exception as e:
        return [{'error': f'Failed to get processes: {str(e)}'}]

def get_system_info():
    """Get system information"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_used = memory.used / 1024 / 1024 / 1024
        memory_total = memory.total / 1024 / 1024 / 1024
        memory_percent = memory.percent
        disk = psutil.disk_usage('.')
        disk_used = disk.used / 1024 / 1024 / 1024
        disk_total = disk.total / 1024 / 1024 / 1024
        disk_percent = disk.percent
        
        return {
            'cpu_percent': round(cpu_percent, 1),
            'memory_used_gb': round(memory_used, 1),
            'memory_total_gb': round(memory_total, 1),
            'memory_percent': round(memory_percent, 1),
            'disk_used_gb': round(disk_used, 1),
            'disk_total_gb': round(disk_total, 1),
            'disk_percent': round(disk_percent, 1)
        }
    except Exception as e:
        return {'error': f'Failed to get system info: {str(e)}'}

def detect_tesseract():
    if CONFIG["tesseract"]:
        return True
    for p in ("/opt/homebrew/bin/tesseract", "/usr/local/bin/tesseract", 
              "/usr/bin/tesseract", shutil.which("tesseract")):
        if p and os.path.exists(p):
            CONFIG["tesseract"] = p
            pytesseract.pytesseract.tesseract_cmd = p
            return True
    return False

def maintain_latest_symlink(new_img):
    link = os.path.join(CONFIG["save_dir"], CONFIG["latest"])
    try:
        if os.path.islink(link) or os.path.exists(link):
            os.unlink(link)
        os.symlink(new_img, link)
    except OSError:
        shutil.copy2(new_img, link)
    shots = sorted(f for f in os.listdir(CONFIG["save_dir"])
                   if f.startswith("snap_") and f.endswith(".png"))
    while len(shots) > CONFIG["retain"]:
        os.remove(os.path.join(CONFIG["save_dir"], shots.pop(0)))

def instant_capture():
    """Take an immediate screenshot and process it"""
    log("🎯 INSTANT CAPTURE: Manual refresh requested")
    shot = capture_snapshot()
    if not shot:
        log("❌ INSTANT CAPTURE: Failed to capture screenshot")
        return None, None
    
    txt = extract_text(shot)
    if txt:
        with open(os.path.join(CONFIG["save_dir"], CONFIG["ocr_txt"]), "w") as f:
            f.write(txt)
        maintain_latest_symlink(shot)
        log(f"✅ INSTANT CAPTURE: Success! {len(txt)} characters extracted")
        return shot, txt
    else:
        log("📸 INSTANT CAPTURE: No text extracted")
        maintain_latest_symlink(shot)
        return shot, None

def capture_snapshot():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    img = os.path.join(CONFIG["save_dir"], f"snap_{ts}.png")
    cmds = [
        ["screencapture", "-x", "-l", "-o", img],
        ["screencapture", "-x", "-m", "-o", img], 
        ["screencapture", "-x", "-o", img],
    ]
    for cmd in cmds:
        try:
            subprocess.run(cmd, check=True, timeout=5, capture_output=True)
            if os.path.getsize(img) > 0:
                return img
        except Exception:
            pass
    if os.path.exists(img):
        os.remove(img)
    return None

def _prep_for_ocr(img):
    img = img.convert("L")
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = img.filter(ImageFilter.SHARPEN)
    return img.point(lambda x: 0 if x < 140 else 255)

def extract_text(path):
    if not detect_tesseract():
        return ""
    text = ""
    try:
        prepped = _prep_for_ocr(Image.open(path))
        for cfg in ("--oem 3 --psm 6", "--oem 3 --psm 11"):
            t = pytesseract.image_to_string(prepped, config=cfg)
            if len(t) > len(text):
                text = t
    except Exception as e:
        log(f"❌ OCR error: {e}")
    return text.strip()

def send_to_gpt_api(ocr_text: str, auto_mode: bool = False) -> str:
    """Send text to GPT API - only works in GPT mode"""
    global last_api_call_time, last_api_content_preview, total_api_cost, current_balance
    
    if not ocr_text.strip():
        return "No text extracted from image"
    
    if not gpt_enabled or GPT_MODE != 'gpt':
        return "GPT analysis unavailable (OCR-only mode)"
    
    try:
        truncated_text = ocr_text[:2500]
        last_api_content_preview = truncated_text[:100] + "..." if len(truncated_text) > 100 else truncated_text
        last_api_call_time = datetime.now()
        
        # Estimate cost before making the call
        estimated_cost = estimate_cost(truncated_text)
        content_type = "Python code/technical content" if any(keyword in ocr_text.lower() for keyword in ["python", "def ", "import ", "function", "code"]) else "general content"
        
        mode_label = "AUTO" if auto_mode else "MANUAL"
        log(f"📤 {mode_label} PROMPT TO GPT-4: {len(ocr_text)} chars of {content_type} (est. cost: ${estimated_cost:.3f})")
        
        # Log input to conversation
        log_conversation("user", truncated_text, "screenshot_ocr")
        
        prompt = f"""
SCREENSHOT CONTENT:
{truncated_text}

TASK: Analyze this content and provide helpful analysis or solutions.

If this contains:
- Python code → Provide complete working solution with explanation
- Technical questions → Explain concepts and provide correct answers  
- General content → Summarize and analyze key points

RESPONSE FORMAT:
- Start with "ANALYSIS:" or "SOLUTION:"
- Use clear headings and code blocks where appropriate
- Provide explanations and context"""

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "model": CONFIG["openai_model"],
            "messages": [
                {
                    "role": "system", 
                    "content": "You are a helpful technical assistant. Analyze the provided content and provide useful solutions, explanations, or summaries as appropriate."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": 1200,
            "temperature": 0.1
        }
        
        log(f"📨 Sending prompt to GPT-4 API...")
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            analysis = result["choices"][0]["message"]["content"].strip()
            
            # Calculate actual cost from response
            usage = result.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            pricing = get_openai_pricing()
            actual_cost = (input_tokens / 1000 * pricing["input"]) + (output_tokens / 1000 * pricing["output"])
            total_api_cost += actual_cost
            
            # Update balance
            try:
                balance_clean = current_balance.replace('$', '').strip()
                balance_float = float(balance_clean)
                new_balance = max(0.0, balance_float - actual_cost)
                current_balance = f"${new_balance:.2f}"
                log(f"💰 Balance updated: ${balance_float:.2f} → {current_balance}")
            except Exception as e:
                log(f"⚠️ Error updating balance: {e}")
            
            # Log response to conversation
            log_conversation("assistant", analysis, "gpt_analysis")
            
            log(f"✅ GPT-4 analysis SUCCESS: {len(analysis)} characters (Cost: ${actual_cost:.3f}, Total: ${total_api_cost:.3f})")
            return analysis
            
        else:
            error_msg = f"API Error {response.status_code}"
            if response.status_code == 429:
                error_msg += " - Rate limit exceeded. Please wait and try again."
            elif response.status_code == 401:
                error_msg += " - Invalid API key. Please check your .env file."
            elif response.status_code == 402:
                error_msg += " - Insufficient credits. Please check your balance."
            
            log(f"❌ GPT-4 API error {response.status_code}: {response.text}")
            return f"{error_msg}. Please try again."
        
    except Exception as e:
        log(f"❌ GPT-4 API error: {e}")
        return f"API Error: {e}. Please try again."

def balance_updater():
    """Update balance automatically every 10 minutes - only in GPT mode"""
    while worker_running:
        try:
            time.sleep(CONFIG["balance_interval"])
            if worker_running and GPT_MODE == 'gpt':
                global current_balance
                new_balance = get_balance_from_api()
                current_balance = new_balance
                log(f"🔄 AUTO-BALANCE UPDATE: {new_balance}")
        except Exception as e:
            log(f"❌ Auto-balance update error: {e}")

def worker():
    global last_text_hash
    last_gpt_call_time = 0
    
    while worker_running:
        shot = capture_snapshot()
        if not shot:
            if worker_running:
                time.sleep(CONFIG["interval"])
            continue

        txt = extract_text(shot)
        current_hash = hash(txt) if txt else ""
        
        if txt:
            with open(os.path.join(CONFIG["save_dir"], CONFIG["ocr_txt"]), "w") as f:
                f.write(txt)
            
            # Log OCR text to conversation
            log_conversation("system", f"OCR extracted {len(txt)} characters", "ocr_result")
            
            # AUTO-GPT: Only in GPT mode
            current_time = time.time()
            if (current_hash != last_text_hash and 
                gpt_enabled and GPT_MODE == 'gpt' and
                (current_time - last_gpt_call_time) >= CONFIG["gpt_interval"]):
                
                log("🎯 AUTO-GPT: Content changed, sending to GPT-4...")
                gpt_analysis = send_to_gpt_api(txt, auto_mode=True)
                
                if gpt_analysis and not gpt_analysis.startswith("API Error"):
                    with open(os.path.join(CONFIG["save_dir"], CONFIG["gpt_analysis"]), "w") as f:
                        f.write(gpt_analysis)
                    last_gpt_call_time = current_time
                
                last_text_hash = current_hash
            
            if worker_running:
                mode_info = "GPT" if GPT_MODE == 'gpt' else "OCR-ONLY"
                log(f"📸 {mode_info} CAPTURE: {len(txt)} characters | Next in {CONFIG['interval']}s")
        else:
            if worker_running:
                log("📸 AUTO-CAPTURE: No text extracted")

        if worker_running:
            maintain_latest_symlink(shot)
            time.sleep(CONFIG["interval"])
    
    log("👋 Worker thread stopped")

def kill_python_process():
    """Simple and reliable process termination"""
    try:
        current_pid = os.getpid()
        log(f"💀 AUTO-KILL: Terminating process PID {current_pid}")
        
        # Stop all threads
        global worker_running, app_running
        worker_running = False
        app_running = False
        
        # Force exit immediately
        log("💀 Process terminated")
        os._exit(0)
        
    except Exception as e:
        log(f"❌ Kill error: {e}")
        os._exit(1)

# Flask UI - Mode-aware template
TPL = """
<!doctype html>
<title>Content Analyzer - {{ "GPT" if gpt_mode == "gpt" else "OCR-ONLY" }} Mode</title>
<style>
body{font-family:Inter,Arial,sans-serif;background:#f8f9fa;margin:20px}
.container{max-width:1200px;background:#fff;border-radius:8px;padding:20px;margin:auto;box-shadow:0 2px 10px rgba(0,0,0,.1)}
h1{margin-top:0}
.meta{color:#666;font-size:.9em;margin-bottom:15px}
.status{display:inline-block;padding:4px 10px;border-radius:4px;font-weight:600;color:#fff;background:#4caf50}
.controls{margin:15px 0;display:flex;gap:10px;flex-wrap:wrap}
.btn{padding:8px 15px;border:0;border-radius:4px;cursor:pointer;font-weight:600;text-decoration:none}
.btn-copy{background:#4caf50;color:#fff}
.btn-refresh{background:#2196f3;color:#fff}
.btn-instant{background:#ff6b00;color:#fff}
.btn-prompt{background:#28a745;color:#fff}
.btn-billing{background:#6f42c1;color:#fff}
.btn:disabled{opacity:0.6;cursor:not-allowed}
.btn:hover:not(:disabled){opacity:0.9;transform:translateY(-1px)}
pre{background:#f5f5f5;padding:15px;border-radius:6px;white-space:pre-wrap;max-height:60vh;overflow-y:auto;border:1px solid #ddd;font-family:monospace}
.imgwrap{text-align:center;margin-top:20px}
.imgwrap img{max-width:100%;border:1px solid #ddd;border-radius:4px}
.balance-info{background:#d4edda;border-left:4px solid #28a745;color:#155724;padding:15px;border-radius:6px;margin:15px 0}
.system-info{background:#e2e3e5;border-left:4px solid #6c757d;color:#383d41;padding:15px;border-radius:6px;margin:15px 0}
.process-info{background:#fff3cd;border-left:4px solid #ffc107;color:#856404;padding:15px;border-radius:6px;margin:15px 0}
.warning{background:#fff3cd;border-left:4px solid #ffc107;color:#856404;padding:15px;border-radius:6px;margin:15px 0}
.error{background:#f8d7da;border-left:4px solid #dc3545;color:#721c24;padding:15px;border-radius:6px;margin:15px 0}
.success{background:#d4edda;border-left:4px solid #28a745;color:#155724;padding:15px;border-radius:6px;margin:15px 0}
.process-table{width:100%;border-collapse:collapse;margin:10px 0}
.process-table th, .process-table td{padding:8px;text-align:left;border-bottom:1px solid #ddd}
.process-table th{background:#f8f9fa;font-weight:600}
.process-table tr:hover{background:#f5f5f5}
.process-table .cmd-cell{max-width:400px;word-wrap:break-word;word-break:break-all;white-space:normal;font-family:monospace;font-size:0.8em}
.system-stats{display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:15px;margin:15px 0}
.stat-box{background:#f8f9fa;padding:15px;border-radius:6px;text-align:center;border:1px solid #e9ecef}
.stat-value{font-size:1.5em;font-weight:bold;color:#007bff}
.stat-label{font-size:0.9em;color:#6c757d;margin-top:5px}
.api-status{background:#e7f3ff;border-left:4px solid #2196f3;color:#0c5460;padding:10px;border-radius:6px;margin:10px 0;font-size:0.9em}
.gpt-ready{background:#d4edda;border-left:4px solid #28a745;color:#155724;padding:15px;border-radius:6px;margin:15px 0}
.cost-info{background:#fff3cd;border-left:4px solid #ffc107;color:#856404;padding:10px;border-radius:6px;margin:10px 0;font-size:0.9em}
.auto-mode{background:#fff3cd;border-left:4px solid #ff9800;color:#e65100;padding:10px;border-radius:6px;margin:10px 0;font-size:0.9em}
.instant-mode{background:#ffebee;border-left:4px solid #ff6b00;color:#c62828;padding:10px;border-radius:6px;margin:10px 0;font-size:0.9em}
.mode-indicator {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 4px;
    font-weight: 600;
    color: #fff;
    margin-left: 10px;
}
.mode-gpt { background: #28a745; }
.mode-ocr { background: #6c757d; }
</style>

<div class="container">
  <h1>Content Analyzer 
    <span class="mode-indicator {{ 'mode-gpt' if gpt_mode == 'gpt' else 'mode-ocr' }}">
      {{ "GPT MODE" if gpt_mode == "gpt" else "OCR-ONLY MODE" }}
    </span>
  </h1>
  <div class="meta">Last updated: {{ts}} | Status: <span class="status">{{status}}</span></div>

  <!-- CONTROLS -->
  <div class="controls">
    <button class="btn btn-copy" onclick="copyAllText()">Copy All Text</button>
    <button class="btn btn-refresh" onclick="location.reload()">Refresh Page</button>
    <button class="btn btn-instant" onclick="instantCapture()" id="instantBtn">📸 INSTANT Capture</button>
    {% if gpt_mode == "gpt" %}
    <button class="btn btn-prompt" onclick="sendPrompt()" id="promptBtn">🚀 INSTANT GPT Prompt</button>
    <a href="https://platform.openai.com/account/billing" target="_blank" class="btn btn-billing">💰 Check Usage</a>
    {% endif %}
  </div>

  {% if last_manual_capture %}
  <div class="instant-mode">
    <h3>🎯 INSTANT CAPTURE ACTIVE</h3>
    <p><strong>Last manual capture:</strong> {{last_manual_capture}}</p>
    <p><em>New screenshot captured instantly! Refresh page to see latest.</em></p>
  </div>
  {% endif %}

  {% if gpt_mode == "gpt" %}
  <!-- Balance Information (GPT mode only) -->
  <div class="balance-info">
    <h3>💰 OpenAI Balance: {{balance}}</h3>
    <p><em>GPT-4: ~$0.03 per 1K tokens | Screenshots/OCR: Free</em></p>
    <p><strong>Remaining credits:</strong> {{balance}} (enough for ~{{estimated_requests}} GPT-4 requests)</p>
    {% if total_cost > 0 %}
    <div class="cost-info">
      <strong>Session API Cost:</strong> ${{ "%.3f"|format(total_cost) }}
    </div>
    {% endif %}
  </div>

  {% if gpt_enabled %}
  <div class="gpt-ready">
    <h3>🟢 GPT-4 READY</h3>
    <p><strong>Model:</strong> {{gpt_model}} | <strong>Cost:</strong> ~$0.03 per analysis</p>
    <p><strong>Last Analysis:</strong> {{last_api_time}}</p>
    <p><strong>Last Content:</strong> {{last_content_preview}}</p>
    {% if auto_gpt_active %}
    <div class="auto-mode">
      <strong>🔄 AUTO-GPT ACTIVE:</strong> Analyzing content changes every {{gpt_interval}} seconds
    </div>
    {% endif %}
  </div>
  {% else %}
  <div class="warning">
    <h3>⚠️ GPT Analysis Disabled</h3>
    <p>OpenAI API key not found in .env file</p>
  </div>
  {% endif %}
  {% else %}
  <!-- OCR-only mode info -->
  <div class="system-info">
    <h3>📝 OCR-ONLY MODE</h3>
    <p>GPT analysis is disabled. Only screenshot capture and OCR are active.</p>
    <p>Run with <code>./launch-flask-on5000.sh gpt</code> to enable GPT features.</p>
  </div>
  {% endif %}

  <!-- System Information -->
  <div class="system-info">
    <h3>🖥️ System Information</h3>
    <div class="system-stats">
      <div class="stat-box">
        <div class="stat-value">{{system_info.cpu_percent}}%</div>
        <div class="stat-label">CPU Usage</div>
      </div>
      <div class="stat-box">
        <div class="stat-value">{{system_info.memory_used_gb}}/{{system_info.memory_total_gb}} GB</div>
        <div class="stat-label">Memory ({{system_info.memory_percent}}%)</div>
      </div>
      <div class="stat-box">
        <div class="stat-value">{{system_info.disk_used_gb}}/{{system_info.disk_total_gb}} GB</div>
        <div class="stat-label">Disk ({{system_info.disk_percent}}%)</div>
      </div>
    </div>
  </div>

  <!-- Python Processes -->
  <div class="process-info">
    <h3>🐍 Current Python Processes ({{python_processes|length}})</h3>
    {% if python_processes and python_processes[0] is mapping %}
    <table class="process-table">
      <thead>
        <tr>
          <th>PID</th>
          <th>Process</th>
          <th>Memory</th>
          <th>Command</th>
        </tr>
      </thead>
      <tbody>
        {% for proc in python_processes %}
        <tr>
          <td><code>{{proc.pid}}</code></td>
          <td><strong>{{proc.name}}</strong></td>
          <td>{{proc.memory_mb}} MB</td>
          <td class="cmd-cell"><small>{{proc.cmdline}}</small></td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    {% else %}
    <p>No Python processes found or error retrieving process information.</p>
    {% endif %}
  </div>

  {% if gpt_analysis %}
    {% if "error" in gpt_analysis.lower() or "429" in gpt_analysis %}
    <div class="error">
      <h3>❌ Analysis Failed</h3>
      <pre id="gptAnalysis">{{gpt_analysis}}</pre>
    </div>
    {% else %}
    <div class="success">
      <h3>✅ GPT-4 Analysis Result:</h3>
      <pre id="gptAnalysis">{{gpt_analysis}}</pre>
    </div>
    {% endif %}
  {% endif %}

  {% if image %}
  <div class="imgwrap">
    <h3>📸 Latest Screenshot:</h3>
    <img src="/latest_image?{{rand}}" alt="Latest screenshot">
  </div>
  {% endif %}

  {% if text %}
  <div class="system-info">
    <h3>📄 Raw OCR Text:</h3>
    <pre id="ocrText">{{text|safe}}</pre>
  </div>
  {% endif %}
</div>

<script>
function copyAllText(){ 
    const ocrText = document.getElementById('ocrText');
    let fullText = '';
    
    if (ocrText && ocrText.textContent.trim()) {
        const rawText = ocrText.textContent.trim();
        const decodedText = decodeHtmlEntities(rawText);
        fullText = '📄 RAW OCR TEXT FROM SCREENSHOT:\n' + decodedText;
        
        navigator.clipboard.writeText(fullText).then(() => {
            showNotification('✅ OCR text copied to clipboard!', 'success');
        }).catch(err => {
            const textArea = document.createElement('textarea');
            textArea.value = fullText;
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                showNotification('✅ OCR text copied to clipboard!', 'success');
            } catch (fallbackErr) {
                showNotification('❌ Failed to copy text', 'error');
            }
            document.body.removeChild(textArea);
        });
    } else {
        showNotification('❌ No OCR text available to copy!', 'error');
    }
}

function decodeHtmlEntities(html) {
    const textArea = document.createElement('textarea');
    textArea.innerHTML = html;
    return textArea.value;
}

function instantCapture() {
    const button = document.getElementById('instantBtn');
    button.disabled = true;
    button.innerHTML = '📸 Capturing NOW...';
    
    fetch('/instant_capture', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('✅ Screenshot captured INSTANTLY! Refreshing...', 'success');
            setTimeout(() => location.reload(), 500);
        } else {
            showNotification('❌ Capture failed: ' + data.error, 'error');
            button.disabled = false;
            button.innerHTML = '📸 INSTANT Capture';
        }
    })
    .catch(error => {
        showNotification('❌ Error: ' + error, 'error');
        button.disabled = false;
        button.innerHTML = '📸 INSTANT Capture';
    });
}

{% if gpt_mode == "gpt" %}
function sendPrompt() {
    const button = document.getElementById('promptBtn');
    button.disabled = true;
    button.innerHTML = '⚡ Sending INSTANTLY...';
    
    fetch('/manual_prompt', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('✅ GPT-4 analysis completed INSTANTLY! Refreshing...', 'success');
            setTimeout(() => location.reload(), 500);
        } else {
            showNotification('❌ Analysis failed: ' + data.error, 'error');
            button.disabled = false;
            button.innerHTML = '🚀 INSTANT GPT Prompt';
        }
    })
    .catch(error => {
        showNotification('❌ Error: ' + error, 'error');
        button.disabled = false;
        button.innerHTML = '🚀 INSTANT GPT Prompt';
    });
}
{% endif %}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 6px;
        color: white;
        font-weight: bold;
        z-index: 10000;
        background: ${type === 'success' ? '#28a745' : '#dc3545'};
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}
</script>
"""

app = Flask(__name__)

last_manual_capture_time = 0

@app.route("/")
def dashboard():
    if not app_running:
        return "Application is shutting down...", 503
    
    txt_path = os.path.join(CONFIG["save_dir"], CONFIG["ocr_txt"])
    gpt_path = os.path.join(CONFIG["save_dir"], CONFIG["gpt_analysis"])
    
    text = ""
    gpt_analysis = ""
    
    try:
        if os.path.exists(txt_path):
            with open(txt_path, "r") as f:
                text = f.read()
    except: pass
        
    try:
        if os.path.exists(gpt_path):
            with open(gpt_path, "r") as f:
                gpt_analysis = f.read()
    except: pass
    
    latest_img_exists = os.path.exists(os.path.join(CONFIG["save_dir"], CONFIG["latest"]))
    
    # Get additional information
    balance = get_openai_balance()
    python_processes = get_python_processes()
    system_info = get_system_info()
    estimated_requests = get_estimated_requests()
    
    # Format last API call time
    last_api_time = "Never" if last_api_call_time is None else last_api_call_time.strftime("%Y-%m-%d %H:%M:%S")
    last_content_preview = last_api_content_preview if last_api_content_preview else "No content analyzed yet"
    
    # Format last manual capture time
    last_manual_capture = "Never" if last_manual_capture_time == 0 else datetime.fromtimestamp(last_manual_capture_time).strftime("%Y-%m-%d %H:%M:%S")
    
    return render_template_string(
        TPL,
        ts=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        status="success" if text or gpt_analysis else "waiting",
        text=text,
        gpt_analysis=gpt_analysis,
        gpt_enabled=gpt_enabled,
        gpt_mode=GPT_MODE,
        gpt_model=CONFIG["openai_model"],
        interval=CONFIG["interval"],
        gpt_interval=CONFIG["gpt_interval"],
        image=latest_img_exists,
        balance=balance,
        python_processes=python_processes,
        system_info=system_info,
        estimated_requests=estimated_requests,
        last_api_time=last_api_time,
        last_content_preview=last_content_preview,
        total_cost=total_api_cost,
        auto_gpt_active=gpt_enabled and GPT_MODE == 'gpt',
        last_manual_capture=last_manual_capture,
        rand=int(time.time())
    )

@app.route("/latest_image")
def latest_image():
    if not app_running:
        return "Application is shutting down...", 503
    path = os.path.join(CONFIG["save_dir"], CONFIG["latest"])
    if os.path.exists(path):
        response = send_file(path, mimetype="image/png")
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    return ("No image", 404)

@app.route("/instant_capture", methods=["POST"])
def instant_capture_endpoint():
    """Take an immediate screenshot when user clicks INSTANT Capture"""
    global last_manual_capture_time
    try:
        shot, txt = instant_capture()
        if shot:
            last_manual_capture_time = time.time()
            return jsonify({
                "success": True, 
                "message": f"Screenshot captured instantly! {len(txt) if txt else 0} characters extracted",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        else:
            return jsonify({"success": False, "error": "Failed to capture screenshot"})
        
    except Exception as e:
        log(f"❌ Instant capture error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/manual_prompt", methods=["POST"])
def manual_prompt():
    """Manual prompt endpoint - sends current OCR text to GPT-4 INSTANTLY (GPT mode only)"""
    if GPT_MODE != 'gpt':
        return jsonify({"success": False, "error": "GPT features are disabled in OCR-only mode"})
        
    try:
        txt_path = os.path.join(CONFIG["save_dir"], CONFIG["ocr_txt"])
        if not os.path.exists(txt_path):
            return jsonify({"success": False, "error": "No OCR text available. Wait for a screenshot first."})
        
        with open(txt_path, "r") as f:
            ocr_text = f.read()
        
        if not ocr_text.strip():
            return jsonify({"success": False, "error": "No text in current screenshot."})
        
        log("🚀 INSTANT MANUAL PROMPT: User clicked 'Send Prompt to GPT Now'")
        gpt_analysis = send_to_gpt_api(ocr_text, auto_mode=False)
        
        # Save the analysis
        with open(os.path.join(CONFIG["save_dir"], CONFIG["gpt_analysis"]), "w") as f:
            f.write(gpt_analysis)
        
        return jsonify({"success": True, "message": "Analysis completed INSTANTLY"})
        
    except Exception as e:
        log(f"❌ Manual prompt error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/health")
def health():
    return jsonify({"status": "running", "app_running": app_running, "gpt_mode": GPT_MODE})

if __name__ == "__main__":
    # Install psutil if not available
    try:
        import psutil
    except ImportError:
        log("📦 Installing psutil for system monitoring...")
        subprocess.run([sys.executable, "-m", "pip", "install", "psutil"], check=True)
        import psutil
    
    # Initialize balance only in GPT mode
    if GPT_MODE == 'gpt':
        current_balance = get_balance_from_api()
    else:
        current_balance = "N/A"
    
    # Start all threads
    Thread(target=worker, daemon=True).start()
    if GPT_MODE == 'gpt':
        Thread(target=balance_updater, daemon=True).start()
    
    ip = socket.gethostbyname(socket.gethostname()) or "localhost"
    log(f"🚀 Content Analyzer Started - {GPT_MODE.upper()} MODE")
    log(f"📊 Dashboard: http://{ip}:{CONFIG['port']}")
    
    if GPT_MODE == 'gpt':
        log(f"💰 OpenAI Balance: {get_openai_balance()}")
        log("🎯 Auto-GPT: Enabled")
    else:
        log("📝 OCR-ONLY: GPT features disabled")
    
    try:
        app.run(host="0.0.0.0", port=CONFIG["port"], debug=False, threaded=True)
    except KeyboardInterrupt:
        log("👋 Application stopped by user")
    finally:
        worker_running = False
        log("👋 Application shutdown complete")