"""
Nous Sidebar Dock Widget for Anki
Displays:
1. Live Tree Growth & Progress (Ported from Nous tree-path.js)
2. Link to Nous City (https://nous.study/city)
3. AI & Web Search with Custom API Key
4. Study Notes with 1-Click Card Appending
"""

import html
import webbrowser
from typing import Any, Dict, Optional

try:
    from aqt.qt import (
        QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QLineEdit, QTextEdit, QTextBrowser, QPushButton, QProgressBar,
        QTabWidget, QFrame, Qt, QCursor, QFont, QSizePolicy
    )
    from aqt import mw
except ImportError:
    # Dummy mock classes for headless testing outside Anki
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
    class Qt:
        Horizontal = None
        RightDockWidgetArea = None
    mw = None

from . import tree
from .ai_search import AISearchClient
from .notes import NotesManager
from .sync import NousSyncService


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
    padding: 12px;
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

QLineEdit, QTextEdit, QTextBrowser {
    background-color: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 6px;
    color: #1f2937;
    font-size: 12px;
}

QTabWidget::pane {
    border: 1px solid #e5e7eb;
    background-color: #ffffff;
    border-radius: 8px;
    padding: 6px;
}
"""


class NousDockWidget(QDockWidget):
    TITLE = "Nous"

    def __init__(self, parent, sync_service: NousSyncService, notes_mgr: NotesManager, config: Dict[str, Any]):
        super().__init__(self.TITLE, parent)
        self.sync_service = sync_service
        self.notes_mgr = notes_mgr
        self.config = config
        self.current_card = None
        self.ai_client = AISearchClient(
            provider=config.get("ai_provider", "openai"),
            api_key=config.get("ai_api_key", ""),
            model=config.get("ai_model", ""),
            base_url=config.get("ai_base_url", "")
        )

        self.setup_ui()
        self.setStyleSheet(STYLESHEET)
        self.refresh_tree_display()

    def setup_ui(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 1. TREE & GAMIFICATION CARD
        self.tree_card = QFrame()
        self.tree_card.setProperty("class", "treeCard")
        tree_layout = QVBoxLayout(self.tree_card)
        tree_layout.setContentsMargins(10, 10, 10, 10)
        tree_layout.setSpacing(6)

        # Top row: Tree name + Tier badge
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

        # Tree SVG view
        self.tree_svg_view = QTextBrowser()
        self.tree_svg_view.setFixedHeight(115)
        self.tree_svg_view.setStyleSheet("border: none; background: transparent;")
        self.tree_svg_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tree_svg_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        tree_layout.addWidget(self.tree_svg_view)

        # Tree Progress Bar
        self.tree_progress = QProgressBar()
        self.tree_progress.setRange(0, 100)
        self.tree_progress.setValue(0)
        tree_layout.addWidget(self.tree_progress)

        # Tree status caption & blurb
        self.tree_caption_label = QLabel("0.0 / 1.0h (1.0h to bloom)")
        self.tree_caption_label.setStyleSheet("font-size: 11px; color: #6b7280; font-weight: 500;")
        tree_layout.addWidget(self.tree_caption_label)

        # Overall summary row (Trees grown & total study hours)
        self.overall_label = QLabel("0.0 hrs on Nous • 0/26 trees grown")
        self.overall_label.setStyleSheet("font-size: 11px; color: #4b5563; font-weight: 600;")
        tree_layout.addWidget(self.overall_label)

        # "Visit My City" button
        self.city_btn = QPushButton("🏙️ Visit My City")
        self.city_btn.setProperty("class", "cityButton")
        self.city_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.city_btn.clicked.connect(self.open_city_link)
        tree_layout.addWidget(self.city_btn)

        layout.addWidget(self.tree_card)

        # 2. STUDY SYNC STATUS ROW
        sync_row = QHBoxLayout()
        self.sync_status_label = QLabel("🟢 Studying active")
        self.sync_status_label.setStyleSheet("font-size: 11px; color: #10b981; font-weight: 500;")
        self.sync_btn = QPushButton("Sync Now")
        self.sync_btn.setProperty("class", "actionButton")
        self.sync_btn.clicked.connect(self.trigger_manual_sync)

        sync_row.addWidget(self.sync_status_label)
        sync_row.addStretch()
        sync_row.addWidget(self.sync_btn)
        layout.addLayout(sync_row)

        # 3. TABS: SEARCH & NOTES
        self.tabs = QTabWidget()

        # --- SEARCH TAB ---
        search_tab = QWidget()
        search_layout = QVBoxLayout(search_tab)
        search_layout.setContentsMargins(6, 6, 6, 6)
        search_layout.setSpacing(6)

        search_input_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search flashcard concept or term...")
        self.search_input.returnPressed.connect(self.run_ai_search)

        self.ask_ai_btn = QPushButton("Ask AI")
        self.ask_ai_btn.setProperty("class", "primaryButton")
        self.ask_ai_btn.clicked.connect(self.run_ai_search)

        search_input_row.addWidget(self.search_input)
        search_input_row.addWidget(self.ask_ai_btn)
        search_layout.addLayout(search_input_row)

        # Quick web search buttons row
        web_row = QHBoxLayout()
        web_row.setSpacing(4)
        for label, prov in [("Google", "google"), ("Amboss", "amboss"), ("PubMed", "pubmed"), ("Wiki", "wikipedia")]:
            btn = QPushButton(label)
            btn.setProperty("class", "actionButton")
            btn.clicked.connect(lambda _, p=prov: self.open_web_search(p))
            web_row.addWidget(btn)
        search_layout.addLayout(web_row)

        # Result display
        self.search_result_view = QTextBrowser()
        self.search_result_view.setPlaceholderText("AI explanations and search results will appear here...")
        search_layout.addWidget(self.search_result_view)

        # Result actions
        result_action_row = QHBoxLayout()
        self.copy_to_notes_btn = QPushButton("Copy to Notes")
        self.copy_to_notes_btn.setProperty("class", "actionButton")
        self.copy_to_notes_btn.clicked.connect(self.copy_search_to_notes)

        self.add_to_card_btn = QPushButton("Add to Card")
        self.add_to_card_btn.setProperty("class", "actionButton")
        self.add_to_card_btn.clicked.connect(self.add_search_to_card)

        result_action_row.addWidget(self.copy_to_notes_btn)
        result_action_row.addWidget(self.add_to_card_btn)
        search_layout.addLayout(result_action_row)

        self.tabs.addTab(search_tab, "🔍 Search")

        # --- NOTES TAB ---
        notes_tab = QWidget()
        notes_layout = QVBoxLayout(notes_tab)
        notes_layout.setContentsMargins(6, 6, 6, 6)
        notes_layout.setSpacing(6)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Jot down quick study notes, mnemonics, or questions...")
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

    # ---------------- Tree & City Logic ----------------

    def refresh_tree_display(self):
        """Recalculates and updates the tree widget based on user's current hours."""
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

        # Render SVG
        cur_id = prog.get("current", {}).get("id", "oak") if prog.get("current") else "oak"
        svg_code = tree.generate_tree_svg(cur_id, pct=pct, size=105)
        html_content = f"""<html><body style="margin:0; padding:0; display:flex; justify-content:center; align-items:center; background:transparent;">
        <center>{svg_code}</center>
        </body></html>"""
        self.tree_svg_view.setHtml(html_content)

    def open_city_link(self):
        city_url = self.config.get("nous_city_url", "https://nous.study/city")
        webbrowser.open(city_url)

    # ---------------- Study Sync Handlers ----------------

    def trigger_manual_sync(self):
        self.sync_status_label.setText("⏳ Syncing to Nous...")
        habit_name = self.config.get("nous_habit_name", "Anki")

        def on_done(ok: bool, count: int):
            def update():
                self.sync_status_label.setText(f"🟢 Synced {count} session(s)")
                self.refresh_tree_display()
            if mw and hasattr(mw, "taskman"):
                mw.taskman.run_on_main(update)
            else:
                update()

        self.sync_service.process_and_sync(habit_name=habit_name, min_ms=1000, on_done=on_done)

    # ---------------- AI & Web Search ----------------

    def set_search_query(self, query: str):
        if query and query.strip():
            self.search_input.setText(query.strip())
            self.tabs.setCurrentIndex(0)

    def run_ai_search(self):
        query = self.search_input.text().strip()
        if not query:
            return

        self.search_result_view.setHtml("<i>Searching AI study assistant...</i>")
        self.ask_ai_btn.setEnabled(False)

        def on_result(res: Dict[str, Any]):
            def update():
                self.ask_ai_btn.setEnabled(True)
                if res.get("success"):
                    ans = html.escape(res.get("answer", "")).replace("\n", "<br>")
                    prov = res.get("provider", "AI")
                    model = res.get("model", "")
                    content = f"""<div style="font-family: sans-serif; font-size: 13px; line-height: 1.5; color: #1f2937;">
                    <div style="font-size: 11px; color: #7c3aed; font-weight: 700; margin-bottom: 6px;">
                        ✦ {prov} ({model})
                    </div>
                    {ans}
                    </div>"""
                    self.search_result_view.setHtml(content)
                else:
                    err = res.get("error", "Unknown error")
                    self.search_result_view.setHtml(f'<span style="color: #ef4444;">Error: {html.escape(err)}</span>')

            if mw and hasattr(mw, "taskman"):
                mw.taskman.run_on_main(update)
            else:
                update()

        self.ai_client.search_query_async(query, on_result)

    def open_web_search(self, provider: str):
        query = self.search_input.text().strip()
        if not query and self.current_card:
            # Fall back to card question text if search input is blank
            try:
                query = self.current_card.question()
            except Exception:
                pass
        if query:
            url = AISearchClient.get_web_search_url(provider, query)
            webbrowser.open(url)

    def copy_search_to_notes(self):
        plain_text = self.search_result_view.toPlainText()
        if plain_text.strip():
            cur = self.notes_edit.toPlainText()
            separator = "\n\n---\n" if cur.strip() else ""
            self.notes_edit.setText(f"{cur}{separator}{plain_text.strip()}")
            self.tabs.setCurrentIndex(1)

    def add_search_to_card(self):
        text = self.search_result_view.toPlainText()
        if not text.strip():
            return
        if not self.current_card:
            self.sync_status_label.setText("⚠️ No active card to add to")
            return

        ok = NotesManager.append_note_to_card(self.current_card, text)
        if ok:
            self.sync_status_label.setText("✅ Added explanation to card!")
        else:
            self.sync_status_label.setText("⚠️ Failed to update card")

    # ---------------- Notes ----------------

    def on_notes_changed(self):
        self.notes_mgr.save_scratchpad(self.notes_edit.toPlainText())

    def append_notes_to_active_card(self):
        text = self.notes_edit.toPlainText().strip()
        if not text:
            return
        if not self.current_card:
            self.sync_status_label.setText("⚠️ No active card open")
            return

        ok = NotesManager.append_note_to_card(self.current_card, text)
        if ok:
            self.sync_status_label.setText("✅ Appended notes to card!")
        else:
            self.sync_status_label.setText("⚠️ Could not append note")

    def clear_notes(self):
        self.notes_edit.clear()
        self.notes_mgr.save_scratchpad("")

    def on_card_will_show(self, card: Any):
        self.current_card = card
