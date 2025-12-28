#!/usr/bin/env python3
"""
Enhanced Keyboard Logger Web Dashboard with Text Reconstruction
"""

from flask import Flask, jsonify
import json
import os
from datetime import datetime
from collections import Counter
import glob

app = Flask(__name__)

def get_latest_log():
    """Get most recent keyboard log"""
    log_files = glob.glob("keylogs/keyboard_*.jsonl")
    if not log_files:
        return None
    log_files.sort(reverse=True)
    return log_files[0]

def reconstruct_text(log_file, limit=200):
    """Reconstruct readable text from keyboard logs"""
    text = ""
    events = []
    
    # Read log file
    with open(log_file, 'r') as f:
        for line in f:
            try:
                events.append(json.loads(line.strip()))
            except:
                continue
    
    if limit:
        events = events[-limit:]  # Get last N events
    
    # Track shift state
    shift_pressed = False
    
    for event in events:
        if event['type'] != 'key_press':
            continue
            
        key = event['key']
        modifiers = event.get('modifiers', [])
        
        # Handle modifier keys
        if key in ['shift', 'shift_r']:
            shift_pressed = True
            continue
        elif key == 'caps_lock':
            # Toggle caps would need state tracking, skip for now
            continue
        
        # Handle text input
        if key == 'space':
            text += ' '
        elif key == 'enter':
            text += '\n'
        elif key == 'tab':
            text += '\t'
        elif key == 'backspace':
            # Remove last character for typos
            text = text[:-1] if text else ''
        elif key in ['left', 'right', 'up', 'down', 'cmd_r', 'ctrl', 'alt']:
            # Navigation and command keys - ignore for text
            shift_pressed = False
            pass
        elif len(key) == 1:  # Regular character
            # Handle case
            if shift_pressed or ('shift' in modifiers):
                text += key.upper()
            else:
                text += key.lower()
            shift_pressed = False
        elif key.startswith('shift_') and len(key.split('_')[1]) == 1:
            # Shift + character
            text += key.split('_')[1].upper()
        elif key in [':', '"', '=', '-', '?', '.', ',', ';', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '+', '{', '}', '[', ']', '|', '\\', '/', '<', '>', '`', '~']:
            # Special characters
            text += key
            shift_pressed = False
        else:
            # Reset shift for other keys
            shift_pressed = False
    
    return text.strip()

