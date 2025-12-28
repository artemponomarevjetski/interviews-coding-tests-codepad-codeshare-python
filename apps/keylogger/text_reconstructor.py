#!/usr/bin/env python3
"""
Text Reconstructor - Reconstruct typed text from keyboard logs
"""

import json
import os
import glob
import argparse
from datetime import datetime

def reconstruct_text(log_file, limit=None, show_typos=True):
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
    
    # Keep track of modifier state
    shift_pressed = False
    caps_lock = False
    
    for event in events:
        if event['type'] != 'key_press':
            continue
            
        key = event['key']
        modifiers = event.get('modifiers', [])
        
        # Handle modifier keys
        if key == 'shift' or key == 'shift_r':
            shift_pressed = True
            continue
        elif key == 'caps_lock':
            caps_lock = not caps_lock
            continue
        
        # Handle text input
        if key == 'space':
            text += ' '
        elif key == 'enter':
            text += '\n'
        elif key == 'tab':
            text += '\t'
        elif key == 'backspace':
            if show_typos:
                text = text[:-1]  # Show backspaces (typos)
        elif key in ['left', 'right', 'up', 'down', 'cmd_r', 'ctrl', 'alt']:
            # Navigation and command keys - ignore for text
            pass
        elif len(key) == 1:  # Regular character
            # Handle case
            if shift_pressed or caps_lock:
                text += key.upper()
            else:
                text += key.lower()
            shift_pressed = False
        elif key.startswith('shift_') and len(key.split('_')[1]) == 1:
            # Shift + character
            text += key.split('_')[1].upper()
        elif key in [':', '"', '=', '-', '?']:
            # Special characters
            text += key
        else:
            # Ignore other keys
            pass
    
    return text

def get_latest_log():
    """Get most recent keyboard log"""
    log_files = glob.glob("keylogs/keyboard_*.jsonl")
    if not log_files:
        return None
    log_files.sort(reverse=True)
    return log_files[0]

def main():
    parser = argparse.ArgumentParser(description="Text Reconstructor from Keyboard Logs")
    parser.add_argument('--file', type=str, help='Specific log file to analyze')
    parser.add_argument('--recent', type=int, default=200, 
                       help='Number of recent keystrokes to analyze (default: 200)')
    parser.add_argument('--all', action='store_true', 
                       help='Reconstruct all text from entire log')
    parser.add_argument('--clean', action='store_true',
                       help='Show cleaned text without backspaces')
    parser.add_argument('--session', type=int,
                       help='Reconstruct text from last N minutes')
    
    args = parser.parse_args()
    
    if args.file:
        log_file = args.file
        if not os.path.exists(log_file):
            print(f"❌ File not found: {log_file}")
            return
    else:
        log_file = get_latest_log()
        if not log_file:
            print("❌ No keyboard log files found in keylogs/")
            return
    
    print(f"📁 Analyzing: {log_file}")
    print("=" * 60)
    
    if args.all:
        limit = None
    elif args.session:
        # Calculate events from last N minutes
        with open(log_file, 'r') as f:
            lines = list(f)
        
        # Find events from last N minutes
        cutoff_time = datetime.now().timestamp() - (args.session * 60)
        recent_events = 0
        for line in reversed(lines):
            try:
                event = json.loads(line.strip())
                timestamp = datetime.fromisoformat(event['timestamp']).timestamp()
                if timestamp < cutoff_time:
                    break
                recent_events += 1
            except:
                continue
        limit = recent_events
        print(f"⏱️  Last {args.session} minutes: {recent_events} events")
    else:
        limit = args.recent
    
    # Reconstruct text
    reconstructed = reconstruct_text(log_file, limit, show_typos=not args.clean)
    
    print("\n📝 RECONSTRUCTED TEXT:")
    print("=" * 60)
    print(reconstructed)
    print("=" * 60)
    
    # Show statistics
    words = reconstructed.split()
    print(f"\n📊 Statistics:")
    print(f"  Characters: {len(reconstructed)}")
    print(f"  Words: {len(words)}")
    print(f"  Lines: {reconstructed.count('\\n') + 1}")
    
    if words:
        print(f"\n🔤 Word list:")
        for i, word in enumerate(words[:50], 1):
            print(f"  {i:2}. {word}")

if __name__ == "__main__":
    main()
