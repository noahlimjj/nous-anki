"""
Settings Dialog for Nous Anki
Allows users to configure Nous credentials, AI Search API keys, and sync options.
"""

from typing import Any, Callable, Dict, Optional

try:
    from aqt.qt import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QComboBox, QSpinBox, QGroupBox, QFormLayout,
        QMessageBox, Qt
    )
    from aqt import mw
except ImportError:
    class QDialog: pass
    class QVBoxLayout: pass
    class QHBoxLayout: pass
    class QLabel: pass
    class QLineEdit: pass
    class QPushButton: pass
    class QComboBox: pass
    class QSpinBox: pass
    class QGroupBox: pass
    class QFormLayout: pass
    class QMessageBox: pass
    class Qt:
        Password = None
        Normal = None
    mw = None

from .sync import NousSyncService
from .theme import NOUS_STYLESHEET, ensure_fonts_loaded


class SettingsDialog(QDialog):
    def __init__(self, parent, config: Dict[str, Any], sync_service: NousSyncService, on_saved: Optional[Callable[[Dict[str, Any]], None]] = None):
        super().__init__(parent)
        self.config = config
        self.sync_service = sync_service
        self.on_saved = on_saved
        self.setWindowTitle("nous anki settings")
        self.setMinimumWidth(450)
        self.setup_ui()

    def setup_ui(self):
        ensure_fonts_loaded()
        self.setStyleSheet(NOUS_STYLESHEET)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # 1. NOUS ACCOUNT GROUP
        nous_group = QGroupBox("nous account && sync")
        nous_form = QFormLayout(nous_group)

        self.email_input = QLineEdit(self.config.get("nous_email", ""))
        self.email_input.setPlaceholderText("your-email@example.com")
        nous_form.addRow("nous email:", self.email_input)

        self.password_input = QLineEdit(self.config.get("nous_password", ""))
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("account password")
        nous_form.addRow("password:", self.password_input)

        self.user_id_input = QLineEdit(self.config.get("nous_user_id", self.sync_service.cached_state.get("userId", "")))
        self.user_id_input.setPlaceholderText("auto-filled after sign-in or manual uid")
        nous_form.addRow("nous user id:", self.user_id_input)

        test_row = QHBoxLayout()
        self.test_conn_btn = QPushButton("sign in && test connection")
        self.test_conn_btn.setProperty("class", "actionButton")
        self.test_conn_btn.setStyleSheet("font-size: 11px; font-weight: 400; padding: 5px 12px; background-color: #f1eef8; color: #5f5390; border: 1px solid #e2ddf0; border-radius: 12px;")
        self.test_conn_btn.clicked.connect(self.test_nous_connection)
        self.conn_status_label = QLabel("")
        test_row.addWidget(self.test_conn_btn)
        test_row.addWidget(self.conn_status_label)
        nous_form.addRow("", test_row)

        self.habit_input = QLineEdit(self.config.get("nous_habit_name", "Anki"))
        nous_form.addRow("habit name in nous:", self.habit_input)

        self.city_url_input = QLineEdit(self.config.get("nous_city_url", "https://nous.study/city"))
        nous_form.addRow("city url:", self.city_url_input)

        self.sync_interval_spin = QSpinBox()
        self.sync_interval_spin.setRange(15, 600)
        self.sync_interval_spin.setValue(int(self.config.get("sync_interval_seconds", 60)))
        self.sync_interval_spin.setSuffix(" seconds")
        nous_form.addRow("auto-sync interval:", self.sync_interval_spin)

        layout.addWidget(nous_group)

        # 2. AI SEARCH & API KEY GROUP
        ai_group = QGroupBox("ai study assistant (custom api key)")
        ai_form = QFormLayout(ai_group)

        self.ai_provider_combo = QComboBox()
        try:
            from PyQt6.QtWidgets import QListView
            self.ai_provider_combo.setView(QListView())
        except Exception:
            pass
        if hasattr(Qt, "CursorShape"):
            self.ai_provider_combo.setCursor(Qt.CursorShape.PointingHandCursor)

        self.ai_provider_combo.addItems(["gemini (free tier)", "openai", "claude", "perplexity", "custom (openai-compatible)"])
        current_prov = self.config.get("ai_provider", "gemini").lower()
        if "gemini" in current_prov:
            self.ai_provider_combo.setCurrentIndex(0)
        elif "openai" in current_prov:
            self.ai_provider_combo.setCurrentIndex(1)
        elif "claude" in current_prov or "anthropic" in current_prov:
            self.ai_provider_combo.setCurrentIndex(2)
        elif "perplexity" in current_prov:
            self.ai_provider_combo.setCurrentIndex(3)
        else:
            self.ai_provider_combo.setCurrentIndex(4)

        ai_form.addRow("provider:", self.ai_provider_combo)

        # Gemini Free key helper row
        gemini_help_row = QHBoxLayout()
        self.gemini_key_link_btn = QPushButton("get free gemini api key 🔑")
        self.gemini_key_link_btn.setStyleSheet("font-size: 11px; font-weight: 400; padding: 4px 10px; background-color: #f1eef8; color: #5f5390; border: 1px solid #e2ddf0; border-radius: 12px;")
        self.gemini_key_link_btn.clicked.connect(lambda: __import__('webbrowser').open("https://aistudio.google.com/app/apikey"))
        gemini_help_row.addWidget(self.gemini_key_link_btn)
        ai_form.addRow("", gemini_help_row)

        self.api_key_input = QLineEdit(self.config.get("ai_api_key", ""))
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("AIzaSy... (gemini) or sk-... (openai)")
        ai_form.addRow("api key:", self.api_key_input)

        self.ai_model_input = QLineEdit(self.config.get("ai_model", "gemini-2.5-flash"))
        self.ai_model_input.setPlaceholderText("gemini-2.5-flash / gpt-4o-mini / sonar")
        ai_form.addRow("model name:", self.ai_model_input)

        self.ai_base_url_input = QLineEdit(self.config.get("ai_base_url", ""))
        self.ai_base_url_input.setPlaceholderText("optional: http://localhost:11434/v1 or openrouter")
        ai_form.addRow("custom base url:", self.ai_base_url_input)

        layout.addWidget(ai_group)

        # 3. ACTION BUTTONS
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.cancel_btn = QPushButton("cancel")
        self.cancel_btn.setProperty("class", "actionButton")
        self.cancel_btn.setStyleSheet("background-color: #f1eef8; color: #5f5390; font-family: 'Satoshi', sans-serif; font-weight: 400; font-size: 11px; border: 1px solid #e2ddf0; border-radius: 14px; padding: 6px 16px;")
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("save settings")
        self.save_btn.setProperty("class", "primaryButton")
        self.save_btn.setStyleSheet("background-color: #8B7FB8; color: white; font-family: 'Satoshi', sans-serif; font-weight: 400; font-size: 11px; padding: 6px 18px; border-radius: 14px; border: none;")
        self.save_btn.clicked.connect(self.save_and_close)
        btn_row.addWidget(self.save_btn)

        layout.addLayout(btn_row)

    def test_nous_connection(self):
        email = self.email_input.text().strip()
        pwd = self.password_input.text()

        if not email or not pwd:
            self.conn_status_label.setText("enter email & password")
            self.conn_status_label.setStyleSheet("color: #d97706; font-size: 11px;")
            return

        self.conn_status_label.setText("connecting…")
        self.conn_status_label.setStyleSheet("color: #6b7280; font-size: 11px;")

        res = self.sync_service.sign_in(email, pwd)
        if res.get("success"):
            uid = res.get("userId", "")
            self.user_id_input.setText(uid)
            # Fetch latest stats
            stats_res = self.sync_service.fetch_user_stats()
            hours = stats_res.get("totalHours", 0.0)
            self.conn_status_label.setText(f"connected ({hours:.1f}h)")
            self.conn_status_label.setStyleSheet("color: #10b981; font-size: 11px; font-weight: 400;")
        else:
            err = res.get("error", "failed")
            self.conn_status_label.setText(f"{err}")
            self.conn_status_label.setStyleSheet("color: #ef4444; font-size: 11px;")

    def save_and_close(self):
        provider_map = {
            0: "gemini",
            1: "openai",
            2: "anthropic",
            3: "perplexity",
            4: "custom"
        }
        chosen_provider = provider_map.get(self.ai_provider_combo.currentIndex(), "gemini")

        updated_config = {
            "nous_email": self.email_input.text().strip(),
            "nous_password": self.password_input.text(),
            "nous_user_id": self.user_id_input.text().strip(),
            "nous_habit_name": self.habit_input.text().strip() or "Anki",
            "nous_city_url": self.city_url_input.text().strip() or "https://nous.study/city",
            "sync_interval_seconds": self.sync_interval_spin.value(),
            "ai_provider": chosen_provider,
            "ai_api_key": self.api_key_input.text().strip(),
            "ai_model": self.ai_model_input.text().strip(),
            "ai_base_url": self.ai_base_url_input.text().strip(),
        }

        # Update cached state userId if entered manually
        if updated_config["nous_user_id"]:
            self.sync_service.cached_state["userId"] = updated_config["nous_user_id"]
            self.sync_service._save_state()

        if self.on_saved:
            self.on_saved(updated_config)

        self.accept()
