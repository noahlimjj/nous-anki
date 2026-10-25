"""
Nous Sidebar Dock Widget for Anki
Features:
1. Live Tree Growth & Progress (Nous tree-path.js)
2. Nous Focus Timer with authentic sound effects & auto-sync to habit dashboard
3. 1-Click Link & Embedded View for Nous City (https://nous.study/city)
4. AI Assistant: Ask questions using ANY model (GPT-4o, Claude 3.5, Gemini, Sonar, DeepSeek, Ollama)
5. Embedded Web Browser: Browse medical resources or Nous City inside Anki
6. Study Notes with 1-Click Card Injection
"""

import html
import webbrowser
from typing import Any, Dict, Optional

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
        class QDockWidget:
            def __init__(self, *args, **kwargs): pass
            def setWidget(self, w): pass
            def setStyleSheet(self, s): pass
        class QVBoxLayout:
            def __init__(self, *args, **kwargs): pass
            def addWidget(self, w): pass
            def addLayout(self, l): pass
            def setContentsMargins(self, *args): pass
            def setSpacing(self, s): pass
        class QHBoxLayout:
            def __init__(self, *args, **kwargs): pass
            def addWidget(self, w): pass
            def addStretch(self): pass
            def addLayout(self, l): pass
            def setContentsMargins(self, *args): pass
            def setSpacing(self, s): pass
        class QLabel:
            def __init__(self, *args, **kwargs): pass
            def setText(self, t): pass
            def setProperty(self, *args): pass
            def setStyleSheet(self, s): pass
            def setAlignment(self, a): pass
        class QLineEdit:
            def __init__(self, *args, **kwargs): pass
            def text(self): return ""
            def setText(self, t): pass
            def setPlaceholderText(self, t): pass
            def hide(self): pass
            def show(self): pass
            returnPressed = None
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
            clicked = None
        class QProgressBar:
            def __init__(self, *args, **kwargs): pass
            def setRange(self, *args): pass
            def setValue(self, v): pass
            def setFormat(self, f): pass
            def maximum(self): return 100
        class QTabWidget:
            def __init__(self, *args, **kwargs): pass
            def addTab(self, *args): pass
            def setCurrentIndex(self, i): pass
            def count(self): return 3
            def tabText(self, i): return ""
        class QFrame:
            def __init__(self, *args, **kwargs): pass
            def setProperty(self, *args): pass
        class QComboBox:
            def __init__(self, *args, **kwargs): pass
            def addItem(self, *args, **kwargs): pass
            def currentData(self): return None
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
from .ai_search import AISearchClient, POPULAR_MODELS
from .browser_view import NousEmbeddedBrowser
from .notes import NotesManager
from .sound import NousSoundPlayer
from .sync import NousSyncService
from .timer_widget import NousTimerWidget
from .tree_widget import NousTreeWidget
from .theme import NOUS_STYLESHEET, ensure_fonts_loaded


