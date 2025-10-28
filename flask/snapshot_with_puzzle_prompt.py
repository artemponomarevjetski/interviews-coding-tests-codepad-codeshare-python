#!/usr/bin/env python3
"""
Screen OCR + GPT Analysis Dashboard with "solve Python puzzle" prompt
"""
import os
import platform
import shutil
import socket
import subprocess
import time
from datetime import datetime
from threading import Thread

from flask import Flask, render_template_string, send_file
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import requests

# ─────────────────────────── Configuration ────────────────────────────
BASE = os.path.expanduser("~/interviews-coding-tests-codepad-codeshare-python")
CONFIG = {
    "save_dir":  f"{BASE}/temp",
    "log_dir":   f"{BASE}/log",
    "log_file":  "snapshot.log",
    "latest":    "snap_latest.png",
    "ocr_txt":   "snapshot.txt",
    "gpt_analysis": "gpt_analysis.txt",
    "port":      5000,
    "interval":  30,
    "retain":    20,
    "tesseract": None,
    "openai_model": "gpt-3.5-turbo",
}
os.makedirs(CONFIG["save_dir"], exist_ok=True)
os.makedirs(CONFIG["log_dir"],  exist_ok=True)

def log(msg: str) -> None:
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
                line = line.strip()
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
    log("✅ GPT features enabled with API key from .env")
else:
    log("⚠️  GPT features disabled - no API key found")

def detect_tesseract():
    if CONFIG["tesseract"]:
        return True
    for p in ("/opt/homebrew/bin/tesseract",
              "/usr/local/bin/tesseract",
              "/usr/bin/tesseract",
              shutil.which("tesseract")):
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

