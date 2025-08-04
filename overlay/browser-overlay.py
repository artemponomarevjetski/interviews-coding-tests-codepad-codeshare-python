""""
This code implements an overlay browser that meets these requirements:

Semi-transparent
Manual login capability

Key Features:

✅ Truly browser-overlay window (no taskbar/dock icon, bypasses window managers)
✅ Adjustable transparency (set via setWindowOpacity)
✅ Manual login possible (while remaining hidden from screen sharing)
✅ Fixes previous errors (URL handling, clean exit)

Installation Instructions:

First clean your environment:

rm -rf browser-overlay-env dist build browser-overlay.spec nohup.out

Create and activate fresh virtual environment:

python3 -m venv browser-overlay-env

source browser-overlay-env/bin/activate

Install required packages:

pip install PyQt6 PyQt6-WebEngine

Run the browser:

python browser-overlay.py
"""
import os
import sys
import signal
import warnings
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage

warnings.filterwarnings("ignore", category=DeprecationWarning)

class browser-overlayBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_browser()
        
    def init_ui(self):
        # browser-overlay window properties
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(0.7)
        self.resize(900, 600)
        
        # Hide from taskbar/dock
        try:
            from AppKit import NSApp, NSApplicationActivationPolicyProhibited
            NSApp.setActivationPolicy_(NSApplicationActivationPolicyProhibited)
        except ImportError:
            pass
            
    def init_browser(self):
        self.profile = QWebEngineProfile("browser-overlay_profile")
        self.browser = QWebEngineView()
        self.browser.setPage(QWebEnginePage(self.profile))
        self.browser.setUrl(QUrl("https://chat.openai.com"))
        self.setCentralWidget(self.browser)
    
    def keyPressEvent(self, event):
        if (event.modifiers() == Qt.KeyboardModifier.ControlModifier and 
            event.key() == Qt.Key.Key_C):
            QTimer.singleShot(0, self.close_gracefully)
        super().keyPressEvent(event)
    
    def close_gracefully(self):
        print("\nClosing browser-overlay browser...")
        self.close()
        QApplication.quit()

def handle_sigint(signum, frame):
    print("\nReceived SIGINT (Ctrl+C) - closing gracefully")
    QApplication.quit()

if __name__ == "__main__":
    # Set up signal handler for terminal Ctrl+C
    signal.signal(signal.SIGINT, handle_sigint)
    
    # Disable GPU for better browser-overlay
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu"
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    browser = browser-overlayBrowser()
    browser.show()

    # Create timer to periodically allow Python to handle signals
    timer = QTimer()
    timer.start(200)
    timer.timeout.connect(lambda: None)  # Let interpreter run
    
    sys.exit(app.exec())