class NousDockWidget(QDockWidget):
    TITLE = "Nous"

    def __init__(self, parent, sync_service: NousSyncService, notes_mgr: NotesManager, sound_player: NousSoundPlayer, config: Dict[str, Any]):
        super().__init__(self.TITLE, parent)
        self.sync_service = sync_service
        self.notes_mgr = notes_mgr
        self.sound = sound_player
        self.config = config
        self.current_card = None

        self.ai_client = AISearchClient(
            provider=config.get("ai_provider", "openai"),
            api_key=config.get("ai_api_key", ""),
            model=config.get("ai_model", "gpt-4o-mini"),
            base_url=config.get("ai_base_url", "")
        )

        ensure_fonts_loaded()
        self.setup_ui()
        self.setStyleSheet(NOUS_STYLESHEET)
        self.refresh_tree_display()

    def setup_ui(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 1. TREE & GAMIFICATION CARD
        self.tree_card = QFrame()
        self.tree_card.setProperty("class", "treeCard")
        tree_layout = QVBoxLayout(self.tree_card)
        tree_layout.setContentsMargins(8, 8, 8, 8)
        tree_layout.setSpacing(4)

        name_tier_row = QHBoxLayout()
        self.tree_name_label = QLabel("oak")
        self.tree_name_label.setProperty("class", "treeName")
        self.tier_badge = QLabel("rare")
        self.tier_badge.setProperty("class", "tierBadge")
        self.tier_badge.setStyleSheet("background-color: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; border-radius: 999px; padding: 2px 8px; font-size: 10px; font-weight: 400;")

        name_tier_row.addWidget(self.tree_name_label)
        name_tier_row.addStretch()
        name_tier_row.addWidget(self.tier_badge)
        tree_layout.addLayout(name_tier_row)

        self.tree_view = NousTreeWidget(self)
        self.tree_svg_view = self.tree_view
        tree_layout.addWidget(self.tree_view)

        self.tree_progress = QProgressBar()
        self.tree_progress.setRange(0, 100)
        self.tree_progress.setValue(0)
        tree_layout.addWidget(self.tree_progress)

        self.tree_caption_label = QLabel("0.0 / 1.0h")
        self.tree_caption_label.setStyleSheet("font-size: 11px; color: #7d8ca8; font-weight: 300;")
        tree_layout.addWidget(self.tree_caption_label)

        self.overall_label = QLabel("0.0 hrs on nous · 0/26 trees grown")
        self.overall_label.setStyleSheet("font-size: 11px; color: #7d8ca8; font-weight: 300;")
        tree_layout.addWidget(self.overall_label)

        city_row = QHBoxLayout()
        self.city_btn = QPushButton("visit my city 🏙️")
        self.city_btn.setProperty("class", "cityButton")
        self.city_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.city_btn.clicked.connect(self.open_city_link)

        self.city_embed_btn = QPushButton("view in app")
        self.city_embed_btn.setProperty("class", "actionButton")
        self.city_embed_btn.clicked.connect(self.open_city_in_embedded_browser)

        city_row.addWidget(self.city_btn)
        city_row.addWidget(self.city_embed_btn)
        tree_layout.addLayout(city_row)

        layout.addWidget(self.tree_card)

        # 2. NOUS FOCUS TIMER
        self.timer_widget = NousTimerWidget(
            self,
            sync_service=self.sync_service,
            sound_player=self.sound,
            on_synced=self.refresh_tree_display
        )
        layout.addWidget(self.timer_widget)

        # 3. TABS: AI Q&A, BROWSER, NOTES
        self.tabs = QTabWidget()

        # --- TAB 1: AI ASSISTANT ---
        ai_tab = QWidget()
        ai_layout = QVBoxLayout(ai_tab)
        ai_layout.setContentsMargins(6, 6, 6, 6)
        ai_layout.setSpacing(6)

        # Model Selector Row
        model_row = QHBoxLayout()
        model_label = QLabel("model:")
        model_label.setStyleSheet("font-size: 11px; font-weight: 400; color: #5f5390;")
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

        self.custom_model_input = QLineEdit()
        self.custom_model_input.setPlaceholderText("any custom model (e.g. gpt-4o, claude-3-5-sonnet)...")
        self.custom_model_input.hide()
        self.model_combo.currentIndexChanged.connect(self._on_model_combo_changed)

        model_row.addWidget(model_label)
        model_row.addWidget(self.model_combo)
        ai_layout.addLayout(model_row)
        ai_layout.addWidget(self.custom_model_input)

        # Question input & Ask button
        q_row = QHBoxLayout()
        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("ask any question or explain card...")
        self.ai_input.returnPressed.connect(self.run_ai_search)

        self.ask_btn = QPushButton("ask")
        self.ask_btn.setProperty("class", "primaryButton")
        self.ask_btn.clicked.connect(self.run_ai_search)

        self.explain_card_btn = QPushButton("explain card")
        self.explain_card_btn.setProperty("class", "actionButton")
        self.explain_card_btn.clicked.connect(self.explain_current_card)

        q_row.addWidget(self.ai_input)
        q_row.addWidget(self.ask_btn)
        q_row.addWidget(self.explain_card_btn)
        ai_layout.addLayout(q_row)

        # AI Result View
        self.ai_result_view = QTextBrowser()
        self.ai_result_view.setPlaceholderText("ai explanations and answers appear here...")
        ai_layout.addWidget(self.ai_result_view)

        # Actions on AI response
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

        self.tabs.addTab(ai_tab, "ai")

        # --- TAB 2: EMBEDDED BROWSER ---
        self.browser_view = NousEmbeddedBrowser(self, home_url=self.config.get("nous_city_url", "https://nous.study/city"))
        self.tabs.addTab(self.browser_view, "browser")

        # --- TAB 3: NOTES ---
        notes_tab = QWidget()
        notes_layout = QVBoxLayout(notes_tab)
        notes_layout.setContentsMargins(6, 6, 6, 6)
        notes_layout.setSpacing(6)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("study notes, mnemonics, scratchpad...")
        self.notes_edit.setText(self.notes_mgr.load_scratchpad())
        self.notes_edit.textChanged.connect(self.on_notes_changed)
        notes_layout.addWidget(self.notes_edit)

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

        self.tabs.addTab(notes_tab, "notes")

        layout.addWidget(self.tabs)

        # Footer Sync Status Row
        footer_row = QHBoxLayout()
        self.sync_status_label = QLabel("✨ auto-syncing to nous")
        self.sync_status_label.setStyleSheet("font-size: 10px; color: #7d8ca8; font-weight: 300;")
        footer_row.addWidget(self.sync_status_label)
        footer_row.addStretch()

        self.manual_sync_btn = QPushButton("sync")
        self.manual_sync_btn.setProperty("class", "actionButton")
        self.manual_sync_btn.clicked.connect(self.trigger_manual_sync)
        footer_row.addWidget(self.manual_sync_btn)

        layout.addLayout(footer_row)
        self.setWidget(container)

    # ---------------- Model Selector Handler ----------------

    def _on_model_combo_changed(self, idx: int):
        data = self.model_combo.currentData()
        if data and data[0] == "custom":
            self.custom_model_input.show()
        else:
            self.custom_model_input.hide()

    def get_selected_model_and_provider(self):
        data = self.model_combo.currentData()
        if not data:
            return "openai", "gpt-4o-mini"
        prov, mname = data
        if prov == "custom":
            custom_name = self.custom_model_input.text().strip()
            return "openai", custom_name or "gpt-4o-mini"
        return prov, mname

    # ---------------- Tree & City Logic ----------------

    def refresh_tree_display(self):
        state = self.sync_service.cached_state
        uid = state.get("userId") or self.config.get("nous_user_id") or "default_user"
        total_hours = float(state.get("totalHours", 0.0))
        boxes_opened = int(state.get("treeBoxesOpened", 0))

        steps = tree.plan(uid, state.get("treePath"))
        prog = tree.progress(steps, total_hours, boxes_opened)

        cur_name = prog.get("current_name", "oak")
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
        total_trees = prog.get("total_trees", 26)

        self.tree_name_label.setText(cur_name.lower())
        self.tier_badge.setText(tier_name.lower())
        self.tier_badge.setStyleSheet(f"background-color: {tier_bg}; color: {tier_color}; border: 1px solid {tier_border}; border-radius: 999px; padding: 2px 8px; font-size: 10px; font-weight: 400;")

        self.tree_progress.setValue(int(pct))
        self.tree_progress.setFormat(f"{into:.1f} / {hours_req:.1f}h ({pct:.0f}%)")
        self.tree_caption_label.setText(f"{hours_left:.1f}h remaining to bloom")
        self.overall_label.setText(f"{total_hours:.1f} hrs on nous · {grown}/{total_trees} trees grown")

        cur_id = prog.get("current", {}).get("id", "oak") if prog.get("current") else "oak"
        is_focusing = getattr(self.timer_widget, "running", False)
        self.tree_view.set_tree(cur_id, pct=pct, is_growing=is_focusing or (pct > 0 and pct < 100))

    def open_city_link(self):
        city_url = self.config.get("nous_city_url", "https://nous.study/city")
        webbrowser.open(city_url)

    def open_city_in_embedded_browser(self):
        city_url = self.config.get("nous_city_url", "https://nous.study/city")
        self.tabs.setCurrentIndex(1)  # switch to Browser tab
        self.browser_view.navigate(city_url)

    def trigger_manual_sync(self):
        self.sync_status_label.setText("syncing to nous…")
        habit = self.config.get("nous_habit_name", "Anki")
        def on_done(ok: bool, count: int):
            self.refresh_tree_display()
            if ok:
                self.sync_status_label.setText("synced to nous")
            else:
                self.sync_status_label.setText("sync failed")
        self.sync_service.process_and_sync(habit_name=habit, min_ms=1000, on_done=on_done)

    # ---------------- AI Q&A Logic ----------------

    def explain_current_card(self):
        if not self.current_card:
            self.ai_result_view.setHtml("<i>No active flashcard currently displayed.</i>")
            return
        try:
            q_text = self.current_card.question()
            import re
            clean_q = re.sub(r"<[^>]+>", " ", q_text).strip()
            self.ai_input.setText(f"Explain this concept and give high-yield pearls: {clean_q[:250]}")
            self.run_ai_search()
        except Exception as e:
            self.ai_result_view.setHtml(f"<i>Could not read card: {e}</i>")

    def run_ai_search(self):
        query = self.ai_input.text().strip()
        if not query:
            return

        prov, model_name = self.get_selected_model_and_provider()

        self.ai_result_view.setHtml(f"<i>thinking with {model_name}…</i>")
        self.ask_btn.setEnabled(False)

        def on_result(res: Dict[str, Any]):
            def update():
                self.ask_btn.setEnabled(True)
                if res.get("success"):
                    ans = html.escape(res.get("answer", "")).replace("\n", "<br>")
                    p = res.get("provider", "AI")
                    m = res.get("model", model_name)
                    content = f"""<div style="font-family: sans-serif; font-size: 13px; line-height: 1.5; color: #1f2937;">
                    <div style="font-size: 11px; color: #7c3aed; font-weight: 400; margin-bottom: 6px;">
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
            self.tabs.setCurrentIndex(2)

    def add_search_to_card(self):
        text = self.ai_result_view.toPlainText()
        if not text.strip():
            return
        if not self.current_card:
            self.ai_result_view.setHtml("<span style='color: #d97706;'>no active card to add to</span>")
            return

        ok = NotesManager.append_note_to_card(self.current_card, text)
        if ok:
            self.ai_result_view.setHtml("<span style='color: #10b981; font-weight: 400;'>added explanation to card</span>")
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
            self.timer_widget.timer_status.setStyleSheet("font-size: 11px; color: #10b981; font-weight: 400;")

    def clear_notes(self):
        self.notes_edit.clear()
        self.notes_mgr.save_scratchpad("")

    def on_card_will_show(self, card: Any):
        self.current_card = card
