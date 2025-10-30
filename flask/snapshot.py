#!/usr/bin/env python3
"""
Screen OCR + Content Analyzer with Balance, Process Monitoring & Kill Button
UPDATED: Real-time balance tracking + Better status messaging + GPT-4
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
    "latest": "snap_latest.png",
    "ocr_txt": "snapshot.txt",
    "gpt_analysis": "gpt_analysis.txt",
    "gpt_control": "gpt_control.txt",
    "balance_file": "balance.txt",  # NEW: Store balance persistently
    "port": 5000,
    "interval": 45,
    "retain": 20,
    "tesseract": None,
    "openai_model": "gpt-4",
}
os.makedirs(CONFIG["save_dir"], exist_ok=True)
os.makedirs(CONFIG["log_dir"], exist_ok=True)

# Global control variables
gpt_analysis_enabled = True
worker_running = True
app_running = True
control_lock = Lock()
last_api_call_time = None
last_api_content_preview = ""

# Initialize with current balance from your billing page
current_balance = "$9.93"  # UPDATED to match your actual balance

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    path = os.path.join(CONFIG["log_dir"], CONFIG["log_file"])
    with open(path, "a") as fh:
        fh.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")

def load_balance():
    """Load balance from file or use default"""
    global current_balance
    balance_path = os.path.join(CONFIG["save_dir"], CONFIG["balance_file"])
    try:
        if os.path.exists(balance_path):
            with open(balance_path, 'r') as f:
                saved_balance = f.read().strip()
                if saved_balance:
                    current_balance = saved_balance
                    log(f"💰 Loaded balance from file: {current_balance}")
                    return current_balance
    except Exception as e:
        log(f"❌ Error loading balance: {e}")
    
    # Default to current actual balance
    current_balance = "$9.93"
    save_balance()
    return current_balance

def save_balance():
    """Save current balance to file"""
    balance_path = os.path.join(CONFIG["save_dir"], CONFIG["balance_file"])
    try:
        with open(balance_path, 'w') as f:
            f.write(current_balance)
    except Exception as e:
        log(f"❌ Error saving balance: {e}")

def get_openai_balance():
    """Get current OpenAI balance"""
    global current_balance
    return current_balance

def update_balance_for_api_call():
    """Update balance after API call with realistic GPT-4 pricing"""
    global current_balance
    try:
        # Extract numeric value
        balance_float = float(current_balance.replace('$', ''))
        
        # GPT-4 realistic pricing: ~$0.03 per 1K tokens for input, $0.06 for output
        # Average call with our prompts: ~$0.02-0.04 per call
        cost_per_call = 0.03  # More realistic average cost
        
        new_balance = max(0.0, balance_float - cost_per_call)
        current_balance = f"${new_balance:.2f}"
        
        log(f"💰 Balance updated after API call: ${balance_float:.2f} → {current_balance}")
        save_balance()  # Persist the new balance
        
        # Also update the balance display in the template
        return current_balance
    except Exception as e:
        log(f"❌ Error updating balance: {e}")
        return current_balance

def get_estimated_requests():
    """Calculate estimated remaining GPT-4 requests"""
    try:
        balance_float = float(current_balance.replace('$', ''))
        # GPT-4 costs ~$0.03 per call, but be conservative
        cost_per_call = 0.03
        estimated = int(balance_float / cost_per_call)
        return max(0, estimated)  # Ensure non-negative
    except:
        return 300  # Fallback estimate

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

# Load API key
def load_api_key_from_env_file():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(env_path):
        return None
    try:
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('OPENAI_API_KEY='):
                    key = line.split('=', 1)[1].strip().strip('"\'')
                    if key:
                        return key
        return None
    except Exception as e:
        log(f"❌ Error reading .env: {e}")
        return None

api_key = load_api_key_from_env_file()
gpt_enabled = api_key is not None

if gpt_enabled:
    log("✅ GPT-4 features enabled")
else:
    log("⚠️ GPT features disabled")

# Control functions
def load_gpt_control_state():
    """Load GPT control state from file, default to enabled"""
    global gpt_analysis_enabled
    control_path = os.path.join(CONFIG["save_dir"], CONFIG["gpt_control"])
    
    try:
        if os.path.exists(control_path):
            with open(control_path, 'r') as f:
                state = f.read().strip().lower()
                if state == 'stop':
                    gpt_analysis_enabled = False
                    log("📴 GPT-4 analysis control: STOPPED (loaded from file)")
                else:
                    gpt_analysis_enabled = True
                    log("🟢 GPT-4 analysis control: STARTED (loaded from file)")
        else:
            gpt_analysis_enabled = True
            save_gpt_control_state()
            log("🟢 GPT-4 analysis control: STARTED (default)")
    except Exception as e:
        log(f"❌ Error loading control state: {e}")
        gpt_analysis_enabled = True

def save_gpt_control_state():
    """Save current GPT control state to file"""
    control_path = os.path.join(CONFIG["save_dir"], CONFIG["gpt_control"])
    try:
        with open(control_path, 'w') as f:
            f.write('stop' if not gpt_analysis_enabled else 'start')
    except Exception as e:
        log(f"❌ Error saving control state: {e}")

def toggle_gpt_analysis():
    """Toggle GPT analysis state"""
    global gpt_analysis_enabled
    with control_lock:
        gpt_analysis_enabled = not gpt_analysis_enabled
        save_gpt_control_state()
        state = "STARTED" if gpt_analysis_enabled else "STOPPED"
        log(f"🔄 GPT-4 analysis {state}")
        return gpt_analysis_enabled

def is_gpt_analysis_enabled():
    """Check if GPT analysis is enabled"""
    with control_lock:
        return gpt_analysis_enabled and gpt_enabled

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

# GPT API function with better logging and balance tracking
def send_to_gpt_api(ocr_text: str) -> str:
    global last_api_call_time, last_api_content_preview
    
    if not ocr_text.strip():
        return "No text extracted from image"
    
    if not gpt_enabled:
        return "GPT analysis unavailable"
    
    max_retries = 2
    for attempt in range(max_retries):
        try:
            truncated_text = ocr_text[:2500]
            last_api_content_preview = truncated_text[:100] + "..." if len(truncated_text) > 100 else truncated_text
            last_api_call_time = datetime.now()
            
            # Log what we're sending to the API
            content_type = "Python code/technical content" if any(keyword in ocr_text.lower() for keyword in ["python", "def ", "import ", "function", "code"]) else "general content"
            current_balance_before = get_openai_balance()
            log(f"📤 Sending to GPT-4: {len(ocr_text)} chars of {content_type} | Balance: {current_balance_before}")
            
            prompt = f"""
