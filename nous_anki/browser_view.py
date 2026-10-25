"""
Embedded Web Browser Widget for Nous Anki
Allows browsing medical resources, web search, or Nous City directly inside Anki.
"""

from typing import Optional
import urllib.parse

try:
    from aqt.qt import (
        QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
        QUrl, Qt
    )
    from PyQt6.QtWebEngineWidgets import QWebEngineView
except ImportError:
    class QWidget: pass
    class QVBoxLayout: pass
    class QHBoxLayout: pass
    class QLineEdit: pass
    class QPushButton: pass
    class QUrl:
        def __init__(self, s=""): pass
    class Qt: pass
    class QWebEngineView(QWidget):
        def setUrl(self, url): pass
        def load(self, url): pass
        def back(self): pass
        def forward(self): pass
        def reload(self): pass


class NousEmbeddedBrowser(QWidget):
    DEFAULT_HOME = "https://nous.study"

    def __init__(self, parent=None, home_url: str = DEFAULT_HOME):
        super().__init__(parent)
        self.home_url = home_url or self.DEFAULT_HOME
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # 1. Navigation & Address Bar
        nav_row = QHBoxLayout()
        nav_row.setSpacing(2)

        self.back_btn = QPushButton("◀")
        self.back_btn.setFixedWidth(28)
        self.back_btn.clicked.connect(self.go_back)

        self.fwd_btn = QPushButton("▶")
        self.fwd_btn.setFixedWidth(28)
        self.fwd_btn.clicked.connect(self.go_forward)

        self.reload_btn = QPushButton("⟳")
        self.reload_btn.setFixedWidth(28)
        self.reload_btn.clicked.connect(self.reload_page)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter URL or search query...")
        self.url_input.returnPressed.connect(self.navigate_to_input)

        self.go_btn = QPushButton("Go")
        self.go_btn.setFixedWidth(36)
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
            ("🏙️ City", "https://nous.study/city"),
            ("Amboss", "https://next.amboss.com/us/search?q="),
            ("Google", "https://www.google.com/search?q="),
            ("PubMed", "https://pubmed.ncbi.nlm.nih.gov/?term="),
            ("Wiki", "https://en.wikipedia.org/wiki/Special:Search?search="),
        ]

        for title, target in pills:
            btn = QPushButton(title)
            btn.setStyleSheet("font-size: 11px; padding: 2px 6px;")
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
