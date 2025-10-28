#!/usr/bin/env python3
"""
Screen OCR + Python Puzzle Solver with Start/Stop Control
"""

import os
import platform
import shutil
import socket
import subprocess
import time
from datetime import datetime
from threading import Thread, Lock

from flask import Flask, render_template_string, send_file
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
    "gpt_control": "gpt_control.txt",  # New file for control state
    "port": 5000,
    "interval": 45,
    "retain": 20,
    "tesseract": None,
    "openai_model": "gpt-3.5-turbo",
}
os.makedirs(CONFIG["save_dir"], exist_ok=True)
os.makedirs(CONFIG["log_dir"], exist_ok=True)

# Global control variable with thread lock
gpt_analysis_enabled = True  # Default: START (enabled)
control_lock = Lock()

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    path = os.path.join(CONFIG["log_dir"], CONFIG["log_file"])
    with open(path, "a") as fh:
        fh.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")

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
    log("✅ GPT features enabled")
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
                    log("📴 GPT analysis control: STOPPED (loaded from file)")
                else:
                    gpt_analysis_enabled = True
                    log("🟢 GPT analysis control: STARTED (loaded from file)")
        else:
            # Default state: enabled
            gpt_analysis_enabled = True
            save_gpt_control_state()
            log("🟢 GPT analysis control: STARTED (default)")
    except Exception as e:
        log(f"❌ Error loading control state: {e}")
        gpt_analysis_enabled = True  # Default to enabled on error

def save_gpt_control_state():
    """Save current GPT control state to file"""
    control_path = os.path.join(CONFIG["save_dir"], CONFIG["gpt_control"])
    try:
        with open(control_path, 'w') as f:
            f.write('stop' if not gpt_analysis_enabled else 'start')
    except Exception as e:
        log(f"❌ Error saving control state: {e}")

def start_gpt_analysis():
    """Start GPT analysis"""
    global gpt_analysis_enabled
    with control_lock:
        gpt_analysis_enabled = True
        save_gpt_control_state()
        log("🟢 GPT analysis STARTED")

def stop_gpt_analysis():
    """Stop GPT analysis"""
    global gpt_analysis_enabled
    with control_lock:
        gpt_analysis_enabled = False
        save_gpt_control_state()
        log("📴 GPT analysis STOPPED")

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

# GPT API function
def send_to_gpt_api(ocr_text: str) -> str:
    if not ocr_text.strip():
        return "No text extracted from image"
    
    if not gpt_enabled:
        return "GPT analysis unavailable"
    
    max_retries = 2
    for attempt in range(max_retries):
        try:
            truncated_text = ocr_text[:2500]
            
            prompt = f"""solve Python puzzle

TASK: Analyze the screenshot text below and solve any Python programming problems you find.

SCREENSHOT TEXT:
{truncated_text}

INSTRUCTIONS:
1. If this contains Python code, programming challenges, or coding problems:
   - PROVIDE THE COMPLETE WORKING SOLUTION
   - EXPLAIN the approach and logic
   - INCLUDE code examples

2. If this contains other technical content:
   - PROVIDE detailed analysis and solutions
   - EXPLAIN key concepts
   - OFFER practical advice

3. For general content:
   - SUMMARIZE the main points
   - EXTRACT key information
   - HIGHLIGHT important details

RESPONSE FORMAT:
- Start with "SOLUTION:" if solving a coding problem
- Use clear headings and code blocks
- Be comprehensive but concise"""

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            data = {
                "model": CONFIG["openai_model"],
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are an expert Python developer and problem solver. Your primary task is to solve Python puzzles and programming challenges. When you see code, provide complete working solutions with explanations. Always respond with detailed, actionable answers."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "max_tokens": 800,
                "temperature": 0.1
            }
            
            log(f"📨 Sending request to GPT API (attempt {attempt + 1})...")
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis = result["choices"][0]["message"]["content"].strip()
                log(f"✅ GPT analysis SUCCESS: {len(analysis)} characters")
                return analysis
                
            elif response.status_code == 429:
                wait_time = 120
                log(f"⏳ Rate limited (429), waiting {wait_time}s")
                time.sleep(wait_time)
                continue
                
            else:
                log(f"❌ GPT API error {response.status_code}: {response.text}")
                return f"API Error {response.status_code}. Will retry later."
            
        except requests.exceptions.Timeout:
            log(f"❌ GPT API timeout (attempt {attempt + 1})")
            time.sleep(30)
            continue
            
        except Exception as e:
            log(f"❌ GPT API error: {e}")
            time.sleep(30)
            continue
    
    return "GPT analysis failed after retries. Waiting before next attempt."

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

