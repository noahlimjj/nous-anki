"""
Embedded Web Browser Widget for Nous Anki
Allows browsing medical resources, web search, or Nous City directly inside Anki.
Features lazy initialization so WebEngine is only allocated on demand.
"""

from typing import Optional
import urllib.parse
from .theme import NOUS_STYLESHEET, ensure_fonts_loaded

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton
    )
    from PyQt6.QtCore import QUrl, Qt
except ImportError:
    try:
        from aqt.qt import (
            QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
            QUrl, Qt
        )
    except ImportError:
        class QWidget:
            def __init__(self, *args, **kwargs): pass
            def setLayout(self, l): pass
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
        class Qt: pass


class NousEmbeddedBrowser(QWidget):
    DEFAULT_HOME = "https://nous.study"

    def __init__(self, parent=None, home_url: str = DEFAULT_HOME):
        super().__init__(parent)
        self.home_url = home_url or self.DEFAULT_HOME
        self._web_view = None
        self.setup_ui()

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
            self._web_view = QWebEngineView(self)
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
        except Exception:
            pass

        if hasattr(self, "content_layout") and hasattr(self._web_view, "setParent"):
            self.content_layout.addWidget(self._web_view)

        return self._web_view

    def setup_ui(self):
        ensure_fonts_loaded()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # 1. Navigation & Address Bar
        nav_row = QHBoxLayout()
        nav_row.setSpacing(4)

        self.back_btn = QPushButton("◀")
        self.back_btn.setProperty("class", "iconButton")
        self.back_btn.setFixedWidth(28)
        try:
            self.back_btn.clicked.connect(self.go_back)
        except Exception:
            pass

        self.fwd_btn = QPushButton("▶")
        self.fwd_btn.setProperty("class", "iconButton")
        self.fwd_btn.setFixedWidth(28)
        try:
            self.fwd_btn.clicked.connect(self.go_forward)
        except Exception:
            pass

        self.reload_btn = QPushButton("⟳")
        self.reload_btn.setProperty("class", "iconButton")
        self.reload_btn.setFixedWidth(28)
        try:
            self.reload_btn.clicked.connect(self.reload_page)
        except Exception:
            pass

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("enter url or search medical terms...")
        try:
            self.url_input.returnPressed.connect(self.navigate_to_input)
        except Exception:
            pass

        self.go_btn = QPushButton("go")
        self.go_btn.setProperty("class", "primaryButton")
        self.go_btn.setFixedWidth(38)
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
            ("city 🏙️", "https://nous.study/city"),
            ("amboss", "https://next.amboss.com/us/search?q="),
            ("google", "https://www.google.com/search?q="),
            ("pubmed", "https://pubmed.ncbi.nlm.nih.gov/?term="),
            ("wiki", "https://en.wikipedia.org/wiki/Special:Search?search="),
        ]

        for title, target in pills:
            btn = QPushButton(title)
            btn.setProperty("class", "actionButton")
            btn.setStyleSheet("font-size: 11px; font-weight: 400; padding: 3px 8px; border-radius: 12px;")
            try:
                btn.clicked.connect(lambda _, t=target: self.open_pill_target(t))
            except Exception:
                pass
            pills_row.addWidget(btn)

        layout.addLayout(pills_row)

        # 3. Content layout for lazy WebEngine View
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self.content_layout)

        self.url_input.setText(self.home_url)

    def showEvent(self, event):
        super().showEvent(event)
        if self._web_view is None:
            self.navigate(self.home_url)

    def navigate(self, url_str: str):
        url_str = url_str.strip()
        if not url_str:
            return

        # If it looks like a search query rather than a URL
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
            # If current input is a full URL, don't use it as query
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
