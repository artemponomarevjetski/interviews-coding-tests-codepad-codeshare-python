#!/usr/bin/env python3
"""
Keyboard Log Viewer - Analyze keyboard-only logs

Usage:
  python keyboard_viewer.py --stats          # Show key statistics
  python keyboard_viewer.py --recent 50      # Show recent 50 keystrokes
  python keyboard_viewer.py --summary        # Show session summary
  python keyboard_viewer.py --top 30         # Show top 30 keys
  python keyboard_viewer.py --file <path>    # Analyze specific log file

Parses JSONL logs from keyboard-only logger.
"""
#!/usr/bin/env python3
"""
Keyboard Log Viewer - Simple viewer for keyboard-only JSONL logs
"""

import json
import argparse
import os
from datetime import datetime
from collections import Counter
import sys

def get_latest_log(log_dir="keylogs"):
    """Get the most recent keyboard log file"""
    if not os.path.exists(log_dir):
        print(f"❌ Log directory '{log_dir}' not found")
        return None
    
    import glob
    log_files = glob.glob(os.path.join(log_dir, "keyboard_*.jsonl"))
    
    if not log_files:
        print("❌ No keyboard log files found")
        return None
    
    log_files.sort(reverse=True)
    return log_files[0]

def show_stats(log_file, top_n=20):
    """Show key statistics"""
    key_counts = Counter()
    total_keys = 0
    
    with open(log_file, 'r') as f:
        for line in f:
            try:
                event = json.loads(line.strip())
                if event['type'] == 'key_press':
                    key = event['key']
                    key_counts[key] += 1
                    total_keys += 1
            except:
                continue
    
    if not key_counts:
        print("❌ No keyboard events found")
        return
    
    print(f"\n🔥 Top {top_n} Most Pressed Keys")
    print("=" * 80)
    
    for i, (key, count) in enumerate(key_counts.most_common(top_n), 1):
        percentage = (count / total_keys) * 100
        bar = "█" * int(percentage / 3)
        print(f"{i:2}. {key:20} {count:6,} ({percentage:5.1f}%) {bar}")
    
    print("=" * 80)
    print(f"📊 Total key presses: {total_keys:,}")
    print(f"🎯 Unique keys: {len(key_counts):,}")
    print(f"📁 Log file: {log_file}")

def show_recent(log_file, count=20):
    """Show recent keyboard events"""
    events = []
    
    with open(log_file, 'r') as f:
        for line in f:
            try:
                events.append(json.loads(line.strip()))
            except:
                continue
    
    if not events:
        print("❌ No keyboard events found")
        return
    
    print(f"\n📋 Recent Keyboard Events ({count} most recent)")
    print("=" * 80)
    
    for event in events[-count:]:
        timestamp = event['timestamp'].split('T')[1][:12]
        key = event['key']
        modifiers = event.get('modifiers', [])
        
        if modifiers:
            print(f"{timestamp}  {key} [{', '.join(modifiers)}]")
        else:
            print(f"{timestamp}  {key}")
    
    print("=" * 80)
    print(f"📊 Total events: {len(events):,}")

def show_summary(log_file):
    """Show session summary"""
    events = []
    
    with open(log_file, 'r') as f:
        for line in f:
            try:
                events.append(json.loads(line.strip()))
            except:
                continue
    
    if not events:
        print("❌ No keyboard data available")
        return
    
    first_time = datetime.fromisoformat(events[0]['timestamp'])
    last_time = datetime.fromisoformat(events[-1]['timestamp'])
    duration = last_time - first_time
    
    key_counts = Counter(event['key'] for event in events if event['type'] == 'key_press')
    
    print(f"\n📈 Keyboard Activity Summary")
    print("=" * 80)
    print(f"🕐 Session start: {first_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🕐 Session end:   {last_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️  Duration:      {duration}")
    print(f"⌨️  Total keys:    {len(events):,}")
    print(f"🎯 Unique keys:    {len(key_counts):,}")
    
    if key_counts:
        print(f"\n🔝 Top 5 keys:")
        for key, count in key_counts.most_common(5):
            print(f"  {key:10}: {count:,}")
    
    print(f"\n📁 Log file:      {log_file}")
    print("=" * 80)

def main():
    parser = argparse.ArgumentParser(description="Keyboard Log Viewer")
    parser.add_argument('--recent', type=int, nargs='?', const=20,
                       help='Show recent keyboard events (default: 20)')
    parser.add_argument('--stats', action='store_true',
                       help='Show key statistics')
    parser.add_argument('--summary', action='store_true',
                       help='Show activity summary')
    parser.add_argument('--top', type=int, default=20,
                       help='Number of top keys to show (default: 20)')
    parser.add_argument('--file', type=str,
                       help='Specific log file to analyze')
    
    args = parser.parse_args()
    
    if args.file:
        log_file = args.file
        if not os.path.exists(log_file):
            print(f"❌ File not found: {log_file}")
            return
    else:
        log_file = get_latest_log()
        if not log_file:
            return
    
    if args.recent:
        show_recent(log_file, args.recent)
    elif args.summary:
        show_summary(log_file)
    elif args.stats:
        show_stats(log_file, args.top)
    else:
        show_stats(log_file, args.top)

if __name__ == "__main__":
    main()
