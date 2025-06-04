import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebEngineCore import QWebEngineProfile, QWebEnginePage, QWebEngineSettings
from dotenv import load_dotenv

# Load credentials securely
load_dotenv(os.path.expanduser('~/.secrets'))

class StealthPage(QWebEnginePage):
    def __init__(self, profile):
        super().__init__(profile)
        self.authenticated = False
        
    def javaScriptConsoleMessage(self, level, message, line, source):
        if "authenticated" in message.lower():
            self.authenticated = True

class InvisibleBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_browser()
        
    def init_ui(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.7)
        self.resize(900, 600)
        self.hide_dock_icon()
        
    def hide_dock_icon(self):
        try:
            from AppKit import NSApp, NSApplicationActivationPolicyAccessory
            NSApp.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
        except ImportError:
            pass
            
    def init_browser(self):
        self.profile = QWebEngineProfile("stealth_profile")
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
        
        self.browser = QWebEngineView()
        self.page = StealthPage(self.profile)
        self.browser.setPage(self.page)
        
        settings = self.browser.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        
        self.page.loadFinished.connect(self.on_load_finished)
        self.setCentralWidget(self.browser)
        
        url = os.getenv('DEFAULT_URL', 'https://chat.openai.com')
        self.browser.setUrl(QUrl(url))
    
    def on_load_finished(self, ok):
        if ok and not self.page.authenticated:
            QTimer.singleShot(2000, self.attempt_login)
    
    def attempt_login(self):
        js = f"""
        const user = document.querySelector('input[type="email"], input[name="username"]');
        const pass = document.querySelector('input[type="password"]');
        if (user && pass) {{
            user.value = '{os.getenv("API_USER")}';
            pass.value = '{os.getenv("API_PASS")}';
            pass.closest('form').submit();
            console.log('authenticated');
        }}
        """
        self.page.runJavaScript(js)
        QTimer.singleShot(3000, self.check_auth)
    
    def check_auth(self):
        if not self.page.authenticated:
            self.attempt_login()

if __name__ == "__main__":
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu"
    QApplication.setAttribute(Qt.AA_PluginApplication, True)
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    browser = InvisibleBrowser()
    browser.show()
    sys.exit(app.exec_())
