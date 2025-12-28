"""
Browser Overlay - Clean Final Version
Semi-transparent browser window that stays on top
"""
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import Qt, QUrl  # Added QUrl import
from PyQt6.QtWebEngineWidgets import QWebEngineView

app = QApplication(sys.argv)
window = QMainWindow()

# Overlay properties - Use correct Qt constants
# Different PyQt6 versions might need different syntax
try:
    # Try Qt.WindowType syntax (newer PyQt6)
    window.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                          Qt.WindowType.WindowStaysOnTopHint)
except AttributeError:
    # Fallback to direct Qt constants (older PyQt6)
    window.setWindowFlags(Qt.FramelessWindowHint |
                          Qt.WindowStaysOnTopHint)

window.setWindowOpacity(0.7)  # 70% transparent
window.resize(800, 600)

# Browser component - MUST use QUrl object, not string
browser = QWebEngineView()
browser.setUrl(QUrl("https://chat.openai.com"))  # FIXED: QUrl()
window.setCentralWidget(browser)

window.show()
sys.exit(app.exec())
