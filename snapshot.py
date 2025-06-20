import os
import time
import subprocess
import sys
from datetime import datetime
from PIL import Image, ImageFilter, ImageEnhance
import pytesseract
from flask import Flask, render_template_string, send_file
import socket
from threading import Thread
import platform
import shutil

# Configuration
CONFIG = {
    'save_dir': os.path.expanduser("~/interviews-coding-tests-codepad-codeshare-python/temp"),
    'log_dir': os.path.expanduser("~/interviews-coding-tests-codepad-codeshare-python/log"),
    'log_file': "snapshot.log",
    'latest_path': "snap_latest.png",
    'ocr_output': "snapshot.txt",
    'port': 5000,
    'capture_interval': 15,
    'max_snapshots': 20,
    'tesseract_path': None  # Will be auto-detected
}

# Ensure directories exist
os.makedirs(CONFIG['save_dir'], exist_ok=True)
os.makedirs(CONFIG['log_dir'], exist_ok=True)

def detect_tesseract():
    """Find Tesseract executable path"""
    try:
        # Check common locations
        possible_paths = [
            '/usr/local/bin/tesseract',
            '/opt/homebrew/bin/tesseract',
            '/usr/bin/tesseract',
            shutil.which('tesseract')
        ]
        
        for path in possible_paths:
            if path and os.path.exists(path):
                CONFIG['tesseract_path'] = path
                pytesseract.pytesseract.tesseract_cmd = path
                return True
        return False
    except Exception as e:
        log(f"Tesseract detection error: {str(e)}")
        return False

