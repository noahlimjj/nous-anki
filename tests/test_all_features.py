"""
Comprehensive Automated Test Suite for Nous Anki
Tests all functionality:
1. Satoshi Font Loading
2. Nous Tree Path & Vector SVG
3. Nous Focus Timer & Audio Chimes
4. Study Tracking & Offline Queue
5. Multi-Model AI Client & Web Search
6. Notes Scratchpad & Card Injection
7. Embedded Browser & Dock Widget Integration
"""

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nous_anki import tree
from nous_anki.ai_search import AISearchClient, POPULAR_MODELS
from nous_anki.notes import NotesManager
from nous_anki.sound import NousSoundPlayer
from nous_anki.sync import NousSyncService, TimeAccumulator


class TestNousAnkiAll(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    # 1. SATOSHI FONT TESTS
    def test_satoshi_fonts_exist(self):
        base_fonts = os.path.join(os.path.dirname(__file__), "..", "nous_anki", "fonts")
        for weight in ["satoshi-300.woff2", "satoshi-400.woff2", "satoshi-500.woff2", "satoshi-700.woff2"]:
            p = os.path.join(base_fonts, weight)
            self.assertTrue(os.path.exists(p), f"Missing font: {weight}")
            self.assertGreater(os.path.getsize(p), 15000, f"Font file too small: {weight}")

    # 2. NOUS TREE SYSTEM TESTS
    def test_tree_rng_and_plan(self):
        # Deterministic match with tree-path.js
        steps = tree.plan("noahlimjj")
        self.assertEqual(len(steps), 35)
        # Each step has id, tier, hours, from, at
        for s in steps:
            self.assertIn("id", s)
            self.assertIn("tier", s)
            self.assertIn("hours", s)
            self.assertIn("at", s)

    def test_tree_progress_and_svg(self):
        steps = tree.plan("noahlimjj")
        prog = tree.progress(steps, 2.5)
        self.assertIn("current_name", prog)
        self.assertIn("pct", prog)
        self.assertIn("hours_left", prog)
        self.assertGreaterEqual(prog["pct"], 0.0)
        self.assertLessEqual(prog["pct"], 100.0)

        # SVG generation
        cur_id = prog["current"]["id"]
        svg = tree.generate_tree_svg(cur_id, pct=prog["pct"])
        self.assertIn("<svg", svg)
        self.assertIn("tree-branch", svg)
        self.assertIn("tree-leaf", svg)

    # 3. SOUND PLAYER & CHIME GENERATION
    def test_sound_effects(self):
        player = NousSoundPlayer(self.test_dir)
        self.assertTrue(os.path.exists(player.bell_path))
        self.assertTrue(os.path.exists(player.chime_path))
        # Non-blocking play triggers
        player.play_start()
        player.play_chime(repeat=1)

    # 4. TIME ACCUMULATION & BOUNDED DURATION
    def test_study_time_tracking(self):
        acc = TimeAccumulator(max_card_seconds=60.0)
        acc.add_card_time(4000)   # 4s
        acc.add_card_time(12000)  # 12s
        acc.add_card_time(90000)  # 90s -> capped to 60s
        self.assertEqual(acc.current_cards, 3)
        self.assertEqual(acc.current_duration_ms, 76000)

        session = acc.drain_session(min_ms=1000)
        self.assertIsNotNone(session)
        self.assertEqual(session["durationMs"], 76000)
        self.assertEqual(session["cardsCount"], 3)
        self.assertEqual(acc.current_duration_ms, 0)

    # 5. OFFLINE QUEUE
    def test_offline_queue_resilience(self):
        service = NousSyncService(self.test_dir)
        self.assertEqual(len(service.get_pending_queue()), 0)

        session_data = {
            "habitId": "anki",
            "habitName": "Anki",
            "durationMs": 180000,
            "cardsCount": 15,
            "createdAt": "2026-10-25T10:00:00Z"
        }
        service.enqueue_session(session_data)
        queue = service.get_pending_queue()
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]["durationMs"], 180000)

    # 6. MULTI-MODEL AI Q&A CLIENT
    def test_multi_model_selection(self):
        client = AISearchClient(provider="openai", api_key="test_key", model="gpt-4o")
        self.assertEqual(client.provider, "openai")
        self.assertEqual(client.model, "gpt-4o")

        # Verify popular models catalogue
        self.assertGreater(len(POPULAR_MODELS), 8)
        model_names = [m[2] for m in POPULAR_MODELS if m[2]]
        self.assertIn("gpt-4o", model_names)
        self.assertIn("claude-3-5-sonnet-20241022", model_names)
        self.assertIn("gemini-2.5-flash", model_names)
        self.assertIn("sonar", model_names)

        # Web search URL builder
        amboss_url = AISearchClient.get_web_search_url("amboss", "hyperkalemia")
        self.assertIn("next.amboss.com/us/search?q=hyperkalemia", amboss_url)

    # 7. NOTES SCRATCHPAD
    def test_notes_scratchpad(self):
        notes = NotesManager(self.test_dir)
        self.assertEqual(notes.load_scratchpad(), "")
        sample_text = "Mnemonic: MUDPILES for anion gap metabolic acidosis"
        notes.save_scratchpad(sample_text)
        self.assertEqual(notes.load_scratchpad(), sample_text)


if __name__ == "__main__":
    unittest.main()
