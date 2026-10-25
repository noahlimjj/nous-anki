"""
Renders showcase screenshots of the Nous Anki Add-on UI
"""

import os
import sys

# Must import QtWebEngineWidgets before QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QColor, QFont, QPainter

from nous_anki.theme import ensure_fonts_loaded, NOUS_STYLESHEET
from nous_anki.dock_widget import NousDockWidget
from nous_anki.settings_dialog import SettingsDialog
from nous_anki.sync import NousSyncService
from nous_anki.notes import NotesManager
from nous_anki.sound import NousSoundPlayer

def main():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication(sys.argv)
    ensure_fonts_loaded()

    storage_dir = "/tmp/nous_test_storage"
    os.makedirs(storage_dir, exist_ok=True)

    sync_service = NousSyncService(storage_dir)
    sync_service.cached_state = {
        "userId": "usr_demo",
        "totalHours": 14.5,
        "treeBoxesOpened": 3
    }
    notes_mgr = NotesManager(storage_dir)
    sound_player = NousSoundPlayer(storage_dir)

    config = {
        "nous_email": "demo@nous.study",
        "nous_user_id": "usr_demo",
        "nous_habit_name": "Anki",
        "nous_city_url": "https://nous.study/city",
        "sync_interval_seconds": 60,
        "ai_provider": "gemini",
        "ai_api_key": "AIzaSyDemoKey",
        "ai_model": "gemini-2.5-flash",
    }

    # 1. Render Dock Widget
    dock = NousDockWidget(None, sync_service, notes_mgr, sound_player, config)
    dock.resize(360, 680)
    dock.show()

    # Pre-populate sample notes
    dock.notes_edit.setText("• primary vs secondary hemostasis mnemonics\n• von willebrand factor stabilizes factor VIII\n• auto-synced from nous anki")
    dock.ai_result_view.setHtml("<div style='font-family: Satoshi; font-size: 11px; color: #363f51;'><span style='color: #7c3aed; font-weight: 400;'>gemini 2.5 flash:</span><br/>von willebrand disease is the most common inherited bleeding disorder, characterized by deficient or defective vWF.</div>")

    app.processEvents()

    dock_pix = dock.grab()
    dock_pix.save("/tmp/nous_anki_dock.png")
    print(f"Saved dock screenshot: /tmp/nous_anki_dock.png ({dock_pix.width()}x{dock_pix.height()})")

    # 2. Render Settings Dialog
    settings = SettingsDialog(None, config, sync_service)
    settings.resize(460, 520)
    settings.show()
    app.processEvents()

    settings_pix = settings.grab()
    settings_pix.save("/tmp/nous_anki_settings.png")
    print(f"Saved settings screenshot: /tmp/nous_anki_settings.png ({settings_pix.width()}x{settings_pix.height()})")

    # 3. Create a side-by-side showcase banner
    total_w = dock_pix.width() + settings_pix.width() + 60
    total_h = max(dock_pix.height(), settings_pix.height()) + 80

    showcase = QPixmap(total_w, total_h)
    showcase.fill(QColor("#f8f9fb"))

    painter = QPainter(showcase)
    # Header title
    title_font = QFont("Satoshi", 18)
    title_font.setWeight(QFont.Weight.Normal)
    painter.setFont(title_font)
    painter.setPen(QColor("#363f51"))
    painter.drawText(30, 42, "nous anki add-on — authentic satoshi & soft pill design")

    subtitle_font = QFont("Satoshi", 11)
    subtitle_font.setWeight(QFont.Weight.Light)
    painter.setFont(subtitle_font)
    painter.setPen(QColor("#7d8ca8"))
    painter.drawText(30, 62, "full nous color palette (#8b7fb8, #5fa8a3, #f1eef8), rounded pill dropdowns, and live tree growth")

    # Draw dock and settings pixmaps
    painter.drawPixmap(30, 75, dock_pix)
    painter.drawPixmap(dock_pix.width() + 50, 75, settings_pix)
    painter.end()

    showcase.save("/tmp/nous_anki_showcase.png")
    print(f"Saved showcase banner: /tmp/nous_anki_showcase.png ({total_w}x{total_h})")

if __name__ == "__main__":
    main()