# ────────────────────────── GPT API with "solve Python puzzle" prompt ───────────────────────
def send_to_gpt_api(ocr_text: str) -> str:
    if not ocr_text.strip():
        return "No text extracted from image"
    
    if not gpt_enabled:
        return "GPT analysis unavailable - no API key provided"
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            truncated_text = ocr_text[:3000]
            
            # MODIFIED PROMPT: Prepend "solve Python puzzle" to the prompt
            prompt = f"""solve Python puzzle

Analyze the following text extracted from a screenshot. This text may be scattered, incomplete, or contain errors from OCR.

Provide:
1. A concise summary of the main content
2. Key insights or notable information  
3. Any actions, tasks, or important details mentioned
4. If this appears to be Python code or a programming problem, provide the solution

Keep your response clear and well-structured.

Extracted text:
{truncated_text}
"""
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            data = {
                "model": CONFIG["openai_model"],
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that analyzes text extracted from screenshots. Provide clear, concise analysis of the content. When you see Python code or programming puzzles, provide solutions."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 400,
                "temperature": 0.3
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=45
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis = result["choices"][0]["message"]["content"].strip()
                log(f"✅ GPT analysis completed: {len(analysis)} characters")
                return analysis
                
            elif response.status_code == 429:
                wait_time = (2 ** attempt) * 30
                log(f"⏳ Rate limited (429), waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                    continue
                else:
                    return "GPT analysis temporarily unavailable due to rate limits. Will retry automatically."
                    
            else:
                log(f"❌ GPT API error: {response.status_code} - {response.text}")
                return f"GPT analysis failed: {response.status_code}"
            
        except requests.exceptions.Timeout:
            log(f"❌ GPT API timeout (attempt {attempt + 1})")
            if attempt < max_retries - 1:
                time.sleep(30)
                continue
            else:
                return "GPT analysis timeout"
                
        except Exception as e:
            log(f"❌ GPT API error: {e}")
            if attempt < max_retries - 1:
                time.sleep(30)
                continue
            else:
                return f"GPT analysis failed: {str(e)}"
    
    return "GPT analysis failed after retries"

# ────────────────────────── Screenshot & OCR functions ───────────────────────
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

# ────────────────────────── Worker thread ───────────────────────────────
def worker():
    last_gpt_success = True
    
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
            
            if gpt_enabled:
                if last_gpt_success or (time.time() % 300 < 30):
                    log("📨 Sending OCR text to GPT API with 'solve Python puzzle' prompt...")
                    gpt_analysis = send_to_gpt_api(txt)
                    
                    if gpt_analysis and "rate limit" not in gpt_analysis.lower() and "429" not in gpt_analysis:
                        last_gpt_success = True
                        with open(os.path.join(CONFIG["save_dir"], CONFIG["gpt_analysis"]), "w") as f:
                            f.write(gpt_analysis)
                        log("✅ GPT analysis completed and saved")
                    else:
                        last_gpt_success = False
                        log("⚠️ GPT analysis skipped due to rate limits")
                else:
                    log("⏸️ GPT analysis paused due to recent rate limits")
                    
            log(f"📸 Snapshot + OCR succeeded ({len(txt)} chars)")
        else:
            log("📸 Snapshot captured – no text recognised")

        maintain_latest_symlink(shot)
        time.sleep(CONFIG["interval"])

# ──────────────────────────── Flask UI ────────────────────────────────
TPL = """
<!doctype html>
<title>Screen OCR + GPT Analysis Dashboard</title>
<meta http-equiv="refresh" content="15">
<style>
body{font-family:Inter,Arial,sans-serif;background:#f8f9fa;margin:20px}
.container{max-width:1200px;background:#fff;border-radius:8px;padding:20px;margin:auto;box-shadow:0 2px 10px rgba(0,0,0,.1)}
h1{margin-top:0}
.meta{color:#666;font-size:.9em;margin-bottom:15px}
.status{display:inline-block;padding:4px 10px;border-radius:4px;font-weight:600;color:#fff;background:#4caf50}
.controls{margin:15px 0;display:flex;gap:10px}
.btn{padding:8px 15px;border:0;border-radius:4px;cursor:pointer;font-weight:600;transition:background .3s}
.btn-copy{background:#4caf50;color:#fff}.btn-copy:hover{background:#43a047}
.btn-refresh{background:#2196f3;color:#fff}.btn-refresh:hover{background:#1976d2}
pre{background:#f5f5f5;padding:15px;border-radius:6px;white-space:pre-wrap;max-height:60vh;overflow-y:auto;border:1px solid #ddd}
.imgwrap{text-align:center;margin-top:20px}
.imgwrap img{max-width:100%;border:1px solid #ddd;border-radius:4px}
.rate-limit{background:#fff3cd;border-left:4px solid #ffc107;color:#856404;padding:15px;border-radius:6px;margin:15px 0}
.success{background:#d4edda;border-left:4px solid #28a745;color:#155724;padding:15px;border-radius:6px;margin:15px 0}
.info{background:#d1ecf1;border-left:4px solid #17a2b8;color:#0c5460;padding:15px;border-radius:6px;margin:15px 0}
.python-mode{background:#e8f4fd;border-left:4px solid #2196f3;color:#0d47a1;padding:15px;border-radius:6px;margin:15px 0}
</style>

<div class="container">
  <h1>Screen OCR + GPT Analysis Dashboard</h1>
  <div class="meta">Last updated: {{ts}} | Status: <span class="status">{{status}}</span></div>

  <div class="controls">
    <button class="btn btn-copy" onclick="copyAllText()">Copy All Text</button>
    <button class="btn btn-refresh" onclick="location.reload()">Refresh</button>
  </div>

  {% if gpt_enabled %}
  <div class="python-mode">
    <h3>🐍 Python Puzzle Solver Mode</h3>
    <p>Using model: {{gpt_model}} | Capture interval: {{interval}} seconds</p>
    <p><strong>Prompt:</strong> "solve Python puzzle" + screen content analysis</p>
    {% if "rate limit" in gpt_analysis.lower() or "429" in gpt_analysis %}
    <p><strong>Note:</strong> Currently handling rate limits - analysis will resume automatically</p>
    {% endif %}
  </div>
  {% else %}
  <div class="info">
    <h3>⚠️ GPT Analysis Disabled</h3>
    <p>OpenAI API key not found in .env file</p>
  </div>
  {% endif %}

  {% if gpt_analysis %}
    {% if "rate limit" in gpt_analysis.lower() or "429" in gpt_analysis %}
    <div class="rate-limit">
      <h3>⏳ GPT Analysis (Rate Limited)</h3>
      <pre>{{gpt_analysis}}</pre>
      <p><small>System will automatically retry. This is normal when starting.</small></p>
    </div>
    {% else %}
    <div class="section">
      <h3>🤖 GPT Analysis (Python Puzzle Mode):</h3>
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
  
  if (gptText) fullText += '🤖 GPT ANALYSIS:\n' + gptText.textContent + '\n\n';
  if (ocrText) fullText += '📄 RAW OCR TEXT:\n' + ocrText.textContent;
  
  navigator.clipboard.writeText(fullText).then(() => {
    alert('All text copied to clipboard!');
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
    except Exception:
        pass
        
    try:
        if os.path.exists(gpt_path):
            with open(gpt_path, "r") as f:
                gpt_analysis = f.read()
    except Exception:
        pass
    
    latest_img_exists = os.path.exists(os.path.join(CONFIG["save_dir"], CONFIG["latest"]))
    
    return render_template_string(
        TPL,
        ts=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        status="success" if text or gpt_analysis else "waiting",
        text=text,
        gpt_analysis=gpt_analysis,
        gpt_enabled=gpt_enabled,
        gpt_model=CONFIG["openai_model"],
        interval=CONFIG["interval"],
        image=latest_img_exists,
        rand=int(time.time())
    )

@app.route("/latest_image")
def latest_image():
    path = os.path.join(CONFIG["save_dir"], CONFIG["latest"])
    return send_file(path, mimetype="image/png") if os.path.exists(path) else ("No image", 404)

if __name__ == "__main__":
    Thread(target=worker, daemon=True).start()
    ip = socket.gethostbyname(socket.gethostname()) or "localhost"
    log(f"🚀 Screen OCR + GPT Analysis Dashboard")
    log(f"📊 Serving on http://{ip}:{CONFIG['port']}")
    log(f"⏰ Capture interval: {CONFIG['interval']} seconds")
    if gpt_enabled:
        log(f"🧠 GPT Model: {CONFIG['openai_model']} - ✅ ENABLED")
        log("🐍 PROMPT MODE: 'solve Python puzzle' + analysis")
        log("💡 Rate limit handling: ACTIVE (automatic retries)")
    app.run(host="0.0.0.0", port=CONFIG["port"], debug=False)
