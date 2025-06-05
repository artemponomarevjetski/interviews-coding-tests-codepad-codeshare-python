import os
import time
import signal
from datetime import datetime
from PIL import Image, ImageFilter, ImageEnhance
import pytesseract
from flask import Flask
import socket
from threading import Thread

# Directories and file paths
save_dir = os.path.expanduser("~/temp")
log_dir = os.path.expanduser("~/log")
log_file = os.path.join(log_dir, "snapshot.log")
latest_path = os.path.join(save_dir, "snap_latest.png")
ocr_output = os.path.join(save_dir, "snapshot.txt")

# Ensure directories exist
os.makedirs(save_dir, exist_ok=True)
os.makedirs(log_dir, exist_ok=True)

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"[{timestamp}] {msg}")

def kill_port_5000():
    # Find process using port 5000 and kill it
    command = "lsof -ti:5000"
    process_id = os.popen(command).read().strip()
    if process_id:
        os.kill(int(process_id), signal.SIGKILL)
        log(f"✓ Process on port 5000 (PID: {process_id}) killed.")

def capture_snapshot():
    command = f'screencapture -x "{latest_path}"'
    os.system(command)
    if os.path.exists(latest_path):
        log("✓ Screenshot captured.")
        extract_text(latest_path)
    else:
        log("❌ Screenshot capture failed.")

def extract_text(image_path):
    try:
        img = Image.open(image_path).convert("L")
        img = img.filter(ImageFilter.SHARPEN)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        text = pytesseract.image_to_string(img)
        with open(ocr_output, "w") as f:
            f.write(text)
        log("✓ OCR text extracted and saved.")
    except Exception as e:
        log(f"❌ Error extracting text: {e}")

app = Flask(__name__)

@app.route('/')
def display_text():
    if os.path.exists(ocr_output):
        with open(ocr_output, "r") as f:
            content = f.read()
        # Auto-refresh every 10 seconds
        return f"<html><head><meta http-equiv='refresh' content='10'></head><body><pre>{content}</pre></body></html>"
    else:
        return "Text not found", 404

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def periodic_snapshot():
    while True:
        capture_snapshot()
        time.sleep(15)

if __name__ == "__main__":
    kill_port_5000()  # Kill the process on port 5000 if any

    ip_address = get_ip()
    port = 5000

    # Start background thread for periodic screenshot + OCR
    snapshot_thread = Thread(target=periodic_snapshot, daemon=True)
    snapshot_thread.start()

    log(f"Flask app running on http://{ip_address}:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
