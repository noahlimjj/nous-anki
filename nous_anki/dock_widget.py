"""
Nous Sidebar Dock Widget for Anki
Features:
1. 4-Tab Segmented Pill Navigation: Focus | AI | Notes | Web
2. Live Tree Growth & Progress (Nous tree-path.js) with Satoshi typography
3. Radial Focus Timer with animated ring, preset pills, authentic sound effects & instant sync
4. Inline Nous Account Sign-In (Email/Password + 1-Click Web/Google Auth capture)
5. Multi-Model AI Study Assistant (Gemini 2.5, Claude 4.5 Haiku/Sonnet, GPT-4o, Perplexity, DeepSeek, Ollama)
6. Study Notes Scratchpad with 1-Click Card Injection
7. Embedded Web Browser (Nous City, Amboss, PubMed, Wikipedia, Google)
"""

import html
import webbrowser
from typing import Any, Callable, Dict, Optional

try:
    from aqt.qt import (
        QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QLineEdit, QTextEdit, QTextBrowser, QPushButton, QProgressBar,
        QTabWidget, QFrame, QComboBox, Qt, QCursor
    )
    from aqt import mw
except ImportError:
    try:
        from PyQt6.QtWidgets import (
            QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
            QLineEdit, QTextEdit, QTextBrowser, QPushButton, QProgressBar,
            QTabWidget, QFrame, QComboBox
        )
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QCursor
        mw = None
    except ImportError:
        class QWidget:
            def __init__(self, *args, **kwargs): pass
            def setLayout(self, l): pass
            def setStyleSheet(self, s): pass
            def setObjectName(self, n): pass
            def hide(self): pass
            def show(self): pass
        class QDockWidget:
            def __init__(self, *args, **kwargs): pass
            def setWidget(self, w): pass
            def setStyleSheet(self, s): pass
        class QVBoxLayout:
            def __init__(self, *args, **kwargs): pass
            def addWidget(self, w, *args): pass
            def addLayout(self, l, *args): pass
            def addStretch(self, *args): pass
            def setContentsMargins(self, *args): pass
            def setSpacing(self, s): pass
        class QHBoxLayout:
            def __init__(self, *args, **kwargs): pass
            def addWidget(self, w, *args): pass
            def addStretch(self, *args): pass
            def addLayout(self, l, *args): pass
            def setContentsMargins(self, *args): pass
            def setSpacing(self, s): pass
        class QLabel:
            def __init__(self, *args, **kwargs): pass
            def setText(self, t): pass
            def text(self): return ""
            def setProperty(self, *args): pass
            def setStyleSheet(self, s): pass
            def setAlignment(self, a): pass
            def setWordWrap(self, w): pass
        class QLineEdit:
            def __init__(self, *args, **kwargs): pass
            def text(self): return ""
            def setText(self, t): pass
            def setPlaceholderText(self, t): pass
            def setEchoMode(self, m): pass
            def hide(self): pass
            def show(self): pass
            returnPressed = None
            class EchoMode:
                Password = None
        class QTextEdit:
            def __init__(self, *args, **kwargs): pass
            def toPlainText(self): return ""
            def setText(self, t): pass
            def clear(self): pass
            def setPlaceholderText(self, t): pass
            textChanged = None
        class QTextBrowser:
            def __init__(self, *args, **kwargs): pass
            def toPlainText(self): return ""
            def setPlainText(self, t): pass
            def setHtml(self, h): pass
            def setFixedHeight(self, h): pass
            def setStyleSheet(self, s): pass
            def setVerticalScrollBarPolicy(self, p): pass
            def setHorizontalScrollBarPolicy(self, p): pass
            def setPlaceholderText(self, t): pass
        class QPushButton:
            def __init__(self, *args, **kwargs): pass
            def setText(self, t): pass
            def setEnabled(self, e): pass
            def setProperty(self, *args): pass
            def setCursor(self, c): pass
            def setToolTip(self, t): pass
            def setFixedWidth(self, w): pass
            def setStyleSheet(self, s): pass
            clicked = None
        class QProgressBar:
            def __init__(self, *args, **kwargs): pass
            def setRange(self, *args): pass
            def setValue(self, v): pass
            def setFormat(self, f): pass
            def setTextVisible(self, b): pass
            def maximum(self): return 100
        class QTabWidget:
            def __init__(self, *args, **kwargs): pass
            def addTab(self, *args): pass
            def setCurrentIndex(self, i): pass
            def currentIndex(self): return 0
            def count(self): return 4
            def tabText(self, i): return ""
        class QFrame:
            def __init__(self, *args, **kwargs): pass
            def setProperty(self, *args): pass
            def setStyleSheet(self, s): pass
            def hide(self): pass
            def show(self): pass
        class QComboBox:
            def __init__(self, *args, **kwargs): pass
            def addItem(self, *args, **kwargs): pass
            def currentData(self): return None
            def count(self): return 0
            def itemData(self, i): return None
            def setCurrentIndex(self, i): pass
            currentIndexChanged = None
        class Qt:
            Horizontal = None
            RightDockWidgetArea = None
            class AlignmentFlag:
                AlignCenter = None
            class ScrollBarPolicy:
                ScrollBarAlwaysOff = None
            class CursorShape:
                PointingHandCursor = None
        mw = None

from . import tree
from .ai_search import (
    AISearchClient,
    POPULAR_MODELS,
    detect_key_provider,
    infer_provider_from_model,
    looks_like_model_name,
    normalize_model_name,
    sanitize_ai_config,
)
from .browser_view import NousEmbeddedBrowser
from .notes import NotesManager
from .sound import NousSoundPlayer
from .sync import NousSyncService
from .timer_widget import NousTimerWidget
from .tree_widget import NousTreeWidget
from .theme import (
    NOUS_STYLESHEET, ensure_fonts_loaded, get_nous_stylesheet,
    is_night_mode, satoshi_font, apply_satoshi_to_widget_tree
)


