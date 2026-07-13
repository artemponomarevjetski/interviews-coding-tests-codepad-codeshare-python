#!/usr/bin/env python3
"""
KEYBOARD-ONLY Desktop Activity Logger - Personal Use Only
Logs only keyboard events, no mouse clicks or scrolls.

Usage:
    python desklog.py                 # start logging (Ctrl+C to stop)
    python desklog.py --recent 50     # show recent key presses
    python desklog.py --stats         # show statistics
    python desklog.py --demo          # quick demo mode

Features:
    • Logs only keyboard events (no mouse/scroll)
    • JSONL format for easy parsing
    • Real‑time console feedback
    • Modifier key tracking (Ctrl, Shift, Alt, Cmd)
    • Daily log files in keylogs/ directory
"""

import os
import sys
import time
import signal
import threading
import json
from datetime import datetime
from collections import deque

# Import pynput for keyboard monitoring only
try:
    from pynput import keyboard
    from pynput.keyboard import Key, Listener as KeyboardListener
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
CONFIG = {
    'log_dir': 'keylogs',
    'max_log_lines': 100_000,
    'max_log_days': 30,
    'session_timeout': 300,
    'log_format': 'jsonl',          # JSON Lines format
}


# ----------------------------------------------------------------------
# Logger class
# ----------------------------------------------------------------------
class KeyboardOnlyLogger:
    def __init__(self, log_dir):
        self.log_dir = log_dir
        self.buffer = deque(maxlen=CONFIG['max_log_lines'])
        os.makedirs(log_dir, exist_ok=True)

        # Today's log file in JSONL format
        today = datetime.now().strftime("%Y-%m-%d")
        self.today_file = os.path.join(log_dir, f"keyboard_{today}.jsonl")

        # System metadata
        self.system_info = {
            "platform": sys.platform,
            "user": os.getlogin(),
            "hostname": os.uname().nodename,
            "version": "keyboard-only-v1.0"
        }

    def log_keypress(self, key_data):
        """Log a key press event in JSONL format."""
        timestamp = datetime.now().isoformat()

        entry = {
            "timestamp": timestamp,
            "type": "key_press",
            "key": key_data['key'],
            "modifiers": key_data.get('modifiers', []),
            "system": self.system_info
        }

        # Keep a human‑readable copy in memory
        human_line = f"[{timestamp}] KEY: {key_data['key']} | Modifiers: {key_data.get('modifiers', [])}"
        self.buffer.appendleft(human_line)

        # Append to the daily JSONL file
        try:
            with open(self.today_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            print(f"⚠️  Error writing log: {e}")

        # Console feedback
        if key_data['key'] not in ['shift', 'ctrl', 'alt', 'cmd', 'tab', 'caps_lock']:
            print(f"⌨️  {key_data['key']}")

    def get_recent_keys(self, count=50):
        """Return the most recent key press lines."""
        return list(self.buffer)[:count]

    def get_stats(self):
        """Return logging statistics."""
        log_count = 0
        if os.path.exists(self.today_file):
            with open(self.today_file, 'r', encoding='utf-8') as f:
                log_count = sum(1 for _ in f)

        return {
            'log_directory': self.log_dir,
            'today_file': self.today_file,
            'entries_today': log_count,
            'entries_in_memory': len(self.buffer),
            'format': CONFIG['log_format'],
            'version': 'keyboard-only'
        }


# ----------------------------------------------------------------------
# Monitor class (listens to keyboard)
# ----------------------------------------------------------------------
class KeyboardMonitor:
    def __init__(self, logger):
        self.logger = logger
        self.last_activity = time.time()
        self.session_active = True
        self.pressed_keys = set()
        self.keyboard_listener = None

    def start(self):
        if not PYNPUT_AVAILABLE:
            print("❌ pynput not available. Install with: pip install pynput")
            return False

        print("✅ Starting KEYBOARD-ONLY monitoring...")
        print("   → No mouse clicks logged")
        print("   → No scroll events logged")
        print("   → Only keyboard presses captured")

        # Start keyboard listener
        self.keyboard_listener = KeyboardListener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.keyboard_listener.start()

        # Start session monitor in a background thread
        threading.Thread(target=self._session_monitor, daemon=True).start()

        return True

    def _on_key_press(self, key):
        self.last_activity = time.time()
        try:
            key_str = self._key_to_string(key)
            self.pressed_keys.add(key)

            modifiers = self._get_current_modifiers()

            # Log only real character keys, not modifier keys alone
            if key_str.lower() not in ['shift', 'ctrl', 'alt', 'cmd', 'win']:
                self.logger.log_keypress({
                    'key': key_str,
                    'modifiers': list(modifiers),
                })
            # else: just track modifier state without logging
        except Exception as e:
            print(f"⚠️  Error processing key: {e}")

    def _on_key_release(self, key):
        try:
            self.pressed_keys.discard(key)
        except:
            pass

    def _key_to_string(self, key):
        """Convert a key object to a string representation."""
        try:
            if hasattr(key, 'char') and key.char:
                return key.char
            elif hasattr(key, 'name'):
                return key.name
            else:
                return str(key).replace("'", "")
        except:
            return str(key)

    def _get_current_modifiers(self):
        """Return the set of currently pressed modifier keys."""
        modifiers = set()
        for key in self.pressed_keys:
            key_str = self._key_to_string(key).lower()
            if 'ctrl' in key_str or 'control' in key_str:
                modifiers.add('ctrl')
            elif 'shift' in key_str:
                modifiers.add('shift')
            elif 'alt' in key_str:
                modifiers.add('alt')
            elif 'cmd' in key_str or 'win' in key_str or 'super' in key_str:
                modifiers.add('cmd')
        return modifiers

    def _session_monitor(self):
        """Monitor idle time and print status changes."""
        while True:
            idle_time = time.time() - self.last_activity
            if idle_time > CONFIG['session_timeout'] and self.session_active:
                self.session_active = False
                print(f"💤 Session idle for {int(idle_time)}s")
            elif idle_time <= CONFIG['session_timeout'] and not self.session_active:
                self.session_active = True
                print("🔋 Session active again")
            time.sleep(30)

    def stop(self):
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
            print("🛑 Keyboard listener stopped")


# ----------------------------------------------------------------------
# Main application
# ----------------------------------------------------------------------
class DesktopLogger:
    def __init__(self):
        self.logger = KeyboardOnlyLogger(CONFIG['log_dir'])
        self.keyboard_monitor = KeyboardMonitor(self.logger)
        self.running = False

    def start(self):
        print("\n" + "=" * 60)
        print("🔑 KEYBOARD-ONLY Desktop Logger")
        print("=" * 60)

        if not PYNPUT_AVAILABLE:
            print("❌ Required dependencies not available")
            print("💡 Install with: pip install pynput")
            sys.exit(1)

        if not self.keyboard_monitor.start():
            sys.exit(1)

        self.running = True
        print(f"📁 Logging to: {CONFIG['log_dir']}")
        print(f"📝 Format: {CONFIG['log_format']}")
        print("🛑 Press Ctrl+C to stop")
        print("=" * 60)

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        print("\n🛑 Stopping keyboard logger...")
        self.running = False
        self.keyboard_monitor.stop()

        stats = self.logger.get_stats()
        print("\n📊 Final Statistics:")
        print("-" * 40)
        for key, value in stats.items():
            if key not in ['today_file']:
                print(f"{key.replace('_', ' ').title():20}: {value}")
        print(f"Log File: {stats['today_file']}")
        print("-" * 40)
        sys.exit(0)


# ----------------------------------------------------------------------
# Command‑line helpers
# ----------------------------------------------------------------------
def show_recent_keys(count=50):
    logger = KeyboardOnlyLogger(CONFIG['log_dir'])
    keys = logger.get_recent_keys(count)
    if not keys:
        print("No keyboard logs found.")
        return
    print(f"\n📄 Last {len(keys)} key presses:")
    print("-" * 80)
    for key in keys:
        print(key)
    print("-" * 80)


def show_statistics():
    logger = KeyboardOnlyLogger(CONFIG['log_dir'])
    stats = logger.get_stats()
    print("\n📊 Keyboard Logger Statistics:")
    print("-" * 40)
    for key, value in stats.items():
        if key not in ['today_file']:
            print(f"{key.replace('_', ' ').title():20}: {value}")
    print(f"Log File: {stats['today_file']}")
    print("-" * 40)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Keyboard-Only Desktop Logger")
    parser.add_argument('--recent', type=int, nargs='?', const=50,
                        help='Show recent key presses (default: 50)')
    parser.add_argument('--stats', action='store_true',
                        help='Show statistics')
    parser.add_argument('--demo', action='store_true',
                        help='Show a quick demo of logging')

    args = parser.parse_args()

    if args.recent:
        show_recent_keys(args.recent)
        return
    elif args.stats:
        show_statistics()
        return
    elif args.demo:
        print("Keyboard logger demo - press some keys to see them logged")
        print("Press Ctrl+C to exit demo")
        logger = KeyboardOnlyLogger(CONFIG['log_dir'])
        monitor = KeyboardMonitor(logger)
        monitor.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            monitor.stop()
        return

    # Start the main logger
    app = DesktopLogger()
    signal.signal(signal.SIGINT, lambda s, f: app.stop())
    signal.signal(signal.SIGTERM, lambda s, f: app.stop())
    app.start()


if __name__ == "__main__":
    main()
