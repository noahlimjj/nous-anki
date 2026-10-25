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


class SettingsDialog(QDialog):
    def __init__(self, parent, config: Dict[str, Any], sync_service: NousSyncService, on_saved: Optional[Callable[[Dict[str, Any]], None]] = None):
        super().__init__(parent)
        self.config = config
        self.sync_service = sync_service
        self.on_saved = on_saved
        self.setWindowTitle("Nous Anki Settings")
        self.setMinimumWidth(450)
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
        QDialog {
            background-color: #f8f9fb;
            font-family: "Satoshi", -apple-system, BlinkMacSystemFont, sans-serif;
            color: #363f51;
        }
        QGroupBox {
            font-family: "Satoshi", sans-serif;
            font-weight: 500;
            font-size: 13px;
            color: #5f5390;
            border: 1px solid #ebe8f3;
            border-radius: 14px;
            margin-top: 12px;
            padding: 16px 12px 12px 12px;
            background-color: #ffffff;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 14px;
            padding: 0 6px;
        }
        QLineEdit, QComboBox, QSpinBox {
            background-color: #ffffff;
            border: 1px solid #ebe8f3;
            border-radius: 8px;
            padding: 6px;
            color: #363f51;
            font-family: "Satoshi", sans-serif;
        }
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
            border: 1px solid #8B7FB8;
        }
        QPushButton {
            border-radius: 14px;
            padding: 5px 14px;
            font-family: "Satoshi", sans-serif;
            font-weight: 500;
            background-color: #f1eef8;
            color: #5f5390;
            border: 1px solid #e2ddf0;
        }
        QPushButton:hover {
            background-color: #e6e0f3;
        }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # 1. NOUS ACCOUNT GROUP
        nous_group = QGroupBox("Nous Account & Sync")
        nous_form = QFormLayout(nous_group)

        self.email_input = QLineEdit(self.config.get("nous_email", ""))
        self.email_input.setPlaceholderText("your-email@example.com")
        nous_form.addRow("Nous Email:", self.email_input)

        self.password_input = QLineEdit(self.config.get("nous_password", ""))
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Account password")
        nous_form.addRow("Password:", self.password_input)

        self.user_id_input = QLineEdit(self.config.get("nous_user_id", self.sync_service.cached_state.get("userId", "")))
        self.user_id_input.setPlaceholderText("Auto-filled after sign-in or manual UID")
        nous_form.addRow("Nous User ID:", self.user_id_input)

        test_row = QHBoxLayout()
        self.test_conn_btn = QPushButton("Sign In & Test Connection")
        self.test_conn_btn.clicked.connect(self.test_nous_connection)
        self.conn_status_label = QLabel("")
        test_row.addWidget(self.test_conn_btn)
        test_row.addWidget(self.conn_status_label)
        nous_form.addRow("", test_row)

        self.habit_input = QLineEdit(self.config.get("nous_habit_name", "Anki"))
        nous_form.addRow("Habit Name in Nous:", self.habit_input)

        self.city_url_input = QLineEdit(self.config.get("nous_city_url", "https://nous.study/city"))
        nous_form.addRow("City URL:", self.city_url_input)

        self.sync_interval_spin = QSpinBox()
        self.sync_interval_spin.setRange(15, 600)
        self.sync_interval_spin.setValue(int(self.config.get("sync_interval_seconds", 60)))
        self.sync_interval_spin.setSuffix(" seconds")
        nous_form.addRow("Auto-Sync Interval:", self.sync_interval_spin)

        layout.addWidget(nous_group)

        # 2. AI SEARCH & API KEY GROUP
        ai_group = QGroupBox("AI Study Assistant (Custom API Key)")
        ai_form = QFormLayout(ai_group)

        self.ai_provider_combo = QComboBox()
        self.ai_provider_combo.addItems(["OpenAI", "Gemini", "Perplexity", "Custom (OpenAI-compatible)"])
        current_prov = self.config.get("ai_provider", "openai").lower()
        if "gemini" in current_prov:
            self.ai_provider_combo.setCurrentIndex(1)
        elif "perplexity" in current_prov:
            self.ai_provider_combo.setCurrentIndex(2)
        elif "custom" in current_prov:
            self.ai_provider_combo.setCurrentIndex(3)
        else:
            self.ai_provider_combo.setCurrentIndex(0)

        ai_form.addRow("Provider:", self.ai_provider_combo)

        self.api_key_input = QLineEdit(self.config.get("ai_api_key", ""))
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("sk-... or AIzaSy...")
        ai_form.addRow("API Key:", self.api_key_input)

        self.ai_model_input = QLineEdit(self.config.get("ai_model", ""))
        self.ai_model_input.setPlaceholderText("gpt-4o-mini / gemini-2.5-flash / sonar")
        ai_form.addRow("Model Name:", self.ai_model_input)

        self.ai_base_url_input = QLineEdit(self.config.get("ai_base_url", ""))
        self.ai_base_url_input.setPlaceholderText("Optional: http://localhost:11434/v1 or OpenRouter")
        ai_form.addRow("Custom Base URL:", self.ai_base_url_input)

        layout.addWidget(ai_group)

        # 3. ACTION BUTTONS
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setStyleSheet("background-color: #8b5cf6; color: white; font-weight: bold; padding: 6px 16px; border-radius: 6px;")
        self.save_btn.clicked.connect(self.save_and_close)
        btn_row.addWidget(self.save_btn)

        layout.addLayout(btn_row)

    def test_nous_connection(self):
        email = self.email_input.text().strip()
        pwd = self.password_input.text()

        if not email or not pwd:
            self.conn_status_label.setText("⚠️ Enter email & password")
            self.conn_status_label.setStyleSheet("color: #d97706;")
            return

        self.conn_status_label.setText("Connecting...")
        self.conn_status_label.setStyleSheet("color: #6b7280;")

        res = self.sync_service.sign_in(email, pwd)
        if res.get("success"):
            uid = res.get("userId", "")
            self.user_id_input.setText(uid)
            # Fetch latest stats
            stats_res = self.sync_service.fetch_user_stats()
            hours = stats_res.get("totalHours", 0.0)
            self.conn_status_label.setText(f"✅ Connected! ({hours:.1f}h)")
            self.conn_status_label.setStyleSheet("color: #10b981; font-weight: bold;")
        else:
            err = res.get("error", "Failed")
            self.conn_status_label.setText(f"❌ {err}")
            self.conn_status_label.setStyleSheet("color: #ef4444;")

    def save_and_close(self):
        provider_map = {
            0: "openai",
            1: "gemini",
            2: "perplexity",
            3: "custom"
        }
        chosen_provider = provider_map.get(self.ai_provider_combo.currentIndex(), "openai")

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