def format_markdown_for_qt(raw_text: str, is_dark: bool = False) -> str:
    """Formats markdown into clean, styled HTML for QTextBrowser."""
    import re
    text = html.escape(raw_text)

    h_color = "#c4b5fd" if is_dark else "#5f5390"
    b_color = "#a78bfa" if is_dark else "#6d28d9"
    c_bg = "#2d2d38" if is_dark else "#f1eef8"
    c_fg = "#e2e8f0" if is_dark else "#4b5563"

    text = re.sub(r"^###\s+(.+)$", rf"<div style='font-size:1.05em;font-weight:600;margin:6px 0 2px 0;color:{h_color};'>\1</div>", text, flags=re.MULTILINE)
    text = re.sub(r"^##\s+(.+)$", rf"<div style='font-size:1.15em;font-weight:600;margin:8px 0 3px 0;color:{h_color};'>\1</div>", text, flags=re.MULTILINE)
    text = re.sub(r"^#\s+(.+)$", rf"<div style='font-size:1.25em;font-weight:600;margin:10px 0 4px 0;color:{h_color};'>\1</div>", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.+?)\*\*", rf"<b style='font-weight:600;color:{b_color};'>\1</b>", text)
    text = re.sub(r"`([^`]+)`", rf"<code style='background:{c_bg};color:{c_fg};padding:1px 5px;border-radius:4px;font-size:0.9em;'>\1</code>", text)

    lines = []
    in_list = False
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("* ") or stripped.startswith("- ") or stripped.startswith("• "):
            if not in_list:
                lines.append("<ul style='margin:4px 0;padding-left:18px;'>")
                in_list = True
            item = stripped[2:].strip()
            lines.append(f"<li style='margin-bottom:4px;line-height:1.4;'>{item}</li>")
        else:
            if in_list:
                lines.append("</ul>")
                in_list = False
            if stripped:
                lines.append(f"<p style='margin:4px 0;line-height:1.4;'>{stripped}</p>")
    if in_list:
        lines.append("</ul>")
    return "".join(lines)


