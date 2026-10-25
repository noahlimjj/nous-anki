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
    class QWidget: pass
    class QDockWidget: pass
    class QVBoxLayout: pass
    class QHBoxLayout: pass
    class QLabel: pass
    class QLineEdit: pass
    class QTextEdit: pass
    class QTextBrowser: pass
    class QPushButton: pass
    class QProgressBar: pass
    class QTabWidget: pass
    class QFrame: pass
    class QComboBox: pass
    class Qt:
        Horizontal = None
        RightDockWidgetArea = None
    mw = None

from . import tree
from .ai_search import AISearchClient, POPULAR_MODELS
from .browser_view import NousEmbeddedBrowser
from .notes import NotesManager
from .sound import NousSoundPlayer
from .sync import NousSyncService
from .timer_widget import NousTimerWidget


STYLESHEET = """
QDockWidget {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background-color: #fafafa;
    color: #1f2937;
}

QFrame.treeCard {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 10px;
}

QLabel.treeName {
    font-size: 15px;
    font-weight: 700;
    color: #111827;
}

QLabel.tierBadge {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    color: #ffffff;
    border-radius: 10px;
    padding: 2px 8px;
}

QProgressBar {
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    text-align: center;
    font-size: 11px;
    font-weight: 600;
    height: 14px;
    background-color: #f3f4f6;
    color: #374151;
}

QProgressBar::chunk {
    border-radius: 5px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669);
}

QPushButton.cityButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #2563eb);
    color: #ffffff;
    font-weight: 600;
    font-size: 12px;
    border-radius: 8px;
    padding: 6px 12px;
    border: none;
}
QPushButton.cityButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #1d4ed8);
}

QPushButton.actionButton {
    background-color: #f3f4f6;
    color: #374151;
    font-weight: 500;
    font-size: 11px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 4px 10px;
}
QPushButton.actionButton:hover {
    background-color: #e5e7eb;
}

QPushButton.primaryButton {
    background-color: #8b5cf6;
    color: #ffffff;
    font-weight: 600;
    font-size: 11px;
    border-radius: 6px;
    padding: 4px 12px;
    border: none;
}
QPushButton.primaryButton:hover {
    background-color: #7c3aed;
}

QLineEdit, QTextEdit, QTextBrowser, QComboBox {
    background-color: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 5px;
    color: #1f2937;
    font-size: 12px;
}

QTabWidget::pane {
    border: 1px solid #e5e7eb;
    background-color: #ffffff;
    border-radius: 8px;
    padding: 4px;
}
"""


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

        self.setup_ui()
        self.setStyleSheet(STYLESHEET)
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
        self.tree_name_label = QLabel("Oak")
        self.tree_name_label.setProperty("class", "treeName")
        self.tier_badge = QLabel("RARE")
        self.tier_badge.setProperty("class", "tierBadge")
        self.tier_badge.setStyleSheet("background-color: #3b82f6;")

        name_tier_row.addWidget(self.tree_name_label)
        name_tier_row.addStretch()
        name_tier_row.addWidget(self.tier_badge)
        tree_layout.addLayout(name_tier_row)

        self.tree_svg_view = QTextBrowser()
        self.tree_svg_view.setFixedHeight(105)
        self.tree_svg_view.setStyleSheet("border: none; background: transparent;")
        self.tree_svg_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tree_svg_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        tree_layout.addWidget(self.tree_svg_view)

        self.tree_progress = QProgressBar()
        self.tree_progress.setRange(0, 100)
        self.tree_progress.setValue(0)
        tree_layout.addWidget(self.tree_progress)

        self.tree_caption_label = QLabel("0.0 / 1.0h")
        self.tree_caption_label.setStyleSheet("font-size: 11px; color: #6b7280; font-weight: 500;")
        tree_layout.addWidget(self.tree_caption_label)

        self.overall_label = QLabel("0.0 hrs on Nous • 0/26 trees grown")
        self.overall_label.setStyleSheet("font-size: 11px; color: #4b5563; font-weight: 600;")
        tree_layout.addWidget(self.overall_label)

        city_row = QHBoxLayout()
        self.city_btn = QPushButton("🏙️ Visit My City")
        self.city_btn.setProperty("class", "cityButton")
        self.city_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.city_btn.clicked.connect(self.open_city_link)

        self.city_embed_btn = QPushButton("View in App")
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
        model_label = QLabel("Model:")
        model_label.setStyleSheet("font-size: 11px; font-weight: 600;")
        self.model_combo = QComboBox()
        for label, prov, mname in POPULAR_MODELS:
            self.model_combo.addItem(label, userData=(prov, mname))

        self.custom_model_input = QLineEdit()
        self.custom_model_input.setPlaceholderText("Any custom model (e.g. gpt-4o, claude-3-5-sonnet)...")
        self.custom_model_input.hide()
        self.model_combo.currentIndexChanged.connect(self._on_model_combo_changed)

        model_row.addWidget(model_label)
        model_row.addWidget(self.model_combo)
        ai_layout.addLayout(model_row)
        ai_layout.addWidget(self.custom_model_input)

        # Question input & Ask button
        q_row = QHBoxLayout()
        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("Ask any question or explain card...")
        self.ai_input.returnPressed.connect(self.run_ai_search)

        self.ask_btn = QPushButton("Ask")
        self.ask_btn.setProperty("class", "primaryButton")
        self.ask_btn.clicked.connect(self.run_ai_search)

        self.explain_card_btn = QPushButton("Explain Card")
        self.explain_card_btn.setProperty("class", "actionButton")
        self.explain_card_btn.clicked.connect(self.explain_current_card)

        q_row.addWidget(self.ai_input)
        q_row.addWidget(self.ask_btn)
        q_row.addWidget(self.explain_card_btn)
        ai_layout.addLayout(q_row)

        # AI Result View
        self.ai_result_view = QTextBrowser()
        self.ai_result_view.setPlaceholderText("AI explanations and answers appear here...")
        ai_layout.addWidget(self.ai_result_view)

        # Actions on AI response
        ai_act_row = QHBoxLayout()
        self.copy_to_notes_btn = QPushButton("Copy to Notes")
        self.copy_to_notes_btn.setProperty("class", "actionButton")
        self.copy_to_notes_btn.clicked.connect(self.copy_search_to_notes)

        self.add_to_card_btn = QPushButton("Add to Card")
        self.add_to_card_btn.setProperty("class", "actionButton")
        self.add_to_card_btn.clicked.connect(self.add_search_to_card)

        ai_act_row.addWidget(self.copy_to_notes_btn)
        ai_act_row.addWidget(self.add_to_card_btn)
        ai_layout.addLayout(ai_act_row)

        self.tabs.addTab(ai_tab, "🤖 AI Q&A")

        # --- TAB 2: EMBEDDED BROWSER ---
        self.browser_view = NousEmbeddedBrowser(self, home_url=self.config.get("nous_city_url", "https://nous.study/city"))
        self.tabs.addTab(self.browser_view, "🌐 Browser")

        # --- TAB 3: NOTES ---
        notes_tab = QWidget()
        notes_layout = QVBoxLayout(notes_tab)
        notes_layout.setContentsMargins(6, 6, 6, 6)
        notes_layout.setSpacing(6)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Study notes, mnemonics, scratchpad...")
        self.notes_edit.setText(self.notes_mgr.load_scratchpad())
        self.notes_edit.textChanged.connect(self.on_notes_changed)
        notes_layout.addWidget(self.notes_edit)

        notes_btn_row = QHBoxLayout()
        self.append_card_btn = QPushButton("Append to Current Card")
        self.append_card_btn.setProperty("class", "primaryButton")
        self.append_card_btn.clicked.connect(self.append_notes_to_active_card)

        self.clear_notes_btn = QPushButton("Clear")
        self.clear_notes_btn.setProperty("class", "actionButton")
        self.clear_notes_btn.clicked.connect(self.clear_notes)

        notes_btn_row.addWidget(self.append_card_btn)
        notes_btn_row.addWidget(self.clear_notes_btn)
        notes_layout.addLayout(notes_btn_row)

        self.tabs.addTab(notes_tab, "📝 Notes")

        layout.addWidget(self.tabs)
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

        cur_name = prog.get("current_name", "Oak")
        cur_tier = prog.get("current_tier", {})
        tier_name = cur_tier.get("name", "RARE")
        tier_color = cur_tier.get("color", "#3b82f6")
        pct = prog.get("pct", 0.0)
        into = prog.get("into", 0.0)
        hours_req = prog.get("current", {}).get("hours", 1) if prog.get("current") else 1
        hours_left = prog.get("hours_left", 0.0)
        grown = prog.get("grown", 0)
        total_trees = prog.get("total_trees", 26)

        self.tree_name_label.setText(cur_name)
        self.tier_badge.setText(tier_name.upper())
        self.tier_badge.setStyleSheet(f"background-color: {tier_color}; color: #ffffff;")

        self.tree_progress.setValue(int(pct))
        self.tree_progress.setFormat(f"{into:.1f} / {hours_req:.1f}h ({pct:.0f}%)")
        self.tree_caption_label.setText(f"{hours_left:.1f}h remaining to bloom")
        self.overall_label.setText(f"{total_hours:.1f} hrs on Nous • {grown}/{total_trees} trees grown 🌲")

        cur_id = prog.get("current", {}).get("id", "oak") if prog.get("current") else "oak"
        svg_code = tree.generate_tree_svg(cur_id, pct=pct, size=95)
        html_content = f"""<html><body style="margin:0; padding:0; display:flex; justify-content:center; align-items:center; background:transparent;">
        <center>{svg_code}</center>
        </body></html>"""
        self.tree_svg_view.setHtml(html_content)

    def open_city_link(self):
        city_url = self.config.get("nous_city_url", "https://nous.study/city")
        webbrowser.open(city_url)

    def open_city_in_embedded_browser(self):
        city_url = self.config.get("nous_city_url", "https://nous.study/city")
        self.browser_view.navigate(city_url)
        self.tabs.setCurrentIndex(1)  # switch to Browser tab

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

        self.ai_result_view.setHtml(f"<i>Thinking with {model_name}...</i>")
        self.ask_btn.setEnabled(False)

        def on_result(res: Dict[str, Any]):
            def update():
                self.ask_btn.setEnabled(True)
                if res.get("success"):
                    ans = html.escape(res.get("answer", "")).replace("\n", "<br>")
                    p = res.get("provider", "AI")
                    m = res.get("model", model_name)
                    content = f"""<div style="font-family: sans-serif; font-size: 13px; line-height: 1.5; color: #1f2937;">
                    <div style="font-size: 11px; color: #7c3aed; font-weight: 700; margin-bottom: 6px;">
                        ✦ {p} ({m})
                    </div>
                    {ans}
                    </div>"""
                    self.ai_result_view.setHtml(content)
                else:
                    err = res.get("error", "Unknown error")
                    self.ai_result_view.setHtml(f'<span style="color: #ef4444;">Error: {html.escape(err)}</span>')

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
            self.ai_result_view.setHtml("<span style='color: #d97706;'>⚠️ No active card to add to</span>")
            return

        ok = NotesManager.append_note_to_card(self.current_card, text)
        if ok:
            self.ai_result_view.setHtml("<span style='color: #10b981; font-weight: bold;'>✅ Added explanation to card!</span>")
        else:
            self.ai_result_view.setHtml("<span style='color: #ef4444;'>⚠️ Failed to update card note</span>")

    # ---------------- Notes ----------------

    def on_notes_changed(self):
        self.notes_mgr.save_scratchpad(self.notes_edit.toPlainText())

    def append_notes_to_active_card(self):
        text = self.notes_edit.toPlainText().strip()
        if not text or not self.current_card:
            return
        ok = NotesManager.append_note_to_card(self.current_card, text)
        if ok:
            self.timer_widget.timer_status.setText("✅ Appended note to card!")
            self.timer_widget.timer_status.setStyleSheet("font-size: 11px; color: #10b981;")

    def clear_notes(self):
        self.notes_edit.clear()
        self.notes_mgr.save_scratchpad("")

    def on_card_will_show(self, card: Any):
        self.current_card = card
