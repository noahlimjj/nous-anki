"""
Embedded Web Browser Widget for Nous Anki
Allows browsing medical resources, web search, or Nous City directly inside Anki.
"""

from typing import Optional
import urllib.parse
from .theme import NOUS_STYLESHEET, ensure_fonts_loaded

try:
    from aqt.qt import (
        QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
        QUrl, Qt
    )
    from PyQt6.QtWebEngineWidgets import QWebEngineView
except ImportError:
    try:
        from PyQt6.QtWidgets import (
            QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton
        )
        from PyQt6.QtCore import QUrl, Qt
        from PyQt6.QtWebEngineWidgets import QWebEngineView
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
        class QWebEngineView(QWidget):
            def __init__(self, *args, **kwargs): pass
            def setUrl(self, url): pass
            def load(self, url): pass
            def back(self): pass
            def forward(self): pass
            def reload(self): pass
            urlChanged = None


class NousEmbeddedBrowser(QWidget):
    DEFAULT_HOME = "https://nous.study"

    def __init__(self, parent=None, home_url: str = DEFAULT_HOME):
        super().__init__(parent)
        self.home_url = home_url or self.DEFAULT_HOME
        self.setup_ui()

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
        self.back_btn.clicked.connect(self.go_back)

        self.fwd_btn = QPushButton("▶")
        self.fwd_btn.setProperty("class", "iconButton")
        self.fwd_btn.setFixedWidth(28)
        self.fwd_btn.clicked.connect(self.go_forward)

        self.reload_btn = QPushButton("⟳")
        self.reload_btn.setProperty("class", "iconButton")
        self.reload_btn.setFixedWidth(28)
        self.reload_btn.clicked.connect(self.reload_page)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("enter url or search medical terms...")
        self.url_input.returnPressed.connect(self.navigate_to_input)

        self.go_btn = QPushButton("go")
        self.go_btn.setProperty("class", "primaryButton")
        self.go_btn.setFixedWidth(38)
        self.go_btn.clicked.connect(self.navigate_to_input)

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
            btn.clicked.connect(lambda _, t=target: self.open_pill_target(t))
            pills_row.addWidget(btn)

        layout.addLayout(pills_row)

        # 3. WebEngine View
        self.web_view = QWebEngineView(self)
        try:
            self.web_view.urlChanged.connect(lambda qurl: self.url_input.setText(qurl.toString()))
        except Exception:
            pass

        layout.addWidget(self.web_view)

        # Load home
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
        try:
            self.web_view.load(QUrl(url_str))
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
            self.web_view.back()
        except Exception:
            pass

    def go_forward(self):
        try:
            self.web_view.forward()
        except Exception:
            pass

    def reload_page(self):
        try:
            self.web_view.reload()
        except Exception:
            pass