class NousDockWidget(QDockWidget):
    TITLE = "Nous"

    # Tab indices
    TAB_FOCUS = 0
    TAB_AI = 1
    TAB_NOTES = 2
    TAB_WEB = 3

    def __init__(
        self,
        parent,
        sync_service: NousSyncService,
        notes_mgr: NotesManager,
        sound_player: NousSoundPlayer,
        config: Dict[str, Any],
        on_open_settings: Optional[Callable[[], None]] = None,
        on_config_changed: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        super().__init__(self.TITLE, parent)
        self.sync_service = sync_service
        self.notes_mgr = notes_mgr
        self.sound = sound_player
        self.config = sanitize_ai_config(config)
        self.on_open_settings = on_open_settings
        self.on_config_changed = on_config_changed
        self.current_card = None

        self.ai_client = AISearchClient(
            provider=self.config.get("ai_provider", "gemini"),
            api_key=self.config.get("ai_api_key", ""),
            model=self.config.get("ai_model", "gemini-2.5-flash"),
            base_url=self.config.get("ai_base_url", "")
        )
        self.ai_client.set_config_keys(self.config)

        # Ensure userId from config is loaded into sync_service if not yet present
        cfg_uid = (self.config.get("nous_user_id") or "").strip()
        if cfg_uid and not self.sync_service.cached_state.get("userId"):
            self.sync_service.cached_state["userId"] = cfg_uid

        ensure_fonts_loaded()
        self.setup_ui()
        self.setStyleSheet(get_nous_stylesheet(self.is_dark_mode()))
        apply_satoshi_to_widget_tree(self)
        self.sync_model_combo_from_config()
        self.refresh_account_card()
        self.refresh_tree_display()

        # Auto sign-in on startup if email & password are saved in config but no active token exists
        self._attempt_startup_signin()

    def is_dark_mode(self) -> bool:
        return is_night_mode()

    def apply_config(self, new_config: Dict[str, Any]):
        """Updates dock widget state and AI client when settings are saved."""
        self.config = sanitize_ai_config(new_config)
        self.ai_client.set_config_keys(self.config)
        self.sync_model_combo_from_config()
        self._refresh_inline_key_bar()
        self.refresh_account_card()
        self.refresh_tree_display()

    def _attempt_startup_signin(self):
        if self.sync_service.is_authenticated():
            return
        email = (self.config.get("nous_email") or "").strip()
        pwd = self.config.get("nous_password") or ""
        if email and pwd:
            import threading
            def _bg_login():
                res = self.sync_service.sign_in(email, pwd)
                if res.get("success"):
                    habit = self.config.get("nous_habit_name", "Anki")
                    self.sync_service.flush_pending(habit)
                    self.sync_service.fetch_user_stats()
                    if mw and hasattr(mw, "taskman"):
                        mw.taskman.run_on_main(self._on_auth_state_updated)
            threading.Thread(target=_bg_login, daemon=True).start()

    def _on_auth_state_updated(self):
        self.refresh_account_card()
        self.refresh_tree_display()

    def setup_ui(self):
        fam = ensure_fonts_loaded()
        container = QWidget()
        container.setObjectName("nousDockContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # TOP 4-TAB SEGMENTED PILL BAR: Focus | AI | Notes | Web
        self.tabs = QTabWidget()

        # ================================================================
        # TAB 0: FOCUS (Tree Card + Radial Timer Card + Account Sync Card)
        # ================================================================
        focus_tab = QWidget()
        focus_layout = QVBoxLayout(focus_tab)
        focus_layout.setContentsMargins(0, 4, 0, 0)
        focus_layout.setSpacing(8)

        # 1. TREE & GAMIFICATION CARD
        self.tree_card = QFrame()
        self.tree_card.setProperty("class", "treeCard")
        tree_layout = QVBoxLayout(self.tree_card)
        tree_layout.setContentsMargins(12, 10, 12, 11)
        tree_layout.setSpacing(6)

        # Header: Tree Name + Blurb on left, Tier Badge on right
        name_tier_row = QHBoxLayout()
        name_col = QVBoxLayout()
        name_col.setContentsMargins(0, 0, 0, 0)
        name_col.setSpacing(1)

        self.tree_name_label = QLabel("oak")
        self.tree_name_label.setProperty("class", "treeName")
        self.tree_name_label.setFont(satoshi_font(16, 500))

        self.tree_blurb_label = QLabel("sturdy, patient, and older than it looks.")
        self.tree_blurb_label.setProperty("class", "treeBlurb")
        self.tree_blurb_label.setFont(satoshi_font(10, 300))
        self.tree_blurb_label.setStyleSheet(f"font-family: '{fam}'; font-size: 10px; color: #7d8ca8; font-weight: 300;")

        name_col.addWidget(self.tree_name_label)
        name_col.addWidget(self.tree_blurb_label)

        self.tier_badge = QLabel("rare")
        self.tier_badge.setProperty("class", "tierBadge")
        self.tier_badge.setFont(satoshi_font(10, 500))
        try:
            self.tier_badge.setFixedHeight(22)
        except Exception:
            pass
        self.tier_badge.setStyleSheet(
            f"font-family: '{fam}'; background-color: #eff6ff; color: #2563eb; "
            "border: 1px solid #bfdbfe; border-radius: 11px; padding: 2px 10px; font-size: 10px; font-weight: 500;"
        )

        name_tier_row.addLayout(name_col)
        name_tier_row.addStretch()
        name_tier_row.addWidget(self.tier_badge)
        tree_layout.addLayout(name_tier_row)

        # Animated Vector Tree Canvas
        self.tree_view = NousTreeWidget(self)
        self.tree_svg_view = self.tree_view
        tree_layout.addWidget(self.tree_view)

        # Slim Teal-to-Purple Progress Bar
        self.tree_progress = QProgressBar()
        self.tree_progress.setRange(0, 100)
        self.tree_progress.setValue(0)
        self.tree_progress.setTextVisible(False)
        tree_layout.addWidget(self.tree_progress)

        # Single-Row Progress Meta Strip
        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 0, 0, 0)
        self.tree_caption_label = QLabel("0.0 / 1.0h (1.0h to bloom)")
        self.tree_caption_label.setFont(satoshi_font(11, 500))
        self.tree_caption_label.setStyleSheet(f"font-family: '{fam}'; font-size: 11px; color: #363f51; font-weight: 500;")

        self.overall_label = QLabel("0.0h · 0/35 🌲")
        self.overall_label.setFont(satoshi_font(11, 400))
        self.overall_label.setStyleSheet(f"font-family: '{fam}'; font-size: 11px; color: #7d8ca8; font-weight: 400;")

        meta_row.addWidget(self.tree_caption_label)
        meta_row.addStretch()
        meta_row.addWidget(self.overall_label)
        tree_layout.addLayout(meta_row)

        # City Action Row
        city_row = QHBoxLayout()
        city_row.setSpacing(6)
        self.city_btn = QPushButton("🏙️ open nous city")
        self.city_btn.setProperty("class", "actionButton")
        self.city_btn.setFont(satoshi_font(11, 500))
        if hasattr(Qt, "CursorShape"):
            self.city_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.city_btn.clicked.connect(self.open_city_link)

        self.city_embed_btn = QPushButton("view in tab ↗")
        self.city_embed_btn.setProperty("class", "ghostLinkButton")
        self.city_embed_btn.setFont(satoshi_font(11, 500))
        if hasattr(Qt, "CursorShape"):
            self.city_embed_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.city_embed_btn.clicked.connect(self.open_city_in_embedded_browser)

        city_row.addWidget(self.city_btn)
        city_row.addStretch()
        city_row.addWidget(self.city_embed_btn)
        tree_layout.addLayout(city_row)

        focus_layout.addWidget(self.tree_card)

        # 2. RADIAL FOCUS TIMER CARD
        self.timer_widget = NousTimerWidget(
            self,
            sync_service=self.sync_service,
            sound_player=self.sound,
            on_synced=self._on_timer_synced,
            on_auth_needed=self.focus_signin_prompt
        )
        focus_layout.addWidget(self.timer_widget)

        # 3. NOUS ACCOUNT & INSTANT SYNC CARD
        self.account_card = QFrame()
        self.account_card.setProperty("class", "accountCard")
        acc_layout = QVBoxLayout(self.account_card)
        acc_layout.setContentsMargins(12, 9, 12, 10)
        acc_layout.setSpacing(5)

        # Signed-Out View (Inline Sign-In Prompt)
        self.signin_box = QWidget()
        signin_layout = QVBoxLayout(self.signin_box)
        signin_layout.setContentsMargins(0, 0, 0, 0)
        signin_layout.setSpacing(5)

        self.signin_title = QLabel("🔒 sign in to nous to sync focus & card hours")
        self.signin_title.setFont(satoshi_font(11, 500))
        self.signin_title.setStyleSheet(f"font-family: '{fam}'; font-size: 11px; font-weight: 500; color: #5f5390;")
        signin_layout.addWidget(self.signin_title)

        creds_row = QHBoxLayout()
        creds_row.setSpacing(5)
        self.quick_email_input = QLineEdit(self.config.get("nous_email", ""))
        self.quick_email_input.setPlaceholderText("nous email")
        self.quick_password_input = QLineEdit(self.config.get("nous_password", ""))
        self.quick_password_input.setPlaceholderText("password")
        try:
            self.quick_password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.quick_password_input.returnPressed.connect(self.quick_sign_in)
        except Exception:
            pass
        creds_row.addWidget(self.quick_email_input, 1)
        creds_row.addWidget(self.quick_password_input, 1)
        signin_layout.addLayout(creds_row)

        signin_btn_row = QHBoxLayout()
        signin_btn_row.setSpacing(5)
        self.quick_signin_btn = QPushButton("sign in && sync")
        self.quick_signin_btn.setProperty("class", "primaryButton")
        self.quick_signin_btn.setFont(satoshi_font(10, 500))
        self.quick_signin_btn.clicked.connect(self.quick_sign_in)

        self.web_signin_btn = QPushButton("google / web login ↗")
        self.web_signin_btn.setProperty("class", "actionButton")
        self.web_signin_btn.setFont(satoshi_font(10, 500))
        self.web_signin_btn.setToolTip("Sign in with Google or Email in the Web tab to auto-connect")
        self.web_signin_btn.clicked.connect(self.open_web_login)

        signin_btn_row.addWidget(self.quick_signin_btn)
        signin_btn_row.addWidget(self.web_signin_btn)
        signin_layout.addLayout(signin_btn_row)

        self.account_status_label = QLabel("")
        self.account_status_label.setFont(satoshi_font(10, 400))
        self.account_status_label.setStyleSheet(f"font-family: '{fam}'; font-size: 10px; color: #7d8ca8;")
        signin_layout.addWidget(self.account_status_label)

        acc_layout.addWidget(self.signin_box)

        # Signed-In View (Connected Account Strip)
        self.connected_box = QWidget()
        conn_row = QHBoxLayout(self.connected_box)
        conn_row.setContentsMargins(0, 0, 0, 0)
        conn_row.setSpacing(6)

        self.connected_label = QLabel("🟢 connected to nous")
        self.connected_label.setFont(satoshi_font(10, 500))
        self.connected_label.setStyleSheet(f"font-family: '{fam}'; font-size: 10px; color: #363f51; font-weight: 500;")

        self.quick_sync_now_btn = QPushButton("↻ sync now")
        self.quick_sync_now_btn.setProperty("class", "actionButton")
        self.quick_sync_now_btn.setFont(satoshi_font(10, 500))
        self.quick_sync_now_btn.setStyleSheet(
            f"font-family: '{fam}'; font-size: 10px; font-weight: 500; padding: 3px 9px; "
            "background-color: #f1eef8; color: #5f5390; border: 1px solid #e2ddf0; border-radius: 10px;"
        )
        self.quick_sync_now_btn.clicked.connect(self.trigger_manual_sync)

        conn_row.addWidget(self.connected_label, 1)
        conn_row.addWidget(self.quick_sync_now_btn, 0)
        acc_layout.addWidget(self.connected_box)

        focus_layout.addWidget(self.account_card)
        focus_layout.addStretch(1)

        self.tabs.addTab(focus_tab, "🌲 focus")

        # ================================================================
        # TAB 1: AI STUDY ASSISTANT
        # ================================================================
        ai_tab = QWidget()
        ai_layout = QVBoxLayout(ai_tab)
        ai_layout.setContentsMargins(2, 6, 2, 2)
        ai_layout.setSpacing(6)

        model_row = QHBoxLayout()
        model_label = QLabel("model:")
        model_label.setFont(satoshi_font(11, 500))
        model_label.setStyleSheet(f"font-family: '{fam}'; font-size: 11px; font-weight: 500; color: #5f5390;")
        self.model_combo = QComboBox()
        try:
            from PyQt6.QtWidgets import QListView
            self.model_combo.setView(QListView())
        except Exception:
            pass
        if hasattr(Qt, "CursorShape"):
            self.model_combo.setCursor(Qt.CursorShape.PointingHandCursor)

        for label, prov, mname in POPULAR_MODELS:
            self.model_combo.addItem(label, userData=(prov, mname))

        self.toggle_key_bar_btn = QPushButton("🔑")
        self.toggle_key_bar_btn.setProperty("class", "iconButton")
        self.toggle_key_bar_btn.setToolTip("Paste or change API key for this model")
        self.toggle_key_bar_btn.clicked.connect(self._toggle_inline_key_bar)

        self.custom_model_input = QLineEdit()
        self.custom_model_input.setPlaceholderText("any custom model (e.g. claude-haiku-4-5, gpt-4o)…")
        self.custom_model_input.hide()

        # Inline quick API key bar (auto-shown when no key is set for the chosen provider)
        self.quick_key_box = QWidget()
        qk_layout = QHBoxLayout(self.quick_key_box)
        qk_layout.setContentsMargins(0, 0, 0, 0)
        qk_layout.setSpacing(4)
        self.inline_key_input = QLineEdit()
        self.inline_key_input.setPlaceholderText("paste claude key (sk-ant-...) or gemini key (AIza...)…")
        try:
            self.inline_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.inline_key_input.returnPressed.connect(self.save_inline_api_key)
        except Exception:
            pass
        self.inline_key_save_btn = QPushButton("save key")
        self.inline_key_save_btn.setProperty("class", "actionButton")
        self.inline_key_save_btn.clicked.connect(self.save_inline_api_key)
        qk_layout.addWidget(self.inline_key_input, 1)
        qk_layout.addWidget(self.inline_key_save_btn)
        self.quick_key_box.hide()

        self.model_combo.currentIndexChanged.connect(self._on_model_combo_changed)

        model_row.addWidget(model_label)
        model_row.addWidget(self.model_combo, 1)
        model_row.addWidget(self.toggle_key_bar_btn)
        ai_layout.addLayout(model_row)
        ai_layout.addWidget(self.custom_model_input)
        ai_layout.addWidget(self.quick_key_box)

        q_row = QHBoxLayout()
        q_row.setSpacing(5)
        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("ask any question or explain card…")
        self.ai_input.returnPressed.connect(self.run_ai_search)

        self.ask_btn = QPushButton("ask")
        self.ask_btn.setProperty("class", "primaryButton")
        self.ask_btn.clicked.connect(self.run_ai_search)

        self.explain_card_btn = QPushButton("✦ card")
        self.explain_card_btn.setProperty("class", "actionButton")
        self.explain_card_btn.setToolTip("Explain current active flashcard")
        self.explain_card_btn.clicked.connect(self.explain_current_card)

        q_row.addWidget(self.ai_input, 1)
        q_row.addWidget(self.ask_btn)
        q_row.addWidget(self.explain_card_btn)
        ai_layout.addLayout(q_row)

        self.ai_result_view = QTextBrowser()
        self.ai_result_view.setPlaceholderText("ai explanations, clinical pearls, and mnemonics appear here…")
        ai_layout.addWidget(self.ai_result_view, 1)

        ai_act_row = QHBoxLayout()
        self.copy_to_notes_btn = QPushButton("copy to notes")
        self.copy_to_notes_btn.setProperty("class", "actionButton")
        self.copy_to_notes_btn.clicked.connect(self.copy_search_to_notes)

        self.add_to_card_btn = QPushButton("add to card")
        self.add_to_card_btn.setProperty("class", "actionButton")
        self.add_to_card_btn.clicked.connect(self.add_search_to_card)

        ai_act_row.addWidget(self.copy_to_notes_btn)
        ai_act_row.addWidget(self.add_to_card_btn)
        ai_layout.addLayout(ai_act_row)

        self.tabs.addTab(ai_tab, "✨ ai")

        # ================================================================
        # TAB 2: STUDY NOTES
        # ================================================================
        notes_tab = QWidget()
        notes_layout = QVBoxLayout(notes_tab)
        notes_layout.setContentsMargins(2, 6, 2, 2)
        notes_layout.setSpacing(6)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("study notes, mnemonics, scratchpad…")
        self.notes_edit.setText(self.notes_mgr.load_scratchpad())
        self.notes_edit.textChanged.connect(self.on_notes_changed)
        notes_layout.addWidget(self.notes_edit, 1)

        notes_btn_row = QHBoxLayout()
        self.append_card_btn = QPushButton("append to card")
        self.append_card_btn.setProperty("class", "primaryButton")
        self.append_card_btn.clicked.connect(self.append_notes_to_active_card)

        self.clear_notes_btn = QPushButton("clear")
        self.clear_notes_btn.setProperty("class", "actionButton")
        self.clear_notes_btn.clicked.connect(self.clear_notes)

        notes_btn_row.addWidget(self.append_card_btn)
        notes_btn_row.addWidget(self.clear_notes_btn)
        notes_layout.addLayout(notes_btn_row)

        self.tabs.addTab(notes_tab, "📝 notes")

        # ================================================================
        # TAB 3: EMBEDDED WEB BROWSER
        # ================================================================
        self.browser_view = NousEmbeddedBrowser(
            self,
            home_url=self.config.get("nous_city_url", "https://nous.study/city"),
            on_auth_detected=self._on_web_auth_detected
        )
        self.tabs.addTab(self.browser_view, "🌐 web")

        layout.addWidget(self.tabs, 1)

        # ================================================================
        # FOOTER BAR
        # ================================================================
        footer_row = QHBoxLayout()
        footer_row.setContentsMargins(2, 0, 2, 0)
        footer_row.setSpacing(5)

        self.sync_status_label = QLabel("🟢 active: 0s (0 cards)")
        self.sync_status_label.setFont(satoshi_font(10, 400))
        self.sync_status_label.setStyleSheet(f"font-family: '{fam}'; font-size: 10px; color: #7d8ca8; font-weight: 400;")
        footer_row.addWidget(self.sync_status_label)
        footer_row.addStretch()

        self.manual_sync_btn = QPushButton("↻ sync")
        self.manual_sync_btn.setProperty("class", "ghostLinkButton")
        self.manual_sync_btn.setFont(satoshi_font(10, 500))
        self.manual_sync_btn.clicked.connect(self.trigger_manual_sync)
        footer_row.addWidget(self.manual_sync_btn)

        self.folder_btn = QPushButton("📁")
        self.folder_btn.setProperty("class", "iconButton")
        self.folder_btn.setToolTip("Open add-on folder in Finder")
        self.folder_btn.clicked.connect(self.open_folder)
        footer_row.addWidget(self.folder_btn)

        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setProperty("class", "iconButton")
        self.settings_btn.setToolTip("Open Nous Anki settings")
        self.settings_btn.clicked.connect(self.open_settings)
        footer_row.addWidget(self.settings_btn)

        layout.addLayout(footer_row)
        self.setWidget(container)

    def open_folder(self):
        try:
            import os, subprocess
            base_dir = os.path.dirname(os.path.abspath(__file__))
            subprocess.run(["open", base_dir])
        except Exception as e:
            print(f"[Nous Anki] Open folder error: {e}")

    def open_settings(self):
        if self.on_open_settings:
            self.on_open_settings()

    # ---------------- Account & Quick Sign-In Logic ----------------

    def refresh_account_card(self):
        is_auth = self.sync_service.is_authenticated()
        queued = len(self.sync_service.get_pending_queue())
        if is_auth:
            self.signin_box.hide()
            self.connected_box.show()
            who = (
                self.sync_service.cached_state.get("email")
                or self.config.get("nous_email")
                or self.sync_service.cached_state.get("userId", "")[:10]
            )
            q_str = f" · {queued} queued" if queued > 0 else ""
            self.connected_label.setText(f"🟢 {who}{q_str}")
        else:
            self.connected_box.hide()
            self.signin_box.show()
            if queued > 0:
                self.account_status_label.setText(f"{queued} session(s) queued offline — sign in to sync")
                self.account_status_label.setStyleSheet("font-size: 10px; color: #d97706; font-weight: 500;")
            else:
                self.account_status_label.setText("")

    def focus_signin_prompt(self):
        self.tabs.setCurrentIndex(self.TAB_FOCUS)
        self.refresh_account_card()
        try:
            self.quick_email_input.setFocus()
        except Exception:
            pass

    def quick_sign_in(self):
        email = self.quick_email_input.text().strip()
        pwd = self.quick_password_input.text()
        if not email or not pwd:
            self.account_status_label.setText("enter your nous email & password, or use google/web login ↗")
            self.account_status_label.setStyleSheet("font-size: 10px; color: #d97706; font-weight: 500;")
            return

        self.account_status_label.setText("signing in & syncing to nous…")
        self.account_status_label.setStyleSheet("font-size: 10px; color: #8B7FB8; font-weight: 500;")
        self.quick_signin_btn.setEnabled(False)

        import threading
        def _run():
            res = self.sync_service.sign_in(email, pwd)
            if res.get("success"):
                uid = res.get("userId", "")
                self.config["nous_email"] = email
                self.config["nous_password"] = pwd
                self.config["nous_user_id"] = uid
                habit = self.config.get("nous_habit_name", "Anki")
                self.sync_service.flush_pending(habit)
                self.sync_service.fetch_user_stats()

            def _ui():
                self.quick_signin_btn.setEnabled(True)
                if res.get("success"):
                    if self.on_config_changed:
                        self.on_config_changed(self.config)
                    self.refresh_account_card()
                    self.refresh_tree_display()
                    self.sync_status_label.setText("🟢 signed in & synced to nous")
                else:
                    err = res.get("error", "sign-in failed")
                    self.account_status_label.setText(f"sign-in failed: {err}")
                    self.account_status_label.setStyleSheet("font-size: 10px; color: #ef4444; font-weight: 500;")

            if mw and hasattr(mw, "taskman"):
                mw.taskman.run_on_main(_ui)
            else:
                _ui()

        threading.Thread(target=_run, daemon=True).start()

    def open_web_login(self):
        """Switches to the embedded Web tab at nous.study so user can log in via Google or Email."""
        self.tabs.setCurrentIndex(self.TAB_WEB)
        self.browser_view.navigate("https://nous.study")

    def _on_web_auth_detected(self, auth_data: Dict[str, Any]):
        """Called automatically when the embedded browser detects a signed-in user on nous.study."""
        uid = auth_data.get("uid", "")
        email = auth_data.get("email", "")
        id_token = auth_data.get("idToken", "")
        refresh_token = auth_data.get("refreshToken", "")
        exp = float(auth_data.get("expirationTime", 0) or 0)

        if not uid or not (id_token or refresh_token):
            return

        self.sync_service.set_web_auth(uid, email, id_token, refresh_token, exp)
        self.config["nous_user_id"] = uid
        if email:
            self.config["nous_email"] = email
        if self.on_config_changed:
            self.on_config_changed(self.config)

        habit = self.config.get("nous_habit_name", "Anki")
        def _after_sync(ok: bool, flushed: int):
            def _ui():
                self.refresh_account_card()
                self.refresh_tree_display()
                self.sync_status_label.setText(f"🟢 synced to nous ({email or uid[:8]})")
            if mw and hasattr(mw, "taskman"):
                mw.taskman.run_on_main(_ui)
            else:
                _ui()

        self.sync_service.process_and_sync(habit_name=habit, min_ms=1000, on_done=_after_sync)

    # ---------------- Model Selector Handler ----------------

    def sync_model_combo_from_config(self):
        """Aligns the AI tab model selector with the configured provider/model/key."""
        prov = (self.config.get("ai_provider") or "gemini").lower()
        if "claude" in prov:
            prov = "anthropic"
        model_name = normalize_model_name(self.config.get("ai_model") or "", prov)

        # If only a Claude key is configured and provider was left on default, prefer Claude Haiku
        primary_kind = detect_key_provider(self.config.get("ai_api_key", ""))
        if (primary_kind == "anthropic" or self.config.get("anthropic_api_key")) and not self.config.get("gemini_api_key"):
            if prov == "gemini":
                prov = "anthropic"
                if "claude" not in model_name.lower():
                    model_name = "claude-haiku-4-5"

        try:
            cnt = self.model_combo.count()
            # 1. Exact model match
            for i in range(cnt):
                data = self.model_combo.itemData(i)
                if data and data[1] == model_name and model_name:
                    self.model_combo.setCurrentIndex(i)
                    self._refresh_inline_key_bar()
                    return
            # 2. Provider match
            for i in range(cnt):
                data = self.model_combo.itemData(i)
                if data and data[0] == prov:
                    self.model_combo.setCurrentIndex(i)
                    self._refresh_inline_key_bar()
                    return
        except Exception:
            pass
        self._refresh_inline_key_bar()

    def _on_model_combo_changed(self, idx: int):
        data = self.model_combo.currentData()
        if data and data[0] == "custom":
            self.tabs.setCurrentIndex(self.TAB_AI)
            self.custom_model_input.show()
        else:
            self.custom_model_input.hide()
        self._refresh_inline_key_bar()

    def _toggle_inline_key_bar(self):
        if hasattr(self, "quick_key_box"):
            if self.quick_key_box.isVisible():
                self.quick_key_box.hide()
            else:
                self._refresh_inline_key_bar(force_show=True)

    def _refresh_inline_key_bar(self, force_show: bool = False):
        if not hasattr(self, "quick_key_box"):
            return
        prov, model_name = self.get_selected_model_and_provider()
        placeholders = {
            "anthropic": "paste claude api key (starts with sk-ant-...)…",
            "gemini": "paste gemini api key (starts with AIza...)…",
            "openai": "paste openai api key (starts with sk-...)…",
            "perplexity": "paste perplexity api key (starts with pplx-...)…",
        }
        self.inline_key_input.setPlaceholderText(placeholders.get(prov, "paste api key…"))
        _, _, key, err = self.ai_client._resolve_execution(prov, model_name)
        if force_show or not key or err:
            self.quick_key_box.show()
        else:
            self.quick_key_box.hide()

    def save_inline_api_key(self) -> bool:
        """Saves an API key pasted directly into the AI tab's inline key bar."""
        raw = self.inline_key_input.text().strip()
        if not raw:
            return False

        if looks_like_model_name(raw):
            norm = normalize_model_name(raw)
            inferred = infer_provider_from_model(norm, "anthropic")
            self.config["ai_provider"] = inferred
            self.config["ai_model"] = norm
            self.inline_key_input.setText("")
            self.sync_model_combo_from_config()
            self.ai_result_view.setHtml(
                f"<span style='color: #d97706;'><b>{html.escape(raw)}</b> is a model name (switched model to "
                f"<b>{html.escape(norm)}</b>). Now paste your <b>{inferred.title()} API key</b> "
                f"(e.g. <code>sk-ant-...</code>) into the key box above.</span>"
            )
            return False

        prov, _ = self.get_selected_model_and_provider()
        detected = detect_key_provider(raw)
        target_prov = detected or prov
        self.config["ai_api_key"] = raw
        self.config[f"{target_prov}_api_key"] = raw
        if detected and detected != prov:
            self.config["ai_provider"] = detected
            if detected == "anthropic":
                self.config["ai_model"] = "claude-haiku-4-5"
            elif detected == "gemini":
                self.config["ai_model"] = "gemini-2.5-flash"
            elif detected == "openai":
                self.config["ai_model"] = "gpt-4o-mini"
        self.config.pop("_misplaced_model_in_key", None)
        self.inline_key_input.setText("")
        self.ai_client.set_config_keys(self.config)
        self.sync_model_combo_from_config()
        if self.on_config_changed:
            self.on_config_changed(self.config)
        self.quick_key_box.hide()
        self.ai_result_view.setHtml(
            f"<span style='color: #10b981; font-weight: 500;'>✓ saved {html.escape(target_prov.title())} API key — ready to ask!</span>"
        )
        return True

    def get_selected_model_and_provider(self):
        data = self.model_combo.currentData()
        if not data:
            return "gemini", "gemini-2.5-flash"
        prov, mname = data
        if prov == "custom":
            custom_raw = self.custom_model_input.text().strip()
            # If user pasted an API key into the custom model input box, capture it gracefully
            detected_key_prov = detect_key_provider(custom_raw)
            if detected_key_prov:
                self.config["ai_api_key"] = custom_raw
                self.config[f"{detected_key_prov}_api_key"] = custom_raw
                self.ai_client.set_config_keys(self.config)
                default_m = "claude-haiku-4-5" if detected_key_prov == "anthropic" else (
                    "gemini-2.5-flash" if detected_key_prov == "gemini" else "gpt-4o-mini"
                )
                return detected_key_prov, default_m

            fallback_model = self.config.get("ai_model") or "gpt-4o-mini"
            custom_name = custom_raw or fallback_model
            inferred_prov = infer_provider_from_model(custom_name, self.config.get("ai_provider") or "openai")
            return inferred_prov, normalize_model_name(custom_name, inferred_prov)
        return prov, normalize_model_name(mname, prov)

    # ---------------- Tree & City Logic ----------------

    def _on_timer_synced(self):
        self.refresh_account_card()
        self.refresh_tree_display()

    def refresh_tree_display(self):
        fam = ensure_fonts_loaded()
        state = self.sync_service.cached_state
        uid = state.get("userId") or self.config.get("nous_user_id") or "default_user"
        total_hours = float(state.get("totalHours", 0.0))
        bonus_hours = min(
            max(0.0, float(state.get("bonusGrowthHours", 0.0))),
            total_hours * 0.1
        )
        tap_hours = max(0.0, float(state.get("tapGrowthHours", 0.0)))
        growth_hours = total_hours + bonus_hours + tap_hours
        boxes_opened = int(state.get("treeBoxesOpened", 0))

        steps = tree.plan(uid, state.get("treePath"))
        prog = tree.progress(steps, growth_hours, boxes_opened)

        cur_name = prog.get("current_name", "Oak")
        cur_blurb = prog.get("current_blurb", "")
        cur_tier = prog.get("current_tier", {})
        tier_name = cur_tier.get("name", "rare")
        tier_color = cur_tier.get("color", "#2563eb")
        tier_bg = cur_tier.get("bg", "#eff6ff")
        tier_border = cur_tier.get("border", "#bfdbfe")
        pct = prog.get("pct", 0.0)
        into = prog.get("into", 0.0)
        hours_req = prog.get("current", {}).get("hours", 1) if prog.get("current") else 1
        hours_left = prog.get("hours_left", 0.0)
        grown = prog.get("grown", 0)
        total_trees = prog.get("total_trees", 35)

        self.tree_name_label.setText(cur_name.lower())
        if hasattr(self, "tree_blurb_label"):
            self.tree_blurb_label.setText(cur_blurb)
        self.tier_badge.setText(tier_name.lower())
        self.tier_badge.setStyleSheet(
            f"font-family: '{fam}'; background-color: {tier_bg}; color: {tier_color}; "
            f"border: 1px solid {tier_border}; border-radius: 10px; padding: 3px 9px; font-size: 10px; font-weight: 500;"
        )

        self.tree_progress.setValue(int(pct))
        self.tree_progress.setFormat(f"{into:.1f} / {hours_req:.1f}h ({pct:.0f}%)")
        self.tree_caption_label.setText(f"{into:.1f} / {hours_req:.1f}h ({hours_left:.1f}h to bloom)")
        self.overall_label.setText(f"{total_hours:.1f}h · {grown}/{total_trees} 🌲")

        cur_id = prog.get("current", {}).get("id", "oak") if prog.get("current") else "oak"
        is_focusing = getattr(self.timer_widget, "running", False)
        self.tree_view.set_tree(cur_id, pct=pct, is_growing=is_focusing or (pct > 0 and pct < 100))

    def open_city_link(self):
        city_url = self.config.get("nous_city_url", "https://nous.study/city")
        webbrowser.open(city_url)

    def open_city_in_embedded_browser(self):
        city_url = self.config.get("nous_city_url", "https://nous.study/city")
        self.tabs.setCurrentIndex(self.TAB_WEB)
        self.browser_view.navigate(city_url)

    def trigger_manual_sync(self):
        if not self.sync_service.is_authenticated():
            self.sync_status_label.setText("🔒 sign in on focus tab to sync")
            self.focus_signin_prompt()
            return

        self.sync_status_label.setText("↻ syncing to nous…")
        habit = self.config.get("nous_habit_name", "Anki")

        def on_done(ok: bool, count: int):
            def _ui():
                self.refresh_account_card()
                self.refresh_tree_display()
                if ok:
                    self.sync_status_label.setText("🟢 synced to nous")
                else:
                    self.sync_status_label.setText("⚠️ sync failed — check sign-in")
            if mw and hasattr(mw, "taskman"):
                mw.taskman.run_on_main(_ui)
            else:
                _ui()

        self.sync_service.process_and_sync(habit_name=habit, min_ms=1000, on_done=on_done)

    # ---------------- AI Q&A Logic ----------------

    def explain_current_card(self):
        self.tabs.setCurrentIndex(self.TAB_AI)
        if not self.current_card:
            self.ai_result_view.setHtml("<i>no active flashcard currently displayed. start reviewing a deck first.</i>")
            return
        try:
            import re
            q_text = self.current_card.question()
            clean_q = re.sub(r"\[sound:[^\]]+\]", "", q_text)
            clean_q = re.sub(r"<[^>]+>", " ", clean_q)
            clean_q = " ".join(clean_q.split())

            cloze_clues = []
            try:
                anki_note = self.current_card.note()
                for fld_name in [f["name"] for f in anki_note.note_type()["flds"]]:
                    val = anki_note[fld_name]
                    matches = re.findall(r"\{\{c\d+::([^:}]+)(?:::([^}]+))?\}\}", val)
                    for m in matches:
                        cloze_clues.append(m[0].strip())
            except Exception:
                pass

            if cloze_clues:
                clue_str = ", ".join(dict.fromkeys(cloze_clues))
                prompt = f"Explain the concept '{clue_str}' in this context and give high-yield pearls: {clean_q[:1000]}"
            else:
                prompt = f"Explain this concept and give high-yield pearls: {clean_q[:1000]}"

            self.ai_input.setText(prompt)
            self.run_ai_search()
        except Exception as e:
            self.ai_result_view.setHtml(f"<i>could not read card: {e}</i>")

    def run_ai_search(self):
        # If user pasted an API key into the inline key box and pressed Ask directly, save it first
        if hasattr(self, "inline_key_input") and self.inline_key_input.text().strip():
            self.save_inline_api_key()

        query = self.ai_input.text().strip()
        if not query:
            return

        # If user accidentally pasted their API key into the question input box
        if detect_key_provider(query) is not None and " " not in query:
            self.inline_key_input.setText(query)
            self.ai_input.setText("")
            self.save_inline_api_key()
            return

        prov, model_name = self.get_selected_model_and_provider()

        self.ai_result_view.setHtml(f"<i>thinking with {model_name}…</i>")
        self.ask_btn.setEnabled(False)

        def on_result(res: Dict[str, Any]):
            def update():
                self.ask_btn.setEnabled(True)
                is_dark = self.is_dark_mode()
                text_color = "#e2e8f0" if is_dark else "#1f2937"
                sub_color = "#a78bfa" if is_dark else "#7c3aed"
                if res.get("success"):
                    ans = format_markdown_for_qt(res.get("answer", ""), is_dark=is_dark)
                    p = res.get("provider", "AI")
                    m = res.get("model", model_name)
                    content = f"""<div style="font-family: 'Satoshi', sans-serif; font-size: 13px; line-height: 1.5; color: {text_color};">
                    <div style="font-size: 11px; color: {sub_color}; font-weight: 500; margin-bottom: 6px;">
                        ✦ {p} ({m})
                    </div>
                    {ans}
                    </div>"""
                    self.ai_result_view.setHtml(content)
                else:
                    err = res.get("error", "Unknown error")
                    self.ai_result_view.setHtml(f'<span style="color: #ef4444;">error: {html.escape(err)}</span>')

            if mw and hasattr(mw, "taskman"):
                mw.taskman.run_on_main(update)
            else:
                update()

        self.ai_client.search_query_async(query, on_result, override_model=model_name, override_provider=prov)

    def copy_search_to_notes(self):
        plain_text = self.ai_result_view.toPlainText()
        if plain_text.strip():
            cur = self.notes_edit.toPlainText()
            separator = "\n\n---\n" if cur.strip() else ""
            self.notes_edit.setText(f"{cur}{separator}{plain_text.strip()}")
            self.tabs.setCurrentIndex(self.TAB_NOTES)

    def add_search_to_card(self):
        text = self.ai_result_view.toPlainText()
        if not text.strip():
            return
        if not self.current_card:
            self.ai_result_view.setHtml("<span style='color: #d97706;'>no active card to add to</span>")
            return

        ok = NotesManager.append_note_to_card(self.current_card, text)
        if ok:
            self.ai_result_view.setHtml("<span style='color: #10b981; font-weight: 500;'>added explanation to card</span>")
        else:
            self.ai_result_view.setHtml("<span style='color: #ef4444;'>failed to update card note</span>")

    # ---------------- Notes ----------------

    def on_notes_changed(self):
        self.notes_mgr.save_scratchpad(self.notes_edit.toPlainText())

    def append_notes_to_active_card(self):
        text = self.notes_edit.toPlainText().strip()
        if not text or not self.current_card:
            return
        ok = NotesManager.append_note_to_card(self.current_card, text)
        if ok:
            self.timer_widget.timer_status.setText("appended note to card")
            self.timer_widget.timer_status.setStyleSheet("font-size: 10px; color: #10b981; font-weight: 500;")

    def clear_notes(self):
        self.notes_edit.clear()
        self.notes_mgr.save_scratchpad("")

    def on_card_will_show(self, card: Any):
        self.current_card = card