# Worker thread
def worker():
    last_gpt_success = True
    gpt_call_count = 0
    
    while True:
        shot = capture_snapshot()
        if not shot:
            log("❌ Screenshot failed")
            time.sleep(CONFIG["interval"])
            continue

        txt = extract_text(shot)
        
        if txt:
            with open(os.path.join(CONFIG["save_dir"], CONFIG["ocr_txt"]), "w") as f:
                f.write(txt)
            
            # Check if GPT analysis is enabled
            if is_gpt_analysis_enabled():
                # Only call GPT every 3rd cycle or if we have good text
                should_call_gpt = (gpt_call_count % 3 == 0) or (len(txt) > 200 and "python" in txt.lower())
                
                if should_call_gpt and last_gpt_success:
                    log("🎯 Calling GPT with Python puzzle solver...")
                    gpt_analysis = send_to_gpt_api(txt)
                    
                    if gpt_analysis and not any(error in gpt_analysis.lower() for error in ["rate limit", "429", "error", "failed"]):
                        last_gpt_success = True
                        with open(os.path.join(CONFIG["save_dir"], CONFIG["gpt_analysis"]), "w") as f:
                            f.write(gpt_analysis)
                        log("💾 GPT analysis saved successfully")
                    else:
                        last_gpt_success = False
                        log("🚫 GPT analysis failed or rate limited")
                    
                    gpt_call_count += 1
                else:
                    log(f"⏸️ GPT cooldown: {gpt_call_count % 3} cycles remaining")
                    gpt_call_count += 1
            else:
                log("⏸️ GPT analysis is currently STOPPED")
                gpt_call_count += 1
                    
            log(f"📸 OCR extracted {len(txt)} characters")
        else:
            log("📸 No text extracted")

        maintain_latest_symlink(shot)
        time.sleep(CONFIG["interval"])