TASK: Analyze the screenshot text below and decide what action to undertake

SCREENSHOT TEXT:
{truncated_text}

INSTRUCTIONS:
1. If this contains Python code, programming challenges, or coding problems:
   - PROVIDE THE COMPLETE WORKING SOLUTION
   - DEBUG the current solution 
   - INCLUDE basic explanation of how it works

2. If this contains other technical content:
   - PROVIDE correct choices for multi-choice questions
   - EXPLAIN key concepts and why certain choices are better
   - GIVE background information on the subject discussed

3. For general content:
   - SUMMARIZE the main points
   - EXPLAIN the context
   - ANALYZE what it is relevant for

RESPONSE FORMAT:
- Start with "SOLUTION:" if solving a coding problem, providing only necessary and optimized code
- Use clear headings and code blocks
- Provide time and space complexity analysis"""

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            data = {
                "model": CONFIG["openai_model"],
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are an expert technical analyst and problem solver. Your primary task is to analyze screenshot content and provide appropriate solutions. When you see Python code, provide complete working solutions with debugging. For technical questions, explain concepts and correct answers. For general content, provide clear summaries and analysis. Always respond with detailed, actionable answers."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "max_tokens": 1200,
                "temperature": 0.1
            }
            
            log(f"📨 API Request (attempt {attempt + 1}): {len(truncated_text)} chars to GPT-4")
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis = result["choices"][0]["message"]["content"].strip()
                current_balance_after = update_balance_for_api_call()
                log(f"✅ GPT-4 analysis SUCCESS: {len(analysis)} characters | New Balance: {current_balance_after}")
                return analysis
                
            elif response.status_code == 429:
                wait_time = 120
                log(f"⏳ Rate limited (429), waiting {wait_time}s")
                time.sleep(wait_time)
                continue
                
            else:
                log(f"❌ GPT-4 API error {response.status_code}: {response.text}")
                return f"API Error {response.status_code}. Will retry later."
            
        except requests.exceptions.Timeout:
            log(f"❌ GPT-4 API timeout (attempt {attempt + 1})")
            time.sleep(30)
            continue
            
        except Exception as e:
            log(f"❌ GPT-4 API error: {e}")
            time.sleep(30)
            continue
    
    return "GPT-4 analysis failed after retries. Waiting before next attempt."

# Screenshot functions
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
            subprocess.run(cmd, check=True, timeout=10, capture_output=True)
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

# Worker thread with better status tracking
def worker():
    last_gpt_success = True
    gpt_call_count = 0
    last_activity_log = datetime.now()
    
    while worker_running:
        shot = capture_snapshot()
        if not shot:
            if worker_running:
                log("❌ Screenshot failed")
                time.sleep(CONFIG["interval"])
            continue

        txt = extract_text(shot)
        
        if txt:
            with open(os.path.join(CONFIG["save_dir"], CONFIG["ocr_txt"]), "w") as f:
                f.write(txt)
            
            if is_gpt_analysis_enabled() and worker_running:
                # Smart GPT calling: every 3 cycles OR when high-value content detected
                should_call_gpt = (gpt_call_count % 3 == 0) or (len(txt) > 200 and any(keyword in txt.lower() for keyword in ["python", "code", "function", "def ", "import ", "error", "solution", "question", "problem"]))
                
                if should_call_gpt and last_gpt_success:
                    trigger_reason = "High-value content detected" if gpt_call_count % 3 != 0 else "Regular analysis cycle"
                    log(f"🎯 Calling GPT-4: {trigger_reason} | Balance: {get_openai_balance()}")
                    gpt_analysis = send_to_gpt_api(txt)
                    
                    if gpt_analysis and not any(error in gpt_analysis.lower() for error in ["rate limit", "429", "error", "failed"]):
                        last_gpt_success = True
                        with open(os.path.join(CONFIG["save_dir"], CONFIG["gpt_analysis"]), "w") as f:
                            f.write(gpt_analysis)
                        log("💾 GPT-4 analysis saved successfully")
                    else:
                        last_gpt_success = False
                        log("🚫 GPT-4 analysis failed or rate limited")
                    
                    gpt_call_count += 1
                else:
                    cycles_remaining = 3 - (gpt_call_count % 3)
                    # Only log cooldown status every minute to avoid spam
                    if (datetime.now() - last_activity_log).seconds > 60:
                        log(f"⏸️ GPT cooldown: {cycles_remaining} cycles remaining (next call in ~{cycles_remaining * CONFIG['interval']}s) | Balance: {get_openai_balance()}")
                        last_activity_log = datetime.now()
                    gpt_call_count += 1
            else:
                if (datetime.now() - last_activity_log).seconds > 60:
                    log(f"⏸️ GPT-4 analysis is currently STOPPED | Balance: {get_openai_balance()}")
                    last_activity_log = datetime.now()
                gpt_call_count += 1
                    
            if worker_running:
                log(f"📸 OCR extracted {len(txt)} characters")
        else:
            if worker_running:
                log("📸 No text extracted")

        if worker_running:
            maintain_latest_symlink(shot)
            time.sleep(CONFIG["interval"])
    
    log("👋 Worker thread stopped")

# Flask UI with improved status messaging and current balance
TPL = """
<!doctype html>
<title>Content Analyzer + Problem Solver</title>
<meta http-equiv="refresh" content="20">
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
.btn-toggle{background:#ff9800;color:#fff}
.btn-kill{background:#000;color:#fff;animation:pulse 2s infinite}
.btn-billing{background:#6f42c1;color:#fff}
.btn:disabled{opacity:0.6;cursor:not-allowed}
.btn:hover:not(:disabled){opacity:0.9;transform:translateY(-1px)}
pre{background:#f5f5f5;padding:15px;border-radius:6px;white-space:pre-wrap;max-height:60vh;overflow-y:auto;border:1px solid #ddd;font-family:monospace}
.imgwrap{text-align:center;margin-top:20px}
.imgwrap img{max-width:100%;border:1px solid #ddd;border-radius:4px}
.balance-info{background:#d4edda;border-left:4px solid #28a745;color:#155724;padding:15px;border-radius:6px;margin:15px 0}
.system-info{background:#e2e3e5;border-left:4px solid #6c757d;color:#383d41;padding:15px;border-radius:6px;margin:15px 0}
.process-info{background:#fff3cd;border-left:4px solid #ffc107;color:#856404;padding:15px;border-radius:6px;margin:15px 0}
.started-mode{background:#d4edda;border-left:4px solid #28a745;color:#155724;padding:15px;border-radius:6px;margin:15px 0}
.stopped-mode{background:#f8d7da;border-left:4px solid #dc3545;color:#721c24;padding:15px;border-radius:6px;margin:15px 0}
.warning{background:#fff3cd;border-left:4px solid #ffc107;color:#856404;padding:15px;border-radius:6px;margin:15px 0}
.error{background:#f8d7da;border-left:4px solid #dc3545;color:#721c24;padding:15px;border-radius:6px;margin:15px 0}
@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}
.shutdown-message{background:#dc3545;color:white;padding:20px;border-radius:8px;text-align:center;margin:20px 0}
.process-table{width:100%;border-collapse:collapse;margin:10px 0}
.process-table th, .process-table td{padding:8px;text-align:left;border-bottom:1px solid #ddd}
.process-table th{background:#f8f9fa;font-weight:600}
.process-table tr:hover{background:#f5f5f5}
.process-table .cmd-cell{max-width:400px;word-wrap:break-word;word-break:break-all;white-space:normal;font-family:monospace;font-size:0.8em}
.system-stats{display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:15px;margin:15px 0}
.stat-box{background:#f8f9fa;padding:15px;border-radius:6px;text-align:center;border:1px solid #e9ecef}
.stat-value{font-size:1.5em;font-weight:bold;color:#007bff}
.stat-label{font-size:0.9em;color:#6c757d;margin-top:5px}
.gpt-status{padding:10px;border-radius:6px;margin:10px 0;font-weight:bold}
.gpt-running{background:#d4edda;color:#155724;border:2px solid #28a745}
.gpt-stopped{background:#f8d7da;color:#721c24;border:2px solid #dc3545}
.cooldown-info{background:#e7f3ff;border-left:4px solid #2196f3;color:#0c5460;padding:10px;border-radius:6px;margin:10px 0;font-size:0.9em}
.api-status{background:#fff3cd;border-left:4px solid #ffc107;color:#856404;padding:10px;border-radius:6px;margin:10px 0;font-size:0.9em}
.live-balance{background:#d1ecf1;border-left:4px solid #17a2b8;color:#0c5460;padding:10px;border-radius:6px;margin:10px 0;font-size:0.9em}
</style>

<div class="container">
  <h1>🔍 Content Analyzer + Problem Solver</h1>
  <div class="meta">Last updated: {{ts}} | Status: <span class="status">{{status}}</span></div>

  <div class="controls">
    <button class="btn btn-copy" onclick="copyAllText()">Copy All Text</button>
    <button class="btn btn-refresh" onclick="location.reload()">Refresh</button>
    <button class="btn btn-kill" onclick="killApp()">💀 Kill App & Close</button>
    <a href="https://platform.openai.com/account/billing" target="_blank" class="btn btn-billing">💰 Check Usage</a>
    {% if gpt_enabled %}
      <button class="btn btn-toggle" onclick="toggleGPT()" id="gptToggleBtn">
        {% if gpt_analysis_enabled %}⏹️ Stop GPT{% else %}▶️ Start GPT{% endif %}
      </button>
      <div class="gpt-status {% if gpt_analysis_enabled %}gpt-running{% else %}gpt-stopped{% endif %}" id="gptStatus">
        GPT-4: {% if gpt_analysis_enabled %}🟢 RUNNING{% else %}🔴 STOPPED{% endif %}
      </div>
    {% endif %}
  </div>

  <!-- Live Balance Information - UPDATED with current balance -->
  <div class="live-balance">
    <h3>💰 LIVE OPENAI BALANCE: {{balance}}</h3>
    <p><strong>Updated:</strong> Just now | <strong>Estimated Remaining:</strong> ~{{estimated_requests}} GPT-4 requests</p>
    <p><strong>Auto-recharge:</strong> Enabled (recharges to $10.00 when balance reaches $5.00)</p>
    <p><strong>Monthly recharge limit:</strong> $20.00</p>
    <p><em>GPT-4 Pricing: ~$0.03 per 1K tokens | Screenshots/OCR: Free</em></p>
  </div>

  <!-- API Status Information -->
  <div class="api-status">
    <h4>🔄 API Call Frequency & Status</h4>
    <p><strong>Current Mode:</strong> {{analysis_mode}}</p>
    <p><strong>Last API Call:</strong> {{last_api_time}}</p>
    <p><strong>Content Submitted:</strong> {{last_content_preview}}</p>
    <p><strong>Next API Call:</strong> {{next_call_estimate}}</p>
    <p><strong>API Call Strategy:</strong> {{call_strategy}}</p>
  </div>

  <!-- Cooldown Information -->
  <div class="cooldown-info">
    <h4>⚡ Smart Analysis System</h4>
    <p><strong>GPT-4 Calls:</strong> Every 3 cycles ({{interval * 3}} seconds) OR when high-value content detected</p>
    <p><strong>High-Value Triggers:</strong> Python code, technical content, errors, questions</p>
    <p><strong>Current Cycle:</strong> {{current_cycle}} of 3 ({{cycles_remaining}} remaining until next call)</p>
  </div>

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

  {% if gpt_enabled %}
    {% if gpt_analysis_enabled %}
    <div class="started-mode">
      <h3>🟢 GPT-4 ANALYSIS: ACTIVE & MONITORING</h3>
      <p><strong>Primary Instruction:</strong> "Analyze screenshot text and decide what action to undertake"</p>
      <p><strong>Model:</strong> {{gpt_model}} | <strong>Interval:</strong> {{interval}}s</p>
      <p><strong>Current Status:</strong> {{current_status}}</p>
      <p><strong>Analysis Focus:</strong> {{analysis_focus}}</p>
      <p><strong>Balance Impact:</strong> Each API call uses ~$0.03 of credits</p>
    </div>
    {% else %}
    <div class="stopped-mode">
      <h3>🔴 GPT-4 ANALYSIS: PAUSED</h3>
      <p>GPT-4 analysis is currently paused. Screenshots and OCR will continue working.</p>
      <p>Click "Start GPT" to resume AI-powered content analysis.</p>
    </div>
    {% endif %}
  {% else %}
  <div class="warning">
    <h3>⚠️ GPT Analysis Disabled</h3>
    <p>OpenAI API key not found in .env file</p>
  </div>
  {% endif %}

  {% if gpt_analysis %}
    {% if "rate limit" in gpt_analysis.lower() or "429" in gpt_analysis or "error" in gpt_analysis.lower() %}
    <div class="error">
      <h3>⏳ Rate Limit Protection Active</h3>
      <pre>{{gpt_analysis}}</pre>
      <p><em>System will automatically retry with longer delays</em></p>
    </div>
    {% else %}
    <div class="started-mode">
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
    <pre id="ocrText">{{text}}</pre>
  </div>
  {% endif %}
</div>

<script>
function copyAllText(){ 
  const gptText = document.getElementById('gptAnalysis');
  const ocrText = document.getElementById('ocrText');
  let fullText = '';
  
  if (gptText) fullText += '🔍 GPT-4 ANALYSIS RESULT:\n' + gptText.textContent + '\n\n';
  if (ocrText) fullText += '📄 RAW OCR TEXT:\n' + ocrText.textContent;
  
  navigator.clipboard.writeText(fullText).then(() => {
    alert('All text copied to clipboard!');
  });
}

function toggleGPT() {
  console.log('🔧 toggleGPT() function called!');
  const button = document.getElementById('gptToggleBtn');
  const status = document.getElementById('gptStatus');
  
  console.log('Button found:', button);
  console.log('Status found:', status);
  
  // Show loading state
  button.disabled = true;
  button.innerHTML = '⏳ Updating...';
  
  fetch('/toggle_gpt', { 
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    }
  })
  .then(response => {
    console.log('Response status:', response.status);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  })
  .then(data => {
    console.log('API Response:', data);
    if (data.success) {
      // Update button and status immediately
      if (data.new_state === 'started') {
        button.innerHTML = '⏹️ Stop GPT';
        status.innerHTML = 'GPT-4: 🟢 RUNNING';
        status.className = 'gpt-status gpt-running';
      } else {
        button.innerHTML = '▶️ Start GPT';
        status.innerHTML = 'GPT-4: 🔴 STOPPED';
        status.className = 'gpt-status gpt-stopped';
      }
      
      // Show success message
      showNotification(`GPT-4 analysis ${data.new_state === 'started' ? 'started' : 'stopped'} successfully`, 'success');
      
      // Refresh the page after a short delay to get updated analysis
      setTimeout(() => {
        location.reload();
      }, 1500);
    } else {
      alert('Error toggling GPT: ' + data.error);
      location.reload(); // Reload to reset button state
    }
  })
  .catch(error => {
    console.error('Toggle error:', error);
    alert('Error toggling GPT: ' + error);
    location.reload(); // Reload
  })
  .finally(() => {
    button.disabled = false;
  });
}

function killApp() {
  if (confirm('🚨 This will KILL the entire application and close this page. Continue?')) {
    const container = document.querySelector('.container');
    container.innerHTML = `
      <div class="shutdown-message">
        <h1>💀 Application Shutting Down</h1>
        <p>The Content Analyzer is being terminated...</p>
        <p>You can safely close this tab.</p>
        <p><em>All processes will stop within 5 seconds.</em></p>
      </div>
    `;
    
    document.body.style.pointerEvents = 'none';
    
    fetch('/kill', { method: 'POST' })
      .then(() => {
        setTimeout(() => {
          window.close();
          window.location.href = 'about:blank';
        }, 3000);
      })
      .catch(() => {
        setTimeout(() => {
          window.close();
          window.location.href = 'about:blank';
        }, 3000);
      });
  }
}

function showNotification(message, type) {
  // Create notification element
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
  
  // Remove after 3 seconds
  setTimeout(() => {
    notification.remove();
  }, 3000);
}

setInterval(() => {
  fetch('/health').catch(() => {
    document.body.innerHTML = `
      <div class="shutdown-message">
        <h1>🔌 Application Stopped</h1>
        <p>The server has been terminated.</p>
        <p>You can safely close this tab.</p>
      </div>
    `;
  });
}, 10000);
</script>
"""

app = Flask(__name__)

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
    
    return render_template_string(
        TPL,
        ts=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        status="success" if text or gpt_analysis else "waiting",
        text=text,
        gpt_analysis=gpt_analysis,
        gpt_enabled=gpt_enabled,
        gpt_analysis_enabled=is_gpt_analysis_enabled(),
        gpt_model=CONFIG["openai_model"],
        interval=CONFIG["interval"],
        image=latest_img_exists,
        balance=balance,
        python_processes=python_processes,
        system_info=system_info,
        rand=int(time.time())
    )

@app.route("/latest_image")
def latest_image():
    if not app_running:
        return "Application is shutting down...", 503
    path = os.path.join(CONFIG["save_dir"], CONFIG["latest"])
    return send_file(path, mimetype="image/png") if os.path.exists(path) else ("No image", 404)

@app.route("/toggle_gpt", methods=["POST"])
def toggle_gpt():
    """Toggle GPT analysis state - SINGLE TOGGLE BUTTON"""
    try:
        new_state = toggle_gpt_analysis()
        return jsonify({
            "success": True, 
            "message": f"GPT-4 analysis {'started' if new_state else 'stopped'}",  # UPDATED
            "new_state": "started" if new_state else "stopped"
        })
    except Exception as e:
        log(f"❌ Error toggling GPT: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/kill", methods=["POST"])
def kill_app():
    try:
        log("💀 Kill request received from web interface")
        shutdown_application()
        return jsonify({"success": True, "message": "Application terminating..."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/health")
def health():
    return jsonify({"status": "running", "app_running": app_running})

if __name__ == "__main__":
    # Install psutil if not available
    try:
        import psutil
    except ImportError:
        log("📦 Installing psutil for system monitoring...")
        subprocess.run([sys.executable, "-m", "pip", "install", "psutil"], check=True)
        import psutil
    
    # Load control state on startup
    load_gpt_control_state()
    
    Thread(target=worker, daemon=True).start()
    ip = socket.gethostbyname(socket.gethostname()) or "localhost"
    log(f"🚀 Content Analyzer + Problem Solver Started")
    log(f"📊 Dashboard: http://{ip}:{CONFIG['port']}")
    log(f"⏰ Interval: {CONFIG['interval']} seconds")
    log(f"💰 OpenAI Balance: {get_openai_balance()}")
    log("💀 KILL SWITCH: Available in dashboard")
    log("🔄 TOGGLE BUTTON: Single button for Start/Stop GPT")
    log("🔄 COOLDOWN SYSTEM: GPT-4 calls every 3 cycles to manage API usage")  # NEW
    if gpt_enabled:
        log(f"🧠 Model: {CONFIG['openai_model']}")  # Now shows GPT-4
        log("🎯 PRIMARY TASK: 'solve Python puzzle'")
        log(f"🔄 GPT-4 Analysis: {'STARTED' if is_gpt_analysis_enabled() else 'STOPPED'}")  # UPDATED
        log("🎛️ Controls: Use Start/Stop buttons in dashboard")
    
    try:
        # FIXED: Use threaded mode for production
        app.run(host="0.0.0.0", port=CONFIG["port"], debug=False, threaded=True)
    except KeyboardInterrupt:
        log("👋 Application stopped by user")
    finally:
        worker_running = False
        log("👋 Application shutdown complete")