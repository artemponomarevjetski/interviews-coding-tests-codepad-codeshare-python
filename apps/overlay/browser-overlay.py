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
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage

def signal_handler(sig, frame):
    print("\n🛑 Ctrl+C pressed – shutting down...")
    app.quit()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# --- Permission handler ---
class WebEnginePage(QWebEnginePage):
    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)
        self.featurePermissionRequested.connect(self.on_feature_permission_requested)

    def on_feature_permission_requested(self, url, feature):
        if feature in (QWebEnginePage.Feature.MediaAudioCapture,
                       QWebEnginePage.Feature.MediaVideoCapture,
                       QWebEnginePage.Feature.MediaAudioVideoCapture):
            self.setFeaturePermission(url, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)
            print(f"✅ Microphone/Camera permission granted for {url.toString()}")
        else:
            self.setFeaturePermission(url, feature, QWebEnginePage.PermissionPolicy.PermissionDeniedByUser)
            print(f"⛔ Permission denied for {url.toString()} - {feature}")
# ---

app = QApplication(sys.argv)

profile = QWebEngineProfile("overlay", None)
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
window.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                      Qt.WindowType.WindowStaysOnTopHint)
window.setWindowOpacity(0.7)
window.resize(800, 600)

browser = QWebEngineView()
page = WebEnginePage(profile, browser)
browser.setPage(page)
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
