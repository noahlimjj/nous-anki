"""
Headless Qt GUI Test for Nous Anki
Tests QFontDatabase Satoshi font registration, DockWidget, Timer, and Browser in offscreen Qt.
"""

import os
import sys
import tempfile
import unittest

# Ensure Anki packages and project are in path
sys.path.insert(0, "/Applications/Anki.app/Contents/Resources/app_packages")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QFontDatabase

from nous_anki.dock_widget import NousDockWidget
from nous_anki.notes import NotesManager
from nous_anki.sound import NousSoundPlayer
from nous_anki.sync import NousSyncService
from nous_anki.timer_widget import NousTimerWidget
from nous_anki.browser_view import NousEmbeddedBrowser


class TestNousAnkiGUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize offscreen Qt Application
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        cls.app = QApplication.instance() or QApplication(["test_nous_anki", "-platform", "offscreen"])

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.sync_service = NousSyncService(self.test_dir)
        self.notes_mgr = NotesManager(self.test_dir)
        self.sound_player = NousSoundPlayer(self.test_dir)
        self.config = {
            "nous_user_id": "test_noah",
            "nous_habit_name": "Anki",
            "nous_city_url": "https://nous.study/city",
            "ai_provider": "openai",
            "ai_api_key": "test_key",
            "ai_model": "gpt-4o-mini",
        }

    def test_satoshi_font_registration(self):
        fonts_dir = os.path.join(os.path.dirname(__file__), "..", "nous_anki", "fonts")
        font_path = os.path.join(fonts_dir, "satoshi-500.woff2")
        font_id = QFontDatabase.addApplicationFont(font_path)
        self.assertNotEqual(font_id, -1, "Failed to load Satoshi into QFontDatabase")
        families = QFontDatabase.applicationFontFamilies(font_id)
        self.assertIn("Satoshi", families)

    def test_timer_widget_controls(self):
        parent = QMainWindow()
        timer = NousTimerWidget(parent, self.sync_service, self.sound_player)
        self.assertFalse(timer.running)
        self.assertEqual(timer.time_label.text(), "00:00")

        # Test start
        timer.toggle_start_pause()
        self.assertTrue(timer.running)
        self.assertEqual(timer.start_btn.text(), "⏸ Pause")

        # Test pause
        timer.toggle_start_pause()
        self.assertFalse(timer.running)
        self.assertEqual(timer.start_btn.text(), "▶ Resume")

        # Test mode change to 25m Focus
        timer.mode_combo.setCurrentIndex(1)
        self.assertEqual(timer.mode, "countdown")
        self.assertEqual(timer.time_label.text(), "25:00")

    def test_dock_widget_initialization(self):
        parent = QMainWindow()
        dock = NousDockWidget(parent, self.sync_service, self.notes_mgr, self.sound_player, self.config)
        self.assertIsNotNone(dock)
        self.assertEqual(dock.tabs.count(), 3)
        self.assertEqual(dock.tabs.tabText(0), "🤖 AI Q&A")
        self.assertEqual(dock.tabs.tabText(1), "🌐 Browser")
        self.assertEqual(dock.tabs.tabText(2), "📝 Notes")

        # Verify tree card populated
        self.assertIn(dock.tree_name_label.text(), ["Oak", "Cherry Blossom", "Ancient Sakura", "Willow", "Bamboo Grove", "Pine"])
        self.assertGreater(dock.tree_progress.maximum(), 0)

    def test_embedded_browser_initialization(self):
        browser = NousEmbeddedBrowser(None, home_url="https://nous.study/city")
        self.assertIsNotNone(browser.web_view)
        self.assertEqual(browser.home_url, "https://nous.study/city")


if __name__ == "__main__":
    unittest.main()
