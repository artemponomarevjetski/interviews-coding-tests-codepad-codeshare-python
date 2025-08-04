#!/usr/bin/env python3
"""
Periodic screen capture ➜ OCR with Tesseract ➜ live Flask dashboard
------------------------------------------------------------------
• macOS‑first (uses `screencapture`, falls back to Quartz)  
• Keeps only the most‑recent N screenshots (configurable)  
• Dashboard auto‑refreshes every 10 s, shows latest image, lets the user
  copy all extracted text with one click / right‑click / Cmd‑C / Ctrl‑C
"""

from __future__ import annotations

import os
import platform
import shutil
import socket
import subprocess
import time
from datetime import datetime
from threading import Thread
from typing import Optional

from flask import Flask, render_template_string, send_file
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

# ─────────────────────────── Configuration ────────────────────────────
BASE = os.path.expanduser("~/interviews-coding-tests-codepad-codeshare-python")
CONFIG = {
    "save_dir":  f"{BASE}/temp",
    "log_dir":   f"{BASE}/log",
    "log_file":  "snapshot.log",
    "latest":    "snap_latest.png",
    "ocr_txt":   "snapshot.txt",
    "port":      5000,
    "interval":  15,          # seconds between captures
    "retain":    20,          # keep N most‑recent screenshots
    "tesseract": None,        # auto‑detected once
}
os.makedirs(CONFIG["save_dir"], exist_ok=True)
os.makedirs(CONFIG["log_dir"],  exist_ok=True)

# ─────────────────────────── Helper utilities ─────────────────────────
def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    path = os.path.join(CONFIG["log_dir"], CONFIG["log_file"])
    with open(path, "a") as fh:
        fh.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")

def detect_tesseract() -> bool:
    """Locate the Tesseract binary once per process."""
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

def maintain_latest_symlink(new_img: str) -> None:
    link = os.path.join(CONFIG["save_dir"], CONFIG["latest"])
    try:
        if os.path.islink(link) or os.path.exists(link):
            os.unlink(link)
        os.symlink(new_img, link)
    except OSError:  # e.g. on non‑Unix FS; fall back to copy
        shutil.copy2(new_img, link)
    # prune old shots
    shots = sorted(f for f in os.listdir(CONFIG["save_dir"])
                   if f.startswith("snap_") and f.endswith(".png"))
    while len(shots) > CONFIG["retain"]:
        os.remove(os.path.join(CONFIG["save_dir"], shots.pop(0)))

# ────────────────────────── Screenshot routines ───────────────────────
def _quartz_capture() -> Optional[str]:
    """macOS Quartz fallback when `screencapture` fails."""
    try:
        from Quartz import (
            CGWindowListCopyWindowInfo, kCGWindowListOptionAll, kCGNullWindowID,
            CGWindowListCreateImage, CGRectInfinite,
            kCGWindowListOptionIncludingWindow, kCGWindowImageBoundsIgnoreFraming,
        )
        onscreen = [w for w in
                    CGWindowListCopyWindowInfo(kCGWindowListOptionAll, kCGNullWindowID)
                    if w.get("kCGWindowIsOnscreen")]
        if not onscreen:
            return None
        win_id = onscreen[0]["kCGWindowNumber"]
        img_ref = CGWindowListCreateImage(
            CGRectInfinite, kCGWindowListOptionIncludingWindow,
            win_id, kCGWindowImageBoundsIgnoreFraming)
        if not img_ref:
            return None
        path = os.path.join(CONFIG["save_dir"],
                            f"snap_quartz_{int(time.time())}.png")
        Image.frombytes("RGBA",
                        (img_ref.getWidth(), img_ref.getHeight()),
                        img_ref.getDataProvider().getData()
                        ).save(path)
        return path
    except Exception as e:
        log(f"Quartz capture failed: {e}")
        return None