def get_stats():
    """Get keyboard statistics including reconstructed text"""
    log_file = get_latest_log()
    if not log_file:
        return {"error": "No logs found"}
    
    key_counts = Counter()
    events = []
    
    with open(log_file, 'r') as f:
        for line in f:
            try:
                event = json.loads(line.strip())
                events.append(event)
                if event['type'] == 'key_press':
                    key = event['key']
                    key_counts[key] += 1
            except:
                continue
    
    if not events:
        return {"error": "No events in log"}
    
    # Session info
    first_time = datetime.fromisoformat(events[0]['timestamp'])
    last_time = datetime.fromisoformat(events[-1]['timestamp'])
    duration = last_time - first_time
    
    # Recent activity
    recent = []
    for event in events[-20:]:
        if event['type'] == 'key_press':
            timestamp = event['timestamp'].split('T')[1][:12]
            key = event['key']
            modifiers = event.get('modifiers', [])
            recent.append({
                'time': timestamp,
                'key': key,
                'modifiers': modifiers
            })
    
    # Reconstructed text (last 300 keystrokes)
    reconstructed_text = reconstruct_text(log_file, 300)
    
    return {
        'total_keys': len(events),
        'unique_keys': len(key_counts),
        'top_keys': [[k, v] for k, v in key_counts.most_common(20)],
        'recent_activity': recent,
        'reconstructed_text': reconstructed_text,
        'session_info': {
            'start': first_time.strftime('%H:%M:%S'),
            'end': last_time.strftime('%H:%M:%S'),
            'duration': str(duration).split('.')[0],
            'log_file': os.path.basename(log_file)
        }
    }

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Keyboard Logger Dashboard</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 40px;
                background: #f5f5f5;
            }
            .container {
                max-width: 1000px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                border-bottom: 2px solid #4CAF50;
                padding-bottom: 10px;
            }
            h2 {
                color: #444;
                margin-top: 30px;
                border-bottom: 1px solid #ddd;
                padding-bottom: 5px;
            }
            .stats {
                display: flex;
                gap: 20px;
                margin: 20px 0;
            }
            .stat-box {
                flex: 1;
                background: #f0f8ff;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
            }
            .stat-value {
                font-size: 24px;
                font-weight: bold;
                color: #4CAF50;
            }
            .key-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(60px, 1fr));
                gap: 10px;
                margin: 20px 0;
            }
            .key-item {
                background: #e3f2fd;
                padding: 10px;
                border-radius: 5px;
                text-align: center;
            }
            .activity {
                margin-top: 20px;
                max-height: 200px;
                overflow-y: auto;
                border: 1px solid #eee;
                padding: 10px;
                border-radius: 5px;
            }
            .activity-item {
                background: #f9f9f9;
                padding: 8px;
                margin: 3px 0;
                border-left: 3px solid #4CAF50;
                font-family: monospace;
                font-size: 13px;
            }
            .text-output {
                margin-top: 20px;
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 15px;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                white-space: pre-wrap;
                word-wrap: break-word;
                min-height: 100px;
                max-height: 300px;
                overflow-y: auto;
                line-height: 1.5;
            }
            .text-label {
                font-weight: bold;
                color: #555;
                margin-bottom: 5px;
                display: block;
            }
            .section {
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 1px solid #eee;
            }
        </style>
        <script>
            async function loadData() {
                try {
                    const response = await fetch('/api/data');
                    const data = await response.json();
                    
                    // Update stats
                    document.getElementById('totalKeys').textContent = data.total_keys;
                    document.getElementById('uniqueKeys').textContent = data.unique_keys;
                    document.getElementById('duration').textContent = data.session_info.duration;
                    
                    // Update keys
                    const keyGrid = document.getElementById('keyGrid');
                    keyGrid.innerHTML = '';
                    if (data.top_keys) {
                        data.top_keys.forEach(([key, count]) => {
                            const div = document.createElement('div');
                            div.className = 'key-item';
                            div.innerHTML = `
                                <div style="font-size: 20px; font-weight: bold;">${key === ' ' ? '␣' : key}</div>
                                <div style="font-size: 12px;">${count}</div>
                            `;
                            keyGrid.appendChild(div);
                        });
                    }
                    
                    // Update activity
                    const activity = document.getElementById('activity');
                    activity.innerHTML = '';
                    if (data.recent_activity) {
                        data.recent_activity.slice(-15).reverse().forEach(item => {
                            const div = document.createElement('div');
                            div.className = 'activity-item';
                            div.textContent = `${item.time} - ${item.key} ${item.modifiers.length ? '[' + item.modifiers.join(',') + ']' : ''}`;
                            activity.appendChild(div);
                        });
                    }
                    
                    // Update reconstructed text
                    const textOutput = document.getElementById('textOutput');
                    if (data.reconstructed_text) {
                        textOutput.textContent = data.reconstructed_text;
                        if (!data.reconstructed_text.trim()) {
                            textOutput.textContent = 'No text reconstructed yet. Start typing!';
                            textOutput.style.color = '#888';
                            textOutput.style.fontStyle = 'italic';
                        } else {
                            textOutput.style.color = '#333';
                            textOutput.style.fontStyle = 'normal';
                        }
                    } else {
                        textOutput.textContent = 'No text data available';
                        textOutput.style.color = '#888';
                        textOutput.style.fontStyle = 'italic';
                    }
                    
                    // Update time
                    document.getElementById('lastUpdate').textContent = 
                        'Last update: ' + new Date().toLocaleTimeString();
                        
                } catch (error) {
                    console.error('Error loading data:', error);
                    document.getElementById('textOutput').textContent = 'Error loading data. Check console.';
                    document.getElementById('textOutput').style.color = '#dc3545';
                }
            }
            
            // Auto-refresh every 3 seconds
            setInterval(loadData, 3000);
            // Initial load
            loadData();
        </script>
    </head>
    <body>
        <div class="container">
            <h1>⌨️ Keyboard Logger Dashboard</h1>
            
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-value" id="totalKeys">0</div>
                    <div>Total Keys</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="uniqueKeys">0</div>
                    <div>Unique Keys</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="duration">0</div>
                    <div>Duration</div>
                </div>
            </div>
            
            <div class="section">
                <h2>📝 Reconstructed Text (Last 300 keystrokes)</h2>
                <span class="text-label">What you actually typed:</span>
                <div class="text-output" id="textOutput">
                    Loading...
                </div>
            </div>
            
            <div class="section">
                <h2>🔥 Most Pressed Keys</h2>
                <div class="key-grid" id="keyGrid"></div>
            </div>
            
            <div class="section">
                <h2>⏰ Recent Activity</h2>
                <div class="activity" id="activity"></div>
            </div>
            
            <div style="text-align: center; margin-top: 20px; color: #888;">
                <div id="lastUpdate">Last update: Just now</div>
                <button onclick="loadData()" style="margin-top: 10px; padding: 8px 16px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    🔄 Refresh Now
                </button>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/api/data')
def api_data():
    return jsonify(get_stats())

if __name__ == '__main__':
    print("=" * 60)
    print("🌐 Enhanced Keyboard Logger Web Dashboard")
    print("=" * 60)
    print("📊 Open your browser and visit: http://localhost:5000")
    print("📁 Logs directory: keylogs/")
    print("📝 Now includes reconstructed text!")
    print("🔄 Auto-refreshes every 3 seconds")
    print("=" * 60)
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
