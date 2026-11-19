"""
Embedded Web Browser Widget for Nous Anki
Allows browsing medical resources, web search, or Nous City directly inside Anki.
Features lazy initialization so WebEngine is only allocated on demand,
OAuth popup support for Google Sign-In on nous.study, and automatic Firebase Auth token capture.
"""

import json
from typing import Callable, Dict, Any, Optional
import urllib.parse
from .theme import ensure_fonts_loaded, apply_satoshi_to_widget_tree, satoshi_font

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QDialog
    )
    from PyQt6.QtCore import QUrl, Qt, QTimer
except ImportError:
    try:
        from aqt.qt import (
            QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QDialog,
            QUrl, Qt, QTimer
        )
    except ImportError:
        class QWidget:
            def __init__(self, *args, **kwargs): pass
            def setLayout(self, l): pass
        class QDialog(QWidget): pass
        class QVBoxLayout:
            def __init__(self, *args, **kwargs): pass
            def addWidget(self, *args): pass
            def addLayout(self, *args): pass
            def setContentsMargins(self, *args): pass
            def setSpacing(self, *args): pass
        class QHBoxLayout:
            def __init__(self, *args, **kwargs): pass
            def addWidget(self, *args): pass
            def addLayout(self, *args): pass
            def setSpacing(self, *args): pass
        class QLineEdit:
            def __init__(self, *args, **kwargs): pass
            def text(self): return ""
            def setText(self, t): pass
            def setPlaceholderText(self, t): pass
            returnPressed = None
        class QPushButton:
            def __init__(self, *args, **kwargs): pass
            def setFixedWidth(self, w): pass
            def setStyleSheet(self, s): pass
            clicked = None
        class QUrl:
            def __init__(self, s=""): pass
            def toString(self): return ""
        class QTimer:
            def __init__(self, *args): pass
            def start(self, *args): pass
            timeout = None
        class Qt: pass


NOUS_AUTH_EXTRACT_JS = """
(function() {
    try {
        var auth = (typeof window.getAuth === 'function') ? window.getAuth() : (window.auth || null);
        var u = auth && auth.currentUser;
        if (u && !u.isAnonymous && u.uid) {
            var tm = u.stsTokenManager || {};
            var tok = tm.accessToken || "";
            var ref = tm.refreshToken || "";
            var exp = tm.expirationTime || 0;
            if (tok || ref) {
                return JSON.stringify({
                    uid: u.uid,
                    email: u.email || u.displayName || "",
                    idToken: tok,
                    refreshToken: ref,
                    expirationTime: exp
                });
            }
        }
    } catch (e) {}
    return "";
})();
"""


