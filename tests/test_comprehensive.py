"""
Comprehensive Integration and Feature Tests for Nous Anki
Tests SettingsDialog, Card Notes Injection, AI Client Payloads (Gemini/OpenAI/Claude/DeepSeek),
Embedded Browser, Timer Lifecycle, Tree SVG / Species, and Anki Hook Bridges.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, "/Applications/Anki.app/Contents/Resources/app_packages")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import Qt

from nous_anki import tree
from nous_anki.ai_search import AISearchClient
from nous_anki.browser_view import NousEmbeddedBrowser
from nous_anki.dock_widget import NousDockWidget
from nous_anki.notes import NotesManager
from nous_anki.settings_dialog import SettingsDialog
from nous_anki.sound import NousSoundPlayer
from nous_anki.sync import NousSyncService, TimeAccumulator
from nous_anki.timer_widget import NousTimerWidget
from nous_anki.tree_art import render_tree_svg_py
from nous_anki.tree_widget import NousTreeWidget, get_tree_svg
import nous_anki


class TestComprehensiveFeatures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        cls.app = QApplication.instance() or QApplication(["test_nous_anki", "-platform", "offscreen"])

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.sync_service = NousSyncService(self.test_dir)
        self.notes_mgr = NotesManager(self.test_dir)
        self.sound_player = NousSoundPlayer(self.test_dir)
        self.config = {
            "nous_email": "test@example.com",
            "nous_password": "password123",
            "nous_user_id": "ELvVX1K0AIRugIBiaS3iA4U2fkp2",
            "nous_habit_name": "Anki",
            "nous_city_url": "https://nous.study/city",
            "sync_interval_seconds": 60,
            "ai_provider": "gemini",
            "ai_api_key": "AIzaSyTestMockKey",
            "ai_model": "gemini-1.5-flash",
            "ai_base_url": "",
            "show_dock_on_startup": True,
        }

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # 1. SETTINGS DIALOG TESTS
    def test_settings_dialog_initialization_and_save(self):
        saved_config = {}

        def on_saved(cfg):
            nonlocal saved_config
            saved_config = cfg

        dialog = SettingsDialog(None, self.config, self.sync_service, on_saved=on_saved)
        self.assertEqual(dialog.email_input.text(), "test@example.com")
        self.assertEqual(dialog.user_id_input.text(), "ELvVX1K0AIRugIBiaS3iA4U2fkp2")
        self.assertEqual(dialog.habit_input.text(), "Anki")
        self.assertEqual(dialog.sync_interval_spin.value(), 60)
        self.assertEqual(dialog.ai_provider_combo.currentIndex(), 0)  # gemini free tier
        self.assertEqual(dialog.api_key_input.text(), "AIzaSyTestMockKey")
        self.assertEqual(dialog.ai_model_input.text(), "gemini-1.5-flash")

        # Edit fields and test save
        dialog.habit_input.setText("Medicine Flashcards")
        dialog.sync_interval_spin.setValue(120)
        dialog.save_and_close()

        self.assertEqual(saved_config.get("nous_habit_name"), "Medicine Flashcards")
        self.assertEqual(saved_config.get("sync_interval_seconds"), 120)
        self.assertEqual(saved_config.get("ai_provider"), "gemini")
        self.assertEqual(self.sync_service.cached_state.get("userId"), "ELvVX1K0AIRugIBiaS3iA4U2fkp2")

    def test_settings_dialog_connection_test(self):
        dialog = SettingsDialog(None, self.config, self.sync_service)
        # Empty credentials check
        dialog.email_input.setText("")
        dialog.password_input.setText("")
        dialog.test_nous_connection()
        self.assertIn("enter email & password", dialog.conn_status_label.text())

        # Mock successful sign-in
        with patch.object(self.sync_service, "sign_in", return_value={"success": True, "userId": "mock_uid_123"}):
            with patch.object(self.sync_service, "fetch_user_stats", return_value={"totalHours": 14.5}):
                dialog.email_input.setText("user@test.com")
                dialog.password_input.setText("pass")
                dialog.test_nous_connection()
                self.assertIn("connected (14.5h)", dialog.conn_status_label.text())
                self.assertEqual(dialog.user_id_input.text(), "mock_uid_123")

    # 2. CARD NOTES INJECTION TESTS
    def test_append_note_to_card_with_notes_field(self):
        mock_note = {
            "Front": "What is the primary treatment for tension pneumothorax?",
            "Back": "Needle thoracostomy followed by tube thoracostomy",
            "Notes": "Old note content"
        }
        mock_note_type = {"flds": [{"name": "Front"}, {"name": "Back"}, {"name": "Notes"}]}

        mock_card = MagicMock()
        mock_anki_note = MagicMock()
        mock_anki_note.__getitem__.side_effect = lambda k: mock_note[k]
        def setitem(k, v):
            mock_note[k] = v
        mock_anki_note.__setitem__.side_effect = setitem
        mock_anki_note.note_type.return_value = mock_note_type
        mock_card.note.return_value = mock_anki_note

        success = NotesManager.append_note_to_card(mock_card, "Remember: 2nd intercostal space midclavicular or 5th lateral")
        self.assertTrue(success)
        self.assertIn("Old note content", mock_note["Notes"])
        self.assertIn("Nous Note", mock_note["Notes"])
        self.assertIn("2nd intercostal space", mock_note["Notes"])

    def test_append_note_to_card_with_extra_field(self):
        mock_note = {
            "Text": "The enzyme inhibited by allopurinol is {{c1::xanthine oxidase}}.",
            "Extra": ""
        }
        mock_note_type = {"flds": [{"name": "Text"}, {"name": "Extra"}]}

        mock_card = MagicMock()
        mock_anki_note = MagicMock()
        mock_anki_note.__getitem__.side_effect = lambda k: mock_note[k]
        def setitem(k, v):
            mock_note[k] = v
        mock_anki_note.__setitem__.side_effect = setitem
        mock_anki_note.note_type.return_value = mock_note_type
        mock_card.note.return_value = mock_anki_note

        success = NotesManager.append_note_to_card(mock_card, "Febuxostat is also a xanthine oxidase inhibitor.")
        self.assertTrue(success)
        self.assertIn("Febuxostat", mock_note["Extra"])
        self.assertIn("Nous Note", mock_note["Extra"])

    # 3. AI PROVIDER PAYLOAD TESTS
    def test_gemini_api_payload_and_url(self):
        client = AISearchClient(provider="gemini", api_key="AIzaSyMockKey", model="gemini-1.5-flash")
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps({
                "candidates": [{
                    "content": {
                        "parts": [{"text": "Gemini answer: high-yield clinical pearl."}]
                    }
                }]
            }).encode("utf-8")
            mock_urlopen.return_value.__enter__.return_value = mock_response

            res = client.search_query("Explain SIADH vs Diabetes Insipidus")
            self.assertTrue(res["success"])
            self.assertEqual(res["provider"].lower(), "gemini")
            self.assertEqual(res["model"], "gemini-1.5-flash")
            self.assertIn("high-yield clinical pearl", res["answer"])

            # Verify request URL format
            called_req = mock_urlopen.call_args[0][0]
            self.assertIn("generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent", called_req.full_url)
            self.assertIn("key=AIzaSyMockKey", called_req.full_url)
            payload = json.loads(called_req.data.decode("utf-8"))
            self.assertIn("contents", payload)
            self.assertIn("SIADH", payload["contents"][0]["parts"][0]["text"])

    def test_openai_api_payload_and_url(self):
        client = AISearchClient(provider="openai", api_key="sk-mockOpenAIKey", model="gpt-4o-mini")
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps({
                "choices": [{
                    "message": {"content": "OpenAI answer: cardiac action potential."}
                }]
            }).encode("utf-8")
            mock_urlopen.return_value.__enter__.return_value = mock_response

            res = client.search_query("Explain phase 0 of cardiac action potential")
            self.assertTrue(res["success"])
            self.assertIn("openai", res["provider"].lower())
            self.assertIn("cardiac action potential", res["answer"])

            called_req = mock_urlopen.call_args[0][0]
            self.assertIn("api.openai.com/v1/chat/completions", called_req.full_url)
            self.assertEqual(called_req.headers.get("Authorization"), "Bearer sk-mockOpenAIKey")

    def test_anthropic_api_payload_and_url(self):
        client = AISearchClient(provider="anthropic", api_key="sk-ant-mockKey", model="claude-3-5-sonnet-20241022")
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps({
                "content": [{
                    "type": "text",
                    "text": "Claude answer: nephrotic syndrome features."
                }]
            }).encode("utf-8")
            mock_urlopen.return_value.__enter__.return_value = mock_response

            res = client.search_query("Nephrotic syndrome triad")
            self.assertTrue(res["success"])
            self.assertEqual(res["provider"].lower(), "anthropic")
            self.assertIn("nephrotic syndrome features", res["answer"])

            called_req = mock_urlopen.call_args[0][0]
            self.assertIn("api.anthropic.com/v1/messages", called_req.full_url)
            self.assertEqual(called_req.headers.get("X-api-key"), "sk-ant-mockKey")

    # 4. EMBEDDED BROWSER AND QUICK LINKS
    def test_embedded_browser_features(self):
        browser = NousEmbeddedBrowser(None, home_url="https://nous.study/city")
        self.assertEqual(browser.home_url, "https://nous.study/city")

        # Quick navigation
        browser.open_pill_target("https://next.amboss.com")
        self.assertEqual(browser.url_input.text(), "https://next.amboss.com")

        browser.open_pill_target("https://pubmed.ncbi.nlm.nih.gov")
        self.assertEqual(browser.url_input.text(), "https://pubmed.ncbi.nlm.nih.gov")

        browser.go_home()
        self.assertEqual(browser.url_input.text(), "https://nous.study/city")

    # 5. TIMER COMPREHENSIVE LIFECYCLE
    def test_timer_widget_short_session_vs_valid_session(self):
        parent = QMainWindow()
        synced_called = False

        def on_synced():
            nonlocal synced_called
            synced_called = True

        timer = NousTimerWidget(parent, self.sync_service, self.sound_player, on_synced=on_synced)
        
        # Test short session (<5s) stop
        timer.elapsed_seconds = 3
        timer.stop_and_sync()
        self.assertFalse(synced_called)
        self.assertIn("session too short", timer.timer_status.text())

        # Test valid session (>=5s) stop
        timer.start_timestamp = 1000.0
        timer.elapsed_seconds = 180  # 3 minutes
        timer.running = True
        def fake_sync(**kwargs):
            if "on_done" in kwargs and kwargs["on_done"]:
                kwargs["on_done"](True, 1)

        with patch("time.time", return_value=1180.0):
            with patch.object(self.sync_service, "process_and_sync", side_effect=fake_sync) as mock_sync:
                with patch.object(self.sound_player, "play_chime") as mock_chime:
                    timer.stop_and_sync()
                    mock_chime.assert_called_once()
                    mock_sync.assert_called_once()
                    self.assertTrue(synced_called)
                    self.assertIn("synced 03:00 to habit dashboard", timer.timer_status.text())

    # 6. TREE ART & PROGRESS COVERAGE
    def test_tree_art_day_and_night_species(self):
        # Day tree: oak
        svg_oak = render_tree_svg_py("oak", 60.0, is_growing=True)
        self.assertIn("<svg", svg_oak)
        self.assertIn("tree-branch", svg_oak)
        self.assertIn("tree-leaf", svg_oak)

        # Night tree: moon-willow
        svg_willow = render_tree_svg_py("moon-willow", 85.0, is_growing=True)
        self.assertIn("<svg", svg_willow)
        self.assertIn("tree-branch", svg_willow)

        # Widget tree setting
        widget = NousTreeWidget()
        widget.set_tree("moon-willow", pct=85.0, is_growing=True)
        self.assertTrue(widget.is_night)
        self.assertEqual(widget.tree_id, "moon-willow")
        self.assertEqual(widget.pct, 85.0)

        # Tick animation
        widget._on_tick()
        self.assertGreater(widget.anim_time, 0.0)

    # 7. ANKI HOOKS & UI BRIDGES
    def test_toolbar_and_badge_hooks(self):
        # Toolbar right tray content
        content_tray = []
        mock_toolbar = MagicMock()
        mock_toolbar.link_handlers = {}
        nous_anki.on_top_toolbar_will_set_right_tray_content(content_tray, mock_toolbar)
        self.assertEqual(len(content_tray), 1)
        self.assertIn("nous_toggle", content_tray[0])
        self.assertIn("nous_folder", content_tray[0])
        self.assertIn("nous", content_tray[0])

        # Main deck browser badge
        content_deck = MagicMock()
        content_deck.stats = ""
        nous_anki.on_deck_browser_will_render_content(None, content_deck)
        self.assertIn("nous anki sync", content_deck.stats)
        self.assertIn("pycmd('nous_toggle')", content_deck.stats)

        # Webview JS message handler
        handled, ret = nous_anki.on_webview_message((False, None), "nous_toggle", None)
        self.assertTrue(handled)

        handled2, ret2 = nous_anki.on_webview_message((False, None), "nous_folder", None)
        self.assertTrue(handled2)

    # 8. DOCK WIDGET USER INTERACTIONS
    def test_dock_widget_user_actions(self):
        parent = QMainWindow()
        dock = NousDockWidget(parent, self.sync_service, self.notes_mgr, self.sound_player, self.config)

        # Test model dropdown switching to custom
        custom_idx = dock.model_combo.findText("custom (any model)", Qt.MatchFlag.MatchContains)
        if custom_idx >= 0:
            dock.model_combo.setCurrentIndex(custom_idx)
            self.assertTrue(dock.custom_model_input.isVisible())
            dock.custom_model_input.setText("ollama/medllama2")
            prov, model = dock.get_selected_model_and_provider()
            self.assertEqual(model, "ollama/medllama2")

        # Test copy to notes
        dock.ai_result_view.setPlainText("Important pearl: Cushing triad = bradycardia, hypertension, irregular respirations")
        dock.copy_to_notes_btn.click()
        self.assertEqual(dock.tabs.currentIndex(), 2)  # Switched to notes tab
        self.assertIn("Cushing triad", dock.notes_edit.toPlainText())

        # Test clear notes
        dock.clear_notes_btn.click()
        self.assertEqual(dock.notes_edit.toPlainText(), "")


if __name__ == "__main__":
    unittest.main()
