import os
import base64
from datetime import datetime
from flask import Flask, request, render_template_string, jsonify
import socket

app = Flask(__name__)

# Create directories
os.makedirs('logs/excerpts', exist_ok=True)
os.makedirs('logs/images', exist_ok=True)

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Paste Saver</title>
    <style>
        body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; background: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; margin-top: 0; }
        textarea { width: 100%; height: 200px; margin: 15px 0; padding: 15px; font-family: monospace; border: 2px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        textarea:focus { outline: none; border-color: #4CAF50; }
        button { padding: 12px 30px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
        button:hover { background: #45a049; }
        .message { padding: 10px; margin: 10px 0; border-radius: 5px; display: none; }
        .success { background: #d4edda; color: #155724; display: block; }
        .error { background: #f8d7da; color: #721c24; display: block; }
        .paste-area { border: 3px dashed #aaa; padding: 30px; text-align: center; margin: 20px 0; border-radius: 10px; background: #fafafa; }
        .paste-area.dragover { border-color: #4CAF50; background: #e8f5e9; }
        .preview { max-width: 100%; max-height: 300px; margin: 15px 0; display: none; border: 1px solid #ddd; border-radius: 5px; }
        .hint { color: #666; font-size: 0.9em; margin-top: 5px; }
        .stats { margin-top: 20px; padding: 15px; background: #f0f0f0; border-radius: 5px; font-size: 0.9em; }
        .footer { margin-top: 20px; text-align: center; color: #777; font-size: 0.8em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 Paste Saver</h1>
        <p>Paste <strong>text</strong> or an <strong>image</strong> (Ctrl+V) below, then click <strong>Save</strong></p>
        
        <div id="message" class="message"></div>
        
        <div class="paste-area" id="pasteArea">
            <div style="font-size: 48px; margin-bottom: 10px;">📋</div>
            <p><strong>Paste here (Ctrl+V)</strong></p>
            <p class="hint">Works with text or images</p>
        </div>
        
        <textarea id="textInput" placeholder="Or type/paste text here..."></textarea>
        
        <img id="imagePreview" class="preview" />
        
        <div style="text-align: center;">
            <button onclick="saveContent()">💾 Save</button>
        </div>
        
        <div class="stats" id="stats">
            Loading stats...
        </div>
        
        <div class="footer">
            Saved in: logs/excerpts/ (text) | logs/images/ (images)
        </div>
    </div>
    
    <script>
        let currentImageData = null;
        
        // Handle paste anywhere in the paste area
        document.getElementById('pasteArea').addEventListener('paste', function(e) {
            e.preventDefault();
            
            const items = (e.clipboardData || e.originalEvent.clipboardData).items;
            
            for (let item of items) {
                if (item.type.indexOf('image') === 0) {
                    // Handle image paste
                    const blob = item.getAsFile();
                    const reader = new FileReader();
                    
                    reader.onload = function(e) {
                        currentImageData = e.target.result;
                        document.getElementById('imagePreview').src = e.target.result;
                        document.getElementById('imagePreview').style.display = 'block';
                        document.getElementById('textInput').style.display = 'none';
                        showMessage('✅ Image ready to save', 'success');
                    };
                    
                    reader.readAsDataURL(blob);
                    break;
                }
            }
        });
        
        // Handle text paste/typing
        document.getElementById('textInput').addEventListener('input', function() {
            currentImageData = null;
            document.getElementById('imagePreview').style.display = 'none';
            document.getElementById('textInput').style.display = 'block';
        });
        
        function saveContent() {
            const textContent = document.getElementById('textInput').value;
            
            if (currentImageData) {
                // Save image
                fetch('/save-image', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image: currentImageData })
                })
                .then(res => res.json())
                .then(data => {
                    showMessage('✅ Image saved: ' + data.filename, 'success');
                    currentImageData = null;
                    document.getElementById('imagePreview').style.display = 'none';
                    updateStats();
                });
            } else if (textContent.trim()) {
                // Save text
                fetch('/save-text', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: textContent })
                })
                .then(res => res.json())
                .then(data => {
                    showMessage('✅ Text saved: ' + data.filename, 'success');
                    document.getElementById('textInput').value = '';
                    updateStats();
                });
            } else {
                showMessage('❌ Nothing to save!', 'error');
            }
        }
        
        function showMessage(msg, type) {
            const msgDiv = document.getElementById('message');
            msgDiv.textContent = msg;
            msgDiv.className = 'message ' + type;
            setTimeout(() => {
                msgDiv.className = 'message';
            }, 3000);
        }
        
        function updateStats() {
            fetch('/stats')
                .then(res => res.json())
                .then(data => {
                    document.getElementById('stats').innerHTML = `
                        <strong>📊 Stats:</strong> 
                        ${data.text_count} text excerpts · 
                        ${data.image_count} images · 
                        Latest: ${data.latest || 'just now'}
                    `;
                });
        }
        
        // Load stats on page load
        updateStats();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/save-text', methods=['POST'])
def save_text():
    data = request.json
    text = data.get('text', '')
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'text.{timestamp}.txt'
    filepath = os.path.join('logs/excerpts', filename)
    
    # Save with metadata header
    content = f"""--- PASTE SAVER ---
Saved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Type: Text
---
{text}
"""
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    return jsonify({'status': 'ok', 'filename': filename})

@app.route('/save-image', methods=['POST'])
def save_image():
    data = request.json
    image_data = data.get('image', '')
    
    # Parse data URL
    if ',' in image_data:
        header, encoded = image_data.split(',', 1)
        ext = header.split(';')[0].split('/')[-1]  # png, jpeg, etc.
    else:
        encoded = image_data
        ext = 'png'
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'img.{timestamp}.{ext}'
    filepath = os.path.join('logs/images', filename)
    
    # Save image
    with open(filepath, 'wb') as f:
        f.write(base64.b64decode(encoded))
    
    # Also save a metadata file
    meta_path = os.path.join('logs/images', f'{filename}.txt')
    with open(meta_path, 'w') as f:
        f.write(f"""--- PASTE SAVER ---
Saved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Type: Image
File: {filename}
---
""")
    
    return jsonify({'status': 'ok', 'filename': filename})

@app.route('/stats')
def stats():
    text_files = os.listdir('logs/excerpts') if os.path.exists('logs/excerpts') else []
    image_files = os.listdir('logs/images') if os.path.exists('logs/images') else []
    
    # Get latest file
    all_files = text_files + image_files
    latest = sorted(all_files)[-1] if all_files else None
    
    # Filter out metadata files for count
    image_count = len([f for f in image_files if not f.endswith('.txt')])
    
    return jsonify({
        'text_count': len(text_files),
        'image_count': image_count,
        'latest': latest
    })

def find_free_port(start=5000):
    port = start
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
            port += 1

if __name__ == '__main__':
    port = find_free_port(5000)
    
    # Get network IP
    import subprocess
    try:
        ip = subprocess.check_output("ipconfig getifaddr en0 2>/dev/null || echo 'localhost'", shell=True).decode().strip()
    except:
        ip = 'localhost'
    
    print(f"\n{'='*50}")
    print(f"📋 PASTE SAVER")
    print(f"{'='*50}")
    print(f"🌐 Local:    http://127.0.0.1:{port}")
    print(f"🌐 Network:  http://{ip}:{port}")
    print(f"\n📁 Text logs:  {os.path.abspath('logs/excerpts')}")
    print(f"📁 Image logs: {os.path.abspath('logs/images')}")
    print(f"\n💡 How to use:")
    print(f"   • Paste text: Type or paste in the box → Save")
    print(f"   • Paste image: Copy image (Ctrl+C) → Paste in box (Ctrl+V) → Save")
    print(f"{'='*50}\n")
    
    app.run(host='0.0.0.0', port=port, debug=True)