class NousEmbeddedBrowser(QWidget):
    DEFAULT_HOME = "https://nous.study"

    def __init__(
        self,
        parent=None,
        home_url: str = DEFAULT_HOME,
        on_auth_detected: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        super().__init__(parent)
        self.home_url = home_url or self.DEFAULT_HOME
        self.on_auth_detected = on_auth_detected
        self._web_view = None
        self._last_captured_uid = ""
        self._popup_dialogs = []
        self.setup_ui()

        self.auth_poll_timer = QTimer(self)
        try:
            self.auth_poll_timer.timeout.connect(self._poll_nous_auth)
            self.auth_poll_timer.start(2500)
        except Exception:
            pass

    @property
    def web_view(self):
        """Lazy property that creates the WebEngine view on first access."""
        if self._web_view is None:
            self._init_web_view()
        return self._web_view

    @web_view.setter
    def web_view(self, val):
        self._web_view = val

    def _init_web_view(self):
        if self._web_view is not None:
            return self._web_view
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            from PyQt6.QtWebEngineCore import QWebEnginePage

            outer = self

            class PopupSupportingWebView(QWebEngineView):
                def createWindow(self, window_type):
                    dlg = QDialog(outer)
                    dlg.setWindowTitle("nous sign in")
                    dlg.resize(480, 620)
                    lay = QVBoxLayout(dlg)
                    lay.setContentsMargins(0, 0, 0, 0)
                    child_view = QWebEngineView(dlg)
                    try:
                        child_page = QWebEnginePage(self.page().profile(), child_view)
                        child_view.setPage(child_page)
                        child_page.windowCloseRequested.connect(dlg.close)
                    except Exception:
                        pass
                    lay.addWidget(child_view)
                    dlg.show()
                    outer._popup_dialogs.append(dlg)
                    return child_view

            self._web_view = PopupSupportingWebView(self)
            try:
                # Set standard macOS Chrome User-Agent so Google OAuth popups never reject QtWebEngine
                profile = self._web_view.page().profile()
                profile.setHttpUserAgent(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
                )
            except Exception:
                pass
        except Exception:
            try:
                from aqt.webview import AnkiWebView
                self._web_view = AnkiWebView(self)
            except Exception:
                class DummyWebView(QWidget):
                    def load(self, *a): pass
                    def back(self): pass
                    def forward(self): pass
                    def reload(self): pass
                    urlChanged = None
                self._web_view = DummyWebView(self)

        try:
            if hasattr(self._web_view, "urlChanged") and self._web_view.urlChanged is not None:
                self._web_view.urlChanged.connect(lambda qurl: self.url_input.setText(qurl.toString()))
            if hasattr(self._web_view, "loadFinished") and self._web_view.loadFinished is not None:
                self._web_view.loadFinished.connect(lambda _: self._poll_nous_auth())
        except Exception:
            pass

        if hasattr(self, "content_layout") and hasattr(self._web_view, "setParent"):
            self.content_layout.addWidget(self._web_view)

        return self._web_view

    def _poll_nous_auth(self):
        """Extracts Firebase Auth tokens if the embedded browser is signed into nous.study."""
        if self._web_view is None or not self.on_auth_detected:
            return
        try:
            cur_url = self.url_input.text()
            if "nous.study" not in cur_url and "nousi.netlify.app" not in cur_url and "localhost" not in cur_url:
                return
            page = getattr(self._web_view, "page", lambda: None)()
            if page and hasattr(page, "runJavaScript"):
                def _on_js(res):
                    if not res or not isinstance(res, str):
                        return
                    try:
                        data = json.loads(res)
                        uid = data.get("uid", "")
                        tok = data.get("idToken", "")
                        if uid and tok and uid != self._last_captured_uid:
                            self._last_captured_uid = uid
                            self.on_auth_detected(data)
                    except Exception:
                        pass
                page.runJavaScript(NOUS_AUTH_EXTRACT_JS, _on_js)
        except Exception:
            pass

    def ensure_loaded(self):
        """Explicitly ensures WebEngine view is created."""
        return self.web_view

    def setup_ui(self):
        ensure_fonts_loaded()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 4, 2, 2)
        layout.setSpacing(6)

        # 1. Navigation & Address Bar
        nav_row = QHBoxLayout()
        nav_row.setSpacing(4)

        self.back_btn = QPushButton("◀")
        self.back_btn.setProperty("class", "iconButton")
        self.back_btn.setFixedWidth(26)
        try:
            self.back_btn.clicked.connect(self.go_back)
        except Exception:
            pass

        self.fwd_btn = QPushButton("▶")
        self.fwd_btn.setProperty("class", "iconButton")
        self.fwd_btn.setFixedWidth(26)
        try:
            self.fwd_btn.clicked.connect(self.go_forward)
        except Exception:
            pass

        self.reload_btn = QPushButton("⟳")
        self.reload_btn.setProperty("class", "iconButton")
        self.reload_btn.setFixedWidth(26)
        try:
            self.reload_btn.clicked.connect(self.reload_page)
        except Exception:
            pass

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("enter url or search medical terms…")
        try:
            self.url_input.returnPressed.connect(self.navigate_to_input)
        except Exception:
            pass

        self.go_btn = QPushButton("go")
        self.go_btn.setProperty("class", "primaryButton")
        self.go_btn.setFixedWidth(36)
        try:
            self.go_btn.clicked.connect(self.navigate_to_input)
        except Exception:
            pass

        nav_row.addWidget(self.back_btn)
        nav_row.addWidget(self.fwd_btn)
        nav_row.addWidget(self.reload_btn)
        nav_row.addWidget(self.url_input)
        nav_row.addWidget(self.go_btn)
        layout.addLayout(nav_row)

        # 2. Quick Bookmark Pills
        pills_row = QHBoxLayout()
        pills_row.setSpacing(4)

        pills = [
            ("nous", "https://nous.study"),
            ("city 🏙️", "https://nous.study/city"),
            ("amboss", "https://next.amboss.com/us/search?q="),
            ("pubmed", "https://pubmed.ncbi.nlm.nih.gov/?term="),
            ("wiki", "https://en.wikipedia.org/wiki/Special:Search?search="),
        ]

        for title, target in pills:
            btn = QPushButton(title)
            btn.setProperty("class", "actionButton")
            btn.setFont(satoshi_font(10, 500))
            btn.setStyleSheet("font-size: 10px; font-weight: 500; padding: 3px 7px; border-radius: 10px;")
            try:
                btn.clicked.connect(lambda _, t=target: self.open_pill_target(t))
            except Exception:
                pass
            pills_row.addWidget(btn)

        layout.addLayout(pills_row)

        # 3. Content layout for lazy WebEngine View
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self.content_layout, 1)

        self.url_input.setText(self.home_url)
        apply_satoshi_to_widget_tree(self)

    def showEvent(self, event):
        super().showEvent(event)
        if self._web_view is None:
            self.navigate(self.home_url)

    def go_home(self):
        self.navigate(self.home_url)

    def navigate(self, url_str: str):
        url_str = (url_str or "").strip()
        if not url_str:
            return

        if not (url_str.startswith("http://") or url_str.startswith("https://") or url_str.startswith("about:")):
            if "." in url_str and " " not in url_str:
                url_str = "https://" + url_str
            else:
                url_str = f"https://www.google.com/search?q={urllib.parse.quote_plus(url_str)}"

        self.url_input.setText(url_str)
        wv = self.web_view
        if wv and hasattr(wv, "load"):
            try:
                wv.load(QUrl(url_str))
            except Exception as e:
                print(f"[NousBrowser] Navigate error: {e}")

    def navigate_to_input(self):
        self.navigate(self.url_input.text())

    def open_pill_target(self, target: str):
        if target.endswith("=") or target.endswith("?q="):
            query = self.url_input.text().strip()
            if query.startswith("http"):
                query = ""
            if query:
                self.navigate(target + urllib.parse.quote_plus(query))
            else:
                self.navigate(target)
        else:
            self.navigate(target)

    def search_term(self, query: str, engine: str = "google"):
        if engine == "amboss":
            url = f"https://next.amboss.com/us/search?q={urllib.parse.quote_plus(query)}"
        elif engine == "pubmed":
            url = f"https://pubmed.ncbi.nlm.nih.gov/?term={urllib.parse.quote_plus(query)}"
        else:
            url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
        self.navigate(url)

    def go_back(self):
        try:
            if self._web_view and hasattr(self._web_view, "back"):
                self._web_view.back()
        except Exception:
            pass

    def go_forward(self):
        try:
            if self._web_view and hasattr(self._web_view, "forward"):
                self._web_view.forward()
        except Exception:
            pass

    def reload_page(self):
        try:
            if self._web_view and hasattr(self._web_view, "reload"):
                self._web_view.reload()
        except Exception:
            pass