def capture_snapshot() -> Optional[str]:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    img = os.path.join(CONFIG["save_dir"], f"snap_{ts}.png")
    cmds = [
        ["screencapture", "-x", "-l", "-o", img],  # active window
        ["screencapture", "-x", "-m", "-o", img],  # main display
        ["screencapture", "-x", "-o", img],        # full screen
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
    return _quartz_capture() if platform.system() == "Darwin" else None

# ───────────────────────── OCR utilities ───────────────────────────────
def _prep_for_ocr(img: Image.Image) -> Image.Image:
    img = img.convert("L")                               # greyscale
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = img.filter(ImageFilter.SHARPEN)
    return img.point(lambda x: 0 if x < 140 else 255)     # threshold

def extract_text(path: str) -> str:
    if not detect_tesseract():
        log("Tesseract not found – OCR skipped")
        return ""
    text = ""
    try:
        prepped = _prep_for_ocr(Image.open(path))
        for cfg in ("--oem 3 --psm 6", "--oem 3 --psm 11", "--oem 3 --psm 4"):
            t = pytesseract.image_to_string(prepped, config=cfg)
            if len(t) > len(text):
                text = t
    except Exception as e:
        log(f"OCR error on {path}: {e}")
    return text.strip()

# ───────────────────────── Worker thread ───────────────────────────────
def worker() -> None:
    while True:
        shot = capture_snapshot()
        if not shot:
            log("Screenshot failed")
            time.sleep(CONFIG["interval"])
            continue

        txt = extract_text(shot)
        if txt:
            with open(os.path.join(CONFIG["save_dir"], CONFIG["ocr_txt"]), "w") as f:
                f.write(txt)
            log("Snapshot + OCR succeeded")
        else:
            log("Snapshot captured – no text recognised")

        maintain_latest_symlink(shot)
        time.sleep(CONFIG["interval"])

# ──────────────────────────── Flask UI  ────────────────────────────────
TPL = """
<!doctype html>
<title>Screen OCR Dashboard</title>
<meta http-equiv="refresh" content="10">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap">
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
.alert{position:fixed;bottom:20px;right:20px;background:#4caf50;color:#fff;padding:10px 15px;border-radius:5px;display:none;box-shadow:0 2px 10px rgba(0,0,0,.2)}
</style>

<div class="container">
  <h1>Screen OCR Results</h1>
  <div class="meta">Last updated: {{ts}}  |  Status: <span class="status">{{status}}</span></div>

  <div class="controls">
    <button class="btn btn-copy" onclick="copyText()">Copy All Text</button>
    <button class="btn btn-refresh" onclick="location.reload()">Refresh</button>
  </div>

  {% if text %}<pre id="ocrText">{{text}}</pre>{% endif %}

  {% if image %}<div class="imgwrap"><h3>Latest Snapshot:</h3>
    <img src="/latest_image?{{rand}}" alt="Latest screenshot">
  </div>{% endif %}

  <div id="copied" class="alert">Text copied ✓</div>
</div>

<script>
function selectAll(){
  const el=document.getElementById('ocrText'); if(!el) return;
  const r=document.createRange(); r.selectNodeContents(el);
  const s=window.getSelection(); s.removeAllRanges(); s.addRange(r);
}
function copyText(){ selectAll(); try{document.execCommand('copy');flash();}catch(e){} }
function flash(){ const a=document.getElementById('copied'); a.style.display='block';
  setTimeout(()=>a.style.display='none',2000);}
document.addEventListener('keydown',e=>{
  if(!(e.metaKey||e.ctrlKey)) return;
  if(['a','A'].includes(e.key)) {e.preventDefault();selectAll();}
  if(['c','C'].includes(e.key)) {e.preventDefault();copyText();}
});
document.addEventListener('contextmenu',e=>{e.preventDefault();copyText();});
</script>
"""

app = Flask(__name__)

@app.route("/")
def dashboard():
    txt_path = os.path.join(CONFIG["save_dir"], CONFIG["ocr_txt"])
    text = open(txt_path).read() if os.path.exists(txt_path) else ""
    latest_img_exists = os.path.exists(os.path.join(CONFIG["save_dir"], CONFIG["latest"]))
    return render_template_string(
        TPL,
        ts=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        status="success" if text else "waiting",
        text=text,
        image=latest_img_exists,
        rand=int(time.time())
    )

@app.route("/latest_image")
def latest_image():
    path = os.path.join(CONFIG["save_dir"], CONFIG["latest"])
    return send_file(path, mimetype="image/png") if os.path.exists(path) else ("No image", 404)

# ───────────────────────────── Main ───────────────────────────────────
if __name__ == "__main__":
    Thread(target=worker, daemon=True).start()
    ip = socket.gethostbyname(socket.gethostname()) or "localhost"
    log(f"Serving on http://{ip}:{CONFIG['port']}")
    app.run(host="0.0.0.0", port=CONFIG["port"], debug=False)