# Flask UI with control buttons
TPL = """
<!doctype html>
<title>Python Puzzle Solver</title>
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
.btn-start{background:#28a745;color:#fff}
.btn-stop{background:#dc3545;color:#fff}
.btn:disabled{opacity:0.6;cursor:not-allowed}
pre{background:#f5f5f5;padding:15px;border-radius:6px;white-space:pre-wrap;max-height:60vh;overflow-y:auto;border:1px solid #ddd;font-family:monospace}
.imgwrap{text-align:center;margin-top:20px}
.imgwrap img{max-width:100%;border:1px solid #ddd;border-radius:4px}
.python-mode{background:#e8f4fd;border-left:4px solid #2196f3;color:#0d47a1;padding:15px;border-radius:6px;margin:15px 0}
.started-mode{background:#d4edda;border-left:4px solid #28a745;color:#155724;padding:15px;border-radius:6px;margin:15px 0}
.stopped-mode{background:#f8d7da;border-left:4px solid #dc3545;color:#721c24;padding:15px;border-radius:6px;margin:15px 0}
.warning{background:#fff3cd;border-left:4px solid #ffc107;color:#856404;padding:15px;border-radius:6px;margin:15px 0}
.error{background:#f8d7da;border-left:4px solid #dc3545;color:#721c24;padding:15px;border-radius:6px;margin:15px 0}
.control-status{margin:10px 0;font-weight:600}
</style>

<div class="container">
  <h1>🐍 Python Puzzle Solver</h1>
  <div class="meta">Last updated: {{ts}} | Status: <span class="status">{{status}}</span></div>

  <div class="controls">
    <button class="btn btn-copy" onclick="copyAllText()">Copy All Text</button>
    <button class="btn btn-refresh" onclick="location.reload()">Refresh</button>
    {% if gpt_enabled %}
      {% if gpt_analysis_enabled %}
        <button class="btn btn-stop" onclick="stopAnalysis()">⏹️ Stop GPT Analysis</button>
        <button class="btn btn-start" disabled>▶️ GPT Analysis Running</button>
      {% else %}
        <button class="btn btn-stop" disabled>⏹️ GPT Analysis Stopped</button>
        <button class="btn btn-start" onclick="startAnalysis()">▶️ Start GPT Analysis</button>
      {% endif %}
    {% endif %}
  </div>

  {% if gpt_enabled %}
    {% if gpt_analysis_enabled %}
    <div class="started-mode">
      <h3>🟢 GPT ANALYSIS: RUNNING</h3>
      <p><strong>Primary Instruction:</strong> "solve Python puzzle"</p>
      <p><strong>Model:</strong> {{gpt_model}} | <strong>Interval:</strong> {{interval}}s</p>
      <p><strong>Mode:</strong> Actively solving coding problems and providing solutions</p>
    </div>
    {% else %}
    <div class="stopped-mode">
      <h3>🔴 GPT ANALYSIS: STOPPED</h3>
      <p>GPT analysis is currently paused. Screenshots and OCR will continue working.</p>
      <p>Click "Start GPT Analysis" to resume AI-powered puzzle solving.</p>
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
    <div class="python-mode">
      <h3>✅ Python Puzzle Solution:</h3>
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
  <div class="section">
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
  
  if (gptText) fullText += '🐍 PYTHON PUZZLE SOLUTION:\n' + gptText.textContent + '\n\n';
  if (ocrText) fullText += '📄 RAW OCR TEXT:\n' + ocrText.textContent;
  
  navigator.clipboard.writeText(fullText).then(() => {
    alert('All text copied to clipboard!');
  });
}

function startAnalysis() {
  fetch('/start_gpt', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        location.reload();
      } else {
        alert('Error starting GPT analysis: ' + data.error);
      }
    })
    .catch(error => {
      alert('Error starting GPT analysis: ' + error);
    });
}

function stopAnalysis() {
  fetch('/stop_gpt', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        location.reload();
      } else {
        alert('Error stopping GPT analysis: ' + data.error);
      }
    })
    .catch(error => {
      alert('Error stopping GPT analysis: ' + error);
    });
}
</script>
"""

app = Flask(__name__)

@app.route("/")
def dashboard():
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
        rand=int(time.time())
    )

@app.route("/latest_image")
def latest_image():
    path = os.path.join(CONFIG["save_dir"], CONFIG["latest"])
    return send_file(path, mimetype="image/png") if os.path.exists(path) else ("No image", 404)

@app.route("/start_gpt", methods=["POST"])
def start_gpt():
    try:
        start_gpt_analysis()
        return {"success": True, "message": "GPT analysis started"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route("/stop_gpt", methods=["POST"])
def stop_gpt():
    try:
        stop_gpt_analysis()
        return {"success": True, "message": "GPT analysis stopped"}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Load control state on startup
    load_gpt_control_state()
    
    Thread(target=worker, daemon=True).start()
    ip = socket.gethostbyname(socket.gethostname()) or "localhost"
    log(f"🚀 Python Puzzle Solver Started")
    log(f"📊 Dashboard: http://{ip}:{CONFIG['port']}")
    log(f"⏰ Interval: {CONFIG['interval']} seconds")
    if gpt_enabled:
        log(f"🧠 Model: {CONFIG['openai_model']}")
        log("🎯 PRIMARY TASK: 'solve Python puzzle'")
        log(f"🔄 GPT Analysis: {'STARTED' if is_gpt_analysis_enabled() else 'STOPPED'}")
        log("🎛️ Controls: Use Start/Stop buttons in dashboard")
    app.run(host="0.0.0.0", port=CONFIG["port"], debug=False)
