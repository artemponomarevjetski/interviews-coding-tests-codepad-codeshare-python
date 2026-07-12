"""
Browser Overlay – Semi-transparent, always-on-top window
"""
import sys
import os
import signal
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile

def signal_handler(sig, frame):
    print("\n🛑 Ctrl+C pressed – shutting down...")
    app.quit()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

app = QApplication(sys.argv)

profile = QWebEngineProfile.defaultProfile()
data_dir = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(data_dir, exist_ok=True)
profile.setPersistentStoragePath(data_dir)
profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)

profile.setHttpUserAgent(
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.0 Safari/605.1.15"
)

window = QMainWindow()

try:
    window.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                          Qt.WindowType.WindowStaysOnTopHint)
except AttributeError:
    window.setWindowFlags(Qt.FramelessWindowHint |
                          Qt.WindowStaysOnTopHint)

window.setWindowOpacity(0.7)
window.resize(800, 600)

browser = QWebEngineView()
browser.setUrl(QUrl("https://chat.openai.com"))
window.setCentralWidget(browser)

def toggle_window():
    if window.isVisible():
        window.hide()
    else:
        window.show()

shortcut = QShortcut(QKeySequence("Ctrl+Shift+H"), window)
shortcut.activated.connect(toggle_window)

window.show()
sys.exit(app.exec())