def log(msg):
    """Log messages to file and console"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_path = os.path.join(CONFIG['log_dir'], CONFIG['log_file'])
    with open(log_path, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"[{timestamp}] {msg}")

def cleanup_old_snapshots():
    """Keep only the newest N snapshots"""
    try:
        files = [f for f in os.listdir(CONFIG['save_dir']) 
                if f.startswith('snap_') and f.endswith('.png')]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(CONFIG['save_dir'], x)))
        
        while len(files) > CONFIG['max_snapshots']:
            oldest = files.pop(0)
            os.remove(os.path.join(CONFIG['save_dir'], oldest))
            log(f"Removed old snapshot: {oldest}")
    except Exception as e:
        log(f"Cleanup error: {str(e)}")

def update_latest(img_path):
    """Update the latest snapshot symlink"""
    latest_path = os.path.join(CONFIG['save_dir'], CONFIG['latest_path'])
    if os.path.exists(latest_path):
        os.remove(latest_path)
    try:
        os.symlink(img_path, latest_path)
        log(f"Updated latest snapshot symlink to {img_path}")
    except OSError as e:
        # Fallback to copy if symlink fails
        try:
            shutil.copy2(img_path, latest_path)
            log(f"Copied latest snapshot (symlink failed): {img_path}")
        except Exception as copy_error:
            log(f"Failed to update latest: {str(copy_error)}")

def capture_snapshot():
    """Capture screenshot using available methods"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    img_path = os.path.join(CONFIG['save_dir'], f"snap_{timestamp}.png")
    
    # Try multiple capture methods with priority
    methods = [
        ['screencapture', '-x', '-l', '-o', img_path],  # Active window
        ['screencapture', '-x', '-m', '-o', img_path],  # Main display
        ['screencapture', '-x', '-o', img_path]         # Full screen
    ]
    
    for method in methods:
        try:
            result = subprocess.run(method, check=True, timeout=10,
                                  stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            if os.path.exists(img_path) and os.path.getsize(img_path) > 0:
                update_latest(img_path)
                cleanup_old_snapshots()
                return img_path
            if os.path.exists(img_path):
                os.remove(img_path)
        except subprocess.CalledProcessError as e:
            log(f"Capture failed ({method}): {e.stderr.decode().strip()}")
        except Exception as e:
            log(f"Capture error ({method}): {str(e)}")
    
    # Fallback to Quartz if all methods fail
    if platform.system() == 'Darwin':
        return quartz_capture()
    return None

def quartz_capture():
    """Alternative capture method using Quartz (macOS only)"""
    try:
        from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionAll, kCGNullWindowID
        from Quartz.CoreGraphics import CGWindowListCreateImage, CGRectInfinite, kCGWindowListOptionIncludingWindow, kCGWindowImageBoundsIgnoreFraming
        
        windows = CGWindowListCopyWindowInfo(kCGWindowListOptionAll, kCGNullWindowID)
        active_windows = [w for w in windows if w.get('kCGWindowIsOnscreen', False)]
        
        if not active_windows:
            log("No active windows found via Quartz")
            return None
            
        window_id = active_windows[0]['kCGWindowNumber']
        image = CGWindowListCreateImage(
            CGRectInfinite,
            kCGWindowListOptionIncludingWindow,
            window_id,
            kCGWindowImageBoundsIgnoreFraming
        )
        
        if image:
            img_path = os.path.join(CONFIG['save_dir'], f"snap_quartz_{int(time.time())}.png")
            width = image.getWidth()
            height = image.getHeight()
            pil_image = Image.frombytes(
                'RGBA',
                (width, height),
                image.getDataProvider().getData()
            )
            pil_image.save(img_path)
            update_latest(img_path)
            cleanup_old_snapshots()
            return img_path
    except Exception as e:
        log(f"Quartz capture failed: {str(e)}")
    return None

def enhance_image_for_ocr(img):
    """Apply multiple enhancements to improve OCR accuracy"""
    try:
        # Convert to grayscale
        img = img.convert('L')
        
        # Increase contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        
        # Sharpen image
        img = img.filter(ImageFilter.SHARPEN)
        
        # Apply threshold to remove noise
        img = img.point(lambda x: 0 if x < 140 else 255)
        
        return img
    except Exception as e:
        log(f"Image enhancement error: {str(e)}")
        return img

def extract_text(image_path):
    """Extract text from image using OCR"""
    try:
        if not CONFIG['tesseract_path'] and not detect_tesseract():
            log("Tesseract OCR not found - please install it")
            return False
            
        img = Image.open(image_path)
        img = enhance_image_for_ocr(img)
        
        # Try multiple OCR configurations
        configs = [
            r'--oem 3 --psm 6',  # Assume uniform block of text
            r'--oem 3 --psm 11',  # Sparse text
            r'--oem 3 --psm 4'    # Single column of text
        ]
        
        best_text = ""
        for config in configs:
            try:
                text = pytesseract.image_to_string(img, config=config)
                if len(text.strip()) > len(best_text.strip()):
                    best_text = text
            except Exception as e:
                log(f"OCR attempt failed (config {config}): {str(e)}")
        
        if best_text.strip():
            with open(os.path.join(CONFIG['save_dir'], CONFIG['ocr_output']), "w") as f:
                f.write(best_text)
            return True
        
        log("OCR returned empty text")
        return False
    except Exception as e:
        log(f"OCR Error: {str(e)}")
        return False

def periodic_snapshot():
    """Periodically capture screenshots and extract text"""
    while True:
        img_path = capture_snapshot()
        if img_path:
            if extract_text(img_path):
                log("Snapshot and OCR completed successfully")
            else:
                log("Snapshot captured but OCR failed")
        else:
            log("Failed to capture snapshot")
        time.sleep(CONFIG['capture_interval'])

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Screen OCR Dashboard</title>
    <meta http-equiv='refresh' content='10'>
    <style>
        body { font-family: -apple-system, sans-serif; margin: 20px; }
        pre { 
            background: #f5f5f5; 
            padding: 15px; 
            border-radius: 5px; 
            white-space: pre-wrap;
            font-size: 1.1em;
        }
        .timestamp { color: #666; font-size: 0.9em; }
        .status { 
            padding: 5px 10px; 
            border-radius: 3px; 
            font-weight: bold;
            background: {% if status == 'success' %}#4CAF50{% else %}#F44336{% endif %};
            color: white;
        }
        .image-container { margin-top: 20px; }
        .image-container img { max-width: 100%; border: 1px solid #ddd; }
        .copy-notification {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #4CAF50;
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
            display: none;
            z-index: 1000;
        }
    </style>
</head>
<body>
    <h1>Screen OCR Results</h1>
    <div class="timestamp">Last updated: {{ timestamp }}</div>
    <div>Status: <span class="status">{{ status }}</span></div>
    {% if text %}
    <pre id="ocrText">{{ text }}</pre>
    {% endif %}
    {% if image_exists %}
    <div class="image-container">
        <h3>Latest Snapshot:</h3>
        <img src="/latest_image?t={{ cache_buster }}" alt="Latest screenshot">
    </div>
    {% endif %}
    <div class="copy-notification" id="copyNotification">Text copied to clipboard!</div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const textElement = document.getElementById('ocrText');
            const notification = document.getElementById('copyNotification');
            
            // Override right-click context menu
            document.addEventListener('contextmenu', function(e) {
                e.preventDefault();
                
                if (textElement) {
                    // Select all text
                    const range = document.createRange();
                    range.selectNodeContents(textElement);
                    const selection = window.getSelection();
                    selection.removeAllRanges();
                    selection.addRange(range);
                    
                    // Copy to clipboard
                    try {
                        document.execCommand('copy');
                        
                        // Show notification
                        notification.style.display = 'block';
                        setTimeout(() => {
                            notification.style.display = 'none';
                        }, 2000);
                    } catch (err) {
                        console.error('Failed to copy text: ', err);
                    }
                }
            });
            
            // Also allow Ctrl+A and Ctrl+C as alternatives
            document.addEventListener('keydown', function(e) {
                if (textElement && e.ctrlKey) {
                    if (e.key === 'a' || e.key === 'A') {
                        e.preventDefault();
                        const range = document.createRange();
                        range.selectNodeContents(textElement);
                        const selection = window.getSelection();
                        selection.removeAllRanges();
                        selection.addRange(range);
                    } else if (e.key === 'c' || e.key === 'C') {
                        try {
                            document.execCommand('copy');
                            notification.style.display = 'block';
                            setTimeout(() => {
                                notification.style.display = 'none';
                            }, 2000);
                        } catch (err) {
                            console.error('Failed to copy text: ', err);
                        }
                    }
                }
            });
        });
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Main dashboard route"""
    txt_path = os.path.join(CONFIG['save_dir'], CONFIG['ocr_output'])
    image_exists = os.path.exists(os.path.join(CONFIG['save_dir'], CONFIG['latest_path']))
    
    status = "success" if os.path.exists(txt_path) else "waiting"
    text = ""
    
    if os.path.exists(txt_path):
        with open(txt_path, "r") as f:
            text = f.read()
        if not text.strip():
            status = "no text"
    
    return render_template_string(HTML_TEMPLATE,
                                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                status=status,
                                text=text,
                                image_exists=image_exists,
                                cache_buster=int(time.time()))

@app.route('/latest_image')
def latest_image():
    """Serve the latest captured image"""
    latest_path = os.path.join(CONFIG['save_dir'], CONFIG['latest_path'])
    if os.path.exists(latest_path):
        return send_file(latest_path, mimetype='image/png')
    return "No image available", 404

if __name__ == "__main__":
    # Verify Tesseract is available
    if not detect_tesseract():
        log("Warning: Tesseract OCR not found - text extraction will not work")
        log("Install with: brew install tesseract (macOS) or apt-get install tesseract-ocr (Linux)")
    
    # Start background thread
    Thread(target=periodic_snapshot, daemon=True).start()
    
    # Get server IP
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except:
        ip = "localhost"
    
    log(f"Starting server on http://{ip}:{CONFIG['port']}")
    app.run(host="0.0.0.0", port=CONFIG['port'], debug=False)
